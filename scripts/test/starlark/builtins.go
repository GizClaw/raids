package main

import (
	starlarkjson "go.starlark.net/lib/json"
	"go.starlark.net/starlark"
)

// GizClaw v0.35.9 exposes JSON to Eino scripts. Only this native module is
// needed by the catalog today; no filesystem, network or provider is exposed.
// Keep default Starlark language options and reject other undeclared names.
func scriptBuiltins() starlark.StringDict {
	return starlark.StringDict{"json": starlarkjson.Module}
}
