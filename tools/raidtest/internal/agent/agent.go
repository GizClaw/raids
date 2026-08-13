package agent

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/GizClaw/raids/tools/raidtest/internal/conversation"
	"github.com/GizClaw/raids/tools/raidtest/internal/openai"
	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
	"github.com/GizClaw/raids/tools/raidtest/internal/report"
)

type Agent struct {
	Client openai.Client
	Model  string
}

func (a Agent) Generate(ctx context.Context, persona string, turn plan.Turn) (string, error) {
	prompt := fmt.Sprintf("Persona:\n%s\n\nImmutable test intent:\n%s\n\nWrite exactly one natural user utterance. Do not answer it, add facts, weaken constraints, or mention testing. Output only the utterance.", persona, turn.Intent)
	text, err := a.Client.Chat(ctx, a.Model, []openai.Message{{Role: "system", Content: "You simulate a human user while preserving the supplied test contract exactly."}, {Role: "user", Content: prompt}})
	if err != nil {
		return "", err
	}
	text = strings.TrimSpace(text)
	if text == "" || len([]rune(text)) > 300 || strings.Contains(text, "\n") {
		return "", errors.New("generated utterance violates the bounded one-line contract")
	}
	return text, nil
}

func (a Agent) Judge(ctx context.Context, persona string, turn plan.Turn, response conversation.Response) ([]report.Check, error) {
	prompt := fmt.Sprintf("Persona: %s\nUser intent: %s\nUser utterance: %s\nAssistant response: %s\nDimensions: %s\nReturn JSON only: {\"checks\":[{\"name\":\"dimension\",\"pass\":true,\"detail\":\"brief reason\"}]}. Do not judge character counts, literal facts, scripts, latency, or cleanup.", persona, turn.Intent, turn.User, response.Text, strings.Join(turn.Judge, ", "))
	var last error
	for attempt := 0; attempt < 2; attempt++ {
		text, err := a.Client.Chat(ctx, a.Model, []openai.Message{{Role: "system", Content: "You are a strict semantic conversation evaluator. Return valid JSON only."}, {Role: "user", Content: prompt}})
		if err != nil {
			return nil, err
		}
		var decoded struct {
			Checks []struct {
				Name   string `json:"name"`
				Pass   bool   `json:"pass"`
				Detail string `json:"detail"`
			} `json:"checks"`
		}
		if err := json.Unmarshal([]byte(text), &decoded); err != nil {
			last = err
			continue
		}
		byName := make(map[string]report.Check, len(decoded.Checks))
		for _, item := range decoded.Checks {
			name := strings.TrimSpace(item.Name)
			if name == "" {
				last = errors.New("judge returned an empty dimension")
				continue
			}
			status := "fail"
			if item.Pass {
				status = "pass"
			}
			if _, duplicate := byName[name]; duplicate {
				last = fmt.Errorf("judge returned duplicate dimension %q", name)
				continue
			}
			byName[name] = report.Check{Name: "judge:" + name, Status: status, Detail: item.Detail}
		}
		checks := make([]report.Check, 0, len(turn.Judge))
		valid := len(byName) == len(turn.Judge)
		for _, name := range turn.Judge {
			check, ok := byName[name]
			if !ok {
				last = fmt.Errorf("judge omitted requested dimension %q", name)
				valid = false
				continue
			}
			checks = append(checks, check)
		}
		if !valid {
			continue
		}
		return checks, nil
	}
	return nil, fmt.Errorf("decode judge result after retry: %w", last)
}
