package chatassistant

import (
	"encoding/json"
	"fmt"
	"strings"
	"testing"

	genxeino "github.com/GizClaw/gizclaw-go/pkgs/genx/transformers/eino"
)

// Supply typed real-user/assistant History at the shipped guard's boundary.
// The guarded path must not enter even a model that would emit a ToolCall.
func guardHistory(history []map[string]string) func(*genxeino.GraphDefinition) {
	return func(graph *genxeino.GraphDefinition) {
		data, _ := json.Marshal(history)
		for index := range graph.Nodes {
			if graph.Nodes[index].ID != "guard-cancelled-value" {
				continue
			}
			seed := graph.Nodes[index]
			config := *seed.Script
			config.Source = fmt.Sprintf("def run(input):\n    return {\"messages\": %s}\n", data)
			seed.ID, seed.Script = "fixture-history", &config
			seed.Inputs = nil
			seed.Outputs = map[string]string{"messages": "fixture-messages"}
			graph.Nodes[index].Inputs["messages"] = genxeino.Binding{From: "fixture-messages"}
			graph.Nodes = append(graph.Nodes, seed)
			graph.State.Fields = append(graph.State.Fields, genxeino.StateField{Name: "fixture-messages", Type: genxeino.StateMessages, Merge: genxeino.MergeReplace})
			for edge := range graph.Edges {
				if graph.Edges[edge].From == "capture-observation" && graph.Edges[edge].To == "guard-cancelled-value" {
					graph.Edges[edge].To = "fixture-history"
				}
			}
			graph.Edges = append(graph.Edges, genxeino.EdgeDefinition{From: "fixture-history", To: "guard-cancelled-value"})
			return
		}
		panic("shipped cancellation guard missing")
	}
}

func TestCancelledValuesCannotReachModel(t *testing.T) {
	history := []map[string]string{
		{"role": "user", "content": "帮我调屏幕亮度。"},
		{"role": "assistant", "content": "想调到多少？"},
		{"role": "user", "content": "算了，不调了。"},
		{"role": "assistant", "content": "好，已取消。"},
	}
	for _, value := range []string{"30%", "30", "百分之三十", "三成"} {
		t.Run(value, func(t *testing.T) {
			answer, f, observations := run(t, value, "model-must-not-run", guardHistory(history))
			if !strings.Contains(answer, "已取消") || !strings.Contains(answer, "屏幕还是状态灯") || f.requests != 0 {
				t.Fatalf("cancelled value was not clarified: %q requests=%d", answer, f.requests)
			}
			if err := observationError(value, answer, observations); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestNewExplicitRequestReopensAfterCancellation(t *testing.T) {
	history := []map[string]string{
		{"role": "user", "content": "帮我调屏幕亮度。"},
		{"role": "user", "content": "算了，不调了。"},
		{"role": "user", "content": "重新帮我调状态灯亮度。"},
	}
	answer, _, _ := run(t, "30%", "casual", guardHistory(history))
	if answer != "我会称呼你为米娜。" {
		t.Fatalf("new explicit request failed to reach the model: %q", answer)
	}
}

func TestAssistantCannotCancelUserRequest(t *testing.T) {
	history := []map[string]string{
		{"role": "user", "content": "帮我调屏幕亮度。"},
		{"role": "assistant", "content": "算了，不调了。"},
	}
	answer, _, _ := run(t, "30%", "casual", guardHistory(history))
	if answer != "我会称呼你为米娜。" {
		t.Fatalf("assistant text cancelled user intent: %q", answer)
	}
}

func TestStateQueriesAndPreferencesDoNotReopenCancelledRequest(t *testing.T) {
	for _, text := range []string{"屏幕亮度没有调，保持不动。", "请查询屏幕亮度是多少。", "把屏幕亮度偏好设为30%，只记录。"} {
		history := []map[string]string{
			{"role": "user", "content": "帮我调屏幕亮度。"},
			{"role": "user", "content": "算了，不调了。"},
			{"role": "user", "content": text},
		}
		answer, _, _ := run(t, "30%", "model-must-not-run", guardHistory(history))
		if !strings.Contains(answer, "已取消") {
			t.Fatalf("statement or preference reopened an operation: %q", text)
		}
	}
}
