#!/bin/sh
set -eu
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GIZCLAW:=gizclaw}"
require_command "$GIZCLAW"
require_python_yaml
cd "$root"
python3 scripts/test/podcast-cases.py | scripts/test/test-starlark-routing.sh
python3 scripts/test/safety_fences.py examples/podcast/eino.yaml
"$GIZCLAW" admin validate -f examples/podcast/eino.yaml
"$GIZCLAW" admin validate -f examples/podcast/runtime-profile.yaml
