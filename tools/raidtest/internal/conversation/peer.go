package conversation

import (
	"context"
	"errors"
	"fmt"
	"io"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/rpcapi"
	"github.com/GizClaw/gizclaw-go/sdk/go/gizcli"
)

type PeerTarget struct {
	Client       *gizcli.Client
	Timeout      time.Duration
	RequireAudio bool
	InputAudio   func(context.Context, string) (AudioInput, error)
}

type AudioInput struct {
	MIMEType string
	Frames   [][]byte
}

func (p *PeerTarget) Select(ctx context.Context, workspaceName, workflowID string) error {
	if _, err := p.Client.SetServerRunWorkspace(ctx, "raidtest-set-workspace", rpcapi.ServerSetRunWorkspaceRequest{WorkspaceName: workspaceName}); err != nil {
		return err
	}
	if _, err := p.Client.ReloadServerRunWorkspace(ctx, "raidtest-start-workspace"); err != nil {
		return err
	}
	return p.waitRunning(ctx, workspaceName, workflowID)
}

func (p *PeerTarget) Reload(ctx context.Context) error {
	_, err := p.Client.ReloadServerRunWorkspace(ctx, "raidtest-reload-workspace")
	if err != nil {
		return err
	}
	return p.waitRunning(ctx, "", "")
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
	if p.Client == nil {
		return Response{}, fmt.Errorf("peer client is required")
	}
	stream, err := p.Client.OpenPeerStream(128)
	if err != nil {
		return Response{}, err
	}
	defer stream.Close()
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
		if err := pushAudioInput(turnCtx, stream, streamID, label, audio); err != nil {
			return Response{}, err
		}
		inputEvidence["input_audio_mime"] = audio.MIMEType
		inputEvidence["input_audio_bytes"] = strconv.Itoa(audioBytes(audio.Frames))
	}
	started := time.Now()
	capture := responseCapture{audioMIMEs: map[string]bool{}, expectAudio: p.RequireAudio}
	for {
		chunk, err := nextWithContext(turnCtx, stream)
		if err != nil {
			return responseWithStreamError(capture.response(started), inputEvidence), err
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
				return result, ErrEmptyResponse
			}
			if p.RequireAudio && capture.audioBytes == 0 {
				return result, errors.New("target returned no TTS audio")
			}
			return result, nil
		}
	}
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

func pushAudioInput(ctx context.Context, stream *gizcli.PeerStream, streamID, label string, input AudioInput) error {
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

type nextResult struct {
	chunk *genx.MessageChunk
	err   error
}

func nextWithContext(ctx context.Context, stream *gizcli.PeerStream) (*genx.MessageChunk, error) {
	ch := make(chan nextResult, 1)
	go func() { c, e := stream.Next(); ch <- nextResult{c, e} }()
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	case result := <-ch:
		if result.err == io.EOF {
			return nil, fmt.Errorf("peer stream closed before answer: %w", result.err)
		}
		return result.chunk, result.err
	}
}
