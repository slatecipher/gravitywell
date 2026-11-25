"""Open a release pull request and its draft release, or print release notes.

`make release-pr` runs `python scripts/release.py pr`. From an up-to-date
`mainline` with a clean working tree, it works out the next version from the
`[Unreleased]` section of `CHANGELOG.md`, by the rules in CONTRIBUTING.md's
"Versions" section, or takes the one `--version` names. It dates that section,
sets the version with the latest uv, which relocks, commits on
`chore/release-X.Y.Z`, pushes to the remote `mainline` tracks, and opens the
pull request with the `gh` CLI. Then it creates a draft GitHub release,
`vX.Y.Z`, with the version's changelog section as its notes. After the pull
request is merged, publishing the draft tags `mainline` and starts the Release
workflow.

`python scripts/release.py notes X.Y.Z` prints the GitHub release notes for a
version, from its changelog section, such as to update a draft's notes after
changing the changelog in its pull request.

It uses only the standard library.
"""

import argparse
import re
import subprocess  # noqa: S404 - runs git, uv and gh, see _run
import sys
import tomllib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
PYPROJECT = ROOT / "pyproject.toml"

# Keep a Changelog's sections. Before 1.0, a release with only the patch ones
# is a patch, and any other is a minor version.
SECTIONS = frozenset({"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"})
PATCH_SECTIONS = frozenset({"Fixed", "Security"})

VERSION = re.compile(r"\d+\.\d+\.\d+")


class ReleaseError(Exception):
    """Raised when a release can't be prepared, with what to do about it."""


# --- The changelog ------------------------------------------------------------
def unreleased(changelog: str) -> str:
    """Return the body of the `[Unreleased]` section, without its heading.

    Raises:
        ReleaseError: If there's no `[Unreleased]` section before a release.
    """
    match = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[)", changelog, re.MULTILINE | re.DOTALL)
    if match is None:
        raise ReleaseError("CHANGELOG.md needs a `## [Unreleased]` section above the last release.")
    return match[1].strip()


def next_version(current: str, changes: str) -> tuple[str, str]:
    """Return the version `changes` call for after `current`, and why.

    `changes` is the `[Unreleased]` section's body. The rules are
    CONTRIBUTING.md's, which cover versions before 1.0 only.

    Raises:
        ReleaseError: If there's nothing to release, a section isn't one of
            Keep a Changelog's, or `current` is 1.0 or later.
    """
    sections = list(dict.fromkeys(re.findall(r"^### (.+?)\s*$", changes, re.MULTILINE)))
    if not sections:
        raise ReleaseError("Nothing to release: the `[Unreleased]` section of CHANGELOG.md is empty.")
    unknown = [section for section in sections if section not in SECTIONS]
    if unknown:
        raise ReleaseError(
            f"CHANGELOG.md's `[Unreleased]` has a section Keep a Changelog doesn't: {', '.join(unknown)}. "
            f"Use {', '.join(sorted(SECTIONS))}."
        )
    major, minor, patch = (int(part) for part in current.split("."))
    if major >= 1:
        raise ReleaseError("CONTRIBUTING.md's version rules cover versions before 1.0 only: pass the version.")
    if set(sections) <= PATCH_SECTIONS:
        return f"{major}.{minor}.{patch + 1}", "`[Unreleased]` has only fixes, so it's a patch"
    listed = " and ".join(sections) if len(sections) <= 2 else f"{', '.join(sections[:-1])} and {sections[-1]}"
    return f"{major}.{minor + 1}.0", f"`[Unreleased]` has {listed}, so it's a minor version"


def date_changelog(changelog: str, version: str, day: date) -> str:
    """Return the changelog with its `[Unreleased]` section released.

    The section becomes `## [version] - day`, under a new, empty
    `[Unreleased]`. `[Unreleased]`'s link compares the new tag with `HEAD`, and
    a new link compares the previous tag with it.

    Raises:
        ReleaseError: If `[Unreleased]` has no compare link.
    """
    link = re.search(r"^\[Unreleased\]: (?P<base>\S+)/compare/(?P<previous>\S+)\.\.\.HEAD$", changelog, re.MULTILINE)
    if link is None:
        raise ReleaseError("CHANGELOG.md needs an `[Unreleased]: <repository>/compare/vX.Y.Z...HEAD` link.")
    base, previous = link["base"], link["previous"]
    links = f"[Unreleased]: {base}/compare/v{version}...HEAD\n[{version}]: {base}/compare/{previous}...v{version}"
    changelog = changelog[: link.start()] + links + changelog[link.end() :]
    return changelog.replace("## [Unreleased]\n", f"## [Unreleased]\n\n## [{version}] - {day.isoformat()}\n", 1)


