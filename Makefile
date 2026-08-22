.DEFAULT_GOAL := help

GO ?= go
CGO_ENABLED ?= 0
GIZCLAW ?= gizclaw
GIZCLAW_TEST_CLI ?= $(GIZCLAW)
RAIDS_OUTPUT ?= raids
RAIDTEST_OUTPUT ?= raidtest
RAID ?= all
PARALLEL ?= 1
APPLY ?= 0
CHECK ?= 0

export GO CGO_ENABLED GIZCLAW GIZCLAW_TEST_CLI RAIDS_OUTPUT RAIDTEST_OUTPUT
export RAID PARALLEL APPLY CHECK GIZCLAW_CONTEXT REPORT

.PHONY: help build-raids build-raidtest build-profiles test-unit-go test-unit-resources test-e2e

help:
	@scripts/config/help.sh

build-raids:
	@scripts/build/build-raids.sh

build-raidtest:
	@scripts/build/build-raidtest.sh

build-profiles:
	@scripts/build/build-profiles.sh

test-unit-go:
	@scripts/test/test-unit-go.sh

test-unit-resources:
	@scripts/test/test-unit-resources.sh

test-e2e:
	@scripts/test/test-e2e.sh
