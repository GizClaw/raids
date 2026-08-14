package suite

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
	"gopkg.in/yaml.v3"
)

const SchemaVersion = "raidtest.suite/v1"

type ResourceRef struct {
	ID         string `yaml:"id"`
	File       string `yaml:"file"`
	InvokeName string `yaml:"invoke_name,omitempty"`
}

type Timing struct {
	FirstResponse time.Duration `yaml:"-"`
	TotalResponse time.Duration `yaml:"-"`
}

type rawTiming struct {
	FirstResponse string `yaml:"first_response"`
	TotalResponse string `yaml:"total_response"`
}

type Pair struct {
	ID                      string   `yaml:"id"`
	TargetWorkflowID        string   `yaml:"target_workflow_id"`
	TargetWorkflowFile      string   `yaml:"target_workflow_file"`
	TesterWorkflowID        string   `yaml:"tester_workflow_id"`
	TesterWorkflowFile      string   `yaml:"tester_workflow_file"`
	PlanFile                string   `yaml:"plan_file"`
	ExpectedTargetResponses int      `yaml:"expected_target_responses"`
	Checkpoints             []string `yaml:"checkpoints"`
	Repeats                 int      `yaml:"repeats"`
	Reloads                 []Reload `yaml:"reloads,omitempty"`
}

type Reload struct {
	BeforeResponse int      `yaml:"before_response"`
	RequiredFacts  []string `yaml:"required_facts,omitempty"`
	Timeout        string   `yaml:"timeout,omitempty"`
}

func (r Reload) Duration() (time.Duration, error) {
	if r.Timeout == "" {
		return 0, nil
	}
	return time.ParseDuration(r.Timeout)
}

type Suite struct {
	SchemaVersion     string      `yaml:"schema_version"`
	ID                string      `yaml:"id"`
	RuntimeProfile    ResourceRef `yaml:"runtime_profile"`
	RegistrationToken ResourceRef `yaml:"registration_token"`
	Tool              ResourceRef `yaml:"tool"`
	Timing            Timing      `yaml:"-"`
	Pairs             []Pair      `yaml:"pairs"`
	Root              string      `yaml:"-"`
}

type rawSuite struct {
	SchemaVersion     string      `yaml:"schema_version"`
	ID                string      `yaml:"id"`
	RuntimeProfile    ResourceRef `yaml:"runtime_profile"`
	RegistrationToken ResourceRef `yaml:"registration_token"`
	Tool              ResourceRef `yaml:"tool"`
	Timing            rawTiming   `yaml:"timing"`
	Pairs             []Pair      `yaml:"pairs"`
}

func Load(path string) (Suite, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Suite{}, err
	}
	var raw rawSuite
	decoder := yaml.NewDecoder(bytes.NewReader(data))
	decoder.KnownFields(true)
	if err := decoder.Decode(&raw); err != nil {
		return Suite{}, fmt.Errorf("decode suite %s: %w", path, err)
	}
	first, err := time.ParseDuration(raw.Timing.FirstResponse)
	if err != nil {
		return Suite{}, fmt.Errorf("first_response: %w", err)
	}
	total, err := time.ParseDuration(raw.Timing.TotalResponse)
	if err != nil {
		return Suite{}, fmt.Errorf("total_response: %w", err)
	}
	root, err := repositoryRoot(path)
	if err != nil {
		return Suite{}, err
	}
	s := Suite{
		SchemaVersion: raw.SchemaVersion, ID: raw.ID, RuntimeProfile: raw.RuntimeProfile,
		RegistrationToken: raw.RegistrationToken, Tool: raw.Tool,
		Timing: Timing{FirstResponse: first, TotalResponse: total}, Pairs: raw.Pairs, Root: root,
	}
	if err := s.Validate(); err != nil {
		return Suite{}, err
	}
	return s, nil
}

func (s Suite) Resolve(path string) string {
	if filepath.IsAbs(path) {
		return filepath.Clean(path)
	}
	return filepath.Join(s.Root, filepath.FromSlash(path))
}

