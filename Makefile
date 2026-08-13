.DEFAULT_GOAL := help

PYTHON ?= python3
GO ?= go
CGO_ENABLED ?= 0

.PHONY: help ci raidtest build-raidtest test-catalog test-pixa test-raidtest

help:
	@printf '%s\n' \
		'GizClaw Raids' \
		'' \
		'Usage: make <target>' \
		'' \
		'Targets:' \
		'  ci            run all repository checks' \
		'  build-raidtest build the public live candidate runner' \
		'  test-catalog  validate the catalog and run validator unit tests' \
		'  test-pixa     validate every PetDef PIXA declaration' \
		'  test-raidtest run raidtest unit tests and vet'

ci: test-catalog test-pixa test-raidtest

raidtest: build-raidtest

build-raidtest:
	cd tools/raidtest && CGO_ENABLED=$(CGO_ENABLED) $(GO) build -o raidtest ./cmd/raidtest

test-raidtest:
	cd tools/raidtest && CGO_ENABLED=$(CGO_ENABLED) $(GO) test ./...
	cd tools/raidtest && CGO_ENABLED=$(CGO_ENABLED) $(GO) vet ./...

test-catalog:
	$(PYTHON) scripts/validate_catalog.py
	$(PYTHON) -m unittest discover -s tests -p 'test_validate_catalog.py' -v

test-pixa:
	$(PYTHON) scripts/validate_pixa.py
	$(PYTHON) -m unittest discover -s tests -p 'test_validate_pixa.py' -v
