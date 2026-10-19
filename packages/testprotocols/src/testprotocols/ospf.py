"""OSPF dynamic-routing configuration (whole-config replace)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch_routing import OspfConfig


@runtime_checkable
class Ospf(Protocol):
    """Abstract contract for OSPF configuration.

    A product that runs OSPF only on a gateway (not the L3 switch) raises
    unsupported-capability.
    """

    def set_ospf_config(self, config: OspfConfig) -> None:
        """Replace the OSPF configuration.

        A write rejected at any step raises naming the step; the driver puts
        nothing back. The state is then the as-found OSPF configuration where
        the family commits atomically, otherwise the steps applied before the
        rejection.
        """
        ...

    def get_ospf_config(self) -> OspfConfig:
        """Return the OSPF configuration."""
        ...
