package conversation

import (
	"testing"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/rpcapi"
)

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

func TestStreamErrorEvidenceDistinguishesResponsePhase(t *testing.T) {
	before := responseWithStreamError(Response{}, nil)
	after := responseWithStreamError(Response{Text: "answer"}, nil)
	if before.Evidence["stream_status"] != "incomplete_before_text" || after.Evidence["stream_status"] != "incomplete_after_text" {
		t.Fatalf("before=%#v after=%#v", before, after)
	}
}
