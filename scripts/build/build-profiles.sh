#!/bin/sh
set -eu

# Regenerate every committed RuntimeProfile from its raid-free base document and
# install plan. CHECK=1 compares instead of writing; the same comparison also
# runs as a Go test, so a stale profile fails test-unit-go.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GO:=go}"
: "${CGO_ENABLED:=0}"
: "${CHECK:=0}"

require_command "$GO"
set --
for plan in "$root"/profile-plans/*.plan.yaml; do
	test -f "$plan" || continue
	set -- "$@" --plan "$plan"
done
test "$#" -gt 0 || {
	printf 'no profile plans found under %s/profile-plans\n' "$root" >&2
	exit 1
}
if test "$CHECK" = 1; then
	set -- --check "$@"
fi

cd "$root/tools/raids"
CGO_ENABLED="$CGO_ENABLED" "$GO" run ./cmd/raids generate --root "$root" "$@"
