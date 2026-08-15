.DEFAULT_GOAL := help

GO ?= go
GIZCLAW ?= gizclaw
CGO_ENABLED ?= 0
RESOURCE_DIRS := credentials tenants models voices memory-layouts petdefs workflows runtime-profiles registration-tokens

.PHONY: help ci raidtest build-raidtest validate-resources test-raidtest

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
		'  test-raidtest run raidtest unit tests and vet'

ci: validate-resources test-raidtest

raidtest: build-raidtest

build-raidtest:
	cd tools/raidtest && CGO_ENABLED=$(CGO_ENABLED) $(GO) build -o raidtest ./cmd/raidtest

test-raidtest:
	cd tools/raidtest && CGO_ENABLED=$(CGO_ENABLED) $(GO) test ./...
	cd tools/raidtest && CGO_ENABLED=$(CGO_ENABLED) $(GO) vet ./...

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
