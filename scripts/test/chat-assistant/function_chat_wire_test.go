package chatassistant

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
	"github.com/openai/openai-go"
	"github.com/openai/openai-go/option"
)

// Exercise the real compatible request serializer with the shipped Model data.
// Both lanes deliberately inherit the same tool context; only the control
// resource may serialize that context into provider tool definitions.
func TestFunctionChatToolIsolationOnTheWire(t *testing.T) {
	for _, tc := range []struct {
		resource string
		tools    bool
	}{
		{"doubao-seed-2-1-lite-no-tools", false},
		{"doubao-seed-2-1-lite", true},
	} {
		t.Run(tc.resource, func(t *testing.T) {
			resource := document(t, "models/"+tc.resource+".yaml")
			data := resource["spec"].(map[string]any)["provider_data"].(map[string]any)
			if data["upstream_model"] != "doubao-seed-2-1-lite-260915" || data["support_tool_calls"] != tc.tools {
				t.Fatal("Both lanes must use the same Seed upstream with distinct tool capability flags")
			}
			requests := make(chan map[string]json.RawMessage, 1)
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				var body map[string]json.RawMessage
				if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
					t.Error(err)
					http.Error(w, "bad body", http.StatusBadRequest)
					return
				}
				requests <- body
				w.Header().Set("Content-Type", "text/event-stream")
				_, _ = io.WriteString(w, "data: {\"id\":\"fixture\",\"object\":\"chat.completion.chunk\",\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\",\"content\":\"Seed回答\"},\"finish_reason\":\"\"}]}\n\ndata: {\"id\":\"fixture\",\"object\":\"chat.completion.chunk\",\"choices\":[{\"index\":0,\"delta\":{},\"finish_reason\":\"stop\"}]}\n\ndata: [DONE]\n\n")
			}))
			defer server.Close()
			client := openai.NewClient(option.WithBaseURL(server.URL+"/"), option.WithAPIKey("synthetic-fixture-only"), option.WithHTTPClient(server.Client()))
			generator := &genx.OpenAIGenerator{Client: &client, Model: data["upstream_model"].(string), SupportToolCalls: data["support_tool_calls"].(bool), TextOnly: true}
			builder := &genx.ModelContextBuilder{}
			builder.UserText("", "你好")
			builder.AddTool(&genx.FuncTool{Name: "screen_brightness", Description: "fixture tool", Parameters: json.RawMessage(`{"type":"object","properties":{"brightness_percent":{"type":"integer"}}}`)})
			stream, err := generator.GenerateStream(t.Context(), "", builder.Build())
			if err != nil {
				t.Fatal(err)
			}
			defer stream.Close()
			for {
				_, err := stream.Next()
				if errors.Is(err, io.EOF) || errors.Is(err, genx.ErrDone) {
					break
				}
				if err != nil {
					t.Fatal(err)
				}
			}
			body := <-requests
			_, hasTools := body["tools"]
			if hasTools != tc.tools {
				t.Errorf("provider tools present=%v, want %v", hasTools, tc.tools)
			}
			if _, forced := body["tool_choice"]; forced {
				t.Error("Neither lane should force a tool call")
			}
		})
	}
}
