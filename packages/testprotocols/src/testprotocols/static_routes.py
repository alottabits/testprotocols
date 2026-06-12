"""Static-route template — WAN edge (twin and managed appliance).

Defines the abstract contract for testbed-managed static routes: per-entry
CRUD keyed by ``StaticRoute.name``, plus a config-view read-back. All
reviewed management planes store static routes as individual objects, so the
contract is per-entry CRUD — deliberately not the whole-list-replace shape
used by the firewall/steering policies.

``list_static_routes`` returns the *configured* entries (config view);
the *operational* routing table (RIB) read stays on
``router.Router.get_routing_table``.

In scope: add/update, remove, and list testbed-managed static routes.

Out of scope: RIB reads (see ``router``), dynamic routing — BGP — (deferred
in GAPS.md), and policy-based routing / steering (see
``sdwan_policy_manager``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import StaticRoute


@runtime_checkable
class StaticRoutes(Protocol):
    """Abstract contract for a WAN edge's testbed-managed static routes."""

    def add_static_route(self, route: StaticRoute) -> None:
        """Create the route, or update it in place if ``route.name`` exists.

        Idempotent by name — repeating a call converges to the same state.
        """
        ...

    def remove_static_route(self, name: str) -> None:
        """Remove the route named *name*.

        Raises KeyError if no route with that name exists.
        """
        ...

    def list_static_routes(self) -> list[StaticRoute]:
        """Return the configured static routes (config view, not the RIB)."""
        ...
