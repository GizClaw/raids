#!/bin/sh
set -eu

# Run the declarative Giztest corpus against a GizClaw deployment. The runner
# itself has no Admin authority: it needs only the Peer access point and the
# testing RegistrationToken.
#
# The deployment is configuration, never a default baked into this script:
# GIZCLAW_TEST_ENDPOINT and GIZCLAW_TEST_REGISTRATION_TOKEN come from the
# environment.
#
#   GIZCLAW_TEST_ENDPOINT=<host:port> GIZCLAW_TEST_REGISTRATION_TOKEN=<token> \
#   make test-e2e RAID=story-aesop/eino
#
# RAID selects the scope:
#   all                  every scenario directory except tests/giztest/h106,
#                        whose targets are not part of the testing profile
#   <raid>               every scenario of one raid, for example story-aesop
#   <raid>/<scenario>    one scenario file, for example story-aesop/eino
#
# APPLY=1 applies the raid packages the run needs (candidate implementations,
# the shared Tester, the testing RuntimeProfile, and the testing token) with
# GIZCLAW_CONTEXT before running. That replaces the retired raidtest shadow
# mode: edit workflows/<raid>/<engine>.yaml, then run
# `APPLY=1 make test-e2e RAID=<raid>/<engine>`.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GIZCLAW:=gizclaw}"
: "${GIZCLAW_TEST_CLI:=$GIZCLAW}"
: "${RAID:=all}"
: "${PARALLEL:=1}"
: "${APPLY:=0}"
: "${REPORT:=}"

require_command "$GIZCLAW_TEST_CLI"
cd "$root"

raid="${RAID%%/*}"
scenario=''
case "$RAID" in */*) scenario="${RAID#*/}" ;; esac

# Resolve the selection into positional parameters.
set --
if test "$RAID" = all; then
	for dir in tests/giztest/*/; do
		case "$(basename -- "$dir")" in h106 | reports) continue ;; esac
		set -- "$@" "${dir%/}"
	done
elif test -n "$scenario"; then
	file="tests/giztest/$raid/$scenario.giztest.yaml"
	test -f "$file" || {
		printf 'unknown scenario: %s\n' "$file" >&2
		ls -1 "tests/giztest/$raid" 2>/dev/null | sed 's|^|  available: |' >&2 || true
		exit 1
	}
	set -- "$file"
else
	test -d "tests/giztest/$raid" || {
		printf 'unknown raid scenario directory: tests/giztest/%s\n' "$raid" >&2
		exit 1
	}
	set -- "tests/giztest/$raid"
fi
test "$#" -gt 0 || {
	printf 'no Giztest scenarios selected\n' >&2
	exit 1
}

if test "$APPLY" = 1; then
	require_command "$GIZCLAW"
	context_args=''
	if test -n "${GIZCLAW_CONTEXT:-}"; then
		context_args="--context $GIZCLAW_CONTEXT"
	fi
	apply() {
		# shellcheck disable=SC2086
		"$GIZCLAW" admin apply $context_args -f "$1" >/dev/null
		printf 'applied %s\n' "$1"
	}
	printf '==> apply the testing closure\n'
	if test "$RAID" = all; then
		find workflows -type f -name '*.yaml' | LC_ALL=C sort | while IFS= read -r file; do
			apply "$file"
		done
	else
		for file in "workflows/$raid"/*.yaml; do
			apply "$file"
		done
	fi
	apply runtime-profiles/testing.yaml
	apply registration-tokens/testing.yaml
fi

: "${GIZCLAW_TEST_ENDPOINT:?set GIZCLAW_TEST_ENDPOINT to the Peer access point (host:port)}"
: "${GIZCLAW_TEST_REGISTRATION_TOKEN:?set GIZCLAW_TEST_REGISTRATION_TOKEN to the testing-runtime RegistrationToken value}"

if test -z "$REPORT"; then
	mkdir -p tests/giztest/reports
	REPORT="tests/giztest/reports/giztest-$(date -u +%Y%m%dT%H%M%SZ).json"
fi

validate_args=''
for path in "$@"; do
	validate_args="$validate_args -f $path"
done
# shellcheck disable=SC2086
"$GIZCLAW_TEST_CLI" test validate $validate_args

printf '==> gizclaw test run --parallel %s --output %s %s\n' "$PARALLEL" "$REPORT" "$*"
"$GIZCLAW_TEST_CLI" test run --parallel "$PARALLEL" --output "$REPORT" "$@"
