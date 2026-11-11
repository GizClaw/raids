package chatassistant

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"slices"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
	eino "github.com/GizClaw/gizclaw-go/pkgs/genx/transformers/eino"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/services/ai/workflow/einoconfig"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/services/runtime/agenthost"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/services/runtime/toolcatalog"
	"github.com/GizClaw/gizclaw-go/pkgs/store/memory"
	"github.com/cloudwego/eino/components/model"
	"github.com/cloudwego/eino/components/retriever"
	"github.com/cloudwego/eino/schema"
)

func TestFunctionChatProfileModelIsolation(t *testing.T) {
	for _, path := range profilePaths {
		t.Run(path, func(t *testing.T) {
			profile := chatProfile(t, path)
			models := *profile.Spec.Resources.Models
			if models["eino-function-chat.model"].ResourceId != "doubao-seed-2-1-lite-no-tools" ||
				models["eino-function-chat.classify"].ResourceId != "doubao-seed-2-1-lite-no-tools" ||
				models["eino-function-chat.intent"].ResourceId != "doubao-seed-2-1-lite" {
				t.Fatal("Function Chat needs tools-disabled conversation/metadata and a tool-enabled intent agent")
			}
			binding := profile.Spec.Workflows["function-assistant"]
			if binding.ResourceId != "eino-function-chat" || binding.Toolkit == nil || binding.Toolkit.VerificationModel != nil {
				t.Fatal("Function Chat must retain its declared toolkit and model-capability isolation")
			}
			names, err := toolcatalog.Selection(profile, "function-assistant", "eino-function-chat", nil)
			if err != nil || len(names) != 9 || slices.Contains(names, "web.search") {
				t.Fatal("Function Chat must explicitly select its nine native controls")
			}
		})
	}
}

type functionProposal struct{ name, args string }

type functionTurn struct {
	input, route, status, chat, intent, want string
	proposals                                []functionProposal
	wantChat, wantIntent, pending, cancelled bool
}

type functionCounts struct{ chat, route, intent, status int }

type functionComponents struct {
	fixture  *functionFixture
	turn     functionTurn
	started  [2]chan struct{}
	parallel bool
	mu       sync.Mutex
	counts   functionCounts
}

func (c *functionComponents) ResolveChatModel(_ context.Context, name string) (model.BaseChatModel, error) {
	kind := "chat"
	if strings.HasSuffix(name, ".classify") {
		kind = "metadata"
	} else if strings.HasSuffix(name, ".intent") {
		kind = "intent"
	}
	return &functionModel{components: c, kind: kind}, nil
}
func (*functionComponents) ResolveRetriever(context.Context, string) (retriever.Retriever, error) {
	return nil, errors.New("unexpected retriever")
}

type functionModel struct {
	components *functionComponents
	kind       string
	rounds     int
}

