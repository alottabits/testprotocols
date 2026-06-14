"""Link-aggregation (LAG) configuration by member ports + mode."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import LinkAggregationGroup


@runtime_checkable
class LinkAggregation(Protocol):
    """Abstract contract for LAG configuration."""

    def list_groups(self) -> list[LinkAggregationGroup]:
        """Return every aggregation group."""
        ...

    def set_group(self, group: LinkAggregationGroup) -> None:
        """Create or replace the group ``group.name``."""
        ...

    def remove_group(self, name: str) -> None:
        """Remove the group *name*."""
        ...
