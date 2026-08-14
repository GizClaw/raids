package openai

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/peerhttp"
	"github.com/GizClaw/gizclaw-go/pkgs/giznet"
)

func TestLoginPeerUsesTemporaryPeerIdentity(t *testing.T) {
	serverKeys, err := giznet.GenerateKeyPair()
	if err != nil {
		t.Fatal(err)
	}
	peerKeys, err := giznet.GenerateKeyPair()
	if err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/login" || r.Method != http.MethodPost {
			t.Errorf("request=%s %s", r.Method, r.URL.Path)
		}
		if r.Header.Get(publicKeyHeader) != peerKeys.Public.String() || r.Header.Get(registrationTokenHeader) != "registration-token" || !strings.HasPrefix(r.Header.Get("Authorization"), "Bearer ") {
			t.Errorf("missing Peer login headers")
		}
		assertion := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
		if !validTestAssertion(assertion, serverKeys, peerKeys.Public) {
			t.Errorf("invalid Peer login assertion")
		}
		_ = json.NewEncoder(w).Encode(peerhttp.LoginResult{AccessToken: "session-token", TokenType: peerhttp.Bearer, ExpiresAt: 1})
	}))
	defer server.Close()
	token, err := LoginPeer(context.Background(), server.URL+"/openai/v1", peerKeys, serverKeys.Public, "registration-token")
	if err != nil || string(token) != "session-token" {
		t.Fatalf("token=%q err=%v", token, err)
	}
}

func validTestAssertion(assertion string, serverKeys *giznet.KeyPair, peerPublicKey giznet.PublicKey) bool {
	parts := strings.Split(assertion, ".")
	if len(parts) != 3 {
		return false
	}
	shared, err := serverKeys.DH(peerPublicKey)
	if err != nil {
		return false
	}
	mac := hmac.New(sha256.New, shared[:])
	_, _ = mac.Write([]byte(parts[0] + "." + parts[1]))
	signature, err := base64.RawURLEncoding.DecodeString(parts[2])
	return err == nil && hmac.Equal(signature, mac.Sum(nil))
}

func TestLoginPeerRedactsAssertionFromHTTPError(t *testing.T) {
	serverKeys, _ := giznet.GenerateKeyPair()
	peerKeys, _ := giznet.GenerateKeyPair()
	var assertion string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assertion = strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
		http.Error(w, assertion, http.StatusUnauthorized)
	}))
	defer server.Close()
	_, err := LoginPeer(context.Background(), server.URL+"/openai/v1", peerKeys, serverKeys.Public, "registration-token")
	if err == nil || assertion == "" || strings.Contains(err.Error(), assertion) {
		t.Fatalf("assertion leaked or error missing: %v", err)
	}
}

func TestLoginPeerRequiresRegistrationToken(t *testing.T) {
	serverKeys, _ := giznet.GenerateKeyPair()
	peerKeys, _ := giznet.GenerateKeyPair()
	_, err := LoginPeer(context.Background(), "https://example.invalid/openai/v1", peerKeys, serverKeys.Public, "")
	if err == nil {
		t.Fatal("missing registration token was accepted")
	}
}
