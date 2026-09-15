#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
: "${GO:=go}"
export GOFLAGS=-mod=mod
# Use the pinned offline module cache when it is present; CI downloads modules.
offline_cache=/Volumes/H002-R02T-APFS/Caches/go/pkg/mod
if [ -z "${GOMODCACHE:-}" ] && [ -d "$offline_cache" ]; then
	export GOMODCACHE=$offline_cache GOPROXY=off GOSUMDB=off
fi
export GOTOOLCHAIN=${GOTOOLCHAIN:-local}
export GOCACHE=${GOCACHE:-${TMPDIR:-/tmp}/raids-starlark-go-cache}
cd "$root/scripts/test/starlark"
exec "$GO" run . "$@"
