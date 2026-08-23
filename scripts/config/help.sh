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
  'Unit test (offline; no network, no credentials):' \
  '  test-unit-resources    validate applyable Resources and Giztest documents with GizClaw' \
  '  test-unit-voices       check catalog-wide Voice invariants (MiniMax synthesis model)' \
  '' \
  'Integration test (live deployment):' \
  '  test-e2e               run the Giztest corpus against a provisioned deployment' \
  '' \
  'Variables:' \
  '  GIZCLAW=gizclaw        GizClaw CLI used for validation and Admin apply' \
  '  GIZCLAW_TEST_CLI       CLI providing `gizclaw test` (default: $GIZCLAW)' \
  '  RAID=all               raid or single scenario for test-e2e, for example RAID=story-aesop or RAID=story-aesop/eino' \
  '  PARALLEL=1             concurrent Giztest tasks for test-e2e' \
  '  APPLY=0                APPLY=1 applies the testing closure before test-e2e (needs Admin context)' \
  '  GIZCLAW_CONTEXT        Admin context used when APPLY=1' \
  '  REPORT                 Giztest JSON report path (default: tests/giztest/reports/<timestamp>.json)'
