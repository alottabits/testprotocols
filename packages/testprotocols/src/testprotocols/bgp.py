"""BGP template — WAN edge (twin and managed appliance).

Defines the abstract contract for a WAN edge's BGP: whole-replace
configuration (local AS + neighbors + advertised networks) plus operational
reads of neighbor session state and learned prefixes.

The config/read split is deliberate and per-method: configuration write and
read-back are universal across the reviewed management planes, while the
two *operational* reads are not — a product without a published BGP state
read raises unsupported-capability on those methods rather than
approximating.

In scope: BGP process configuration (whole-replace, idempotent), neighbor
session status, learned-prefix read.

Out of scope: RIB reads (see ``router``), static routes (see
``static_routes``), route maps / filters / per-neighbor policy (grow on
evidence), and other dynamic routing protocols (no driving test).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import BgpConfig, BgpPeerStatus
from testprotocols.models.wan_edge import RouteEntry


@runtime_checkable
class Bgp(Protocol):
    """Abstract contract for a WAN edge's BGP configuration and state."""

    def set_bgp_config(self, config: BgpConfig) -> None:
        """Replace the BGP configuration with *config* (idempotent)."""
        ...

    def get_bgp_config(self) -> BgpConfig:
        """Return the current BGP configuration (config read-back)."""
        ...

    def get_bgp_neighbors(self) -> list[BgpPeerStatus]:
        """Return the operational status of every configured neighbor.

        Operational read — products without a published BGP state read
        raise unsupported-capability rather than approximating.
        """
        ...

    def get_learned_routes(self) -> list[RouteEntry]:
        """Return BGP-learned prefixes (operational read; same convention).

        ``gateway`` carries the peer next-hop; ``interface`` may be empty
        when not reported.
        """
        ...
