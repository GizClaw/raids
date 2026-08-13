package report

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"time"
)

const SchemaVersion = "raidtest.report/v1"

type Report struct {
	SchemaVersion string            `json:"schema_version"`
	RunID         string            `json:"run_id"`
	StartedAt     time.Time         `json:"started_at"`
	FinishedAt    time.Time         `json:"finished_at"`
	Server        Server            `json:"server"`
	Resources     Resources         `json:"resources"`
	Models        map[string]string `json:"models,omitempty"`
	Cases         []Case            `json:"cases"`
	Lifecycle     []Lifecycle       `json:"lifecycle"`
	Status        string            `json:"status"`
	Error         string            `json:"error,omitempty"`
}

type Server struct {
	Endpoint     string `json:"endpoint"`
	PeerEndpoint string `json:"peer_endpoint,omitempty"`
	PublicKey    string `json:"public_key"`
	Version      string `json:"version,omitempty"`
}
type ResourceRef struct {
	SourceID     string `json:"source_id"`
	ShadowID     string `json:"shadow_id"`
	SourceDigest string `json:"source_digest"`
	ShadowDigest string `json:"shadow_digest"`
}
type Resources struct {
	Workflow       ResourceRef   `json:"workflow"`
	RuntimeProfile ResourceRef   `json:"runtime_profile"`
	MemoryLayouts  []ResourceRef `json:"memory_layouts,omitempty"`
}
type Check struct {
	Name   string `json:"name"`
	Status string `json:"status"`
	Detail string `json:"detail,omitempty"`
}
type Turn struct {
	ID            string            `json:"id"`
	User          string            `json:"user"`
	Assistant     string            `json:"assistant"`
	FirstResponse time.Duration     `json:"first_response_ns"`
	TotalResponse time.Duration     `json:"total_response_ns"`
	RuneCount     int               `json:"rune_count"`
	Checks        []Check           `json:"checks"`
	Status        string            `json:"status"`
	Error         string            `json:"error,omitempty"`
	Evidence      map[string]string `json:"evidence,omitempty"`
}
type Case struct {
	ID     string `json:"id"`
	Status string `json:"status"`
	Error  string `json:"error,omitempty"`
	Turns  []Turn `json:"turns"`
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
	file, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o600)
	if err != nil {
		return err
	}
	if err := file.Chmod(0o600); err != nil {
		_ = file.Close()
		return err
	}
	if _, err := file.Write(b); err != nil {
		_ = file.Close()
		return err
	}
	return file.Close()
}

func (r Report) WriteTerminal(w io.Writer) {
	fmt.Fprintf(w, "raidtest run=%s status=%s cases=%d lifecycle=%d\n", r.RunID, r.Status, len(r.Cases), len(r.Lifecycle))
	for _, c := range r.Cases {
		fmt.Fprintf(w, "case %-32s %s turns=%d", c.ID, c.Status, len(c.Turns))
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
