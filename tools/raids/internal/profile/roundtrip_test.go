package profile

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/GizClaw/raids/tools/raids/internal/raid"
)

// TestCommittedProfilesRoundTrip proves the tool can reproduce the committed
// RuntimeProfiles: every raid implementation is uninstalled and reinstalled
// with the values recorded from the profile, and the result must be identical.
func TestCommittedProfilesRoundTrip(t *testing.T) {
	root := repoRoot(t)
	catalog, err := raid.LoadCatalog(root)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"testing.yaml", "default.yaml"} {
		t.Run(name, func(t *testing.T) {
			source := filepath.Join(root, "runtime-profiles", name)
			doc, err := Load(source)
			if err != nil {
				t.Fatal(err)
			}
			original, err := doc.Bytes()
			if err != nil {
				t.Fatal(err)
			}
			raw, _ := os.ReadFile(source)
			if string(raw) != string(original) {
				t.Fatalf("%s: yaml.v3 rendering does not reproduce the committed file verbatim", name)
			}
			installed, err := doc.Inspect(root, catalog)
			if err != nil {
				t.Fatal(err)
			}
			if len(installed) < 30 {
				t.Fatalf("%s: expected the catalog raids, found %d implementations", name, len(installed))
			}
			for _, entry := range installed {
				r, err := raid.Load(root, entry.Raid)
				if err != nil {
					t.Fatal(err)
				}
				if err := doc.Uninstall(r, Options{Implementation: entry.Implementation, Tester: len(entry.TesterBindings) > 0}); err != nil {
					t.Fatal(err)
				}
				for index, binding := range entry.Bindings {
					opts := Options{
						Implementation: entry.Implementation, Collection: binding.Collection, Name: binding.Key,
						Models: entry.Models, Voices: entry.Voices, I18n: binding.I18n,
					}
					if index == 0 && len(entry.TesterBindings) > 0 {
						opts.Tester = true
						opts.TesterColl = entry.TesterBindings[0].Collection
						opts.TesterI18n = entry.TesterBindings[0].I18n
					}
					if err := doc.Install(r, catalog, opts); err != nil {
						t.Fatalf("%s: reinstall %s/%s into %s/%s: %v", name, entry.Raid, entry.Implementation, binding.Collection, binding.Key, err)
					}
				}
			}
			// Re-installation appends bindings at the end of each mapping, so
			// compare the parsed structure rather than byte order.
			after, err := doc.Bytes()
			if err != nil {
				t.Fatal(err)
			}
			if !sameYAML(t, stripAliasText(original), stripAliasText(after)) {
				t.Fatalf("%s: uninstall+install round trip changed the profile", name)
			}
		})
	}
}
