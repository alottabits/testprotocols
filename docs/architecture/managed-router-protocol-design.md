# Design: vendor-neutral **managed (on-box-managed) router** archetype

| Field   | Value                                                                                                                                                                                                                                                                                       |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Status  | **Proposed — exploratory.** No code exists yet; this document is the design + evaluation framework, to be reviewed before any implementation and before the branch (`explore/managed-router-archetype`) is considered for merge.                                                            |
| Author  | rjvisser                                                                                                                                                                                                                                                                                    |
| Date    | 2026-08-20                                                                                                                                                                                                                                                                                  |
| Related | `docs/architecture/sdwan-appliance-protocol-design.md` (the precedent this follows), `docs/architecture/capability-only-archetypes.md`, `packages/testprotocols/SPLITS.md`, `packages/testprotocols/GAPS.md`, `packages/testprotocols/LEVELS.md`, `devices/sdwan.py`, `devices/switch.py`, `router.py`, `wan_link_admin.py`, `appliance_nat.py`, `switch_acl.py`, `site_to_site_vpn.py`, `gateway_redundancy.py` |

This document explains why `testprotocols` should carry a dedicated
**on-box-managed router** archetype alongside the existing SD-WAN *router*
(Linux twin) and SD-WAN *appliance* (cloud/controller-managed) archetypes, and
records the vendor-neutral shape proposed for it. It follows the SD-WAN
appliance design as its template: a cross-vendor concept check drives every
baseline capability, product names appear here only to evidence that a concept
is genuinely shared, and nothing vendor-specific leaks into the contract.

The **trigger** is a concrete estate of on-box-managed enterprise and
carrier/aggregation routers under test. As with the SD-WAN appliance, that
estate is the trigger, not the target: the deliverable is a **portable,
vendor-neutral test interface** that the major on-box-managed router families
(the reviewed set in §2) satisfy equally.

---

## 1. Context and problem statement

### Three WAN-edge substrates, not one

`testprotocols` already models two WAN-edge device classes:

- **`SdwanRouterDevice`** (`linux_sdwan_router`) — the **Linux digital twin**.
  Host substrate: `conntrack`, `pcap`, `ip_interface`, iptables `nat`, plus
  `wan_admin` (it shells `ip link set … down`). Built from a Linux host.
- **`SdwanApplianceDevice`** (`sdwan_appliance`) — the **cloud/controller-managed
  appliance**. Driven through a management API; no host substrate; and
  structurally **cannot admin-down its own uplink** (`Router` is a read-only
  surface, link administration is excluded — see the appliance doc and
  `SPLITS.md` 2026-06-12).

A traditional on-box-managed router — running IOS-XE, Junos, SR OS, VRP,
Comware, FortiOS, or RouterOS — is **neither**. It is a closed product like the
appliance, but it **manages itself on-box** through its own management plane
(CLI, and increasingly NETCONF/YANG, RESTCONF, or gNMI). Two consequences make
it a distinct archetype:

1. **It administers its own interfaces.** `shutdown` / `no shutdown` is on-box
   and universal across the reviewed families. This is the exact lever the
   *appliance* lacks and the *twin* has only via host shell — here it is a
   first-class, API-native operation. It is the archetype's defining trait.
2. **Its services are on-box-native, not host-native and not cloud-flat.** NAT
   is inside/outside translation (not iptables chains, not a cloud appliance's
   flat 1:1/1:N policy); firewalling is interface ACLs and/or a zone-based
   stateful engine; QoS is class-based; routing runs traditional IGP/BGP with
   on-box config and operational reads.

### Over- and under-specification against the existing archetypes

Modelling this device against either existing WAN-edge archetype fails the same
way the appliance failed against the Linux twin:

- **Against the twin (`SdwanRouterDevice`)** — *over*-specified: a closed router
  exposes no `conntrack`, no host `pcap`, no iptables `nat`, no per-`netdev`
  `ip_interface`. It can satisfy only stubs, exactly as the appliance could not
  satisfy the host levers.
- **Against the appliance (`SdwanApplianceDevice`)** — *both*. *Under*: the
  appliance archetype has no interface-admin lever at all (it was deliberately
  excluded), yet self-interface-admin is this class's defining capability. *Over
  in the wrong direction*: the appliance's `uplinks`/`lan`/`appliance_nat`
  surfaces are shaped for a cloud edge's WAN-uplink + LAN-VLAN object model, not
  a router's interface/routing model; and the appliance carries cloud-edge
  security bundles (`content_filtering`, `l7_firewall`, `ThreatPrevention`) that
  are not universal to the router class.

