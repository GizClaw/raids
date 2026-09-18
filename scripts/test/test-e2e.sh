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
#   make test-e2e TIER=smoke RAID=story-aesop
#
# TIER=smoke|quality|soak|device|all and RAID=<raid>|all select tier files.
# Audio-only raids have no soak file and only story, adventure and Journey raids
# have device files; TIER=all selects their available tiers.
#
# APPLY=1 applies the complete testing closure (every raid package, the testing
# RuntimeProfile, and the testing token) with GIZCLAW_CONTEXT before running.
# That replaces the retired raidtest shadow mode: edit
# workflows/<raid>/<engine>.yaml, then run
# `APPLY=1 make test-e2e TIER=smoke RAID=<raid>` to publish the edit and exercise
# just that scenario.
. "$(dirname -- "$0")/../common/repo.sh"
root="$(repo_root)"
: "${GIZCLAW:=gizclaw}"
: "${GIZCLAW_TEST_CLI:=$GIZCLAW}"
: "${RAID:=all}"
: "${TIER:=all}"
: "${PARALLEL:=4}"
: "${APPLY:=0}"
: "${REPORT:=}"

require_command "$GIZCLAW_TEST_CLI"
cd "$root"

case "$TIER" in
 all) tiers='smoke quality soak device' ;;
 smoke|quality|soak|device) tiers="$TIER" ;;
 *) printf 'unknown TIER: %s\n' "$TIER" >&2; exit 1 ;;
esac
case "$RAID" in ''|*[!a-z0-9-]*) printf 'invalid RAID: %s\n' "$RAID" >&2; exit 1 ;; esac
set --
for tier in $tiers; do
 if test "$RAID" = all; then
  set -- "$@" "tests/giztest/$tier"
 else
  found=0
  for file in "tests/giztest/$tier/$RAID".*.giztest.yaml; do
   test -f "$file" || continue
   set -- "$@" "$file"
   found=1
  done
  if test "$found" = 0 && test "$TIER" != all; then
   printf 'no %s tests for RAID=%s\n' "$tier" "$RAID" >&2; exit 1
  fi
 fi
done
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
	# The testing RuntimeProfile binds the whole catalog, so every Workflow it
	# references must exist before it is applied, whatever RAID selects.
	printf '==> apply the testing closure\n'
	find workflows -type f -name '*.yaml' | LC_ALL=C sort | while IFS= read -r file; do
		apply "$file"
	done
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
