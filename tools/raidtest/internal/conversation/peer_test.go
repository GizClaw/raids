package conversation

import (
	"testing"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/genx"
)

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