The conclusion mirrors the appliance decision: **a third archetype**, composing
what an on-box-managed router genuinely exposes, reusing the neutral capabilities
that already fit, and adding the few that have no home yet.

---

## 2. Device-class definition and inventory

**On-box-managed router:** a closed network product that manages *itself*
through an on-box management plane (CLI / NETCONF / RESTCONF / gNMI), forwards
at L3, and runs traditional routing. Not a general-purpose Linux host (rules out
the twin); not a cloud-only controller-managed edge (rules out the appliance
class and, for the router review, Meraki/Cradlepoint/Peplink/Versa).

### Device classes in scope

The archetype must cover the full on-box-managed router range, from the lean
carrier core to the feature-dense teleworker unit. Four broad classes recur
across every vendor's line-up:

- **Carrier / aggregation edge** — high-throughput L3 aggregation; a lean
  routing core with **no** LAN switching, voice, or access modems.
- **Enterprise branch** — full routing plus on-box security and services (NAT,
  firewall, QoS, VPN).
- **Teleworker / small branch** — the branch feature set plus an **integrated
  switch**, **xDSL** and/or **cellular** access WAN, and voice on some models.
- **Industrial** — a ruggedized subset of the branch / teleworker classes.

Standalone switches sometimes present in the same estate — enterprise
access/distribution switches, carrier Metro-Ethernet switches, and EtherSwitch
service modules — are **out of scope** for this archetype; see §10.

### Competitor families reviewed

