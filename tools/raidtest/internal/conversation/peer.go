package conversation

import (
	"context"
	"errors"
	"fmt"
	"io"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/rpcapi"
	"github.com/GizClaw/gizclaw-go/sdk/go/gizcli"
)

type PeerTarget struct {
	Client         *gizcli.Client
	Timeout        time.Duration
	RealtimeSettle time.Duration
	RequireAudio   bool
	InputMode      string
	InputAudio     func(context.Context, string) (AudioInput, error)
	AgentStarts    bool

	sendMu          sync.Mutex
	streamMu        sync.Mutex
	stream          peerStream
	streamNext      <-chan peerNextResult
	streamStop      chan struct{}
	streamTurnIDs   map[string]struct{}
	openStream      func(int) (peerStream, error)
	recallWorkspace func(context.Context, string, rpcapi.ServerRunWorkspaceRecallRequest) (*rpcapi.ServerRunWorkspaceRecallResponse, error)
	requestSeq      atomic.Uint64
}

type AudioInput struct {
	MIMEType string
	Frames   [][]byte
}

// CacheAudioInput gives every mode the same synthesized fixture for an
// utterance. Returned frames are cloned so a caller cannot mutate the cached
// value, and failed synthesis is not cached so a later mode can retry it.
func CacheAudioInput(source func(context.Context, string) (AudioInput, error)) func(context.Context, string) (AudioInput, error) {
	var mutex sync.Mutex
	cache := map[string]AudioInput{}
	return func(ctx context.Context, text string) (AudioInput, error) {
		mutex.Lock()
		defer mutex.Unlock()
		if input, ok := cache[text]; ok {
			return cloneAudioInput(input), nil
		}
		input, err := source(ctx, text)
		if err != nil {
			return AudioInput{}, err
		}
		cache[text] = cloneAudioInput(input)
		return cloneAudioInput(input), nil
	}
}

func cloneAudioInput(input AudioInput) AudioInput {
	cloned := AudioInput{MIMEType: input.MIMEType, Frames: make([][]byte, len(input.Frames))}
	for index := range input.Frames {
		cloned.Frames[index] = append([]byte(nil), input.Frames[index]...)
	}
	return cloned
}

type peerStream interface {
	Push(context.Context, *genx.MessageChunk) error
	Next() (*genx.MessageChunk, error)
	Close() error
}

func (p *PeerTarget) Select(ctx context.Context, workspaceName, workflowID string, agentStarts bool) (Response, error) {
	if err := p.Close(); err != nil {
		return Response{}, fmt.Errorf("close previous Peer stream: %w", err)
	}
	p.AgentStarts = agentStarts
	if p.AgentStarts {
		if _, _, err := p.ensureStream(); err != nil {
			return Response{}, fmt.Errorf("subscribe before selecting agent-start Workspace: %w", err)
		}
	}
	started := time.Now()
	if _, err := p.Client.SetServerRunWorkspace(ctx, p.nextRequestID("set-workspace"), rpcapi.ServerSetRunWorkspaceRequest{WorkspaceName: workspaceName}); err != nil {
		return Response{}, err
	}
	return p.reloadAndConsumeOpening(ctx, "start-workspace", workspaceName, workflowID, started)
}

func (p *PeerTarget) reloadAndConsumeOpening(ctx context.Context, action, workspaceName, workflowID string, started time.Time) (Response, error) {
	var next <-chan peerNextResult
	if p.AgentStarts {
		_, streamNext, err := p.ensureStream()
		if err != nil {
			return Response{}, fmt.Errorf("subscribe before agent opening: %w", err)
		}
		next = streamNext
	}
	if started.IsZero() {
		started = time.Now()
	}
	if _, err := p.Client.ReloadServerRunWorkspace(ctx, p.nextRequestID(action)); err != nil {
		return Response{}, err
	}
	if err := p.waitRunning(ctx, workspaceName, workflowID); err != nil {
		return Response{}, err
	}
	if !p.AgentStarts {
		return Response{}, nil
	}
	openingCtx := ctx
	cancel := func() {}
	if p.Timeout > 0 {
		openingCtx, cancel = context.WithTimeout(ctx, p.Timeout)
	}
	defer cancel()
	response, err := p.readCompletedResponse(openingCtx, next, "", nil, started, map[string]string{"initiative": "agent"}, true)
	if err != nil {
		_ = p.Close()
		return response, fmt.Errorf("consume agent opening: %w", err)
	}
	return response, nil
}

