package chatassistant

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
	genxeino "github.com/GizClaw/gizclaw-go/pkgs/genx/transformers/eino"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/services/ai/workflow/einoconfig"
	"github.com/cloudwego/eino/components/model"
	"github.com/cloudwego/eino/components/retriever"
	"github.com/cloudwego/eino/schema"
)

type newsComponents struct{ model model.BaseChatModel }

func (c newsComponents) ResolveChatModel(_ context.Context, alias string) (model.BaseChatModel, error) {
	if alias != "eino-podcast-news.model" {
		return nil, fmt.Errorf("unexpected news Model alias %q", alias)
	}
	return c.model, nil
}
func (newsComponents) ResolveRetriever(context.Context, string) (retriever.Retriever, error) {
	return nil, errors.New("unexpected news retriever")
}

type newsMaterial struct{ Text, Source, Date, URL string }
type newsItem struct {
	Key, Title, Source, Date, URL, Brief string
	Details, Comments                    []newsMaterial
}
type newsHit struct{ ID, Title, SiteName, PublishTime, URL, Snippet, Content string }

// These values originate only in the HTTP response, never in the model's first
// request. The model simulates provider formatting, while queueing, branching,
// deduplication and HTTP argument mapping execute the unmodified shipped Graph.
type newsModel struct {
	query        string
	blockScanAt  int64
	interruption string
	scans        atomic.Int64
	questions    atomic.Int64
	blocked      chan struct{}
	once         sync.Once
}

