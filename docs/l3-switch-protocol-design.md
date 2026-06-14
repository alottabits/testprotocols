# Design: vendor-neutral **L3Switch** (managed distribution switch) protocol shape

| Field    | Value                                                                                                                                                                                                                                                                                                                       |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Status   | Proposed                                                                                                                                                                                                                                                                                                                    |
| Author   | rjvisser                                                                                                                                                                                                                                                                                                                    |
| Date     | 2026-06-14 (updated 2026-06-14: Arista EOS verification — CCS-720XP Series added as a cross-vendor verification column; see *Cross-vendor neutrality v2*)                                                                                                                                                                       |
| Related  | `docs/l2-switch-protocol-design.md` (the composed L2 capability layer — read it first), `docs/sdwan-appliance-protocol-design.md` (the API-managed-device exclusion precedent), `packages/testprotocols/GAPS.md` (L2Bridge HIGH entry; IgmpSnooping / PortMirror / MulticastRouting deferrals), `packages/testprotocols/SPLITS.md` (Router RIB carve-out; ApplianceVlans SVI/DHCP reuse; unified SwitchAcl), `packages/testprotocols/LEVELS.md` (`MacTableWhiteBox`), `devices/switch.py` and `models/switch.py` (authored in the L2Switch doc; this doc adds to / composes them), `models/switch_routing.py` (proposed/new — authored by this doc) |

This document explains why `testprotocols` carries a dedicated **managed
distribution switch** archetype, `L3Switch`, modelled as a **strict superset**
of the `L2Switch` access-switch archetype, and records the shape proposed for it.
It is a proposal; the L2 capability layer it composes is derived in full in the
sibling document `docs/l2-switch-protocol-design.md` and is **not** re-derived
here. This document focuses on the **L3-only additions** that `L3Switch` layers
on top of the complete L2 baseline.

## Context and problem statement

`testprotocols` already models WAN-edge devices (`SdwanRouterDevice`,
`SdwanApplianceDevice`) and a managed access switch (`L2Switch`, see the sibling
doc). A **managed distribution switch** is a distinct device class: it does
everything an access switch does — ports, VLANs, spanning tree, link
aggregation, PoE, port security, storm control, ACLs, discovery, FDB/port reads,
QoS, syslog — **and** it routes between those VLANs. It owns routed interfaces
(SVIs and routed ports), reads its RIB, serves or relays DHCP per SVI, runs a
dynamic IGP, provides first-hop gateway redundancy, and enforces L3/L4 ACLs.

Modelling such a switch against any existing archetype is **both over- and
under-specified**:

**Over-specified — the WAN-edge `Router` and host levers carry the wrong shape.**

- The `Router` protocol (and the WAN-edge archetypes that compose it) is built
  around WAN uplinks, default-gateway / ping behaviour, and overlay steering.
  A distribution switch routes **east-west between local SVIs**; its routing
  surface is a RIB read plus IGP and static config, not a WAN-uplink admin
  surface. Forcing the full `Router` shape onto a switch over-specifies it with
  uplink methods it does not have.
- The host-substrate levers an L2-only Linux twin might carry
  (`ip_interface`, `ip_routing`, `packet_filter`, `nat`, `conntrack`,
  `firewall_zones`, `pcap`) are all wrong-shape for an API/controller-managed
  switch — the same boundary the SD-WAN appliance archetype drew when it
  excluded the four host levers. A distribution switch is a closed product
  driven through a management plane (cloud controller, on-box REST/NETCONF, or
  controller UI), not a Linux host you shell into.

**Under-specified — no archetype models routed-switch surfaces.**
SVIs and routed ports, a RIB read carved free of WAN methods, per-SVI DHCP
server/relay, OSPF, an L2+L3 unified port/VLAN-bound ACL, and a normalized
gateway-redundancy concept all sit on every reviewed distribution switch and
have no home in the contract. `ApplianceVlans` is close to the SVI+DHCP shape
but is named and scoped for the WAN edge; `static_routes.py` and `bgp.py` are
reusable as-is but were authored for the WAN edge; the RIB read is buried inside
the WAN-edge `Router`.

The clean answer is a **strict-superset archetype**: `L3Switch` composes the
entire shared L2 capability layer (cross-referenced, not re-derived) **plus** an
L3 layer, and is declared `L3Switch(L2Switch, Protocol)` so the superset
relationship is `runtime_checkable`-verifiable.

## Decision

Add a vendor-neutral **`L3Switch`** archetype that **composes every capability
of `L2Switch`** (see `docs/l2-switch-protocol-design.md` for the full derivation
of the L2 layer) and **adds the L3 layer**:

```
L3Switch ⊇ L2Switch
         + { RoutedInterfaces, StaticRoutes, RoutingRead, Ospf,
             InterfaceDhcp, SwitchAcl(L3 fields), GatewayRedundancy }
```

`L3Switch` excludes the same host-substrate levers `L2Switch` excludes (a
distribution switch is no more a Linux host than an access switch is), and
excludes the WAN-edge `Router`'s uplink surface, carving the RIB-read kernel out
into a switch-scoped `RoutingRead`.

The concrete peer/driver target is a cloud-managed distribution switch
(Meraki MS355 in the cross-vendor matrix, named there **only** as the concept
check). The Protocol itself is intent-level and vendor-neutral; the design-target
shortfalls (no BGP, no RIB read, warm-spare instead of per-VIP VRRP, RSTP-only,
implicit VLANs) are surfaced as per-method **unsupported-capability** exceptions
in the driver — never as contract leaks.

This mirrors the SD-WAN appliance precedent (`docs/sdwan-appliance-protocol-design.md`):
an API-managed device gets an archetype that reflects what its management plane
genuinely exposes, excludes host-substrate levers, and adds the missing
capabilities — guarded by a cross-vendor concept check.

### Evidence convention — why these capabilities are built now

`GAPS.md` is firm that net-new protocols land on **tracked evidence — a test
that needs it and a cross-vendor concept check** (a concept a strong majority of
reviewed families expose through their management plane, not a one-vendor quirk).
Two framings apply, and both point the same way:

