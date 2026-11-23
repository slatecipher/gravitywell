# Contributing to gravitywell

Thanks for your interest in gravitywell. It's a personal project maintained in spare time, so replies to issues and pull requests may take a while.

## Issues

- **Bugs:** include a minimal example that reproduces the problem, what you expected to happen, your versions of Python, `gravitywell` and `clientx`, and your Pi-hole's version (`GET /api/info/version`).
- **Features:** describe the use case first, then the solution you have in mind.

For anything bigger than a small fix, please open an issue to discuss it before you start on a pull request.

## Development setup

You need Python 3.12 or newer and [uv](https://docs.astral.sh/uv/). Fork the repository, clone your fork, and run:

```bash
uv sync --all-groups --reinstall-package gravitywell
make check   # lint, type check, and tests
```

uv installs the package in editable mode, so your changes to `src/` take effect right away. Its metadata, such as the version `gravitywell.__version__` reports, is read from the installation: after changing `pyproject.toml`, run the `uv sync` command again.

Other useful commands:

```bash
make lint                                           # format and auto-fix with ruff
make typecheck                                      # pyright, strict on src/
uv run pytest test/test_public_api.py::test_name    # run a single test
```

When you change code:

- New code in `src/` needs complete type annotations. Pyright checks `src/` in strict mode.
- Add tests for new behavior and for bug fixes. `make test` prints a coverage report.
- Tests never reach the network or a real Pi-hole: send requests through `httpx2.MockTransport`, as ClientX's [testing guide](https://github.com/slatecipher/ClientX/blob/mainline/docs/testing.md) shows. pytest runs in its recommended `importlib` import mode, where test modules can't import helper modules, so share test helpers as fixtures in `conftest.py`. It also runs in strict mode: an unregistered marker or a duplicate parametrize ID is an error.
- Never put a Pi-hole password in code, tests or docs. Read it from an environment variable, such as `PIHOLE_PASSWORD`.
- Ruff formats and lints the code with a 120-character line limit, and checks that docstrings and comments wrap at 80 (W505). `make lint` fixes most issues for you, but not W505: rewrap those lines yourself.
- Write docstrings by the rules in [Docstrings](#docstrings).

## Docstrings

Docstrings follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings), kept short: don't restate what the signature, type hints and names already say. Ruff checks the layout with its `D` rules and the Google convention.

- **When to write one:**
  - Public modules, classes, and complex functions: always. A module docstring says what the module does, with an example.
  - Simple public functions: a one-line docstring only (`"""Do X."""`). Leave out `Args:`, `Returns:` and `Raises:` when the signature and type hints make them obvious.
  - Private helpers (`_helper`): none, unless the logic is non-obvious or tricky, or has side effects.
  - Standard dunder methods (`__str__`, `__repr__`, `__eq__`): none. Document `__init__` only if it takes non-trivial arguments or has setup side effects. Ruff's D105 and D107 are off for this.
  - Test functions (`test_*`): none. The name says what the test checks.
- **No bloat:**
  - Don't repeat type hints: no `(int)` or `(str)` in `Args:` or `Returns:`.
  - No filler, such as `name: The name.` If every parameter is self-explanatory, leave out `Args:`. Ruff's D417 wants every parameter once there's an `Args:` section, so when only one needs explaining, explain it in the description instead.
  - Use the description for why, edge cases, units (seconds or milliseconds), mutations, and exceptions callers must handle.
- **Format:**
  - Use triple double quotes, and wrap lines at 80 characters, though code wraps at 120. Ruff's W505 checks this, for comments too.
  - Start with a one-line imperative summary that ends with a period, such as `"""Fetch the blocking status."""`, and follow it with a blank line if more follows. The summary fits on one line.
  - Write section headers exactly as `Args:`, `Returns:`, `Yields:`, `Raises:` and `Attributes:`. Indent their content 4 spaces, with a hanging indent for wrapped lines.
  - Leave out `Returns:` for a function that returns `None`.
  - Mark code with double backticks, as in `` ``name`` ``.

## Pull requests

- Keep each pull request to one change, on a branch named `<type>/<short-description>`, for example `feat/blocking`.
- In the description, say what changed and why, and how you tested it. If the pull request resolves an issue, add `Closes #N`.
- For changes users will notice, add an entry under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md), and update [README.md](README.md) if it describes the behavior.
- CI must pass: lint, type check, tests on Python 3.12 to 3.14 and on the lowest supported dependency versions, and a build of the package.
- Pull requests are squash-merged, so each one becomes a single commit on `mainline`. That commit's subject comes from the pull request title, or from the commit subject when there is only one commit. Use the format below for both.

## Commit messages

A subject line, a blank line, then a bullet list of the changes. Put any note, such as "No behavior changes", as the last bullet.

```
<type>: <Summary in the imperative, capitalized, no period>

- First change
- Second change
- Note
```

For example:

```
feat: Add the blocking status endpoints

- Add `api.dns.blocking()` and `api.dns.set_blocking()`, sync and async.
- Model the status as a `Literal` of the four values Pi-hole returns.
```

| Type | Use for | Label |
|---|---|---|
| `feat` | New features and public API | `enhancement` |
| `fix` | Bug fixes | `bug` |
| `docs` | Documentation only | `documentation` |
| `refactor` | Internal changes with no change in behavior | `refactor` |
| `ci` | GitHub Actions workflows and Dependabot configuration | `ci` |
| `chore` | Packaging, tooling, and dependency updates | `maintenance` |

The maintainer applies the labels. Two more labels mark special cases:

- `breaking change`: the change can break code that uses gravitywell. Say so in the pull request description and in the changelog entry.
- `release`: preparing or publishing a release.

Dependabot's update pull requests get the `dependencies` label automatically.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
