"""The names gravitywell exports.

A change here is a change to the public API.
"""

import importlib.metadata

import gravitywell


def test_package_exports() -> None:
    assert sorted(gravitywell.__all__) == sorted(
        [
            "__version__",
            "AsyncPiHole",
            "PiHole",
            "ComponentVersion",
            "LocalVersion",
            "VersionResponse",
            "Versions",
        ]
    )
    for name in gravitywell.__all__:
        assert hasattr(gravitywell, name), name


def test_version_is_the_installed_one() -> None:
    assert gravitywell.__version__ == importlib.metadata.version("gravitywell")
