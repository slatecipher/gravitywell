"""Copy each sample in docs_src/ into the code block that shows it in the docs.

GitHub and PyPI show Markdown as it is, with no way to include a file, so each
page holds a copy of its samples. A comment naming the file goes right before
the block that shows it:

    <!-- docs_src/readme/quickstart.py -->
    ```python
    ...the file's contents...
    ```

Run it with `make docs` after changing a sample, or `make lint`, which runs it
too. `test/test_docs.py` fails while a block differs from its file.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every page that can show samples: the guide, the README and llms.txt.
PAGES = [*sorted((ROOT / "docs").glob("*.md")), ROOT / "README.md", ROOT / "llms.txt"]

MARKER = re.compile(r"<!-- (?P<path>docs_src/\S+\.py) -->")


def synced(page: Path) -> str:
    """Return a page's text with each marked block replaced by its file.

    Raises:
        ValueError: If a marker isn't followed by a `python` block, or names
            a file that doesn't exist.
    """
    lines = page.read_text().splitlines()
    out: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        out.append(line)
        index += 1
        marker = MARKER.fullmatch(line)
        if marker is None:
            continue
        sample = ROOT / marker["path"]
        if index == len(lines) or lines[index] != "```python" or not sample.is_file():
            raise ValueError(
                f"{page.name}:{index}: {line} must name a file in docs_src/ and come right before a ```python block."
            )
        out.append(lines[index])
        index += 1
        while index < len(lines) and lines[index] != "```":
            index += 1
        out += [*sample.read_text().splitlines(), "```"]
        index += 1
    return "\n".join(out) + "\n"


def shown_samples() -> set[Path]:
    """Return the docs_src files the pages show."""
    return {ROOT / match["path"] for page in PAGES for match in MARKER.finditer(page.read_text())}


def main() -> None:
    """Rewrite each page whose blocks differ from their files."""
    for page in PAGES:
        text = synced(page)
        if text != page.read_text():
            page.write_text(text)
            print(f"Updated {page.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