func (p *PeerTarget) Reload(ctx context.Context) error {
	if err := p.Close(); err != nil {
		return fmt.Errorf("close Peer stream before reload: %w", err)
	}
	_, err := p.reloadAndConsumeOpening(ctx, "reload-workspace", "", "", time.Time{})
	// Agent-start Workflows emit a fresh unsolicited opening on reload. Waiting
	// for it prevents the next player request from racing a still-running graph,
	// but its audio is not a planned acceptance response. Some Dev providers end
	// that discarded TTS stream with AGENT_AUDIO_OUTPUT_ERROR after the text/graph
	// is complete; treat only that known discard error as non-fatal.
	if err != nil && p.AgentStarts && strings.Contains(err.Error(), "AGENT_AUDIO_OUTPUT_ERROR") {
		return nil
	}
	return err
}

func (p *PeerTarget) WaitForRecall(ctx context.Context, facts []string, timeout time.Duration) error {
	if len(facts) == 0 {
		return nil
	}
	if timeout <= 0 {
		return errors.New("positive persistence timeout is required")
	}
	if err := p.Close(); err != nil {
		return fmt.Errorf("close Peer stream before persisted recall: %w", err)
	}
	waitCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	query := strings.Join(facts, " ")
	limit := 20
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()
	var lastDetail string
	attempts := 0
	for {
		attempts++
		attemptTimeout := 15 * time.Second
		if deadline, ok := waitCtx.Deadline(); ok {
			attemptTimeout = min(attemptTimeout, time.Until(deadline))
		}
		attemptCtx, attemptCancel := context.WithTimeout(waitCtx, attemptTimeout)
		response, err := p.workspaceRecall(attemptCtx, p.nextRequestID("recall-barrier"), rpcapi.ServerRunWorkspaceRecallRequest{Query: query, Limit: &limit})
		attemptCancel()
		if err != nil {
			lastDetail = err.Error()
		} else if response == nil {
			lastDetail = "Workspace recall returned an empty response"
		} else if !response.Available {
			return errors.New("Workspace recall is unavailable")
		} else if recallContainsAll(response.Hits, facts) {
			return nil
		} else {
			lastDetail = fmt.Sprintf("required facts not recalled yet: %s", strings.Join(facts, ", "))
		}
		select {
		case <-waitCtx.Done():
			return fmt.Errorf("persistence timeout after %s (%d attempts): %s", timeout, attempts, lastDetail)
		case <-ticker.C:
		}
	}
}

func (p *PeerTarget) workspaceRecall(ctx context.Context, id string, request rpcapi.ServerRunWorkspaceRecallRequest) (*rpcapi.ServerRunWorkspaceRecallResponse, error) {
	if p.recallWorkspace != nil {
		return p.recallWorkspace(ctx, id, request)
	}
	if p.Client == nil {
		return nil, errors.New("Workspace recall client is not configured")
	}
	return p.Client.ServerRunWorkspaceRecall(ctx, id, request)
}

