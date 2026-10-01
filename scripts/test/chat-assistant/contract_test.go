package chatassistant

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
	genxeino "github.com/GizClaw/gizclaw-go/pkgs/genx/transformers/eino"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/services/ai/workflow/einoconfig"
	"github.com/GizClaw/gizclaw-go/pkgs/giztools"
	"github.com/GizClaw/gizclaw-go/pkgs/store/memory"
	"github.com/cloudwego/eino/components/model"
	"github.com/cloudwego/eino/components/retriever"
	"github.com/cloudwego/eino/schema"
	"github.com/goccy/go-yaml"
	"github.com/google/jsonschema-go/jsonschema"
)

// Read the shipped resources; no copy of the graph or HTTP mapping is maintained here.
func document(t *testing.T, path string) map[string]any {
	t.Helper()
	data, err := os.ReadFile(filepath.Join("..", "..", "..", path))
	if err != nil {
		t.Fatal(err)
	}
	data, err = yaml.YAMLToJSON(data)
	if err != nil {
		t.Fatal(err)
	}
	var result map[string]any
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatal(err)
	}
	return result
}

func decode(t *testing.T, value any, output any) {
	t.Helper()
	data, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(data, output); err != nil {
		t.Fatal(err)
	}
}

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

type fixture struct {
	requests int
	fact     string
	query    string
	body     map[string]any
}

func searchToolkit(t *testing.T, f *fixture) *genx.Toolkit {
	t.Helper()
	resource := document(t, "tools/volc-web-search.yaml")
	spec := resource["spec"].(map[string]any)
	var public apitypes.ToolHTTPRequest
	decode(t, spec["http"], &public)
	var argument jsonschema.Schema
	decode(t, spec["input_schema"], &argument)
	timeout, err := time.ParseDuration(public.Timeout)
	if err != nil {
		t.Fatal(err)
	}
	operation := giztools.HTTPOperation{
		URL: public.Url, Method: string(public.Method), Timeout: timeout,
		ResponsePointer: public.ResponsePointer, MaxResponseBytes: int64(public.MaxResponseBytes),
	}
	for _, binding := range *public.Body {
		required := binding.Required == nil || *binding.Required
		operation.Body = append(operation.Body, giztools.HTTPBinding{
			ArgumentPointer: binding.ArgumentPointer, Target: binding.Target, Required: required,
		})
	}
	executor := giztools.HTTPExecutor{Transport: roundTripFunc(func(request *http.Request) (*http.Response, error) {
		f.requests++
		if request.Method != "POST" || request.URL.String() != "https://open.feedcoopapi.com/search_api/web_search" {
			return nil, fmt.Errorf("unexpected search destination: %s %s", request.Method, request.URL)
		}
		var body map[string]any
		if err := json.NewDecoder(request.Body).Decode(&body); err != nil {
			return nil, err
		}
		f.body = body
		if body["Query"] != f.query || body["SearchType"] != "web" || body["Count"] != float64(3) {
			return nil, fmt.Errorf("wrong search argument mapping: %#v", body)
		}
		// This value exists only in the HTTP fixture, never in the prompt or model's first round.
		data, _ := json.Marshal(map[string]any{"Result": map[string]string{"fact": f.fact}})
		return &http.Response{StatusCode: 200, Header: http.Header{"Content-Type": {"application/json"}},
			Body: io.NopCloser(bytes.NewReader(data))}, nil
	})}
	tool := &genx.FuncTool{Name: spec["invoke_name"].(string), Description: spec["description"].(string), Argument: &argument,
		Invoke: func(ctx context.Context, _ *genx.FuncCall, input string) (any, error) {
			result, err := executor.Invoke(ctx, operation, json.RawMessage(input), nil)
			if err != nil {
				return nil, err
			}
			var value any
			err = json.Unmarshal(result, &value)
			return value, err
		}}
	toolkit, err := genx.NewToolkit(tool)
	if err != nil {
		t.Fatal(err)
	}
	return toolkit
}

type scriptedModel struct {
	mode   string
	rounds int
}

