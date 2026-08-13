package main

import (
	"bytes"
	"testing"

	"github.com/GizClaw/gizclaw-go/pkgs/audio/codec/ogg"
	"github.com/GizClaw/raids/tools/raidtest/internal/provision"
)

func TestOpusFramesDropsOggHeaders(t *testing.T) {
	var pages []*ogg.Page
	sequence := uint32(0)
	for index, packet := range [][]byte{[]byte("OpusHead"), []byte("OpusTags"), {1, 2, 3}} {
		built, err := ogg.BuildPacketPages(7, sequence, packet, uint64(index*960), index == 0, index == 2)
		if err != nil {
			t.Fatal(err)
		}
		pages = append(pages, built...)
		sequence += uint32(len(built))
	}
	encoded, err := ogg.MarshalPages(pages)
	if err != nil {
		t.Fatal(err)
	}
	frames, err := opusFrames(encoded)
	if err != nil || len(frames) != 1 || !bytes.Equal(frames[0], []byte{1, 2, 3}) {
		t.Fatalf("frames=%#v err=%v", frames, err)
	}
}

func TestParseFlagsAcceptsOnlySecretSources(t *testing.T) {
	t.Setenv("RAIDTEST_ADMIN", "private")
	var stderr bytes.Buffer
	cfg, err := parseFlags([]string{
		"--server", "admin.example:9820",
		"--peer-server", "edge.example:9821",
		"--workflow", "workflow.yaml",
		"--plan", "plan.yaml",
		"--admin-private-key-env", "RAIDTEST_ADMIN",
	}, &stderr)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.AdminKey.Env != "RAIDTEST_ADMIN" || cfg.PeerServer != "edge.example:9821" || cfg.OpenAIBaseURL != "http://admin.example:9820/openai/v1" {
		t.Fatalf("config=%#v", cfg.Redacted())
	}
	stderr.Reset()
	if _, err := parseFlags([]string{"--admin-private-key", "raw-secret"}, &stderr); err == nil {
		t.Fatal("raw private-key argv flag was accepted")
	}
}

func TestDriverMatchesPublicWorkflowFamilies(t *testing.T) {
	for workflow, planned := range map[string]string{
		"flowcraft":       "flowcraft",
		"doubao-realtime": "realtime",
		"ast-translate":   "translate",
		"pet":             "pet",
	} {
		if !driverMatches(workflow, planned) {
			t.Fatalf("driver %q did not match %q", workflow, planned)
		}
	}
	if driverMatches("flowcraft", "translate") {
		t.Fatal("mismatched driver was accepted")
	}
}

func TestRegistrationMismatchStillRecordsPeerForCleanup(t *testing.T) {
	lifecycle := provision.New(nil, false)
	err := recordPeerAndValidateProfile(lifecycle, "peer-public-key", "wrong-profile", "shadow-profile")
	if err == nil {
		t.Fatal("mismatched RuntimeProfile was accepted")
	}
	if len(lifecycle.Ledger) != 1 || lifecycle.Ledger[0].ResourceType != "Peer" || lifecycle.Ledger[0].ID != "peer-public-key" {
		t.Fatalf("peer was not recorded before validation: %#v", lifecycle.Ledger)
	}
}