func recallContainsAll(hits []rpcapi.PeerRunRecallHit, facts []string) bool {
	for _, fact := range facts {
		found := false
		for _, hit := range hits {
			text := normalizeLiteral(hit.Name + "\n" + hit.Snippet)
			if strings.Contains(text, normalizeLiteral(fact)) {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}
	return true
}

func (p *PeerTarget) nextRequestID(action string) string {
	return fmt.Sprintf("raidtest-%s-%d", action, p.requestSeq.Add(1))
}

func (p *PeerTarget) waitRunning(ctx context.Context, workspaceName, workflowID string) error {
	deadline := time.NewTimer(30 * time.Second)
	defer deadline.Stop()
	ticker := time.NewTicker(250 * time.Millisecond)
	defer ticker.Stop()
	lastMismatch := ""
	for {
		state, err := p.Client.GetServerRunWorkspace(ctx, "raidtest-get-run-workspace")
		if err != nil {
			return err
		}
		if state.RuntimeState == rpcapi.PeerRunStatusStateRunning {
			if matches, mismatch := runningMatchesCandidate(*state, workspaceName, workflowID); matches {
				return nil
			} else {
				lastMismatch = mismatch
			}
		}
		if state.RuntimeState == rpcapi.PeerRunStatusStateError {
			message := ""
			if state.Message != nil {
				message = *state.Message
			}
			return fmt.Errorf("Workspace failed to start: %s", message)
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-deadline.C:
			if lastMismatch != "" {
				return fmt.Errorf("Workspace did not select candidate within 30s: %s", lastMismatch)
			}
			return errors.New("Workspace did not reach running state within 30s")
		case <-ticker.C:
		}
	}
}

func runningMatchesCandidate(state rpcapi.PeerRunWorkspaceState, workspaceName, workflowID string) (bool, string) {
	if workspaceName != "" && state.WorkspaceName != workspaceName {
		return false, fmt.Sprintf("running Workspace %q, want %q", state.WorkspaceName, workspaceName)
	}
	// v0.2.5 does not populate workflow_name in the run-state response. The
	// owner-scoped Workspace creation already resolved the supplied alias through
	// the shadow RuntimeProfile, so only enforce this field when the Server emits it.
	if workflowID != "" && state.WorkflowName != nil && strings.TrimSpace(*state.WorkflowName) != "" && *state.WorkflowName != workflowID {
		return false, fmt.Sprintf("running Workflow %q, want shadow Workflow %q", *state.WorkflowName, workflowID)
	}
	return true, ""
}

func (p *PeerTarget) Send(ctx context.Context, streamID, text string) (Response, error) {
	p.sendMu.Lock()
	defer p.sendMu.Unlock()
	if p.Client == nil && p.openStream == nil {
		return Response{}, fmt.Errorf("peer client is required")
	}
	stream, next, err := p.ensureStream()
	if err != nil {
		return Response{}, err
	}
	previousStreamIDs := p.beginTurn(streamID)
	failed := true
	defer func() {
		if failed {
			_ = p.Close()
		}
	}()
	if p.Timeout <= 0 {
		p.Timeout = 2 * time.Minute
	}
	turnCtx, cancel := context.WithTimeout(ctx, p.Timeout)
	defer cancel()
	label := "raidtest"
	inputEvidence := map[string]string{}
	if p.InputAudio == nil {
		for _, chunk := range textInputChunks(streamID, label, text) {
			if err := stream.Push(turnCtx, chunk); err != nil {
				return Response{}, err
			}
		}
	} else {
		audio, err := p.InputAudio(turnCtx, text)
		if err != nil {
			return Response{}, fmt.Errorf("synthesize input audio: %w", err)
		}
		inputEvidence["input_mode"] = p.InputMode
		inputEvidence["input_audio_mime"] = audio.MIMEType
		inputEvidence["input_audio_bytes"] = strconv.Itoa(audioBytes(audio.Frames))
		if p.InputMode == "realtime" || p.InputMode == "push-to-talk" {
			response, sendErr := p.sendModeAudio(turnCtx, stream, next, streamID, previousStreamIDs, label, audio, inputEvidence)
			failed = sendErr != nil
			return response, sendErr
		}
		if err := pushAudioInput(turnCtx, stream, streamID, label, audio); err != nil {
			return Response{}, err
		}
	}
	started := time.Now()
	response, readErr := p.readCompletedResponse(turnCtx, next, streamID, previousStreamIDs, started, inputEvidence, false)
	failed = readErr != nil
	return response, readErr
}

func (p *PeerTarget) ensureStream() (peerStream, <-chan peerNextResult, error) {
	p.streamMu.Lock()
	defer p.streamMu.Unlock()
	if p.stream != nil {
		return p.stream, p.streamNext, nil
	}
	open := p.openStream
	if open == nil {
		open = func(buffer int) (peerStream, error) { return p.Client.OpenPeerStream(buffer) }
	}
	stream, err := open(128)
	if err != nil {
		return nil, nil, err
	}
	stop := make(chan struct{})
	p.stream = stream
	p.streamStop = stop
	p.streamNext = readPeerStream(stream, stop)
	p.streamTurnIDs = map[string]struct{}{}
	return stream, p.streamNext, nil
}

func (p *PeerTarget) beginTurn(streamID string) []string {
	p.streamMu.Lock()
	defer p.streamMu.Unlock()
	previous := make([]string, 0, len(p.streamTurnIDs))
	for known := range p.streamTurnIDs {
		if known != streamID {
			previous = append(previous, known)
		}
	}
	p.streamTurnIDs[streamID] = struct{}{}
	return previous
}

// Close ends the workspace-scoped conversational stream. Successful turns in
// the same case deliberately keep it open; Select and Reload establish a new
// stream boundary before changing runtime state.
func (p *PeerTarget) Close() error {
	p.streamMu.Lock()
	defer p.streamMu.Unlock()
	if p.stream == nil {
		return nil
	}
	close(p.streamStop)
	err := p.stream.Close()
	p.stream = nil
	p.streamNext = nil
	p.streamStop = nil
	p.streamTurnIDs = nil
	return err
}

func (p *PeerTarget) readCompletedResponse(ctx context.Context, next <-chan peerNextResult, streamID string, previousStreamIDs []string, started time.Time, inputEvidence map[string]string, skipEmptySegments bool) (Response, error) {
	capture := responseCapture{audioMIMEs: map[string]bool{}, expectAudio: p.RequireAudio}
	for {
		var received peerNextResult
		var ok bool
		select {
		case <-ctx.Done():
			return responseWithStreamError(capture.response(started), inputEvidence), ctx.Err()
		case received, ok = <-next:
		}
		if !ok || received.err != nil {
			return responseWithStreamError(capture.response(started), inputEvidence), peerReadError(received.err)
		}
		chunk := received.chunk
		if chunkBelongsToPreviousTurn(chunk, streamID, previousStreamIDs) {
			continue
		}
		if chunk != nil && chunk.Ctrl != nil && chunk.Ctrl.Error != "" {
			code := strings.TrimSpace(chunk.Ctrl.ErrorCode)
			if code != "" {
				return responseWithStreamError(capture.response(started), inputEvidence), fmt.Errorf("target stream error %s: %s", code, chunk.Ctrl.Error)
			}
			return responseWithStreamError(capture.response(started), inputEvidence), fmt.Errorf("target stream error: %s", chunk.Ctrl.Error)
		}
		capture.observe(chunk, time.Since(started))
		if capture.textDone && (!p.RequireAudio || capture.audioDone) {
			result := responseWithEvidence(capture.response(started), inputEvidence)
			if result.Text == "" {
				if skipEmptySegments {
					// Agent-initiated runtimes may close an empty control segment before
					// beginning the actual assistant response. Keep the subscription alive
					// until text arrives or the caller's deadline expires.
					capture.beginNextResponse()
					continue
				}
				return result, ErrEmptyResponse
			}
			if p.RequireAudio && capture.audioBytes == 0 {
				return result, errors.New("target returned no TTS audio")
			}
			return result, nil
		}
	}
}

func (p *PeerTarget) sendModeAudio(ctx context.Context, stream peerStream, next <-chan peerNextResult, streamID string, previousStreamIDs []string, label string, audio AudioInput, inputEvidence map[string]string) (Response, error) {
	type pushResult struct {
		err error
	}
	if next == nil {
		// Unit-level callers can supply only a stream. Production calls always
		// use the one stream-owned reader created by ensureStream.
		next = readPeerStream(stream, make(chan struct{}))
	}
	started := time.Now()
	var inputEOS atomic.Int64
	pushDone := make(chan pushResult, 1)
	go func() {
		err := pushAudioInputObserved(ctx, stream, streamID, label, audio, func(at time.Time) {
			inputEOS.Store(at.UnixNano())
		})
		pushDone <- pushResult{err: err}
	}()
	capture := responseCapture{audioMIMEs: map[string]bool{}, expectAudio: p.RequireAudio}
	inputDone := false
	responseDone := false
	settleWindow := p.RealtimeSettle
	if settleWindow <= 0 {
		settleWindow = 750 * time.Millisecond
	}
	var settleTimer *time.Timer
	var settle <-chan time.Time
	startSettle := func() {
		if settleTimer == nil {
			settleTimer = time.NewTimer(settleWindow)
		} else {
			if !settleTimer.Stop() {
				select {
				case <-settleTimer.C:
				default:
				}
			}
			settleTimer.Reset(settleWindow)
		}
		settle = settleTimer.C
	}
	stopSettle := func() {
		if settleTimer != nil && !settleTimer.Stop() {
			select {
			case <-settleTimer.C:
			default:
			}
		}
		settle = nil
	}
	defer stopSettle()
	for {
		select {
		case <-ctx.Done():
			return responseWithStreamError(capture.response(started), inputEvidence), ctx.Err()
		case <-settle:
			return p.completedResponse(capture, started, inputEvidence)
		case pushed := <-pushDone:
			pushDone = nil
			inputDone = true
			if pushed.err != nil {
				return responseWithStreamError(capture.response(started), inputEvidence), pushed.err
			}
			if eosAt := inputEOS.Load(); eosAt > 0 {
				inputEvidence["input_eos_ms"] = strconv.FormatInt(time.Unix(0, eosAt).Sub(started).Milliseconds(), 10)
			}
			if responseDone {
				if p.InputMode == "realtime" {
					startSettle()
				} else {
					return p.completedResponse(capture, started, inputEvidence)
				}
			}
		case received, ok := <-next:
			if !ok || received.err != nil {
				return responseWithStreamError(capture.response(started), inputEvidence), peerReadError(received.err)
			}
			if chunkBelongsToPreviousTurn(received.chunk, streamID, previousStreamIDs) {
				continue
			}
			if received.chunk != nil && received.chunk.Ctrl != nil && received.chunk.Ctrl.Error != "" {
				code := strings.TrimSpace(received.chunk.Ctrl.ErrorCode)
				if code != "" {
					return responseWithStreamError(capture.response(started), inputEvidence), fmt.Errorf("target stream error %s: %s", code, received.chunk.Ctrl.Error)
				}
				return responseWithStreamError(capture.response(started), inputEvidence), fmt.Errorf("target stream error: %s", received.chunk.Ctrl.Error)
			}
			eosAt := inputEOS.Load()
			beforeInputEOS := eosAt == 0 || received.receivedAt.UnixNano() < eosAt
			if p.InputMode == "push-to-talk" && beforeInputEOS && isPTTOutputChunk(received.chunk) {
				return responseWithStreamError(capture.response(started), inputEvidence), errors.New("push-to-talk target emitted output before input EOS")
			}
			if responseDone && startsAssistantResponse(received.chunk) {
				capture.beginNextResponse()
				responseDone = false
				stopSettle()
			}
			hadFirstResponse := capture.first != 0
			capture.observe(received.chunk, time.Since(started))
			if !hadFirstResponse && capture.first != 0 {
				inputEvidence["first_response_before_input_eos"] = strconv.FormatBool(beforeInputEOS)
			}
			responseDone = capture.textDone && (!p.RequireAudio || capture.audioDone)
			if responseDone && inputDone {
				if p.InputMode == "realtime" {
					startSettle()
				} else {
					return p.completedResponse(capture, started, inputEvidence)
				}
			}
		}
	}
}

func (p *PeerTarget) completedResponse(capture responseCapture, started time.Time, inputEvidence map[string]string) (Response, error) {
	result := responseWithEvidence(capture.response(started), inputEvidence)
	if result.Text == "" {
		return result, ErrEmptyResponse
	}
	if p.RequireAudio && capture.audioBytes == 0 {
		return result, errors.New("target returned no TTS audio")
	}
	return result, nil
}

func responseWithStreamError(response Response, extra map[string]string) Response {
	response = responseWithEvidence(response, extra)
	if response.Text == "" {
		response.Evidence["stream_status"] = "incomplete_before_text"
	} else {
		response.Evidence["stream_status"] = "incomplete_after_text"
	}
	return response
}

func responseWithEvidence(response Response, extra map[string]string) Response {
	if response.Evidence == nil {
		response.Evidence = map[string]string{}
	}
	for key, value := range extra {
		response.Evidence[key] = value
	}
	return response
}

func textInputChunks(streamID, label, value string) []*genx.MessageChunk {
	return []*genx.MessageChunk{
		{Role: genx.RoleUser, Ctrl: &genx.StreamCtrl{StreamID: streamID, Label: label, BeginOfStream: true}},
		{Role: genx.RoleUser, Part: genx.Text(value), Ctrl: &genx.StreamCtrl{StreamID: streamID, Label: label}},
		{Role: genx.RoleUser, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{StreamID: streamID, Label: label, EndOfStream: true}},
	}
}

func pushAudioInput(ctx context.Context, stream peerStream, streamID, label string, input AudioInput) error {
	return pushAudioInputObserved(ctx, stream, streamID, label, input, nil)
}

func pushAudioInputObserved(ctx context.Context, stream peerStream, streamID, label string, input AudioInput, onEOS func(time.Time)) error {
	if strings.TrimSpace(input.MIMEType) == "" || len(input.Frames) == 0 || audioBytes(input.Frames) == 0 {
		return errors.New("input audio must contain frames")
	}
	if err := stream.Push(ctx, &genx.MessageChunk{Role: genx.RoleUser, Part: &genx.Blob{MIMEType: input.MIMEType}, Ctrl: &genx.StreamCtrl{StreamID: streamID, Label: label, BeginOfStream: true}}); err != nil {
		return err
	}
	timestamp := time.Now().UnixMilli()
	for index, frame := range input.Frames {
		if len(frame) == 0 {
			continue
		}
		if err := stream.Push(ctx, &genx.MessageChunk{Role: genx.RoleUser, Part: &genx.Blob{MIMEType: input.MIMEType, Data: frame}, Ctrl: &genx.StreamCtrl{StreamID: streamID, Label: label, Timestamp: timestamp}}); err != nil {
			return err
		}
		timestamp += 20
		if index+1 < len(input.Frames) {
			timer := time.NewTimer(20 * time.Millisecond)
			select {
			case <-ctx.Done():
				timer.Stop()
				return ctx.Err()
			case <-timer.C:
			}
		}
	}
	if onEOS != nil {
		onEOS(time.Now())
	}
	return stream.Push(ctx, &genx.MessageChunk{Role: genx.RoleUser, Part: &genx.Blob{MIMEType: input.MIMEType}, Ctrl: &genx.StreamCtrl{StreamID: streamID, Label: label, EndOfStream: true}})
}

func audioBytes(frames [][]byte) int {
	total := 0
	for _, frame := range frames {
		total += len(frame)
	}
	return total
}

type responseCapture struct {
	answer      strings.Builder
	transcript  strings.Builder
	first       time.Duration
	textDone    bool
	audioDone   bool
	audioBytes  int
	audioMIMEs  map[string]bool
	expectAudio bool
}

func (c *responseCapture) beginNextResponse() {
	c.textDone = false
	c.audioDone = false
}

func (c *responseCapture) observe(chunk *genx.MessageChunk, elapsed time.Duration) {
	if chunk == nil {
		return
	}
	label := ""
	if chunk.Ctrl != nil {
		label = strings.TrimSpace(chunk.Ctrl.Label)
	}
	if strings.EqualFold(label, "transcript") {
		if value, ok := chunk.Part.(genx.Text); ok && value != "" {
			c.transcript.WriteString(string(value))
		}
		return
	}
	assistant := strings.EqualFold(chunk.Name, "assistant") || strings.EqualFold(label, "assistant") || (label == "" && chunk.Name == "" && chunk.Role == genx.RoleModel)
	if !assistant {
		return
	}
	switch value := chunk.Part.(type) {
	case genx.Text:
		if value != "" {
			if c.first == 0 {
				c.first = elapsed
			}
			c.answer.WriteString(string(value))
		}
		if chunk.Ctrl != nil && chunk.Ctrl.EndOfStream {
			c.textDone = true
		}
	case *genx.Blob:
		if value == nil || !strings.HasPrefix(strings.ToLower(value.MIMEType), "audio/") {
			return
		}
		c.audioBytes += len(value.Data)
		if value.MIMEType != "" {
			c.audioMIMEs[value.MIMEType] = true
		}
		if chunk.Ctrl != nil && chunk.Ctrl.EndOfStream {
			c.audioDone = true
		}
	default:
		if chunk.Ctrl != nil && chunk.Ctrl.EndOfStream {
			c.textDone = true
		}
	}
}

func isAssistantChunk(chunk *genx.MessageChunk) bool {
	if chunk == nil {
		return false
	}
	label := ""
	if chunk.Ctrl != nil {
		label = strings.TrimSpace(chunk.Ctrl.Label)
	}
	return strings.EqualFold(chunk.Name, "assistant") ||
		strings.EqualFold(label, "assistant") ||
		(label == "" && chunk.Name == "" && chunk.Role == genx.RoleModel)
}

func isPTTOutputChunk(chunk *genx.MessageChunk) bool {
	if chunk == nil {
		return false
	}
	if chunk.Ctrl != nil && strings.EqualFold(strings.TrimSpace(chunk.Ctrl.Label), "transcript") {
		return true
	}
	return isAssistantChunk(chunk)
}

func startsAssistantResponse(chunk *genx.MessageChunk) bool {
	if !isAssistantChunk(chunk) {
		return false
	}
	if chunk.Ctrl != nil && chunk.Ctrl.BeginOfStream {
		return true
	}
	switch value := chunk.Part.(type) {
	case genx.Text:
		return value != ""
	case *genx.Blob:
		return value != nil && len(value.Data) > 0
	default:
		return false
	}
}

func chunkBelongsToPreviousTurn(chunk *genx.MessageChunk, current string, previous []string) bool {
	if chunk == nil || chunk.Ctrl == nil {
		return false
	}
	actual := strings.TrimSpace(chunk.Ctrl.StreamID)
	if actual == "" || streamIDMatches(actual, current) {
		return false
	}
	for _, old := range previous {
		if streamIDMatches(actual, old) {
			return true
		}
	}
	return false
}

func streamIDMatches(actual, input string) bool {
	actual = strings.TrimSpace(actual)
	input = strings.TrimSpace(input)
	return input != "" && (actual == input || strings.HasPrefix(actual, input+":"))
}

func (c *responseCapture) response(started time.Time) Response {
	evidence := map[string]string{}
	if transcript := strings.TrimSpace(c.transcript.String()); transcript != "" {
		evidence["input_transcript"] = transcript
	}
	if c.audioDone && c.audioBytes > 0 {
		evidence["tts_status"] = "received"
	} else if c.audioDone {
		evidence["tts_status"] = "empty"
	} else if c.expectAudio {
		evidence["tts_status"] = "not_completed"
	}
	if c.audioBytes > 0 {
		evidence["tts_bytes"] = strconv.Itoa(c.audioBytes)
	}
	if len(c.audioMIMEs) > 0 {
		mimes := make([]string, 0, len(c.audioMIMEs))
		for mime := range c.audioMIMEs {
			mimes = append(mimes, mime)
		}
		sort.Strings(mimes)
		evidence["tts_mime_types"] = strings.Join(mimes, ",")
	}
	return Response{Text: strings.TrimSpace(c.answer.String()), FirstResponse: c.first, TotalResponse: time.Since(started), Evidence: evidence}
}

type peerNextResult struct {
	chunk      *genx.MessageChunk
	err        error
	receivedAt time.Time
}

// readPeerStream is the only reader for a Peer stream. Turns consume its
// ordered results sequentially, so a canceled turn cannot leave a blocked
// reader behind to steal the next turn's response.
func readPeerStream(stream peerStream, stop <-chan struct{}) <-chan peerNextResult {
	next := make(chan peerNextResult, 128)
	go func() {
		defer close(next)
		for {
			chunk, err := stream.Next()
			result := peerNextResult{chunk: chunk, err: err, receivedAt: time.Now()}
			select {
			case next <- result:
			case <-stop:
				return
			}
			if err != nil {
				return
			}
		}
	}()
	return next
}

func peerReadError(err error) error {
	if err == nil {
		err = io.EOF
	}
	if errors.Is(err, io.EOF) {
		return fmt.Errorf("peer stream closed before answer: %w", err)
	}
	return err
}
