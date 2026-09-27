#!/bin/sh
set -eu

# Regenerate every guess-* package offline, compare it with the catalog, and
# replay the Starlark game scenarios with the GizClaw Starlark interpreter.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
require_command python3

tmp="$(mktemp -d "${TMPDIR:-/tmp}/raids-guess.XXXXXX")"
trap 'rm -rf -- "$tmp"' EXIT HUP INT TERM

cd "$root"
python3 scripts/guess/generate.py --out "$tmp"
python3 scripts/guess/check.py "$root" "$tmp"
python3 scripts/guess/cases.py
