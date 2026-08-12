package plan

import (
	"errors"
	"fmt"
	"os"
	"regexp"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

type Plan struct {
	Version string `yaml:"version" json:"version"`
	Name    string `yaml:"name" json:"name"`
	Driver  string `yaml:"driver" json:"driver"`
	Persona string `yaml:"persona,omitempty" json:"persona,omitempty"`
	Cases   []Case `yaml:"cases" json:"cases"`
}

type Case struct {
	ID         string `yaml:"id" json:"id"`
	WorkflowID string `yaml:"workflow_id,omitempty" json:"workflow_id,omitempty"`
	Turns      []Turn `yaml:"turns" json:"turns"`
}

func (p Plan) ForWorkflow(workflowID string) (Plan, error) {
	filtered := p
	filtered.Cases = nil
	qualified := false
	for _, c := range p.Cases {
		if c.WorkflowID != "" {
			qualified = true
		}
		if c.WorkflowID == "" || c.WorkflowID == workflowID {
			filtered.Cases = append(filtered.Cases, c)
		}
	}
	if qualified && len(filtered.Cases) == 0 {
		return Plan{}, fmt.Errorf("plan %s has no cases for Workflow %q", p.Name, workflowID)
	}
	return filtered, nil
}

type Turn struct {
	ID                 string        `yaml:"id" json:"id"`
	User               string        `yaml:"user" json:"user"`
	Intent             string        `yaml:"intent,omitempty" json:"intent,omitempty"`
	ReloadBefore       bool          `yaml:"reload_before,omitempty" json:"reload_before,omitempty"`
	Required           []string      `yaml:"required,omitempty" json:"required,omitempty"`
	RequiredAny        [][]string    `yaml:"required_any,omitempty" json:"required_any,omitempty"`
	Forbidden          []string      `yaml:"forbidden,omitempty" json:"forbidden,omitempty"`
	Scripts            []string      `yaml:"scripts,omitempty" json:"scripts,omitempty"`
	RequirePunctuation bool          `yaml:"require_punctuation,omitempty" json:"require_punctuation,omitempty"`
	MaxRunes           int           `yaml:"max_runes,omitempty" json:"max_runes,omitempty"`
	FirstResponse      time.Duration `yaml:"-" json:"first_response,omitempty"`
	TotalResponse      time.Duration `yaml:"-" json:"total_response,omitempty"`
	FirstResponseText  string        `yaml:"first_response,omitempty" json:"-"`
	TotalResponseText  string        `yaml:"total_response,omitempty" json:"-"`
	Judge              []string      `yaml:"judge,omitempty" json:"judge,omitempty"`
}

func (p Plan) NeedsAgent() bool {
	for _, c := range p.Cases {
		for _, turn := range c.Turns {
			if strings.TrimSpace(turn.User) == "" {
				return true
			}
		}
	}
	return false
}

func (p Plan) NeedsJudge() bool {
	for _, c := range p.Cases {
		for _, turn := range c.Turns {
			if len(turn.Judge) > 0 {
				return true
			}
		}
	}
	return false
}

func Load(path string) (Plan, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return Plan{}, err
	}
	var p Plan
	if err := yaml.Unmarshal(b, &p); err != nil {
		return Plan{}, fmt.Errorf("decode plan: %w", err)
	}
	for ci := range p.Cases {
		for ti := range p.Cases[ci].Turns {
			t := &p.Cases[ci].Turns[ti]
			if t.FirstResponseText != "" {
				t.FirstResponse, err = time.ParseDuration(t.FirstResponseText)
				if err != nil {
					return Plan{}, fmt.Errorf("case %s turn %s first_response: %w", p.Cases[ci].ID, t.ID, err)
				}
			}
			if t.TotalResponseText != "" {
				t.TotalResponse, err = time.ParseDuration(t.TotalResponseText)
				if err != nil {
					return Plan{}, fmt.Errorf("case %s turn %s total_response: %w", p.Cases[ci].ID, t.ID, err)
				}
			}
		}
	}
	return p, p.Validate()
}

var stableID = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,62}$`)

func (p Plan) Validate() error {
	if p.Version != "v1" {
		return errors.New("plan version must be v1")
	}
	if !stableID.MatchString(p.Name) {
		return errors.New("plan name must be a stable lowercase ID")
	}
	switch p.Driver {
	case "flowcraft", "realtime", "translate", "pet":
	default:
		return fmt.Errorf("unsupported driver %q", p.Driver)
	}
	if len(p.Cases) == 0 {
		return errors.New("plan must contain at least one case")
	}
	seenCases := map[string]bool{}
	for _, c := range p.Cases {
		if !stableID.MatchString(c.ID) || seenCases[c.ID] {
			return fmt.Errorf("invalid or duplicate case ID %q", c.ID)
		}
		seenCases[c.ID] = true
		if len(c.Turns) == 0 {
			return fmt.Errorf("case %s has no turns", c.ID)
		}
		seenTurns := map[string]bool{}
		for _, turn := range c.Turns {
			if !stableID.MatchString(turn.ID) || seenTurns[turn.ID] {
				return fmt.Errorf("case %s has invalid or duplicate turn ID %q", c.ID, turn.ID)
			}
			seenTurns[turn.ID] = true
			if strings.TrimSpace(turn.User) == "" && strings.TrimSpace(turn.Intent) == "" {
				return fmt.Errorf("case %s turn %s needs user or intent", c.ID, turn.ID)
			}
			if turn.MaxRunes < 0 || turn.FirstResponse < 0 || turn.TotalResponse < 0 {
				return fmt.Errorf("case %s turn %s has negative budget", c.ID, turn.ID)
			}
			if turn.FirstResponse > 0 && turn.TotalResponse > 0 && turn.FirstResponse > turn.TotalResponse {
				return fmt.Errorf("case %s turn %s first response exceeds total response budget", c.ID, turn.ID)
			}
			facts := map[string]string{}
			for _, fact := range turn.Required {
				key := strings.ToLower(strings.TrimSpace(fact))
				if key == "" {
					return fmt.Errorf("case %s turn %s has an empty required fact", c.ID, turn.ID)
				}
				facts[key] = "required"
			}
			for _, fact := range turn.Forbidden {
				key := strings.ToLower(strings.TrimSpace(fact))
				if key == "" {
					return fmt.Errorf("case %s turn %s has an empty forbidden fact", c.ID, turn.ID)
				}
				if facts[key] == "required" {
					return fmt.Errorf("case %s turn %s both requires and forbids %q", c.ID, turn.ID, fact)
				}
			}
			for _, alternatives := range turn.RequiredAny {
				if len(alternatives) == 0 {
					return fmt.Errorf("case %s turn %s has an empty required_any group", c.ID, turn.ID)
				}
				for _, fact := range alternatives {
					if strings.TrimSpace(fact) == "" {
						return fmt.Errorf("case %s turn %s has an empty required_any alternative", c.ID, turn.ID)
					}
				}
			}
			for _, script := range turn.Scripts {
				switch strings.ToLower(strings.TrimSpace(script)) {
				case "han", "latin", "japanese", "korean":
				default:
					return fmt.Errorf("case %s turn %s has unsupported script %q", c.ID, turn.ID, script)
				}
			}
			judge := map[string]bool{}
			for _, dimension := range turn.Judge {
				dimension = strings.TrimSpace(dimension)
				if dimension == "" || judge[dimension] {
					return fmt.Errorf("case %s turn %s has empty or duplicate judge dimension %q", c.ID, turn.ID, dimension)
				}
				judge[dimension] = true
			}
		}
	}
	return nil
}
