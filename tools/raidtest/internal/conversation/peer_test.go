package conversation

import (
	"context"
	"errors"
	"io"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/rpcapi"
)

type fakeModeStream struct {
	output    chan fakeModeResult
	onPush    func(*genx.MessageChunk)
	firstRead chan struct{}
	firstOnce sync.Once
	closeOnce sync.Once
	blockNext <-chan struct{}
	closed    int
}

type fakeModeResult struct {
	chunk *genx.MessageChunk
	err   error
}

func (s *fakeModeStream) Push(_ context.Context, chunk *genx.MessageChunk) error {
	if s.onPush != nil {
		s.onPush(chunk)
	}
	return nil
}

func (s *fakeModeStream) Next() (*genx.MessageChunk, error) {
	if s.blockNext != nil {
		<-s.blockNext
		return nil, io.EOF
	}
	result, ok := <-s.output
	if !ok {
		return nil, io.EOF
	}
	s.firstOnce.Do(func() { close(s.firstRead) })
	return result.chunk, result.err
}

func (s *fakeModeStream) Close() error {
	s.closed++
	s.closeOnce.Do(func() { close(s.output) })
	return nil
}

func newFakeModeStream() *fakeModeStream {
	return &fakeModeStream{output: make(chan fakeModeResult, 8), firstRead: make(chan struct{})}
}

func TestCacheAudioInputReusesAndIsolatesFixture(t *testing.T) {
	calls := 0
	cached := CacheAudioInput(func(_ context.Context, text string) (AudioInput, error) {
		calls++
		return AudioInput{MIMEType: "audio/opus", Frames: [][]byte{{byte(len(text))}}}, nil
	})
	first, err := cached(context.Background(), "same")
	if err != nil {
		t.Fatal(err)
	}
	first.Frames[0][0] = 0
	second, err := cached(context.Background(), "same")
	if err != nil || calls != 1 || second.Frames[0][0] != 4 {
		t.Fatalf("second=%#v calls=%d err=%v", second, calls, err)
	}
	if _, err := cached(context.Background(), "other"); err != nil || calls != 2 {
		t.Fatalf("calls=%d err=%v", calls, err)
	}
}

func TestCacheAudioInputRetriesFailedSynthesis(t *testing.T) {
	calls := 0
	cached := CacheAudioInput(func(_ context.Context, _ string) (AudioInput, error) {
		calls++
		if calls == 1 {
			return AudioInput{}, errors.New("temporary")
		}
		return AudioInput{MIMEType: "audio/opus", Frames: [][]byte{{1}}}, nil
	})
	if _, err := cached(context.Background(), "same"); err == nil {
		t.Fatal("first synthesis unexpectedly passed")
	}
	if _, err := cached(context.Background(), "same"); err != nil || calls != 2 {
		t.Fatalf("calls=%d err=%v", calls, err)
	}
}

func TestPeerTargetRequestIDsAreUnique(t *testing.T) {
	target := &PeerTarget{}
	first := target.nextRequestID("reload-workspace")
	second := target.nextRequestID("reload-workspace")
	if first == second || !strings.HasPrefix(first, "raidtest-reload-workspace-") || !strings.HasPrefix(second, "raidtest-reload-workspace-") {
		t.Fatalf("request IDs first=%q second=%q", first, second)
	}
}

func TestRecallContainsAllFactsAcrossHits(t *testing.T) {
	hits := []rpcapi.PeerRunRecallHit{{Name: "correction", Snippet: "有效鞋印为３９码"}, {Name: "objective", Snippet: "正在寻找商队"}}
	if !recallContainsAll(hits, []string{"39码", "商队"}) {
		t.Fatal("expected recalled facts across hits")
	}
	if recallContainsAll(hits, []string{"39码", "青铜铃"}) {
		t.Fatal("accepted a missing persisted fact")
	}
	if recallContainsAll([]rpcapi.PeerRunRecallHit{{Snippet: "有效鞋印为39"}, {Snippet: "码数已复核"}}, []string{"39码"}) {
		t.Fatal("assembled one fact across unrelated recall hits")
	}
}