func (m *newsModel) Generate(ctx context.Context, input []*schema.Message, opts ...model.Option) (*schema.Message, error) {
	stream, err := m.Stream(ctx, input, opts...)
	if err != nil {
		return nil, err
	}
	defer stream.Close()
	return stream.Recv()
}
func (m *newsModel) Stream(ctx context.Context, input []*schema.Message, opts ...model.Option) (*schema.StreamReader[*schema.Message], error) {
	options := model.GetCommonOptions(nil, opts...)
	if len(options.Tools) != 1 || options.Tools[0].Name != "news_search" {
		return nil, errors.New("news Model did not receive only its batch search Tool")
	}
	reply := func(text string) (*schema.StreamReader[*schema.Message], error) {
		return schema.StreamReaderFromArray([]*schema.Message{schema.AssistantMessage(text, nil)}), nil
	}
	system := input[0].Content
	last := input[len(input)-1]
	scan, enrich := strings.Contains(system, "任务是“批量扫描”"), strings.Contains(system, "任务是“批量补充”")
	if scan || enrich {
		if last.Role == schema.Tool {
			var result struct{ WebResults []newsHit }
			if err := json.Unmarshal([]byte(last.Content), &result); err != nil {
				return nil, err
			}
			if scan {
				var items []newsItem
				for _, hit := range result.WebResults {
					item := newsItem{Key: hit.ID, Title: hit.Title, Source: hit.SiteName, Date: hit.PublishTime[:10], URL: hit.URL, Brief: hit.Snippet, Details: []newsMaterial{}, Comments: []newsMaterial{}}
					if hit.Content != "" {
						parts := strings.SplitN(hit.Content, "\n评论：", 2)
						item.Details = append(item.Details, newsMaterial{Text: parts[0], Source: hit.SiteName, Date: item.Date, URL: hit.URL})
						if len(parts) == 2 {
							item.Comments = append(item.Comments, newsMaterial{Text: parts[1], Source: hit.SiteName, Date: item.Date, URL: hit.URL})
						}
					}
					items = append(items, item)
				}
				var records strings.Builder
				for _, item := range items {
					fmt.Fprintf(&records, "EVENT\nkey:%s\ntitle:%s\nsource:%s\ndate:%s\nurl:%s\nbrief:%s\n", item.Key, item.Title, item.Source, item.Date, item.URL, item.Brief)
					for _, v := range item.Details {
						fmt.Fprintf(&records, "FACT|%s|%s|%s|%s\n", v.Source, v.Date, v.URL, v.Text)
					}
					for _, v := range item.Comments {
						fmt.Fprintf(&records, "COMMENT|%s|%s|%s|%s\n", v.Source, v.Date, v.URL, v.Text)
					}
					records.WriteString("END\n")
				}
				return reply(records.String())
			}
			var records strings.Builder
			for _, hit := range result.WebResults {
				kind := "FACT"
				if hit.SiteName == "评论机构" {
					kind = "COMMENT"
				}
				fmt.Fprintf(&records, "EVENT\nkey:%s\n%s|%s|%s|%s|%s\nEND\n", hit.ID, kind, hit.SiteName, hit.PublishTime[:10], hit.URL, hit.Content)
			}
			return reply(records.String())
		}
		number := m.scans.Load()
		if scan {
			number = m.scans.Add(1)
			if number == m.blockScanAt {
				m.once.Do(func() { close(m.blocked) })
				<-ctx.Done()
				return nil, context.Cause(ctx)
			}
		}
		timeRange := "OneDay"
		if enrich {
			timeRange = "OneWeek"
		}
		args, _ := json.Marshal(map[string]any{"query": m.query, "search_type": "web", "count": 10, "time_range": timeRange})
		return schema.StreamReaderFromArray([]*schema.Message{{Role: schema.Assistant, ToolCalls: []schema.ToolCall{{ID: fmt.Sprintf("batch-%s-%d", timeRange, number), Type: "function", Function: schema.FunctionCall{Name: "news_search", Arguments: string(args)}}}}}), nil
	}
	for mode, text := range map[string]string{"暂停": "好，先停在这里。", "选择领域": "你想听科技、国内、国际、财经还是体育新闻？", "暂无新增": "没有可靠的新消息。", "暂无细节": "没有更多可核实的细节。", "批次结束": "接着看看还有哪些新消息。"} {
		if strings.Contains(system, "当前状态："+mode+"。") {
			if mode == "暂停" && (!strings.Contains(last.Content, "停止播讲") || !strings.Contains(last.Content, text)) {
				return nil, errors.New("pause reached the model as an empty news-material request")
			}
			return reply(text)
		}
	}
	if strings.Contains(system, "当前状态：回答提问。") {
		if !strings.Contains(last.Content, "问题："+m.interruption) {
			return nil, errors.New("listener question missing from the answering request")
		}
		_, material, ok := strings.Cut(last.Content, "已有来源材料：")
		var items []newsItem
		if !ok || json.Unmarshal([]byte(material), &items) != nil || len(items) == 0 {
			return nil, errors.New("answer lost the cached source material")
		}
		m.questions.Add(1)
		return reply("答复。" + items[0].Source + items[0].Date + "报道，" + items[0].Brief + "。")
	}
	material := strings.TrimPrefix(last.Content, "播报以下新闻事实：")
	if strings.Contains(system, "当前状态：今日总览。") {
		var items []newsItem
		if err := json.Unmarshal([]byte(material), &items); err != nil {
			return nil, err
		}
		text := "今日总览。"
		for _, item := range items {
			text += item.Source + item.Date + "报道，" + item.Brief + "。"
		}
		return reply(text)
	}
	var item newsItem
	if err := json.Unmarshal([]byte(material), &item); err != nil {
		return nil, err
	}
	text := "深入。"
	for _, fact := range item.Details {
		text += fact.Source + fact.Date + "报道，" + fact.Text + "。"
	}
	for _, comment := range item.Comments {
		text += comment.Source + comment.Date + "的评论认为，" + comment.Text + "。"
	}
	return reply(text)
}
func wireNewsItem(item newsItem) map[string]any {
	materials := func(values []newsMaterial) []any {
		out := []any{}
		for _, v := range values {
			out = append(out, map[string]any{"text": v.Text, "source": v.Source, "date": v.Date, "url": v.URL})
		}
		return out
	}
	return map[string]any{"key": item.Key, "title": item.Title, "source": item.Source, "date": item.Date, "url": item.URL, "brief": item.Brief, "details": materials(item.Details), "comments": materials(item.Comments)}
}

