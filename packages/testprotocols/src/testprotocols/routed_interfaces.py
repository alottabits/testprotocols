"""Routed-interface (SVI / routed port / loopback) configuration."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch_routing import RoutedInterface


@runtime_checkable
class RoutedInterfaces(Protocol):
    """Abstract contract for L3 interface configuration.

    Scope is the default VRF; multi-VRF is deferred (GAPS.md). A product whose
    SVIs are gateway-anchored or standalone-only raises unsupported-capability on
    the unsupported facets.
    """

    def list_interfaces(self) -> list[RoutedInterface]:
        """Return every routed interface."""
        ...

    def get_interface(self, name: str) -> RoutedInterface:
        """Return the routed interface *name*. Raises KeyError if absent."""
        ...

    def set_interface(self, interface: RoutedInterface) -> None:
        """Create or replace the routed interface ``interface.name``."""
        ...
