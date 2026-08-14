package acceptance

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"
	"sync"
	"time"
)

const (
	ActionContinue = "continue"
	ActionPass     = "pass"
	ActionFail     = "fail"
)

type Check struct {
	Name     string `json:"name"`
	Status   string `json:"status"`
	Detail   string `json:"detail"`
	Evidence string `json:"evidence"`
}

type Submission struct {
	CaseID           string        `json:"case_id"`
	TargetWorkflowID string        `json:"target_workflow_id"`
	ResponseID       string        `json:"response_id"`
	TurnID           string        `json:"turn_id"`
	Action           string        `json:"action"`
	NextMessage      string        `json:"next_message"`
	Checks           []Check       `json:"checks"`
	Summary          string        `json:"summary"`
	DecisionLatency  time.Duration `json:"-"`
}

type Expectation struct {
	CaseID           string
	TargetWorkflowID string
	ResponseID       string
	TurnID           string
}

type Handler struct {
	mu      sync.Mutex
	pending *pending
}

type pending struct {
	expectation Expectation
	result      chan Submission
	failure     error
}

func (h *Handler) Arm(expectation Expectation) (<-chan Submission, error) {
	if strings.TrimSpace(expectation.CaseID) == "" || strings.TrimSpace(expectation.TargetWorkflowID) == "" || strings.TrimSpace(expectation.ResponseID) == "" || strings.TrimSpace(expectation.TurnID) == "" {
		return nil, errors.New("complete acceptance expectation is required")
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.pending != nil {
		return nil, errors.New("an acceptance response is already pending")
	}
	ch := make(chan Submission, 1)
	h.pending = &pending{expectation: expectation, result: ch}
	return ch, nil
}

func (h *Handler) Cancel() error {
	h.mu.Lock()
	defer h.mu.Unlock()
	var err error
	if h.pending != nil {
		err = h.pending.failure
	}
	h.pending = nil
	return err
}

func (h *Handler) reject(err error) error {
	h.mu.Lock()
	if h.pending != nil {
		h.pending.failure = err
	}
	h.mu.Unlock()
	return err
}

func (h *Handler) Handle(_ context.Context, args json.RawMessage) (json.RawMessage, error) {
	var submission Submission
	decoder := json.NewDecoder(bytes.NewReader(args))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&submission); err != nil {
		err = fmt.Errorf("decode acceptance report: %w", err)
		return nil, h.reject(err)
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		return nil, h.reject(errors.New("acceptance report contains trailing JSON"))
	}
	if err := validateSubmission(submission); err != nil {
		return nil, h.reject(err)
	}

	h.mu.Lock()
	defer h.mu.Unlock()
	if h.pending == nil {
		return nil, errors.New("no acceptance response is pending")
	}
	want := h.pending.expectation
	if submission.CaseID != want.CaseID || submission.TargetWorkflowID != want.TargetWorkflowID || submission.ResponseID != want.ResponseID || submission.TurnID != want.TurnID {
		err := fmt.Errorf(
			"acceptance correlation mismatch: got %s/%s/%s/%s want %s/%s/%s/%s",
			submission.CaseID, submission.TargetWorkflowID, submission.ResponseID, submission.TurnID,
			want.CaseID, want.TargetWorkflowID, want.ResponseID, want.TurnID,
		)
		h.pending.failure = err
		return nil, err
	}
	h.pending.result <- submission
	close(h.pending.result)
	h.pending = nil
	return json.RawMessage(`{"accepted":true}`), nil
}

func validateSubmission(submission Submission) error {
	for name, value := range map[string]string{
		"case_id": submission.CaseID, "target_workflow_id": submission.TargetWorkflowID,
		"response_id": submission.ResponseID, "turn_id": submission.TurnID, "summary": submission.Summary,
	} {
		if strings.TrimSpace(value) == "" {
			return fmt.Errorf("%s is required", name)
		}
	}
	switch submission.Action {
	case ActionContinue:
		if strings.TrimSpace(submission.NextMessage) == "" {
			return errors.New("continue action requires next_message")
		}
	case ActionPass:
		if strings.TrimSpace(submission.NextMessage) != "" {
			return errors.New("pass action forbids next_message")
		}
	case ActionFail:
		if strings.TrimSpace(submission.NextMessage) != "" {
			return errors.New("fail action forbids next_message")
		}
	default:
		return fmt.Errorf("unsupported action %q", submission.Action)
	}
	if len(submission.Checks) < 4 {
		return errors.New("at least four checks are required")
	}
	seen := map[string]bool{}
	required := map[string]bool{
		"instruction_following": false,
		"continuity":            false,
		"factuality":            false,
		"non_repetition":        false,
	}
	failed := false
	for _, check := range submission.Checks {
		name := strings.TrimSpace(check.Name)
		if name == "" || seen[name] || strings.TrimSpace(check.Detail) == "" || strings.TrimSpace(check.Evidence) == "" {
			return fmt.Errorf("invalid or duplicate check %q", check.Name)
		}
		if len([]rune(check.Evidence)) > 512 {
			return fmt.Errorf("check %q evidence exceeds 512 Unicode characters", check.Name)
		}
		seen[name] = true
		if _, ok := required[name]; ok {
			required[name] = true
		}
		switch check.Status {
		case "pass":
		case "fail":
			failed = true
		default:
			return fmt.Errorf("check %q has unsupported status %q", name, check.Status)
		}
	}
	for name, present := range required {
		if !present {
			return fmt.Errorf("required check %q is missing", name)
		}
	}
	if failed && submission.Action == ActionPass {
		return errors.New("action=pass forbids failed checks")
	}
	if !failed && submission.Action == ActionFail {
		return errors.New("action=fail requires at least one failed check")
	}
	return nil
}
