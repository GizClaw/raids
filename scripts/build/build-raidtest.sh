#!/bin/sh
set -eu

# The report embeds the candidate revision and pre-build dirty state because Go
# does not discover VCS metadata from this nested module.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GO:=go}"
: "${CGO_ENABLED:=0}"
: "${RAIDTEST_OUTPUT:=raidtest}"

require_command "$GO"
require_command git

revision="$(git -C "$root" rev-parse --verify HEAD)"
if test -z "$(git -C "$root" status --porcelain)"; then
	modified=false
else
	modified=true
fi
package=github.com/GizClaw/raids/tools/raidtest/internal/report

cd "$root/tools/raidtest"
CGO_ENABLED="$CGO_ENABLED" "$GO" build \
	-ldflags "-X $package.buildRevision=$revision -X $package.buildModified=$modified" \
	-o "$RAIDTEST_OUTPUT" ./cmd/raidtest
printf 'built %s\n' "$(cd "$(dirname -- "$RAIDTEST_OUTPUT")" && pwd)/$(basename -- "$RAIDTEST_OUTPUT")"
