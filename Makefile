.DEFAULT_GOAL := help

GO ?= go
GIZCLAW ?= gizclaw
GIZCLAW_TEST_CLI ?= $(GIZCLAW)
CGO_ENABLED ?= 0
RAIDTEST_OUTPUT ?= raidtest
RAIDS_OUTPUT ?= raids
RAIDTEST_REVISION := $(shell git rev-parse --verify HEAD)
RAIDTEST_MODIFIED := $(shell if test -z "$$(git status --porcelain)"; then printf false; else printf true; fi)
RAIDTEST_LDFLAGS := -X github.com/GizClaw/raids/tools/raidtest/internal/report.buildRevision=$(RAIDTEST_REVISION) -X github.com/GizClaw/raids/tools/raidtest/internal/report.buildModified=$(RAIDTEST_MODIFIED)
RESOURCE_DIRS := credentials tenants models voices memory-layouts petdefs workflows tool-resources runtime-profiles registration-tokens

.PHONY: help ci raidtest build-raidtest build-raids validate-resources validate-giztest test-raidtest test-raids check-raids

help:
	@printf '%s\n' \
		'GizClaw Raids' \
		'' \
		'Usage: make <target>' \
		'' \
		'Targets:' \
		'  ci            run all repository checks' \
		'  build-raidtest build the public live candidate runner' \
		'  validate-resources validate applyable Resources with GizClaw' \
		'  validate-giztest validate the declarative Giztest corpus offline' \
		'  build-raids   build the raids package manager CLI' \
		'  test-raids    run raids unit tests and vet' \
		'  check-raids   validate raid.json manifests and RuntimeProfile bindings' \
		'  test-raidtest run raidtest unit tests and vet'

ci: validate-resources validate-giztest check-raids test-raids test-raidtest

raidtest: build-raidtest

build-raids:
	cd tools/raids && CGO_ENABLED=$(CGO_ENABLED) $(GO) build -o "$(RAIDS_OUTPUT)" ./cmd/raids

test-raids:
	cd tools/raids && CGO_ENABLED=$(CGO_ENABLED) $(GO) test ./...
	cd tools/raids && CGO_ENABLED=$(CGO_ENABLED) $(GO) vet ./...

check-raids:
	cd tools/raids && CGO_ENABLED=$(CGO_ENABLED) $(GO) run ./cmd/raids validate --root ../..
	cd tools/raids && CGO_ENABLED=$(CGO_ENABLED) $(GO) run ./cmd/raids check --root ../.. --profile ../../runtime-profiles/testing.yaml --profile ../../runtime-profiles/default.yaml
	cd tools/raids && CGO_ENABLED=$(CGO_ENABLED) $(GO) run ./cmd/raids generate --check --root ../.. --plan ../../profile-plans/testing.plan.yaml --plan ../../profile-plans/default.plan.yaml

build-raidtest:
	cd tools/raidtest && CGO_ENABLED=$(CGO_ENABLED) $(GO) build -ldflags "$(RAIDTEST_LDFLAGS)" -o "$(RAIDTEST_OUTPUT)" ./cmd/raidtest

test-raidtest:
	cd tools/raidtest && CGO_ENABLED=$(CGO_ENABLED) $(GO) test ./...
	cd tools/raidtest && CGO_ENABLED=$(CGO_ENABLED) $(GO) vet ./...

validate-giztest:
	@set -eu; \
	command -v "$(GIZCLAW_TEST_CLI)" >/dev/null 2>&1 || { printf 'missing GizClaw binary with `gizclaw test`: %s\n' "$(GIZCLAW_TEST_CLI)" >&2; exit 1; }; \
	test -d tests/giztest || { printf 'missing Giztest corpus: tests/giztest\n' >&2; exit 1; }; \
	"$(GIZCLAW_TEST_CLI)" test validate -f tests/giztest

validate-resources:
	@set -eu; \
	command -v "$(GIZCLAW)" >/dev/null 2>&1 || { printf 'missing GizClaw binary: %s\n' "$(GIZCLAW)" >&2; exit 1; }; \
	test -n "$(strip $(RESOURCE_DIRS))" || { printf 'no Resource directories configured\n' >&2; exit 1; }; \
	for dir in $(RESOURCE_DIRS); do \
		test -d "$$dir" || { printf 'missing Resource directory: %s\n' "$$dir" >&2; exit 1; }; \
	done; \
	test -f .env.example || { printf 'missing validation environment template: .env.example\n' >&2; exit 1; }; \
	while IFS= read -r line; do \
		case "$$line" in ''|'#'*) continue ;; *=*) ;; *) printf 'invalid .env.example entry\n' >&2; exit 1 ;; esac; \
		name="$${line%%=*}"; value="$${line#*=}"; \
		case "$$name" in ''|*[!A-Z0-9_]*) printf 'invalid .env.example variable: %s\n' "$$name" >&2; exit 1 ;; esac; \
		test -z "$$value" || { printf 'non-empty .env.example value: %s\n' "$$name" >&2; exit 1; }; \
		export "$$name=raids-static-validation"; \
	done < .env.example; \
	files="$$(find $(RESOURCE_DIRS) -type f -name '*.yaml' -print | LC_ALL=C sort)"; \
	test -n "$$files" || { printf 'no applyable Resource files found\n' >&2; exit 1; }; \
	printf '%s\n' "$$files" | while IFS= read -r file; do \
		printf 'validate %s\n' "$$file"; \
		"$(GIZCLAW)" admin validate -f "$$file"; \
	done
