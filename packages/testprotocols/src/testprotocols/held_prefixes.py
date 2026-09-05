"""Held-prefixes template — hold an address on an interface of the device's own.

Defines the abstract contract for a testbed instrument that *holds* a prefix
behind itself: it takes a caller-supplied host address (``host/prefixlen``) on a
loopback-class interface it allocates, so the prefix becomes a connected,
locally-originated network the instrument answers for. A routing peer that must
advertise, or be the static next hop for, a network that exists only behind it
uses this to make that network real.

A host/substrate instrument capability, distinct from
``ip_interface.IpInterface``: that contract addresses an interface the caller
names; this one allocates the interface itself and is keyed on the address, so a
caller never learns or spells an interface name, and releasing one held address
never disturbs another. Advertising a held prefix is a different contract
(``bgp.Bgp`` ``advertised_networks``, or a static route on the device that must
reach it); this capability only holds.

Scope is exactly "hold / release / list held addresses". Addresses are
``host/prefixlen`` strings compared normalized; holding an address already held
and releasing one not held are both no-ops.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class HeldPrefixes(Protocol):
    """Abstract contract for holding addresses on interfaces of the device's own."""

    def hold(self, address: str) -> None:
        """Hold *address* (``"host/prefixlen"``, e.g. ``"203.0.113.1/24"``) on an
        interface of the device's own — a loopback-class interface the device
        allocates — so the prefix becomes connected/local. Idempotent on the
        normalized address: holding an address already held is a no-op."""
        ...

    def release(self, address: str) -> None:
        """Stop holding *address*; a no-op when it is not held. Releases exactly
        that address — other held addresses stay in force."""
        ...

    def held(self) -> list[str]:
        """Every address currently held, normalized ``"host/prefixlen"``; ``[]``
        when none."""
        ...
