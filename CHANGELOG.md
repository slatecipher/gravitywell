# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). While the version is below 1.0, the public API may change between minor versions.

## [Unreleased]

### Added

- `PiHole` and `AsyncPiHole`, clients for a Pi-hole's v6 REST API, with `api.info.version()` for the installed versions of the Pi-hole's components (`GET /api/info/version`). They take the Pi-hole's URL, such as `http://pi.hole`, a required `auth=`, and `verify=` and `transport=`. Each endpoint returns a model of its whole response body, from `gravitywell.models`, which extends `BaseResponse` and so has `took`, the seconds the Pi-hole took to process the request.
- `PiHoleAuth`, for a client's `auth=`, with a password, preferably an application password. It logs in before the first request (`POST /api/auth`), sends the session in the `X-FTL-SID` header, logs in again once after a 401, and shares one login between concurrent requests. A failed login raises `httpx2.HTTPStatusError` with the login's response. Two-factor authentication isn't supported.
- Closing a client (`close()`, `aclose()`, or leaving its `with` block) logs out of its `PiHoleAuth` session, so it doesn't hold one of the Pi-hole's few sessions until it expires.