func (m *scriptedModel) Generate(ctx context.Context, input []*schema.Message, opts ...model.Option) (*schema.Message, error) {
	r, err := m.Stream(ctx, input, opts...)
	if err != nil {
		return nil, err
	}
	defer r.Close()
	return r.Recv()
}
func (m *scriptedModel) Stream(_ context.Context, input []*schema.Message, opts ...model.Option) (*schema.StreamReader[*schema.Message], error) {
	options := model.GetCommonOptions(nil, opts...)
	if len(options.Tools) != 1 || options.Tools[0].Name != "web_search" {
		return nil, errors.New("the Model did not receive the declared search Tool")
	}
	m.rounds++
	if m.mode == "fabricated" {
		return schema.StreamReaderFromArray([]*schema.Message{schema.AssistantMessage("上海今天晴，25度，今天9月21日。", nil)}), nil
	}
	if m.mode == "casual" {
		return schema.StreamReaderFromArray([]*schema.Message{schema.AssistantMessage("我会称呼你为米娜。", nil)}), nil
	}
	if m.rounds == 1 {
		query := input[len(input)-1].Content
		arguments := map[string]any{"query": query, "search_type": "web", "count": 3}
		if m.mode == "search-null" {
			arguments["time_range"] = nil
		}
		args, _ := json.Marshal(arguments)
		return schema.StreamReaderFromArray([]*schema.Message{{Role: schema.Assistant, Content: "我查一下。",
			ToolCalls: []schema.ToolCall{{ID: "search-1", Type: "function", Function: schema.FunctionCall{Name: "web_search", Arguments: string(args)}}}}}), nil
	}
	last := input[len(input)-1]
	if m.rounds != 2 || last.Role != schema.Tool || last.ToolCallID != "search-1" {
		return nil, fmt.Errorf("missing matching Tool result: %#v", last)
	}
	var result struct{ Fact string }
	if err := json.Unmarshal([]byte(last.Content), &result); err != nil {
		return nil, err
	}
	if result.Fact == "" {
		return nil, errors.New("response_pointer dropped the controlled search fact")
	}
	return schema.StreamReaderFromArray([]*schema.Message{schema.AssistantMessage(result.Fact, nil)}), nil
}

type components struct{ chat model.BaseChatModel }

func (c components) ResolveChatModel(_ context.Context, alias string) (model.BaseChatModel, error) {
	if alias != "eino-chat-assistant.model" {
		return nil, fmt.Errorf("unexpected Model alias %q", alias)
	}
	return c.chat, nil
}
func (components) ResolveRetriever(context.Context, string) (retriever.Retriever, error) {
	return nil, errors.New("unexpected retriever")
}

type memoryStore struct{ observed chan memory.Observation }

func (*memoryStore) SupportsDirectFactObservation() bool { return true }
func (*memoryStore) Recall(context.Context, memory.Query) (memory.RecallResult, error) {
	return memory.RecallResult{}, nil
}
func (s *memoryStore) Observe(_ context.Context, observation memory.Observation) (memory.ObserveResult, error) {
	s.observed <- observation
	return memory.ObserveResult{}, nil
}
func (*memoryStore) Update(context.Context, memory.UpdateRequest) (memory.Fact, error) {
	return memory.Fact{}, errors.New("unexpected update")
}
func (*memoryStore) Delete(context.Context, memory.DeleteRequest) error {
	return errors.New("unexpected delete")
}

func run(t *testing.T, input, mode string) (string, *fixture, memory.Observation) {
	t.Helper()
	workflow := document(t, "workflows/chat-assistant/eino.yaml")["spec"].(map[string]any)
	if workflow["memory"] != "user-chat-with-assistant" {
		t.Fatal("Chat Memory layout changed")
	}
	ids := workflow["toolkit"].(map[string]any)["tool_ids"].([]any)
	if len(ids) != 1 || ids[0] != "volc-web-search" {
		t.Fatal("Workflow search allow-list changed")
	}
	for _, path := range []string{"runtime-profiles/default.yaml", "runtime-profiles/testing.yaml"} {
		profile := document(t, path)["spec"].(map[string]any)
		tools := profile["resources"].(map[string]any)["tools"].(map[string]any)
		if tools["web-search"].(map[string]any)["resource_id"] != ids[0] {
			t.Fatal("unbound search Tool")
		}
	}
	var public apitypes.EinoWorkflowSpec
	decode(t, workflow["eino"], &public)
	graph, err := einoconfig.MapGraph(public.Graph)
	if err != nil {
		t.Fatal(err)
	}
	for _, node := range graph.Nodes {
		if node.MemoryObserve != nil && node.MemoryObserve.WaitForCompletion {
			t.Fatal("memory observation must remain asynchronous")
		}
	}
	nonce := make([]byte, 16)
	if _, err := rand.Read(nonce); err != nil {
		t.Fatal(err)
	}
	f := &fixture{query: input, fact: "搜索结果报码" + hex.EncodeToString(nonce)}
	store := &memoryStore{observed: make(chan memory.Observation, 1)}
	transformer, err := genxeino.New(t.Context(), genxeino.Config{
		Agent: genxeino.AgentConfig{ID: "chat-assistant-contract"}, Graph: graph,
		Components: components{chat: &scriptedModel{mode: mode}}, ToolInvoker: searchToolkit(t, f),
		Memory: &genxeino.MemoryConfig{Store: store, Scope: memory.Scope{AppID: "chat-assistant-contract"}},
	})
	if err != nil {
		t.Fatal(err)
	}
	b := genx.NewGrowableStreamBuilder((&genx.ModelContextBuilder{}).Build(), 8)
	if err := b.Add(genx.NewBeginOfStream(genx.NewStreamID()), &genx.MessageChunk{Role: genx.RoleUser, Part: genx.Text(input)}, genx.NewTextEndOfStream()); err != nil {
		t.Fatal(err)
	}
	if err := b.Done(genx.Usage{}); err != nil {
		t.Fatal(err)
	}
	output, err := transformer.Transform(t.Context(), b.Stream())
	if err != nil {
		t.Fatal(err)
	}
	var text strings.Builder
	for {
		chunk, err := output.Next()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			t.Fatal(err)
		}
		if chunk.Ctrl != nil && chunk.Ctrl.Error != "" {
			t.Fatal(chunk.Ctrl.Error)
		}
		if part, ok := chunk.Part.(genx.Text); ok && !chunk.IsEndOfStream() {
			text.WriteString(string(part))
		}
	}
	select {
	case observation := <-store.observed:
		return text.String(), f, observation
	case <-time.After(time.Second):
		t.Fatal("the completed turn was not observed")
	}
	return "", nil, memory.Observation{}
}