Seven families were reviewed as the genuinely comparable, on-box-managed set
(the router-class analogue of the appliance review's five families). The
IOS/IOS-XE line — the market reference for the class — is the matrix's reference
column (§3); the six competitor families are:

- **Juniper Junos** — MX (carrier edge), ACX (aggregation/metro), SRX
  (branch/security router incl. switching, LTE, VDSL modules).
- **Nokia SR OS** — 7750 SR (carrier edge), 7250 IXR (aggregation), 7705 SAR
  (access/industrial, incl. cellular and xDSL variants).
- **Huawei VRP** — NetEngine AR (branch) and NE (carrier); the closest
  one-to-one structural mirror of the IOS branch shape.
- **HPE Comware** — FlexNetwork MSR (H3C heritage); a full branch competitor
  incl. voice cards, DSL, LTE, ADVPN.
- **Fortinet FortiOS** — FortiGate operated as a branch router; bridges to the
  SD-WAN review.
- **MikroTik RouterOS** — closed router product, large SMB/WISP base; probes the
  low end of the neutrality envelope.

**Excluded and why:** Arista EOS (aggregation/DC routing; lacks the branch set —
overlaps only the carrier/aggregation corner); Ericsson Cradlepoint, Peplink, Versa
(controller/cloud-managed → fail the on-box criterion, as Meraki did in the
appliance review); Ubiquiti EdgeRouter (EdgeOS effectively end-of-development);
Palo Alto PAN-OS (firewall family, adjacent to the SD-WAN review).

A structural fact recurs across **every** family, reference included: **capability
presence is platform-scoped within a family.** A vendor's carrier-metro platform
omits the NAT, zone firewall, voice, and DSL that concentrate on its branch
platforms — the pattern holds across the set (metro-vs-branch at the reference
vendor, SRX-vs-MX at Juniper, SAR-vs-7750 at Nokia). The neutral contract therefore
needs **per-method unsupported-capability signalling even inside one vendor
family**, and the core/tier split (below) carries the additive facets.

---

## 3. Cross-vendor concept check

✓ = fully present · ◐ = partial/caveated · ✗ = absent

| Capability | Cisco (ref) | Juniper | Nokia | Huawei | HPE | Fortinet | MikroTik |
| --- | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Interface admin (shut/no-shut own interfaces) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Static routes (per-entry) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| OSPF | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BGP (config + operational read) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| EIGRP / proprietary IGP | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| On-box NAT (source/PAT, static 1:1, port-forward) | ✓ | ✓ | ◐ CGN/hw | ✓ | ✓ | ✓ | ✓ |
| Stateful/zone firewall and/or ACL filtering | ✓ | ✓ | ◐ ACL✓/stateful hw | ✓ | ✓ | ✓ | ◐ chains, no zones |
| QoS (classify, mark DSCP, shape/police, queue) | ✓ MQC | ✓ CoS | ✓ H-QoS | ✓ | ✓ | ◐ shaping-policy | ◐ mangle+queues |
| IPsec site-to-site | ✓ | ✓ | ◐ hw on 7750 | ✓ | ✓ | ✓ | ✓ |
| Dynamic-overlay VPN (DMVPN-class) | ✓ DMVPN | ✓ ADVPN | ✗ | ✓ DSVPN | ✓ ADVPN(VAM) | ✓ ADVPN | ✗ |
| DHCP server (on-box) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DHCP client | ✓ | ✓ | ◐ mgmt/ZTP | ✓ | ✓ | ✓ | ✓ |
| NTP / syslog / SNMP | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FHRP (VRRP / HSRP-equivalent) | ✓ HSRP+VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP |
| IP SLA / reachability probing | ✓ IP SLA | ✓ RPM | ✓ OAM/TWAMP | ✓ NQA | ✓ NQA | ◐ link-monitor | ◐ netwatch |
| Flow telemetry (NetFlow/IPFIX-class) | ✓ NetFlow/FNF | ✓ J-Flow/IPFIX | ✓ Cflowd/IPFIX | ✓ NetStream | ✓ NetStream | ✓ (IPFIX) | ◐ Traffic-Flow |
| Integrated L2 switching | ✓ | ✓ branch SRX | ◐ service-model | ✓ | ✓ | ✓ | ✓ |
| Cellular / LTE / 5G WAN | ✓ | ✓ LTE mPIM | ◐ SAR-Hm only | ✓ | ✓ | ◐ select models | ✓ |
| xDSL WAN | ✓ | ✓ VDSL2 mPIM | ◐ SAR-M module | ✓ | ✓ | ◐ 60E-DSL only | ✗ |
| Voice (FXS/FXO/E1, SRST/SBC-class) | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ |

> **Citation status.** All rows except *IP SLA / reachability probing* and
> *Flow telemetry* are from the cited competitor review (§13). Those two rows
> were added per the scope-breadth decision and are populated from well-known
> per-vendor equivalents (Junos RPM, Nokia OAM/TWAMP, Huawei/HPE NQA; NetFlow/
> J-Flow/Cflowd/NetStream/Traffic-Flow, plus sampled sFlow) — **to be
> citation-verified at implementation** before either graduates from ◐ to ✓.

**Management planes.** Floor is "on-box CLI plus ≥1 programmatic interface", but
the programmatic interface is **NETCONF/YANG for four families** (Junos, SR OS,
VRP, Comware) and **vendor REST for two** (FortiOS, RouterOS). A NETCONF-only
harness would exclude two of six — the driver layer must not assume a single
programmatic transport. Cisco IOS-XE offers CLI + NETCONF + RESTCONF + gNMI.

**Classification of the surface:**

- **Universal (mandatory baseline)** — interface admin; static/OSPF/BGP; ACL/
  packet filtering; IPsec s2s; DHCP server + client; NTP/syslog; VRRP-shaped
  FHRP; QoS *by intent*; IP SLA/probing; flow telemetry.
- **Strong-majority (baseline, per-method unsupported-capability)** — on-box NAT
  (6/7; Nokia CGN-on-hardware); stateful/zone firewall (5/7); dynamic-overlay
  VPN (5/7).
- **Minority / additive (optional tiers)** — integrated switching (6/7 but
  model-scoped); cellular WAN; xDSL WAN.
- **Excluded from the neutral contract** — EIGRP (Cisco-only); voice (3/7 →
  deferred, second-consumer rule).

---

## 4. Decision

Add a vendor-neutral **`ManagedRouterDevice`** archetype (registered
`managed_router`), **alongside** — not replacing — `SdwanRouterDevice` and
`SdwanApplianceDevice`. It composes what an on-box-managed router universally
exposes, adds interface-admin as a first-class lever, and grows the additive
facets (WAN-edge reads, integrated switching, access-WAN) as **optional tiers**.

The excluded host-substrate levers (`conntrack`, `pcap`, `ip_interface`,
iptables `nat`) stay on the twin, exactly as for the appliance (§9). Packet
capture remains the `TrafficControllerDevice`'s job (the netem/capture precedent
in `SPLITS.md`).

---

## 5. The archetype — core plus optional tiers

