#!/usr/bin/env bash
# Apply the stable Dev testing closure that the declarative Giztest corpus runs
# against: every catalog Workflow, every relay Tester Workflow, the `testing`
# RuntimeProfile, and the `testing-runtime` RegistrationToken.
#
# This is the provisioning boundary that `gizclaw test` deliberately does not own
# (GizClaw #917 non-goals). Credentials, Tenants, Models, Voices, MemoryLayouts,
# and PetDefs are deployment-owned and must already exist on the target Server.
#
# Usage:
#   tests/giztest/apply-testing.sh [--context <gizclaw-context>] [--dry-run]
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
gizclaw="${GIZCLAW:-gizclaw}"
context=""
dry_run=0

while (($# > 0)); do
	case "$1" in
	--context)
		context="$2"
		shift 2
		;;
	--dry-run)
		dry_run=1
		shift
		;;
	*)
		echo "unknown argument: $1" >&2
		exit 2
		;;
	esac
done

command -v "$gizclaw" >/dev/null 2>&1 || {
	echo "missing GizClaw binary: $gizclaw (set GIZCLAW=/path/to/gizclaw)" >&2
	exit 1
}

apply() {
	local file="$1"
	if ((dry_run)); then
		"$gizclaw" admin validate -f "$file" >/dev/null
		echo "validated $file"
		return
	fi
	if [[ -n "$context" ]]; then
		"$gizclaw" admin apply --context "$context" -f "$file" >/dev/null
	else
		"$gizclaw" admin apply -f "$file" >/dev/null
	fi
	echo "applied $file"
}

cd "$repo_root"

# 1. Catalog targets (every engine) and the relay Tester Workflows.
find workflows -type f -name '*.yaml' | LC_ALL=C sort | while IFS= read -r file; do
	apply "$file"
done

# 2. The stable testing RuntimeProfile binds targets, testers, and aliases.
apply runtime-profiles/testing.yaml

# 3. The Dev/E2E-only RegistrationToken targets that profile.
apply registration-tokens/testing.yaml

echo "testing closure ready: export GIZCLAW_TEST_REGISTRATION_TOKEN from registration-tokens/testing.yaml and GIZCLAW_TEST_ENDPOINT for the Peer access point"
