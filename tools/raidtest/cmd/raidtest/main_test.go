package main

import (
	"bytes"
	"testing"
)

func TestParseFlagsAcceptsOnlySecretSources(t *testing.T) {
	t.Setenv("RAIDTEST_ADMIN", "private")
	var stderr bytes.Buffer
	cfg, err := parseFlags([]string{
		"--server", "edge.example:9821",
		"--workflow", "workflow.yaml",
		"--plan", "plan.yaml",
		"--admin-private-key-env", "RAIDTEST_ADMIN",
	}, &stderr)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.AdminKey.Env != "RAIDTEST_ADMIN" || cfg.OpenAIBaseURL != "http://edge.example:9821/openai/v1" {
		t.Fatalf("config=%#v", cfg.Redacted())
	}
	stderr.Reset()
	if _, err := parseFlags([]string{"--admin-private-key", "raw-secret"}, &stderr); err == nil {
		t.Fatal("raw private-key argv flag was accepted")
	}
}

func TestDriverMatchesPublicWorkflowFamilies(t *testing.T) {
	for workflow, planned := range map[string]string{
		"flowcraft":       "flowcraft",
		"doubao-realtime": "realtime",
		"ast-translate":   "translate",
		"pet":             "pet",
	} {
		if !driverMatches(workflow, planned) {
			t.Fatalf("driver %q did not match %q", workflow, planned)
		}
	}
	if driverMatches("flowcraft", "translate") {
		t.Fatal("mismatched driver was accepted")
	}
}
