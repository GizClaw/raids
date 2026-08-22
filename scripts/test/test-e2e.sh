#!/bin/sh
set -eu

# Run the declarative Giztest corpus against an already provisioned GizClaw
# deployment. The runner itself has no Admin authority: it needs only the Peer
# access point and the testing RegistrationToken. APPLY=1 applies the testing
# closure first with the selected Admin context.
#
#   GIZCLAW_TEST_ENDPOINT=edge-bj-01.e2e.gizclaw.com:9821 \
#   GIZCLAW_TEST_REGISTRATION_TOKEN=... \
#   make test-e2e RAID=story-aesop PARALLEL=2
#
# RAID=all skips tests/giztest/h106, whose target Workflows are not part of the
# testing RuntimeProfile.
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

if test "$APPLY" = 1; then
	require_command "$GIZCLAW"
	printf '==> apply the testing closure\n'
	set --
	if test -n "${GIZCLAW_CONTEXT:-}"; then
		set -- --context "$GIZCLAW_CONTEXT"
	fi
	find workflows -type f -name '*.yaml' | LC_ALL=C sort | while IFS= read -r file; do
		"$GIZCLAW" admin apply "$@" -f "$file" >/dev/null
		printf 'applied %s\n' "$file"
	done
	for file in runtime-profiles/testing.yaml registration-tokens/testing.yaml; do
		"$GIZCLAW" admin apply "$@" -f "$file" >/dev/null
		printf 'applied %s\n' "$file"
	done
fi

: "${GIZCLAW_TEST_ENDPOINT:?set GIZCLAW_TEST_ENDPOINT to the Peer access point, for example edge-bj-01.e2e.gizclaw.com:9821}"
: "${GIZCLAW_TEST_REGISTRATION_TOKEN:?set GIZCLAW_TEST_REGISTRATION_TOKEN to the testing-runtime RegistrationToken value}"

set --
if test "$RAID" = all; then
	for dir in tests/giztest/*/; do
		case "$(basename -- "$dir")" in h106 | reports) continue ;; esac
		set -- "$@" "${dir%/}"
	done
else
	test -d "tests/giztest/$RAID" || {
		printf 'unknown raid scenario directory: tests/giztest/%s\n' "$RAID" >&2
		exit 1
	}
	set -- "tests/giztest/$RAID"
fi
test "$#" -gt 0 || {
	printf 'no Giztest scenario directories selected\n' >&2
	exit 1
}

if test -z "$REPORT"; then
	mkdir -p tests/giztest/reports
	REPORT="tests/giztest/reports/giztest-$(date -u +%Y%m%dT%H%M%SZ).json"
fi

validate_args=""
for path in "$@"; do
	validate_args="$validate_args -f $path"
done
# shellcheck disable=SC2086
"$GIZCLAW_TEST_CLI" test validate $validate_args

printf '==> gizclaw test run --parallel %s --output %s %s\n' "$PARALLEL" "$REPORT" "$*"
"$GIZCLAW_TEST_CLI" test run --parallel "$PARALLEL" --output "$REPORT" "$@"