The mandatory **core** is the lean universal surface — satisfiable by a
carrier-aggregation box that has no LAN switching, no access modems, and no
"active WAN uplink" concept. The additive facets are **orthogonal axes**, not a
linear superset chain (a teleworker unit has switching **and** access-WAN **and**
WAN-edge reads; a carrier box has none), so they are modelled as independent
optional tier Protocols. Concrete *combined* tier archetypes (e.g. a
teleworker that is switched + access-WAN + WAN-edge at once) are **composed on
consumer evidence** — plugin-local first, lifted to commons on a second consumer
(the `StreamingServerDevice` / `MaliciousHostDevice` playbook) — rather than
pre-enumerating the power set here.

```python
@runtime_checkable
class ManagedRouterDevice(BaseDeviceProtocol, Protocol):
    """On-box-managed router — universal core. Vendor-neutral; satisfiable by
    any CLI/NETCONF/RESTCONF/gNMI-managed router (IOS-XE, Junos, SR OS, VRP,
    Comware, FortiOS, RouterOS)."""

    interface_admin: InterfaceAdmin      # NEW — admin up/down + status of own interfaces (defining lever)
    routing_read: RoutingRead            # reuse — RIB read (RouteEntry)
    static_routes: StaticRoutes          # reuse — per-entry CRUD
    ospf: Ospf                           # reuse
    bgp: Bgp                             # reuse — config + operational reads
    nat: RouterNat                       # NEW-or-reuse — outcome-shaped (see §6, §7)
    acl: PacketFilterAcl                 # NEW-or-reuse — ordered ACL bound to interface+direction (§6, §7)
    stateful_firewall: StatefulFirewall  # NEW — behavior-shaped admission; per-method unsupported (5/7)
    qos: Qos                             # NEW — intent-level classify/mark/rate-limit/prioritize
    vpn: SiteToSiteVpn                   # reuse — static IPsec s2s + dynamic-overlay role model (per-method unsupported 5/7)
    dhcp_server: DhcpServer              # reuse — pool-based server
    dhcp_client: DhcpClient              # reuse — WAN-interface client
    fhrp: GatewayRedundancy              # reuse — VRRP-shaped
    probing: ReachabilityProbe           # NEW — IP SLA/RPM/NQA/TWAMP-class configured probe + result read
    flow_export: FlowExport              # NEW — NetFlow/IPFIX/NetStream-class exporter config
    ntp: NtpConfig                       # reuse
    syslog: SyslogConfig                 # reuse
    discovery: Discovery                 # reuse — LLDP-shaped (CDP is a driver detail)
    info: DeviceInfo                     # reuse — hardware model = coverage axis
    ownership: ConfigOwnership           # reuse — monitored-vs-managed

register_device_type("managed_router", ManagedRouterDevice)
```

Optional tier Protocols (each a strict `(ManagedRouterDevice, Protocol)`
superset adding one facet):

```python
@runtime_checkable
class WanEdgeRouterDevice(ManagedRouterDevice, Protocol):
    """Adds the SD-WAN/WAN-edge read surface — active uplink, path metrics,
    link health. Absent on carrier-aggregation cores (no 'active WAN uplink')."""
    routing: Router                      # reuse — WAN-uplink read surface (read-only)
    wan_admin: WanLinkAdmin              # reuse — forced WAN link-down by label (see §7 interface-admin note)

@runtime_checkable
class SwitchedRouterDevice(ManagedRouterDevice, Protocol):
    """Adds the integrated-switch facet — small-branch models with an integrated
    switch, and EtherSwitch service modules. Reuses the existing switch layer."""
    switch_ports: SwitchPorts            # reuse
    switch_vlans: SwitchVlans            # reuse
    spanning_tree: SpanningTree          # reuse
    port_poe: PortPoe                    # reuse (PoE-capable models)

@runtime_checkable
class AccessWanRouterDevice(ManagedRouterDevice, Protocol):
    """Adds access-side WAN modems — cellular and/or xDSL, with PPP/PPPoE
    session encapsulation. Teleworker / small-branch models."""
    cellular_wan: CellularWan            # NEW — LTE/5G modem state + config
    dsl_wan: DslWan                      # NEW — xDSL line state + config
    ppp: PppSession                      # NEW — PPP/PPPoE session config + status (rides DSL/cellular)
```

Registration of the tier archetypes is **deferred to consumer evidence**: which
facet combinations become named commons device types depends on which the test
environment actually instantiates. The `register_device_type` purity gate runs
downstream, so a testbed can register a combined archetype plugin-local until a
second consumer justifies lifting it.

---

## 6. Capabilities — reuse vs. net-new

