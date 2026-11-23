.PHONY: lint lint-ci typecheck test test-ci check

lint:
	uv run ruff format src test
	uv run ruff check --fix src test

lint-ci:
	uv run ruff format --check src test
	uv run ruff check src test

# Gates CI. Paths on the command line override `include` in pyproject.toml,
# so this stays scoped to the shipped package.
typecheck:
	uv run pyright src

test:
	uv run pytest

# CI fails below 95% line coverage, so new code arrives with its tests. Only here: local runs of
# a single test file would always fall short.
test-ci:
	uv run pytest --cov=gravitywell --cov-report=term-missing --cov-fail-under=95

check: lint typecheck test