func TestWaitForRecallClosesConversationStreamBeforePolling(t *testing.T) {
	stream := newFakeModeStream()
	target := PeerTarget{
		stream:     stream,
		streamStop: make(chan struct{}),
		recallWorkspace: func(_ context.Context, _ string, request rpcapi.ServerRunWorkspaceRecallRequest) (*rpcapi.ServerRunWorkspaceRecallResponse, error) {
			if request.Query != "39码" {
				t.Fatalf("query=%q", request.Query)
			}
			return &rpcapi.ServerRunWorkspaceRecallResponse{Available: true, Hits: []rpcapi.PeerRunRecallHit{{Snippet: "更正后的鞋印是39码"}}}, nil
		},
	}
	if err := target.WaitForRecall(context.Background(), []string{"39码"}, time.Second); err != nil {
		t.Fatal(err)
	}
	if stream.closed != 1 {
		t.Fatalf("close count=%d", stream.closed)
	}
}

func TestWaitForRecallRetriesTransientRPCFailure(t *testing.T) {
	attempts := 0
	requestIDs := map[string]bool{}
	target := PeerTarget{recallWorkspace: func(_ context.Context, id string, _ rpcapi.ServerRunWorkspaceRecallRequest) (*rpcapi.ServerRunWorkspaceRecallResponse, error) {
		attempts++
		if requestIDs[id] {
			t.Fatalf("duplicate request ID %q", id)
		}
		requestIDs[id] = true
		if attempts == 1 {
			return nil, context.DeadlineExceeded
		}
		return &rpcapi.ServerRunWorkspaceRecallResponse{Available: true, Hits: []rpcapi.PeerRunRecallHit{{Snippet: "39码"}}}, nil
	}}
	if err := target.WaitForRecall(context.Background(), []string{"39码"}, 2*time.Second); err != nil {
		t.Fatal(err)
	}
	if attempts != 2 {
		t.Fatalf("attempts=%d", attempts)
	}
}

func TestPeerTargetReusesStreamUntilClosed(t *testing.T) {
	opens := 0
	stream := newFakeModeStream()
	target := PeerTarget{openStream: func(buffer int) (peerStream, error) {
		opens++
		if buffer != 128 {
			t.Fatalf("buffer=%d", buffer)
		}
		return stream, nil
	}}
	first, firstNext, err := target.ensureStream()
	if err != nil {
		t.Fatal(err)
	}
	second, secondNext, err := target.ensureStream()
	if err != nil || first != second || firstNext != secondNext || opens != 1 {
		t.Fatalf("first=%p second=%p opens=%d err=%v", first, second, opens, err)
	}
	if err := target.Close(); err != nil || stream.closed != 1 {
		t.Fatalf("closed=%d err=%v", stream.closed, err)
	}
	if _, _, err := target.ensureStream(); err != nil || opens != 2 {
		t.Fatalf("opens=%d err=%v", opens, err)
	}
	if err := target.Close(); err != nil || stream.closed != 2 {
		t.Fatalf("closed=%d err=%v", stream.closed, err)
	}
}

