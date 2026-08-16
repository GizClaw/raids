package config

import (
	"os"
	"strings"
	"testing"
	"time"
)

func TestSecretSourceRequiresExactlyOneSource(t *testing.T) {
	_, err := (SecretSource{}).Read(strings.NewReader(""))
	if err == nil {
		t.Fatal("expected missing source error")
	}
	_, err = (SecretSource{Env: "A", File: "b"}).Read(strings.NewReader(""))
	if err == nil {
		t.Fatal("expected conflicting source error")
	}
}

func TestConfigValidatesPairedExecutionControls(t *testing.T) {
	valid := Config{Server: "edge.example:9821", Suite: "suite.yaml", AdminKey: SecretSource{Env: "RAIDTEST_TEST_ADMIN"}, CaseParallelism: 8, CaseRampUp: 250 * time.Millisecond, DiagnosticProbeInterval: time.Second}
	if err := valid.Validate(); err != nil {
		t.Fatal(err)
	}
	for name, mutate := range map[string]func(*Config){
		"parallelism":   func(c *Config) { c.CaseParallelism = 9 },
		"explicit zero": func(c *Config) { c.CaseParallelism = 0; c.CaseParallelismSet = true },
		"ramp":          func(c *Config) { c.CaseRampUp = -1 },
		"probe":         func(c *Config) { c.DiagnosticProbeInterval = 99 * time.Millisecond },
	} {
		t.Run(name, func(t *testing.T) {
			candidate := valid
			mutate(&candidate)
			if err := candidate.Validate(); err == nil {
				t.Fatal("invalid execution control was accepted")
			}
		})
	}
	nonSuite := Config{Server: "edge.example:9821", Workflow: "workflow.yaml", Plan: "plan.yaml", AdminKey: SecretSource{Env: "RAIDTEST_TEST_ADMIN"}, CaseParallelism: 2}
	if err := nonSuite.Validate(); err == nil {
		t.Fatal("programmatic parallelism outside suite mode was accepted")
	}
	withProfile := valid
	withProfile.RuntimeProfileFile = "/tmp/volc-mem0-profile.yaml"
	if err := withProfile.Validate(); err != nil {
		t.Fatalf("suite RuntimeProfile override was rejected: %v", err)
	}
}

func TestSecretSourceReportsWhetherItIsConfigured(t *testing.T) {
	if (SecretSource{}).Configured() || !(SecretSource{File: "key"}).Configured() {
		t.Fatal("unexpected Configured result")
	}
}

func TestSecretSourceReadsEnvironmentWithoutEchoingValue(t *testing.T) {
	t.Setenv("RAIDTEST_TEST_SECRET", "super-secret")
	got, err := (SecretSource{Env: "RAIDTEST_TEST_SECRET"}).Read(strings.NewReader(""))
	if err != nil || string(got) != "super-secret" {
		t.Fatalf("Read() = %q, %v", got, err)
	}
	if strings.Contains(""+errorString(err), string(got)) {
		t.Fatal("secret appeared in error")
	}
}

func TestConfigValidation(t *testing.T) {
	t.Setenv("RAIDTEST_TEST_ADMIN", "key")
	c := Config{Server: "edge.example:9821", Workflow: "workflow.yaml", Plan: "plan.yaml", AdminKey: SecretSource{Env: "RAIDTEST_TEST_ADMIN"}}
	if err := c.Validate(); err != nil {
		t.Fatal(err)
	}
	if c.RuntimeProfile != "default" || c.PeerServer != c.Server || c.OpenAIBaseURL != "http://edge.example:9821/openai/v1" ||
		len(c.ASTInputModes) != 2 || c.ASTInputModes[0] != "push-to-talk" || c.ASTInputModes[1] != "realtime" {
		t.Fatalf("unexpected defaults: %#v", c)
	}
	if _, ok := c.Redacted()["admin_key"]; ok {
		t.Fatal("redacted config contains secret field")
	}
	_ = os.Unsetenv("RAIDTEST_TEST_ADMIN")
}