- **Foundation baseline.** `testprotocols` is pre-1.0 and deliberately
  establishing a *sound, complete baseline* for the switch archetypes — the same
  way the Wi-Fi capability family was built out ahead of any single consumer.
  A capability a strong majority of reviewed distribution switches expose belongs
  in that baseline.
- **Per-capability evidence.** Each L3 capability maps to a concrete
  switch-test concern — inter-VLAN reachability, RIB correctness, per-SVI DHCP
  hand-out, dynamic-route convergence, L3 ACL enforcement, first-hop failover.

Every L3 capability below carries a `K/6` cross-vendor check against the
distribution review set (Meraki MS355, Aruba CX 6300, Juniper EX4400,
Catalyst 9300, UniFi Pro Max, FortiSwitch 400). The bar is the same the L2
sibling sets — a concept a **strong majority (≥ 5/6)** of reviewed families
expose — and the `K/6` count uses **one convention throughout this doc: `◐`
(partial/divergent, maps in via driver translation) counts as present**; only
`✗` (absent) does not. Capabilities that clear the ≥ 5/6 bar **and** carry a
driving switch concern are in the mandatory `L3Switch` baseline. Two capabilities
sit below or beside the bar and are handled like the appliance precedent rather
than forced into the baseline: `Bgp` (4/6 under the ◐-counts-as-present
convention — full on Aruba CX / Juniper / Catalyst, ◐ standalone-only on
FortiSwitch, absent on the design-target MS355 and UniFi — still short of the
≥ 5/6 bar) is composed only on an optional routed variant; `MulticastRouting`
reaches 5/6
present but is deferred to `GAPS.md` on the **driving-test discriminator** — high
surface area and no switch test drives it — not on the headcount. `RoutingRead`'s
dynamic-RIB read is the one mandatory surface that does **not** clear the bar
(3/6); it is admitted as a per-method best-effort read on an otherwise-6/6
capability, with the split stated explicitly below.

## The archetype

`L3Switch` is declared as a subtype of `L2Switch` so the strict-superset
relationship is explicit and `runtime_checkable`-verifiable. The block lists the
**complete** attribute set (the composed L2 layer plus the L3 layer) so the
Protocol is self-contained; the L2 attributes are derived in
`docs/l2-switch-protocol-design.md` and only summarised here.

```python
@runtime_checkable
class L3Switch(L2Switch, Protocol):
    # ── composed L2 capability layer (full derivation in the L2Switch doc) ──
    switch_ports: SwitchPorts             # per-port mode/PVID/allowed-VLANs/voice/isolation
    switch_vlans: SwitchVlans             # per-VLAN id/name registry (membership target)
    spanning_tree: SpanningTree           # global mode + bridge priority; per-port guard/edge/cost
    link_aggregation: LinkAggregation     # LAG group CRUD by member ports + mode
    port_poe: PortPoe                     # per-port PoE enable + draw/status read
    port_security: PortSecurity           # per-port access policy + MAC allow/sticky limits
    storm_control: StormControl           # per-port broadcast/multicast/unknown-unicast thresholds
    switch_acl: SwitchAcl                 # unified L2+L3 port/VLAN-bound ACL (see L3 note below)
    discovery: Discovery                  # read — LLDP/CDP neighbour view per port
    mac_table: MacTable                   # read — FDB (MAC/port/VLAN)
    port_status: PortStatus               # read — link state, speed/duplex, counters per port
    switch_qos: SwitchQos                 # QoS rule list + DSCP→CoS map + trust mode
    syslog: SyslogConfig                  # reuse-as-is — remote-logging destinations

    # ── L3 capability layer (this document) ──
    routed_interfaces: RoutedInterfaces   # new (reshape of ApplianceVlans) — SVI + routed port
    static_routes: StaticRoutes           # reuse-as-is — per-entry static-route CRUD
    routing_read: RoutingRead             # new (RIB kernel carved out of Router)
    ospf: Ospf                            # new — dynamic IGP (OSPFv2/v3)
    interface_dhcp: InterfaceDhcp         # reuse VlanConfig DHCP fields — per-SVI server/relay
    gateway_redundancy: GatewayRedundancy # new — first-hop redundancy (virtual IP + role)

register_device_type("managed_switch_l3", L3Switch)
```

> Note: the unified `switch_acl: SwitchAcl` attribute is composed once. The L2
> match fields are derived in the L2Switch doc; this document adds the L3/L4
> match fields to the **same** capability — the reviewed switches use one ACL
> engine, so there is one ACL protocol, not two (see *New capabilities →
> `SwitchAcl` (L3 fields)*).

**Optional routed variant.** `Bgp` does **not** clear the L3-switch majority bar
(4/6 under the ◐-counts-as-present convention — full on three families, ◐ on
FortiSwitch, absent on the design-target) and is absent on the design-target. It
is composed only on an optional routed-distribution variant, not on the mandatory
`L3Switch`:

```python
@runtime_checkable
class L3SwitchRouted(L3Switch, Protocol):
    bgp: Bgp                              # reuse-as-is (bgp.py) — composed only here

register_device_type("managed_switch_l3_routed", L3SwitchRouted)
```

Excluded host-substrate levers (same as `L2Switch`): `conntrack`, `pcap`
(`PcapCapture`), `ip_interface`, `nat`, `packet_filter` /
`PacketFilterWhiteBox`, `firewall_zones`, `wan_link_admin`. Also excluded: the
WAN-uplink methods of `Router`, `l3_firewall` (LAN/WAN/VPN triad),
`dhcp_server` (CPE-provisioning), and `ip_routing` (host ping / default-gw) —
superseded by `RoutingRead`, `SwitchAcl`, and `InterfaceDhcp`. See *Excluded
host-substrate levers*.

## Reuse notes — capabilities taken from existing protocols

