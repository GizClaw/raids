#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
: "${GO:=go}"
export GOFLAGS=-mod=mod
export GOMODCACHE=${GOMODCACHE:-/Volumes/H002-R02T-APFS/Caches/go/pkg/mod}
export GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local
export GOCACHE=${GOCACHE:-${TMPDIR:-/tmp}/raids-starlark-go-cache}
cd "$root/scripts/test/starlark"
exec "$GO" run . "$@"
