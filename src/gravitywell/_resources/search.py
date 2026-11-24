"""The search endpoint, under `/search`."""

from typing import Annotated

from clientx import AsyncResource, Query, Resource, method

from gravitywell.models import SearchResponse


class Search(Resource, prefix="/search", tags=["search"]):
    """Look up how the Pi-hole treats a domain."""

    @method.get("/{domain}")
    def lists(
        self,
        domain: str,
        partial: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(alias="N", ge=1, le=10_000)] = 20,
    ) -> SearchResponse:
        """Find the allow/deny rules and list entries that match a domain.

        Use it to explain why a domain is blocked or allowed. It searches the
        Pi-hole's allow and deny rules, exact domains and regexes that match,
        and the entries of its subscribed blocklists and allowlists, including
        ABP-style entries for a parent domain (`||example.com^`). The first
        match in this order decides: an allow rule, an exact deny rule, an
        allowlist entry, then a blocklist entry or a regex deny rule. A rule
        or list that's disabled, or not in a client's groups, doesn't apply
        to that client. It changes nothing.

        Args:
            domain: The domain to look up, such as `doubleclick.net`, in any
                case. International names work too.
            partial: `true` to also find entries that contain `domain`, such
                as every domain with `doubleclick` in it. It may miss complex
                regexes.
            count: The most results to return of each kind, from 1 to
                10,000. 20 by default; `results` counts every match.
        """
        ...


class AsyncSearch(AsyncResource, prefix="/search", tags=["search"]):
    """Look up how the Pi-hole treats a domain."""

    @method.get("/{domain}")
    async def lists(
        self,
        domain: str,
        partial: Annotated[bool, Query()] = False,
        count: Annotated[int, Query(alias="N", ge=1, le=10_000)] = 20,
    ) -> SearchResponse:
        """Find the allow/deny rules and list entries that match a domain.

        Use it to explain why a domain is blocked or allowed. It searches the
        Pi-hole's allow and deny rules, exact domains and regexes that match,
        and the entries of its subscribed blocklists and allowlists, including
        ABP-style entries for a parent domain (`||example.com^`). The first
        match in this order decides: an allow rule, an exact deny rule, an
        allowlist entry, then a blocklist entry or a regex deny rule. A rule
        or list that's disabled, or not in a client's groups, doesn't apply
        to that client. It changes nothing.

        Args:
            domain: The domain to look up, such as `doubleclick.net`, in any
                case. International names work too.
            partial: `true` to also find entries that contain `domain`, such
                as every domain with `doubleclick` in it. It may miss complex
                regexes.
            count: The most results to return of each kind, from 1 to
                10,000. 20 by default; `results` counts every match.
        """
        ...
