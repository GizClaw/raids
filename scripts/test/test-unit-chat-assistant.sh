#!/bin/sh
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
: "${GO:=go}"
# This suite uses released SDK modules and controlled text/HTTP transports.
export CGO_ENABLED=0 GOWORK=off
cd "$root/scripts/test/chat-assistant"

# The current SDK's process-metrics dependency requires native system bindings
# for Darwin. Run the same static Linux test binary in the released Runtime
# container instead; the container has no network or provider credentials.
if [ "$(uname -s)" = Darwin ]; then
  command -v docker >/dev/null 2>&1 || { printf '%s\n' 'Docker is required for SDK contract tests on macOS' >&2; exit 1; }
  work=$(mktemp -d "${TMPDIR:-/tmp}/raids-chat-contracts.XXXXXXXX")
  trap 'rm -rf "$work"' EXIT HUP INT TERM
  architecture=$(docker info --format '{{.Architecture}}')
  case "$architecture" in
    arm64 | aarch64) target_arch=arm64 ;;
    amd64 | x86_64) target_arch=amd64 ;;
    *) printf 'unsupported Docker architecture: %s\n' "$architecture" >&2; exit 1 ;;
  esac
  GOOS=linux GOARCH="$target_arch" "$GO" test -mod=readonly -c -o "$work/contracts" .
  image=${RAIDS_CHAT_UNIT_IMAGE:-ghcr.io/gizclaw/gizclaw@sha256:73cfa235e15489c08ee1fe438897fd55b3bb454141a3a6c05422b2a7bb9d593f}
  docker run --rm --network none \
    --mount "type=bind,source=$root,target=/raids,readonly" \
    --mount "type=bind,source=$work/contracts,target=/contracts,readonly" \
    --workdir /raids/scripts/test/chat-assistant --entrypoint /contracts "$image" \
    -test.count=1
else
  exec "$GO" test -mod=readonly -count=1 ./...
fi
