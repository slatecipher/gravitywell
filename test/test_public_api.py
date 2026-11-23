"""The names gravitywell exports.

A change here is a change to the public API.
"""

import importlib.metadata

import gravitywell
from gravitywell import BaseResponse


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
            "BaseResponse",
        ]
    )
    for name in gravitywell.__all__:
        assert hasattr(gravitywell, name), name


def test_every_response_model_extends_base_response() -> None:
    responses = [name for name in gravitywell.__all__ if name.endswith("Response") and name != "BaseResponse"]
    assert responses
    for name in responses:
        assert issubclass(getattr(gravitywell, name), BaseResponse), name


def test_version_is_the_installed_one() -> None:
    assert gravitywell.__version__ == importlib.metadata.version("gravitywell")
