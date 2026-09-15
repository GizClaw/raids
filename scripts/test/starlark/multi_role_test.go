package main

import (
	"encoding/json"
	"go.starlark.net/starlark"
	"os"
	"testing"
)

// Multi-role Testers declare a two-million-step budget in their workflow.
func TestMultiRoleTranscript(t *testing.T) {
	path := os.Getenv("RAIDS_MULTI_ROLE_CASES")
	if path == "" {
		t.Skip("no multi-role transcript cases supplied")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var cases []struct {
		ID, Source, Entry string
		Input             map[string]any
		Expect            map[string]any
	}
	if err := json.Unmarshal(raw, &cases); err != nil {
		t.Fatal(err)
	}
	for _, c := range cases {
		t.Run(c.ID, func(t *testing.T) {
			thread := &starlark.Thread{Name: "multi-role"}
			thread.SetMaxExecutionSteps(2000000)
			globals, err := starlark.ExecFile(thread, "tester.star", c.Source, nil)
			if err != nil {
				t.Fatal(err)
			}
			entry := c.Entry
			if entry == "" {
				entry = "run"
			}
			result, err := starlark.Call(thread, globals[entry], starlark.Tuple{value(c.Input)}, nil)
			if err != nil {
				t.Fatal(err)
			}
			for key, want := range c.Expect {
				got, found, err := result.(*starlark.Dict).Get(starlark.String(key))
				if err != nil || !found {
					t.Fatalf("missing %s", key)
				}
				equal, err := starlark.Equal(got, value(want))
				if err != nil || !equal {
					t.Errorf("%s got %s want %v", key, got, want)
				}
			}
		})
	}
}
