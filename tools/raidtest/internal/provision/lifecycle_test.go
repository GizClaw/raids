package provision

import (
	"context"
	"errors"
	"reflect"
	"strings"
	"testing"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/adminhttp"
	"github.com/GizClaw/raids/tools/raidtest/internal/catalog"
)

type fakeAdmin struct {
	calls []string
	fail  map[string]error
}

func (f *fakeAdmin) EnsureAbsent(_ context.Context, kind, _ string) error {
	return f.call("absent " + kind)
}

func (f *fakeAdmin) call(name string) error { f.calls = append(f.calls, name); return f.fail[name] }
func (f *fakeAdmin) CreateWorkflow(context.Context, adminhttp.WorkflowUpsert) error {
	return f.call("create Workflow")
}
func (f *fakeAdmin) GetWorkflow(context.Context, string) error    { return f.call("get Workflow") }
func (f *fakeAdmin) DeleteWorkflow(context.Context, string) error { return f.call("delete Workflow") }
func (f *fakeAdmin) CreateMemoryLayout(context.Context, adminhttp.MemoryLayoutUpsert) error {
	return f.call("create MemoryLayout")
}
func (f *fakeAdmin) GetMemoryLayout(context.Context, string) error { return f.call("get MemoryLayout") }
func (f *fakeAdmin) DeleteMemoryLayout(context.Context, string) error {
	return f.call("delete MemoryLayout")
}
func (f *fakeAdmin) CreateRuntimeProfile(context.Context, adminhttp.RuntimeProfileUpsert) error {
	return f.call("create RuntimeProfile")
}
func (f *fakeAdmin) GetRuntimeProfile(context.Context, string) error {
	return f.call("get RuntimeProfile")
}
func (f *fakeAdmin) DeleteRuntimeProfile(context.Context, string) error {
	return f.call("delete RuntimeProfile")
}
func (f *fakeAdmin) CreateRegistrationToken(context.Context, adminhttp.RegistrationTokenUpsert) error {
	return f.call("create RegistrationToken")
}
func (f *fakeAdmin) DeleteRegistrationToken(context.Context, string) error {
	return f.call("delete RegistrationToken")
}
func (f *fakeAdmin) CreateWorkspace(context.Context, adminhttp.WorkspaceUpsert) error {
	return f.call("create Workspace")
}
func (f *fakeAdmin) GetWorkspace(context.Context, string) error    { return f.call("get Workspace") }
func (f *fakeAdmin) DeleteWorkspace(context.Context, string) error { return f.call("delete Workspace") }
func (f *fakeAdmin) DeletePeer(context.Context, string) error      { return f.call("delete Peer") }
func (f *fakeAdmin) GetReference(_ context.Context, kind, _ string) error {
	return f.call("get reference " + kind)
}

func TestCleanupRunsInReverseOrderAndContinues(t *testing.T) {
	f := &fakeAdmin{fail: map[string]error{"delete Peer": errors.New("busy")}}
	l := New(f, false)
	l.created = []Resource{{"Workflow", "w"}, {"MemoryLayout", "m"}, {"RuntimeProfile", "r"}, {"RegistrationToken", "t"}, {"Peer", "p"}, {"Workspace", "x"}}
	if err := l.Cleanup(context.Background()); err == nil {
		t.Fatal("expected aggregate cleanup error")
	}
	want := []string{"delete Workspace", "delete Peer", "delete RegistrationToken", "delete RuntimeProfile", "delete MemoryLayout", "delete Workflow"}
	if !reflect.DeepEqual(f.calls, want) {
		t.Fatalf("cleanup calls=%v want=%v", f.calls, want)
	}
	delete(f.fail, "delete Peer")
	if err := l.Cleanup(context.Background()); err != nil {
		t.Fatal(err)
	}
	if got := f.calls[len(f.calls)-1]; got != "delete Peer" {
		t.Fatalf("retry deleted %q, want only the failed Peer", got)
	}
	callCount := len(f.calls)
	if err := l.Cleanup(context.Background()); err != nil || len(f.calls) != callCount {
		t.Fatal("completed cleanup was not idempotent")
	}
}

