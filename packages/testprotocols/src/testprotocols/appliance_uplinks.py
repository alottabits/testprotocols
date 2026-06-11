"""WAN uplink template — managed SD-WAN appliance.

Defines the abstract contract for observing an appliance's WAN uplinks: their
operational state and addressing. Read-only — uplink *configuration* (static vs
DHCP, PPPoE, etc.) is a separate concern not yet modelled (add on evidence).

This replaces, for a managed appliance, the Linux-host ``ip_interface`` surface
(per-interface ``ip addr``/``link``/``mtu``/``mac``) which a cloud-managed
appliance does not expose.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import UplinkStatus


@runtime_checkable
class ApplianceUplinks(Protocol):
    """Abstract contract for observing an appliance's WAN uplinks."""

    def get_uplinks(self) -> list[UplinkStatus]:
        """Return the status of every WAN uplink."""
        ...

    def get_uplink(self, name: str) -> UplinkStatus:
        """Return the status of the named uplink (e.g. ``"wan1"``).

        Raises KeyError if no uplink with that name exists.
        """
        ...
