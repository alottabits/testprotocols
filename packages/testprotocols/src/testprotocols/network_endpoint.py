"""Network endpoint template.

Defines the abstract contract for a *logical* network endpoint's identity
— the address a peer would use to reach a device's named role (the CPE's
WAN side, a server's data-plane interface, etc.). Distinct from
``IpInterface``, which is the per-physical-interface query surface:
``NetworkEndpoint`` is what the test wants ("give me the WAN address"),
``IpInterface`` is one of the things a driver might use under the hood
to satisfy it.

Drivers attach one ``NetworkEndpoint`` per logical role they expose, so
the device shape remains a clean aggregation of capability namespaces
rather than accreting role-specific accessor methods.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class NetworkEndpoint(Protocol):
    """Abstract contract for a logical network endpoint's identity."""

    def get_ipv4_addr(self) -> str:
        """Return the IPv4 address for this logical endpoint.

        The resolution strategy is driver-internal: it may query a live
        interface, read inventory metadata, lift a value from a TR-069
        data model, etc. Callers see only the address.
        """
        ...
