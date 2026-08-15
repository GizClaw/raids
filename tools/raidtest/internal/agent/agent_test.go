package agent

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/GizClaw/raids/tools/raidtest/internal/conversation"
	"github.com/GizClaw/raids/tools/raidtest/internal/openai"
	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
	"github.com/GizClaw/raids/tools/raidtest/internal/report"
)

func TestAgentTypesRemainExplicit(t *testing.T) {
	a := Agent{Model: "model"}
	if a.Model != "model" {
		t.Fatal("model changed")
	}
}

func TestJudgeRetriesUntilEveryRequestedDimensionIsPresent(t *testing.T) {
	attempt := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		attempt++
		checks := []map[string]any{{"name": "continuity", "pass": true, "detail": "ok"}}
		if attempt == 2 {
			checks = append(checks, map[string]any{"name": "naturalness", "pass": true, "detail": "ok"})
		}
		content, _ := json.Marshal(map[string]any{"checks": checks})
		_ = json.NewEncoder(w).Encode(map[string]any{"choices": []any{map[string]any{"message": map[string]string{"content": string(content)}}}})
	}))
	defer server.Close()
	a := Agent{Client: openai.Client{BaseURL: server.URL, APIKey: "key", HTTPClient: server.Client()}, Model: "judge"}
	checks, err := a.Judge(context.Background(), "persona", nil, plan.Turn{User: "hello", Judge: []string{"continuity", "naturalness"}}, conversation.Response{Text: "hi"})
	if err != nil || attempt != 2 || len(checks) != 2 {
		t.Fatalf("attempt=%d checks=%#v err=%v", attempt, checks, err)
	}
}

func TestJudgeUsesBoundedThirdAttemptForMalformedOutput(t *testing.T) {
	attempt := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		attempt++
		content := "not-json"
		if attempt == judgeMaxAttempts {
			content = `{"checks":[{"name":"continuity","pass":true,"detail":"ok"}]}`
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"choices": []any{map[string]any{"message": map[string]string{"content": content}}}})
	}))
	defer server.Close()
	a := Agent{Client: openai.Client{BaseURL: server.URL, APIKey: "key", HTTPClient: server.Client()}, Model: "judge"}
	checks, err := a.Judge(context.Background(), "persona", nil, plan.Turn{User: "hello", Judge: []string{"continuity"}}, conversation.Response{Text: "hi"})
	if err != nil || attempt != judgeMaxAttempts || len(checks) != 1 {
		t.Fatalf("attempt=%d checks=%#v err=%v", attempt, checks, err)
	}
}

func TestJudgeUsesFinalAdjudicatorForDisputedSemanticFailure(t *testing.T) {
	attempt := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		attempt++
		passing := attempt > 1
		content, _ := json.Marshal(map[string]any{"checks": []map[string]any{{"name": "continuity", "pass": passing, "detail": "evidence"}}})
		_ = json.NewEncoder(w).Encode(map[string]any{"choices": []any{map[string]any{"message": map[string]string{"content": string(content)}}}})
	}))
	defer server.Close()
	a := Agent{Client: openai.Client{BaseURL: server.URL, APIKey: "key", HTTPClient: server.Client()}, Model: "judge"}
	checks, err := a.Judge(context.Background(), "persona", nil, plan.Turn{User: "hello", Judge: []string{"continuity"}}, conversation.Response{Text: "hi"})
	if err != nil || attempt != 3 || len(checks) != 1 || checks[0].Status != "pass" || !strings.Contains(checks[0].Detail, "disputed 1-1; final adjudication") {
		t.Fatalf("attempt=%d checks=%#v err=%v", attempt, checks, err)
	}
}

func TestJudgeFinalAdjudicatorCanRetainDisputedFailure(t *testing.T) {
	attempt := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		attempt++
		passing := attempt == 2
		content, _ := json.Marshal(map[string]any{"checks": []map[string]any{{"name": "continuity", "pass": passing, "detail": "evidence"}}})
		_ = json.NewEncoder(w).Encode(map[string]any{"choices": []any{map[string]any{"message": map[string]string{"content": string(content)}}}})
	}))
	defer server.Close()
	a := Agent{Client: openai.Client{BaseURL: server.URL, APIKey: "key", HTTPClient: server.Client()}, Model: "judge"}
	checks, err := a.Judge(context.Background(), "persona", nil, plan.Turn{User: "hello", Judge: []string{"continuity"}}, conversation.Response{Text: "hi"})
	if err != nil || attempt != 3 || len(checks) != 1 || checks[0].Status != "fail" || !strings.Contains(checks[0].Detail, "disputed 1-1; final adjudication") {
		t.Fatalf("attempt=%d checks=%#v err=%v", attempt, checks, err)
	}
}