The full L2-layer reuse map (which L2 capabilities are NEW, REUSE, or RESHAPE) is
in `docs/l2-switch-protocol-design.md`. For the L3 layer the reuse decisions are:

| L3 capability                | Existing protocol / model                                   | Action                                            |
| ---------------------------- | ----------------------------------------------------------- | ------------------------------------------------- |
| `RoutedInterfaces` (SVI)     | `appliance_vlans.py` `VlanConfig` (SVI IP, DHCP fields)     | **RESHAPE** — rename `appliance_ip → svi_ip`, add routed-port mode |
| `StaticRoutes`               | `static_routes.py` (`StaticRoute`)                          | **REUSE-AS-IS** — vendor-neutral, no WAN coupling |
| `RoutingRead` (RIB)          | `router.py` `get_routing_table()` + `models/wan_edge.py` `RouteEntry` | **RESHAPE** — carve the RIB kernel, drop WAN methods; `RouteEntry` gains an `origin` field (back-compat default — see note) |
| `Ospf`                       | —                                                           | **NEW** (`models/switch_routing.py`)              |
| `Bgp` (optional variant)     | protocol `Bgp` in `bgp.py`; `BgpConfig` / `BgpPeerStatus` / `BgpNeighbor` / `BgpSessionState` in `models/sdwan_appliance.py` (`bgp.py` imports them) | **REUSE-AS-IS** — composed only on the routed variant |
| `InterfaceDhcp`              | `VlanConfig` DHCP fields + `DhcpMode` StrEnum               | **REUSE** fields, new per-SVI accessor surface    |
| `SwitchAcl` (L3 fields)      | `L3Rule` / `FirewallRule` record + `RuleAction` / `RuleProtocol` | **RESHAPE/MERGE** — one engine, add L3/L4 fields to the unified `SwitchAcl` |
| `GatewayRedundancy`          | —                                                           | **NEW** (`models/switch_routing.py`)              |

The strongest reuse is `RoutedInterfaces`: `VlanConfig` already carries an SVI
IP and the `DhcpMode{SERVER,RELAY,DISABLED}` field, so `RoutedInterfaces` and
`InterfaceDhcp` are reshapes of one existing model rather than greenfield. The
RIB carve-out keeps the `RouteEntry` *model* (`models/wan_edge.py`) shared
between the WAN-edge `Router` and the switch's `RoutingRead`; the WAN-uplink
methods stay on the WAN-edge `Router`. Note this is a **reshape, not pure
reuse-as-is** of `RouteEntry`: today it is
`RouteEntry(destination, gateway, interface, metric)` with **no origin field**,
and the switch read wants the route source. Adding `origin: RouteOrigin` is
back-compatible **only because the new field carries a default**
(`RouteOrigin.STATIC` / unknown), so existing consumers —
`Router.get_routing_table()` on the WAN edge and `Bgp.get_learned_routes()` —
keep constructing `RouteEntry` unchanged. That cross-consumer impact is recorded
explicitly in `SPLITS.md` (below) rather than described as a no-op.

## New capabilities

Each capability below is intent-level: it describes *what a distribution switch
can be asked to do*, not how any product's API spells it. New models live in
`models/switch_routing.py` (new); reshaped models reuse `models/switch.py` (the
L2 module) and the existing WAN-edge / appliance models. Each carries its
cross-vendor `K/6` concept check.

### `routed_interfaces: RoutedInterfaces` — **6/6**
SVIs (one L3 interface per VLAN) and routed ports, reshaped from the appliance's
`VlanConfig`. `RoutedInterfaces` lists/gets/sets routed interfaces; each carries
an `InterfaceMode{SVI,ROUTED,LOOPBACK}`, the renamed `svi_ip` (was
`appliance_ip`), subnet, VLAN binding (for SVIs), and the DHCP fields reused by
`InterfaceDhcp`. **Cross-vendor:** every reviewed family exposes SVI-style L3
interfaces (Meraki `RoutingInterface`, Aruba CX `interface vlan`, Juniper IRB,
Catalyst `interface Vlan`); UniFi anchors them to the gateway (◐) and
FortiSwitch exposes them standalone-only (◐) — both raise unsupported-capability
on the unsupported facets, not a contract leak.

### `static_routes: StaticRoutes` — **6/6** (reuse-as-is)
The existing `StaticRoute(name, destination_cidr, next_hop)` per-entry CRUD
surface is vendor-neutral with no WAN coupling and directly satisfies the switch
role. **Cross-vendor:** all six store static routes as individual objects;
UniFi caps the GUI route count (◐) and FortiSwitch is standalone-only (◐).

### `routing_read: RoutingRead` — **6/6 capability (dynamic-RIB facet 3/6)**
A read-only routing-table surface — `get_routing_table() -> list[RouteEntry]` —
carved out of the WAN-edge `Router`. `RouteEntry` is shared; the WAN-uplink
methods stay on `Router`. The capability splits per-method, and the split is what
clears it for the mandatory baseline:

- **Config-view read — 6/6.** *Every* reviewed family can return the routes it is
  configured to carry: connected/SVI routes, static routes, and (where present)
  the OSPF config. All six expose this view, so the `RoutingRead` *capability*
  itself is 6/6 — every mandatory-archetype driver satisfies the route-read
  surface for the configured/connected/static `RouteEntry` set.
- **Dynamic-learned facet — 3/6.** Only Aruba CX, Juniper, and Catalyst expose a
  clean *learned*-RIB endpoint (routes learned via the IGP). Meraki MS355, UniFi,
  and FortiSwitch-via-controller are config-only on routing state and raise
  **per-method unsupported-capability** on the dynamic/learned facet only — a
  best-effort read, the same per-method discipline `bgp.py` uses for its
  operational reads.

So the carve-out is mandatory on the strength of the 6/6 config-view read; only
the 3/6 dynamic-learned facet is best-effort, and that is stated as a per-method
caveat rather than a sub-bar capability. (This is the inverse of `Bgp`, where the
*whole* capability — config and reads alike — is sub-bar at 4/6 and therefore
moves to the optional variant.) **Cross-vendor:** config-view read 6/6;
learned-RIB facet 3/6 full, 3/6 config-only (per-method unsupported-capability).

