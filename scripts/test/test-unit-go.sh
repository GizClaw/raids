#!/bin/sh
set -eu

# Vet and test every Go module under tools/. The raids module also owns the
# offline checks of every raid.json manifest, the committed RuntimeProfile
# bindings, and profile generation staleness.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GO:=go}"
: "${CGO_ENABLED:=0}"

require_command "$GO"
found=0
for module in $(go_modules "$root"); do
	found=1
	printf '==> %s\n' "${module#"$root/"}"
	cd "$module"
	CGO_ENABLED="$CGO_ENABLED" "$GO" vet ./...
	CGO_ENABLED="$CGO_ENABLED" "$GO" test ./...
done
test "$found" = 1 || {
	printf 'no Go modules found under %s/tools\n' "$root" >&2
	exit 1
}
