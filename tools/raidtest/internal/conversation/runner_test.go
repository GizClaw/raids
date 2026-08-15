package conversation

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
	"github.com/GizClaw/raids/tools/raidtest/internal/report"
)

type fakeTarget struct {
	responses  map[string]Response
	errors     map[string]error
	reloads    int
	reloadErr  error
	recallErr  error
	operations []string
}

func (f *fakeTarget) Send(_ context.Context, id, _ string) (Response, error) {
	f.operations = append(f.operations, "send")
	return f.responses[id], f.errors[id]
}
func (f *fakeTarget) Reload(context.Context) error {
	f.operations = append(f.operations, "reload")
	f.reloads++
	return f.reloadErr
}
func (f *fakeTarget) WaitForRecall(_ context.Context, _ []string, _ time.Duration) error {
	f.operations = append(f.operations, "wait-recall")
	return f.recallErr
}

type historyJudge struct {
	history []report.Turn
}

func (j *historyJudge) Judge(_ context.Context, _ string, history []report.Turn, _ plan.Turn, _ Response) ([]report.Check, error) {
	j.history = append([]report.Turn(nil), history...)
	return []report.Check{{Name: "judge:continuity", Status: "pass"}}, nil
}

func TestRunnerDoesNotFailFast(t *testing.T) {
	target := &fakeTarget{responses: map[string]Response{"first-one": {Text: "too long", FirstResponse: time.Millisecond, TotalResponse: time.Millisecond}, "second-two": {Text: "Alice 12", FirstResponse: time.Millisecond, TotalResponse: time.Millisecond}}, errors: map[string]error{"first-one": errors.New("boom")}}
	p := plan.Plan{Version: "v1", Name: "test", Driver: "flowcraft", Cases: []plan.Case{{ID: "first", Turns: []plan.Turn{{ID: "one", User: "hello"}}}, {ID: "second", Turns: []plan.Turn{{ID: "two", User: "recall", ReloadBefore: true, Required: []string{"Alice", "12"}, MaxRunes: 8}}}}}
	got := (Runner{Target: target}).Run(context.Background(), p)
	if len(got) != 2 || got[0].Status != "fail" || got[1].Status != "pass" || target.reloads != 2 {
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

func TestRunnerWaitsForPersistedRecallBeforeReload(t *testing.T) {
	target := &fakeTarget{responses: map[string]Response{"case-recall": {Text: "39码"}}, errors: map[string]error{}}
	p := plan.Plan{Version: "v1", Name: "test", Driver: "flowcraft", Cases: []plan.Case{{ID: "case", Turns: []plan.Turn{{
		ID: "recall", User: "recall", ReloadBefore: true, PersistedBeforeReload: []string{"39码"}, PersistenceTimeout: time.Second,
	}}}}}
	got := (Runner{Target: target}).Run(context.Background(), p)
	if got[0].Status != "pass" || strings.Join(target.operations, ",") != "wait-recall,reload,send" {
		t.Fatalf("results=%#v operations=%v", got, target.operations)
	}
}

func TestRunnerStopsReloadTurnWhenPersistenceBarrierFails(t *testing.T) {
	target := &fakeTarget{responses: map[string]Response{}, errors: map[string]error{}, recallErr: errors.New("not persisted")}
	p := plan.Plan{Version: "v1", Name: "test", Driver: "flowcraft", Cases: []plan.Case{{ID: "case", Turns: []plan.Turn{{
		ID: "recall", User: "recall", ReloadBefore: true, PersistedBeforeReload: []string{"39码"}, PersistenceTimeout: time.Second,
	}}}}}
	got := (Runner{Target: target}).Run(context.Background(), p)
	if got[0].Status != "fail" || !strings.Contains(got[0].Turns[0].Error, "not persisted") || strings.Join(target.operations, ",") != "wait-recall" {
		t.Fatalf("results=%#v operations=%v", got, target.operations)
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
	if turn.Status != "fail" || turn.Error == "" || hasFailure(turn.Checks) || turn.Evidence["stream_status"] != "incomplete_after_text" || target.reloads != 1 {
		t.Fatalf("turn=%#v", turn)
	}
}

func TestRunnerReportsWorkspaceRecoveryFailureAndContinues(t *testing.T) {
	target := &fakeTarget{
		responses: map[string]Response{"case-first": {}, "case-second": {Text: "ok"}},
		errors:    map[string]error{"case-first": context.DeadlineExceeded}, reloadErr: errors.New("reload failed"),
	}
	p := plan.Plan{Version: "v1", Name: "test", Driver: "flowcraft", Cases: []plan.Case{{ID: "case", Turns: []plan.Turn{
		{ID: "first", User: "one"}, {ID: "second", User: "two"},
	}}}}
	got := (Runner{Target: target}).Run(context.Background(), p)
	if len(got[0].Turns) != 2 || got[0].Turns[1].Status != "pass" || !strings.Contains(got[0].Turns[0].Error, "recover Workspace: reload failed") {
		t.Fatalf("results=%#v", got)
	}
}

func TestRunnerJudgeReceivesPriorFailedTurnButNotCurrentTurn(t *testing.T) {
	target := &fakeTarget{responses: map[string]Response{
		"case-first":  {Text: "旧事实"},
		"case-second": {Text: "新事实"},
	}, errors: map[string]error{}}
	judge := &historyJudge{}
	p := plan.Plan{Version: "v1", Name: "test", Driver: "flowcraft", Cases: []plan.Case{{ID: "case", Turns: []plan.Turn{
		{ID: "first", User: "建立事实", Required: []string{"缺失事实"}},
		{ID: "second", User: "回忆事实", Judge: []string{"continuity"}},
	}}}}
	got := (Runner{Target: target, Judge: judge}).Run(context.Background(), p)
	if got[0].Turns[0].Status != "fail" || len(judge.history) != 1 {
		t.Fatalf("results=%#v history=%#v", got, judge.history)
	}
	if judge.history[0].ID != "first" || judge.history[0].Status != "fail" {
		t.Fatalf("history=%#v", judge.history)
	}
}

func TestDeterministicFailureCannotBeOverridden(t *testing.T) {
	checks := DeterministicChecks(plan.Turn{Required: []string{"new"}, Forbidden: []string{"old"}, MinRunes: 12, MaxRunes: 15, Scripts: []string{"latin"}}, Response{Text: "old value", TotalResponse: 2 * time.Second})
	if !hasFailure(checks) {
		t.Fatal("expected deterministic failure")
	}
}

func TestDeterministicRuneRange(t *testing.T) {
	checks := DeterministicChecks(plan.Turn{MinRunes: 4, MaxRunes: 6}, Response{Text: "四个字符"})
	if hasFailure(checks) {
		t.Fatalf("checks=%#v", checks)
	}
	checks = DeterministicChecks(plan.Turn{MinRunes: 5}, Response{Text: "太短"})
	if !hasFailure(checks) {
		t.Fatalf("checks=%#v", checks)
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

func TestForbiddenChecksIgnoreInsertedPunctuation(t *testing.T) {
	checks := DeterministicChecks(plan.Turn{Forbidden: []string{"证据显示厨师全程"}}, Response{Text: "现有证据显示，厨师全程在后厨。"})
	if !hasFailure(checks) {
		t.Fatalf("checks=%#v", checks)
	}
}

func TestForbiddenLabelChecksPreserveDeclaredPunctuation(t *testing.T) {
	checks := DeterministicChecks(plan.Turn{Forbidden: []string{"车次："}}, Response{Text: "乘坐的车次是G7331。"})
	if hasFailure(checks) {
		t.Fatalf("natural prose was mistaken for a label: %#v", checks)
	}
	checks = DeterministicChecks(plan.Turn{Forbidden: []string{"车次："}}, Response{Text: "车次：G7331"})
	if !hasFailure(checks) {
		t.Fatalf("label punctuation was ignored: %#v", checks)
	}
	checks = DeterministicChecks(plan.Turn{Forbidden: []string{"房间木蜡、钓鱼线和现场痕迹"}}, Response{Text: "房间木蜡，钓鱼线和现场痕迹可以相互印证。"})
	if !hasFailure(checks) {
		t.Fatalf("non-label punctuation stopped being punctuation-insensitive: %#v", checks)
	}
}

func TestForbiddenFormattingSentinelsRemainLiteral(t *testing.T) {
	checks := DeterministicChecks(plan.Turn{Forbidden: []string{"1.", "2.", "- ", "###", "```"}}, Response{Text: "后来种子长成了一株向日葵，也带来一个温暖的道理。"})
	if hasFailure(checks) {
		t.Fatalf("ordinary prose failed formatting sentinel checks: %#v", checks)
	}
	checks = DeterministicChecks(plan.Turn{Forbidden: []string{"1."}}, Response{Text: "1. 第一个寓意"})
	if !hasFailure(checks) {
		t.Fatalf("numbered-list marker was not detected: %#v", checks)
	}
}

func TestHanScriptAllowsPreservedLatinFacts(t *testing.T) {
	check := scriptCheck("Alice没有取消G7331次列车。", "han")
	if check.Status != "pass" {
		t.Fatalf("check=%#v", check)
	}
}
