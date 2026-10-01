#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
: "${GO:=go}"
cd "$root/scripts/test/chat-assistant"
exec "$GO" test -mod=readonly -count=1 ./...
