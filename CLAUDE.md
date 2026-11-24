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

## Layout

- `models/`: the Pydantic models of request and response bodies, one private module per API area (`models/_info.py`), all re-exported from `gravitywell.models`, the one public path for a model. Model names are unique across areas. Models never import ClientX.
- `_resources/`: one module per API area (`_resources/info.py`), holding the area's sync `Resource` and its async `AsyncResource` side by side. Private: callers reach them as `api.info`.
- `_auth.py`: `PiHoleAuth`, an `httpx2.Auth` that logs in, sends the session, logs in again once after a 401, and logs out (`log_out`, `alog_out`) when a client closes.
- `_client.py`: `PiHole` and `AsyncPiHole`, which mount one resource per area and share `_BasePiHole`'s constructor: the Pi-hole's URL, a required `auth=` (`PiHoleAuth`), `verify=` and `transport=`, not all of ClientX's arguments. The top-level `gravitywell` namespace exports only the clients, the auth and `__version__`.
- Tests: one file per API area (`test_info.py`); `test_pi_hole.py` covers the client classes themselves, and `test_public_api.py` pins the exports of `gravitywell` and `gravitywell.models`.

## ClientX

Read ClientX from its public repo, as an outside user would: its [`llms.txt`](https://github.com/slatecipher/ClientX/blob/mainline/llms.txt) before writing endpoints, the [guide](https://github.com/slatecipher/ClientX/tree/mainline/docs) for each feature, and its source when the docs don't answer. When ClientX makes something awkward, say so before working around it: gravitywell doubles as ClientX's first real client, and a ClientX issue is often the better fix.

- Write each sync endpoint on a `Resource` and its async twin on an `AsyncResource`, in the same change, so they never drift.
- The clients set the base URL's path to `/api` (`_BasePiHole.__init__`), so callers pass the Pi-hole's URL with or without it (`http://pi.hole`), and resource prefixes are relative to `/api` (`Resource(prefix="/stats")`). `PiHoleAuth` logs in at `/api/auth` on the requests' host.
- An endpoint returns a model of its whole response body, named `<Endpoint>Response` (`VersionResponse`), with no `decoder=` to unwrap Pi-hole's `{"version": ...}` envelopes: unwrapping would drop siblings such as `processed`. Each one extends `BaseResponse` (`models/_base.py`), which holds `took`, the field every Pi-hole response has. Model only the fields used; Pydantic ignores the rest.
- Pi-hole's one text body, a gravity update's streamed output, goes through a `decoder=` (`_gravity_update` in `_resources/action.py`) into `GravityUpdate`, which has no `took` and so no `Response` suffix: `test_public_api.py` holds every `*Response` to extending `BaseResponse`.
- Set `tool_options=ToolOptions(...)` (`clientx.tools`) where the HTTP method's AI tool hints are wrong, such as a POST that overwrites a setting: `set_blocking` is destructive and idempotent. ClientX's `list_tools` shows what a model sees: check new endpoints' descriptions and schemas with it.
- An endpoint over a time range takes `time_range: Annotated[TimeRange, Query()]` (`models/_time.py`): ClientX spreads the model into `from` and `until`, and its serializers send Unix seconds, so callers and models pass `datetime`s with a timezone. A serializer on a parameter itself raises `DefinitionError`, and Pydantic's `AwareDatetime` isn't a plain value ClientX spreads, hence `datetime` with a validator.
- Resource prefixes are absolute, also when nested: a resource mounted on another repeats its parent's prefix (`HistoryDatabase(prefix="/history/database")` on `History(prefix="/history")`). Dropping the parent's part sends requests to the wrong path. ClientX #178 proposes relative prefixes.
- To guard an endpoint, or convert an argument ClientX can't send as is (`info.delete_messages()` joins a list of IDs into one path segment), give the raw request a private name, such as `_delete`, which ClientX 0.5 leaves out of AI tools (ClientX #179), and make the public method a `@tool` (`clientx.tools`) that checks first and raises `ArgumentError`: ClientX turns it into a `ToolError` whose message reaches the model. `groups.delete()` refuses the Default group this way.
- ClientX joins a resource's prefix and path with `/`, so declare Pi-hole's `:batchDelete` paths with the full path (`"/domains:batchDelete"`) on a resource without that prefix (ClientX #173).

## Pi-hole

- Send the session in the `X-FTL-SID` header, never as the `sid` query parameter: httpx2 logs full URLs at `INFO`.
- Pi-hole limits concurrent sessions: log in once per client, reuse the session, log in again only after a 401, and log out on close. httpx2's `__exit__` doesn't call `close()` (nor `__aexit__` `aclose()`), so the clients override all four.
- Don't wrap `GET /api/info/client`: it echoes the request's headers, including `X-FTL-SID`, so a tool would hand a model the session ID.
- FTL's and the web server's logs can hold session IDs: with `debug.api` on, FTL logs `Read sid="..."` for each request and requests' query strings, and after a database error `sid = ...`. The log methods redact them (`_SESSION_ID` in `_resources/logs.py`): when FTL changes, check its new log lines for one.
- With an application password, changing settings (`PATCH /api/config`) and the session endpoints answer 403 unless the Pi-hole sets `webserver.api.app_sudo`. Say so in each such tool.
- `api.config` has typed methods for the list settings, whose packed entries a model would get wrong (local DNS and CNAME records, upstreams, reverse servers, static leases), and `settings` and `update` for the rest, within `_ALLOWED` and less `_REFUSED` (`_resources/config.py`). Don't widen the allowlist to `webserver`, `files`, `misc` or the auth settings: a model could lock the user out, move the web server or stop DNS. A config response carries the password hashes when `app_sudo` is on, so decoders and `settings` read only what they need. FTL skips an unknown key in a `PATCH` silently and answers one in a `GET` with an empty config, so `update` checks each key first. Pi-hole matches an array item exactly, so a delete looks up the stored entry first.
- A Pi-hole with no password answers a login with a `null` session ID: send no `X-FTL-SID` header then.
- Pi-hole's `PUT` replaces an item: a comment left out is removed and `enabled` becomes `true`, though groups left out stay. Say so in each update tool. A domain rule moves with a `PUT` to its new type and kind that names its current ones in the body, so gravitywell has a separate `move()` rather than optional fields on `update()`.
- Read an endpoint's spec from the Pi-hole itself (`/api/docs/specs/<area>.yaml`, no login needed), and FTL's source (`src/api/`) when the spec is vague. They can disagree: for a DNS server that isn't running, FTL sends the blocking status `failure` while the spec says `failed`. Accept what FTL sends.
- Brand rules for third-party apps: never call gravitywell "official" or suggest Pi-hole makes or supports it; use "Pi-hole" only to say what it works with; no Pi-hole logo or a lookalike.

## Tests

- Tests never reach the network: requests go through `httpx2.MockTransport`. Run against a real Pi-hole only when asked, with the password from `PIHOLE_PASSWORD`; never write a password into code, tests or docs.
- pytest runs in strict mode and `importlib` import mode, so test modules can't import each other: shared helpers are fixtures in `conftest.py`. Async tests use anyio (`@pytest.mark.anyio`), on asyncio only: `conftest.py`'s `anyio_backend` picks it, since anyio 4.10, the lowest version allowed, also runs them on trio, which isn't installed.
- Endpoint tests use `conftest.py`'s `serve` and `sent` fixtures: `serve(body)` makes a transport that answers `PiHoleAuth`'s login and logout, and every other request with `body`, recorded in `sent`. Name its type in the module: `type Serve = Callable[[object], httpx2.MockTransport]`.
- One test per rule, not per branch.

## Conventions

@CONTRIBUTING.md is the source of truth for commit messages, branch names, pull request descriptions, labels and docstrings. Follow it for every commit and pull request, and its Docstrings section for every docstring you write or change. Keep this section, and the `@CONTRIBUTING.md` import in it, when rewriting this file.