func TestJudgeRetainsConfirmedSemanticFailure(t *testing.T) {
	attempt := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		attempt++
		content := `{"checks":[{"name":"continuity","pass":false,"detail":"concrete contradiction"}]}`
		_ = json.NewEncoder(w).Encode(map[string]any{"choices": []any{map[string]any{"message": map[string]string{"content": content}}}})
	}))
	defer server.Close()
	a := Agent{Client: openai.Client{BaseURL: server.URL, APIKey: "key", HTTPClient: server.Client()}, Model: "judge"}
	checks, err := a.Judge(context.Background(), "persona", nil, plan.Turn{User: "hello", Judge: []string{"continuity"}}, conversation.Response{Text: "hi"})
	if err != nil || attempt != 2 || len(checks) != 1 || checks[0].Status != "fail" {
		t.Fatalf("attempt=%d checks=%#v err=%v", attempt, checks, err)
	}
}

func TestJudgeReceivesOrderedHistoryIncludingFailedTurns(t *testing.T) {
	var prompt string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var request struct {
			Messages []openai.Message `json:"messages"`
		}
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			t.Errorf("decode request: %v", err)
		}
		prompt = request.Messages[1].Content
		content := `{"checks":[{"name":"history-continuity","pass":true,"detail":"ok"}]}`
		_ = json.NewEncoder(w).Encode(map[string]any{"choices": []any{map[string]any{"message": map[string]string{"content": content}}}})
	}))
	defer server.Close()
	a := Agent{Client: openai.Client{BaseURL: server.URL, APIKey: "key", HTTPClient: server.Client()}, Model: "judge"}
	history := []report.Turn{
		{ID: "first", User: "鞋印是42码", Assistant: "记住了", Status: "pass"},
		{ID: "correction", User: "更正为39码", Assistant: "仍然是42码", Status: "fail"},
	}
	_, err := a.Judge(context.Background(), "persona", history, plan.Turn{User: "现在多少码", Judge: []string{"history-continuity"}}, conversation.Response{Text: "39码"})
	if err != nil {
		t.Fatal(err)
	}
	first := strings.Index(prompt, `"id":"first"`)
	correction := strings.Index(prompt, `"id":"correction"`)
	if first < 0 || correction <= first || !strings.Contains(prompt, `"status":"fail"`) {
		t.Fatalf("history missing or unordered in prompt: %s", prompt)
	}
}

func TestGenerateReceivesPriorHistory(t *testing.T) {
	var prompt string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var request struct {
			Messages []openai.Message `json:"messages"`
		}
		_ = json.NewDecoder(r.Body).Decode(&request)
		prompt = request.Messages[1].Content
		_ = json.NewEncoder(w).Encode(map[string]any{"choices": []any{map[string]any{"message": map[string]string{"content": "我想核对厨师刚才实际说过的证词。"}}}})
	}))
	defer server.Close()
	a := Agent{Client: openai.Client{BaseURL: server.URL, APIKey: "key", HTTPClient: server.Client()}, Model: "agent"}
	history := []report.Turn{{ID: "interview-chef", User: "厨师在哪里", Assistant: "我当时在厨房。", Status: "pass"}}
	utterance, err := a.Generate(context.Background(), "persona", history, plan.Turn{Intent: "核对厨师证词"})
	if err != nil || utterance == "" || !strings.Contains(prompt, `"id":"interview-chef"`) || !strings.Contains(prompt, "Do not") {
		t.Fatalf("utterance=%q prompt=%q err=%v", utterance, prompt, err)
	}
}

func TestJudgeHistoryKeepsNewestCompleteTurnsWithinBound(t *testing.T) {
	history := make([]report.Turn, 0, 60)
	for index := 0; index < 60; index++ {
		history = append(history, report.Turn{ID: fmt.Sprintf("turn-%02d", index), User: strings.Repeat("用", 120), Assistant: strings.Repeat("答", 120), Status: "pass"})
	}
	encoded := boundedHistory(history)
	if len([]rune(encoded)) > judgeHistoryMaxRunes {
		t.Fatalf("history has %d runes", len([]rune(encoded)))
	}
	if !strings.Contains(encoded, `"id":"turn-59"`) || strings.Contains(encoded, `"id":"turn-00"`) {
		t.Fatalf("expected newest bounded suffix, got %s", encoded)
	}
	if strings.Index(encoded, `"id":"turn-58"`) > strings.Index(encoded, `"id":"turn-59"`) {
		t.Fatalf("history not chronological: %s", encoded)
	}
}