func (m *functionModel) Generate(ctx context.Context, messages []*schema.Message, options ...model.Option) (*schema.Message, error) {
	stream, err := m.Stream(ctx, messages, options...)
	if err != nil {
		return nil, err
	}
	defer stream.Close()
	return stream.Recv()
}
func (m *functionModel) Stream(ctx context.Context, messages []*schema.Message, _ ...model.Option) (*schema.StreamReader[*schema.Message], error) {
	c := m.components
	var content strings.Builder
	for _, message := range messages {
		content.WriteString(message.Content)
		content.WriteByte('\n')
	}
	if !strings.Contains(content.String(), c.fixture.memoryNonce) {
		return nil, errors.New("agent did not receive the shared recalled Memory")
	}
	if c.fixture.history.hasEntries() && !strings.Contains(content.String(), c.fixture.historyNonce) {
		return nil, errors.New("agent did not receive the shared chat History")
	}
	kind := m.kind
	if kind == "metadata" {
		kind = "route"
		for _, message := range messages {
			if message.Role == schema.System && strings.Contains(message.Content, "内部意图状态记录器") {
				kind = "status"
			}
		}
	}
	c.mu.Lock()
	switch kind {
	case "chat":
		c.counts.chat++
	case "route":
		c.counts.route++
	case "status":
		c.counts.status++
	case "intent":
		c.counts.intent++
	}
	c.mu.Unlock()
	// Idle turns must start both conversation and intent routing before either
	// model finishes. Pending turns intentionally do not use this barrier.
	if c.parallel && (kind == "chat" || kind == "route") {
		index := 0
		if kind == "route" {
			index = 1
		}
		close(c.started[index])
		select {
		case <-c.started[1-index]:
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}
	text := c.turn.chat
	switch kind {
	case "route":
		text = c.turn.route
	case "status":
		text = c.turn.status
	case "intent":
		m.rounds++
		if m.rounds <= len(c.turn.proposals) {
			proposal := c.turn.proposals[m.rounds-1]
			return schema.StreamReaderFromArray([]*schema.Message{{Role: schema.Assistant, ToolCalls: []schema.ToolCall{{ID: fmt.Sprintf("call-%d", m.rounds), Type: "function", Function: schema.FunctionCall{Name: proposal.name, Arguments: proposal.args}}}}}), nil
		}
		if len(c.turn.proposals) != 0 {
			found := false
			for _, message := range messages {
				if message.Role == schema.Tool && (strings.Contains(message.Content, c.fixture.device.nonce) || strings.Contains(message.Content, "invalid_arguments")) {
					found = true
				}
			}
			if !found {
				return nil, errors.New("intent reply lacks a real current tool result")
			}
		}
		text = c.turn.intent
	}
	return schema.StreamReaderFromArray([]*schema.Message{schema.AssistantMessage(text, nil)}), nil
}

type functionDeviceCall struct {
	alias string
	args  json.RawMessage
}
type functionDevice struct {
	mu    sync.Mutex
	nonce string
	calls []functionDeviceCall
}

func (*functionDevice) Inspect(_ context.Context, owner string, _ apitypes.RuntimeProfile, _ toolcatalog.Tool) (toolcatalog.Availability, error) {
	if owner != "function-peer" {
		return toolcatalog.Availability{}, errors.New("wrong device owner")
	}
	return toolcatalog.Availability{Supported: true, Online: true}, nil
}
func (d *functionDevice) Invoke(ctx context.Context, owner string, _ apitypes.RuntimeProfile, tool toolcatalog.Tool, args json.RawMessage) (json.RawMessage, error) {
	if err := tool.Authorize(ctx); err != nil {
		return nil, err
	}
	if owner != "function-peer" {
		return nil, errors.New("cross-Peer invocation")
	}
	if tool.Alias == "screen.brightness" && (tool.Target["id"] != "display.main" || tool.Target["operation"] != "write") {
		return nil, errors.New("wrong fixed MHS target")
	}
	d.mu.Lock()
	defer d.mu.Unlock()
	d.calls = append(d.calls, functionDeviceCall{tool.Alias, append(json.RawMessage(nil), args...)})
	result := map[string]any{"receipt": d.nonce}
	switch tool.Alias {
	case "music.playlist":
		result["items"] = []any{map[string]any{"title": "小星星", "index": 0}, map[string]any{"title": "卡农", "index": 1}}
		result["playlist_revision"] = d.nonce
	case "music.play", "music.status":
		result["state"] = "playing"
		result["current_index"] = 1
	case "screen.get":
		result["brightness_percent"] = 50
	case "screen.brightness":
		result["brightness_percent"] = 30
	}
	return json.Marshal(result)
}
func (d *functionDevice) count(alias string) int {
	d.mu.Lock()
	defer d.mu.Unlock()
	n := 0
	for _, call := range d.calls {
		if call.alias == alias {
			n++
		}
	}
	return n
}

type functionState struct {
	mu      sync.Mutex
	version int
	fields  map[string]any
}

func (s *functionState) Load(context.Context, string) (eino.StateSnapshot, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	copy := map[string]any{}
	for key, value := range s.fields {
		copy[key] = value
	}
	return eino.StateSnapshot{Version: strconv.Itoa(s.version), Fields: copy}, nil
}
func (s *functionState) CompareAndSwap(_ context.Context, _ string, version string, fields map[string]any) (eino.StateSnapshot, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if version != strconv.Itoa(s.version) {
		return eino.StateSnapshot{}, errors.New("fixture state conflict")
	}
	s.version++
	s.fields = map[string]any{}
	copy := map[string]any{}
	for key, value := range fields {
		s.fields[key] = value
		copy[key] = value
	}
	return eino.StateSnapshot{Version: strconv.Itoa(s.version), Fields: copy}, nil
}

type functionHistory struct {
	mu      sync.Mutex
	scope   string
	entries []memory.HistoryEntry
}

func (h *functionHistory) Query(_ context.Context, query memory.HistoryQuery) (memory.HistoryPage, error) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if query.ConversationID != h.scope {
		return memory.HistoryPage{}, errors.New("wrong shared History scope")
	}
	entries := []memory.HistoryEntry{}
	for _, entry := range h.entries {
		if query.ExcludeTurnID == "" || entry.TurnID != query.ExcludeTurnID {
			entries = append(entries, entry)
		}
	}
	if query.Descending {
		slices.Reverse(entries)
	}
	if query.Limit > 0 && len(entries) > query.Limit {
		entries = entries[:query.Limit]
	}
	return memory.HistoryPage{Entries: entries}, nil
}
func (h *functionHistory) hasEntries() bool {
	h.mu.Lock()
	defer h.mu.Unlock()
	return len(h.entries) > 0
}
func (h *functionHistory) appendTurn(user, reply string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	turn := fmt.Sprintf("turn-%d", len(h.entries)/2)
	for index, text := range []string{user, reply} {
		role := memory.RoleUser
		if index == 1 {
			role = memory.RoleAssistant
		}
		h.entries = append(h.entries, memory.HistoryEntry{ConversationID: h.scope, ID: strconv.Itoa(len(h.entries) + 1), TurnID: turn, Role: role, Text: text, CreatedAt: time.Unix(0, int64(len(h.entries)+1))})
	}
}

