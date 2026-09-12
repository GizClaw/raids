#!/bin/sh
set -eu

# Regenerate every learn-* package offline and compare it with the catalog.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
require_command python3

tmp="$(mktemp -d "${TMPDIR:-/tmp}/raids-learn.XXXXXX")"
trap 'rm -rf -- "$tmp"' EXIT HUP INT TERM

cd "$root"
python3 scripts/learn/generate.py --out "$tmp"
python3 scripts/learn/check.py "$root" "$tmp"