func TestConfigValidatesASTInputModes(t *testing.T) {
	c := Config{
		Server: "admin.example:9820", Workflow: "workflow.yaml", Plan: "plan.yaml",
		AdminKey:      SecretSource{Env: "RAIDTEST_TEST_ADMIN"},
		ASTInputModes: []string{"realtime", "push-to-talk", "realtime"},
	}
	if err := c.Validate(); err != nil {
		t.Fatal(err)
	}
	if len(c.ASTInputModes) != 2 || c.ASTInputModes[0] != "realtime" || c.ASTInputModes[1] != "push-to-talk" {
		t.Fatalf("ASTInputModes=%#v", c.ASTInputModes)
	}
	c.ASTInputModes = []string{"text"}
	if err := c.Validate(); err == nil {
		t.Fatal("unsupported AST input mode was accepted")
	}
}

func TestConfigAcceptsSeparatePeerServer(t *testing.T) {
	c := Config{
		Server: "admin.example:9820", PeerServer: "edge.example:9821",
		Workflow: "workflow.yaml", Plan: "plan.yaml",
		AdminKey: SecretSource{Env: "RAIDTEST_TEST_ADMIN"},
	}
	if err := c.Validate(); err != nil {
		t.Fatal(err)
	}
	if c.PeerServer != "edge.example:9821" {
		t.Fatalf("PeerServer = %q", c.PeerServer)
	}
	if c.OpenAIBaseURL != "http://edge.example:9821/openai/v1" {
		t.Fatalf("OpenAIBaseURL = %q", c.OpenAIBaseURL)
	}
}

func TestConfigAllowsClusterOpenAIWithoutSeparateKey(t *testing.T) {
	c := Config{
		Server: "admin.example:9820", PeerServer: "edge.example:9821",
		Workflow: "workflow.yaml", Plan: "plan.yaml", JudgeModel: "compact",
		AdminKey: SecretSource{Env: "RAIDTEST_TEST_ADMIN"},
	}
	if err := c.Validate(); err != nil {
		t.Fatal(err)
	}
	c.OpenAIBaseURL = "https://api.openai.com/v1"
	if err := c.Validate(); err == nil {
		t.Fatal("external OpenAI endpoint without a key was accepted")
	}
	c.OpenAIKey = SecretSource{Env: "RAIDTEST_TEST_OPENAI"}
	if err := c.Validate(); err != nil {
		t.Fatalf("external OpenAI endpoint with key: %v", err)
	}
}

func TestConfigRejectsInvalidPeerServer(t *testing.T) {
	c := Config{
		Server: "admin.example:9820", PeerServer: "https://edge.example:9821",
		Workflow: "workflow.yaml", Plan: "plan.yaml",
		AdminKey: SecretSource{Env: "RAIDTEST_TEST_ADMIN"},
	}
	if err := c.Validate(); err == nil {
		t.Fatal("peer server with URL scheme was accepted")
	}
}

func TestConfigRejectsServerWithoutExplicitPort(t *testing.T) {
	c := Config{Server: "edge.example", Workflow: "workflow.yaml", Plan: "plan.yaml", AdminKey: SecretSource{Env: "RAIDTEST_TEST_ADMIN"}}
	if err := c.Validate(); err == nil {
		t.Fatal("server without port was accepted")
	}
}

func TestConfigAcceptsPairedSuiteWithoutOpenAI(t *testing.T) {
	c := Config{
		Server: "edge.example:9821", Suite: "suite.yaml",
		AdminKey: SecretSource{Env: "RAIDTEST_TEST_ADMIN"},
	}
	if err := c.Validate(); err != nil {
		t.Fatal(err)
	}
	if c.Workflow != "" || c.Plan != "" {
		t.Fatalf("suite mode unexpectedly selected legacy inputs: %#v", c)
	}
	c.AgentModel = "external-agent"
	if err := c.Validate(); err == nil {
		t.Fatal("suite mode accepted an external OpenAI model")
	}
}

func errorString(err error) string {
	if err == nil {
		return ""
	}
	return err.Error()
}
