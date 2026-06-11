"""Content-filtering template — URL / category blocking for a managed appliance.

Defines the abstract contract for an SD-WAN appliance's web content filter:
blocking by normalized content category and by explicit allow/block URL
patterns.

Categories are the normalized ``ContentCategory`` taxonomy owned by commons; the
driver maps each to its product's category id. URL patterns are free strings
(host / glob patterns), passed through to the appliance.

In scope: the blocked-category set and the allow / block URL-pattern lists.

Out of scope: application-aware (L7) rules (see ``l7_firewall``) and L3 5-tuple
filtering (see ``l3_firewall``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import ContentCategory


@runtime_checkable
class ContentFiltering(Protocol):
    """Abstract contract for an appliance's web content filter."""

    def set_blocked_categories(self, categories: list[ContentCategory]) -> None:
        """Replace the set of blocked content categories with *categories*."""
        ...

    def get_blocked_categories(self) -> list[ContentCategory]:
        """Return the currently blocked content categories."""
        ...

    def set_url_rules(self, allowed: list[str], blocked: list[str]) -> None:
        """Replace the explicit allow / block URL-pattern lists.

        *allowed* takes precedence over both *blocked* and category blocks, per
        the usual content-filter precedence; the driver maps that intent to its
        product's allow/deny-list semantics.
        """
        ...

    def get_url_rules(self) -> tuple[list[str], list[str]]:
        """Return ``(allowed, blocked)`` URL-pattern lists."""
        ...
