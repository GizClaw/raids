package suite

import (
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestLoadPR61PairedSuite(t *testing.T) {
	path := filepath.Join("..", "..", "suites", "pr61-paired.yaml")
	loaded, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	if loaded.SchemaVersion != SchemaVersion || len(loaded.Pairs) != 14 {
		t.Fatalf("suite=%#v", loaded)
	}
	if loaded.Timing.FirstResponse != 6*time.Second || loaded.Timing.TotalResponse != 90*time.Second {
		t.Fatalf("timing=%#v", loaded.Timing)
	}
	murderRepeats := 0
	for _, pair := range loaded.Pairs {
		if pair.TargetWorkflowID == "flowcraft-murder-mystery" {
			murderRepeats = pair.Repeats
			if pair.ExpectedTargetResponses != 26 {
				t.Fatalf("murder responses=%d", pair.ExpectedTargetResponses)
			}
			if len(pair.Reloads) != 1 || pair.Reloads[0].BeforeResponse != 20 {
				t.Fatalf("murder reloads=%#v", pair.Reloads)
			}
		}
	}
	if murderRepeats != 5 {
		t.Fatalf("murder repeats=%d", murderRepeats)
	}
}

func TestValidateRejectsPairIDThatDoesNotMatchTarget(t *testing.T) {
	loaded := loadValidSuite(t)
	loaded.Pairs[0].ID = "different-pair-id"
	assertValidationError(t, loaded, "id must match target workflow")
}

func TestValidateRejectsRecursiveTesterTarget(t *testing.T) {
	loaded := loadValidSuite(t)
	loaded.Pairs[0].ID = "recursive-test"
	loaded.Pairs[0].TargetWorkflowID = "recursive-test"
	loaded.Pairs[0].TesterWorkflowID = "recursive-test-test"
	assertValidationError(t, loaded, "target workflow cannot be a tester")
}

func TestValidateRejectsDuplicateTargetsAndTesters(t *testing.T) {
	tests := []struct {
		name    string
		mutate  func(*Suite)
		message string
	}{
		{
			name: "target",
			mutate: func(s *Suite) {
				s.Pairs[1].TargetWorkflowID = s.Pairs[0].TargetWorkflowID
			},
			message: "duplicate target workflow",
		},
		{
			name: "tester",
			mutate: func(s *Suite) {
				s.Pairs[1].TesterWorkflowID = s.Pairs[0].TesterWorkflowID
			},
			message: "duplicate tester workflow",
		},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			loaded := loadValidSuite(t)
			test.mutate(&loaded)
			assertValidationError(t, loaded, test.message)
		})
	}
}

func loadValidSuite(t *testing.T) Suite {
	t.Helper()
	loaded, err := Load(filepath.Join("..", "..", "suites", "pr61-paired.yaml"))
	if err != nil {
		t.Fatal(err)
	}
	loaded.Pairs = append([]Pair(nil), loaded.Pairs...)
	return loaded
}

func assertValidationError(t *testing.T, loaded Suite, message string) {
	t.Helper()
	err := loaded.Validate()
	if err == nil || !strings.Contains(err.Error(), message) {
		t.Fatalf("error=%v want substring %q", err, message)
	}
}
