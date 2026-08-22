package profile

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"gopkg.in/yaml.v3"

	"github.com/GizClaw/raids/tools/raids/internal/raid"
)

const fixtureProfile = `---
apiVersion: gizclaw.admin/v1alpha1
kind: RuntimeProfile
metadata:
  id: fixture
spec:
  workflows:
    system:
      pet: pet-care
    collections:
      role-play: {}
  resources:
    models:
      asr:
        resource_id: volc-bigasr-sauc
        i18n: {en: {display_name: Speech Recognition}, zh-CN: {display_name: 语音识别}}
    memories:
      story-teller: {layout_id: story-teller, driver: flowcraft, connection: {type: flowcraft_bbh}}
`

func repoRoot(t *testing.T) string {
	t.Helper()
	root, err := raid.FindRoot(".")
	if err != nil {
		t.Skip("repository root not found:", err)
	}
	return root
}

func writeFixture(t *testing.T) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "fixture.yaml")
	if err := os.WriteFile(path, []byte(fixtureProfile), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestInstallUninstallRoundTrip(t *testing.T) {
	root := repoRoot(t)
	catalog, err := raid.LoadCatalog(root)
	if err != nil {
		t.Fatal(err)
	}
	r, err := raid.Load(root, "story-aesop")
	if err != nil {
		t.Fatal(err)
	}
	path := writeFixture(t)
	doc, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	opts := Options{
		Implementation: "flowcraft", Collection: "story-teller", Tester: true,
		Models: map[string]string{"flowcraft-story-aesop.model": "doubao-seed-2-0-lite", "story-aesop-test.model": "doubao-seed-2-0-lite"},
		Voices: map[string]string{"flowcraft-story-aesop.storyteller": "volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts"},
	}
	if err := doc.Install(r, catalog, opts); err != nil {
		t.Fatal(err)
	}
	if err := doc.Save(); err != nil {
		t.Fatal(err)
	}
	data, _ := os.ReadFile(path)
	var parsed struct {
		Spec struct {
			Workflows struct {
				Collections map[string]map[string]struct {
					ResourceID string                       `yaml:"resource_id"`
					I18n       map[string]map[string]string `yaml:"i18n"`
				} `yaml:"collections"`
			} `yaml:"workflows"`
			Resources struct {
				Models map[string]struct {
					ResourceID string `yaml:"resource_id"`
				} `yaml:"models"`
				Voices map[string]struct {
					ResourceID string `yaml:"resource_id"`
				} `yaml:"voices"`
			} `yaml:"resources"`
		} `yaml:"spec"`
	}
	if err := yaml.Unmarshal(data, &parsed); err != nil {
		t.Fatal(err)
	}
	binding := parsed.Spec.Workflows.Collections["story-teller"]["flowcraft-story-aesop"]
	if binding.ResourceID != "flowcraft-story-aesop" || binding.I18n["zh-CN"]["display_name"] == "" {
		t.Fatalf("workflow binding not written: %+v", binding)
	}
	if parsed.Spec.Workflows.Collections["raidtest-testers"]["story-aesop-test"].ResourceID != "story-aesop-test" {
		t.Fatal("tester binding not written")
	}
	if parsed.Spec.Resources.Models["flowcraft-story-aesop.model"].ResourceID != "doubao-seed-2-0-lite" {
		t.Fatal("model alias not written")
	}
	if parsed.Spec.Resources.Voices["flowcraft-story-aesop.storyteller"].ResourceID == "" {
		t.Fatal("voice alias not written")
	}
	if parsed.Spec.Resources.Models["asr"].ResourceID != "volc-bigasr-sauc" {
		t.Fatal("unrelated alias was disturbed")
	}
	if !strings.Contains(string(data), "role-play:") {
		t.Fatal("unrelated collection was removed")
	}

	// Idempotent re-install keeps one binding and the same content.
	doc2, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := doc2.Install(r, catalog, opts); err != nil {
		t.Fatal(err)
	}
	again, err := doc2.Bytes()
	if err != nil {
		t.Fatal(err)
	}
	if string(again) != string(data) {
		t.Fatalf("re-install is not idempotent:\n%s\n---\n%s", data, again)
	}

	installed, err := doc2.Inspect(root, catalog)
	if err != nil {
		t.Fatal(err)
	}
	if len(installed) != 1 || installed[0].Raid != "story-aesop" || len(installed[0].TesterBindings) == 0 || len(installed[0].Missing) != 0 {
		t.Fatalf("unexpected inspect result: %+v", installed)
	}

	if err := doc2.Uninstall(r, opts); err != nil {
		t.Fatal(err)
	}
	after, err := doc2.Bytes()
	if err != nil {
		t.Fatal(err)
	}
	for _, needle := range []string{"flowcraft-story-aesop", "story-aesop-test"} {
		if strings.Contains(string(after), needle) {
			t.Fatalf("uninstall left %q behind:\n%s", needle, after)
		}
	}
	if !strings.Contains(string(after), "asr:") || !strings.Contains(string(after), "story-teller:") {
		t.Fatal("uninstall removed unrelated content")
	}
}

func TestInstallRejectsMissingSlotsAndUnknownResources(t *testing.T) {
	root := repoRoot(t)
	catalog, err := raid.LoadCatalog(root)
	if err != nil {
		t.Fatal(err)
	}
	r, err := raid.Load(root, "story-aesop")
	if err != nil {
		t.Fatal(err)
	}
	doc, err := Load(writeFixture(t))
	if err != nil {
		t.Fatal(err)
	}
	err = doc.Install(r, catalog, Options{Implementation: "eino", Collection: "story-teller"})
	if err == nil || !strings.Contains(err.Error(), "missing slot values") {
		t.Fatalf("expected missing slot error, got %v", err)
	}
	err = doc.Install(r, catalog, Options{Implementation: "eino", Collection: "story-teller", Models: map[string]string{"eino-story-aesop.model": "no-such-model"}})
	if err == nil || !strings.Contains(err.Error(), "not in models/") {
		t.Fatalf("expected unknown model error, got %v", err)
	}
	err = doc.Install(r, catalog, Options{Implementation: "nope", Collection: "story-teller"})
	if err == nil || !strings.Contains(err.Error(), "no implementation") {
		t.Fatalf("expected unknown implementation error, got %v", err)
	}
}

func TestRepositoryProfilesAreComplete(t *testing.T) {
	root := repoRoot(t)
	catalog, err := raid.LoadCatalog(root)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"testing.yaml", "default.yaml"} {
		doc, err := Load(filepath.Join(root, "runtime-profiles", name))
		if err != nil {
			t.Fatal(err)
		}
		installed, err := doc.Inspect(root, catalog)
		if err != nil {
			t.Fatal(err)
		}
		if len(installed) == 0 {
			t.Fatalf("%s binds no raid implementations", name)
		}
		for _, entry := range installed {
			if len(entry.Missing) > 0 || len(entry.Unknown) > 0 {
				t.Errorf("%s: %s/%s incomplete: missing=%v unknown=%v", name, entry.Raid, entry.Implementation, entry.Missing, entry.Unknown)
			}
		}
	}
}

