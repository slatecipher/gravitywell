"""The Pydantic models of the Pi-hole's request and response bodies.

Example:
    import os

    from gravitywell import PiHole, PiHoleAuth
    from gravitywell.models import VersionResponse

    auth = PiHoleAuth(os.environ["PIHOLE_PASSWORD"])
    with PiHole("http://pi.hole", auth=auth) as api:
        body: VersionResponse = api.info.version()
"""

from gravitywell.models._auth import Session, SessionResponse
from gravitywell.models._base import BaseResponse, ProcessedItem, ProcessedItems, ProcessingError
from gravitywell.models._dns import BlockingResponse
from gravitywell.models._domains import (
    ChangedDomainsResponse,
    DomainRule,
    DomainRuleKey,
    DomainsResponse,
    RuleKind,
    RuleType,
)
from gravitywell.models._groups import ChangedGroupsResponse, Group, GroupKey, GroupsResponse
from gravitywell.models._history import (
    ActivityResponse,
    ActivitySlot,
    ClientActivityResponse,
    ClientActivitySlot,
    DatabaseActivityResponse,
    DatabaseActivitySlot,
    DatabaseClientActivityResponse,
    DatabaseClientActivitySlot,
    HistoryClient,
)
from gravitywell.models._info import ComponentVersion, LocalVersion, VersionResponse, Versions
from gravitywell.models._lists import ChangedListsResponse, ListKey, ListsResponse, ListType, SubscribedList
from gravitywell.models._queries import (
    DnssecStatus,
    ExtendedDnsError,
    LoggedQuery,
    QueryClient,
    QueryLogResponse,
    QueryReply,
    QueryStatus,
    QuerySuggestions,
    QuerySuggestionsResponse,
    ReplyType,
)
from gravitywell.models._search import (
    ListMatch,
    ListMatchCounts,
    RuleMatchCounts,
    SearchCounts,
    SearchResponse,
    SearchResults,
)
from gravitywell.models._stats import (
    ClientSummary,
    DatabaseSummaryResponse,
    DatabaseTopClient,
    DatabaseTopClientsResponse,
    DatabaseTopDomainsResponse,
    DatabaseUpstream,
    DatabaseUpstreamsResponse,
    GravitySummary,
    QuerySummary,
    QueryTypesResponse,
    RecentBlockedResponse,
    SummaryResponse,
    TopClient,
    TopClientsResponse,
    TopDomain,
    TopDomainsResponse,
    Upstream,
    UpstreamsResponse,
    UpstreamStatistics,
)
from gravitywell.models._time import TimeRange

__all__ = [
    # gravitywell.models._auth
    "Session",
    "SessionResponse",
    # gravitywell.models._base
    "BaseResponse",
    "ProcessedItem",
    "ProcessedItems",
    "ProcessingError",
    # gravitywell.models._dns
    "BlockingResponse",
    # gravitywell.models._domains
    "ChangedDomainsResponse",
    "DomainRule",
    "DomainRuleKey",
    "DomainsResponse",
    "RuleKind",
    "RuleType",
    # gravitywell.models._groups
    "ChangedGroupsResponse",
    "Group",
    "GroupKey",
    "GroupsResponse",
    # gravitywell.models._history
    "ActivityResponse",
    "ActivitySlot",
    "ClientActivityResponse",
    "ClientActivitySlot",
    "DatabaseActivityResponse",
    "DatabaseActivitySlot",
    "DatabaseClientActivityResponse",
    "DatabaseClientActivitySlot",
    "HistoryClient",
    # gravitywell.models._info
    "ComponentVersion",
    "LocalVersion",
    "VersionResponse",
    "Versions",
    # gravitywell.models._lists
    "ChangedListsResponse",
    "ListKey",
    "ListsResponse",
    "ListType",
    "SubscribedList",
    # gravitywell.models._queries
    "DnssecStatus",
    "ExtendedDnsError",
    "LoggedQuery",
    "QueryClient",
    "QueryLogResponse",
    "QueryReply",
    "QueryStatus",
    "QuerySuggestions",
    "QuerySuggestionsResponse",
    "ReplyType",
    # gravitywell.models._search
    "ListMatch",
    "ListMatchCounts",
    "RuleMatchCounts",
    "SearchCounts",
    "SearchResponse",
    "SearchResults",
    # gravitywell.models._stats
    "ClientSummary",
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
    "TopClient",
    "TopClientsResponse",
    "TopDomain",
    "TopDomainsResponse",
    "Upstream",
    "UpstreamStatistics",
    "UpstreamsResponse",
    # gravitywell.models._time
    "TimeRange",
]
