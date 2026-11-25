.PHONY: lint lint-ci typecheck typecheck-tests test test-ci docs check release-pr

# Formats and fixes, then copies the formatted samples into the docs.
lint:
	uv run ruff format src test docs_src scripts
	uv run ruff check --fix src test docs_src scripts
	uv run python scripts/sync_docs.py

lint-ci:
	uv run ruff format --check src test docs_src scripts
	uv run ruff check src test docs_src scripts

# Gates CI. Paths on the command line override `include` in pyproject.toml,
# so this stays scoped to the shipped package, the docs' samples and scripts.
typecheck:
	uv run pyright src docs_src scripts

# Advisory: reported in CI via continue-on-error, never blocks a merge.
typecheck-tests:
	uv run pyright test

test:
	uv run pytest

# CI fails below 95% line coverage, so new code arrives with its tests. Only here: local runs of
# a single test file would always fall short.
test-ci:
	uv run pytest --cov=gravitywell --cov-report=term-missing --cov-fail-under=95

# Copies each sample in docs_src/ into the code block that shows it in the docs.
docs:
	uv run python scripts/sync_docs.py

check: lint typecheck test

# Opens the release pull request and its draft release, with the version the
# changelog calls for, or VERSION=X.Y.Z. See "Releasing" in CONTRIBUTING.md.
release-pr:
	uv run python scripts/release.py pr $(if $(VERSION),--version $(VERSION))
