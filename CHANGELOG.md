# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). While the version is below 1.0, the public API may change between minor versions.

## [Unreleased]

### Added

- `PiHole` and `AsyncPiHole`, clients for a Pi-hole's v6 REST API, with `api.info.version()` for the installed versions of the Pi-hole's components (`GET /api/info/version`). They take the Pi-hole's URL, such as `http://pi.hole`, a required `auth=`, and `verify=` and `transport=`. Each endpoint returns a model of its whole response body, from `gravitywell.models`, which extends `BaseResponse` and so has `took`, the seconds the Pi-hole took to process the request.
- `PiHoleAuth`, for a client's `auth=`, with a password, preferably an application password. It logs in before the first request (`POST /api/auth`), sends the session in the `X-FTL-SID` header, logs in again once after a 401, and shares one login between concurrent requests. A failed login raises `httpx2.HTTPStatusError` with the login's response. Two-factor authentication isn't supported.
- Closing a client (`close()`, `aclose()`, or leaving its `with` block) logs out of its `PiHoleAuth` session, so it doesn't hold one of the Pi-hole's few sessions until it expires.
- `api.dns.blocking()` and `api.dns.set_blocking()`, to read and change whether the Pi-hole blocks ads and trackers, with an optional timer that switches the status back on its own (`GET` and `POST /api/dns/blocking`). AI tools mark `set_blocking` as destructive and idempotent.
- `api.stats.summary()`, totals of the Pi-hole's queries (blocked, forwarded and cached, and by record type, status and reply), clients and blocklists, over the history it keeps, the last 24 hours by default (`GET /api/stats/summary`). The blocklists' last update is a `datetime` in UTC, or `None` when the Pi-hole doesn't know.
- `api.stats.top_domains()` and `api.stats.top_clients()`, the most queried domains and the clients that sent the most queries, ranked by permitted (domains) or all (clients) queries, or by blocked queries with `blocked=True`; `count=` sets how many, 10 by default (`GET /api/stats/top_domains` and `/api/stats/top_clients`). Their totals are `None` when the Pi-hole's privacy level hides the list.
