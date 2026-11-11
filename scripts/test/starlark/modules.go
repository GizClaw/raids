package main

import (
	"encoding/json"
	"fmt"
	"os"

	starlarkjson "go.starlark.net/lib/json"
	"go.starlark.net/starlark"
)

// Match the Runtime compiler and its pure JSON builtin. Do not enable global
// reassignment or substitute Python for Starlark name resolution.
func checkModules() {
	var scripts []struct{ File, Path, Source, Entrypoint string }
	if err := json.NewDecoder(os.Stdin).Decode(&scripts); err != nil {
		panic(err)
	}
	bindings := starlark.StringDict{"json": starlarkjson.Module}
	failures := 0
	for _, s := range scripts {
		name := s.File + ":" + s.Path
		_, program, err := starlark.SourceProgram(name, s.Source, func(name string) bool { _, ok := bindings[name]; return ok })
		if err == nil {
			thread := &starlark.Thread{Name: name}
			thread.SetMaxExecutionSteps(1000000)
			var globals starlark.StringDict
			globals, err = program.Init(thread, bindings)
			entry := s.Entrypoint
			if entry == "" {
				entry = "run"
			}
			if err == nil {
				if _, ok := globals[entry].(starlark.Callable); !ok {
					err = fmt.Errorf("entrypoint %q is not callable", entry)
				}
			}
		}
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s: %v\n", name, err)
			failures++
		}
	}
	if failures > 0 {
		fmt.Fprintf(os.Stderr, "%d/%d Starlark modules failed\n", failures, len(scripts))
		os.Exit(1)
	}
	if len(scripts) == 0 {
		panic("no Starlark scripts found")
	}
	fmt.Printf("validated %d Starlark modules with GizClaw compiler and initialization\n", len(scripts))
}