func TestPeerTargetSequentialTurnsShareOneReader(t *testing.T) {
	opens := 0
	stream := newFakeModeStream()
	stream.onPush = func(chunk *genx.MessageChunk) {
		if chunk.IsEndOfStream() {
			if chunk.Ctrl.StreamID == "turn-two" {
				stream.output <- fakeModeResult{chunk: &genx.MessageChunk{Ctrl: &genx.StreamCtrl{StreamID: "turn-one:ast:1", Error: "stale failure"}}}
				stream.output <- fakeModeResult{chunk: &genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text("stale"), Ctrl: &genx.StreamCtrl{StreamID: "turn-one:ast:1", Label: "assistant", EndOfStream: true}}}
			}
			emitTranslatedAudio(stream)
		}
	}
	target := PeerTarget{
		Timeout:      time.Second,
		RequireAudio: true,
		InputMode:    "push-to-talk",
		InputAudio: func(context.Context, string) (AudioInput, error) {
			return AudioInput{MIMEType: "audio/opus", Frames: [][]byte{{1}}}, nil
		},
		openStream: func(int) (peerStream, error) {
			opens++
			return stream, nil
		},
	}
	defer target.Close()
	for _, streamID := range []string{"turn-one", "turn-two"} {
		response, err := target.Send(context.Background(), streamID, "source")
		if err != nil || response.Text != "thanks" {
			t.Fatalf("stream=%s response=%#v err=%v", streamID, response, err)
		}
	}
	if opens != 1 {
		t.Fatalf("opens=%d, want one persistent stream", opens)
	}
}

func TestReadCompletedResponseSkipsEmptyControlSegment(t *testing.T) {
	next := make(chan peerNextResult, 3)
	next <- peerNextResult{chunk: &genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}}}
	next <- peerNextResult{chunk: &genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text("主动开场"), Ctrl: &genx.StreamCtrl{Label: "assistant"}}}
	next <- peerNextResult{chunk: &genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}}}
	target := PeerTarget{}
	response, err := target.readCompletedResponse(context.Background(), next, "", nil, time.Now(), nil, true)
	if err != nil || response.Text != "主动开场" {
		t.Fatalf("response=%#v err=%v", response, err)
	}
}

func TestReadCompletedResponseRejectsEmptyUserTurnImmediately(t *testing.T) {
	next := make(chan peerNextResult, 1)
	next <- peerNextResult{chunk: &genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}}}
	target := PeerTarget{}
	_, err := target.readCompletedResponse(context.Background(), next, "turn", nil, time.Now(), nil, false)
	if !errors.Is(err, ErrEmptyResponse) {
		t.Fatalf("error=%v, want ErrEmptyResponse", err)
	}
}

func TestPreviousTurnChunkMatchingUsesExactStreamBoundary(t *testing.T) {
	previous := []string{"case-turn-one"}
	for _, actual := range []string{"case-turn-one", "case-turn-one:ast:2"} {
		chunk := &genx.MessageChunk{Ctrl: &genx.StreamCtrl{StreamID: actual}}
		if !chunkBelongsToPreviousTurn(chunk, "case-turn-two", previous) {
			t.Fatalf("stream %q was not identified as previous", actual)
		}
	}
	for _, actual := range []string{"case-turn-two", "case-turn-two:ast:1", "case-turn-one-more", "provider-audio"} {
		chunk := &genx.MessageChunk{Ctrl: &genx.StreamCtrl{StreamID: actual}}
		if chunkBelongsToPreviousTurn(chunk, "case-turn-two", previous) {
			t.Fatalf("stream %q was incorrectly identified as previous", actual)
		}
	}
}

func emitTranslatedAudio(stream *fakeModeStream) {
	for _, chunk := range []*genx.MessageChunk{
		{Role: genx.RoleModel, Part: genx.Text("thanks"), Ctrl: &genx.StreamCtrl{Label: "assistant"}},
		{Role: genx.RoleModel, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}},
		{Role: genx.RoleModel, Part: &genx.Blob{MIMEType: "audio/opus", Data: []byte{1}}, Ctrl: &genx.StreamCtrl{Label: "assistant"}},
		{Role: genx.RoleModel, Part: &genx.Blob{MIMEType: "audio/opus"}, Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}},
	} {
		stream.output <- fakeModeResult{chunk: chunk}
	}
}

func TestRunningCandidateAcceptsMissingV025WorkflowName(t *testing.T) {
	state := rpcapi.PeerRunWorkspaceState{RuntimeState: rpcapi.PeerRunStatusStateRunning, WorkspaceName: "candidate"}
	if matches, mismatch := runningMatchesCandidate(state, "candidate", "shadow-workflow"); !matches {
		t.Fatalf("missing workflow_name rejected: %s", mismatch)
	}
}

