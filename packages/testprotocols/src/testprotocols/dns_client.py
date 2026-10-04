"""DNS / Client template.

Defines the abstract contract for DNS client operations including
name resolution lookups.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols.models.networking import DnsRecordType


@runtime_checkable
class DnsClient(Protocol):
    """Abstract contract for DNS client operations."""

    def dns_lookup(
        self,
        domain_name: str,
        record_type: DnsRecordType | str,
        opts: str = "",
    ) -> list[dict[str, Any]]:
        """Perform a DNS lookup for *domain_name* and return matching records.

        *record_type* is a :class:`~testprotocols.models.DnsRecordType`. A plain ``str``
        naming a member (``"A"``) is deprecated: the driver converts it and warns. The
        annotation stays ``DnsRecordType | str`` until the removal step, as a record type the
        enum does not name yet (``"CAA"``) is still passed as text.
        """
        ...
