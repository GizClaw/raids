package openai

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestModelsAndChat(t *testing.T) {
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer key" {
			t.Error("missing bearer key")
		}
		if r.URL.Path == "/v1/models" {
			_ = json.NewEncoder(w).Encode(map[string]any{"data": []map[string]string{{"id": "model-a"}}})
			return
		}
		var body struct {
			Temperature *float64 `json:"temperature"`
			Messages    []struct {
				Role    string `json:"role"`
				Content string `json:"content"`
			} `json:"messages"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Errorf("decode chat request: %v", err)
		}
		if len(body.Messages) != 1 || body.Messages[0].Role != "user" || body.Messages[0].Content != "hi" {
			t.Errorf("chat messages = %#v", body.Messages)
		}
		if body.Temperature != nil {
			t.Errorf("temperature must use the model default, got %v", *body.Temperature)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"choices": []any{map[string]any{"message": map[string]string{"content": "hello"}}}})
	}))
	defer s.Close()
	c := Client{BaseURL: s.URL + "/v1", APIKey: "key", HTTPClient: s.Client()}
	models, err := c.Models(context.Background())
	if err != nil || len(models) != 1 {
		t.Fatalf("models=%v err=%v", models, err)
	}
	text, err := c.Chat(context.Background(), models[0], []Message{{Role: "user", Content: "hi"}})
	if err != nil || text != "hello" {
		t.Fatalf("chat=%q err=%v", text, err)
	}
}

func TestSpeechRequestsOpus(t *testing.T) {
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/audio/speech" {
			t.Fatalf("path = %q", r.URL.Path)
		}
		var body map[string]any
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Fatal(err)
		}
		if body["model"] != "tts" || body["voice"] != "alloy" || body["input"] != "你好" || body["response_format"] != "opus" {
			t.Fatalf("body = %#v", body)
		}
		_, _ = w.Write([]byte{0, 0, 1, 0})
	}))
	defer s.Close()
	got, err := (Client{BaseURL: s.URL + "/v1", APIKey: "key", HTTPClient: s.Client()}).Speech(context.Background(), "tts", "alloy", "你好")
	if err != nil || len(got) != 4 {
		t.Fatalf("Speech() bytes=%d err=%v", len(got), err)
	}
}

func TestResponseSizeLimitIsExplicit(t *testing.T) {
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		_, _ = w.Write(make([]byte, maxResponseBytes+1))
	}))
	defer s.Close()
	_, err := (Client{BaseURL: s.URL, APIKey: "key", HTTPClient: s.Client()}).Speech(context.Background(), "tts", "alloy", "hello")
	if err == nil || !strings.Contains(err.Error(), "exceeds") {
		t.Fatalf("Speech() err=%v", err)
	}
}

func TestHTTPFailureRedactsCredential(t *testing.T) {
	secret := "top-secret"
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(500)
		_, _ = w.Write([]byte("failed " + secret))
	}))
	defer s.Close()
	_, err := (Client{BaseURL: s.URL, APIKey: secret, HTTPClient: s.Client()}).Models(context.Background())
	if err == nil || strings.Contains(err.Error(), secret) {
		t.Fatalf("credential leaked: %v", err)
	}
}

func TestClientDoesNotForwardCredentialThroughRedirect(t *testing.T) {
	reached := false
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/sink" {
			reached = true
		}
		http.Redirect(w, r, "/sink", http.StatusTemporaryRedirect)
	}))
	defer s.Close()
	_, err := (Client{BaseURL: s.URL, APIKey: "secret", HTTPClient: s.Client()}).Models(context.Background())
	if err == nil || reached {
		t.Fatalf("redirect followed=%t err=%v", reached, err)
	}
}
