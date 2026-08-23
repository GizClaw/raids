.DEFAULT_GOAL := help

GIZCLAW ?= gizclaw
GIZCLAW_TEST_CLI ?= $(GIZCLAW)
RAID ?= all
PARALLEL ?= 1
APPLY ?= 0

export GIZCLAW GIZCLAW_TEST_CLI
export RAID PARALLEL APPLY GIZCLAW_CONTEXT REPORT

.PHONY: help test-unit-resources test-unit-voices test-e2e

help:
	@scripts/config/help.sh

test-unit-resources:
	@scripts/test/test-unit-resources.sh

test-unit-voices:
	@scripts/test/test-unit-voices.sh

test-e2e:
	@scripts/test/test-e2e.sh
