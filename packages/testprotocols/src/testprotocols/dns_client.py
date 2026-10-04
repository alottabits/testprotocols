"""DNS / Client template.

Defines the abstract contract for DNS client operations including
name resolution lookups.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from testprotocols.models.networking import DnsRecord, DnsRecordType


@runtime_checkable
class DnsClient(Protocol):
    """Abstract contract for DNS client operations."""

    def dns_lookup(
        self,
        domain_name: str,
        record_type: DnsRecordType | str,
        opts: str = "",
    ) -> list[dict[str, Any]]:
        """Deprecated: use :meth:`resolve`, which returns typed records.

        Performs a DNS lookup for *domain_name* and returns the resolver's parsed responses.
        A driver keeps its released output here until the removal step (it warns with
        ``warn_renamed("dns_lookup", "resolve")``): the responses carry more than the answer
        records :meth:`resolve` returns, so they cannot be rebuilt from them.

        *record_type* is a :class:`~testprotocols.models.DnsRecordType`. A plain ``str``
        naming a member (``"A"``) is deprecated: the driver converts it and warns. The
        annotation stays ``DnsRecordType | str`` until the removal step, as a record type the
        enum does not name yet (``"CAA"``) is still passed as text. ``DnsRecordType.OTHER``
        names no record type and is refused (``ValueError``).

        *opts* (extra resolver options) is deprecated with no typed replacement: no caller
        was seen to pass a particular option, and :meth:`resolve` takes none. A driver warns
        when it is non-empty.
        """
        ...

    def resolve(self, domain_name: str, record_type: DnsRecordType) -> list[DnsRecord]:
        """Look up *domain_name* for *record_type* and return the answer records, in answer
        order (a ``CNAME`` chain included); ``[]`` when the answer is empty.
        ``DnsRecordType.OTHER`` is refused (``ValueError``)."""
        ...