func TestAllRaidManifestsValidate(t *testing.T) {
	root := repoRoot(t)
	ids, err := raid.List(root)
	if err != nil {
		t.Fatal(err)
	}
	if len(ids) < 30 {
		t.Fatalf("expected the catalog raids, found %d", len(ids))
	}
	for _, id := range ids {
		if _, err := raid.Load(root, id); err != nil {
			t.Error(err)
		}
	}
}

func TestUninstallKeepsSharedTesterWhileAnotherImplementationRemains(t *testing.T) {
	root := repoRoot(t)
	catalog, err := raid.LoadCatalog(root)
	if err != nil {
		t.Fatal(err)
	}
	r, err := raid.Load(root, "story-aesop")
	if err != nil {
		t.Fatal(err)
	}
	doc, err := Load(writeFixture(t))
	if err != nil {
		t.Fatal(err)
	}
	models := map[string]string{"flowcraft-story-aesop.model": "doubao-seed-2-0-lite", "eino-story-aesop.model": "doubao-seed-2-0-lite", "story-aesop-test.model": "doubao-seed-2-0-lite"}
	voices := map[string]string{"flowcraft-story-aesop.storyteller": "volc-tenant:volc-cn-beijing:zh_female_shaoergushi_mars_bigtts"}
	if err := doc.Install(r, catalog, Options{Implementation: "flowcraft", Collection: "story-teller", Tester: true, Models: models, Voices: voices}); err != nil {
		t.Fatal(err)
	}
	if err := doc.Install(r, catalog, Options{Implementation: "eino", Collection: "story-teller", Tester: true, Models: models}); err != nil {
		t.Fatal(err)
	}
	if err := doc.Uninstall(r, Options{Implementation: "flowcraft", Tester: true}); err != nil {
		t.Fatal(err)
	}
	if len(doc.bindingsOf("story-aesop-test")) != 1 || mapGet(doc.path("spec", "resources", "models"), "story-aesop-test.model") == nil {
		t.Fatal("shared tester was removed while eino remained installed")
	}
	if len(doc.bindingsOf("flowcraft-story-aesop")) != 0 {
		t.Fatal("flowcraft binding survived uninstall")
	}
	if err := doc.Uninstall(r, Options{Implementation: "eino", Tester: true}); err != nil {
		t.Fatal(err)
	}
	if len(doc.bindingsOf("story-aesop-test")) != 0 || mapGet(doc.path("spec", "resources", "models"), "story-aesop-test.model") != nil {
		t.Fatal("shared tester should be removed with the last implementation")
	}
}
