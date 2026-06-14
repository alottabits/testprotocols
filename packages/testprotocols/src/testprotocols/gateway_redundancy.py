"""First-hop gateway redundancy — virtual IP + role per group."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch_routing import RedundancyGroup


@runtime_checkable
class GatewayRedundancy(Protocol):
    """Abstract contract for first-hop redundancy.

    Normalized to a virtual-IP + role group so VRRP, HSRP, and warm-spare map
    onto one concept. A product with no switch-side FHR raises
    unsupported-capability.
    """

    def list_groups(self) -> list[RedundancyGroup]:
        """Return every redundancy group."""
        ...

    def get_group(self, group_id: int) -> RedundancyGroup:
        """Return the redundancy group *group_id*. Raises KeyError if absent."""
        ...

    def set_group(self, group: RedundancyGroup) -> None:
        """Create or replace the redundancy group ``group.group_id``."""
        ...
