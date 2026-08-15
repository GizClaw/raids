package acceptance

import (
	"context"
	"encoding/json"
	"strings"
	"testing"
)

func validSubmission() Submission {
	return Submission{
		CaseID: "case-1", TargetWorkflowID: "target", ResponseID: "response-1", TurnID: "turn-1",
		Action: ActionContinue, NextMessage: "继续调查。",
		Checks: []Check{
			{Name: "instruction_following", Status: "pass", Detail: "遵循", Evidence: "回复遵循当前要求"},
			{Name: "continuity", Status: "pass", Detail: "连续", Evidence: "承接当前调查阶段"},
			{Name: "factuality", Status: "pass", Detail: "事实一致", Evidence: "事实与已公开线索一致"},
			{Name: "non_repetition", Status: "pass", Detail: "无重复", Evidence: "没有重复固定套话"},
		},
		Summary: "可以继续",
	}
}

func TestHandlerRejectsMissingOrOversizedEvidence(t *testing.T) {
	for name, evidence := range map[string]string{"missing": "", "oversized": strings.Repeat("证", 513)} {
		t.Run(name, func(t *testing.T) {
			var handler Handler
			_, _ = handler.Arm(Expectation{CaseID: "case-1", TargetWorkflowID: "target", ResponseID: "response-1", TurnID: "turn-1"})
			submission := validSubmission()
			submission.Checks[0].Evidence = evidence
			body, _ := json.Marshal(submission)
			if _, err := handler.Handle(context.Background(), body); err == nil {
				t.Fatal("invalid evidence was accepted")
			}
		})
	}
}

func TestHandlerCorrelatesOneSubmission(t *testing.T) {
	var handler Handler
	result, err := handler.Arm(Expectation{CaseID: "case-1", TargetWorkflowID: "target", ResponseID: "response-1", TurnID: "turn-1"})
	if err != nil {
		t.Fatal(err)
	}
	body, _ := json.Marshal(validSubmission())
	response, err := handler.Handle(context.Background(), body)
	if err != nil || string(response) != `{"accepted":true}` {
		t.Fatalf("response=%s err=%v", response, err)
	}
	if got := <-result; got.NextMessage != "继续调查。" {
		t.Fatalf("submission=%#v", got)
	}
	if _, err := handler.Handle(context.Background(), body); err == nil {
		t.Fatal("duplicate submission was accepted")
	}
}

func TestHandlerAllowsFailedCheckWhileContinuingCoverage(t *testing.T) {
	var handler Handler
	result, _ := handler.Arm(Expectation{CaseID: "case-1", TargetWorkflowID: "target", ResponseID: "response-1", TurnID: "turn-1"})
	submission := validSubmission()
	submission.Checks[0].Status = "fail"
	body, _ := json.Marshal(submission)
	if _, err := handler.Handle(context.Background(), body); err != nil {
		t.Fatalf("continue with a retained failed check: %v", err)
	}
	if got := <-result; got.Checks[0].Status != "fail" {
		t.Fatalf("submission=%#v", got)
	}
}

func TestHandlerRejectsPassWithFailedCheck(t *testing.T) {
	var handler Handler
	_, _ = handler.Arm(Expectation{CaseID: "case-1", TargetWorkflowID: "target", ResponseID: "response-1", TurnID: "turn-1"})
	submission := validSubmission()
	submission.Action = ActionPass
	submission.NextMessage = ""
	submission.Checks[0].Status = "fail"
	body, _ := json.Marshal(submission)
	if _, err := handler.Handle(context.Background(), body); err == nil {
		t.Fatal("pass with a failed check was accepted")
	}
	if err := handler.Cancel(); err == nil {
		t.Fatal("rejected Tool submission was not retained for the runner")
	}
}

func TestHandlerRejectsCorrelationMismatch(t *testing.T) {
	var handler Handler
	_, _ = handler.Arm(Expectation{CaseID: "case-1", TargetWorkflowID: "target", ResponseID: "response-1", TurnID: "turn-1"})
	submission := validSubmission()
	submission.ResponseID = "other"
	body, _ := json.Marshal(submission)
	if _, err := handler.Handle(context.Background(), body); err == nil {
		t.Fatal("mismatched response was accepted")
	}
}
