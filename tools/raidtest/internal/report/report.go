package report

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const SchemaVersion = "raidtest.report/v1"

type Report struct {
	SchemaVersion  string            `json:"schema_version"`
	RunID          string            `json:"run_id"`
	SuiteID        string            `json:"suite_id,omitempty"`
	StartedAt      time.Time         `json:"started_at"`
	FinishedAt     time.Time         `json:"finished_at"`
	Server         Server            `json:"server"`
	Resources      Resources         `json:"resources"`
	Models         map[string]string `json:"models,omitempty"`
	Cases          []Case            `json:"cases"`
	Lifecycle      []Lifecycle       `json:"lifecycle"`
	CredentialScan string            `json:"credential_scan,omitempty"`
	Status         string            `json:"status"`
	Error          string            `json:"error,omitempty"`
}

type Server struct {
	Endpoint     string `json:"endpoint"`
	PeerEndpoint string `json:"peer_endpoint,omitempty"`
	PublicKey    string `json:"public_key"`
	Version      string `json:"version,omitempty"`
}
type ResourceRef struct {
	Kind             string `json:"kind,omitempty"`
	SourceID         string `json:"source_id"`
	ShadowID         string `json:"shadow_id"`
	SourceDigest     string `json:"source_digest"`
	ShadowDigest     string `json:"shadow_digest"`
	LiveDigest       string `json:"live_digest,omitempty"`
	CandidateChanged bool   `json:"candidate_changed,omitempty"`
}
type Resources struct {
	Workflow       ResourceRef   `json:"workflow"`
	RuntimeProfile ResourceRef   `json:"runtime_profile"`
	MemoryLayouts  []ResourceRef `json:"memory_layouts,omitempty"`
	Paired         []ResourceRef `json:"paired,omitempty"`
}
type Check struct {
	Name     string `json:"name"`
	Status   string `json:"status"`
	Detail   string `json:"detail,omitempty"`
	Evidence string `json:"evidence,omitempty"`
}
type Turn struct {
	ID               string            `json:"id"`
	ResponseID       string            `json:"response_id,omitempty"`
	TargetWorkflowID string            `json:"target_workflow_id,omitempty"`
	TesterWorkflowID string            `json:"tester_workflow_id,omitempty"`
	User             string            `json:"user"`
	Assistant        string            `json:"assistant"`
	Tester           string            `json:"tester,omitempty"`
	JudgeSummary     string            `json:"judge_summary,omitempty"`
	TesterDecision   time.Duration     `json:"tester_decision_ns,omitempty"`
	FirstResponse    time.Duration     `json:"first_response_ns"`
	TotalResponse    time.Duration     `json:"total_response_ns"`
	RuneCount        int               `json:"rune_count"`
	Checks           []Check           `json:"checks"`
	Status           string            `json:"status"`
	Owner            string            `json:"owner,omitempty"`
	Error            string            `json:"error,omitempty"`
	Evidence         map[string]string `json:"evidence,omitempty"`
}
type Case struct {
	ID                string `json:"id"`
	InputMode         string `json:"input_mode,omitempty"`
	TargetPeerID      string `json:"target_peer_id,omitempty"`
	TesterPeerID      string `json:"tester_peer_id,omitempty"`
	TargetWorkspaceID string `json:"target_workspace_id,omitempty"`
	TesterWorkspaceID string `json:"tester_workspace_id,omitempty"`
	Status            string `json:"status"`
	Owner             string `json:"owner,omitempty"`
	Error             string `json:"error,omitempty"`
	Turns             []Turn `json:"turns"`
}
type Lifecycle struct {
	ResourceType string `json:"resource_type"`
	ID           string `json:"id"`
	Action       string `json:"action"`
	Status       string `json:"status"`
	Error        string `json:"error,omitempty"`
}

func New(runID string) Report {
	return Report{SchemaVersion: SchemaVersion, RunID: runID, StartedAt: time.Now().UTC(), Models: map[string]string{}}
}

