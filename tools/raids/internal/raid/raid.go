// Package raid loads and validates workflows/<raid>/raid.json package manifests
// and resolves the catalog resources a RuntimeProfile may bind them to.
package raid

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"gopkg.in/yaml.v3"
)

const Schema = "raids.raid/v1alpha1"

var idPattern = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,62}$`)

// Slot is one model or voice parameter the installer must fill.
type Slot struct {
	Kind        string `json:"kind,omitempty"`
	Role        string `json:"role"`
	Language    string `json:"language,omitempty"`
	Description string `json:"description,omitempty"`
}

// Parameters groups the alias slots declared by an implementation or tester.
type Parameters struct {
	Models map[string]Slot `json:"models"`
	Voices map[string]Slot `json:"voices"`
}

// Implementation is one engine-specific Workflow of a raid.
type Implementation struct {
	File       string     `json:"file"`
	WorkflowID string     `json:"workflow_id"`
	Driver     string     `json:"driver"`
	Input      []string   `json:"input"`
	Memory     *Memory    `json:"memory,omitempty"`
	Parameters Parameters `json:"parameters"`
}

// Memory is the MemoryLayout an implementation requires.
type Memory struct {
	LayoutID string `json:"layout_id"`
}

// Tester is the raid's shared relay Tester Workflow.
type Tester struct {
	File       string     `json:"file"`
	WorkflowID string     `json:"workflow_id"`
	Driver     string     `json:"driver"`
	Parameters Parameters `json:"parameters"`
}

// Raid is the package manifest.
type Raid struct {
	Schema          string                    `json:"schema"`
	ID              string                    `json:"id"`
	Category        string                    `json:"category"`
	Title           map[string]string         `json:"title"`
	Summary         map[string]string         `json:"summary"`
	Implementations map[string]Implementation `json:"implementations"`
	Tester          *Tester                   `json:"tester,omitempty"`

	Dir string `json:"-"`
}

// FindRoot walks up from start until it finds the Raids repository root.
func FindRoot(start string) (string, error) {
	current, err := filepath.Abs(start)
	if err != nil {
		return "", err
	}
	for {
		if isDir(filepath.Join(current, "workflows")) && isDir(filepath.Join(current, "runtime-profiles")) && isDir(filepath.Join(current, "models")) {
			return current, nil
		}
		parent := filepath.Dir(current)
		if parent == current {
			return "", fmt.Errorf("cannot find the Raids repository root from %s", start)
		}
		current = parent
	}
}

func isDir(path string) bool {
	info, err := os.Stat(path)
	return err == nil && info.IsDir()
}

// Load reads workflows/<id>/raid.json under root.
func Load(root, id string) (*Raid, error) {
	if !idPattern.MatchString(id) {
		return nil, fmt.Errorf("invalid raid id %q", id)
	}
	dir := filepath.Join(root, "workflows", id)
	data, err := os.ReadFile(filepath.Join(dir, "raid.json"))
	if err != nil {
		return nil, err
	}
	var r Raid
	decoder := json.NewDecoder(strings.NewReader(string(data)))
	if err := decoder.Decode(&r); err != nil {
		return nil, fmt.Errorf("decode %s: %w", filepath.Join(dir, "raid.json"), err)
	}
	r.Dir = dir
	if err := r.Validate(); err != nil {
		return nil, err
	}
	return &r, nil
}

// List returns every raid id that has a raid.json.
func List(root string) ([]string, error) {
	entries, err := os.ReadDir(filepath.Join(root, "workflows"))
	if err != nil {
		return nil, err
	}
	var ids []string
	for _, entry := range entries {
		if entry.IsDir() {
			if _, err := os.Stat(filepath.Join(root, "workflows", entry.Name(), "raid.json")); err == nil {
				ids = append(ids, entry.Name())
			}
		}
	}
	sort.Strings(ids)
	return ids, nil
}

// Validate checks the manifest shape and that referenced files exist.
func (r *Raid) Validate() error {
	if r.Schema != Schema {
		return fmt.Errorf("%s: schema must be %q", r.ID, Schema)
	}
	if !idPattern.MatchString(r.ID) || filepath.Base(r.Dir) != r.ID {
		return fmt.Errorf("raid id %q must match its directory %s", r.ID, r.Dir)
	}
	if len(r.Implementations) == 0 {
		return fmt.Errorf("%s: at least one implementation is required", r.ID)
	}
	for name, impl := range r.Implementations {
		if !idPattern.MatchString(name) {
			return fmt.Errorf("%s: invalid implementation name %q", r.ID, name)
		}
		if err := r.checkWorkflowFile(impl.File, impl.WorkflowID); err != nil {
			return fmt.Errorf("%s/%s: %w", r.ID, name, err)
		}
		if err := validateParameters(impl.Parameters, impl.WorkflowID); err != nil {
			return fmt.Errorf("%s/%s: %w", r.ID, name, err)
		}
	}
	if r.Tester != nil {
		if err := r.checkWorkflowFile(r.Tester.File, r.Tester.WorkflowID); err != nil {
			return fmt.Errorf("%s tester: %w", r.ID, err)
		}
		if r.Tester.WorkflowID != r.ID+"-test" {
			return fmt.Errorf("%s tester id must be %s-test, got %s", r.ID, r.ID, r.Tester.WorkflowID)
		}
		if err := validateParameters(r.Tester.Parameters, r.Tester.WorkflowID); err != nil {
			return fmt.Errorf("%s tester: %w", r.ID, err)
		}
	}
	return nil
}

func validateParameters(p Parameters, workflowID string) error {
	for alias := range p.Models {
		if !strings.HasPrefix(alias, workflowID+".") {
			return fmt.Errorf("model slot %q must be namespaced by %s.", alias, workflowID)
		}
	}
	for alias := range p.Voices {
		if !strings.HasPrefix(alias, workflowID+".") {
			return fmt.Errorf("voice slot %q must be namespaced by %s.", alias, workflowID)
		}
	}
	return nil
}

func (r *Raid) checkWorkflowFile(file, workflowID string) error {
	if file == "" || strings.Contains(file, "/") {
		return fmt.Errorf("file %q must be a bare file name inside the raid directory", file)
	}
	path := filepath.Join(r.Dir, file)
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var doc struct {
		Kind     string `yaml:"kind"`
		Metadata struct {
			ID string `yaml:"id"`
		} `yaml:"metadata"`
	}
	if err := yaml.Unmarshal(data, &doc); err != nil {
		return fmt.Errorf("decode %s: %w", path, err)
	}
	if doc.Kind != "Workflow" || doc.Metadata.ID != workflowID {
		return fmt.Errorf("%s must be Workflow/%s, got %s/%s", file, workflowID, doc.Kind, doc.Metadata.ID)
	}
	return nil
}

// Catalog indexes the applyable resource IDs under the repository.
type Catalog struct {
	Models        map[string]bool
	Voices        map[string]bool
	MemoryLayouts map[string]bool
}

// LoadCatalog scans models/, voices/, and memory-layouts/ for metadata.id values.
func LoadCatalog(root string) (*Catalog, error) {
	c := &Catalog{Models: map[string]bool{}, Voices: map[string]bool{}, MemoryLayouts: map[string]bool{}}
	for dir, target := range map[string]map[string]bool{"models": c.Models, "voices": c.Voices, "memory-layouts": c.MemoryLayouts} {
		err := filepath.WalkDir(filepath.Join(root, dir), func(path string, entry fs.DirEntry, walkErr error) error {
			if walkErr != nil {
				return walkErr
			}
			if entry.IsDir() || filepath.Ext(path) != ".yaml" {
				return nil
			}
			data, err := os.ReadFile(path)
			if err != nil {
				return err
			}
			var doc struct {
				Metadata struct {
					ID string `yaml:"id"`
				} `yaml:"metadata"`
			}
			if err := yaml.Unmarshal(data, &doc); err != nil {
				return fmt.Errorf("decode %s: %w", path, err)
			}
			if doc.Metadata.ID != "" {
				target[doc.Metadata.ID] = true
			}
			return nil
		})
		if err != nil && !errors.Is(err, fs.ErrNotExist) {
			return nil, err
		}
	}
	return c, nil
}
