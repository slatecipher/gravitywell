# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

gravitywell is a third-party, typed Python client for the Pi-hole v6 REST API, built on [ClientX](https://github.com/slatecipher/ClientX). Python 3.12+. Pre-1.0. It supports Pi-hole v6 only, with sync (`PiHole`) and async (`AsyncPiHole`) clients that ship together.

## Commands

```bash
uv sync --all-groups --reinstall-package gravitywell   # install; rerun after changing pyproject.toml (the version comes from metadata)
make check            # lint + typecheck + test
make lint             # ruff format + ruff check --fix on src, test, docs_src and scripts, then make docs
make typecheck        # pyright, strict on src, docs_src and scripts; gates CI
make typecheck-tests  # pyright on test/, standard mode; advisory in CI
make docs             # copy the samples in docs_src/ into the pages that show them
make test-ci          # pytest with the 95% coverage gate CI uses (make test: without the gate)
make release-pr       # maintainer: open the release PR and its draft release (CONTRIBUTING.md's Releasing)
uv run pytest test/test_public_api.py::test_name --no-cov   # one test, without coverage
```

- Ruff wraps code at 120 columns, and docstrings and comments at 80 (W505). `make lint` doesn't fix W505: rewrap by hand. The docs' samples wrap at 100, comments too, so pages show them without scrolling sideways.
- Pyright is strict on `src`, `docs_src` and `scripts`: complete annotations, and explicit types on empty containers.
- CI runs the tests on Python 3.12 to 3.14, and on the lowest dependency versions `pyproject.toml` allows.

## Layout

- `models/`: the Pydantic models of request and response bodies, one private module per API area (`models/_info.py`), all re-exported from `gravitywell.models`, the one public path for a model. Model names are unique across areas. Models never import ClientX.
- `_resources/`: one module per API area (`_resources/info.py`), holding the area's sync `Resource` and its async `AsyncResource` side by side. Private: callers reach them as `api.info`.
- `_auth.py`: `PiHoleAuth`, an `httpx2.Auth` that logs in, sends the session, logs in again once after a 401, and logs out (`log_out`, `alog_out`) when a client closes.
- `_client.py`: `PiHole` and `AsyncPiHole`, which mount one resource per area and share `_BasePiHole`'s constructor: the Pi-hole's URL, a required `auth=` (`PiHoleAuth`), `verify=` and `transport=`, not all of ClientX's arguments. The top-level `gravitywell` namespace exports only the clients, the auth, `__version__` and `PIHOLE_VERSIONS`.
- `_insights.py`: the logic of the insights tools, `explain_domain`, `explain_client` and `check_health`, which answer in one call what takes several endpoints. They're `@tool` methods on `PiHole` and `AsyncPiHole` themselves, as a ClientX resource can't call another, tagged `insights` and read-only: the methods make the requests, sync or async, and `_insights.py` builds the answer from the replies.
- `mcp.py`: the public `gravitywell.mcp` module, an MCP server on FastMCP through `clientx.fastmcp`, in the `mcp` extra: `create_server()` and the `gravitywell-mcp` command (click). It registers the read-only tools unless allowed, by hint, and the areas asked for, by tag; the password comes from `PIHOLE_PASSWORD` only, in the environment or a `--env-file`, never an option. The server closes its client, logging out, when it stops.
- Tests: one file per API area (`test_info.py`); `test_pi_hole.py` covers the client classes themselves, and `test_public_api.py` pins the exports of `gravitywell` and `gravitywell.models`.

## Docs

- `README.md` is the PyPI page: short, with absolute GitHub links into the guide in `docs/`, whose pages link to each other relatively. `docs/README.md` indexes the guide. `llms.txt` is a compact guide for AI assistants and must match the docs and the API.
- Code samples are modules in `docs_src/<page>/<name>.py`, checked by `make lint` and `make typecheck` and run by `test/test_docs.py` up to their first request, with `PIHOLE_PASSWORD` set, in a temporary directory holding a `pihole-backup.zip`; a sample's `test_` functions run in full. A page shows a copy after a `<!-- docs_src/... -->` comment: edit the file, then run `make docs` (`scripts/sync_docs.py`), which `make lint` runs too. The tests fail while a copy is stale or a ```` ```python ```` block has no file; a deliberate fragment is fenced ```` ```python no-check ````.
- `test/test_docs.py` also holds `docs/reference.md` to every public method, `docs/mcp.md`'s areas table to every tool's area, and `README.md`, `docs/compatibility.md` and `llms.txt` to `PIHOLE_VERSIONS`. A new endpoint goes in the reference's table for its area, with its Pi-hole endpoint and tool hint, and in its guide page.
- The logo, `docs/assets/logo-light.svg` and `logo-dark.svg`, is the wordmark in Noto Sans CJK JP Bold (the font of ClientX's logo), converted to paths at 48 px with -10 units of tracking, so it doesn't depend on the viewer's fonts. Its `w` is two downward chevrons, the second faded, in sky blue (`#0284c7` light, `#38bdf8` dark), as ClientX's X is two orange chevrons. The README shows it with a `<picture>`: relative sources for GitHub, and the absolute light URL as the fallback PyPI shows.

## ClientX

Read ClientX from its public repo, as an outside user would: its [`llms.txt`](https://github.com/slatecipher/ClientX/blob/mainline/llms.txt) before writing endpoints, the [guide](https://github.com/slatecipher/ClientX/tree/mainline/docs) for each feature, and its source when the docs don't answer. When ClientX makes something awkward, say so before working around it: gravitywell doubles as ClientX's first real client, and a ClientX issue is often the better fix.

- Write each sync endpoint on a `Resource` and its async twin on an `AsyncResource`, in the same change, so they never drift.
- Tag each resource class, nested ones too, with its area, the name it's mounted as (`tags=["stats"]`): `gravitywell-mcp --areas` keeps a tool by that tag, and `test_mcp.py` holds every tool to exactly one.
- The clients set the base URL's path to `/api` (`_BasePiHole.__init__`), so callers pass the Pi-hole's URL with or without it (`http://pi.hole`), and resource prefixes are relative to `/api` (`Resource(prefix="/stats")`). `PiHoleAuth` logs in at `/api/auth` on the requests' host.
- An endpoint returns a model of its whole response body, named `<Endpoint>Response` (`VersionResponse`), with no `decoder=` to unwrap Pi-hole's `{"version": ...}` envelopes: unwrapping would drop siblings such as `processed`. Each one extends `BaseResponse` (`models/_base.py`), which holds `took`, the field every Pi-hole response has. Model only the fields used; Pydantic ignores the rest.
- Pi-hole's one text body, a gravity update's streamed output, goes through a `decoder=` (`_gravity_update` in `_resources/action.py`) into `GravityUpdate`, which has no `took` and so no `Response` suffix: `test_public_api.py` holds every `*Response` to extending `BaseResponse`.
- Set `tool_options=ToolOptions(...)` (`clientx.tools`) where the HTTP method's AI tool hints are wrong, such as a POST that overwrites a setting: `set_blocking` is destructive and idempotent. ClientX's `list_tools` shows what a model sees: check new endpoints' descriptions and schemas with it.
- Mark a write destructive unless its update is only additive, as MCP defines `destructiveHint`: a restart, a flush or an overwrite counts, though it deletes no data. `gravitywell-mcp --allow-writes` serves every write that isn't destructive, so a wrong hint widens what a model can do.
- An endpoint over a time range takes `time_range: Annotated[TimeRange, Query()]` (`models/_time.py`): ClientX spreads the model into `from` and `until`, and its serializers send Unix seconds, so callers and models pass `datetime`s with a timezone. A serializer on a parameter itself raises `DefinitionError`, and Pydantic's `AwareDatetime` isn't a plain value ClientX spreads, hence `datetime` with a validator.
- Resource prefixes are absolute, also when nested: a resource mounted on another repeats its parent's prefix (`HistoryDatabase(prefix="/history/database")` on `History(prefix="/history")`). Dropping the parent's part sends requests to the wrong path. ClientX #178 proposes relative prefixes.
- To guard an endpoint, or convert an argument ClientX can't send as is (`info.delete_messages()` joins a list of IDs into one path segment), give the raw request a private name, such as `_delete`, which ClientX 0.5 leaves out of AI tools (ClientX #179), and make the public method a `@tool` (`clientx.tools`) that checks first and raises `ArgumentError`: ClientX turns it into a `ToolError` whose message reaches the model. `groups.delete()` refuses the Default group this way.
- ClientX joins a resource's prefix and path with `/`, so declare Pi-hole's `:batchDelete` paths with the full path (`"/domains:batchDelete"`) on a resource without that prefix (ClientX #173).

## Pi-hole

- Send the session in the `X-FTL-SID` header, never as the `sid` query parameter: httpx2 logs full URLs at `INFO`.
- Pi-hole limits concurrent sessions: log in once per client, reuse the session, log in again only after a 401, and log out on close. httpx2's `__exit__` doesn't call `close()` (nor `__aexit__` `aclose()`), so the clients override all four.
- Don't wrap `GET /api/info/client` or `GET /api/auth`: the first echoes the request's headers, including `X-FTL-SID`, and the second returns the session ID and CSRF token, so a tool would hand a model the session. `GET /api/auth/sessions` lists sessions by number only, as `api.sessions` (`api.auth` is httpx2's).
- Teleporter backups hold the password hashes, and a restore overwrites everything, so neither is an AI tool: `export()` is marked `include_in_tools=False` (ClientX 0.6, #182), and `restore()` is a plain method over a private endpoint (`test_teleporter_is_not_an_ai_tool`). Mark any endpoint only code should call the same way, rather than relying on its types.
- FTL's and the web server's logs can hold session IDs: with `debug.api` on, FTL logs `Read sid="..."` for each request and requests' query strings, and after a database error `sid = ...`. The log methods redact them (`_SESSION_ID` in `_resources/logs.py`): when FTL changes, check its new log lines for one.
- With an application password, changing settings (`PATCH /api/config`) and the session endpoints answer 403 unless the Pi-hole sets `webserver.api.app_sudo`. Say so in each such tool.
- `api.config` has typed methods for the list settings, whose packed entries a model would get wrong (local DNS and CNAME records, upstreams, reverse servers, static leases), and `settings` and `update` for the rest, within `_ALLOWED` and less `_REFUSED` (`_resources/config.py`). Don't widen the allowlist to `webserver`, `files`, `misc` or the auth settings: a model could lock the user out, move the web server or stop DNS. A config response carries the password hashes when `app_sudo` is on, so decoders and `settings` read only what they need. FTL skips an unknown key in a `PATCH` silently and answers one in a `GET` with an empty config, so `update` checks each key first. Pi-hole matches an array item exactly, so a delete looks up the stored entry first.
- A Pi-hole with no password answers a login with a `null` session ID: send no `X-FTL-SID` header then.
- Pi-hole's `PUT` replaces an item: a comment left out is removed and `enabled` becomes `true`, though groups left out stay. Say so in each update tool. A domain rule moves with a `PUT` to its new type and kind that names its current ones in the body, so gravitywell has a separate `move()` rather than optional fields on `update()`.
- `PIHOLE_VERSIONS` (`_version.py`) records the Pi-hole release the endpoints were modeled on and tested against. When you check them against a newer release, update it, and the docs that quote it.
- Read an endpoint's spec from the Pi-hole itself (`/api/docs/specs/<area>.yaml`, no login needed), and FTL's source (`src/api/`) when the spec is vague. They can disagree: for a DNS server that isn't running, FTL sends the blocking status `failure` while the spec says `failed`. Accept what FTL sends.
- Brand rules for third-party apps: never call gravitywell "official" or suggest Pi-hole makes or supports it; use "Pi-hole" only to say what it works with; no Pi-hole logo or a lookalike.

## Tests

- Tests never reach the network: requests go through `httpx2.MockTransport`. Run against a real Pi-hole only when asked, with the password from `PIHOLE_PASSWORD`; never write a password into code, tests or docs.
- pytest runs in strict mode and `importlib` import mode, so test modules can't import each other: shared helpers are fixtures in `conftest.py`. Async tests use anyio (`@pytest.mark.anyio`), on asyncio only: `conftest.py`'s `anyio_backend` picks it, since anyio 4.10, the lowest version allowed, also runs them on trio, which isn't installed.
- Endpoint tests use `conftest.py`'s `serve` and `sent` fixtures: `serve(body)` makes a transport that answers `PiHoleAuth`'s login and logout, and every other request with `body`, recorded in `sent`. Name its type in the module: `type Serve = Callable[[object], httpx2.MockTransport]`.
- A tool that calls several endpoints is tested with `route(bodies)`, which answers each path with its own body: `type Route = Callable[[Mapping[str, object]], httpx2.MockTransport]`.
- One test per rule, not per branch.

## Conventions

@CONTRIBUTING.md is the source of truth for commit messages, branch names, pull request descriptions, labels, docstrings and the release steps. Follow it for every commit and pull request, and its Docstrings section for every docstring you write or change. Keep this section, and the `@CONTRIBUTING.md` import in it, when rewriting this file.
