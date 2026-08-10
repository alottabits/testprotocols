"""Site-to-site VPN template — managed SD-WAN appliance.

Defines the abstract contract for an appliance's participation in the
site-to-site VPN overlay: its role (hub / spoke / disabled), the hubs a
spoke connects to (including whether the default route points into the
overlay), the local subnets advertised into the overlay, and a read of peer
reachability.

The configuration is one ``SiteToSiteVpnConfig`` read and replaced whole —
role and hubs are semantically coupled (hubs are only meaningful for a
spoke), and a managed appliance exposes overlay participation as a single
configuration surface. "Point the default route into the overlay" is a
config edit: get, flip ``use_default_route`` on a hub entry, set.

Mapping pattern — relational role models: on some management planes the
role is not stored on the device. Hub-ness exists only relationally (an
edge *is* a hub because other sites' configs reference it), and the
default-route intent is a backhaul designation rather than a per-hub flag.
A driver for such a product synthesizes the role on read (referenced as
hub anywhere → ``HUB``; overlay enabled with hub list → ``SPOKE``) and on
write registers/dereferences the device in the relevant site configs. The
round-trip is intent-preserving even where the stored shape differs.

In scope: overlay participation (role, hubs + default route, subnets),
overlay exclusions (flow-level membership carve-outs — local breakout),
peer status, and observed overlay path quality per local uplink
(``get_vpn_path_metrics`` — the *tunnel* quantity, distinct from the
underlay probe metrics on ``Router.get_wan_path_metrics``; see SPLITS.md).
Overlay *membership* — which flows are in the overlay at all
(role, hubs + default route, subnets, exclusions) — lives here; path
selection *within* a domain (e.g. which overlay uplink, or which internet
uplink) lives in ``sdwan_policy_manager``.

Out of scope: VPN-scoped firewall rules (see ``l3_firewall``), IPsec crypto
parameters (no driving test; highly vendor-divergent — add on evidence),
path steering across the overlay (see ``sdwan_policy_manager``), and
third-party / non-overlay tunnels (add on evidence).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import (
    FlowMatch,
    SiteToSiteVpnConfig,
    VpnPeerStatus,
)
from testprotocols.models.wan_edge import PathMetrics


@runtime_checkable
class SiteToSiteVpn(Protocol):
    """Abstract contract for an appliance's site-to-site VPN overlay."""

    def set_vpn_config(self, config: SiteToSiteVpnConfig) -> None:
        """Replace the appliance's overlay participation with *config*.

        The config is complete — role, hubs (spoke only, priority order),
        and subnet advertisement — and replaces the previous state whole.
        """
        ...

    def get_vpn_config(self) -> SiteToSiteVpnConfig:
        """Return the current overlay-participation configuration."""
        ...

    def get_vpn_peers(self) -> list[VpnPeerStatus]:
        """Return the observed status of every site-to-site VPN peer.

        Empty list when the device participates in no overlay.
        """
        ...

    def get_vpn_exclusions(self) -> list[FlowMatch]:
        """Return the flow matches excluded from the overlay (local breakout).

        Flows matching an entry bypass the site-to-site overlay and egress
        the local uplink, even when an overlay route — including an overlay
        default learned from a routing protocol — covers the destination.
        Empty list when every flow is eligible for overlay routing.
        """
        ...

    def set_vpn_exclusions(self, rules: list[FlowMatch]) -> None:
        """Replace the overlay-exclusion rule set with *rules*.

        Whole-replace; read-modify-write is the caller's responsibility.
        Products that cannot express a constrained field (e.g. source-side
        matches) raise rather than approximate. Vendor rule kinds outside
        this contract (e.g. application-based exclusions) are preserved
        unchanged by the driver.
        """
        ...

    def get_vpn_path_metrics(
        self, timespan_s: int, peer: str | None = None
    ) -> dict[str, PathMetrics]:
        """Return observed overlay path quality per local uplink.

        Keyed by local uplink name (``PathMetrics.link_name`` repeats the
        key); aggregated over every overlay peer, or over the single peer
        named by *peer* (its testbed-level site name, as ``get_vpn_peers``
        reports it). This is the **tunnel** quantity — the path quality the
        product's own overlay steering evaluates — not the underlay probe
        metrics of ``Router.get_wan_path_metrics``.

        *timespan_s* is explicit because products report this as a windowed
        aggregate: the caller owns the freshness/staleness trade and sizes
        its observation intervals beyond the product's reporting lag. An
        uplink absent from the result carried no measured overlay path in
        the window — presence is itself evidence a tunnel rode that uplink.
        Empty dict when the device participates in no overlay.
        """
        ...
