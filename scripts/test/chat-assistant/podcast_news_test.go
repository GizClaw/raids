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

type newsModel struct {
	generation int
	query      string
	blocked    chan struct{}
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
	if len(options.Tools) != 1 || options.Tools[0].Name != "web_search" {
		return nil, errors.New("news Model did not receive the selected search Tool")
	}
	if strings.Contains(input[0].Content, "当前状态：暂停") {
		return schema.StreamReaderFromArray([]*schema.Message{schema.AssistantMessage("好，先停在这里。", nil)}), nil
	}
	if strings.Contains(input[0].Content, "当前状态：选择领域") {
		return schema.StreamReaderFromArray([]*schema.Message{schema.AssistantMessage("你想听科技、国内、国际、财经还是体育新闻？", nil)}), nil
	}
	last := input[len(input)-1]
	if last.Role == schema.Tool {
		var result struct{ Fact string }
		if err := json.Unmarshal([]byte(last.Content), &result); err != nil || result.Fact == "" {
			return nil, errors.New("news generation did not receive the current HTTP search result")
		}
		return schema.StreamReaderFromArray([]*schema.Message{schema.AssistantMessage(result.Fact, nil)}), nil
	}
	m.generation++
	if m.generation == 4 {
		close(m.blocked)
		<-ctx.Done()
		return nil, context.Cause(ctx)
	}
	args, _ := json.Marshal(map[string]any{"query": m.query, "search_type": "web", "count": 3, "time_range": "OneDay"})
	return schema.StreamReaderFromArray([]*schema.Message{{Role: schema.Assistant,
		ToolCalls: []schema.ToolCall{{ID: fmt.Sprintf("news-%d", m.generation), Type: "function", Function: schema.FunctionCall{Name: "web_search", Arguments: string(args)}}}}}), nil
}

func TestNewsPodcastSearchesEveryGenerationAndStops(t *testing.T) {
	ctx, cancel := context.WithTimeout(t.Context(), 5*time.Second)
	defer cancel()
	doc := document(t, "workflows/podcast-news/eino.yaml")
	var public apitypes.EinoWorkflowSpec
	decode(t, doc["spec"].(map[string]any)["eino"], &public)
	graph, err := einoconfig.MapGraph(public.Graph)
	if err != nil {
		t.Fatal(err)
	}
	nonce := make([]byte, 16)
	if _, err := rand.Read(nonce); err != nil {
		t.Fatal(err)
	}
	f := &fixture{query: "科技今天新闻", fact: "检索事实" + hex.EncodeToString(nonce)}
	profile := chatProfile(t, "runtime-profiles/testing.yaml")
	m := &newsModel{query: f.query, blocked: make(chan struct{})}
	transformer, err := genxeino.New(ctx, genxeino.Config{
		Agent: genxeino.AgentConfig{ID: "news-contract"}, Graph: graph,
		ContinueFrom: *public.Conversation.ContinueFrom, Components: newsComponents{model: m},
		ToolInvoker: workflowSearchToolkit(t, f, &profile, "podcast-news", nil),
	})
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
	push("科技新闻")
	var delivered strings.Builder
	completed := 0
	for completed < 3 {
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
		t.Fatal("next news generation did not begin")
	}
	push("停一下")
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
	if f.requests != 3 || f.body["TimeRange"] != "OneDay" || strings.Count(delivered.String(), f.fact) != 3 || !strings.HasSuffix(delivered.String(), "好，先停在这里。") {
		t.Fatalf("searches=%d request=%v output=%q", f.requests, f.body, delivered.String())
	}
}