### `ospf: Ospf` — **5/6 ✓**
Dynamic IGP that clears the bar: whole-config-replace plus per-interface settings,
with RFC-standard vocabulary seeded in full (`OspfVersion{V2,V3}`). Model shape,
consistent with how the other new L3 capabilities name their record fields:

- `OspfConfig(enabled, version: OspfVersion, router_id, areas, interfaces)` —
  whole-config replace (`set_ospf_config` / `get_ospf_config`), where `areas` is
  the configured area list and `interfaces` the per-interface settings below.
- `OspfInterfaceSettings(interface, area, cost, passive)` — per-routed-interface
  participation: area binding, metric `cost`, and a `passive` toggle.

`OspfNetworkType` / `OspfAreaType` are **not** seeded now — they grow on
evidence (the open-taxonomy rule), unlike `OspfVersion` which is the standardized
v2/v3 set. **Cross-vendor:** Meraki, Aruba CX, Juniper, Catalyst, and
FortiSwitch (standalone) all run OSPF; UniFi runs OSPF only on its gateways,
never on the L3 switch (✗) and raises unsupported-capability. OSPF is the
dynamic-routing capability in the mandatory `L3Switch` baseline.

### `interface_dhcp: InterfaceDhcp` — **6/6**
Per-SVI DHCP server **and** relay, reusing the `DhcpMode{SERVER,RELAY,DISABLED}`
StrEnum and the DHCP fields already on `VlanConfig`. Each SVI carries a
`dhcp_mode`, relay target IPs, and (for server mode) pools / options /
reservations. Deliberately **not** the host-shaped `dhcp_server` (which is
CPE-provisioning). **Cross-vendor:** per-SVI server+relay is universal; only
FortiSwitch is standalone-only (◐).

### `switch_acl: SwitchAcl` (L3 fields) — **6/6**
The reviewed switches enforce L2 and L3/L4 ACLs through **one engine** (on Meraki
literally the same endpoint), so there is **one** `SwitchAcl` capability carrying
both L2 (MAC) and L3 (5-tuple) match fields — not two protocols. The capability
is composed once (the attribute is shared with the L2 layer); this document adds
the L3/L4 match fields. Bindings are by port/VLAN and `AclDirection{INGRESS,
EGRESS}`; the rule record reuses `L3Rule` / `FirewallRule` with `RuleAction` and
`RuleProtocol`. It deliberately does **not** compose `l3_firewall` (the
appliance LAN/WAN/VPN triad) or `packet_filter` (host chains). **Cross-vendor:**
all six match L3/L4; Meraki exposes a single network-wide ordered list (◐) and
UniFi expresses ACLs as controller isolation/policy constructs (◐) — ordering and
named-ACL divergence is handled in driver translation.

### `gateway_redundancy: GatewayRedundancy` — **5/6 ✓**
First-hop redundancy normalized to a **redundancy-group** concept — a virtual IP
plus a `RedundancyRole{PRIMARY,SPARE}` — **not** raw VRRP/HSRP group internals.
This lets Meraki's whole-switch warm-spare map into the same concept as Aruba CX
/ Juniper / Catalyst VRRP. Behaviour is asserted via virtual-IP + role (the
IPS-signature precedent: assert behaviour, not vendor protocol internals). The
record is whole-config-replace per redundancy group:
`RedundancyGroup(group_id, virtual_ip, role: RedundancyRole, interface)`, listed
/ get / set on the bound routed interface. **Cross-vendor (5/6, counting ◐ as
present, the same convention used for `RoutedInterfaces` / `StaticRoutes` /
`InterfaceDhcp`):** Aruba CX / Juniper VRRP and Catalyst HSRP/VRRP/GLBP are full
(3 ✓); Meraki warm-spare (◐) and FortiSwitch standalone-only (◐) map in (2 ◐);
UniFi has no switch-side FHR (✗). The absent families raise
unsupported-capability. It clears the strong-majority bar **and** carries a
driving test (first-hop failover), so it is in the mandatory baseline —
distinguishing it from `MulticastRouting`, which reaches the same 5/6 present but
is deferred precisely because it carries **high surface area and no driving
switch test** (the deferral discriminator, not the headcount).

### `bgp: Bgp` (optional routed variant only) — **4/6 ✗**
The existing `Bgp` protocol (`bgp.py`) and its models (`BgpConfig` /
`BgpPeerStatus` / `BgpNeighbor` and the RFC-4271 `BgpSessionState` FSM, all in
`models/sdwan_appliance.py`) are reusable as-is, but BGP **fails the L3-switch
majority bar** — under the ◐-counts-as-present convention it is 4/6 (full on
Aruba CX, Juniper, and Catalyst; ◐ standalone-only on FortiSwitch; absent on the
design-target MS355 and on UniFi), still short of the ≥ 5/6 bar. **Decision:**
`Bgp` is an
**optional/conditional** capability composed only on `L3SwitchRouted`, never on
the mandatory `L3Switch`. Products without BGP raise unsupported-capability per
the documented convention. This mirrors the appliance's per-method discipline
rather than forcing a one-segment-of-the-market shape onto every L3 switch.

## Normalized vocabulary (commons-owned `StrEnum`; mappings in the plugin)

The L2 vocabularies (`PortMode`, `PortAdminState`, `LinkState`, `Duplex`,
`StpMode`, `StpGuard`, `StpPortState`, `AggregationMode`, `PoeStatus`,
`PoePriority`, `AccessPolicyType`, `AclDirection` (the ACL action reuses
`RuleAction`, not a new `AclAction`), `DiscoveryProtocol`, `StormControlType`,
`QosTrustMode`, and the `LinkSpeed`
int-Mbps-field decision) are authored in `models/switch.py` and derived in
`docs/l2-switch-protocol-design.md`. They are **not** repeated here.

