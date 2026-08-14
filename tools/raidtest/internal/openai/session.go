package openai

import (
	"context"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/peerhttp"
	"github.com/GizClaw/gizclaw-go/pkgs/giznet"
)

const maxLoginResponseBytes = 1 << 20

const publicKeyHeader = "X-Public-Key"

const registrationTokenHeader = "X-Registration-Token"

type loginAssertionHeader struct {
	Algorithm string `json:"alg"`
	Type      string `json:"typ"`
}

type loginAssertionClaims struct {
	Issuer    string `json:"iss"`
	Audience  string `json:"aud"`
	IssuedAt  int64  `json:"iat"`
	ExpiresAt int64  `json:"exp"`
	Nonce     string `json:"nonce"`
}

// LoginPeer exchanges the already-registered temporary Peer identity for the
// short-lived session required by the cluster OpenAI-compatible HTTP surface.
func LoginPeer(ctx context.Context, openAIBaseURL string, peerKeys *giznet.KeyPair, serverPublicKey giznet.PublicKey, registrationToken string) ([]byte, error) {
	if strings.TrimSpace(registrationToken) == "" {
		return nil, errors.New("temporary Peer login requires the candidate registration token")
	}
	base, err := url.Parse(openAIBaseURL)
	if err != nil {
		return nil, fmt.Errorf("parse cluster OpenAI base URL: %w", err)
	}
	base.Path, base.RawPath, base.RawQuery, base.Fragment = "/login", "", "", ""
	assertion, err := newLoginAssertion(peerKeys, serverPublicKey, time.Now())
	if err != nil {
		return nil, fmt.Errorf("create temporary Peer login assertion: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, base.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("create temporary Peer login request: %w", err)
	}
	req.Header.Set(publicKeyHeader, peerKeys.Public.String())
	req.Header.Set(registrationTokenHeader, registrationToken)
	req.Header.Set("Authorization", "Bearer "+assertion)
	client := &http.Client{
		Timeout: 30 * time.Second,
		CheckRedirect: func(*http.Request, []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("login temporary Peer for cluster OpenAI: %w", err)
	}
	defer resp.Body.Close()
	limited := io.LimitReader(resp.Body, maxLoginResponseBytes+1)
	data, err := io.ReadAll(limited)
	if err != nil {
		return nil, fmt.Errorf("read temporary Peer login response: %w", err)
	}
	if len(data) > maxLoginResponseBytes {
		return nil, fmt.Errorf("temporary Peer login response exceeds %d bytes", maxLoginResponseBytes)
	}
	if resp.StatusCode != http.StatusOK {
		detail := strings.ReplaceAll(strings.TrimSpace(string(data)), assertion, "[REDACTED]")
		if len(detail) > 500 {
			detail = detail[:500]
		}
		return nil, fmt.Errorf("temporary Peer login HTTP %d: %s", resp.StatusCode, detail)
	}
	var result peerhttp.LoginResult
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("decode temporary Peer login response: %w", err)
	}
	if strings.TrimSpace(result.AccessToken) == "" {
		return nil, errors.New("temporary Peer login returned an empty access token")
	}
	return []byte(result.AccessToken), nil
}

// newLoginAssertion implements the GizClaw v0.2.5 public-login wire contract
// without importing the server implementation and its storage dependencies.
func newLoginAssertion(peerKeys *giznet.KeyPair, serverPublicKey giznet.PublicKey, now time.Time) (string, error) {
	if peerKeys == nil {
		return "", errors.New("temporary Peer login requires a key pair")
	}
	nonceBytes := make([]byte, 16)
	if _, err := io.ReadFull(rand.Reader, nonceBytes); err != nil {
		return "", fmt.Errorf("create temporary Peer login nonce: %w", err)
	}
	header, err := json.Marshal(loginAssertionHeader{Algorithm: "X25519-HS256", Type: "JWT"})
	if err != nil {
		return "", err
	}
	claims, err := json.Marshal(loginAssertionClaims{
		Issuer: peerKeys.Public.String(), Audience: serverPublicKey.String(),
		IssuedAt: now.Unix(), ExpiresAt: now.Add(time.Minute).Unix(),
		Nonce: base64.RawURLEncoding.EncodeToString(nonceBytes),
	})
	if err != nil {
		return "", err
	}
	shared, err := peerKeys.DH(serverPublicKey)
	if err != nil {
		return "", fmt.Errorf("derive temporary Peer login secret: %w", err)
	}
	signed := base64.RawURLEncoding.EncodeToString(header) + "." + base64.RawURLEncoding.EncodeToString(claims)
	mac := hmac.New(sha256.New, shared[:])
	_, _ = mac.Write([]byte(signed))
	return signed + "." + base64.RawURLEncoding.EncodeToString(mac.Sum(nil)), nil
}
