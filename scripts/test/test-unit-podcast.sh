#!/bin/sh
set -eu
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GIZCLAW:=gizclaw}"
require_command "$GIZCLAW"
require_python_yaml
cd "$root"
python3 scripts/test/podcast-cases.py | scripts/test/test-starlark-routing.sh
python3 scripts/test/podcast-news-cases.py | scripts/test/test-starlark-routing.sh
python3 scripts/test/safety_fences.py workflows/podcast/eino.yaml workflows/podcast-news/eino.yaml
"$GIZCLAW" admin validate -f workflows/podcast/eino.yaml
"$GIZCLAW" admin validate -f workflows/podcast-news/eino.yaml
(
  cd scripts/test/chat-assistant
  CGO_ENABLED=0 "${GO:-go}" test -mod=readonly -count=1 -run '^TestNewsPodcast' ./...
)