func (s Suite) Validate() error {
	if s.SchemaVersion != SchemaVersion {
		return fmt.Errorf("unsupported suite schema %q", s.SchemaVersion)
	}
	if strings.TrimSpace(s.ID) == "" {
		return errors.New("suite id is required")
	}
	for name, resource := range map[string]ResourceRef{
		"runtime_profile": s.RuntimeProfile, "registration_token": s.RegistrationToken, "tool": s.Tool,
	} {
		if strings.TrimSpace(resource.ID) == "" || strings.TrimSpace(resource.File) == "" {
			return fmt.Errorf("%s id and file are required", name)
		}
		if _, err := os.Stat(s.Resolve(resource.File)); err != nil {
			return fmt.Errorf("%s file: %w", name, err)
		}
	}
	if strings.TrimSpace(s.Tool.InvokeName) == "" {
		return errors.New("tool invoke_name is required")
	}
	if s.Timing.FirstResponse <= 0 || s.Timing.TotalResponse <= 0 || s.Timing.FirstResponse > s.Timing.TotalResponse {
		return errors.New("suite timing budgets are invalid")
	}
	if len(s.Pairs) == 0 {
		return errors.New("suite requires at least one pair")
	}
	seenPairs := map[string]bool{}
	seenTargets := map[string]bool{}
	seenTesters := map[string]bool{}
	for _, pair := range s.Pairs {
		if pair.ID == "" || pair.TargetWorkflowID == "" || pair.TesterWorkflowID == "" ||
			pair.TargetWorkflowFile == "" || pair.TesterWorkflowFile == "" || pair.PlanFile == "" {
			return fmt.Errorf("pair %q is incomplete", pair.ID)
		}
		if seenPairs[pair.ID] {
			return fmt.Errorf("duplicate pair %q", pair.ID)
		}
		if seenTargets[pair.TargetWorkflowID] {
			return fmt.Errorf("duplicate target workflow %q", pair.TargetWorkflowID)
		}
		if seenTesters[pair.TesterWorkflowID] {
			return fmt.Errorf("duplicate tester workflow %q", pair.TesterWorkflowID)
		}
		if pair.ID != pair.TargetWorkflowID {
			return fmt.Errorf("pair %q id must match target workflow %q", pair.ID, pair.TargetWorkflowID)
		}
		if strings.HasSuffix(pair.TargetWorkflowID, "-test") {
			return fmt.Errorf("pair %q target workflow cannot be a tester", pair.ID)
		}
		if pair.TargetWorkflowID == pair.TesterWorkflowID || pair.TesterWorkflowID != pair.TargetWorkflowID+"-test" {
			return fmt.Errorf("pair %q does not use the required one-to-one tester ID", pair.ID)
		}
		seenPairs[pair.ID] = true
		seenTargets[pair.TargetWorkflowID] = true
		seenTesters[pair.TesterWorkflowID] = true
		if pair.ExpectedTargetResponses < 1 || pair.Repeats < 1 {
			return fmt.Errorf("pair %q has invalid response or repeat count", pair.ID)
		}
		if len(pair.Checkpoints) != pair.ExpectedTargetResponses {
			return fmt.Errorf("pair %q has %d checkpoints, want %d", pair.ID, len(pair.Checkpoints), pair.ExpectedTargetResponses)
		}
		checkpointIDs := map[string]bool{}
		for _, checkpoint := range pair.Checkpoints {
			if strings.TrimSpace(checkpoint) == "" || checkpointIDs[checkpoint] {
				return fmt.Errorf("pair %q has empty or duplicate checkpoint %q", pair.ID, checkpoint)
			}
			checkpointIDs[checkpoint] = true
		}
		reloads := map[int]bool{}
		for _, reload := range pair.Reloads {
			if reload.BeforeResponse < 2 || reload.BeforeResponse > pair.ExpectedTargetResponses || reloads[reload.BeforeResponse] {
				return fmt.Errorf("pair %q has invalid duplicate reload before response %d", pair.ID, reload.BeforeResponse)
			}
			reloads[reload.BeforeResponse] = true
			if len(reload.RequiredFacts) > 0 {
				duration, err := reload.Duration()
				if err != nil || duration <= 0 {
					return fmt.Errorf("pair %q reload persistence timeout is invalid", pair.ID)
				}
			}
		}
		for _, path := range []string{pair.TargetWorkflowFile, pair.TesterWorkflowFile, pair.PlanFile} {
			if _, err := os.Stat(s.Resolve(path)); err != nil {
				return fmt.Errorf("pair %q file %s: %w", pair.ID, path, err)
			}
		}
		loadedPlan, err := plan.Load(s.Resolve(pair.PlanFile))
		if err != nil {
			return fmt.Errorf("pair %q plan: %w", pair.ID, err)
		}
		loadedPlan, err = loadedPlan.ForWorkflow(pair.TargetWorkflowID)
		if err != nil {
			return fmt.Errorf("pair %q plan selection: %w", pair.ID, err)
		}
		if len(loadedPlan.Cases) != 1 {
			return fmt.Errorf("pair %q plan must select exactly one case", pair.ID)
		}
		turns := loadedPlan.Cases[0].Turns
		if len(turns) != len(pair.Checkpoints) {
			return fmt.Errorf("pair %q plan has %d turns, want %d", pair.ID, len(turns), len(pair.Checkpoints))
		}
		for index, checkpoint := range pair.Checkpoints {
			if turns[index].ID != checkpoint {
				return fmt.Errorf("pair %q plan turn %d is %q, want %q", pair.ID, index+1, turns[index].ID, checkpoint)
			}
		}
	}
	return nil
}

func repositoryRoot(path string) (string, error) {
	current, err := filepath.Abs(filepath.Dir(path))
	if err != nil {
		return "", err
	}
	for {
		if _, err := os.Stat(filepath.Join(current, "runtime-profiles")); err == nil {
			if _, err := os.Stat(filepath.Join(current, "workflows")); err == nil {
				return current, nil
			}
		}
		parent := filepath.Dir(current)
		if parent == current {
			return "", fmt.Errorf("cannot find repository root from %s", path)
		}
		current = parent
	}
}