| Concern | Capability | Disposition | X-vendor | Notes |
| --- | --- | --- | :--: | --- |
| Interface admin | `InterfaceAdmin` | **NEW** (neutralises `WanLinkAdmin`) | 7/7 | admin up/down + status, per interface name; §7 |
| RIB read | `RoutingRead` | reuse | 7/7 | `get_routing_table() -> [RouteEntry]` |
| Static routes | `StaticRoutes` | reuse | 7/7 | per-entry CRUD |
| OSPF | `Ospf` | reuse | 7/7 | |
| BGP | `Bgp` | reuse | 7/7 | config + operational reads (per-method) |
| NAT | `RouterNat` (or generalise `ApplianceNat`) | **NEW-or-reuse** | 6/7 | define by *outcome*, not attachment; §7 |
| ACL filtering | `PacketFilterAcl` (or generalise `SwitchAcl`) | **NEW-or-reuse** | 7/7 | ordered ACL, interface+direction; §7 |
| Stateful firewall | `StatefulFirewall` | **NEW** | 5/7 | behavior-shaped (return-traffic admission, per-session state); per-method unsupported |
| QoS | `Qos` | **NEW** | 7/7 | intent-level only; never MQC structure; §7 |
| IPsec s2s + dynamic overlay | `SiteToSiteVpn` | reuse | 5–7/7 | s2s universal; overlay 5/7 per-method; §7 |
| DHCP server | `DhcpServer` | reuse | 7/7 | pool-based; confirm pool shape on first driver |
| DHCP client | `DhcpClient` | reuse | 6/7 | Nokia's is ZTP/mgmt-oriented (◐) |
| FHRP | `GatewayRedundancy` | reuse | 7/7 | **VRRP-shaped** (HSRP/GLBP are Cisco-local) |
| Reachability/SLA probing | `ReachabilityProbe` | **NEW** | 5–7/7 | configured probe (icmp/udp/tcp/http/twamp) + result series; distinct from host-side `NetworkProbe` |
| Flow telemetry | `FlowExport` | **NEW** | 6–7/7 | exporter config (collector, sampling, timeouts); sFlow divergence noted |
| NTP / syslog | `NtpConfig` / `SyslogConfig` | reuse | 7/7 | telemetry path = syslog (as appliance) |
| Discovery | `Discovery` | reuse | 7/7 | LLDP-shaped |
| Model identity | `DeviceInfo` | reuse | 7/7 | coverage axis |
| Config ownership | `ConfigOwnership` | reuse | n/a | monitored-vs-managed |
| Integrated switching | `SwitchPorts`/`SwitchVlans`/`SpanningTree`/`PortPoe` | reuse (tier) | 6/7 | `SwitchedRouterDevice` |
| Cellular WAN | `CellularWan` | **NEW** (tier) | model-scoped | `AccessWanRouterDevice` |
| xDSL WAN | `DslWan` | **NEW** (tier) | model-scoped | `AccessWanRouterDevice` |
| PPP/PPPoE | `PppSession` | **NEW** (tier) | with access-WAN | rides DSL/cellular encapsulation |

---

## 7. Modeling decisions on the net-new / reuse-boundary calls

### Interface admin — neutralise `WanLinkAdmin`
The universal, defining lever is "administratively bring **any** interface
up/down and read its admin/oper state." `WanLinkAdmin` already encodes exactly
this behaviour but is **WAN-label-scoped** (`bring_wan_down(label)` /
`bring_wan_up(label)`) and composed only on the Linux twin. A carrier-aggregation
core has no "WAN" label, so the neutral core needs an **interface-generic**
`InterfaceAdmin` (`set_admin_state(interface, up|down)` / `get_admin_state`
/ status). Recommendation: introduce `InterfaceAdmin`; keep `WanLinkAdmin` as
the WAN-edge tier's label-scoped convenience (reused on `WanEdgeRouterDevice`),
or later reframe `WanLinkAdmin` as a thin alias over `InterfaceAdmin` — a
`SPLITS.md`-worthy generalisation to settle at implementation. Richer interface
*config* (IP assignment, description, encapsulation, MTU) is **deferred** — the
test-relevant baseline verb is admin-state, and the twin's host `ip_interface`
covers per-`netdev` config where a Linux substrate is in play.

