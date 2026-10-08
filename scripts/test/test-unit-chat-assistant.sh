#!/bin/sh
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
: "${GO:=go}"
# This text/HTTP contract suite does not exercise native audio codecs.
export CGO_ENABLED=0
cd "$root/scripts/test/chat-assistant"
exec "$GO" test -mod=readonly -count=1 ./...
