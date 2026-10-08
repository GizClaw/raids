#!/bin/sh
set -eu

printf '%s\n' \
  'GizClaw Raids' \
  '' \
  'Usage: make <target> [VARIABLE=value ...]' \
  '' \
  'Configuration:' \
  '  help                   show every public Make target' \
  '' \
  'Unit test (no live deployment or provider credentials):' \
  '  test-unit-resources    validate applyable Resources and Giztest documents with GizClaw' \
  '  test-unit-learn        regenerate learn-* raids and fail on committed-output drift' \
  '  test-unit-guess        regenerate guess-* raids, check drift, and replay game-state scenarios' \
  '  test-unit-figure       regenerate figure-* raids and fail on committed-output drift' \
  '  test-unit-voices       check catalog-wide Voice invariants (MiniMax synthesis model)' \
  '  test-unit-chat-assistant  run the shipped Eino graph with controlled search and Memory fixtures' \
  '' \
  'Integration test (live deployment):' \
  '  test-e2e               run the Giztest corpus against a provisioned deployment' \
  '  test-e2e-chat-assistant  run isolated released Docker runtime, real providers and device receipts' \
  '' \
  'Variables:' \
  '  GIZCLAW=gizclaw        GizClaw CLI used for validation and Admin apply' \
  '  GIZCLAW_TEST_CLI       CLI providing `gizclaw test` (default: $GIZCLAW)' \
  '  TIER=all               smoke|quality|soak|device|all for test-e2e' \
  '  RAID=all               raid name or all; example: TIER=smoke RAID=story-aesop' \
  '  PARALLEL=4             concurrent Giztest tasks for test-e2e' \
  '  APPLY=0                APPLY=1 applies the testing closure before test-e2e (needs Admin context)' \
  '  GIZCLAW_CONTEXT        Admin context used when APPLY=1' \
  '  REPORT                 Giztest JSON report path (default: tests/giztest/reports/<timestamp>.json)' \
  '  RAIDS_CHAT_E2E_CREDENTIAL_FILE  provider env file for isolated Chat Docker E2E; never archived' \
  '  RAIDS_CHAT_E2E_REPEAT=3  repetitions per device scenario and public Profile' \
  '  RAIDS_CHAT_E2E_STANDARD=all  none|smoke|quality|soak|all; device scenarios always run'
