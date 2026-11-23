# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

gravitywell is a third-party, typed Python client for the Pi-hole v6 REST API, built on [ClientX](https://github.com/slatecipher/ClientX). Python 3.12+. Pre-1.0. It supports Pi-hole v6 only, with sync (`PiHole`) and async (`AsyncPiHole`) clients that ship together.

## Commands

```bash
uv sync --all-groups --reinstall-package gravitywell   # install; rerun after changing pyproject.toml (the version comes from metadata)
make check            # lint + typecheck + test
make lint             # ruff format + ruff check --fix on src and test
make typecheck        # pyright, strict on src; gates CI
make test-ci          # pytest with the 95% coverage gate CI uses (make test: without the gate)
uv run pytest test/test_public_api.py::test_name --no-cov   # one test, without coverage
```

- Ruff wraps code at 120 columns, and docstrings and comments at 80 (W505). `make lint` doesn't fix W505: rewrap by hand.
- Pyright is strict on `src`: complete annotations, and explicit types on empty containers.
- CI runs the tests on Python 3.12 to 3.14, and on the lowest dependency versions `pyproject.toml` allows.

## ClientX

Read ClientX from its public repo, as an outside user would: its [`llms.txt`](https://github.com/slatecipher/ClientX/blob/mainline/llms.txt) before writing endpoints, the [guide](https://github.com/slatecipher/ClientX/tree/mainline/docs) for each feature, and its source when the docs don't answer. When ClientX makes something awkward, say so before working around it: gravitywell doubles as ClientX's first real client, and a ClientX issue is often the better fix.

- Write each sync endpoint on a `Resource` and its async twin on an `AsyncResource`, in the same change, so they never drift.
- Put `/api` in the base URL; resource prefixes are absolute (`Resource(prefix="/stats")`).
- ClientX joins a resource's prefix and path with `/`, so declare Pi-hole's `:batchDelete` paths with the full path (`"/domains:batchDelete"`) on a resource without that prefix (ClientX #173).

## Pi-hole

- Send the session in the `X-FTL-SID` header, never as the `sid` query parameter: httpx2 logs full URLs at `INFO`.
- Pi-hole limits concurrent sessions: log in once per client, reuse the session, log in again only after a 401.
- Brand rules for third-party apps: never call gravitywell "official" or suggest Pi-hole makes or supports it; use "Pi-hole" only to say what it works with; no Pi-hole logo or a lookalike.

## Tests

- Tests never reach the network: requests go through `httpx2.MockTransport`. Run against a real Pi-hole only when asked, with the password from `PIHOLE_PASSWORD`; never write a password into code, tests or docs.
- pytest runs in strict mode and `importlib` import mode, so test modules can't import each other: shared helpers are fixtures in `conftest.py`. Async tests use anyio (`@pytest.mark.anyio`).
- One test per rule, not per branch.

## Conventions

@CONTRIBUTING.md is the source of truth for commit messages, branch names, pull request descriptions, labels and docstrings. Follow it for every commit and pull request, and its Docstrings section for every docstring you write or change. Keep this section, and the `@CONTRIBUTING.md` import in it, when rewriting this file.
