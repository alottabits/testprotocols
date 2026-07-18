"""DHCP / Client template.

Defines the abstract contract for DHCP client operations including lease
release and renewal for both IPv4 and IPv6, and the scoped lease observation
that validates a served scope's option contents from the client side.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from testprotocols.models.dhcp import DhcpLeaseObservation


@runtime_checkable
class DhcpClient(Protocol):
    """Abstract contract for DHCP client operations."""

    def release_dhcp(self, interface: str) -> None:
        """Release the DHCPv4 lease on *interface*."""
        ...

    def renew_dhcp(self, interface: str) -> None:
        """Renew the DHCPv4 lease on *interface*."""
        ...

    def release_ipv6(self, interface: str, stateless: bool = False) -> None:
        """Release the DHCPv6 lease on *interface*."""
        ...

    def renew_ipv6(self, interface: str, stateless: bool = False) -> None:
        """Renew the DHCPv6 lease on *interface*."""
        ...

    def observe_lease(
        self, interface: str, request_options: Sequence[int] = ()
    ) -> DhcpLeaseObservation:
        """Obtain a fresh DHCPv4 lease on *interface* as a scoped observation.

        Performs a full DHCP exchange that explicitly requests every option
        code in *request_options* (on top of the core lease parameters — a
        DHCP server only answers the options a client asks for), WITHOUT
        altering the interface's configured addressing: the lease exists as
        an observation record, not as interface state. Returns the received
        lease with its raw option values. The caller closes the observation
        with :meth:`release_observed_lease`. Raises if no lease is granted.
        """
        ...

    def release_observed_lease(self, interface: str) -> None:
        """Release the lease obtained by :meth:`observe_lease` (idempotent).

        Sends a DHCP release for the observed lease and discards the
        observation record. A no-op when no observed lease is outstanding.
        """
        ...
