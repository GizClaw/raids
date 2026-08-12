package catalog

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strings"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
	"gopkg.in/yaml.v3"
)

type Metadata struct {
	ID string `json:"id"`
}

type Resource[T any] struct {
	APIVersion string   `json:"apiVersion"`
	Kind       string   `json:"kind"`
	Metadata   Metadata `json:"metadata"`
	Spec       T        `json:"spec"`
}

type Workflow struct {
	Source Resource[apitypes.WorkflowSpec]
	Driver string
	Digest string
}

type MemoryLayout struct {
	Source Resource[apitypes.MemoryLayoutSpec]
	Digest string
}

type RuntimeProfile struct {
	Source Resource[apitypes.RuntimeProfileSpec]
	Digest string
}

func RuntimeProfileFrom(id string, spec apitypes.RuntimeProfileSpec) RuntimeProfile {
	r := Resource[apitypes.RuntimeProfileSpec]{APIVersion: "gizclaw.admin/v1alpha1", Kind: "RuntimeProfile", Metadata: Metadata{ID: id}, Spec: spec}
	return RuntimeProfile{Source: r, Digest: Digest(r)}
}

func readYAMLJSON(path string, out any) ([]byte, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var raw any
	if err := yaml.Unmarshal(b, &raw); err != nil {
		return nil, fmt.Errorf("decode %s: %w", path, err)
	}
	j, err := json.Marshal(raw)
	if err != nil {
		return nil, err
	}
	decoder := json.NewDecoder(bytes.NewReader(j))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(out); err != nil {
		return nil, fmt.Errorf("decode typed %s: %w", path, err)
	}
	return j, nil
}

func LoadWorkflow(path string) (Workflow, error) {
	var r Resource[apitypes.WorkflowSpec]
	j, err := readYAMLJSON(path, &r)
	if err != nil {
		return Workflow{}, err
	}
	if r.APIVersion != "gizclaw.admin/v1alpha1" || r.Kind != "Workflow" || strings.TrimSpace(r.Metadata.ID) == "" {
		return Workflow{}, errors.New("expected Workflow with metadata.id")
	}
	var envelope map[string]any
	if err := json.Unmarshal(j, &envelope); err != nil {
		return Workflow{}, err
	}
	spec, _ := envelope["spec"].(map[string]any)
	driver, _ := spec["driver"].(string)
	switch driver {
	case "flowcraft", "doubao-realtime", "ast-translate", "pet":
	default:
		return Workflow{}, fmt.Errorf("unsupported Workflow driver %q", driver)
	}
	return Workflow{Source: r, Driver: driver, Digest: digestJSON(j)}, nil
}

func LoadMemoryLayout(path string) (MemoryLayout, error) {
	var r Resource[apitypes.MemoryLayoutSpec]
	j, err := readYAMLJSON(path, &r)
	if err != nil {
		return MemoryLayout{}, err
	}
	if r.APIVersion != "gizclaw.admin/v1alpha1" || r.Kind != "MemoryLayout" || strings.TrimSpace(r.Metadata.ID) == "" {
		return MemoryLayout{}, errors.New("expected MemoryLayout with metadata.id")
	}
	return MemoryLayout{Source: r, Digest: digestJSON(j)}, nil
}

func LoadRuntimeProfile(path string) (RuntimeProfile, error) {
	var r Resource[apitypes.RuntimeProfileSpec]
	j, err := readYAMLJSON(path, &r)
	if err != nil {
		return RuntimeProfile{}, err
	}
	if r.APIVersion != "gizclaw.admin/v1alpha1" || r.Kind != "RuntimeProfile" || strings.TrimSpace(r.Metadata.ID) == "" {
		return RuntimeProfile{}, errors.New("expected RuntimeProfile with metadata.id")
	}
	return RuntimeProfile{Source: r, Digest: digestJSON(j)}, nil
}

func digestJSON(value []byte) string {
	var normalized any
	if json.Unmarshal(value, &normalized) == nil {
		value, _ = json.Marshal(normalized)
	}
	sum := sha256.Sum256(value)
	return hex.EncodeToString(sum[:])
}

func Digest(value any) string {
	b, _ := json.Marshal(value)
	return digestJSON(b)
}

type Closure struct {
	Workflow      Workflow
	WorkflowID    string
	Profile       RuntimeProfile
	ProfileID     string
	MemoryLayouts []MemoryLayout
	MemoryIDs     map[string]string
}

