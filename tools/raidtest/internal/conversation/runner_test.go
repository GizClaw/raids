package conversation

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
)

type fakeTarget struct {
	responses map[string]Response
	errors    map[string]error
	reloads   int
}

func (f *fakeTarget) Send(_ context.Context, id, _ string) (Response, error) {
	return f.responses[id], f.errors[id]
}
func (f *fakeTarget) Reload(context.Context) error { f.reloads++; return nil }

func TestRunnerDoesNotFailFast(t *testing.T) {
	target := &fakeTarget{responses: map[string]Response{"first-one": {Text: "too long", FirstResponse: time.Millisecond, TotalResponse: time.Millisecond}, "second-two": {Text: "Alice 12", FirstResponse: time.Millisecond, TotalResponse: time.Millisecond}}, errors: map[string]error{"first-one": errors.New("boom")}}
	p := plan.Plan{Version: "v1", Name: "test", Driver: "flowcraft", Cases: []plan.Case{{ID: "first", Turns: []plan.Turn{{ID: "one", User: "hello"}}}, {ID: "second", Turns: []plan.Turn{{ID: "two", User: "recall", ReloadBefore: true, Required: []string{"Alice", "12"}, MaxRunes: 8}}}}}
	got := (Runner{Target: target}).Run(context.Background(), p)
	if len(got) != 2 || got[0].Status != "fail" || got[1].Status != "pass" || target.reloads != 1 {
		t.Fatalf("unexpected results: %#v reloads=%d", got, target.reloads)
	}
}

func TestDeterministicFailureCannotBeOverridden(t *testing.T) {
	checks := DeterministicChecks(plan.Turn{Required: []string{"new"}, Forbidden: []string{"old"}, MaxRunes: 3, Scripts: []string{"latin"}}, Response{Text: "old value", TotalResponse: 2 * time.Second})
	if !hasFailure(checks) {
		t.Fatal("expected deterministic failure")
	}
}

func TestDeterministicAlternativesAndPunctuation(t *testing.T) {
	checks := DeterministicChecks(plan.Turn{RequiredAny: [][]string{{"没", "未", "不"}}, RequirePunctuation: true}, Response{Text: "Alice未取消会议。"})
	if hasFailure(checks) {
		t.Fatalf("checks=%#v", checks)
	}
}
