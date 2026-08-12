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

type Message struct{ Role, Content string }

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

func (c Client) Chat(ctx context.Context, model string, messages []Message) (string, error) {
	if strings.TrimSpace(model) == "" {
		return "", errors.New("model is required")
	}
	body := map[string]any{"model": model, "messages": messages, "temperature": 0.2}
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

func (c Client) do(ctx context.Context, method, path string, body, output any) error {
	var reader io.Reader
	if body != nil {
		encoded, err := json.Marshal(body)
		if err != nil {
			return err
		}
		reader = bytes.NewReader(encoded)
	}
	req, err := http.NewRequestWithContext(ctx, method, strings.TrimRight(c.BaseURL, "/")+path, reader)
	if err != nil {
		return err
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
		return fmt.Errorf("OpenAI-compatible request: %w", err)
	}
	defer resp.Body.Close()
	limited := io.LimitReader(resp.Body, 4<<20)
	data, err := io.ReadAll(limited)
	if err != nil {
		return err
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		detail := strings.ReplaceAll(strings.TrimSpace(string(data)), c.APIKey, "[REDACTED]")
		if len(detail) > 500 {
			detail = detail[:500]
		}
		return fmt.Errorf("OpenAI-compatible HTTP %d: %s", resp.StatusCode, detail)
	}
	if err := json.Unmarshal(data, output); err != nil {
		return fmt.Errorf("decode OpenAI-compatible response: %w", err)
	}
	return nil
}