func TestRunningCandidateRejectsReportedWorkflowMismatch(t *testing.T) {
	actual := "other-workflow"
	state := rpcapi.PeerRunWorkspaceState{RuntimeState: rpcapi.PeerRunStatusStateRunning, WorkspaceName: "candidate", WorkflowName: &actual}
	if matches, _ := runningMatchesCandidate(state, "candidate", "shadow-workflow"); matches {
		t.Fatal("reported workflow mismatch was accepted")
	}
}

func TestTextInputChunksKeepUserRoleAndBoundaries(t *testing.T) {
	chunks := textInputChunks("stream", "label", "hello")
	if len(chunks) != 3 || !chunks[0].IsBeginOfStream() || !chunks[2].IsEndOfStream() || chunks[1].Role != genx.RoleUser {
		t.Fatalf("chunks = %#v", chunks)
	}
}

func TestResponseCaptureSeparatesTranslatedTextAndTTSAudio(t *testing.T) {
	capture := responseCapture{audioMIMEs: map[string]bool{}, expectAudio: true}
	capture.observe(&genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text("bonjour")}, time.Millisecond)
	capture.observe(&genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{EndOfStream: true}}, 2*time.Millisecond)
	if !capture.textDone || capture.audioDone {
		t.Fatalf("premature completion: %#v", capture)
	}
	capture.observe(&genx.MessageChunk{Role: genx.RoleModel, Part: &genx.Blob{MIMEType: "audio/mpeg", Data: []byte{1, 2, 3}}}, 3*time.Millisecond)
	capture.observe(&genx.MessageChunk{Role: genx.RoleModel, Part: &genx.Blob{MIMEType: "audio/mpeg"}, Ctrl: &genx.StreamCtrl{EndOfStream: true}}, 4*time.Millisecond)
	result := capture.response(time.Now())
	if result.Text != "bonjour" || result.Evidence["tts_status"] != "received" || result.Evidence["tts_bytes"] != "3" || result.Evidence["tts_mime_types"] != "audio/mpeg" {
		t.Fatalf("response=%#v", result)
	}
}

func TestResponseCaptureAcceptsControlOnlyTextEOS(t *testing.T) {
	capture := responseCapture{audioMIMEs: map[string]bool{}}
	capture.observe(&genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text("answer")}, time.Millisecond)
	capture.observe(&genx.MessageChunk{Role: genx.RoleModel, Ctrl: &genx.StreamCtrl{EndOfStream: true}}, 2*time.Millisecond)
	if !capture.textDone || capture.answer.String() != "answer" {
		t.Fatalf("capture=%#v", capture)
	}
}

func TestResponseCaptureSeparatesInputTranscript(t *testing.T) {
	capture := responseCapture{audioMIMEs: map[string]bool{}}
	capture.observe(&genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text("source"), Ctrl: &genx.StreamCtrl{Label: "transcript"}}, time.Millisecond)
	capture.observe(&genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text("target"), Ctrl: &genx.StreamCtrl{Label: "assistant"}}, 2*time.Millisecond)
	capture.observe(&genx.MessageChunk{Role: genx.RoleModel, Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}}, 3*time.Millisecond)
	result := capture.response(time.Now())
	if result.Text != "target" || result.Evidence["input_transcript"] != "source" {
		t.Fatalf("response = %#v", result)
	}
}