def release_notes(changelog: str, version: str) -> str:
    """Return a version's GitHub release notes, from its changelog section.

    Raises:
        ReleaseError: If the changelog has no section for `version`.
    """
    pattern = rf"^## \[{re.escape(version)}\] - [^\n]*\n(.*?)(?=^## \[|^\[)"
    section = re.search(pattern, changelog, re.MULTILINE | re.DOTALL)
    if section is None:
        raise ReleaseError(f"CHANGELOG.md has no `## [{version}] - YYYY-MM-DD` section.")
    notes = f"```bash\npip install --upgrade gravitywell\n```\n\n{section[1].strip()}\n"
    link = re.search(rf"^\[{re.escape(version)}\]: (\S+)$", changelog, re.MULTILINE)
    return f"{notes}\n**Full changelog:** {link[1]}\n" if link else notes


# --- The pull request ---------------------------------------------------------
def open_release_pr(version: str | None) -> tuple[str, str]:
    """Prepare the release on a branch, and open its PR and draft release.

    Returns:
        The URLs of the pull request and of the draft release.

    Raises:
        ReleaseError: If `mainline` isn't ready, `version` doesn't fit, or a
            command fails. A failure after the branch is created leaves it,
            for a look.
    """
    remote = _check_mainline()
    changelog = CHANGELOG.read_text()
    current: str = tomllib.loads(PYPROJECT.read_text())["project"]["version"]
    changes = unreleased(changelog)
    if version is None:
        version, reason = next_version(current, changes)
    else:
        reason = "chosen with `--version`"
        _check_version(version, current)
        if not changes:
            raise ReleaseError("Nothing to release: the `[Unreleased]` section of CHANGELOG.md is empty.")
    if _run("git", "tag", "--list", f"v{version}"):
        raise ReleaseError(f"v{version} is already tagged.")
    day = date.today()
    branch = f"chore/release-{version}"
    print(f"Releasing {version}: {reason}.")

    _run("git", "switch", "--create", branch)
    CHANGELOG.write_text(date_changelog(changelog, version, day))
    print("Setting the version with the latest uv, which relocks...")
    _run("uvx", "uv@latest", "version", version, "--no-sync")
    _check_one_line_changed("pyproject.toml")
    _check_one_line_changed("uv.lock")

    title = f"chore: Prepare the {version} release"
    message = (
        f"{title}\n\n"
        f"- Set `version` to {version}: {reason}.\n"
        "- Relock with the latest uv; only gravitywell's own version changes.\n"
        f"- Date the changelog's `[Unreleased]` section as `[{version}] - {day.isoformat()}`\n"
        "  and add its compare link.\n"
    )
    _run("git", "add", "CHANGELOG.md", "pyproject.toml", "uv.lock")
    _run("git", "commit", "--quiet", "--file", "-", stdin=message)
    print(f"Pushing {branch} to {remote}...")
    _run("git", "push", "--set-upstream", remote, branch)

    body = (
        f"Prepares the {version} release, opened by `make release-pr`: {reason}.\n\n"
        "## Changes\n\n"
        f"- `version` in `pyproject.toml` goes from `{current}` to `{version}`.\n"
        "- `uv.lock` changes only gravitywell's own version. It was locked with the latest uv, so its revision "
        "stays the same.\n"
        f"- `## [Unreleased]` in `CHANGELOG.md` becomes `## [{version}] - {day.isoformat()}`, with a new, empty "
        f"`## [Unreleased]` above it, and the link references compare `v{version}`. If you merge on a later day, "
        "change the date to match.\n\n"
        f"## What's in {version}\n\n"
        f"{changes}\n\n"
        "## After merging\n\n"
        f"Publish the draft release `v{version}`, on GitHub or with `gh release edit v{version} --draft=false`, "
        f"right after merging: it tags `v{version}` on `mainline`. The Release workflow checks that the tag matches "
        "the project version, builds and smoke-tests the package, publishes it to TestPyPI, and waits for your "
        "approval on the `pypi` environment before it publishes to PyPI.\n\n"
        "If you change the changelog here, update the draft's notes before publishing: "
        f"`uv run python scripts/release.py notes {version} | gh release edit v{version} --notes-file -`.\n"
    )
    url = _run("gh", "pr", "create", "--base", "mainline", "--head", branch, "--title", title, "--body", body)
    number = url.rsplit("/", 1)[-1]
    issue = f"repos/{{owner}}/{{repo}}/issues/{number}"
    _run("gh", "api", "--method", "POST", f"{issue}/labels", "-f", "labels[]=release", "-f", "labels[]=maintenance")
    login = _run("gh", "api", "user", "--jq", ".login")
    _run("gh", "api", "--method", "POST", f"{issue}/assignees", "-f", f"assignees[]={login}")
    print("Creating the draft release...")
    tag = f"v{version}"
    create = ("gh", "release", "create", tag, "--draft", "--target", "mainline", "--title", tag)
    draft = _run(*create, "--notes-file", "-", stdin=release_notes(CHANGELOG.read_text(), version))
    return url, draft


