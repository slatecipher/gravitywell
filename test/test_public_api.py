"""The names gravitywell exports.

A change here is a change to the public API.
"""

import importlib.metadata
import re

import pytest

import gravitywell
import gravitywell.models
from gravitywell.models import BaseResponse


def test_package_exports() -> None:
    assert sorted(gravitywell.__all__) == sorted(
        ["__version__", "AsyncPiHole", "PIHOLE_VERSIONS", "PiHole", "PiHoleAuth"]
    )
    for name in gravitywell.__all__:
        assert hasattr(gravitywell, name), name


def test_models_exports() -> None:
    assert sorted(gravitywell.models.__all__) == sorted(
        [
            "ActiveSession",
            "ActiveSessionsResponse",
            "ActivityResponse",
            "ActivitySlot",
            "AllowDenyCounts",
            "AllowedValue",
            "BaseResponse",
            "BlockingResponse",
            "CacheContent",
            "CacheCount",
            "ChangedClientsResponse",
            "ChangedDomainsResponse",
            "ChangedGroupsResponse",
            "ChangedListsResponse",
            "ChangedSettingsResponse",
            "ClientActivityResponse",
            "ClientActivitySlot",
            "ClientCounts",
            "ClientExplanation",
            "ClientKey",
            "ClientSuggestion",
            "ClientSuggestionsResponse",
            "ClientSummary",
            "ClientsResponse",
            "CnameRecord",
            "CnameRecordsResponse",
            "ComponentUpdate",
            "ComponentVersion",
            "ConfigSetting",
            "ConfigSettingsResponse",
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
            "DeviceAddress",
            "DhcpLease",
            "DhcpLeases",
            "DhcpLeasesResponse",
            "DhcpMetrics",
            "DiagnosisMessage",
            "DnsCache",
            "DnsMetrics",
            "DnsRecord",
            "DnsRecordsResponse",
            "DnsReplies",
            "DnssecStatus",
            "DomainExplanation",
            "DomainRule",
            "DomainRuleKey",
            "DomainsResponse",
            "EnabledCount",
            "ExtendedDnsError",
            "FtlInfo",
            "FtlInfoResponse",
            "FtlUsage",
            "Gateway",
            "GatewayResponse",
            "GravityCounts",
            "GravitySummary",
            "GravityTables",
            "GravityUpdate",
            "Group",
            "GroupKey",
            "GroupsResponse",
            "HealthReport",
            "HistoryClient",
            "HostInfo",
            "HostInfoResponse",
            "InterfaceAddress",
            "InterfaceStats",
            "InterfaceTraffic",
            "InterfacesResponse",
            "ListKey",
            "ListMatch",
            "ListMatchCounts",
            "ListType",
            "ListsResponse",
            "LocalVersion",
            "LogLine",
            "LogResponse",
            "LoggedQuery",
            "MemoryUsage",
            "MessageCountResponse",
            "MessagesResponse",
            "Metrics",
            "MetricsResponse",
            "NetworkDevice",
            "NetworkDevicesResponse",
            "NetworkInterface",
            "PaddCache",
            "PaddConfig",
            "PaddInterface",
            "PaddInterfaces",
            "PaddQueries",
            "PaddResponse",
            "PaddSensors",
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
            "RemoteVersion",
            "ReplyType",
            "RestoreParts",
            "RestoreResponse",
            "ReverseServer",
            "ReverseServersResponse",
            "Route",
            "RoutesResponse",
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
            "SessionTls",
            "StaticLease",
            "StaticLeasesResponse",
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
            "UpstreamServersResponse",
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


def test_mcp_exports() -> None:
    import gravitywell.mcp

    assert gravitywell.mcp.__all__ == ["create_server", "main"]


def test_version_is_the_installed_one() -> None:
    assert gravitywell.__version__ == importlib.metadata.version("gravitywell")


def test_pihole_versions_name_each_component_and_cannot_change() -> None:
    assert list(gravitywell.PIHOLE_VERSIONS) == ["core", "web", "ftl"]
    for component in gravitywell.PIHOLE_VERSIONS.values():
        assert re.fullmatch(r"v6\.\d+(\.\d+)?", component), component
    with pytest.raises(TypeError):
        gravitywell.PIHOLE_VERSIONS["ftl"] = "v7.0"  # pyright: ignore[reportIndexIssue]