### NAT — define by translation outcome
The set exhibits **five attachment models** for the same outcomes: interface
inside/outside (Cisco/Huawei/HPE), zone-pair rule-sets (Junos), policy/VIP
objects (FortiOS), a global rule chain (RouterOS), subscriber CGN pools (Nokia).
A neutral NAT contract must therefore be keyed to the **outcome** —
source/overload (PAT), static 1:1, destination/port-forward — never the
attachment. The existing `ApplianceNat` (`OneToOneNatRule` / `OneToManyNatRule`
/ `PortForwardRule`, each a list-replace) is *already* outcome-shaped. Options:
(a) **reuse `ApplianceNat` as-is** on the router (its name is a symbol, but
"appliance" misleads on a router); (b) **generalise** it — rename to a neutral
`EdgeNat`/`NatRules` sharing the models, a `SPLITS.md` reshape touching the
appliance archetype; (c) a **sibling** `RouterNat` sharing `models/…` NAT
records. Recommendation: **(b) generalise** — one outcome-shaped NAT capability
serving both edge archetypes, models shared, name de-branded. Nokia's
CGN-on-hardware raises unsupported-capability per method.

### ACL filtering vs. stateful firewall — split by shape, as the switch/appliance work did
Two distinct universal-ish concepts, kept separate (the `SwitchAcl`-vs-
`FirewallZones` precedent):
- **ACL filtering** (7/7) — an ordered rule list bound to an interface +
  direction. `SwitchAcl` already models exactly this (ordered whole-list
  replace, bound by port/VLAN + `AclDirection`). Router ACLs bind to
  interface+direction and are L3/L4 (occasionally L2). Recommendation: reuse the
  `SwitchAcl` **shape** under a de-branded neutral name `PacketFilterAcl` (a
  `SPLITS.md` generalisation), or reuse `SwitchAcl` directly if the switch
  binding vocabulary (`port`/`vlan`) is acceptable on a router interface.
- **Stateful/zone firewall** (5/7) — return-traffic admission with per-session
  state, expressed by **behaviour**, not by any one vendor's zone construct
  (Cisco ZBF zone-pairs, Junos security zones, Huawei/HPE ASPF zone-pairs;
  FortiOS native; MikroTik stateful chains without zones; Nokia stateful on
  optional hardware). New `StatefulFirewall`; drivers lacking a stateful engine
  raise unsupported-capability. Keep it **distinct** from `PacketFilterAcl` —
  stateless ordered filtering and stateful admission are different shapes on
  different subsets of the fleet.

### QoS — intent-level, never MQC structure
QoS is 7/7 present but the **most model-divergent** capability in the set: MQC
class/policy-maps (Cisco/Huawei/HPE), Junos CoS, Nokia H-QoS, FortiOS
shaping-policies, RouterOS mangle+HTB. The neutral `Qos` must express **intent**
— *classify on a match, mark DSCP, rate-limit (police/shape), prioritise
(queue)* — and expose none of the policy-map / queue-tree machinery. This is
strictly larger than `SwitchQos` (switch-port QoS) and `TrafficShaping`
(appliance per-uplink/per-client caps), so it is net-new; whether `TrafficShaping`
folds under it later is a follow-on, not part of this baseline.