def _check_mainline() -> str:
    """Raise `ReleaseError` unless on a clean, up-to-date `mainline`.

    Returns:
        The remote `mainline` tracks, such as `origin` or `upstream`, which
        the release branch is pushed to.
    """
    if _run("git", "branch", "--show-current") != "mainline":
        raise ReleaseError("Switch to mainline first: git switch mainline.")
    if _run("git", "status", "--porcelain"):
        raise ReleaseError("Commit or stash your changes first: the working tree isn't clean.")
    try:
        remote = _run("git", "config", "branch.mainline.remote")
    except ReleaseError:
        raise ReleaseError("mainline tracks no remote: git branch --set-upstream-to=<remote>/mainline.") from None
    _run("git", "fetch", "--quiet", "--tags", remote, "mainline")
    if _run("git", "rev-parse", "HEAD") != _run("git", "rev-parse", f"{remote}/mainline"):
        raise ReleaseError("Bring mainline up to date first: git pull --ff-only.")
    return remote


def _check_version(version: str, current: str) -> None:
    """Raise `ReleaseError` unless `version` is X.Y.Z, after `current`."""
    if not VERSION.fullmatch(version):
        raise ReleaseError(f"{version!r} isn't a version: use X.Y.Z, such as 0.4.0.")
    if tuple(map(int, version.split("."))) <= tuple(map(int, current.split("."))):
        raise ReleaseError(f"{version} isn't after the current version, {current}.")


def _check_one_line_changed(path: str) -> None:
    """Raise `ReleaseError` unless `path` changed in exactly one line.

    Setting the version changes one line of `pyproject.toml` and one of
    `uv.lock`. More in `uv.lock` means uv re-resolved a dependency or rewrote
    the file in another format, which a release shouldn't carry.
    """
    if _run("git", "diff", "--numstat", "--", path) != f"1\t1\t{path}":
        raise ReleaseError(f"Setting the version changed more than one line of {path}: see git diff {path}.")


def _run(*command: str, stdin: str | None = None) -> str:
    """Run a command in the repository, and return its output, stripped.

    Raises:
        ReleaseError: If it fails, with its error output.
    """
    # The commands are this script's own, run without a shell.
    result = subprocess.run(command, cwd=ROOT, input=stdin, capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode != 0:
        output = result.stderr.strip() or result.stdout.strip()
        raise ReleaseError(f"`{' '.join(command[:3])}` failed:\n{output}")
    return result.stdout.strip()


# --- Entry point --------------------------------------------------------------
def main() -> None:
    """Run the command the arguments name."""
    parser = argparse.ArgumentParser(description="Open a gravitywell release pull request, or print release notes.")
    commands = parser.add_subparsers(dest="command", required=True)
    pr = commands.add_parser("pr", help="open the release pull request")
    pr.add_argument("--version", help="the version to release, instead of the one the changelog calls for")
    notes = commands.add_parser("notes", help="print a version's GitHub release notes")
    notes.add_argument("version")
    arguments = parser.parse_args()
    try:
        if arguments.command == "pr":
            url, draft = open_release_pr(arguments.version)
            print(f"Pull request: {url}\nDraft release: {draft}")
        else:
            print(release_notes(CHANGELOG.read_text(), arguments.version), end="")
    except ReleaseError as error:
        sys.exit(f"release.py: {error}")


if __name__ == "__main__":
    main()