type newsState struct {
	mu       sync.Mutex
	fields   map[string]any
	revision int
}

func (s *newsState) Load(context.Context, string) (genxeino.StateSnapshot, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return genxeino.StateSnapshot{Version: fmt.Sprint(s.revision), Fields: s.fields}, nil
}
func (s *newsState) CompareAndSwap(_ context.Context, _ string, version string, fields map[string]any) (genxeino.StateSnapshot, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if version != fmt.Sprint(s.revision) {
		return genxeino.StateSnapshot{}, errors.New("state conflict")
	}
	s.revision++
	s.fields = fields
	return genxeino.StateSnapshot{Version: fmt.Sprint(s.revision), Fields: s.fields}, nil
}

func newsNonce(t *testing.T) string {
	t.Helper()
	nonce := make([]byte, 16)
	if _, err := rand.Read(nonce); err != nil {
		t.Fatal(err)
	}
	return hex.EncodeToString(nonce)
}
func newsDate() string { return time.Now().In(time.FixedZone("Beijing", 8*3600)).Format("2006-01-02") }
func hit(key, nonce string, details bool) newsHit {
	h := newsHit{ID: key, Title: "新闻" + key, SiteName: "新闻机构", PublishTime: newsDate() + "T12:00:00+08:00", URL: "https://news.example/article?id=" + key, Snippet: "概要" + nonce + key}
	if details {
		h.Content = "新增事实" + nonce + key + "\n评论：媒体评论" + nonce + key
	}
	return h
}

func runNewsUntilInterrupt(t *testing.T, f *fixture, m *newsModel, initial map[string]any, sections int, text string) string {
	t.Helper()
	ctx, cancel := context.WithTimeout(t.Context(), 10*time.Second)
	defer cancel()
	doc := document(t, "workflows/podcast-news/eino.yaml")
	var public apitypes.EinoWorkflowSpec
	decode(t, doc["spec"].(map[string]any)["eino"], &public)
	graph, err := einoconfig.MapGraph(public.Graph)
	if err != nil {
		t.Fatal(err)
	}
	if initial == nil {
		initial = map[string]any{}
	}
	state := &newsState{fields: map[string]any{"bulletin": initial}}
	profile := chatProfile(t, "runtime-profiles/testing.yaml")
	transformer, err := genxeino.New(ctx, genxeino.Config{Agent: genxeino.AgentConfig{ID: "news-contract"}, Graph: graph, ContinueFrom: *public.Conversation.ContinueFrom,
		State:      &genxeino.StatePersistenceConfig{Store: state, Scope: "news-contract", Fields: public.StatePersistence.Fields},
		Components: newsComponents{model: m}, ToolInvoker: workflowSearchToolkit(t, f, &profile, "podcast-news", nil)})
	if err != nil {
		t.Fatal(err)
	}
	defer transformer.Close()
	b := genx.NewGrowableStreamBuilder((&genx.ModelContextBuilder{}).Build(), 8)
	push := func(text string) {
		t.Helper()
		if err := b.Add(genx.NewBeginOfStream(genx.NewStreamID()), &genx.MessageChunk{Role: genx.RoleUser, Part: genx.Text(text)}, genx.NewTextEndOfStream()); err != nil {
			t.Fatal(err)
		}
	}
	output, err := transformer.Transform(ctx, b.Stream())
	if err != nil {
		t.Fatal(err)
	}
	defer output.Close()
	push(text)
	var delivered strings.Builder
	completed := 0
	for completed < sections {
		chunk, err := output.Next()
		if err != nil {
			t.Fatal(err)
		}
		if chunk.Ctrl != nil && chunk.Ctrl.MessageEnd {
			completed++
		}
		if text, ok := chunk.Part.(genx.Text); ok {
			delivered.WriteString(string(text))
		}
	}
	select {
	case <-m.blocked:
	case <-ctx.Done():
		t.Fatal("next batch did not begin after consumption")
	}
	interruption := m.interruption
	if interruption == "" {
		interruption = "停一下"
	}
	push(interruption)
	if err := b.Done(genx.Usage{}); err != nil {
		t.Fatal(err)
	}
	for {
		chunk, err := output.Next()
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			t.Fatal(err)
		}
		if text, ok := chunk.Part.(genx.Text); ok {
			delivered.WriteString(string(text))
		}
	}
	if interruption == "停一下" && !strings.HasSuffix(delivered.String(), "好，先停在这里。") {
		t.Fatalf("interruption output=%q", delivered.String())
	}
	if strings.Contains(delivered.String(), "EVENT\n") || strings.Contains(delivered.String(), "FACT|") || strings.Contains(delivered.String(), "COMMENT|") {
		t.Fatal("internal collection records leaked into narration")
	}
	return delivered.String()
}