func TestOnlyAssistantContentStartsAnotherRealtimeSegment(t *testing.T) {
	for name, chunk := range map[string]*genx.MessageChunk{
		"transcript": {Role: genx.RoleModel, Part: genx.Text("source"), Ctrl: &genx.StreamCtrl{Label: "transcript"}},
		"empty-eos":  {Role: genx.RoleModel, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}},
	} {
		if startsAssistantResponse(chunk) {
			t.Fatalf("%s unexpectedly starts a response", name)
		}
	}
	if !startsAssistantResponse(&genx.MessageChunk{Role: genx.RoleModel, Part: genx.Text("next"), Ctrl: &genx.StreamCtrl{Label: "assistant"}}) {
		t.Fatal("assistant content did not start a response")
	}
}

func TestStreamErrorEvidenceDistinguishesResponsePhase(t *testing.T) {
	before := responseWithStreamError(Response{}, nil)
	after := responseWithStreamError(Response{Text: "answer"}, nil)
	if before.Evidence["stream_status"] != "incomplete_before_text" || after.Evidence["stream_status"] != "incomplete_after_text" {
		t.Fatalf("before=%#v after=%#v", before, after)
	}
}

func TestPushToTalkRejectsOutputBeforeInputEOS(t *testing.T) {
	stream := newFakeModeStream()
	var once sync.Once
	stream.onPush = func(chunk *genx.MessageChunk) {
		blob, ok := chunk.Part.(*genx.Blob)
		if !ok || len(blob.Data) == 0 {
			return
		}
		once.Do(func() {
			emitTranslatedAudio(stream)
			<-stream.firstRead
			time.Sleep(20 * time.Millisecond)
		})
	}
	target := PeerTarget{RequireAudio: true, InputMode: "push-to-talk"}
	_, err := target.sendModeAudio(context.Background(), stream, nil, "turn", nil, "raidtest", AudioInput{MIMEType: "audio/opus", Frames: [][]byte{{1}}}, map[string]string{})
	if err == nil || !strings.Contains(err.Error(), "before input EOS") {
		t.Fatalf("err=%v", err)
	}
}

func TestPushToTalkRejectsTranscriptBeforeInputEOS(t *testing.T) {
	stream := newFakeModeStream()
	var once sync.Once
	stream.onPush = func(chunk *genx.MessageChunk) {
		blob, ok := chunk.Part.(*genx.Blob)
		if !ok || len(blob.Data) == 0 {
			return
		}
		once.Do(func() {
			stream.output <- fakeModeResult{chunk: &genx.MessageChunk{
				Role: genx.RoleModel,
				Part: genx.Text("source"),
				Ctrl: &genx.StreamCtrl{Label: "transcript"},
			}}
			<-stream.firstRead
			time.Sleep(20 * time.Millisecond)
		})
	}
	target := PeerTarget{RequireAudio: true, InputMode: "push-to-talk"}
	_, err := target.sendModeAudio(context.Background(), stream, nil, "turn", nil, "raidtest", AudioInput{MIMEType: "audio/opus", Frames: [][]byte{{1}}}, map[string]string{})
	if err == nil || !strings.Contains(err.Error(), "before input EOS") {
		t.Fatalf("err=%v", err)
	}
}

func TestRealtimeReadsOutputWhileAudioIsStillOpen(t *testing.T) {
	stream := newFakeModeStream()
	var once sync.Once
	stream.onPush = func(chunk *genx.MessageChunk) {
		blob, ok := chunk.Part.(*genx.Blob)
		if !ok || len(blob.Data) == 0 {
			return
		}
		once.Do(func() {
			emitTranslatedAudio(stream)
			<-stream.firstRead
			time.Sleep(20 * time.Millisecond)
		})
	}
	target := PeerTarget{RequireAudio: true, InputMode: "realtime", RealtimeSettle: 5 * time.Millisecond}
	response, err := target.sendModeAudio(context.Background(), stream, nil, "turn", nil, "raidtest", AudioInput{MIMEType: "audio/opus", Frames: [][]byte{{1}}}, map[string]string{})
	if err != nil || response.Text != "thanks" || response.Evidence["first_response_before_input_eos"] != "true" || response.Evidence["tts_status"] != "received" {
		t.Fatalf("response=%#v err=%v", response, err)
	}
}

