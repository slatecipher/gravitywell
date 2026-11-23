# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). While the version is below 1.0, the public API may change between minor versions.

## [Unreleased]

### Added

- `PiHole` and `AsyncPiHole`, clients for a Pi-hole's v6 REST API, with `api.info.version()` for the installed versions of the Pi-hole's components (`GET /api/info/version`).