func BuildClosure(workflow Workflow, base RuntimeProfile, layouts []MemoryLayout, runID string) (Closure, error) {
	runID = compactID(runID)
	if runID == "" {
		return Closure{}, errors.New("run ID is required")
	}
	wid := shadowID(workflow.Source.Metadata.ID, runID)
	pid := shadowID(base.Source.Metadata.ID, runID)
	if len(layouts) > 0 {
		var aliases []string
		if workflow.Source.Spec.Memory != nil {
			aliases = append(aliases, strings.TrimSpace(string(*workflow.Source.Spec.Memory)))
		}
		if workflow.Source.Spec.Pet != nil && workflow.Source.Spec.Pet.Memory != nil {
			aliases = append(aliases, strings.TrimSpace(string(*workflow.Source.Spec.Pet.Memory)))
		}
		if len(aliases) == 0 {
			return Closure{}, fmt.Errorf("Workflow %q does not select a MemoryLayout alias", workflow.Source.Metadata.ID)
		}
		if base.Source.Spec.Resources.Memories == nil {
			return Closure{}, fmt.Errorf("RuntimeProfile does not bind Workflow memory aliases %q", aliases)
		}
		selectedLayouts := map[string]bool{}
		for _, alias := range aliases {
			if alias == "" {
				continue
			}
			binding, ok := (*base.Source.Spec.Resources.Memories)[alias]
			if !ok {
				return Closure{}, fmt.Errorf("RuntimeProfile does not bind Workflow memory alias %q", alias)
			}
			selectedLayouts[binding.LayoutId] = true
		}
		for _, layout := range layouts {
			if !selectedLayouts[layout.Source.Metadata.ID] {
				return Closure{}, fmt.Errorf("MemoryLayout %q is not selected by Workflow %q", layout.Source.Metadata.ID, workflow.Source.Metadata.ID)
			}
		}
	}
	memoryIDs := map[string]string{}
	shadowMemoryIDs := map[string]string{}
	for _, layout := range layouts {
		id := layout.Source.Metadata.ID
		if _, exists := memoryIDs[id]; exists {
			return Closure{}, fmt.Errorf("duplicate MemoryLayout %q", id)
		}
		shadow := shadowID(id, runID)
		if other, exists := shadowMemoryIDs[shadow]; exists {
			return Closure{}, fmt.Errorf("MemoryLayouts %q and %q produce the same shadow ID %q", other, id, shadow)
		}
		memoryIDs[id] = shadow
		shadowMemoryIDs[shadow] = id
	}

	b, err := json.Marshal(base.Source.Spec)
	if err != nil {
		return Closure{}, err
	}
	var generic any
	if err := json.Unmarshal(b, &generic); err != nil {
		return Closure{}, err
	}
	replacedWorkflow := 0
	replacedMemory := map[string]int{}
	root, _ := generic.(map[string]any)
	workflows, _ := root["workflows"].(map[string]any)
	if system, ok := workflows["system"].(map[string]any); ok {
		for key, raw := range system {
			if value, ok := raw.(string); ok && value == workflow.Source.Metadata.ID {
				system[key] = wid
				replacedWorkflow++
			}
		}
	}
	if collections, ok := workflows["collections"].(map[string]any); ok {
		for _, rawCollection := range collections {
			collection, _ := rawCollection.(map[string]any)
			for _, rawBinding := range collection {
				binding, _ := rawBinding.(map[string]any)
				if value, _ := binding["resource_id"].(string); value == workflow.Source.Metadata.ID {
					binding["resource_id"] = wid
					replacedWorkflow++
				}
			}
		}
	}
	resources, _ := root["resources"].(map[string]any)
	if memories, ok := resources["memories"].(map[string]any); ok {
		for _, rawBinding := range memories {
			binding, _ := rawBinding.(map[string]any)
			value, _ := binding["layout_id"].(string)
			if replacement, found := memoryIDs[value]; found {
				binding["layout_id"] = replacement
				replacedMemory[value]++
			}
		}
	}
	if replacedWorkflow == 0 {
		return Closure{}, fmt.Errorf("RuntimeProfile does not bind Workflow %q", workflow.Source.Metadata.ID)
	}
	for id := range memoryIDs {
		if replacedMemory[id] == 0 {
			return Closure{}, fmt.Errorf("RuntimeProfile does not bind MemoryLayout %q", id)
		}
	}
	b, err = json.Marshal(generic)
	if err != nil {
		return Closure{}, err
	}
	var spec apitypes.RuntimeProfileSpec
	if err := json.Unmarshal(b, &spec); err != nil {
		return Closure{}, fmt.Errorf("decode rewritten RuntimeProfile: %w", err)
	}
	base.Source.Metadata.ID = pid
	base.Source.Spec = spec
	base.Digest = Digest(base.Source)
	return Closure{Workflow: workflow, WorkflowID: wid, Profile: base, ProfileID: pid, MemoryLayouts: layouts, MemoryIDs: memoryIDs}, nil
}

func shadowID(source, runID string) string {
	const max = 63
	prefix := "raidtest-"
	suffix := "-" + compactID(runID)
	source = compactID(source)
	available := max - len(prefix) - len(suffix)
	if available < 1 {
		return trimID(prefix + compactID(runID))
	}
	if len(source) > available {
		source = strings.TrimRight(source[:available], "-")
	}
	return prefix + source + suffix
}

func compactID(value string) string {
	var b strings.Builder
	dash := false
	for _, r := range strings.ToLower(value) {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') {
			b.WriteRune(r)
			dash = false
		} else if b.Len() > 0 && !dash {
			b.WriteByte('-')
			dash = true
		}
	}
	return strings.Trim(b.String(), "-")
}

func trimID(value string) string {
	const max = 63
	if len(value) > max {
		value = strings.TrimRight(value[:max], "-")
	}
	return value
}