The L3 layer adds these `StrEnum`s in `models/switch_routing.py`, authored as
`StrEnum` from day one per the legacy-`str`→`StrEnum` GAPS rule. The plugin holds
the vendor⇄normalized mapping table; `testprotocols` never imports it. Records are
plain `@dataclass`es composing these enums.

- `InterfaceMode(StrEnum)`: `SVI`, `ROUTED`, `LOOPBACK`.
- `DhcpMode(StrEnum)`: **REUSE existing** `SERVER` / `RELAY` / `DISABLED` from
  `models/sdwan_appliance.py` — not re-declared.
- `OspfVersion(StrEnum)`: `V2`, `V3`. `OspfNetworkType` / `OspfAreaType` grow on
  evidence.
- `BgpSessionState`: **REUSE existing** full RFC-4271 FSM enum from
  `models/sdwan_appliance.py` (where `BgpConfig` / `BgpPeerStatus` / `BgpNeighbor`
  also live; the `Bgp` protocol in `bgp.py` imports them). Seeded in full because
  it is protocol-standard, not a vendor taxonomy.
- `RedundancyRole(StrEnum)`: `PRIMARY`, `SPARE` — normalizes warm-spare and
  VRRP master/backup. Raw VRRP/HSRP group internals are **not** modelled;
  behaviour is asserted via virtual-IP + role. **Candidate `ACTIVE_ACTIVE`**
  (shared/anycast-gateway) recorded on the 2026-06-14 Arista review (symmetric
  active/active VARP, which has no "spare"); not seeded now — a driver maps both
  VARP nodes to `PRIMARY` today, and the member lands only on a test asserting
  active/active explicitly (open-taxonomy rule). See the v2 subsection.
- `RouteOrigin(StrEnum)` (new `origin` field on `RouteEntry`): `STATIC`,
  `CONNECTED`, `OSPF`, `BGP`, `LOCAL` — standardized, full seed. Adding it
  **reshapes** the shared `RouteEntry` (`models/wan_edge.py`); the field carries a
  default so the WAN-edge `Router.get_routing_table()` and
  `Bgp.get_learned_routes()` consumers stay source-compatible. Tracked in
  `SPLITS.md`, not treated as pure reuse. **Candidate `ISIS` / `RIP`** recorded on
  the 2026-06-14 Arista review (its RIB exposes those origins); not seeded now —
  added on a driving test per the open-taxonomy rule. See the v2 subsection.

**Commons owns the vocabulary; the plugin owns the mappings.** Every value
vocabulary is a normalized `StrEnum` in `testprotocols`; the testbed plugin ships
the `{normalized → vendor-id}` translation table and the driver maps on the way
in/out of its API. A vendor lacking a mapped entry surfaces as a clear
**unsupported-capability** error — a coverage gap, not a contract leak. Read
models carry only normalized fields (no `native` bucket); a vendor-only datum
with no normalized field is the signal to add a normalized field on evidence.

**Per-method unsupported-capability exceptions surfaced by the cross-vendor data
(driver-side, not contract leaks):**

- Meraki MS355: **no BGP**, no RIB read (config-only routing state), warm-spare
  instead of per-VIP VRRP, RSTP-only (no MSTP), VLANs implicit, single
  network-wide ordered ACL.
- UniFi Pro Max: no OSPF/BGP, no switch-side `GatewayRedundancy`, no
  `MulticastRouting`, RIB read CLI-only, static-route count capped, SVIs
  gateway-anchored / IPv6-less.
- FortiSwitch 400 (FortiLink mode): the **entire L3 layer** is unsupported via
  the controller (standalone-only, advanced-features-licensed); a FortiLink
  deployment raises unsupported-capability across the L3 layer.
- LLDP-only families (Aruba CX / Juniper / UniFi / FortiSwitch): `CDP` field
  unsupported (an L2-layer exception, noted in the L2 doc).

## Cross-vendor neutrality

Every L3 capability is a concept the reviewed **distribution-switch families —
Cisco Meraki MS355, Aruba CX 6300, Juniper EX4400, Catalyst 9300, UniFi Pro Max,
FortiSwitch 400, and (since the v2 review below) the Arista CCS-720XP Series² —
expose through their management plane** (subject to the per-method exceptions
above). Vendor names appear **only** here, as the concept check; they never
enter the package source. Endpoint and feature names differ
across products; the Protocol is intent-level, so the differences live entirely
in driver translation. `✓` full · `◐` partial/divergent · `✗` absent.

| Capability                       | Meraki MS355      | Aruba CX 6300       | Juniper EX4400        | Catalyst 9300       | UniFi Pro Max      | FortiSwitch 400      | Arista CCS-720XP² (verification) |
| -------------------------------- | :---------------: | :-----------------: | :-------------------: | :-----------------: | :----------------: | :------------------: | :------------------------------: |
| RoutedInterfaces (SVI)           | ✓ (RoutingInterface) | ✓ (interface vlan) | ✓ (IRB)               | ✓ (interface Vlan)  | ◐ (gateway-anchored) | ◐ (standalone only)  | ✓ (interface Vlan / no switchport) |
| StaticRoutes                     | ✓ (RoutingStaticRoute) | ✓ (ip route)    | ✓ (routing-options)   | ✓ (ip route)        | ◐ (GUI-capped)     | ◐ (standalone only)  | ✓ (ip route, VRF-aware) |
| RoutingRead (config-view 6/6; learned-RIB facet) | ◐ (config-view; no learned RIB) | ✓ (show ip route) | ✓ (show route RPC) | ✓ (show ip route)   | ◐ (CLI-only learned) | ◐ (standalone only)  | ✓ (show ip route eAPI JSON; full learned RIB) |
| Ospf                             | ✓ (RoutingOspf)   | ✓ (ospf_router)     | ✓ ([protocols ospf])  | ✓ (router ospf)     | ✗ (gateway-only)   | ◐ (standalone only)  | ✓ (router ospf, OSPFv2/v3) |
| Bgp (optional variant)           | ✗ (MS355 none)    | ✓ (bgp_router)      | ✓ ([protocols bgp])   | ✓ (router bgp)      | ✗ (gateway-only)   | ◐ (standalone only)  | ✓ (router bgp, MP-BGP) |
| InterfaceDhcp                    | ✓ (Interface DHCP) | ✓ (relay+server)   | ✓ (dhcp-relay/server) | ✓ (ip dhcp/helper)  | ◐ (Local Networks) | ◐ (standalone only)  | ✓ (ip helper-address / DHCP server) |
| SwitchAcl (L3 fields)            | ◐ (single ordered list) | ✓ (acl ip)     | ✓ (firewall filter inet) | ✓ (ip access-list) | ◐ (policy constructs) | ✓ (acl ingress)   | ✓ (ip access-list, one unified engine) |
| GatewayRedundancy                | ◐ (warm spare/VRRP) | ✓ (VRRP)          | ✓ (VRRP)              | ✓ (HSRP/VRRP/GLBP)  | ✗ (gateway-only)   | ◐ (VRRP standalone)  | ✓ (VRRP + Virtual-ARP/VARP) |
| *MulticastRouting (deferred)*    | ✓ (PIM-SM + RP)   | ✓ (PIM)             | ✓ (PIM)               | ✓ (PIM)             | ✗                  | ◐ (standalone only)  | ✓ (PIM-SM/SSM/BiDiR) |