func TestPushToTalkAcceptsOutputAfterInputEOS(t *testing.T) {
	stream := newFakeModeStream()
	stream.onPush = func(chunk *genx.MessageChunk) {
		if chunk.IsEndOfStream() {
			emitTranslatedAudio(stream)
		}
	}
	target := PeerTarget{RequireAudio: true, InputMode: "push-to-talk"}
	response, err := target.sendModeAudio(context.Background(), stream, nil, "turn", nil, "raidtest", AudioInput{MIMEType: "audio/opus", Frames: [][]byte{{1}}}, map[string]string{})
	if err != nil || response.Text != "thanks" || response.Evidence["first_response_before_input_eos"] != "false" || response.Evidence["tts_status"] != "received" {
		t.Fatalf("response=%#v err=%v", response, err)
	}
}

func TestRealtimeAggregatesSegmentsAcrossInputEOS(t *testing.T) {
	stream := newFakeModeStream()
	var once sync.Once
	stream.onPush = func(chunk *genx.MessageChunk) {
		blob, ok := chunk.Part.(*genx.Blob)
		if ok && len(blob.Data) > 0 {
			once.Do(func() {
				for _, response := range []*genx.MessageChunk{
					{Role: genx.RoleModel, Part: genx.Text("first"), Ctrl: &genx.StreamCtrl{Label: "assistant"}},
					{Role: genx.RoleModel, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}},
					{Role: genx.RoleModel, Part: &genx.Blob{MIMEType: "audio/opus", Data: []byte{1}}, Ctrl: &genx.StreamCtrl{Label: "assistant"}},
					{Role: genx.RoleModel, Part: &genx.Blob{MIMEType: "audio/opus"}, Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}},
				} {
					stream.output <- fakeModeResult{chunk: response}
				}
			})
		}
		if chunk.IsEndOfStream() {
			for _, response := range []*genx.MessageChunk{
				{Role: genx.RoleModel, Part: genx.Text("second"), Ctrl: &genx.StreamCtrl{Label: "assistant"}},
				{Role: genx.RoleModel, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}},
				{Role: genx.RoleModel, Part: &genx.Blob{MIMEType: "audio/opus", Data: []byte{2}}, Ctrl: &genx.StreamCtrl{Label: "assistant"}},
				{Role: genx.RoleModel, Part: &genx.Blob{MIMEType: "audio/opus"}, Ctrl: &genx.StreamCtrl{Label: "assistant", EndOfStream: true}},
			} {
				stream.output <- fakeModeResult{chunk: response}
			}
		}
	}
	target := PeerTarget{RequireAudio: true, InputMode: "realtime", RealtimeSettle: 5 * time.Millisecond}
	response, err := target.sendModeAudio(context.Background(), stream, nil, "turn", nil, "raidtest", AudioInput{MIMEType: "audio/opus", Frames: [][]byte{{1}}}, map[string]string{})
	if err != nil || response.Text != "firstsecond" || response.Evidence["tts_bytes"] != "2" {
		t.Fatalf("response=%#v err=%v", response, err)
	}
}

func TestModeAudioReturnsWhenContextExpiresAfterInputEOS(t *testing.T) {
	stream := newFakeModeStream()
	blocked := make(chan struct{})
	stream.blockNext = blocked
	defer close(blocked)
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	target := PeerTarget{RequireAudio: true, InputMode: "realtime"}
	started := time.Now()
	response, err := target.sendModeAudio(ctx, stream, nil, "turn", nil, "raidtest", AudioInput{MIMEType: "audio/opus", Frames: [][]byte{{1}}}, map[string]string{})
	if !errors.Is(err, context.DeadlineExceeded) || time.Since(started) > time.Second || response.Evidence["stream_status"] != "incomplete_before_text" {
		t.Fatalf("response=%#v err=%v elapsed=%s", response, err, time.Since(started))
	}
}