func (r *Report) Finish(err error) {
	r.FinishedAt = time.Now().UTC()
	r.Status = "pass"
	if err != nil {
		r.Status, r.Error = "fail", err.Error()
		return
	}
	for _, c := range r.Cases {
		if c.Status != "pass" {
			r.Status = "fail"
			return
		}
	}
	for _, l := range r.Lifecycle {
		if l.Status != "pass" {
			r.Status = "fail"
			return
		}
	}
}

func (r Report) WriteJSON(path string) error {
	b, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return err
	}
	b = append(b, '\n')
	parent := filepath.Dir(path)
	if parent != "." {
		if _, err := os.Stat(parent); errors.Is(err, os.ErrNotExist) {
			if err := os.MkdirAll(parent, 0o700); err != nil {
				return err
			}
			if err := os.Chmod(parent, 0o700); err != nil {
				return err
			}
		} else if err != nil {
			return err
		}
	}
	file, err := os.CreateTemp(parent, "."+filepath.Base(path)+".tmp-*")
	if err != nil {
		return err
	}
	temporaryPath := file.Name()
	committed := false
	defer func() {
		if !committed {
			_ = os.Remove(temporaryPath)
		}
	}()
	if err := file.Chmod(0o600); err != nil {
		_ = file.Close()
		return err
	}
	if _, err := file.Write(b); err != nil {
		_ = file.Close()
		return err
	}
	if err := file.Sync(); err != nil {
		_ = file.Close()
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	if err := os.Rename(temporaryPath, path); err != nil {
		return err
	}
	committed = true
	return nil
}

// WriteCaseReports retains one independently readable evidence file per suite
// attempt in addition to the aggregate report. Legacy single-workflow runs do
// not create the companion directory.
func (r Report) WriteCaseReports(aggregatePath string) error {
	if r.SuiteID == "" {
		return nil
	}
	directory := strings.TrimSuffix(aggregatePath, filepath.Ext(aggregatePath)) + ".d"
	if err := os.MkdirAll(directory, 0o700); err != nil {
		return err
	}
	if err := os.Chmod(directory, 0o700); err != nil {
		return err
	}
	for _, c := range r.Cases {
		if strings.TrimSpace(c.ID) == "" || c.ID == "." || c.ID == ".." || strings.ContainsAny(c.ID, `/\\`) {
			return fmt.Errorf("unsafe case report id %q", c.ID)
		}
		caseReport := r
		caseReport.Cases = []Case{c}
		if err := caseReport.WriteJSON(filepath.Join(directory, c.ID+".json")); err != nil {
			return err
		}
	}
	return nil
}

func (r Report) WriteTerminal(w io.Writer) {
	fmt.Fprintf(w, "raidtest run=%s status=%s cases=%d lifecycle=%d\n", r.RunID, r.Status, len(r.Cases), len(r.Lifecycle))
	for _, c := range r.Cases {
		fmt.Fprintf(w, "case %-32s %s turns=%d", c.ID, c.Status, len(c.Turns))
		if c.InputMode != "" {
			fmt.Fprintf(w, " input=%s", c.InputMode)
		}
		if c.Error != "" {
			fmt.Fprintf(w, " error=%q", c.Error)
		}
		fmt.Fprintln(w)
	}
	for _, l := range r.Lifecycle {
		fmt.Fprintf(w, "lifecycle %-14s %-10s %s id=%s", l.ResourceType, l.Action, l.Status, l.ID)
		if l.Error != "" {
			fmt.Fprintf(w, " error=%q", l.Error)
		}
		fmt.Fprintln(w)
	}
}

func Redact(text string, secrets ...[]byte) string {
	for _, secret := range secrets {
		value := strings.TrimSpace(string(secret))
		if value != "" {
			text = strings.ReplaceAll(text, value, "[REDACTED]")
		}
	}
	return text
}
