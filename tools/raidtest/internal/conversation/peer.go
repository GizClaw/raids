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
			if workspaceName != "" && state.WorkspaceName != workspaceName {
				lastMismatch = fmt.Sprintf("running Workspace %q, want %q", state.WorkspaceName, workspaceName)
			} else if workflowID != "" && (state.WorkflowName == nil || *state.WorkflowName != workflowID) {
				actual := ""
				if state.WorkflowName != nil {
					actual = *state.WorkflowName
				}
				lastMismatch = fmt.Sprintf("running Workflow %q, want shadow Workflow %q", actual, workflowID)
			} else {
				return nil
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
	for _, chunk := range []*genx.MessageChunk{
		{Role: genx.RoleUser, Ctrl: &genx.StreamCtrl{StreamID: streamID, Label: label, BeginOfStream: true}},
		{Role: genx.RoleUser, Part: genx.Text(text), Ctrl: &genx.StreamCtrl{StreamID: streamID, Label: label}},
		{Role: genx.RoleUser, Part: genx.Text(""), Ctrl: &genx.StreamCtrl{StreamID: streamID, Label: label, EndOfStream: true}},
	} {
		if err := stream.Push(turnCtx, chunk); err != nil {
			return Response{}, err
		}
	}
	started := time.Now()
	capture := responseCapture{audioMIMEs: map[string]bool{}, expectAudio: p.RequireAudio}
	for {
		chunk, err := nextWithContext(turnCtx, stream)
		if err != nil {
			return capture.response(started), err
		}
		if chunk != nil && chunk.Ctrl != nil && chunk.Ctrl.Error != "" {
			code := strings.TrimSpace(chunk.Ctrl.ErrorCode)
			if code != "" {
				return capture.response(started), fmt.Errorf("target stream error %s: %s", code, chunk.Ctrl.Error)
			}
			return capture.response(started), fmt.Errorf("target stream error: %s", chunk.Ctrl.Error)
		}
		capture.observe(chunk, time.Since(started))
		if capture.textDone && (!p.RequireAudio || capture.audioDone) {
			result := capture.response(started)
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

type responseCapture struct {
	answer      strings.Builder
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
	assistant := chunk.Role == genx.RoleModel || strings.EqualFold(chunk.Name, "assistant") || (chunk.Ctrl != nil && strings.EqualFold(chunk.Ctrl.Label, "assistant"))
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
