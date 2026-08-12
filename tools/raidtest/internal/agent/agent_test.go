package agent

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/GizClaw/raids/tools/raidtest/internal/conversation"
	"github.com/GizClaw/raids/tools/raidtest/internal/openai"
	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
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
	checks, err := a.Judge(context.Background(), "persona", plan.Turn{User: "hello", Judge: []string{"continuity", "naturalness"}}, conversation.Response{Text: "hi"})
	if err != nil || attempt != 2 || len(checks) != 2 {
		t.Fatalf("attempt=%d checks=%#v err=%v", attempt, checks, err)
	}
}
