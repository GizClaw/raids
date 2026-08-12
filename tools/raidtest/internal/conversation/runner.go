package conversation

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"
	"unicode"

	"github.com/GizClaw/raids/tools/raidtest/internal/plan"
	"github.com/GizClaw/raids/tools/raidtest/internal/report"
)

type Response struct {
	Text          string
	FirstResponse time.Duration
	TotalResponse time.Duration
	Evidence      map[string]string
}

type Target interface {
	Send(context.Context, string, string) (Response, error)
	Reload(context.Context) error
}

type UtteranceAgent interface {
	Generate(context.Context, string, plan.Turn) (string, error)
}
type Judge interface {
	Judge(context.Context, string, plan.Turn, Response) ([]report.Check, error)
}

type Runner struct {
	Target Target
	Agent  UtteranceAgent
	Judge  Judge
}

func (r Runner) Run(ctx context.Context, p plan.Plan) []report.Case {
	results := make([]report.Case, 0, len(p.Cases))
	for _, plannedCase := range p.Cases {
		result := report.Case{ID: plannedCase.ID, Status: "pass"}
		for _, turn := range plannedCase.Turns {
			turnResult := report.Turn{ID: turn.ID, User: turn.User, Status: "pass"}
			if turnResult.User == "" && r.Agent != nil {
				generated, err := r.Agent.Generate(ctx, p.Persona, turn)
				if err != nil {
					turnResult.Status, turnResult.Error = "fail", fmt.Sprintf("generate utterance: %v", err)
					result.Turns = append(result.Turns, turnResult)
					result.Status = "fail"
					continue
				}
				turnResult.User = generated
			}
			turn.User = turnResult.User
			if turn.ReloadBefore {
				if err := r.Target.Reload(ctx); err != nil {
					turnResult.Status, turnResult.Error = "fail", fmt.Sprintf("reload: %v", err)
					result.Turns = append(result.Turns, turnResult)
					result.Status = "fail"
					continue
				}
			}
			response, err := r.Target.Send(ctx, plannedCase.ID+"-"+turn.ID, turnResult.User)
			turnResult.Assistant, turnResult.FirstResponse, turnResult.TotalResponse, turnResult.Evidence = response.Text, response.FirstResponse, response.TotalResponse, response.Evidence
			if p.Driver == "translate" {
				if turnResult.Evidence == nil {
					turnResult.Evidence = map[string]string{}
				}
				turnResult.Evidence["source_text"] = turnResult.User
				turnResult.Evidence["translated_text"] = response.Text
				if _, ok := turnResult.Evidence["tts_status"]; !ok {
					turnResult.Evidence["tts_status"] = "not_requested"
				}
				turnResult.Evidence["transcription_status"] = "not_requested"
			}
			turnResult.RuneCount = len([]rune(response.Text))
			if err != nil {
				turnResult.Status, turnResult.Error = "fail", err.Error()
			} else {
				turnResult.Checks = DeterministicChecks(turn, response)
				if hasFailure(turnResult.Checks) {
					turnResult.Status = "fail"
				}
				if r.Judge != nil && len(turn.Judge) > 0 {
					checks, judgeErr := r.Judge.Judge(ctx, p.Persona, turn, response)
					turnResult.Checks = append(turnResult.Checks, checks...)
					if judgeErr != nil {
						turnResult.Status, turnResult.Error = "fail", fmt.Sprintf("judge: %v", judgeErr)
					} else if hasFailure(checks) {
						turnResult.Status = "fail"
					}
				}
			}
			if turnResult.Status != "pass" {
				result.Status = "fail"
			}
			result.Turns = append(result.Turns, turnResult)
		}
		results = append(results, result)
	}
	return results
}

