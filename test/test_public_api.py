"""The names gravitywell exports.

A change here is a change to the public API.
"""

import importlib.metadata

import gravitywell
import gravitywell.models
from gravitywell.models import BaseResponse


def test_package_exports() -> None:
    assert sorted(gravitywell.__all__) == sorted(["__version__", "AsyncPiHole", "PiHole", "PiHoleAuth"])
    for name in gravitywell.__all__:
        assert hasattr(gravitywell, name), name


def test_models_exports() -> None:
    assert sorted(gravitywell.models.__all__) == sorted(
        [
            "BaseResponse",
            "BlockingResponse",
            "ClientSummary",
            "ComponentVersion",
            "DatabaseSummaryResponse",
            "DatabaseTopClient",
            "DatabaseTopClientsResponse",
            "DatabaseTopDomainsResponse",
            "DatabaseUpstream",
            "DatabaseUpstreamsResponse",
            "GravitySummary",
            "QuerySummary",
            "QueryTypesResponse",
            "RecentBlockedResponse",
            "SummaryResponse",
            "TimeRange",
            "TopClient",
            "TopClientsResponse",
            "TopDomain",
            "TopDomainsResponse",
            "Upstream",
            "UpstreamStatistics",
            "UpstreamsResponse",
            "Session",
            "SessionResponse",
            "LocalVersion",
            "VersionResponse",
            "Versions",
        ]
    )
    for name in gravitywell.models.__all__:
        assert hasattr(gravitywell.models, name), name


def test_every_response_model_extends_base_response() -> None:
    responses = [name for name in gravitywell.models.__all__ if name.endswith("Response") and name != "BaseResponse"]
    assert responses
    for name in responses:
        assert issubclass(getattr(gravitywell.models, name), BaseResponse), name


def test_version_is_the_installed_one() -> None:
    assert gravitywell.__version__ == importlib.metadata.version("gravitywell")
