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
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
	genxeino "github.com/GizClaw/gizclaw-go/pkgs/genx/transformers/eino"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/services/ai/workflow/einoconfig"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/services/runtime/toolkit"
	"github.com/GizClaw/gizclaw-go/pkgs/giztools"
	"github.com/GizClaw/gizclaw-go/pkgs/store/memory"
	"github.com/GizClaw/gizclaw-go/pkgs/store/memory/mem0"
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
	requests      int
	fact          string
	query         string
	body          map[string]any
	memoryMu      sync.Mutex
	memoryBatches [][]string
}

func searchToolkit(t *testing.T, f *fixture, mutations ...func(*giztools.HTTPOperation)) *genx.Toolkit {
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
	for _, mutate := range mutations {
		mutate(&operation)
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

type memoryStore struct {
	observed chan memory.Observation
	delegate memory.Store
}

func (*memoryStore) SupportsDirectFactObservation() bool { return true }
func (*memoryStore) Recall(context.Context, memory.Query) (memory.RecallResult, error) {
	return memory.RecallResult{}, nil
}
func (s *memoryStore) Observe(ctx context.Context, observation memory.Observation) (memory.ObserveResult, error) {
	result, err := s.delegate.Observe(ctx, observation)
	if err != nil {
		return result, err
	}
	s.observed <- observation
	return result, nil
}
func (*memoryStore) Update(context.Context, memory.UpdateRequest) (memory.Fact, error) {
	return memory.Fact{}, errors.New("unexpected update")
}
func (*memoryStore) Delete(context.Context, memory.DeleteRequest) error {
	return errors.New("unexpected delete")
}

func run(t *testing.T, input, mode string, mutations ...func(*genxeino.GraphDefinition)) (string, *fixture, []memory.Observation) {
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
	for _, mutate := range mutations {
		mutate(&graph)
	}
	nonce := make([]byte, 16)
	if _, err := rand.Read(nonce); err != nil {
		t.Fatal(err)
	}
	f := &fixture{query: input, fact: "搜索结果报码" + hex.EncodeToString(nonce)}
	// Exercise the real self-hosted adapter with a keyed multi-fact HTTP batch.
	memoryHTTP := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, request *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if request.URL.Path == "/search" {
			_, _ = io.WriteString(w, `{"results":[]}`)
			return
		}
		if request.URL.Path != "/memories" || request.Method != "POST" {
			http.Error(w, "unexpected Mem0 operation", http.StatusBadRequest)
			return
		}
		var body map[string]any
		if err := json.NewDecoder(request.Body).Decode(&body); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		messages, ok := body["messages"].([]any)
		if !ok || len(messages) == 0 || body["infer"] != false || body["observation_id"] == nil || body["observation_digest"] == nil {
			http.Error(w, "expected keyed direct-fact batch", http.StatusBadRequest)
			return
		}
		var batch []string
		for _, value := range messages {
			batch = append(batch, value.(map[string]any)["content"].(string))
		}
		f.memoryMu.Lock()
		f.memoryBatches = append(f.memoryBatches, batch)
		f.memoryMu.Unlock()
		var results []any
		for index, value := range messages {
			message := value.(map[string]any)
			metadata, _ := message["metadata"].(map[string]any)
			if metadata == nil {
				metadata = map[string]any{}
			}
			metadata["gizclaw.observation_id"] = body["observation_id"]
			metadata["gizclaw.observation_digest"] = body["observation_digest"]
			metadata["gizclaw.fact_index"] = index
			results = append(results, map[string]any{
				"id": fmt.Sprintf("fact-%s-%d", body["observation_id"], index), "memory": message["content"],
				"user_id": body["user_id"], "metadata": metadata,
			})
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"results": results})
	}))
	t.Cleanup(memoryHTTP.Close)
	delegate, err := mem0.New(mem0.Config{Endpoint: memoryHTTP.URL, Flavor: mem0.SelfHosted, HTTPClient: memoryHTTP.Client()})
	if err != nil {
		t.Fatal(err)
	}
	store := &memoryStore{observed: make(chan memory.Observation, 4), delegate: delegate}
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
	var observations []memory.Observation
	for _, node := range graph.Nodes {
		if node.MemoryObserve == nil {
			continue
		}
		select {
		case observation := <-store.observed:
			observations = append(observations, observation)
		case <-time.After(time.Second):
			t.Fatal("the completed turn was not observed")
		}
	}
	f.memoryMu.Lock()
	defer f.memoryMu.Unlock()
	if len(f.memoryBatches) != len(observations) {
		t.Fatal("wrong number of Mem0 HTTP batches")
	}
	for index, observation := range observations {
		batch := f.memoryBatches[index]
		if len(batch) != len(observation.Facts) {
			t.Fatalf("Mem0 HTTP lost a fact: got %#v for %#v", batch, observation.Facts)
		}
		for factIndex, fact := range observation.Facts {
			if batch[factIndex] != fact.Text {
				t.Fatalf("Mem0 HTTP changed fact order or text: got %#v", batch)
			}
		}
	}
	return text.String(), f, observations
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
	var argument jsonschema.Schema
	decode(t, document(t, "tools/volc-web-search.yaml")["spec"].(map[string]any)["input_schema"], &argument)
	catalogTool := toolkit.Tool{InputSchema: *argument.CloneSchemas()}
	for _, suffix := range []string{"", `,"time_range":null`, `,"time_range":"OneDay"`} {
		t.Run(suffix, func(t *testing.T) {
			f := &fixture{query: "天气", fact: "结果"}
			args := json.RawMessage(`{"query":"天气","search_type":"web","count":3` + suffix + `}`)
			if err := toolkit.ValidateToolArgs(catalogTool, args); err != nil {
				t.Fatal(err)
			}
			_, err := searchToolkit(t, f).InvokeTool(t.Context(), "web_search",
				args)
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
	for _, invalid := range []string{`""`, `"null"`, `"Yesterday"`, `42`} {
		f := &fixture{query: "天气"}
		args := json.RawMessage(`{"query":"天气","search_type":"web","count":3,"time_range":` + invalid + `}`)
		if err := toolkit.ValidateToolArgs(catalogTool, args); err == nil {
			t.Fatalf("invalid time range passed the runtime authorizer: %s", invalid)
		}
		_, err := searchToolkit(t, f).InvokeTool(t.Context(), "web_search",
			args)
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
	if err := observationError(input, text, observation); err != nil {
		t.Fatal(err)
	}
}

func observationError(input, answer string, observations []memory.Observation) error {
	if len(observations) != 1 || len(observations[0].Facts) != 2 ||
		observations[0].Facts[0].Text != input || observations[0].Facts[1].Text != answer || observations[0].ID == "" {
		return fmt.Errorf("one observation lost the user or assistant facts: %#v", observations)
	}
	return nil
}

func TestObservationOracleRejectsMissingAssistantCandidate(t *testing.T) {
	input := "以后请叫我米娜。"
	answer, _, observations := run(t, input, "casual", func(graph *genxeino.GraphDefinition) {
		for i := range graph.Nodes {
			if node := graph.Nodes[i].MemoryObserve; node != nil {
				node.Facts = node.Facts[:1]
			}
		}
	})
	if len(observations) != 1 || len(observations[0].Facts) != 1 || observations[0].Facts[0].Text != input {
		t.Fatalf("mutation did not remove only the assistant fact: %#v", observations)
	}
	if err := observationError(input, answer, observations); err == nil {
		t.Fatal("missing assistant fact passed the complete-turn oracle")
	}
}

func TestSearchRejectsBrokenResponsePointer(t *testing.T) {
	f := &fixture{query: "上海天气", fact: "仅存在于HTTP响应中的事实"}
	toolkit := searchToolkit(t, f, func(operation *giztools.HTTPOperation) {
		pointer := "/Result/missing"
		operation.ResponsePointer = &pointer
	})
	_, err := toolkit.InvokeTool(t.Context(), "web_search",
		json.RawMessage(`{"query":"上海天气","search_type":"web","count":3}`))
	if f.requests != 1 {
		t.Fatalf("broken pointer test did not execute HTTP: requests=%d", f.requests)
	}
	if err == nil {
		t.Fatal("broken response pointer was accepted by the real HTTP Tool executor")
	}
}
