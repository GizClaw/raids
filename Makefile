.DEFAULT_GOAL := help

PYTHON ?= python3

.PHONY: help ci test-catalog test-pixa

help:
	@printf '%s\n' \
		'GizClaw Raids' \
		'' \
		'Usage: make <target>' \
		'' \
		'Targets:' \
		'  ci            run all repository checks' \
		'  test-catalog  validate the catalog and run validator unit tests' \
		'  test-pixa     validate every PetDef PIXA declaration'

ci: test-catalog test-pixa

test-catalog:
	$(PYTHON) scripts/validate_catalog.py
	$(PYTHON) -m unittest discover -s tests -p 'test_validate_catalog.py' -v

test-pixa:
	$(PYTHON) scripts/validate_pixa.py
	$(PYTHON) -m unittest discover -s tests -p 'test_validate_pixa.py' -v
