package profile

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"

	"github.com/GizClaw/raids/tools/raids/internal/raid"
)

// PlanSchema identifies a profile generation plan.
const PlanSchema = "raids.profile/v1alpha1"

// Plan regenerates one RuntimeProfile: a base document that holds everything
// raid packages do not own, plus the ordered installs that add the raids.
type Plan struct {
	Schema   string    `yaml:"apiVersion"`
	Base     string    `yaml:"base"`   // relative to the plan file
	Output   string    `yaml:"output"` // relative to the plan file
	Installs []Install `yaml:"installs"`
}

// Install is one `raids install` invocation inside a Plan.
type Install struct {
	Raid             string            `yaml:"raid"`
	Implementation   string            `yaml:"impl"`
	Collection       string            `yaml:"collection"`
	Name             string            `yaml:"name,omitempty"`
	Tester           bool              `yaml:"tester,omitempty"`
	TesterCollection string            `yaml:"tester_collection,omitempty"`
	Set              map[string]string `yaml:"set,omitempty"`  // model.<alias> / voice.<alias> -> resource id
	I18n             I18n              `yaml:"i18n,omitempty"` // overrides when the raid.json defaults are not wanted
	TesterI18n       I18n              `yaml:"tester_i18n,omitempty"`
}

// LoadPlan reads a plan file.
func LoadPlan(path string) (*Plan, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var plan Plan
	if err := yaml.Unmarshal(data, &plan); err != nil {
		return nil, fmt.Errorf("decode %s: %w", path, err)
	}
	if plan.Schema != PlanSchema {
		return nil, fmt.Errorf("%s: apiVersion must be %s", path, PlanSchema)
	}
	if plan.Base == "" || plan.Output == "" {
		return nil, fmt.Errorf("%s: base and output are required", path)
	}
	return &plan, nil
}

// Generate applies the plan's installs to its base and returns the rendered
// profile bytes; callers write them to plan.Output or compare them.
func Generate(root string, planPath string, plan *Plan, catalog *raid.Catalog) ([]byte, error) {
	dir := filepath.Dir(planPath)
	doc, err := Load(filepath.Join(dir, plan.Base))
	if err != nil {
		return nil, err
	}
	for index, install := range plan.Installs {
		r, err := raid.Load(root, install.Raid)
		if err != nil {
			return nil, fmt.Errorf("install %d: %w", index, err)
		}
		models, voices := map[string]string{}, map[string]string{}
		for key, value := range install.Set {
			switch {
			case strings.HasPrefix(key, "model."):
				models[strings.TrimPrefix(key, "model.")] = value
			case strings.HasPrefix(key, "voice."):
				voices[strings.TrimPrefix(key, "voice.")] = value
			default:
				return nil, fmt.Errorf("install %d (%s/%s): set key %q must start with model. or voice.", index, install.Raid, install.Implementation, key)
			}
		}
		opts := Options{
			Implementation: install.Implementation, Collection: install.Collection, Name: install.Name,
			Tester: install.Tester, TesterColl: install.TesterCollection,
			Models: models, Voices: voices, I18n: install.I18n, TesterI18n: install.TesterI18n,
		}
		if err := doc.Install(r, catalog, opts); err != nil {
			return nil, fmt.Errorf("install %d (%s/%s into %s): %w", index, install.Raid, install.Implementation, install.Collection, err)
		}
	}
	return doc.Bytes()
}
