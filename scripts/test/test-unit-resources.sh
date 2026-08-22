#!/bin/sh
set -eu

# Offline schema validation of every declarative file: applyable Admin Resources
# through `gizclaw admin validate`, and the Giztest corpus through
# `gizclaw test validate`. It never uses a GizClaw context, contacts a Server,
# or reads a real credential: each empty .env.example variable is exported with
# a fixed non-secret placeholder so Credential and Tenant manifests resolve.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GIZCLAW:=gizclaw}"
: "${GIZCLAW_TEST_CLI:=$GIZCLAW}"

resource_dirs='credentials tenants models voices memory-layouts petdefs workflows tool-resources runtime-profiles registration-tokens'

require_command "$GIZCLAW"
require_command "$GIZCLAW_TEST_CLI"
cd "$root"

for dir in $resource_dirs; do
	test -d "$dir" || {
		printf 'missing Resource directory: %s\n' "$dir" >&2
		exit 1
	}
done
test -f .env.example || {
	printf 'missing validation environment template: .env.example\n' >&2
	exit 1
}

while IFS= read -r line; do
	case "$line" in '' | '#'*) continue ;; *=*) ;; *)
		printf 'invalid .env.example entry\n' >&2
		exit 1
		;;
	esac
	name="${line%%=*}"
	value="${line#*=}"
	case "$name" in '' | *[!A-Z0-9_]*)
		printf 'invalid .env.example variable: %s\n' "$name" >&2
		exit 1
		;;
	esac
	test -z "$value" || {
		printf 'non-empty .env.example value: %s\n' "$name" >&2
		exit 1
	}
	export "$name=raids-static-validation"
done <.env.example

files="$(find $resource_dirs -type f -name '*.yaml' -print | LC_ALL=C sort)"
test -n "$files" || {
	printf 'no applyable Resource files found\n' >&2
	exit 1
}
printf '%s\n' "$files" | while IFS= read -r file; do
	printf 'validate %s\n' "$file"
	"$GIZCLAW" admin validate -f "$file"
done

test -d tests/giztest || {
	printf 'missing Giztest corpus: tests/giztest\n' >&2
	exit 1
}
"$GIZCLAW_TEST_CLI" test validate -f tests/giztest
