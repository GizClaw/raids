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

func TestRunnerReloadsBetweenIndependentCases(t *testing.T) {
	target := &fakeTarget{responses: map[string]Response{"first-turn": {Text: "one"}, "second-turn": {Text: "two"}}, errors: map[string]error{}}
	p := plan.Plan{Version: "v1", Name: "test", Driver: "translate", Cases: []plan.Case{
		{ID: "first", Turns: []plan.Turn{{ID: "turn", User: "one"}}},
		{ID: "second", Turns: []plan.Turn{{ID: "turn", User: "two"}}},
	}}
	got := (Runner{Target: target}).Run(context.Background(), p)
	if len(got) != 2 || target.reloads != 1 {
		t.Fatalf("results=%#v reloads=%d", got, target.reloads)
	}
}

func TestRunnerChecksTextReturnedBeforeExecutionError(t *testing.T) {
	target := &fakeTarget{
		responses: map[string]Response{
			"case-turn": {Text: "39码", Evidence: map[string]string{"stream_status": "incomplete_after_text"}},
		},
		errors: map[string]error{"case-turn": context.DeadlineExceeded},
	}
	p := plan.Plan{Version: "v1", Name: "test", Driver: "flowcraft", Cases: []plan.Case{{ID: "case", Turns: []plan.Turn{{ID: "turn", User: "recall", Required: []string{"39"}, Forbidden: []string{"42"}}}}}}
	got := (Runner{Target: target}).Run(context.Background(), p)
	turn := got[0].Turns[0]
	if turn.Status != "fail" || turn.Error == "" || hasFailure(turn.Checks) || turn.Evidence["stream_status"] != "incomplete_after_text" {
		t.Fatalf("turn=%#v", turn)
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

func TestLiteralChecksIgnoreSpeechTranscriptSpacing(t *testing.T) {
	checks := DeterministicChecks(plan.Turn{Required: []string{"G7331", "12"}}, Response{Text: "G 7 3 3 1, 共有1 2个"})
	if hasFailure(checks) {
		t.Fatalf("checks=%#v", checks)
	}
}

func TestLiteralChecksTreatEquivalentDigitsEqually(t *testing.T) {
	checks := DeterministicChecks(plan.Turn{Required: []string{"四点"}, Forbidden: []string{"三点"}}, Response{Text: "已改为下午４点"})
	if hasFailure(checks) {
		t.Fatalf("checks=%#v", checks)
	}
	checks = DeterministicChecks(plan.Turn{Forbidden: []string{"三点"}}, Response{Text: "仍是下午3点"})
	if !hasFailure(checks) {
		t.Fatalf("checks=%#v", checks)
	}
}

func TestHanScriptAllowsPreservedLatinFacts(t *testing.T) {
	check := scriptCheck("Alice没有取消G7331次列车。", "han")
	if check.Status != "pass" {
		t.Fatalf("check=%#v", check)
	}
}