func searchResultError(text string, f *fixture) error {
	if f.requests != 1 {
		return fmt.Errorf("actual search requests = %d, want 1", f.requests)
	}
	if text != "我查一下。"+f.fact {
		return errors.New("answer does not contain the controlled search result")
	}
	return nil
}

func TestQualitySearchInputsUseControlledResults(t *testing.T) {
	quality := document(t, "tests/giztest/quality/chat-assistant.eino.giztest.yaml")
	probes := 0
	for _, entry := range quality["steps"].([]any) {
		step := entry.(map[string]any)
		if step["id"] != "eino_quality_4" && step["id"] != "eino_quality_5" {
			continue
		}
		probes++
		t.Run(step["id"].(string), func(t *testing.T) {
			text, f, _ := run(t, step["peer_stream"].(map[string]any)["input"].(string), "search")
			if err := searchResultError(text, f); err != nil {
				t.Fatal(err)
			}
		})
	}
	if probes != 2 {
		t.Fatal("weather/date live probes missing")
	}
}

func TestSearchOracleRejectsFabricatedWeatherAndDate(t *testing.T) {
	text, f, _ := run(t, "上海今天天气怎么样？", "fabricated")
	if !strings.Contains(text, "度") || !strings.Contains(text, "月") {
		t.Fatal("fixture must pass the former keyword-only gates")
	}
	if err := searchResultError(text, f); err == nil {
		t.Fatal("fabricated weather/date passed without executing web_search")
	}
}

func TestOptionalSearchTimeRange(t *testing.T) {
	// Ark can emit explicit null for an optional field. Exercise the shipped
	// schema and the real executor, including its absent-versus-null mapping.
	for _, suffix := range []string{"", `,"time_range":null`, `,"time_range":"OneDay"`} {
		t.Run(suffix, func(t *testing.T) {
			f := &fixture{query: "天气", fact: "结果"}
			_, err := searchToolkit(t, f).InvokeTool(t.Context(), "web_search",
				json.RawMessage(`{"query":"天气","search_type":"web","count":3`+suffix+`}`))
			if err != nil {
				t.Fatal(err)
			}
			value, present := f.body["TimeRange"]
			if f.requests != 1 || present != (suffix != "") ||
				(suffix == `,"time_range":null` && value != nil) ||
				(suffix == `,"time_range":"OneDay"` && value != "OneDay") {
				t.Fatalf("unexpected HTTP mapping: %#v", f.body)
			}
		})
	}
	for _, invalid := range []string{`""`, `"Yesterday"`, `42`} {
		f := &fixture{query: "天气"}
		_, err := searchToolkit(t, f).InvokeTool(t.Context(), "web_search",
			json.RawMessage(`{"query":"天气","search_type":"web","count":3,"time_range":`+invalid+`}`))
		if err == nil || f.requests != 0 {
			t.Fatalf("invalid time range reached HTTP executor: %s", invalid)
		}
	}
	text, f, _ := run(t, "上海今天天气怎么样？", "search-null")
	if err := searchResultError(text, f); err != nil {
		t.Fatal(err)
	}
}

func TestObservesUserAndAssistantWithoutSearchingCasualTurn(t *testing.T) {
	input := "以后请叫我米娜。"
	text, f, observation := run(t, input, "casual")
	if f.requests != 0 {
		t.Fatal("casual turn unexpectedly searched")
	}
	if len(observation.Facts) != 2 || observation.Facts[0].Text != input || observation.Facts[1].Text != text {
		t.Fatalf("observation lost the user or assistant turn: %#v", observation.Facts)
	}
}
