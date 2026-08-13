package server

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
	"time"

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

func TestLoginReturnsRegisteredPeerAccessToken(t *testing.T) {
	serverKeys, _ := giznet.GenerateKeyPair()
	peerKeys, _ := giznet.GenerateKeyPair()
	httpServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/login" {
			http.Error(w, "unexpected request", http.StatusNotFound)
			return
		}
		if r.Header.Get("X-Public-Key") != peerKeys.Public.String() {
			http.Error(w, "missing login proof", http.StatusUnauthorized)
			return
		}
		assertValidLoginProof(t, strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer "), serverKeys, peerKeys)
		_ = json.NewEncoder(w).Encode(map[string]any{"access_token": "peer-session", "token_type": "Bearer", "expires_at": time.Now().Add(time.Hour).UnixMilli()})
	}))
	defer httpServer.Close()

	token, err := Login(t.Context(), strings.TrimPrefix(httpServer.URL, "http://"), peerKeys, serverKeys.Public, httpServer.Client())
	if err != nil || string(token) != "peer-session" {
		t.Fatalf("Login() = %q, %v", token, err)
	}
}

func assertValidLoginProof(t *testing.T, token string, serverKeys, peerKeys *giznet.KeyPair) {
	t.Helper()
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		t.Fatalf("assertion has %d parts", len(parts))
	}
	decode := func(part string, target any) {
		data, err := base64.RawURLEncoding.DecodeString(part)
		if err != nil {
			t.Fatal(err)
		}
		if err := json.Unmarshal(data, target); err != nil {
			t.Fatal(err)
		}
	}
	var header loginAssertionHeader
	var claims loginAssertionClaims
	decode(parts[0], &header)
	decode(parts[1], &claims)
	if header.Alg != "X25519-HS256" || header.Typ != "JWT" {
		t.Fatalf("assertion header = %#v", header)
	}
	now := time.Now().Unix()
	if claims.Iss != peerKeys.Public.String() || claims.Aud != serverKeys.Public.String() || claims.Nonce == "" || claims.Iat > now || claims.Exp <= now || claims.Exp-claims.Iat > 60 {
		t.Fatalf("assertion claims = %#v", claims)
	}
	signature, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil {
		t.Fatal(err)
	}
	shared, err := serverKeys.DH(peerKeys.Public)
	if err != nil {
		t.Fatal(err)
	}
	mac := hmac.New(sha256.New, shared[:])
	_, _ = mac.Write([]byte(parts[0] + "." + parts[1]))
	if !hmac.Equal(signature, mac.Sum(nil)) {
		t.Fatal("assertion HMAC mismatch")
	}
}

func serverURL(r *http.Request) string { return "http://" + r.Host }
