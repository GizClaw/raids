#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
: "${GO:=go}"
export GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local
export GOCACHE=${GOCACHE:-${TMPDIR:-/tmp}/raids-starlark-go-cache}
cd "$root/scripts/test/starlark"
exec "$GO" run -mod=readonly .
