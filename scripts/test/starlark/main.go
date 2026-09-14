// Execute the unmodified Workflow script with the same no-predeclared environment as Eino.
package main

import (
	"encoding/json"
	"fmt"
	"os"

	"go.starlark.net/starlark"
)

func value(v any) starlark.Value {
	switch x := v.(type) {
	case bool:
		return starlark.Bool(x)
	case float64:
		if x == float64(int64(x)) {
			return starlark.MakeInt64(int64(x))
		}
		return starlark.Float(x)
	case string:
		return starlark.String(x)
	case []any:
		a := []starlark.Value{}
		for _, e := range x {
			a = append(a, value(e))
		}
		return starlark.NewList(a)
	case map[string]any:
		d := starlark.NewDict(len(x))
		for k, e := range x {
			if err := d.SetKey(starlark.String(k), value(e)); err != nil {
				panic(err)
			}
		}
		return d
	case nil:
		return starlark.None
	}
	panic(fmt.Sprintf("unsupported %T", v))
}
func main() {
	var data struct {
		Source string
		Cases  []struct {
			ID      string
			Input   map[string]any
			Speaker string
			Expect  map[string]map[string]any
		}
	}
	if err := json.NewDecoder(os.Stdin).Decode(&data); err != nil {
		panic(err)
	}
	for i, c := range data.Cases {
		t := &starlark.Thread{Name: "routing"}
		t.SetMaxExecutionSteps(100000)
		globals, err := starlark.ExecFile(t, "controller.star", data.Source, nil)
		if err != nil {
			panic(err)
		}
		result, err := starlark.Call(t, globals["run"], starlark.Tuple{value(c.Input)}, nil)
		if err != nil {
			panic(err)
		}
		checks := c.Expect
		if checks == nil {
			checks = map[string]map[string]any{}
		}
		if c.Speaker != "" {
			checks["speaker"] = map[string]any{"equals": c.Speaker}
		}
		for key, ops := range checks {
			got, found, err := result.(*starlark.Dict).Get(starlark.String(key))
			if err != nil || !found {
				panic(fmt.Sprintf("case %d (%s): missing %s", i, c.ID, key))
			}
			for op, want := range ops {
				switch op {
				case "equals":
					equal, err := starlark.Equal(got, value(want))
					if err != nil || !equal {
						panic(fmt.Sprintf("%s: %s got %s want %v", c.ID, key, got, want))
					}
				case "non_empty":
					if !got.Truth() {
						panic(fmt.Sprintf("%s: empty %s", c.ID, key))
					}
				default:
					panic("unknown assertion " + op)
				}
			}
		}
	}
	fmt.Printf("validated Eino Starlark routing: %d cases\n", len(data.Cases))
}