The full L2-layer matrix (the access-switch capabilities `L3Switch` inherits) is
in `docs/l2-switch-protocol-design.md` and is not repeated here. The endpoint and
feature names in parentheses are each vendor's term for the same intent — they
live only in the per-driver mapping, never in `testprotocols`. A capability that
did not clear the ≥ 5/6 strong-majority bar (counting ◐ as present) did not enter
the mandatory baseline — `Bgp` (4/6) → optional variant; `MulticastRouting`
(5/6 present, but high surface area and no driving test) → deferred on the
driving-test discriminator.

² Seventh column added by the v2 review below as an additional cross-vendor
verification point. The original six-family review set and its `K/6` counts
remain the primary bar; Arista is presented as a verification column (the same
way the SD-WAN appliance doc kept its original counts and footnoted its fifth
family). `✓` / `◐` / `✗` carry the same meaning as the primary columns.

### Cross-vendor neutrality v2 (2026-06-14 — Arista EOS verification)

A seventh distribution-switch family — the **Arista CCS-720XP Series** (campus
PoE switch running the full **Arista EOS** image, managed interchangeably
through **CloudVision** state-streaming, **eAPI** JSON-RPC, **NETCONF/OpenConfig**,
and the EOS CLI) — was reviewed against the proposed L3 protocol set as an
additional cross-vendor verification point. All CCS-720XP variants run the same
full EOS feature set, so the surface reviewed is EOS itself, not a stripped
campus subset. No protocol, model, or enum was invalidated; the proposed shape
**held in full**, and on several axes Arista is a stronger confirmation than the
design-target.

**What held.** Every mandatory L3 capability is present and first-class on EOS
across all four management planes: `RoutedInterfaces` (SVIs via `interface Vlan`,
routed ports via `no switchport`, loopbacks, VRF-aware), `StaticRoutes`
(per-entry `ip route`, VRF-aware), `Ospf` (OSPFv2 **and** OSPFv3),
`InterfaceDhcp` (relay incl. Smart Relay **and** server mode per L3 interface),
`SwitchAcl`, and `GatewayRedundancy`. Two design decisions are confirmed
especially cleanly:

- **The unified-ACL decision is confirmed exactly.** EOS exposes a *single*
  ACL engine (ingress/egress, L2/L3/L4 fields, MAC ACLs, IPv4/IPv6, with
  logging/counters and atomic hitless restart) rather than separate L2 and L3
  ACL surfaces — matching the proposed one-`SwitchAcl`-engine decision rather
  than two protocols.
- **The `RoutingRead` dynamic-learned facet is fully supported here.** EOS
  returns the learned RIB with route origin (connected/static/OSPF/BGP, and
  also IS-IS/RIP) via `show ip route` over eAPI JSON, NETCONF, and CloudVision.
  This does **not** change the primary `RoutingRead` count — the dynamic-learned
  facet stays **3/6** on the original review set and remains a per-method
  best-effort read on the families that lack it. Arista is simply a fourth
  family that *does* expose it; with Arista counted the facet would be 4/7, but
  the 3/6 best-effort framing is kept as the primary bar.
- **`Bgp` is fully supported here, but the optional-variant decision stands.**
  EOS runs BGP and MP-BGP (also IS-IS, RIPv2) — unlike the design-target MS355,
  which has none. This does **not** promote `Bgp` into the mandatory baseline:
  the primary count stays **4/6** under the ◐-counts-as-present convention (full
  on Aruba CX / Juniper / Catalyst, ◐ standalone-only on FortiSwitch, absent on
  MS355 and UniFi), and Arista becomes a fifth present BGP family (5/7) — still
  short of the ≥ 5/6 primary bar, so it reinforces the *optional* `L3SwitchRouted`
  placement rather than changing BGP's mandatory/optional status. No primary K/6
  count is revised by the Arista review.

**Arista-specific shapes, handled via driver translation / the
unsupported-capability convention** (named here and in the matrix only, never in
a proposed protocol/model/enum name):

- **Multi-chassis link aggregation (MLAG).** EOS offers MLAG (up to 128 ports)
  as its active/active distribution-uplink shape, but the datasheet states it
  *"Uses IEEE 802.3ad LACP."* MLAG therefore satisfies a LACP-LAG intent and
  normalizes onto the existing `AggregationMode.LACP` (an L2-layer vocabulary);
  the multi-chassis property is a **topology attribute**, not a distinct
  aggregation mode. A driver maps a LAG intent to either a single-chassis
  port-channel or an MLAG. **No new `AggregationMode` member is justified** by
  this evidence — confirmation, not a revision. (If a test ever needs to assert
  multi-chassis specifically, that is a separate boolean/attribute, not an
  `AggregationMode` member.)
