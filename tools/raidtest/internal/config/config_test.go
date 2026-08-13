package config

import (
	"os"
	"strings"
	"testing"
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
	if c.RuntimeProfile != "default" || c.PeerServer != c.Server || c.OpenAIBaseURL != "http://edge.example:9821/openai/v1" {
		t.Fatalf("unexpected defaults: %#v", c)
	}
	if _, ok := c.Redacted()["admin_key"]; ok {
		t.Fatal("redacted config contains secret field")
	}
	_ = os.Unsetenv("RAIDTEST_TEST_ADMIN")
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

func errorString(err error) string {
	if err == nil {
		return ""
	}
	return err.Error()
}