type functionMemory struct {
	mu       sync.Mutex
	nonce    string
	recalls  int
	observed chan memory.Observation
}

func (*functionMemory) SupportsDirectFactObservation() bool { return true }
func (m *functionMemory) Recall(context.Context, memory.Query) (memory.RecallResult, error) {
	m.mu.Lock()
	m.recalls++
	m.mu.Unlock()
	return memory.RecallResult{Matches: []memory.Match{{Fact: memory.Fact{ID: "shared-preference", Text: m.nonce + "：用户喜欢轻音乐"}, Score: 1}}}, nil
}
func (m *functionMemory) Observe(_ context.Context, observation memory.Observation) (memory.ObserveResult, error) {
	m.observed <- observation
	return memory.ObserveResult{}, nil
}
func (*functionMemory) Update(context.Context, memory.UpdateRequest) (memory.Fact, error) {
	return memory.Fact{}, errors.New("unexpected update")
}
func (*functionMemory) Delete(context.Context, memory.DeleteRequest) error {
	return errors.New("unexpected delete")
}

type functionFixture struct {
	graph                     eino.GraphDefinition
	profile                   apitypes.RuntimeProfile
	state                     *functionState
	history                   *functionHistory
	memory                    *functionMemory
	device                    *functionDevice
	memoryNonce, historyNonce string
}

