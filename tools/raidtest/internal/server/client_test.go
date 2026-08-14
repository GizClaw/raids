package server

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/GizClaw/gizclaw-go/pkgs/giznet"
)

func TestFetchInfoSeparatesAuthoritativeAndTransportIdentity(t *testing.T) {
	a, _ := giznet.GenerateKeyPair()
	b, _ := giznet.GenerateKeyPair()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(map[string]any{"public_key": a.Public.String(), "protocol": "gizclaw-webrtc", "transport": map[string]any{"mode": "edge-gateway", "endpoint": strings.TrimPrefix(serverURL(r), "http://"), "public_key": b.Public.String(), "signaling_path": "/signal"}})
	}))
	defer server.Close()
	info, err := FetchInfo(context.Background(), strings.TrimPrefix(server.URL, "http://"), server.Client())
	if err != nil {
		t.Fatal(err)
	}
	if !info.AuthoritativePublicKey.Equal(a.Public) || !info.TransportPublicKey.Equal(b.Public) {
		t.Fatal("server identities were not preserved")
	}
}

func TestKeyPairFromTextRedactsInvalidInput(t *testing.T) {
	secret := "definitely-not-a-key"
	_, err := KeyPairFromText([]byte(secret))
	if err == nil || strings.Contains(err.Error(), secret) {
		t.Fatalf("error must be redacted: %v", err)
	}
}

func TestKeyPairFromTextAcceptsRawIdentityFile(t *testing.T) {
	raw := make([]byte, giznet.KeySize)
	for index := range raw {
		raw[index] = byte(index + 1)
	}
	pair, err := KeyPairFromText(raw)
	if err != nil {
		t.Fatal(err)
	}
	if pair == nil || pair.Public.IsZero() {
		t.Fatalf("pair=%#v", pair)
	}
}

func serverURL(r *http.Request) string { return "http://" + r.Host }
