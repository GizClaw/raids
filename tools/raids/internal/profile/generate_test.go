package profile

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/GizClaw/raids/tools/raids/internal/raid"
)

// TestPlansRegenerateCommittedProfiles proves the committed RuntimeProfiles
// are exactly what their plans generate.
func TestPlansRegenerateCommittedProfiles(t *testing.T) {
	root := repoRoot(t)
	catalog, err := raid.LoadCatalog(root)
	if err != nil {
		t.Fatal(err)
	}
	plans, err := filepath.Glob(filepath.Join(root, "profile-plans", "*.plan.yaml"))
	if err != nil || len(plans) == 0 {
		t.Fatalf("no plans found: %v", err)
	}
	for _, planPath := range plans {
		plan, err := LoadPlan(planPath)
		if err != nil {
			t.Fatal(err)
		}
		generated, err := Generate(root, planPath, plan, catalog)
		if err != nil {
			t.Fatalf("%s: %v", planPath, err)
		}
		committed, err := os.ReadFile(filepath.Join(filepath.Dir(planPath), plan.Output))
		if err != nil {
			t.Fatal(err)
		}
		if string(generated) != string(committed) {
			t.Errorf("%s: committed %s is stale; run make build-profiles", filepath.Base(planPath), plan.Output)
		}
	}
}
