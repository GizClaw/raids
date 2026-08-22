#!/bin/sh
set -eu

. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GO:=go}"
: "${CGO_ENABLED:=0}"
: "${RAIDS_OUTPUT:=raids}"

require_command "$GO"
cd "$root/tools/raids"
CGO_ENABLED="$CGO_ENABLED" "$GO" build -o "$RAIDS_OUTPUT" ./cmd/raids
printf 'built %s\n' "$(cd "$(dirname -- "$RAIDS_OUTPUT")" && pwd)/$(basename -- "$RAIDS_OUTPUT")"