func TestNewsPodcastQuestionInterruptsAndKeepsCachedSourcesWithoutSearch(t *testing.T) {
	nonce := newsNonce(t)
	date := newsDate()
	h := hit("a", nonce, true)
	item := wireNewsItem(newsItem{Key: h.ID, Title: h.Title, Source: h.SiteName, Date: date, URL: h.URL, Brief: h.Snippet, Details: []newsMaterial{{Text: h.Content, Source: h.SiteName, Date: date, URL: h.URL}}, Comments: []newsMaterial{}})
	initial := map[string]any{"topic": "科技新闻", "today": date, "day": (time.Now().UnixMilli() + 28800000) / 86400000, "items": []any{item}, "cursor": 0, "overview": true, "enriched": true, "seen": []any{}}
	f := &fixture{query: "should-not-search", count: 10}
	m := &newsModel{query: f.query, blockScanAt: 1, blocked: make(chan struct{}), interruption: "停一下，刚才那条消息的来源是哪家媒体？请先回答我。"}
	output := runNewsUntilInterrupt(t, f, m, initial, 2, "继续")
	want := "答复。新闻机构" + newsDate() + "报道，概要" + nonce + "a。"
	if f.requests != 0 || m.questions.Load() != 1 || strings.Count(output, "今日总览。") != 1 || !strings.HasSuffix(output, want) {
		t.Fatalf("searches=%d answers=%d output=%q", f.requests, m.questions.Load(), output)
	}
}