func TestKeepRecordsTerminalRetentionOnce(t *testing.T) {
	l := New(&fakeAdmin{}, true)
	l.created = []Resource{{"Workflow", "w"}, {"RuntimeProfile", "r"}}
	if err := l.Cleanup(context.Background()); err != nil {
		t.Fatal(err)
	}
	if len(l.Ledger) != 2 || l.Ledger[0].Action != "retain" || l.Ledger[0].ID != "r" {
		t.Fatalf("retention ledger=%#v", l.Ledger)
	}
	if err := l.Cleanup(context.Background()); err != nil || len(l.Ledger) != 2 {
		t.Fatal("retention cleanup was not idempotent")
	}
}

func TestCreateRecordsResourceBeforeReadbackFailure(t *testing.T) {
	f := &fakeAdmin{fail: map[string]error{"get Workspace": errors.New("readback failed")}}
	l := New(f, false)
	if err := l.CreateWorkspace(context.Background(), "x", "name", "w"); err == nil {
		t.Fatal("expected failure")
	}
	if err := l.Cleanup(context.Background()); err != nil {
		t.Fatal(err)
	}
	if got := f.calls[len(f.calls)-1]; got != "delete Workspace" {
		t.Fatalf("last call=%s", got)
	}
}

func TestStatusErrorCanBeRedactedBeforeLedgerUse(t *testing.T) {
	secret := "registration-secret"
	err := statusError("create RegistrationToken", 400, []byte(`{"token":"`+secret+`"}`))
	redacted := strings.ReplaceAll(err.Error(), secret, "[REDACTED]")
	if strings.Contains(redacted, secret) {
		t.Fatal("registration token remained in error")
	}
}

func TestCreateRefusesToOverwriteExistingShadowResource(t *testing.T) {
	f := &fakeAdmin{fail: map[string]error{"absent Workspace": errors.New("resource already exists")}}
	l := New(f, false)
	if err := l.CreateWorkspace(context.Background(), "x", "name", "w"); err == nil {
		t.Fatal("expected preflight conflict")
	}
	if len(f.calls) != 1 || f.calls[0] != "absent Workspace" || len(l.created) != 0 {
		t.Fatalf("preflight mutated resource: calls=%v created=%v", f.calls, l.created)
	}
}

func TestCreateClosureVerifiesRetainedReferencesBeforeProfileMutation(t *testing.T) {
	workflow, err := catalog.LoadWorkflow("../../testdata/workflow-flowcraft.yaml")
	if err != nil {
		t.Fatal(err)
	}
	profile, err := catalog.LoadRuntimeProfile("../../testdata/runtime-profile.yaml")
	if err != nil {
		t.Fatal(err)
	}
	closure, err := catalog.BuildClosure(workflow, profile, nil, "run")
	if err != nil {
		t.Fatal(err)
	}
	f := &fakeAdmin{}
	l := New(f, false)
	setup := Setup{Closure: closure, TokenID: "token", Token: "secret", WorkspaceID: "workspace", WorkspaceName: "workspace"}
	if err := l.CreateClosure(context.Background(), setup); err != nil {
		t.Fatal(err)
	}
	refIndex, profileIndex := -1, -1
	for index, call := range f.calls {
		if strings.HasPrefix(call, "get reference ") && refIndex < 0 {
			refIndex = index
		}
		if call == "create RuntimeProfile" {
			profileIndex = index
		}
	}
	if refIndex < 0 || profileIndex < 0 || refIndex > profileIndex {
		t.Fatalf("retained references were not verified before profile create: %v", f.calls)
	}
	if got := f.calls[len(f.calls)-1]; got != "create RegistrationToken" {
		t.Fatalf("last setup call=%q calls=%v", got, f.calls)
	}
}
