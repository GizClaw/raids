package server

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/GizClaw/gizclaw-go/pkgs/gizclaw/api/apitypes"
	"github.com/GizClaw/gizclaw-go/pkgs/giznet"
	"github.com/GizClaw/gizclaw-go/pkgs/giznet/gizwebrtc"
	"github.com/GizClaw/gizclaw-go/sdk/go/gizcli"
)

type Info struct {
	AuthoritativePublicKey giznet.PublicKey
	TransportPublicKey     giznet.PublicKey
	SignalingURL           string
	ICEServers             []gizwebrtc.ICEServer
	Version                string
}

func FetchInfo(ctx context.Context, endpoint string, client *http.Client) (Info, error) {
	endpoint = strings.TrimSpace(endpoint)
	if endpoint == "" || strings.Contains(endpoint, "://") {
		return Info{}, errors.New("server endpoint must be host:port without a URL scheme")
	}
	if client == nil {
		client = &http.Client{Timeout: 10 * time.Second}
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, "http://"+endpoint+"/server-info", nil)
	if err != nil {
		return Info{}, err
	}
	resp, err := client.Do(req)
	if err != nil {
		return Info{}, fmt.Errorf("fetch server-info: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return Info{}, fmt.Errorf("server-info status %s", resp.Status)
	}
	var body struct {
		PublicKey     string                `json:"public_key"`
		Protocol      string                `json:"protocol"`
		Version       string                `json:"version"`
		SignalingPath string                `json:"signaling_path"`
		ICEServers    []gizwebrtc.ICEServer `json:"ice_servers"`
		Transport     *struct {
			Mode          string `json:"mode"`
			Endpoint      string `json:"endpoint"`
			PublicKey     string `json:"public_key"`
			SignalingPath string `json:"signaling_path"`
		} `json:"transport"`
	}
	if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&body); err != nil {
		return Info{}, fmt.Errorf("decode server-info: %w", err)
	}
	if body.Protocol != "" && body.Protocol != "gizclaw-webrtc" {
		return Info{}, fmt.Errorf("unsupported server-info protocol %q", body.Protocol)
	}
	authoritative, err := parseKey(body.PublicKey)
	if err != nil {
		return Info{}, fmt.Errorf("authoritative public key: %w", err)
	}
	transport, signalingEndpoint, signalingPath, ice := authoritative, endpoint, strings.TrimSpace(body.SignalingPath), body.ICEServers
	if body.Transport != nil {
		if body.Transport.Mode != "edge-gateway" {
			return Info{}, fmt.Errorf("unsupported transport mode %q", body.Transport.Mode)
		}
		signalingEndpoint, err = normalizeEndpoint(body.Transport.Endpoint)
		if err != nil {
			return Info{}, fmt.Errorf("transport endpoint: %w", err)
		}
		transport, err = parseKey(body.Transport.PublicKey)
		if err != nil {
			return Info{}, fmt.Errorf("transport public key: %w", err)
		}
		if transport.Equal(authoritative) {
			return Info{}, errors.New("transport public key must differ from authoritative server key")
		}
		signalingPath, ice = strings.TrimSpace(body.Transport.SignalingPath), nil
	}
	if signalingPath == "" {
		signalingPath = gizwebrtc.SignalingPath
	}
	if !strings.HasPrefix(signalingPath, "/") || strings.HasPrefix(signalingPath, "//") {
		return Info{}, fmt.Errorf("invalid signaling path %q", signalingPath)
	}
	signalingURL := url.URL{Scheme: "http", Host: signalingEndpoint, Path: signalingPath}
	return Info{AuthoritativePublicKey: authoritative, TransportPublicKey: transport, SignalingURL: signalingURL.String(), ICEServers: ice, Version: strings.TrimSpace(body.Version)}, nil
}

type Connection struct {
	Client *gizcli.Client
	done   <-chan error
}

func (c *Connection) Close() error {
	if c == nil || c.Client == nil {
		return nil
	}
	err := c.Client.Close()
	select {
	case <-c.done:
	case <-time.After(2 * time.Second):
	}
	return err
}

func Dial(ctx context.Context, endpoint string, keyPair *giznet.KeyPair, name string, httpClient *http.Client) (*Connection, Info, error) {
	if keyPair == nil {
		return nil, Info{}, errors.New("key pair is required")
	}
	info, err := FetchInfo(ctx, endpoint, httpClient)
	if err != nil {
		return nil, Info{}, err
	}
	client := &gizcli.Client{
		KeyPair: keyPair,
		Device:  apitypes.DeviceInfo{Name: &name},
		DialTransport: func(key *giznet.KeyPair, _ giznet.PublicKey, _ string, policy giznet.SecurityPolicy) (giznet.Listener, giznet.Conn, error) {
			dialCtx, cancel := context.WithTimeout(ctx, 20*time.Second)
			defer cancel()
			return gizwebrtc.Dial(dialCtx, key, info.TransportPublicKey, gizwebrtc.DialConfig{SignalingURL: info.SignalingURL, ICEServers: info.ICEServers, SecurityPolicy: policy, HTTPClient: httpClient})
		},
	}
	if err := client.Dial(info.AuthoritativePublicKey, endpoint); err != nil {
		return nil, Info{}, fmt.Errorf("dial server: %w", err)
	}
	done := make(chan error, 1)
	go func() { done <- client.Serve() }()
	return &Connection{Client: client, done: done}, info, nil
}

func KeyPairFromText(text []byte) (*giznet.KeyPair, error) {
	var private giznet.Key
	if len(text) == giznet.KeySize {
		copy(private[:], text)
	} else if err := private.UnmarshalText([]byte(strings.TrimSpace(string(text)))); err != nil {
		return nil, errors.New("invalid admin private key")
	}
	return giznet.NewKeyPair(private)
}

func parseKey(text string) (giznet.PublicKey, error) {
	var key giznet.PublicKey
	if strings.TrimSpace(text) == "" {
		return key, errors.New("public key is required")
	}
	if err := key.UnmarshalText([]byte(strings.TrimSpace(text))); err != nil {
		return key, err
	}
	if key.IsZero() {
		return key, errors.New("public key is zero")
	}
	return key, nil
}

func normalizeEndpoint(value string) (string, error) {
	value = strings.TrimSpace(value)
	if value == "" || strings.Contains(value, "://") {
		return "", errors.New("endpoint must be host:port")
	}
	parsed, err := url.Parse("http://" + value)
	if err != nil || parsed.Host == "" || parsed.Hostname() == "" || parsed.User != nil || parsed.Path != "" || parsed.RawQuery != "" || parsed.Fragment != "" {
		return "", errors.New("endpoint must be host:port")
	}
	port, err := strconv.Atoi(parsed.Port())
	if err != nil || port < 1 || port > 65535 {
		return "", errors.New("endpoint must include a valid port")
	}
	return parsed.Host, nil
}