func TestNewsPodcastOneSearchFeedsOverviewAndThreeDeepDives(t *testing.T) {
	nonce := newsNonce(t)
	f := &fixture{query: "科技今日新闻", count: 10, searchResult: func(_ int, body map[string]any) any {
		if body["TimeRange"] != "OneDay" {
			t.Errorf("unexpected range %v", body)
		}
		duplicate := hit("a", nonce, true)
		duplicate.URL = "https://other.example/reprint"
		return map[string]any{"WebResults": []newsHit{hit("a", nonce, true), duplicate, hit("b", nonce, true), hit("c", nonce, true)}}
	}}
	m := &newsModel{query: f.query, blockScanAt: 2, blocked: make(chan struct{})}
	output := runNewsUntilInterrupt(t, f, m, nil, 4, "科技新闻")
	if f.requests != 1 || strings.Count(output, "今日总览。") != 1 || strings.Count(output, "深入。") != 3 {
		t.Fatalf("searches=%d output=%q", f.requests, output)
	}
	for _, key := range []string{"a", "b", "c"} {
		if strings.Count(output, "概要"+nonce+key) != 1 || strings.Count(output, "新增事实"+nonce+key) != 1 {
			t.Fatalf("repeated or missing event %s: %s", key, output)
		}
	}
}
func TestNewsPodcastRefillsAfterBatchAndRejectsPreviouslyCoveredEvents(t *testing.T) {
	nonce := newsNonce(t)
	f := &fixture{query: "今日新闻", count: 10, searchResult: func(round int, _ map[string]any) any {
		if round == 1 {
			return map[string]any{"WebResults": []newsHit{hit("a", nonce, true), hit("b", nonce, true)}}
		}
		repeated := hit("a", nonce, true)
		repeated.Title = "另一家媒体的新标题"
		repeated.URL = "https://other.example/reprint"
		repeatedURL := hit("rename", nonce, true)
		repeatedURL.URL = hit("b", nonce, true).URL + "&utm_source=feed"
		return map[string]any{"WebResults": []newsHit{repeated, repeatedURL, hit("c", nonce, true)}}
	}}
	m := &newsModel{query: f.query, blockScanAt: 3, blocked: make(chan struct{})}
	output := runNewsUntilInterrupt(t, f, m, nil, 5, "科技新闻")
	if f.requests != 2 || strings.Count(output, "今日总览。") != 2 || strings.Count(output, "深入。") != 3 {
		t.Fatalf("searches=%d output=%s", f.requests, output)
	}
	for _, key := range []string{"a", "b", "c"} {
		if strings.Count(output, "概要"+nonce+key) != 1 || strings.Count(output, "新增事实"+nonce+key) != 1 {
			t.Fatalf("repeated event %s: %s", key, output)
		}
	}
	if strings.Contains(output, "概要"+nonce+"rename") {
		t.Fatal("tracked URL bypassed the consumed-event ledger")
	}
}
func TestNewsPodcastSupplementsWholeBatchOnceAndAttributesComments(t *testing.T) {
	nonce := newsNonce(t)
	f := &fixture{query: "科技新闻", count: 10, searchResult: func(round int, body map[string]any) any {
		if round == 1 {
			return map[string]any{"WebResults": []newsHit{hit("a", nonce, false), hit("b", nonce, false)}}
		}
		if body["TimeRange"] != "OneWeek" {
			t.Errorf("enrichment request=%v", body)
		}
		comment := hit("a", nonce, true)
		comment.SiteName = "评论机构"
		comment.Content = "媒体观点" + nonce
		fact := hit("b", nonce, true)
		fact.Content = "新增事实" + nonce + "b"
		return map[string]any{"WebResults": []newsHit{comment, fact}}
	}}
	m := &newsModel{query: f.query, blockScanAt: 2, blocked: make(chan struct{})}
	output := runNewsUntilInterrupt(t, f, m, nil, 3, "科技新闻")
	if f.requests != 2 || strings.Count(output, "今日总览。") != 1 || strings.Count(output, "的评论认为，媒体观点"+nonce) != 1 || strings.Count(output, "新增事实"+nonce+"b") != 1 {
		t.Fatalf("searches=%d output=%s", f.requests, output)
	}
}
func TestNewsPodcastRestoresRemainingQueueWithoutSearchOrOverview(t *testing.T) {
	nonce := newsNonce(t)
	date := newsDate()
	day := (time.Now().UnixMilli() + 28800000) / 86400000
	items := []any{}
	for _, key := range []string{"a", "b"} {
		h := hit(key, nonce, true)
		items = append(items, wireNewsItem(newsItem{Key: h.ID, Title: h.Title, Source: h.SiteName, Date: date, URL: h.URL, Brief: h.Snippet, Details: []newsMaterial{{Text: h.Content, Source: h.SiteName, Date: date, URL: h.URL}}, Comments: []newsMaterial{}}))
	}
	initial := map[string]any{"topic": "科技新闻", "today": date, "day": day, "items": items, "cursor": 1, "overview": false, "enriched": true, "seen": []any{}}
	f := &fixture{query: "should-not-search", count: 10}
	m := &newsModel{query: f.query, blockScanAt: 1, blocked: make(chan struct{})}
	output := runNewsUntilInterrupt(t, f, m, initial, 1, "继续")
	if f.requests != 0 || strings.Contains(output, "今日总览") || strings.Contains(output, nonce+"a") || strings.Count(output, "新增事实"+nonce+"b") != 1 {
		t.Fatalf("searches=%d resumed output=%s", f.requests, output)
	}
}