func newFunctionFixture(t *testing.T) *functionFixture {
	t.Helper()
	var public struct {
		Spec struct {
			Eino apitypes.EinoWorkflowSpec `json:"eino"`
		} `json:"spec"`
	}
	decode(t, document(t, "workflows/chat-assistant/eino.function-chat.yaml"), &public)
	if public.Spec.Eino.StatePersistence == nil || !slices.Equal(public.Spec.Eino.StatePersistence.Fields, []string{"intent-active", "pending-context", "intent-cancelled"}) {
		t.Fatal("pending intent must persist across reload")
	}
	graph, err := einoconfig.MapGraph(public.Spec.Eino.Graph)
	if err != nil {
		t.Fatal(err)
	}
	bytes := make([]byte, 8)
	_, _ = rand.Read(bytes)
	nonce := hex.EncodeToString(bytes)
	return &functionFixture{graph: graph, profile: chatProfile(t, "runtime-profiles/testing.yaml"), state: &functionState{fields: map[string]any{"intent-active": false, "pending-context": "", "intent-cancelled": false}}, history: &functionHistory{scope: "history-" + nonce}, memory: &functionMemory{nonce: "memory-" + nonce, observed: make(chan memory.Observation, 32)}, device: &functionDevice{nonce: "receipt-" + nonce}, memoryNonce: "memory-" + nonce, historyNonce: "history-token-" + nonce}
}
func (f *functionFixture) run(t *testing.T, turn functionTurn) {
	t.Helper()
	ctx, cancel := context.WithTimeout(t.Context(), 5*time.Second)
	defer cancel()
	before, err := f.state.Load(ctx, "fixture")
	if err != nil {
		t.Fatal(err)
	}
	wasPending, _ := before.Fields["intent-active"].(bool)
	components := &functionComponents{fixture: f, turn: turn, parallel: !wasPending, started: [2]chan struct{}{make(chan struct{}), make(chan struct{})}}
	invoker := &agenthost.ToolkitInvoker{Catalog: &toolcatalog.Catalog{Devices: f.device}, Owner: func(context.Context) (string, error) { return "function-peer", nil }, Scope: func(context.Context, string) (apitypes.RuntimeProfile, []string, error) {
		names, err := toolcatalog.Selection(f.profile, "function-assistant", "eino-function-chat", nil)
		return f.profile, names, err
	}}
	// Rebuild every turn: State, History and Memory must come from the same
	// external scopes, not an in-process transformer's previous scratch fields.
	transformer, err := eino.New(ctx, eino.Config{Agent: eino.AgentConfig{ID: "function-chat-fixture"}, Graph: f.graph, Components: components, ToolInvoker: invoker, State: &eino.StatePersistenceConfig{Store: f.state, Scope: "fixture", Fields: []string{"intent-active", "pending-context", "intent-cancelled"}}, History: &eino.HistoryConfig{Store: f.history, Scope: f.history.scope, Limit: 100}, Memory: &eino.MemoryConfig{Store: f.memory, Scope: memory.Scope{AppID: "function-chat-fixture"}}})
	if err != nil {
		t.Fatal(err)
	}
	builder := genx.NewGrowableStreamBuilder((&genx.ModelContextBuilder{}).Build(), 8)
	if err := builder.Add(genx.NewBeginOfStream(genx.NewStreamID()), &genx.MessageChunk{Role: genx.RoleUser, Part: genx.Text(turn.input)}, genx.NewTextEndOfStream()); err != nil {
		t.Fatal(err)
	}
	if err := builder.Done(genx.Usage{}); err != nil {
		t.Fatal(err)
	}
	stream, err := transformer.Transform(ctx, builder.Stream())
	if err != nil {
		t.Fatal(err)
	}
	defer stream.Close()
	var text strings.Builder
	for {
		chunk, err := stream.Next()
		if errors.Is(err, io.EOF) || errors.Is(err, genx.ErrDone) {
			break
		}
		if err != nil {
			t.Fatal(err)
		}
		if err := genx.StreamError(chunk.Ctrl); err != nil {
			t.Fatal(err)
		}
		if part, ok := chunk.Part.(genx.Text); ok && !chunk.IsEndOfStream() {
			text.WriteString(string(part))
		}
	}
	if text.String() != turn.want {
		t.Fatalf("reply %q, want %q", text.String(), turn.want)
	}
	components.mu.Lock()
	counts := components.counts
	components.mu.Unlock()
	if (counts.chat > 0) != turn.wantChat || (counts.intent > 0) != turn.wantIntent {
		t.Fatalf("agent calls=%+v, want chat=%v intent=%v", counts, turn.wantChat, turn.wantIntent)
	}
	if counts.route != 1 || (counts.status > 0) != turn.wantIntent {
		t.Fatalf("route/status calls=%+v", counts)
	}
	after, err := f.state.Load(ctx, "fixture")
	if err != nil {
		t.Fatal(err)
	}
	if after.Fields["intent-active"] != turn.pending {
		t.Fatalf("intent-active=%v, want %v", after.Fields["intent-active"], turn.pending)
	}
	if after.Fields["intent-cancelled"] != turn.cancelled {
		t.Fatalf("intent-cancelled=%v, want %v", after.Fields["intent-cancelled"], turn.cancelled)
	}
	if turn.pending && after.Fields["pending-context"] == "" {
		t.Fatal("pending task lost its context")
	}
	if !turn.pending && after.Fields["pending-context"] != "" {
		t.Fatal("completed or cancelled task retained pending context")
	}
	if wasPending && turn.route == "CHAT" && after.Fields["pending-context"] != before.Fields["pending-context"] {
		t.Fatal("a pure-chat detour changed the pending intent")
	}
	select {
	case observed := <-f.memory.observed:
		if len(observed.Facts) != 2 || observed.Facts[0].Text != turn.input || observed.Facts[1].Text != turn.want {
			t.Fatal("shared Memory must observe only current input and the selected agent reply")
		}
	case <-ctx.Done():
		t.Fatal("selected reply was not observed")
	}
	// Standalone Transform tests supply caller-owned History. Real Giztest
	// coverage separately checks the Server's actual durable History records.
	f.history.appendTurn(turn.input, turn.want)
}

