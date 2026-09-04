"""Network attachment template.

Defines the abstract contract for an endpoint's *declared or discovered
homing* onto the testbed's network planes: its test-plane address, its
management-plane address, the name of the leg that test-plane address lives
on, and — for a guest-attached endpoint (one whose test leg sits on a segment
the testbed does not manage) — the declared segment label and subnet.

Distinct from ``NetworkEndpoint``: that is the live role-address query
("give me the WAN address, now"), answered by whatever means the driver
chooses. ``NetworkAttachment`` is homing *metadata* the driver resolves
from its own config or discovers at attach time (e.g. a DHCP lease),
published so consumers never reach into a framework-specific config
object. Archetypes whose drivers already answer addressing via
``NetworkEndpoint`` should not also compose this; it earns its place
where declared homing (segment labels, plane separation) is the
mechanism under test.

All values are vendor-neutral; empty string means undeclared/not homed.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class NetworkAttachment(Protocol):
    """Abstract contract for an endpoint's homing metadata."""

    @property
    def test_ip(self) -> str:
        """The endpoint's test-plane address as a CIDR (e.g. ``"10.1.30.50/24"``),
        empty if not homed to a test segment. May be discovered at attach time
        (e.g. from a DHCP lease) rather than declared."""
        ...

    @property
    def mgmt_ip(self) -> str:
        """The endpoint's management-plane address, empty when undeclared.
        Published so isolation checks never consume a framework-specific
        config object."""
        ...

    @property
    def segment(self) -> str:
        """Declared segment LABEL of a guest attachment — a stable role name
        (e.g. ``"provider-vpn"``), never an address — empty for managed homing
        or when undeclared. Lets tests resolve "the endpoint on segment X" by
        declaration when address facts are foreign-owned or discovered late."""
        ...

    @property
    def subnet(self) -> str:
        """Declared subnet (CIDR) of a guest attachment, empty when undeclared."""
        ...

    @property
    def test_interface(self) -> str:
        """The name of this endpoint's leg on the test segment — the interface
        ``test_ip`` lives on — as the endpoint's own ``IpInterface`` keys it (an
        endpoint whose test leg sits in a namespace publishes its in-namespace
        name). Empty when the endpoint has no test leg."""
        ...
