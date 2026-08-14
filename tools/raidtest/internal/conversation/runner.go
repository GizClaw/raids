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

type RecallWaiter interface {
	WaitForRecall(context.Context, []string, time.Duration) error
}

type UtteranceAgent interface {
	Generate(context.Context, string, []report.Turn, plan.Turn) (string, error)
}
type Judge interface {
	Judge(context.Context, string, []report.Turn, plan.Turn, Response) ([]report.Check, error)
}

type Runner struct {
	Target Target
	Agent  UtteranceAgent
	Judge  Judge
}

func (r Runner) Run(ctx context.Context, p plan.Plan) []report.Case {
	results := make([]report.Case, 0, len(p.Cases))
	for caseIndex, plannedCase := range p.Cases {
		result := report.Case{ID: plannedCase.ID, Status: "pass"}
		for turnIndex, turn := range plannedCase.Turns {
			turnResult := report.Turn{ID: turn.ID, User: turn.User, Status: "pass"}
			if turnResult.User == "" && r.Agent != nil {
				history := append([]report.Turn(nil), result.Turns...)
				generated, err := r.Agent.Generate(ctx, p.Persona, history, turn)
				if err != nil {
					turnResult.Status, turnResult.Error = "fail", fmt.Sprintf("generate utterance: %v", err)
					result.Turns = append(result.Turns, turnResult)
					result.Status = "fail"
					continue
				}
				turnResult.User = generated
			}
			turn.User = turnResult.User
			// The command gives each Case its own Workspace. Reload remains useful to
			// direct Runner callers and closes pending realtime/translation audio, but
			// it must not be treated as clearing a persistent Workspace conversation.
			if len(turn.PersistedBeforeReload) > 0 {
				waiter, ok := r.Target.(RecallWaiter)
				if !ok {
					turnResult.Status, turnResult.Error = "fail", "persisted recall barrier is not supported by this target"
					result.Turns = append(result.Turns, turnResult)
					result.Status = "fail"
					continue
				}
				if err := waiter.WaitForRecall(ctx, turn.PersistedBeforeReload, turn.PersistenceTimeout); err != nil {
					turnResult.Status, turnResult.Error = "fail", fmt.Sprintf("wait for persisted recall before reload: %v", err)
					result.Turns = append(result.Turns, turnResult)
					result.Status = "fail"
					continue
				}
			}
			if turn.ReloadBefore || (caseIndex > 0 && turnIndex == 0) {
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
			if response.Text != "" {
				turnResult.Checks = DeterministicChecks(turn, response)
			}
			if err != nil {
				turnResult.Status, turnResult.Error = "fail", err.Error()
				// A timed-out graph may still be producing chunks after its Peer stream
				// closes. Restart the selected Workspace before the next independent
				// turn so a late response cannot be attributed to the following input.
				if reloadErr := r.Target.Reload(ctx); reloadErr != nil {
					turnResult.Error += fmt.Sprintf("; recover Workspace: %v", reloadErr)
				}
			} else {
				if hasFailure(turnResult.Checks) {
					turnResult.Status = "fail"
				}
				if r.Judge != nil && len(turn.Judge) > 0 {
					// Semantic continuity can only be evaluated against the turns that
					// actually happened in this case. Keep failed prior turns in the
					// transcript: their user facts and assistant contradictions remain
					// relevant evidence for every later answer.
					history := append([]report.Turn(nil), result.Turns...)
					checks, judgeErr := r.Judge.Judge(ctx, p.Persona, history, turn, response)
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
			if strings.Contains(normalizeLiteral(response.Text), normalizeLiteral(fact)) {
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
		found := forbiddenContains(response.Text, fact)
		status := "pass"
		if found {
			status = "fail"
		}
		checks = append(checks, report.Check{Name: "forbidden:" + fact, Status: status, Detail: fmt.Sprintf("found=%t", found)})
	}
	if turn.MinRunes > 0 {
		count := len([]rune(response.Text))
		status := "pass"
		if count < turn.MinRunes {
			status = "fail"
		}
		checks = append(checks, report.Check{Name: "min_runes", Status: status, Detail: fmt.Sprintf("got=%d min=%d", count, turn.MinRunes)})
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

func forbiddenContains(text, needle string) bool {
	trimmed := strings.TrimSpace(needle)
	if strings.HasSuffix(trimmed, ":") || strings.HasSuffix(trimmed, "：") {
		return strings.Contains(normalizeLiteral(text), normalizeLiteral(trimmed))
	}
	normalizedNeedle := normalizeForbiddenLiteral(needle)
	// Formatting sentinels can normalize to an empty or overly broad value.
	// Match them literally so arbitrary prose cannot make every response fail.
	if normalizedNeedle == "" || isFormattingSentinel(trimmed) {
		return strings.Contains(text, trimmed)
	}
	return strings.Contains(normalizeForbiddenLiteral(text), normalizedNeedle)
}

func isFormattingSentinel(value string) bool {
	if value == "```" || value == "###" || value == "-" {
		return true
	}
	if len(value) < 2 || value[len(value)-1] != '.' {
		return false
	}
	for _, r := range value[:len(value)-1] {
		if !unicode.IsDigit(r) {
			return false
		}
	}
	return true
}

func containsCheck(name, text, needle string, required bool) report.Check {
	found := strings.Contains(normalizeLiteral(text), normalizeLiteral(needle))
	pass := found == required
	status := "pass"
	if !pass {
		status = "fail"
	}
	return report.Check{Name: name, Status: status, Detail: fmt.Sprintf("found=%t", found)}
}

func normalizeLiteral(value string) string {
	return strings.Map(func(r rune) rune {
		if unicode.IsSpace(r) {
			return -1
		}
		if normalized, ok := equivalentDigit(r); ok {
			return normalized
		}
		return unicode.ToLower(r)
	}, value)
}

func normalizeForbiddenLiteral(value string) string {
	return strings.Map(func(r rune) rune {
		if unicode.IsSpace(r) || unicode.IsPunct(r) {
			return -1
		}
		if normalized, ok := equivalentDigit(r); ok {
			return normalized
		}
		return unicode.ToLower(r)
	}, value)
}

func equivalentDigit(r rune) (rune, bool) {
	const arabic = "0123456789"
	for _, digits := range []string{"０１２３４５６７８９", "零一二三四五六七八九"} {
		index := 0
		for _, candidate := range digits {
			if r == candidate {
				return rune(arabic[index]), true
			}
			index++
		}
	}
	return 0, false
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
	if name == "han" {
		// Target-language output may legitimately preserve Latin proper names,
		// train codes, and other source facts. Require Han to remain the majority
		// rather than rejecting otherwise-Chinese output for preserving them.
		threshold = 0.5
	} else if name == "latin" {
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