### VPN — reuse `SiteToSiteVpn` for both static and dynamic overlay
`SiteToSiteVpn` is already neutral (role/hubs/subnets + peer status,
name-referenced, crypto-param-free) and its **hub/spoke role model already fits
dynamic-overlay topologies**. Static IPsec s2s is universal; the dynamic-overlay
*behaviour* (automatic spoke-to-spoke shortcut) is 5/7 via **four incompatible
mechanisms** — NHRP (Cisco DMVPN), IKEv2 shortcut exchange (Juniper ADVPN),
VAM registration (HPE ADVPN), FortiOS shortcut offers, Huawei DSVPN. The contract
carries the **behaviour** (is a shortcut established to a given peer?), never a
mechanism; Nokia and MikroTik raise unsupported-capability for the overlay read.
A shortcut-status read is the one likely `SiteToSiteVpn` addition — grow on
evidence (the appliance doc already flagged "no MESH role / no crypto params
yet — both grow on evidence").

### Probing and flow telemetry — the two selected baseline additions
- **`ReachabilityProbe`** — the router *originates* a configured probe
  (icmp/udp/tcp/http/twamp) and exposes a result series (latency/jitter/loss/
  reachability). This is a **config + operational-read** surface distinct from
  the host-side `NetworkProbe` (a one-shot prober on client/server archetypes)
  and from `Router.get_link_health` (a WAN-uplink health read). Cross-vendor:
  Cisco IP SLA, Junos RPM, Nokia OAM/TWAMP, Huawei/HPE NQA are ✓; FortiOS
  link-monitor and MikroTik netwatch are ◐ (narrower) → per-method unsupported.
- **`FlowExport`** — configure a flow exporter (collector, sampling rate,
  active/inactive timeouts). Cross-vendor by *protocol* varies (NetFlow/Flexible
  NetFlow, IPFIX, J-Flow, Cflowd, NetStream, RouterOS Traffic-Flow, and the
  packet-sampled **sFlow** on some). The neutral contract is the **exporter
  configuration intent**; the wire protocol is a driver detail, and sFlow's
  packet-sampling semantics (vs. flow-cache export) are recorded as a driver
  note, not a contract fork.

---

## 8. Neutrality notes and quirks (for the driver layer)

- **Per-method, not per-vendor.** Presence is platform-scoped inside every
  family (a vendor's carrier-metro platform omits the NAT/ZBF/voice/DSL its
  branch platforms carry). Unsupported-capability signalling is
  per method, per the established convention — never "this whole capability is
  absent for vendor X."
- **VRRP is the only portable FHRP.** HSRP and GLBP are Cisco-local; the
  `GatewayRedundancy` contract stays VRRP-shaped, and a Cisco driver maps HSRP
  onto it.
- **EIGRP is Cisco-only** (informational RFC 7868; **zero** reviewed-competitor
  adoption). It is **excluded from the neutral contract** — the router-world
  analogue of keeping vendor strike-ids out of `PacketInjector`/`ThreatPrevention`.
  A Cisco driver that must drive EIGRP does so through a plugin-local capability,
  never a commons method. Deferred entry in §11.
- **Overlay-VPN mechanism names never enter the contract.** "DMVPN" / "ADVPN" /
  "DSVPN" / "VAM" are vendor terms for one behaviour; the contract names the
  behaviour.
- **Config-transaction semantics split the set.** Commit-based (Junos, SR OS
  model-driven, IOS-XE candidate mode) vs. immediate-apply (classic IOS,
  Comware, FortiOS, RouterOS). A neutral driver must **verify-after-apply**
  rather than assume either — a driver-contract note, not a protocol shape.
- **Programmatic-transport floor.** CLI + ≥1 programmatic interface, but that
  interface is NETCONF for four families and vendor REST for two. Drivers own
  transport choice; the protocol surface is transport-agnostic.
- **Service-scoped platforms.** On Nokia SR OS an L3 interface lives inside an
  IES/VPRN service and L2 is VPLS/Epipe, not a global-scope interface or an
  EtherSwitch. A driver maps the neutral per-interface / per-port surface onto
  the service model; the contract assumes neither global-scope interfaces nor a
  hardware switch.

---

## 9. Excluded host-substrate levers (explicit)

Not on `ManagedRouterDevice` — they remain on `SdwanRouterDevice`
(`linux_sdwan_router`) with their `*WhiteBox` extensions, exactly as for the
appliance:

- `conntrack` — no netfilter connection table on a closed router.
- `pcap` (`PcapCapture`) — Linux-tool-shaped; capture is the
  `TrafficControllerDevice`'s job (the netem/capture precedent).
- `ip_interface` (`IpInterface`) — per-`netdev` `ip addr/link/mtu/mac`; the
  neutral `InterfaceAdmin` covers the universal admin-state lever instead.
- iptables `nat` (`Nat`) — replaced by the outcome-shaped NAT capability (§7).

Unlike the appliance, the managed router **does** carry an interface-admin lever
(`InterfaceAdmin`) — it administers itself on-box. That is the archetype's
defining inclusion.

No `*WhiteBox` extensions are proposed yet — no router-only deep-introspection
surface has been identified; one would be added on signal per `LEVELS.md`
(a `RoutingReadWhiteBox` raw-RIB dump and a `StatefulFirewallWhiteBox`
session-table dump are the likely first candidates).

---

## 10. Standalone switches — scoping note

Standalone switches sometimes present in the same estate are **not** modelled by
this archetype. Expectation:

- **Enterprise access/distribution switches** fold into the existing
  vendor-neutral `L2Switch` / `L3Switch` / `L3SwitchRouted` archetypes via a
  CLI/NETCONF driver. Those archetypes are capability-shaped and already
  anticipate on-box/structured-RPC switch families in `LEVELS.md`
  (`MacTableWhiteBox` note), so this is primarily a **driver** exercise, not a
  commons change.
- **EtherSwitch service modules** are the integrated-switch facet of a
  *router* — covered here by the `SwitchedRouterDevice` tier (§5), which reuses
  the same switch capability layer.
- **Carrier Metro-Ethernet switches** (EVC, QinQ, service-instance / pseudowire,
  MPLS L2VPN) exceed the enterprise `L2Switch`/`L3Switch` shape and are recorded
  as a **candidate `GAPS.md` entry** (`CarrierEthernet` / EVC capability) to
  assess separately on real test evidence.

---

## 11. Tracking-file entries to create on implementation

When (if) this design is picked up, the following entries land — recorded here
so the exploration is self-documenting:

**`GAPS.md` (deferred capabilities / archetypes):**

- `ManagedRouterDevice` core + the new capabilities (`InterfaceAdmin`,
  `StatefulFirewall`, `Qos`, `ReachabilityProbe`, `FlowExport`) — with this doc
  as the design record and the §3 matrix as the evidence.
- **EIGRP-class proprietary IGP** [priority: low] — single-vendor; plugin-local
  capability only, never neutral. Trigger: a Cisco-only test that must drive
  EIGRP through a typed surface.
- **Router voice** (`RouterVoice` — FXS/FXO/E1 + SRST/SBC-class) [priority:
  low] — 3/7 (Cisco, Huawei, HPE). Defer under the second-consumer rule; a large
  coherent family of its own. Trigger: a voice-gateway test.
- **`CellularWan` / `DslWan` / `PppSession`** access-WAN tier — net-new but
  module-scoped; land with the first `AccessWanRouterDevice` consumer.
- **`CarrierEthernet` (EVC)** [priority: low] — for carrier Metro-Ethernet
  switches (§10); assess separately.
- Richer **interface config** (IP/description/encap/MTU) and **SNMP-agent
  config** [priority: low] — deferred; syslog is the telemetry path, admin-state
  is the interface baseline.

**`SPLITS.md` (generalisations this archetype motivates):**

- `WanLinkAdmin` → neutral `InterfaceAdmin` (WAN-label-scoped admin becomes an
  interface-generic lever; §7).
- `ApplianceNat` → de-branded outcome-shaped NAT reused on both edge archetypes
  (§7).
- `SwitchAcl` → de-branded `PacketFilterAcl` ordered-ACL shape reused on the
  router (§7).

**`LEVELS.md`:** none at seed; `RoutingReadWhiteBox` / `StatefulFirewallWhiteBox`
are the first likely candidates (§9).

---

## 12. Verification approach (at implementation time)

Mirrors the appliance archetype: per-capability protocol-conformance tests;
archetype registration + `runtime_checkable` `isinstance` gate in the
device-types test; the `register_device_type` capability-only purity gate
(`test_archetype_purity.py`); `mypy --strict`; twin + appliance regression
(both unchanged); and the **vendor-isolation grep** ensuring no product name or
vendor id appears anywhere in the `testprotocols` package source. Product names
appear only in this design doc, where they evidence the cross-vendor concept
check — never in a model, enum, or protocol.

---

## 13. References

Vendor documentation consulted for the §3 concept check (public sources):

- Juniper — NETCONF/Junos XML API overview; ADVPN; SRX port-switching modes;
  SRX LTE and VDSL2 Mini-PIMs (`juniper.net/documentation`).
- Nokia — Model-driven management interfaces; 7750 local DHCP server;
  Multiservice ISA/ESA (NAT/firewall); 7705 SAR-Hm (cellular), SAR-M xDSL
  module (`documentation.nokia.com`, `infocenter.nokia.com`).
- Huawei — NetEngine AR NETCONF/YANG reference; DSVPN overview; AR2200
  datasheet (switching/cellular/xDSL cards); FXS/FXO voice interface cards
  (`support.huawei.com`).
- HPE — Comware 7 Fundamentals / NETCONF; FlexNetwork MSR ADVPN (VAM); MSR
  LTE / ADSL2+ / G.SHDSL modules; FXS/FXO/E1 voice SICs (`hpe.com/psnow`,
  vendor manuals).
- Fortinet — FortiOS REST Config/Monitor API; ADVPN and shortcut paths; VRRP;
  hardware switch; traffic-shaping policy; 60E-DSL datasheet
  (`docs.fortinet.com`).
- MikroTik — RouterOS REST API; OSPF; BGP; Mangle/queues; LTE/5G product group
  (`help.mikrotik.com`, `mikrotik.com`).

Deep-link URLs from the competitor review can be pasted inline here on request.
The vendor-isolation rule forbids vendor names and URLs in the `testprotocols`
package **source**, not in this design record — the same convention the SD-WAN
appliance doc follows.
