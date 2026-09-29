#!/bin/sh
set -eu

# Regenerate every figure-* package offline and compare it with the catalog.
# The Workflows' routing suites run with the other story raids in
# test-unit-resources.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
require_command python3

tmp="$(mktemp -d "${TMPDIR:-/tmp}/raids-figure.XXXXXX")"
trap 'rm -rf -- "$tmp"' EXIT HUP INT TERM

cd "$root"
python3 scripts/figure/generate.py --out "$tmp"
python3 scripts/figure/check.py "$root" "$tmp"
