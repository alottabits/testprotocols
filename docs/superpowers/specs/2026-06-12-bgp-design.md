# Design: `Bgp` capability seed

| Field   | Value                                                              |
| ------- | ------------------------------------------------------------------ |
| Status  | Approved for implementation                                         |
| Author  | rjvisser                                                            |
| Date    | 2026-06-12                                                          |
| Related | `GAPS.md` (2026-06-12 BGP entry — resolved by this; the last SD-WAN-round gap), `docs/sdwan-appliance-protocol-design.md`, `router.py` (read-only), `static_routes.py` (sibling-capability precedent), `models/wan_edge.py::RouteEntry` |

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

## Constraints

- No customer/test-suite names in package source, tests, tracking files,
  commit messages, or this spec; vendor names only in `docs/` and
  `GAPS.md`/`SPLITS.md` with public-API citations.
- `mypy --strict`; established conventions (StrEnum vocabularies, dataclass
  models in `models/sdwan_appliance.py`, parametrized conformance tests,
  vendor-isolation grep).
- **Adding a required archetype attribute is conformance-breaking** for both
  existing device implementations — the Linux digital twin (vitro-bdd
  `examples/sdwan-digital-twin`) and the MX driver (the MX-driver testbed
  repo). Both are migrated **in step** (same working session).
- All python via each repo's `.venv-3.12`.

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

## Protocol (`bgp.py`, new)

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

**Config/read split at method granularity** (the GAPS design-note demand):
config write + read-back are universal (5/5 — even the family without
operational reads has a config GET); only the two *operational* reads carry
the unsupported-capability convention (4/5).

Module docstring: In scope — BGP process config (whole-replace), neighbor
session status, learned-prefix read. Out of scope — RIB reads
(`router.get_routing_table`), static routes (`static_routes`), route
maps/filters and per-neighbor policy (grow on evidence), other dynamic
protocols (OSPF — no driving test).

## Archetypes (`devices/sdwan.py`)

`bgp: Bgp` added to **both** `SdwanRouterDevice` and `SdwanApplianceDevice`,
directly after `static_routes` in each. Both device-type gate tests
extended. Conformance entry in `tests/test_wan_edge_templates.py` (shared
WAN-edge surface, beside `Router`/`WanLinkAdmin`/`StaticRoutes`).

## Cross-vendor concept check (public API references — docs only)

| Intent | Meraki MX | Catalyst SD-WAN | FortiGate | Prisma SD-WAN | Arista (VeloCloud) |
|---|---|---|---|---|---|
| BGP config (write + read-back) | `appliance/vpn/bgp` GET/PUT (enabled, asNumber, neighbors) | BGP feature template / Service-profile BGP parcel | `router/bgp` singleton + neighbor table | element `bgppeers` CRUD | `deviceSettings` `device_settings_bgp` (neighbors/networks/filters) |
| neighbor session status | **✗** (no published read) | `/device/bgp/neighbors` | routing monitor (BGP neighbors) | `bgppeers/status` | `monitoring/getEnterpriseBgpPeerStatus` |
| learned prefixes | **✗** | `/device/bgp/routes` | `monitor/router/ipv4` (type=bgp) | `bgppeers/{id}/reachableprefixes` | enterprise route table (BGP-learned entries) |

Config 5/5; operational reads 4/5 — handled per method by the
unsupported-capability convention, consistent with the design doc's v2
posture and the validation record (the one family's learned-route
verification stays a manual dashboard step).

## Consumer migration (in step, same session)

1. **Twin** — vitro-bdd `examples/sdwan-digital-twin`: real FRR
   implementation via the existing vtysh plumbing — `router bgp <AS>`,
   `neighbor <ip> remote-as <as>`, `network <cidr>` (and `no router bgp
   <AS>` on disable / reconfigure). `get_bgp_config` returns the stored
   config (same stored-state pattern as the static-routes dict; FRR
   running-config parsing deferred). Operational reads parse
   `show bgp ipv4 unicast summary json` (neighbor states, pfxRcd) and
   `show ip route bgp json` (learned prefixes) via the device's existing
   JSON-extraction helper. Unit tests with mocked vtysh/command output.
2. **MX driver** — the MX-driver testbed repo: `set_bgp_config` /
   `get_bgp_config` over the dashboard BGP endpoint (enabled, asNumber,
   neighbors[{ip, remoteAsNumber}]); `advertised_networks` non-empty →
   unsupported-capability (the product auto-advertises overlay subnets);
   `get_bgp_neighbors` / `get_learned_routes` raise unsupported-capability
   with a message pointing at the dashboard (matching the validation
   addendum's disposition for the learned-route acceptance case). Unit
   tests with mocked dashboard client. Driver caveat (docstring): the
   product applies BGP in hub/concentrator contexts — a testbed
   precondition, not a contract concern.
3. Neither repo may pin/upgrade across this change without its migration.

## Tests (testprotocols)

1. Model tests: `BgpSessionState` full-FSM membership + validation;
   `BgpNeighbor`/`BgpConfig` defaults (empty lists, independent instances);
   `BgpPeerStatus.prefixes_received is None` default.
2. Conformance: `Bgp` entry in `test_wan_edge_templates.py` (four methods).
3. Device-type gates: `bgp` expected on BOTH archetypes.
4. `mypy --strict`; vendor-isolation + customer-name greps; full suite green.

## Tracking & docs

- **GAPS.md**: delete the BGP deferred entry; append an Implemented bullet
  (this closes the last SD-WAN-round gap).
- **`docs/sdwan-appliance-protocol-design.md`**: `bgp:` archetype-block
  line, capability note, cross-vendor row (config 5/5 / reads 4/5).
- **MX-driver repo validation addendum**: §5.4 row flips to Implemented
  once the MX migration lands.
- **`SPLITS.md` / `LEVELS.md`**: no entries.

## Error handling

Unsupported-capability per the framework convention on the operational
reads and on `advertised_networks` where a product cannot comply. No new
error types; no KeyError semantics needed (whole-config replace).

## Acceptance

- testprotocols: full suite + mypy --strict + vendor/customer greps green.
- Twin and MX-driver repo suites green with the new capability wired and
  tested.
- GAPS.md BGP entry resolved; docs updated as listed.
