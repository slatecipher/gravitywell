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
            "ActivityResponse",
            "ActivitySlot",
            "AllowDenyCounts",
            "BaseResponse",
            "BlockingResponse",
            "CacheContent",
            "CacheCount",
            "ChangedClientsResponse",
            "ChangedDomainsResponse",
            "ChangedGroupsResponse",
            "ChangedListsResponse",
            "ClientActivityResponse",
            "ClientActivitySlot",
            "ClientCounts",
            "ClientKey",
            "ClientSuggestion",
            "ClientSuggestionsResponse",
            "ClientSummary",
            "ClientsResponse",
            "ComponentVersion",
            "ConfiguredClient",
            "CpuLoad",
            "CpuUsage",
            "DatabaseActivityResponse",
            "DatabaseActivitySlot",
            "DatabaseClientActivityResponse",
            "DatabaseClientActivitySlot",
            "DatabaseInfoResponse",
            "DatabaseSummaryResponse",
            "DatabaseTopClient",
            "DatabaseTopClientsResponse",
            "DatabaseTopDomainsResponse",
            "DatabaseUpstream",
            "DatabaseUpstreamsResponse",
            "DhcpLeases",
            "DhcpMetrics",
            "DiagnosisMessage",
            "DnsCache",
            "DnsMetrics",
            "DnsReplies",
            "DnssecStatus",
            "DomainRule",
            "DomainRuleKey",
            "DomainsResponse",
            "EnabledCount",
            "ExtendedDnsError",
            "FtlInfo",
            "FtlInfoResponse",
            "FtlUsage",
            "GravityCounts",
            "GravitySummary",
            "Group",
            "GroupKey",
            "GroupsResponse",
            "HistoryClient",
            "HostInfo",
            "HostInfoResponse",
            "ListKey",
            "ListMatch",
            "ListMatchCounts",
            "ListType",
            "ListsResponse",
            "LocalVersion",
            "LoggedQuery",
            "MemoryUsage",
            "MessageCountResponse",
            "MessagesResponse",
            "Metrics",
            "MetricsResponse",
            "ProcessedItem",
            "ProcessedItems",
            "ProcessingError",
            "QueryClient",
            "QueryLogResponse",
            "QueryReply",
            "QueryStatus",
            "QuerySuggestions",
            "QuerySuggestionsResponse",
            "QuerySummary",
            "QueryTypesResponse",
            "RamUsage",
            "RecentBlockedResponse",
            "ReplyType",
            "RuleKind",
            "RuleMatchCounts",
            "RuleType",
            "SearchCounts",
            "SearchResponse",
            "SearchResults",
            "Sensor",
            "Sensors",
            "SensorsResponse",
            "Session",
            "SessionResponse",
            "SubscribedList",
            "SummaryResponse",
            "SwapUsage",
            "SystemInfo",
            "SystemInfoResponse",
            "Temperature",
            "TimeRange",
            "TopClient",
            "TopClientsResponse",
            "TopDomain",
            "TopDomainsResponse",
            "Uname",
            "Upstream",
            "UpstreamStatistics",
            "UpstreamsResponse",
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
