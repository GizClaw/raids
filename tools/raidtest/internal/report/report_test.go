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
	r.Cases = []Case{{ID: "case-one", InputMode: "realtime", Status: "fail", Turns: []Turn{{ID: "turn-one", Status: "fail", Error: Redact("token secret-value", []byte("secret-value"))}}}}
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
	if !strings.Contains(terminal.String(), "case-one") || !strings.Contains(terminal.String(), "fail") || !strings.Contains(terminal.String(), "input=realtime") {
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
	body, err := os.ReadFile(path)
	if err != nil || string(body) == "old" || !json.Valid(body) {
		t.Fatalf("body=%q err=%v", body, err)
	}
	matches, err := filepath.Glob(filepath.Join(filepath.Dir(path), ".report.json.tmp-*"))
	if err != nil || len(matches) != 0 {
		t.Fatalf("temporary files=%v err=%v", matches, err)
	}
}

func TestWriteJSONReplacesSymlinkWithoutOverwritingTarget(t *testing.T) {
	directory := t.TempDir()
	target := filepath.Join(directory, "target.txt")
	path := filepath.Join(directory, "report.json")
	if err := os.WriteFile(target, []byte("do-not-overwrite"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(target, path); err != nil {
		t.Skipf("symlinks unavailable: %v", err)
	}
	if err := (Report{}).WriteJSON(path); err != nil {
		t.Fatal(err)
	}
	body, err := os.ReadFile(target)
	if err != nil || string(body) != "do-not-overwrite" {
		t.Fatalf("symlink target body=%q err=%v", body, err)
	}
	info, err := os.Lstat(path)
	if err != nil || info.Mode()&os.ModeSymlink != 0 {
		t.Fatalf("report path info=%v err=%v", info, err)
	}
}

func TestWriteJSONCreatesPrivateReportDirectory(t *testing.T) {
	directory := filepath.Join(t.TempDir(), "nested", "reports")
	path := filepath.Join(directory, "report.json")
	if err := (Report{}).WriteJSON(path); err != nil {
		t.Fatal(err)
	}
	info, err := os.Stat(directory)
	if err != nil {
		t.Fatal(err)
	}
	if got := info.Mode().Perm(); got != 0o700 {
		t.Fatalf("directory permissions=%#o want 0700", got)
	}
}

func TestWriteCaseReportsCreatesPrivatePerCaseEvidence(t *testing.T) {
	directory := t.TempDir()
	aggregate := filepath.Join(directory, "aggregate.json")
	r := New("run-1")
	r.SuiteID = "paired"
	r.Cases = []Case{{ID: "pair-01", Status: "pass"}, {ID: "pair-02", Status: "fail"}}
	r.Finish(nil)
	if err := r.WriteCaseReports(aggregate); err != nil {
		t.Fatal(err)
	}
	caseDirectory := filepath.Join(directory, "aggregate.d")
	info, err := os.Stat(caseDirectory)
	if err != nil || info.Mode().Perm() != 0o700 {
		t.Fatalf("case report directory info=%v err=%v", info, err)
	}
	for _, id := range []string{"pair-01", "pair-02"} {
		path := filepath.Join(caseDirectory, id+".json")
		info, err := os.Stat(path)
		if err != nil || info.Mode().Perm() != 0o600 {
			t.Fatalf("case report %s info=%v err=%v", id, info, err)
		}
		var decoded Report
		body, _ := os.ReadFile(path)
		if err := json.Unmarshal(body, &decoded); err != nil || len(decoded.Cases) != 1 || decoded.Cases[0].ID != id {
			t.Fatalf("case report %s decoded=%#v err=%v", id, decoded, err)
		}
	}
}

func TestWriteCaseReportsRejectsPathTraversal(t *testing.T) {
	r := New("run-1")
	r.SuiteID = "paired"
	r.Cases = []Case{{ID: "../outside", Status: "fail"}}
	if err := r.WriteCaseReports(filepath.Join(t.TempDir(), "aggregate.json")); err == nil {
		t.Fatal("path-traversing case id was accepted")
	}
}
