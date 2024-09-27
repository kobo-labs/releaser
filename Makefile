.PHONY: help prettier_check prettier_format nixfmt_format nixfmt_check ruff_format ruff_format_check ruff_check ruff_check_fix pyright pytest check format test

SHELL := bash

help: ## The default task is help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
.DEFAULT_GOAL := help

# Make sure current working directory is file dir
# to secure correct build context
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))

prettier_check: ## Run prettier check
	prettier --check .

prettier_format: ## Run prettier format
	prettier --write .

nixfmt_format: ## Run nix format
	git ls-files -z --cached --others --exclude-standard | \
	xargs -0 -I {} bash -c "if [[ {} == *.nix ]]; \
	then nixfmt {}; fi"

nixfmt_check: ## Run nix format check
	git ls-files -z --cached --others --exclude-standard | \
	xargs -0 -I {} bash -c "if [[ {} == *.nix ]]; \
	then nixfmt --check {}; fi"

ruff_format: ## Run ruff format
	ruff format

ruff_format_check: ## Run ruff format check
	ruff format --check

ruff_check: ## Run ruff linter
	ruff check

ruff_check_fix: ## Run ruff linter with fixes enabled
	ruff check --fix --unsafe-fixes

pyright: ## Run pyright check
	pyright --pythonpath $(shell which python)

pytest: ## Run pytest
	pytest --cov=src --cov-fail-under=100 --cov-report term-missing --verbose

check: prettier_check nixfmt_check ruff_format_check ruff_check pyright ## Run all checks

format: prettier_format nixfmt_format ruff_format ruff_check_fix ## Run all formatters

test: pytest ## Run all tests
