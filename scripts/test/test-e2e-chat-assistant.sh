#!/bin/sh
set -eu
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
cd "$root"
require_python_yaml
: "${RAIDS_CHAT_E2E_REPEAT:=3}"
: "${PARALLEL:=3}"
: "${RAIDS_CHAT_E2E_STANDARD:=all}"
exec python3 scripts/test/chat-e2e/run.py \
  --repeat "$RAIDS_CHAT_E2E_REPEAT" --parallel "$PARALLEL" \
  --standard "$RAIDS_CHAT_E2E_STANDARD" --filter "${RAIDS_CHAT_E2E_FILTER:-}"