func TestFunctionChatStickyIntentAndSharedContext(t *testing.T) {
	f := newFunctionFixture(t)
	turns := []functionTurn{
		{input: "记住我喜欢轻音乐，暗号是 " + f.historyNonce, route: "CHAT", chat: "已记住。", want: "已记住。", wantChat: true},
		{input: "我要唱歌。", route: "INTENT", status: "PENDING", chat: "DISCARDED_CHAT_DRAFT", intent: "你想自己唱，还是播放现有音乐？", want: "你想自己唱，还是播放现有音乐？", wantChat: true, wantIntent: true, pending: true},
		{input: "播放现有列表的音乐，先让我选，不要播放。", route: "INTENT", status: "PENDING", intent: "列表有小星星和卡农，你选哪一首？", want: "列表有小星星和卡农，你选哪一首？", proposals: []functionProposal{{"music_playlist", "{}"}}, wantIntent: true, pending: true},
		{input: "先聊纯知识：二加二等于几？", route: "CHAT", chat: "二加二等于四。", want: "二加二等于四。", wantChat: true, pending: true},
		{input: "第二首，开始播放。", route: "INTENT", status: "DONE", intent: "已播放卡农。", want: "已播放卡农。", proposals: []functionProposal{{"music_playlist", "{}"}, {"music_play", `{"index":1}`}, {"music_status", "{}"}}, wantIntent: true},
		{input: "再帮我选一首，先别播放。", route: "INTENT", status: "PENDING", chat: "DISCARDED_CHAT_DRAFT", intent: "你想听哪一首？", want: "你想听哪一首？", wantChat: true, wantIntent: true, pending: true},
		{input: "我不想取消，继续让我选。", route: "INTENT", status: "PENDING", intent: "好的，继续选歌，你想听哪一首？", want: "好的，继续选歌，你想听哪一首？", wantIntent: true, pending: true},
		{input: "取消，不选了。", route: "INTENT", status: "CANCELLED", intent: "已取消这次选歌。", want: "已取消这次选歌。", wantIntent: true, cancelled: true},
		{input: "第一首。", route: "INTENT", chat: "DISCARDED_CHAT_DRAFT", want: "刚才的选择已取消。你现在想做什么？", wantChat: true, cancelled: true},
		{input: "我们做加法，你问我二加二，让我答。", route: "CHAT", chat: "二加二等于几？", want: "二加二等于几？", wantChat: true, cancelled: true},
		{input: "4", route: "CHAT", chat: "答对了。", want: "答对了。", wantChat: true, cancelled: true},
		{input: "第一首。", route: "CHAT", chat: "DISCARDED_CHAT_DRAFT", want: "刚才的选择已取消。你现在想做什么？", wantChat: true, cancelled: true},
		{input: "屏幕亮度是多少？", route: "INTENT", status: "DONE", chat: "DISCARDED_CHAT_DRAFT", intent: "当前屏幕亮度为50%。", want: "当前屏幕亮度为50%。", proposals: []functionProposal{{"screen_get", "{}"}}, wantChat: true, wantIntent: true},
		{input: "把屏幕亮度改成30%。", route: "INTENT", status: "DONE", chat: "DISCARDED_CHAT_DRAFT", intent: "屏幕已设为30%。", want: "屏幕已设为30%。", proposals: []functionProposal{{"screen_brightness", `{"brightness_percent":30}`}}, wantChat: true, wantIntent: true},
	}
	for index, turn := range turns {
		t.Run(strconv.Itoa(index), func(t *testing.T) { f.run(t, turn) })
	}
	if f.device.count("music.play") != 1 {
		t.Fatal("selection, pure chat or cancellation caused an extra play")
	}
	f.memory.mu.Lock()
	recalls := f.memory.recalls
	f.memory.mu.Unlock()
	if recalls != len(turns) {
		t.Fatalf("shared recall calls=%d, want one per turn", recalls)
	}
}

