"""The docs' samples run, the pages show them as they are, and match the API.

Each sample is a module in docs_src/, so `make lint` and `make typecheck` check
it like any other code, in pyright's strict mode. GitHub and PyPI can't include
a file, so a page shows a copy of each of its samples, which `make docs`
(scripts/sync_docs.py) keeps up to date.

Each sample also runs on its own, up to the first request it sends, which
raises instead of reaching the network. A sample's `test_` functions run too.
"""

import contextlib
import re
import runpy
import ssl
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NoReturn

import httpx2
import pytest
from clientx import Resource
from clientx.tools import list_tools

import gravitywell

ROOT = Path(__file__).parent.parent
SAMPLES = sorted((ROOT / "docs_src").rglob("*.py"))
SYNC: dict[str, Any] = runpy.run_path(str(ROOT / "scripts" / "sync_docs.py"))


def test_each_page_shows_its_samples_as_they_are() -> None:
    stale = [page.name for page in SYNC["PAGES"] if SYNC["synced"](page) != page.read_text()]
    assert stale == [], f"Run `make docs` to copy the samples in docs_src/ into {', '.join(stale)}."


def test_each_python_block_shows_a_sample_and_each_sample_is_shown() -> None:
    unshown: list[str] = []
    for page in SYNC["PAGES"]:
        lines = page.read_text().splitlines()
        unshown += [
            f"{page.name}:{number}"
            for number, line in enumerate(lines, start=1)
            if line == "```python" and (number == 1 or not SYNC["MARKER"].fullmatch(lines[number - 2]))
        ]
    assert unshown == [], "Move each block's code into docs_src/ and name the file in a comment before the block."
    assert SYNC["shown_samples"]() == set(SAMPLES)


class RequestSentError(Exception):
    """Stop a sample at the first request it sends."""


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda path: str(path.relative_to(ROOT / "docs_src")))
def test_the_sample_runs(sample: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def stop(*_: object) -> NoReturn:
        raise RequestSentError

    async def astop(*_: object) -> NoReturn:
        raise RequestSentError

    monkeypatch.setattr(httpx2.HTTPTransport, "handle_request", stop)
    monkeypatch.setattr(httpx2.AsyncHTTPTransport, "handle_async_request", astop)
    # What the samples read: the passwords, a backup to restore, and the
    # Pi-hole's certificate authority, which isn't here to load.
    for variable in ("PIHOLE_PASSWORD", "PIHOLE_PRIMARY_PASSWORD", "PIHOLE_SECONDARY_PASSWORD"):
        monkeypatch.setenv(variable, "docs-sample")
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pihole-backup.zip").write_bytes(b"PK\x05\x06" + bytes(18))
    monkeypatch.setattr(ssl.SSLContext, "load_verify_locations", lambda *_, **__: None)
    with contextlib.suppress(RequestSentError):
        namespace = runpy.run_path(str(sample), run_name="docs_sample")
        for name, value in namespace.items():
            if name.startswith("test_") and callable(value):
                value()


def test_the_docs_name_the_pihole_release_gravitywell_was_modeled_on() -> None:
    versions = gravitywell.PIHOLE_VERSIONS
    release = f"core {versions['core']}, web {versions['web']} and FTL {versions['ftl']}"
    for page in ("README.md", "docs/compatibility.md", "llms.txt"):
        assert release in (ROOT / page).read_text(), page


def _methods(resource: object, path: str) -> Iterator[str]:
    for name, member in vars(type(resource)).items():
        if name.startswith("_"):
            continue
        value = getattr(resource, name)
        if isinstance(value, Resource):
            yield from _methods(value, f"{path}.{name}")
        elif callable(member):
            yield f"{path}.{name}"


def test_the_reference_shows_every_method() -> None:
    api = gravitywell.PiHole("http://pi.hole", auth=gravitywell.PiHoleAuth("docs"))
    methods = [
        f"api.{name}"
        for name, member in vars(gravitywell.PiHole).items()
        if not name.startswith("_") and callable(member) and name != "close"
    ]
    for name, value in vars(api).items():
        if isinstance(value, Resource):
            methods += _methods(value, f"api.{name}")
    page = (ROOT / "docs/reference.md").read_text()
    assert [method for method in methods if f"`{method}(" not in page] == []


def test_the_mcp_page_lists_every_area() -> None:
    api = gravitywell.PiHole("http://pi.hole", auth=gravitywell.PiHoleAuth("docs"))
    page = (ROOT / "docs/mcp.md").read_text()
    table = page[page.index("| Area | Tools |") :].split("\n\n", 1)[0]
    listed = re.findall(r"^\| `(\w+)` \|", table, flags=re.MULTILINE)
    assert listed == sorted({tool.tags[0] for tool in list_tools(api)})
