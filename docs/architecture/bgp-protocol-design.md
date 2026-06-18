# Design: WAN-edge `Bgp` capability

| Field   | Value                                                              |
| ------- | ------------------------------------------------------------------ |
| Status  | Implemented                                                        |
| Author  | rjvisser                                                           |
| Date    | 2026-06-12                                                         |
| Related | `packages/testprotocols/GAPS.md` (2026-06-12 BGP entry — resolved by this; the last SD-WAN-round gap), `docs/architecture/sdwan-appliance-protocol-design.md`, `router.py` (read-only), `static_routes.py` (sibling-capability precedent), `models/wan_edge.py::RouteEntry` |

## Purpose

Add the BGP capability missing from the WAN-edge contract: configuration
(local AS + neighbors + advertised networks) and operational reads (neighbor
session state, learned prefixes). Driving evidence: operator acceptance
scope requires BGP peering between the WAN edge and a LAN-side router,
asserting advertised routes on the peer and learned routes on the edge.

This resolves the final GAPS.md entry from the 2026-06-12 SD-WAN seeding
round. Placement follows the `StaticRoutes` precedent: a **sibling
capability** (`bgp: Bgp`) on both WAN-edge archetypes — `Router` stays
read-only-RIB, and dynamic-routing config does not ride on it.

## Conventions

Normalized `StrEnum` vocabularies, dataclass models in
`models/sdwan_appliance.py`, `runtime_checkable` Protocols, and parametrized
conformance tests. The grow-on-evidence rule applies to vendor taxonomies,
not to standardized protocol states. `mypy --strict` clean.

## Models (`models/sdwan_appliance.py`)

```python
class BgpSessionState(StrEnum):
    """BGP FSM state of a neighbor session.

    The RFC 4271 state vocabulary — protocol-standard, not vendor-specific,
    so the full set is seeded (the grow-on-evidence rule applies to vendor
    taxonomies, not to standardized protocol states). ``UNKNOWN`` absorbs
    vendor representations that do not map to an FSM state.
    """

    IDLE = "idle"
    CONNECT = "connect"
    ACTIVE = "active"
    OPEN_SENT = "open_sent"
    OPEN_CONFIRM = "open_confirm"
    ESTABLISHED = "established"
    UNKNOWN = "unknown"


@dataclass
class BgpNeighbor:
    """A configured BGP neighbor (minimal — timers/auth/multihop grow on
    evidence)."""

    peer_ip: str
    remote_as: int


@dataclass
class BgpConfig:
    """Complete BGP configuration — read and replaced whole.

    ``enabled`` / ``as_number`` / ``neighbors`` are semantically coupled,
    and most reviewed management planes expose BGP as one object, so the
    surface is whole-config replace (idempotent), not per-neighbor CRUD.
    ``advertised_networks`` lists CIDRs announced to peers; products that
    auto-advertise their overlay subnets and offer no per-network control
    raise unsupported-capability when it is non-empty.
    """

    enabled: bool
    as_number: int
    neighbors: list[BgpNeighbor] = field(default_factory=list)
    advertised_networks: list[str] = field(default_factory=list)


@dataclass
class BgpPeerStatus:
    """Observed status of one BGP neighbor session (read-only).

    ``prefixes_received`` is ``None`` when the product does not report a
    count.
    """

    peer_ip: str
    remote_as: int
    state: BgpSessionState
    prefixes_received: int | None = None
```

## Protocol (`bgp.py`)

```python
@runtime_checkable
class Bgp(Protocol):
    """Abstract contract for a WAN edge's BGP configuration and state."""

    def set_bgp_config(self, config: BgpConfig) -> None:
        """Replace the BGP configuration with *config* (idempotent)."""

    def get_bgp_config(self) -> BgpConfig:
        """Return the current BGP configuration (config read-back)."""

    def get_bgp_neighbors(self) -> list[BgpPeerStatus]:
        """Return the operational status of every configured neighbor.

        Operational read — products without a published BGP state read
        raise unsupported-capability rather than approximating.
        """

    def get_learned_routes(self) -> list[RouteEntry]:
        """Return BGP-learned prefixes (operational read; same convention).

        Reuses ``wan_edge.RouteEntry``; ``gateway`` carries the peer
        next-hop and ``interface`` may be empty when not reported.
        """
```

**Config/read split at method granularity:** config write + read-back are
universal (5/5 — even the family without operational reads has a config
GET); only the two *operational* reads carry the unsupported-capability
convention (4/5).

Module docstring scope — In scope: BGP process config (whole-replace),
neighbor session status, learned-prefix read. Out of scope: RIB reads
(`router.get_routing_table`), static routes (`static_routes`), route
maps/filters and per-neighbor policy (grow on evidence), other dynamic
protocols (OSPF — no driving test).

## Archetypes (`devices/sdwan.py`)

`bgp: Bgp` added to **both** `SdwanRouterDevice` and `SdwanApplianceDevice`,
directly after `static_routes` in each. Both device-type gate tests
extended. Conformance entry in `tests/test_wan_edge_templates.py` (shared
WAN-edge surface, beside `Router`/`WanLinkAdmin`/`StaticRoutes`).

## Cross-vendor concept check (public API references)

| Intent | Meraki MX | Catalyst SD-WAN | FortiGate | Prisma SD-WAN | Arista (VeloCloud) |
|---|---|---|---|---|---|
| BGP config (write + read-back) | `appliance/vpn/bgp` GET/PUT (enabled, asNumber, neighbors) | BGP feature template / Service-profile BGP parcel | `router/bgp` singleton + neighbor table | element `bgppeers` CRUD | `deviceSettings` `device_settings_bgp` (neighbors/networks/filters) |
| neighbor session status | **✗** (no published read) | `/device/bgp/neighbors` | routing monitor (BGP neighbors) | `bgppeers/status` | `monitoring/getEnterpriseBgpPeerStatus` |
| learned prefixes | **✗** | `/device/bgp/routes` | `monitor/router/ipv4` (type=bgp) | `bgppeers/{id}/reachableprefixes` | enterprise route table (BGP-learned entries) |

Config 5/5; operational reads 4/5 — handled per method by the
unsupported-capability convention, consistent with the design doc's v2
posture (the one family's learned-route verification stays a manual
dashboard step). Endpoint names stay in docs; only normalized intent enters
the package.

## Error handling

Unsupported-capability per the framework convention on the operational
reads and on `advertised_networks` where a product cannot comply. No new
error types; no KeyError semantics needed (whole-config replace).
