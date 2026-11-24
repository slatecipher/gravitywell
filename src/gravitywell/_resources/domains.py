"""The domain management endpoints, under `/domains`."""

from typing import Annotated

from clientx import AsyncResource, Json, Resource, method
from clientx.tools import ToolOptions

from gravitywell.models import ChangedDomainsResponse, DomainRuleKey, DomainsResponse, RuleKind, RuleType

# A POST, so AI tools would treat it as neither: it deletes, and deleting the
# same rules again changes nothing more.
_BATCH_DELETE = ToolOptions(destructive=True, idempotent=True)


class DomainsBatch(Resource):
    """Change several domain rules at once."""

    # The full path: ClientX joins a prefix and `:batchDelete` with a slash
    # (ClientX #173).
    @method.post("/domains:batchDelete", tool_options=_BATCH_DELETE)
    def delete(self, rules: Annotated[list[DomainRuleKey], Json()]) -> None:
        """Delete several allow or deny rules at once.

        It takes effect right away. Rules that don't exist are skipped, but if
        none of them exists, it answers with an error (404).

        Args:
            rules: The rules to delete, each by its domain or regex, type and
                kind.
        """
        ...


class Domains(Resource, prefix="/domains"):
    """The Pi-hole's allow and deny rules for domains."""

    batch = DomainsBatch()

    @method.get("/{rule_type}/{rule_kind}/{domain}")
    def get(self, rule_type: RuleType, rule_kind: RuleKind, domain: str) -> DomainsResponse:
        """Fetch one allow or deny rule.

        It returns the rule in a list, or an empty list if there's no such
        rule. It changes nothing.

        Args:
            rule_type: The rule's type: `allow` or `deny`.
            rule_kind: The rule's kind: `exact` or `regex`.
            domain: The rule's domain, or its regex, as `list` shows it, such as
                `ads.example.com`.
        """
        ...

    @method.post("/{rule_type}/{rule_kind}")
    def add(
        self,
        rule_type: RuleType,
        rule_kind: RuleKind,
        domain: Annotated[str | list[str], Json()],
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedDomainsResponse:
        r"""Add allow or deny rules for one or more domains.

        An `allow` rule lets matching domains through, even ones on a
        blocklist; a `deny` rule blocks them. A rule takes effect right away,
        for the clients in its groups. Exact domains are lowercased, and
        international names converted to punycode. Each domain is saved or
        refused on its own, such as one that already has this rule, and
        `processed` says which; if all are refused, it answers with an error.

        Args:
            rule_type: `allow` to let matching domains through, `deny` to
                block them.
            rule_kind: `exact` for the domain alone, or `regex` for a regex
                that matches domains, such as `(\.|^)example\.com$`.
            domain: The domain or regex, or a list of them, such as
                `ads.example.com`.
            comment: A note on the rule, such as `Breaks the banking app`.
            groups: IDs of the groups the rule applies to. Leave it out for
                the Default group, `0`.
            enabled: `false` to add the rule without putting it in effect.
        """
        ...

    @method.put("/{rule_type}/{rule_kind}/{domain}")
    def update(
        self,
        rule_type: RuleType,
        rule_kind: RuleKind,
        domain: str,
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedDomainsResponse:
        """Change an allow or deny rule's comment, groups or state.

        It replaces the rule's settings: a comment left out is removed, and
        `enabled` left out means enabled, while groups left out stay as they
        are. If there's no such rule, it adds one. To change a rule's type or
        kind, use the move endpoint. It takes effect right away.

        Args:
            rule_type: The rule's type: `allow` or `deny`.
            rule_kind: The rule's kind: `exact` or `regex`.
            domain: The rule's domain, or its regex, as `list` shows it, such as
                `ads.example.com`.
            comment: The rule's comment, such as `Breaks the banking app`.
                Leave it out to remove the current one.
            groups: IDs of the groups the rule applies to. Leave it out to
                keep the current ones.
            enabled: `false` to keep the rule but take it out of effect.
        """
        ...

    # Pi-hole moves a rule with a PUT to its new type and kind, naming its
    # current ones in the body.
    @method.put("/{to_type}/{to_kind}/{domain}")
    def move(
        self,
        domain: str,
        from_type: Annotated[RuleType, Json(alias="type")],
        from_kind: Annotated[RuleKind, Json(alias="kind")],
        to_type: RuleType,
        to_kind: RuleKind,
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedDomainsResponse:
        """Move an allow or deny rule to another type or kind.

        For example, move a deny rule to allow to stop blocking its domain.
        It also replaces the rule's settings, as an update does: a comment
        left out is removed, and `enabled` left out means enabled, while
        groups left out stay as they are. If the rule isn't at `from_type`
        and `from_kind`, it adds one at `to_type` and `to_kind` instead. It
        takes effect right away.

        Args:
            domain: The rule's domain, or its regex, as `list` shows it, such as
                `ads.example.com`.
            from_type: The rule's type now: `allow` or `deny`.
            from_kind: The rule's kind now: `exact` or `regex`.
            to_type: The type to move it to: `allow` or `deny`.
            to_kind: The kind to move it to: `exact` or `regex`.
            comment: The rule's comment, such as `Breaks the banking app`.
                Leave it out to remove the current one.
            groups: IDs of the groups the rule applies to. Leave it out to
                keep the current ones.
            enabled: `false` to keep the rule but take it out of effect.
        """
        ...

    @method.delete("/{rule_type}/{rule_kind}/{domain}")
    def delete(self, rule_type: RuleType, rule_kind: RuleKind, domain: str) -> None:
        """Delete an allow or deny rule.

        It takes effect right away. A rule that doesn't exist answers with an
        error (404). To delete several rules at once, use the batch delete.

        Args:
            rule_type: The rule's type: `allow` or `deny`.
            rule_kind: The rule's kind: `exact` or `regex`.
            domain: The rule's domain, or its regex, as `list` shows it, such as
                `ads.example.com`.
        """
        ...

    # Last in the class: a method named `list` hides the builtin for the rest
    # of the class body.
    @method.get()
    def list(self) -> DomainsResponse:
        """Fetch all of the Pi-hole's allow and deny rules for domains.

        Each rule is an exact domain or a regex, allows or denies, and applies
        to the clients in its groups. To find the rules that match one domain,
        the search endpoint is quicker. It changes nothing.
        """
        ...


class AsyncDomainsBatch(AsyncResource):
    """Change several domain rules at once."""

    # The full path: ClientX joins a prefix and `:batchDelete` with a slash
    # (ClientX #173).
    @method.post("/domains:batchDelete", tool_options=_BATCH_DELETE)
    async def delete(self, rules: Annotated[list[DomainRuleKey], Json()]) -> None:
        """Delete several allow or deny rules at once.

        It takes effect right away. Rules that don't exist are skipped, but if
        none of them exists, it answers with an error (404).

        Args:
            rules: The rules to delete, each by its domain or regex, type and
                kind.
        """
        ...


class AsyncDomains(AsyncResource, prefix="/domains"):
    """The Pi-hole's allow and deny rules for domains."""

    batch = AsyncDomainsBatch()

    @method.get("/{rule_type}/{rule_kind}/{domain}")
    async def get(self, rule_type: RuleType, rule_kind: RuleKind, domain: str) -> DomainsResponse:
        """Fetch one allow or deny rule.

        It returns the rule in a list, or an empty list if there's no such
        rule. It changes nothing.

        Args:
            rule_type: The rule's type: `allow` or `deny`.
            rule_kind: The rule's kind: `exact` or `regex`.
            domain: The rule's domain, or its regex, as `list` shows it, such as
                `ads.example.com`.
        """
        ...

    @method.post("/{rule_type}/{rule_kind}")
    async def add(
        self,
        rule_type: RuleType,
        rule_kind: RuleKind,
        domain: Annotated[str | list[str], Json()],
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedDomainsResponse:
        r"""Add allow or deny rules for one or more domains.

        An `allow` rule lets matching domains through, even ones on a
        blocklist; a `deny` rule blocks them. A rule takes effect right away,
        for the clients in its groups. Exact domains are lowercased, and
        international names converted to punycode. Each domain is saved or
        refused on its own, such as one that already has this rule, and
        `processed` says which; if all are refused, it answers with an error.

        Args:
            rule_type: `allow` to let matching domains through, `deny` to
                block them.
            rule_kind: `exact` for the domain alone, or `regex` for a regex
                that matches domains, such as `(\.|^)example\.com$`.
            domain: The domain or regex, or a list of them, such as
                `ads.example.com`.
            comment: A note on the rule, such as `Breaks the banking app`.
            groups: IDs of the groups the rule applies to. Leave it out for
                the Default group, `0`.
            enabled: `false` to add the rule without putting it in effect.
        """
        ...

    @method.put("/{rule_type}/{rule_kind}/{domain}")
    async def update(
        self,
        rule_type: RuleType,
        rule_kind: RuleKind,
        domain: str,
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedDomainsResponse:
        """Change an allow or deny rule's comment, groups or state.

        It replaces the rule's settings: a comment left out is removed, and
        `enabled` left out means enabled, while groups left out stay as they
        are. If there's no such rule, it adds one. To change a rule's type or
        kind, use the move endpoint. It takes effect right away.

        Args:
            rule_type: The rule's type: `allow` or `deny`.
            rule_kind: The rule's kind: `exact` or `regex`.
            domain: The rule's domain, or its regex, as `list` shows it, such as
                `ads.example.com`.
            comment: The rule's comment, such as `Breaks the banking app`.
                Leave it out to remove the current one.
            groups: IDs of the groups the rule applies to. Leave it out to
                keep the current ones.
            enabled: `false` to keep the rule but take it out of effect.
        """
        ...

    # Pi-hole moves a rule with a PUT to its new type and kind, naming its
    # current ones in the body.
    @method.put("/{to_type}/{to_kind}/{domain}")
    async def move(
        self,
        domain: str,
        from_type: Annotated[RuleType, Json(alias="type")],
        from_kind: Annotated[RuleKind, Json(alias="kind")],
        to_type: RuleType,
        to_kind: RuleKind,
        comment: Annotated[str | None, Json()] = None,
        groups: Annotated[list[int] | None, Json()] = None,
        enabled: Annotated[bool, Json()] = True,
    ) -> ChangedDomainsResponse:
        """Move an allow or deny rule to another type or kind.

        For example, move a deny rule to allow to stop blocking its domain.
        It also replaces the rule's settings, as an update does: a comment
        left out is removed, and `enabled` left out means enabled, while
        groups left out stay as they are. If the rule isn't at `from_type`
        and `from_kind`, it adds one at `to_type` and `to_kind` instead. It
        takes effect right away.

        Args:
            domain: The rule's domain, or its regex, as `list` shows it, such as
                `ads.example.com`.
            from_type: The rule's type now: `allow` or `deny`.
            from_kind: The rule's kind now: `exact` or `regex`.
            to_type: The type to move it to: `allow` or `deny`.
            to_kind: The kind to move it to: `exact` or `regex`.
            comment: The rule's comment, such as `Breaks the banking app`.
                Leave it out to remove the current one.
            groups: IDs of the groups the rule applies to. Leave it out to
                keep the current ones.
            enabled: `false` to keep the rule but take it out of effect.
        """
        ...

    @method.delete("/{rule_type}/{rule_kind}/{domain}")
    async def delete(self, rule_type: RuleType, rule_kind: RuleKind, domain: str) -> None:
        """Delete an allow or deny rule.

        It takes effect right away. A rule that doesn't exist answers with an
        error (404). To delete several rules at once, use the batch delete.

        Args:
            rule_type: The rule's type: `allow` or `deny`.
            rule_kind: The rule's kind: `exact` or `regex`.
            domain: The rule's domain, or its regex, as `list` shows it, such as
                `ads.example.com`.
        """
        ...

    # Last in the class: a method named `list` hides the builtin for the rest
    # of the class body.
    @method.get()
    async def list(self) -> DomainsResponse:
        """Fetch all of the Pi-hole's allow and deny rules for domains.

        Each rule is an exact domain or a regex, allows or denies, and applies
        to the clients in its groups. To find the rules that match one domain,
        the search endpoint is quicker. It changes nothing.
        """
        ...
