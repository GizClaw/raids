package report

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestReportIsCompleteAndRedactsSecrets(t *testing.T) {
	r := New("run-1")
	r.Cases = []Case{{ID: "case-one", Status: "fail", Turns: []Turn{{ID: "turn-one", Status: "fail", Error: Redact("token secret-value", []byte("secret-value"))}}}}
	r.Finish(nil)
	path := filepath.Join(t.TempDir(), "report.json")
	if err := r.WriteJSON(path); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(path)
	if strings.Contains(string(b), "secret-value") {
		t.Fatal("report leaked secret")
	}
	var decoded Report
	if err := json.Unmarshal(b, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded.SchemaVersion != SchemaVersion || decoded.Status != "fail" {
		t.Fatalf("unexpected report: %#v", decoded)
	}
	var terminal bytes.Buffer
	r.WriteTerminal(&terminal)
	if !strings.Contains(terminal.String(), "case-one") || !strings.Contains(terminal.String(), "fail") {
		t.Fatal("terminal summary omitted terminal case status")
	}
}

func TestWriteJSONRestrictsExistingFilePermissions(t *testing.T) {
	path := filepath.Join(t.TempDir(), "report.json")
	if err := os.WriteFile(path, []byte("old"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := (Report{}).WriteJSON(path); err != nil {
		t.Fatal(err)
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	if got := info.Mode().Perm(); got != 0o600 {
		t.Fatalf("permissions=%#o want 0600", got)
	}
}
