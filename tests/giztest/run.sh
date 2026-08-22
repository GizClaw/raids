#!/usr/bin/env bash
# Run one or more Giztest directories/files against an already provisioned
# GizClaw deployment. The command itself has no Admin authority; run
# tests/giztest/apply-testing.sh first (or any equivalent deployment Apply).
#
# Usage:
#   GIZCLAW_TEST_ENDPOINT=ap.dev.example.com:9821 \
#   GIZCLAW_TEST_REGISTRATION_TOKEN=... \
#   tests/giztest/run.sh [--parallel N] [--output report.json] [path ...]
#
# Defaults: --parallel 1, paths = every scenario directory under tests/giztest
# except h106/ (its target Workflows are not provisioned by apply-testing.sh;
# pass tests/giztest/h106 explicitly against a deployment that exposes them).
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
gizclaw="${GIZCLAW:-gizclaw}"
parallel=1
output=""
paths=()

while (($# > 0)); do
	case "$1" in
	--parallel)
		parallel="$2"
		shift 2
		;;
	--output)
		output="$2"
		shift 2
		;;
	--)
		shift
		paths+=("$@")
		break
		;;
	-*)
		echo "unknown flag: $1" >&2
		exit 2
		;;
	*)
		paths+=("$1")
		shift
		;;
	esac
done

command -v "$gizclaw" >/dev/null 2>&1 || {
	echo "missing GizClaw binary: $gizclaw (set GIZCLAW=/path/to/gizclaw)" >&2
	exit 1
}
: "${GIZCLAW_TEST_ENDPOINT:?set GIZCLAW_TEST_ENDPOINT to the Peer access point, for example ap.dev.gizclaw.com:9821}"
: "${GIZCLAW_TEST_REGISTRATION_TOKEN:?set GIZCLAW_TEST_REGISTRATION_TOKEN to the testing-runtime RegistrationToken value}"

if ((${#paths[@]} == 0)); then
	# Every scenario directory except h106/, whose target Workflows are not part
	# of the testing RuntimeProfile that apply-testing.sh provisions.
	for dir in "$script_dir"/*/; do
		case "$(basename "$dir")" in
		h106 | reports) ;;
		*) paths+=("${dir%/}") ;;
		esac
	done
fi

if [[ -z "$output" ]]; then
	mkdir -p "$script_dir/reports"
	output="$script_dir/reports/giztest-$(date -u +%Y%m%dT%H%M%SZ).json"
fi

cd "$repo_root"
validate_args=()
for path in "${paths[@]}"; do
	validate_args+=(-f "$path")
done
"$gizclaw" test validate "${validate_args[@]}"
echo "==> gizclaw test run --parallel $parallel --output $output ${paths[*]}"
"$gizclaw" test run --parallel "$parallel" --output "$output" "${paths[@]}"