- **Virtual-ARP (VARP) alongside VRRPv2/v3.** EOS offers both VRRP and VARP for
  first-hop redundancy, with VARP preferred under MLAG because it avoids
  peer-link traversal. Both map onto the normalized `GatewayRedundancy` concept
  (virtual IP + role): VRRP has explicit master/backup → `RedundancyRole`;
  VARP is **symmetric active/active** (both nodes share the virtual IP/MAC, with
  no "spare"). VARP is not cleanly captured by `RedundancyRole{PRIMARY,SPARE}`
  — see the vocabulary note below. A driver can normalize VARP to both nodes
  presenting `PRIMARY` rather than forcing a primary/spare split, so the
  capability still holds without a contract change.
- **sFlow / IPFIX traffic visibility.** EOS offers RFC 3176 sFlow and
  IPFIX/FlowTracker (statistical/flow export) in addition to SPAN/mirror
  sessions (16 configured, 4 active, with L2/3/4 filtering and Enhanced Remote
  mirroring). sFlow is a flow-sampling visibility intent distinct from a
  `PortMirror`/capture-session intent; both sit on the **deferred** `PortMirror`
  / multicast-adjacent surface area (the L2-layer `PortMirror` deferral), so no
  proposed protocol is affected — recorded here as the mechanism a driver would
  select between when that capability is seeded.
- **Whole-config / multi-plane management model.** eAPI and the CLI apply config
  as ordered EOS CLI commands (running-config replace/merge per command), while
  NETCONF/OpenConfig supports incremental `edit-config` with lock/candidate
  semantics, and CloudVision provides config plus state-streaming telemetry. A
  driver chooses incremental (NETCONF) vs command-list (eAPI) per operation;
  the intent-level protocols are agnostic to this, so the whole-config shape is
  absorbed entirely in driver translation.

**No capability's mandatory/optional/deferred status changed.** The Arista
evidence is uniformly confirming: it does not force any capability out of the
baseline, into the baseline, or out of deferral. It strengthens (does not
revise) the `RoutingRead` dynamic-learned facet and the `Bgp` optional-variant
placement. (Separately, this review pass corrected the `Bgp` primary count from a
mis-stated 3/6 to **4/6** so the ◐-counts-as-present convention is applied to BGP
the same way it is to OSPF and GatewayRedundancy — FortiSwitch's standalone-only
◐ counts as present throughout. The correction does not move BGP past the ≥ 5/6
bar, so its optional placement is unchanged.) The `RoutingRead` dynamic-learned
facet keeps its **3/6** primary count, which is genuinely sub-bar (Meraki, UniFi,
and FortiSwitch are config-only ◐ on the learned-RIB facet, so even counting ◐ as
present it does not reach 5/6).

**Vocabulary candidates recorded on this evidence** (candidates, not mandatory —
each grows on a driving test per the open-taxonomy rule):

- **`RedundancyRole` — candidate `ACTIVE_ACTIVE`.** VARP's symmetric
  active/active (both nodes share the virtual IP, neither is a "spare") is not
  cleanly captured by `RedundancyRole{PRIMARY,SPARE}`. An `ACTIVE_ACTIVE` (or
  shared/anycast-gateway) member would let a VARP/active-active gateway avoid a
  primary/spare framing it does not have. Marked a **candidate**: the driver can
  also map both VARP nodes to `PRIMARY`, so `GatewayRedundancy` holds today
  without it; the member lands only if a test needs to assert active/active
  explicitly. Reflected in the *Normalized vocabulary* section below.
- **`RouteOrigin` — candidate `ISIS`, `RIP`.** Arista's RIB exposes IS-IS and
  RIP origins in addition to the seeded `STATIC`/`CONNECTED`/`OSPF`/`BGP`/`LOCAL`
  set. If those route sources must be represented, `ISIS` and `RIP` members are
  justified (open taxonomy, add on a driving test). Reflected in the
  *Normalized vocabulary* section below.

## Excluded host-substrate levers (explicit)

Mirroring the SD-WAN appliance exclusion and the L2Switch exclusion: a managed
distribution switch is API/controller-managed, not a Linux host.

| Excluded lever                          | File                  | Why excluded                                                                                          |
| --------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------- |
| `conntrack` (+ WhiteBox)                | `conntrack.py`        | Stateful-host/firewall concept; a switch is not a flow tracker.                                       |
| `pcap` (`PcapCapture`)                   | `pcap_capture.py`     | tcpdump/tshark on the box shell; packet capture is the `TrafficControllerDevice`'s job (SPLITS.md).   |
| `ip_interface` (`IpInterface`)           | `ip_interface.py`     | Host `ip addr/link/mtu/mac` per-NIC admin; replaced by `PortStatus` read + SVI config.               |
| `nat` (host iptables `Nat`)              | `nat.py`              | iptables SNAT/DNAT primitives; a switch is not a NAT box.                                             |
| `packet_filter` / `PacketFilterWhiteBox` | `packet_filter.py`   | Linux netfilter INPUT/OUTPUT/FORWARD chains + kernel dumps; switch ACLs are port/VLAN-bound.          |
| `firewall_zones`                         | `firewall_zones.py`   | OpenWrt/firewalld gateway zone+masquerade model; not a switch ACL surface.                            |
| `wan_link_admin`                         | (WAN twin)            | Forced link up/down is host-substrate-only; port enable/disable lives on `SwitchPorts.enabled`.      |
| `l3_firewall`, `dhcp_server`, `ip_routing`, WAN methods of `Router` | various | Wrong-shape per the inventory; superseded by `SwitchAcl`, `InterfaceDhcp`, `RoutingRead`. |

No `*WhiteBox` is added for the L3 capabilities yet — no L3-only deep-introspection
surface has been identified beyond the L2 `MacTableWhiteBox` candidate (recorded
in `LEVELS.md`); one would be added on signal.

