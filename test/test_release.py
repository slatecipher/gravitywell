"""The release script: the next version, the dated changelog and the notes."""

import runpy
import tomllib
from datetime import date
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
RELEASE: dict[str, Any] = runpy.run_path(str(ROOT / "scripts" / "release.py"))

CHANGELOG = """# Changelog

## [Unreleased]

### Fixed

- A fix.

## [0.3.0] - 2026-11-23

### Added

- A feature.

[Unreleased]: https://github.com/owner/repo/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/owner/repo/compare/v0.2.1...v0.3.0
"""


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        pytest.param("### Fixed\n\n- A fix.", "0.3.1", id="only fixes"),
        pytest.param("### Added\n\n- A feature.\n\n### Fixed\n\n- A fix.", "0.4.0", id="a feature"),
        pytest.param("### Changed\n\n- **Breaking:** a change.", "0.4.0", id="a breaking change"),
    ],
)
def test_the_next_version_follows_the_rules_before_1_0(changes: str, expected: str) -> None:
    assert RELEASE["next_version"]("0.3.0", changes)[0] == expected


@pytest.mark.parametrize(
    ("current", "changes", "message"),
    [
        pytest.param("0.3.0", "", "Nothing to release", id="nothing"),
        pytest.param(
            "0.3.0", "### Improved\n\n- A change.", "a section Keep a Changelog doesn't: Improved", id="unknown"
        ),
        pytest.param("1.0.0", "### Fixed\n\n- A fix.", "before 1.0 only: pass the version", id="1.0"),
    ],
)
def test_the_next_version_needs_known_sections_before_1_0(current: str, changes: str, message: str) -> None:
    with pytest.raises(RELEASE["ReleaseError"], match=message):
        RELEASE["next_version"](current, changes)


def test_releasing_dates_the_unreleased_section_and_links_its_tag() -> None:
    released = RELEASE["date_changelog"](CHANGELOG, "0.3.1", date(2026, 11, 24))
    assert "## [Unreleased]\n\n## [0.3.1] - 2026-11-24\n\n### Fixed\n\n- A fix.\n\n## [0.3.0]" in released
    assert released.endswith(
        "[Unreleased]: https://github.com/owner/repo/compare/v0.3.1...HEAD\n"
        "[0.3.1]: https://github.com/owner/repo/compare/v0.3.0...v0.3.1\n"
        "[0.3.0]: https://github.com/owner/repo/compare/v0.2.1...v0.3.0\n"
    )
    assert RELEASE["unreleased"](released) == ""


def test_release_notes_are_the_versions_section_and_its_compare_link() -> None:
    assert RELEASE["release_notes"](CHANGELOG, "0.3.0") == (
        "```bash\npip install --upgrade gravitywell\n```\n\n"
        "### Added\n\n- A feature.\n\n"
        "**Full changelog:** https://github.com/owner/repo/compare/v0.2.1...v0.3.0\n"
    )


def test_the_changelog_has_notes_for_the_current_version() -> None:
    # make release-pr writes them into the version's draft release.
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert "**Full changelog:**" in RELEASE["release_notes"]((ROOT / "CHANGELOG.md").read_text(), version)
