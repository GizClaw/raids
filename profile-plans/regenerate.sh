#!/usr/bin/env bash
# Regenerate the committed RuntimeProfiles from their raid-free base documents
# and install plans with the `raids` package manager. Run after editing a
# plan, a base, or any workflows/<raid>/raid.json; CI runs the same command
# with --check and fails when the committed profiles are stale.
#
# Usage: profile-plans/regenerate.sh [--check]
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
args=()
for plan in "$script_dir"/*.plan.yaml; do
	args+=(--plan "$plan")
done
cd "$repo_root/tools/raids"
CGO_ENABLED=0 go run ./cmd/raids generate --root "$repo_root" "$@" "${args[@]}"