func TestFunctionChatChatTextIsNotADeviceReceipt(t *testing.T) {
	f := newFunctionFixture(t)
	f.run(t, functionTurn{input: "history " + f.historyNonce, route: "CHAT", chat: "已记住。", want: "已记住。", wantChat: true})
	// A chat-model statement is text, not native execution. Preserve the selected
	// chat reply and evaluate tool execution using actual dispatch receipts.
	f.run(t, functionTurn{input: "把屏幕亮度设为30%。", route: "CHAT", chat: "已调整成功。", want: "已调整成功。", wantChat: true})
	if f.device.count("screen.brightness") != 0 || f.device.count("music.play") != 0 {
		t.Fatal("chat text was incorrectly treated as a tool execution")
	}
}

func TestFunctionChatIntentStateBoundaries(t *testing.T) {
	f := newFunctionFixture(t)
	f.run(t, functionTurn{input: "history " + f.historyNonce, route: "unrecognized", chat: "普通对话。", want: "普通对话。", wantChat: true})
	f.run(t, functionTurn{input: "调屏幕亮度。", route: "INTENT", status: "unrecognized", chat: "DISCARDED_CHAT_DRAFT", intent: "亮度要设为多少？", want: "亮度要设为多少？", wantChat: true, wantIntent: true, pending: true})
	f.run(t, functionTurn{input: "30%。", route: "unrecognized", status: "DONE", intent: "屏幕已设为30%。", want: "屏幕已设为30%。", proposals: []functionProposal{{"screen_brightness", `{"brightness_percent":30}`}}, wantIntent: true})
	f.run(t, functionTurn{input: "屏幕设为120%。", route: "INTENT", status: "PENDING", chat: "DISCARDED_CHAT_DRAFT", intent: "数值超出范围，请给0到100的合法值。", want: "数值超出范围，请给0到100的合法值。", proposals: []functionProposal{{"screen_brightness", `{"brightness_percent":120}`}}, wantChat: true, wantIntent: true, pending: true})
	f.run(t, functionTurn{input: "不调了，讲个笑话。", route: "CHAT_CANCEL", chat: "这次不调了。给你讲个笑话。", want: "这次不调了。给你讲个笑话。", wantChat: true, cancelled: true})
	if f.device.count("screen.brightness") != 1 {
		t.Fatal("invalid parameters or cancellation reached device writes")
	}
	f.run(t, functionTurn{input: "重新帮我选歌，先别播放。", route: "INTENT", status: "PENDING", chat: "DISCARDED_CHAT_DRAFT", intent: "你想选哪一首？", want: "你想选哪一首？", wantChat: true, wantIntent: true, pending: true})
	f.run(t, functionTurn{input: "取消选歌，改为把屏幕亮度设为30%。", route: "INTENT", status: "DONE", intent: "已取消选歌，屏幕已设为30%。", want: "已取消选歌，屏幕已设为30%。", proposals: []functionProposal{{"screen_brightness", `{"brightness_percent":30}`}}, wantIntent: true})
	if f.device.count("screen.brightness") != 2 {
		t.Fatal("an explicit new request did not complete after cancelling the old task")
	}
}
