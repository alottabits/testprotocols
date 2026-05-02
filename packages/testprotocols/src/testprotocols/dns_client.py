"""DNS / Client template.

Defines the abstract contract for DNS client operations including
name resolution lookups.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DnsClient(Protocol):
    """Abstract contract for DNS client operations."""

    def dns_lookup(
        self,
        domain_name: str,
        record_type: str,
        opts: str = "",
    ) -> list[dict[str, Any]]:
        """Perform a DNS lookup for *domain_name* and return matching records."""
        ...