func DeterministicChecks(turn plan.Turn, response Response) []report.Check {
	var checks []report.Check
	for _, fact := range turn.Required {
		checks = append(checks, containsCheck("required:"+fact, response.Text, fact, true))
	}
	for _, alternatives := range turn.RequiredAny {
		found := false
		for _, fact := range alternatives {
			if strings.Contains(strings.ToLower(response.Text), strings.ToLower(fact)) {
				found = true
				break
			}
		}
		status := "fail"
		if found {
			status = "pass"
		}
		checks = append(checks, report.Check{Name: "required_any:" + strings.Join(alternatives, "|"), Status: status, Detail: fmt.Sprintf("found=%t", found)})
	}
	for _, fact := range turn.Forbidden {
		checks = append(checks, containsCheck("forbidden:"+fact, response.Text, fact, false))
	}
	if turn.MaxRunes > 0 {
		count := len([]rune(response.Text))
		status := "pass"
		if count > turn.MaxRunes {
			status = "fail"
		}
		checks = append(checks, report.Check{Name: "max_runes", Status: status, Detail: fmt.Sprintf("got=%d max=%d", count, turn.MaxRunes)})
	}
	if turn.FirstResponse > 0 {
		checks = append(checks, durationCheck("first_response", response.FirstResponse, turn.FirstResponse))
	}
	if turn.TotalResponse > 0 {
		checks = append(checks, durationCheck("total_response", response.TotalResponse, turn.TotalResponse))
	}
	for _, script := range turn.Scripts {
		checks = append(checks, scriptCheck(response.Text, script))
	}
	if turn.RequirePunctuation {
		found := false
		for _, value := range response.Text {
			if unicode.IsPunct(value) {
				found = true
				break
			}
		}
		status := "fail"
		if found {
			status = "pass"
		}
		checks = append(checks, report.Check{Name: "punctuation", Status: status, Detail: fmt.Sprintf("found=%t", found)})
	}
	return checks
}

func containsCheck(name, text, needle string, required bool) report.Check {
	found := strings.Contains(strings.ToLower(text), strings.ToLower(needle))
	pass := found == required
	status := "pass"
	if !pass {
		status = "fail"
	}
	return report.Check{Name: name, Status: status, Detail: fmt.Sprintf("found=%t", found)}
}
func durationCheck(name string, got, max time.Duration) report.Check {
	status := "pass"
	if got > max {
		status = "fail"
	}
	return report.Check{Name: name, Status: status, Detail: fmt.Sprintf("got=%s max=%s", got, max)}
}
func hasFailure(checks []report.Check) bool {
	for _, check := range checks {
		if check.Status != "pass" {
			return true
		}
	}
	return false
}

func scriptCheck(text, name string) report.Check {
	name = strings.ToLower(strings.TrimSpace(name))
	total, matching, requiredMarker := 0, 0, 0
	for _, r := range text {
		if !unicode.IsLetter(r) {
			continue
		}
		total++
		switch name {
		case "han":
			if unicode.In(r, unicode.Han) {
				matching++
			}
		case "latin":
			if unicode.In(r, unicode.Latin) {
				matching++
			}
		case "japanese":
			if unicode.In(r, unicode.Hiragana, unicode.Katakana, unicode.Han) {
				matching++
			}
			if unicode.In(r, unicode.Hiragana, unicode.Katakana) {
				requiredMarker++
			}
		case "korean":
			if unicode.In(r, unicode.Hangul) {
				matching++
				requiredMarker++
			}
		}
	}
	status := "pass"
	ratio := 0.0
	if total > 0 {
		ratio = float64(matching) / float64(total)
	}
	detail := fmt.Sprintf("matching=%d letters=%d ratio=%.2f", matching, total, ratio)
	threshold := 0.6
	if name == "latin" {
		threshold = 0.7
	}
	if total == 0 || ratio < threshold || ((name == "japanese" || name == "korean") && requiredMarker == 0) {
		status = "fail"
	}
	if name != "han" && name != "latin" && name != "japanese" && name != "korean" {
		status = "fail"
		detail = "unknown script"
	}
	return report.Check{Name: "script:" + name, Status: status, Detail: detail}
}

var ErrEmptyResponse = errors.New("target returned an empty response")
