# Design: `StaticRoutes` capability seed

| Field   | Value                                                              |
| ------- | ------------------------------------------------------------------ |
| Status  | Approved for implementation                                         |
| Author  | rjvisser                                                            |
| Date    | 2026-06-12                                                          |
| Related | `GAPS.md` (2026-06-12 static-route entry — resolved by this), `docs/sdwan-appliance-protocol-design.md`, `router.py` (read-only RIB surface), `models/wan_edge.py::RouteEntry`, `devices/sdwan.py` |

## Purpose

Add the static-route **write** surface missing from the WAN-edge contract.
Driving evidence: operator acceptance scope requires configuring a static
route on the appliance toward a downstream LAN router via the management API
and verifying traffic follows it. `Router` is deliberately read-only (since
the 2026-06-12 `WanLinkAdmin` split), so this lands as a **sibling
capability** composed on both WAN-edge archetypes.

This resolves the GAPS.md entry of 2026-06-12 ("Router static-route
configuration", priority high). The entry's trigger — a driver/testbed
implementing a static-routing acceptance case — has fired.

## Constraints

- No customer/test-suite names in package source, tests, tracking files, or
  commit messages; vendor names only in `docs/`, `GAPS.md`/`SPLITS.md` (and
  the vendor-specific consumer repos).
- `mypy --strict`; established conventions (dataclass models in
  `models/sdwan_appliance.py`, `runtime_checkable` Protocols, parametrized
  conformance tests, vendor-isolation grep).
- **Adding a required archetype attribute is conformance-breaking** for both
  existing device implementations — the Linux digital twin
  (vitro-bdd `examples/sdwan-digital-twin`, `LinuxSdwanRouter`) and the MX
  driver (kpn-sdwan `MerakiMx`). Both are migrated **in step** (same working
  session).
- All python via each repo's `.venv-3.12`.

## Model (`models/sdwan_appliance.py`)

```python
@dataclass
class StaticRoute:
    """A testbed-owned static route.

    ``name`` is the per-entry CRUD handle (``remove_static_route(name)``).
    Products whose API keys routes by sequence number or opaque id carry the
    name in their description/comment field or a driver-side mapping — a
    driver concern, not a contract one. ``next_hop`` is a next-hop IP
    address; interface-bound next hops, metrics/administrative distance, and
    per-route advertise flags grow on evidence.
    """

    name: str
    destination_cidr: str
    next_hop: str
```

Decisions recorded:

- **New minimal dataclass, not `RouteEntry`.** The read model
  (`wan_edge.RouteEntry`: destination/gateway/interface/metric) has no
  `name` and carries operational fields that are wrong as write inputs.
  Reads of the operational table stay `Router.get_routing_table() ->
  list[RouteEntry]`.
- **Per-entry CRUD, not list-replace** — all five reviewed appliance
  families store static routes as individual objects.

## Protocol (`static_routes.py`, new)

```python
@runtime_checkable
class StaticRoutes(Protocol):
    """Abstract contract for a WAN edge's testbed-managed static routes."""

    def add_static_route(self, route: StaticRoute) -> None:
        """Create the route, or update it in place if *route.name* exists.

        Idempotent by name — repeating a call converges to the same state.
        """

    def remove_static_route(self, name: str) -> None:
        """Remove the route named *name*.

        Raises KeyError if no route with that name exists.
        """

    def list_static_routes(self) -> list[StaticRoute]:
        """Return the configured static routes (config view, not the RIB)."""
```

**Deviation from the GAPS sketch, deliberate:** the sketch said "reads stay
on `get_routing_table`", but that is the *operational* RIB (no names).
Per-entry CRUD needs a config-view read-back for round-trip verification;
`list_static_routes` provides it and is trivially available on all five
reviewed families. No overlap with `Router` (operational vs config view).

Module docstring carries In scope (testbed-managed static-route CRUD +
config read-back) / Out of scope (RIB reads → `router`; dynamic routing —
BGP — deferred in `GAPS.md`; policy-based routing → `sdwan_policy_manager`).

## Archetypes (`devices/sdwan.py`)

`static_routes: StaticRoutes` added to **both** `SdwanRouterDevice` (after
`wan_admin`) and `SdwanApplianceDevice` (after `routing`). Both device-type
gate tests extended. Conformance entry lands in
`tests/test_wan_edge_templates.py` beside `Router`/`WanLinkAdmin` (shared
WAN-edge surface).

## Cross-vendor concept check (public API references — docs only; 5/5)

| Intent | Meraki MX | Catalyst SD-WAN | FortiGate | Prisma SD-WAN | Arista (VeloCloud) |
|---|---|---|---|---|---|
| per-entry static-route CRUD | `staticRoutes` CRUD (name, subnet, gatewayIp) | service-VPN parcel IPv4 static-route tables (config-group push) | `router/static` (seq-num mkey; name via comment/driver map) | element `staticroutes` CRUD | `deviceSettings` `static[]` of `device_settings_static_route` (destination, cidrPrefix, gateway, description, advertise — Orchestrator API 6.4 guide, schema verified) |

Driver-mechanics caveats (not contract concerns): Catalyst writes are
template/parcel pushes; sequence-/id-keyed stores carry the name in
comment/description or a driver map.

## Consumer migration (in step, same session)

1. **Twin** — vitro-bdd `examples/sdwan-digital-twin`: new methods on the
   device's routing-side impl family using the existing `_run_vtysh`
   plumbing — `ip route <destination_cidr> <next_hop>` /
   `no ip route <destination_cidr> <next_hop>`. FRR stores no route names,
   so the impl keeps a name→`StaticRoute` dict as the CRUD handle and
   serves `list_static_routes` from it (add-with-existing-name first
   removes the old prefix/next-hop pair, then installs the new one). Wire
   `static_routes` onto `LinuxSdwanRouter` (cli route + device alias, same
   pattern as `wan_admin`). Unit tests with mocked vtysh.
2. **MX driver** — kpn-sdwan: new `impls/static_routes.py` —
   `add_static_route` resolves name→`staticRouteId` via
   `getNetworkApplianceStaticRoutes`; update in place when the name exists
   (`updateNetworkApplianceStaticRoute`), else
   `createNetworkApplianceStaticRoute(network_id, name=..., subnet=...,
   gatewayIp=...)`; `remove_static_route` deletes by resolved id (KeyError
   when absent); `list_static_routes` maps the GET. Wire `static_routes`
   onto `MerakiMx`. Unit tests with mocked dashboard client.
3. Neither repo may pin/upgrade across this change without its migration.

## Tests (testprotocols)

1. Model test: `StaticRoute` fields (no defaults beyond none — all three
   required) and value behavior.
2. Conformance: new `StaticRoutes` entry in `test_wan_edge_templates.py`
   (`add_static_route`, `remove_static_route`, `list_static_routes`).
3. Device-type gates: `static_routes` expected on BOTH archetypes.
4. `mypy --strict`; vendor-isolation grep; full suite green.

## Tracking & docs

- **GAPS.md**: move the 2026-06-12 static-route entry into the existing
  `## Implemented` section (delete the deferred entry; one summary bullet).
- **`docs/sdwan-appliance-protocol-design.md`**: `static_routes:` line in
  the archetype block, a short capability note, and a cross-vendor table
  row (5/5, including the fifth family).
- **kpn-sdwan validation addendum**: §5.3 row flips to Implemented once the
  MX migration lands.
- **`SPLITS.md` / `LEVELS.md`**: no entries (addition; no white-box).

## Error handling

`KeyError` on `remove_static_route` of an unknown name (mirrors
`get_vlan` / `get_uplink`). Unsupported-capability per the framework
convention where a product cannot comply (none expected across the five
reviewed families). No new error types.

## Acceptance

- testprotocols: full suite + mypy --strict + vendor/customer-name greps
  green.
- vitro-bdd twin and kpn-sdwan MX suites green with the new capability
  wired and tested.
- GAPS.md entry resolved; docs updated as listed.
