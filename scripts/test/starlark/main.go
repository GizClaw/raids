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
		}
	}
	if err := json.NewDecoder(os.Stdin).Decode(&data); err != nil {
		panic(err)
	}
	for i, c := range data.Cases {
		t := &starlark.Thread{Name: "routing"}
		t.SetMaxExecutionSteps(100000)
		globals, err := starlark.ExecFile(t, "select-speaker.star", data.Source, nil)
		if err != nil {
			panic(err)
		}
		result, err := starlark.Call(t, globals["run"], starlark.Tuple{value(c.Input)}, nil)
		if err != nil {
			panic(err)
		}
		got, _, err := result.(*starlark.Dict).Get(starlark.String("speaker"))
		if err != nil {
			panic(err)
		}
		s, _ := starlark.AsString(got)
		if s != c.Speaker {
			panic(fmt.Sprintf("case %d (%s) %v: got %s want %s", i, c.ID, c.Input, s, c.Speaker))
		}
	}
	fmt.Printf("validated Eino Starlark routing: %d cases\n", len(data.Cases))
}