## Tracking-file entries

### `GAPS.md`

- **`MulticastRouting` [MEDIUM]** — PIM-SM + RP reaches 5/6 present (4 ✓
  Meraki/Aruba/Juniper/Catalyst, 1 ◐ FortiSwitch, ✗ UniFi) — the same count as
  `GatewayRedundancy` — but is deferred on the **driving-test discriminator**: it
  has high surface area and no switch test drives it, whereas
  `GatewayRedundancy` carries a first-hop-failover test. Defer; reuse
  `RouteEntry` and the multicast vocab when seeded. Trigger: a switch scenario
  asserting routed multicast distribution.
- **`Bgp` on `L3Switch` [LOW/note]** — `bgp.py` is reused as-is, but BGP fails
  the L3-switch majority bar (4/6 under the ◐-counts-as-present convention —
  full on three families, ◐ standalone-only on FortiSwitch, absent on the
  design-target — short of the ≥ 5/6 bar). Recorded as composed only on the
  optional `L3SwitchRouted` variant; revisit if a switch test drives it into the
  mandatory baseline.
- **`SwitchStacks` / stack-scoped routing [LOW]** — physical stacking and
  stack-level L3 are exposed by Meraki/Aruba/UniFi/Catalyst; no current test.
  Defer.
- Inherited L2-layer deferrals (`IgmpSnooping` [HIGH], `PortMirror` [MEDIUM])
  are recorded in `docs/l2-switch-protocol-design.md` / its GAPS entries and
  cross-referenced here; `IgmpSnooping` cross-references `MulticastRouting` for
  shared multicast vocab.
- **L2Bridge HIGH entry [UPDATE] — owned by the L2 doc, cross-referenced here.**
  The deferred `L2Bridge` (2026-05-02, Linux-bridge-shaped: `brctl` / `ip link` /
  `nft table bridge` / `bridge fdb show`,
  `br-lan`-is-both-a-bridge-and-an-interface, CPE-triggered) is **NOT** realized
  by the switch archetypes — the realize-as-switch-native decision applies to the
  whole switch family (L2 + L3). To avoid the same mandatory edit being performed
  twice or not at all, the **single owner of the L2Bridge `[UPDATE]` is the L2
  doc** (`docs/l2-switch-protocol-design.md`, *Tracking-file entries → `GAPS.md`
  → `L2Bridge` HIGH entry*): the shared STP/FDB vocabulary the update points at
  (`StpMode`, `StpGuard`, `StpPortState`, `MacTableEntry`) is authored in
  `models/switch.py`, which is the L2 layer's module — so the cross-reference
  logically belongs to the L2 layer. This L3 doc records **only** that the L3
  layer likewise does not realize `L2Bridge` (its first-class object is the
  routed switchport / SVI, not "add port to bridge"; LAG/PoE/SVI have no home in
  `L2Bridge`), and defers the actual `GAPS.md` edit to the L2 doc rather than
  duplicating its three obligations here.

### `SPLITS.md`

- **`Router` RIB carve-out + `RouteEntry` reshape** — `get_routing_table()` /
  `RouteEntry` shared into `RoutingRead` for the switch; the WAN-uplink methods
  stay on the WAN-edge `Router`. `RouteEntry` (`models/wan_edge.py`) is
  **reshaped**: an `origin: RouteOrigin` field is added with a default. Log
  Signal / Decision(reshape) / Rationale / Migration. Cross-consumer impact: the
  field touches **both** existing `RouteEntry` consumers —
  `Router.get_routing_table()` and `Bgp.get_learned_routes()` — but the default
  keeps them source-compatible (no call-site change required); the switch gets a
  new read surface composing the same `RouteEntry`. The method carve-out itself
  leaves `Router` consumers unaffected (it keeps its methods).
- **`ApplianceVlans` SVI/DHCP reuse** — the SVI + DHCP fields of `VlanConfig` are
  shared into `RoutedInterfaces` / `InterfaceDhcp`, with `appliance_ip` renamed
  to `svi_ip`. Log the rename and any appliance-consumer migration.
- **`SwitchAcl` unified L2+L3** — record the decision to model **one** ACL
  surface (not separate L2 and L3 protocols) reusing `L3Rule`, since the reviewed
  switches use one engine.

### `LEVELS.md`

- **`MacTableWhiteBox(MacTable, Protocol)`** — raw FDB dump (`show mac
  address-table` / `show ethernet-switching table` equivalent) for kernel/ASIC
  FDB pinning; analogous to the L2Bridge `bridge fdb show` WhiteBox note.
  Black-box impact: base `MacTable` returns normalized entries; the raw dump
  lives on the WhiteBox only (LSP rule). Drivers expected to satisfy:
  Aruba CX / Juniper / Catalyst / Omada; **not** Meraki (no FDB API). No L3-only
  WhiteBox candidate identified yet — record "none yet" for the L3 capabilities.

### Registration

Add a new `switch` module to the auto-import tuple in `devices/__init__.py`.
Register at module scope: `register_device_type("managed_switch_l2", L2Switch)`
(in the L2 doc) and `register_device_type("managed_switch_l3", L3Switch)` here,
plus `register_device_type("managed_switch_l3_routed", L3SwitchRouted)` for the
optional BGP-bearing variant. `L3Switch(L2Switch, Protocol)` makes the
strict-superset relationship explicit and `runtime_checkable`-verifiable.

## Verification

Protocol-conformance tests per L3 capability; archetype registration +
`runtime_checkable` `isinstance` gate in the device-types test, including an
explicit assertion that any `L3Switch` is also an `L2Switch` (the strict-superset
invariant) and that `L3SwitchRouted` is an `L3Switch`; `mypy --strict`; the
RIB-carve-out regression confirming existing `Router` consumers are unaffected;
and a vendor-isolation grep ensuring no product name or vendor id appears
anywhere in the `testprotocols` **package source** (the contract surface).
Product names appear only in design docs like this one, where they document the
cross-vendor concept check — never in a model, enum, or protocol.
