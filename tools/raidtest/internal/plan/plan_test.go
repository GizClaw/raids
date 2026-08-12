package plan

import "testing"

func TestValidateRejectsDuplicateCaseAndUnknownDriver(t *testing.T) {
	p := Plan{Version: "v1", Name: "sample", Driver: "flowcraft", Cases: []Case{{ID: "one", Turns: []Turn{{ID: "turn", User: "hello"}}}, {ID: "one", Turns: []Turn{{ID: "turn", User: "again"}}}}}
	if err := p.Validate(); err == nil {
		t.Fatal("expected duplicate error")
	}
	p.Driver = "unknown"
	if err := p.Validate(); err == nil {
		t.Fatal("expected driver error")
	}
}

func TestCommittedDefaultPlansAreValid(t *testing.T) {
	files := []string{"pet-care.yaml", "assistant-general.yaml", "assistant-doubao.yaml", "murder-mystery.yaml", "journey.yaml", "translations.yaml"}
	for _, file := range files {
		t.Run(file, func(t *testing.T) {
			p, err := Load("../../plans/default/" + file)
			if err != nil {
				t.Fatal(err)
			}
			if len(p.Cases) == 0 {
				t.Fatal("plan has no cases")
			}
		})
	}
}

func TestValidateAcceptsDeterministicContracts(t *testing.T) {
	p := Plan{Version: "v1", Name: "sample", Driver: "translate", Cases: []Case{{ID: "facts", Turns: []Turn{{ID: "translate", User: "Alice has 12 apples.", Required: []string{"Alice", "12"}, Forbidden: []string{"13"}, Scripts: []string{"latin"}, MaxRunes: 40}}}}}
	if err := p.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestPlanReportsRequiredOptionalModelCapabilities(t *testing.T) {
	p := Plan{Cases: []Case{{Turns: []Turn{{Intent: "say hello"}, {User: "hello", Judge: []string{"naturalness"}}}}}}
	if !p.NeedsAgent() || !p.NeedsJudge() {
		t.Fatalf("requirements not detected: %#v", p)
	}
}

func TestValidateRejectsContradictoryFactsAndUnknownScripts(t *testing.T) {
	p := Plan{Version: "v1", Name: "sample", Driver: "translate", Cases: []Case{{ID: "facts", Turns: []Turn{{ID: "turn", User: "hello", Required: []string{"Alice"}, Forbidden: []string{"alice"}}}}}}
	if err := p.Validate(); err == nil {
		t.Fatal("expected contradictory fact error")
	}
	p.Cases[0].Turns[0].Forbidden = nil
	p.Cases[0].Turns[0].Scripts = []string{"made-up"}
	if err := p.Validate(); err == nil {
		t.Fatal("expected unsupported script error")
	}
}
