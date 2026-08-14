package openai

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

type Client struct {
	BaseURL, APIKey string
	HTTPClient      *http.Client
}

const maxResponseBytes = 4 << 20

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

func (c Client) Models(ctx context.Context) ([]string, error) {
	var response struct {
		Data []struct {
			ID string `json:"id"`
		} `json:"data"`
	}
	if err := c.do(ctx, http.MethodGet, "/models", nil, &response); err != nil {
		return nil, err
	}
	models := make([]string, 0, len(response.Data))
	for _, item := range response.Data {
		if item.ID != "" {
			models = append(models, item.ID)
		}
	}
	if len(models) == 0 {
		return nil, errors.New("OpenAI-compatible endpoint returned no models")
	}
	return models, nil
}

func (c Client) Voices(ctx context.Context) ([]string, error) {
	var response struct {
		Data []struct {
			ID string `json:"id"`
		} `json:"data"`
	}
	if err := c.do(ctx, http.MethodGet, "/voices", nil, &response); err != nil {
		return nil, err
	}
	voices := make([]string, 0, len(response.Data))
	for _, item := range response.Data {
		if id := strings.TrimSpace(item.ID); id != "" {
			voices = append(voices, id)
		}
	}
	if len(voices) == 0 {
		return nil, errors.New("OpenAI-compatible endpoint returned no voices")
	}
	return voices, nil
}

func (c Client) Chat(ctx context.Context, model string, messages []Message) (string, error) {
	if strings.TrimSpace(model) == "" {
		return "", errors.New("model is required")
	}
	body := map[string]any{"model": model, "messages": messages}
	var response struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}
	if err := c.do(ctx, http.MethodPost, "/chat/completions", body, &response); err != nil {
		return "", err
	}
	if len(response.Choices) == 0 || strings.TrimSpace(response.Choices[0].Message.Content) == "" {
		return "", errors.New("OpenAI-compatible endpoint returned an empty completion")
	}
	return strings.TrimSpace(response.Choices[0].Message.Content), nil
}

func (c Client) Speech(ctx context.Context, model, voice, input string) ([]byte, error) {
	if strings.TrimSpace(model) == "" || strings.TrimSpace(voice) == "" || strings.TrimSpace(input) == "" {
		return nil, errors.New("speech model, voice, and input are required")
	}
	body := map[string]any{"model": model, "voice": voice, "input": input, "response_format": "opus"}
	data, err := c.doBytes(ctx, http.MethodPost, "/audio/speech", body)
	if err != nil {
		return nil, err
	}
	if len(data) == 0 {
		return nil, errors.New("OpenAI-compatible speech returned empty Opus audio")
	}
	return data, nil
}

func (c Client) do(ctx context.Context, method, path string, body, output any) error {
	data, err := c.doBytes(ctx, method, path, body)
	if err != nil {
		return err
	}
	if err := json.Unmarshal(data, output); err != nil {
		return fmt.Errorf("decode OpenAI-compatible response: %w", err)
	}
	return nil
}

func (c Client) doBytes(ctx context.Context, method, path string, body any) ([]byte, error) {
	var reader io.Reader
	if body != nil {
		encoded, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reader = bytes.NewReader(encoded)
	}
	req, err := http.NewRequestWithContext(ctx, method, strings.TrimRight(c.BaseURL, "/")+path, reader)
	if err != nil {
		return nil, err
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	req.Header.Set("Authorization", "Bearer "+c.APIKey)
	client := c.HTTPClient
	if client == nil {
		client = &http.Client{Timeout: 60 * time.Second}
	}
	safeClient := *client
	safeClient.CheckRedirect = func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }
	resp, err := safeClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("OpenAI-compatible request: %w", err)
	}
	defer resp.Body.Close()
	limited := io.LimitReader(resp.Body, maxResponseBytes+1)
	data, err := io.ReadAll(limited)
	if err != nil {
		return nil, err
	}
	if len(data) > maxResponseBytes {
		return nil, fmt.Errorf("OpenAI-compatible response exceeds %d bytes", maxResponseBytes)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		detail := strings.ReplaceAll(strings.TrimSpace(string(data)), c.APIKey, "[REDACTED]")
		if len(detail) > 500 {
			detail = detail[:500]
		}
		return nil, fmt.Errorf("OpenAI-compatible HTTP %d: %s", resp.StatusCode, detail)
	}
	return data, nil
}
