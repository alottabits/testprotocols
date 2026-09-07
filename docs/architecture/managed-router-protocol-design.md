# Design: vendor-neutral **managed (on-box-managed) router** archetype

| Field   | Value                                                                                                                                                                                                                                                                                       |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Status  | **Proposed — exploratory, revision 4 (2026-09-07).** No code exists yet. Revision 2 applied the approval-team review against the three-family trigger context (§2): reviewed-family list ratified at eight, the §3 matrix re-run with per-cell sources (§13), the net-new list re-derived through the zero-contract-change test (§7), on-box packet capture composed (§7, §9), voice added as an optional tier (§5). Revision 3 (same day) applies the appliance-overlap review: the archetype boundary restated by published operation set rather than management transport (§1), `InterfaceDhcp` replaces the mis-picked `DhcpServer` (§5), the WAN-edge tier composes the appliance's WAN-edge surface including SD-WAN policy by composition (§5, §7), a security-bundle tier candidate (§5), and a shared-with-appliance table (§6). Revision 4 (same day) applies the two-level review: the sea-level intent surface shared with the appliance, plus white-box extensions for raw state and console-only levers (§7, §9, §11, §12). To be re-reviewed before any implementation and before the branch (`explore/managed-router-archetype`) is considered for merge. |
| Author  | rjvisser                                                                                                                                                                                                                                                                                    |
| Date    | 2026-08-20 · rev. 2 2026-09-07                                                                                                                                                                                                                                                              |
| Related | `docs/architecture/sdwan-appliance-protocol-design.md` (the precedent this follows), `docs/architecture/capability-only-archetypes.md`, `docs/architecture/capture-analysis-operations-design.md`, `packages/testprotocols/SPLITS.md`, `packages/testprotocols/GAPS.md`, `packages/testprotocols/LEVELS.md`, `devices/sdwan.py`, `devices/switch.py`, `devices/cpe.py`, `devices/traffic.py`, `devices/voice.py`, `router.py`, `wan_link_admin.py`, `routed_interfaces.py`, `appliance_nat.py`, `switch_acl.py`, `firewall_zones.py`, `traffic_shaping.py`, `site_to_site_vpn.py`, `gateway_redundancy.py`, `network_probe.py`, `pcap_capture.py`, `interface_dhcp.py`, `appliance_vlans.py`, `l3_firewall.py`, `appliance_uplinks.py`, `uplink_ports.py`, `sdwan_policy_manager.py`, `l7_firewall.py`, `content_filtering.py`, `threat_prevention.py`, `docs/architecture/typed-path-steering-protocol-design.md` |

This document explains why `testprotocols` should carry a dedicated
**on-box-managed router** archetype alongside the existing SD-WAN *router*
(Linux twin) and SD-WAN *appliance* (cloud/controller-managed) archetypes, and
records the vendor-neutral shape proposed for it. It follows the SD-WAN
appliance design as its template: a cross-vendor concept check drives every
baseline capability, product names appear here only to evidence that a concept
is genuinely shared, and nothing vendor-specific leaks into the contract.

The **trigger** is a concrete estate of on-box-managed enterprise and
carrier/aggregation routers under test, drawn from three vendor families at
the review-baseline generations recorded in §2. As with the SD-WAN appliance,
that estate is the trigger, not the target: the deliverable is a **portable,
vendor-neutral test interface** that the major on-box-managed router families
(the ratified eight-family set in §2) satisfy equally.

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

A traditional on-box-managed router — running IOS-XE (autonomous mode), VRP,
OneOS6, Junos, SR OS, Comware, FortiOS, or RouterOS — is **neither**. It is a
closed product like the appliance. **How a driver reaches the box** — a cloud
dashboard API, a NETCONF session, a CLI over SSH — **is a driver concern and
plays no part in the split.** The archetypes differ in the **operation set
their management planes publish**, and two published-operation facts make the
router a distinct archetype:

1. **It publishes interface administration.** `shutdown` / `no shutdown` is a
   published operation on all eight reviewed router families and on none of
   the five cloud-managed appliance families (the appliance review verified
   the absence; `SPLITS.md` 2026-06-12). The *twin* has the lever only via host
   shell; here it is a first-class operation. It is the archetype's defining
   trait.
2. **It publishes on-box capture and interface-bound services.** The box
   captures its own traffic to a file (§7), which no reviewed appliance family
   publishes; firewalling is interface-bound ACLs plus a zone-based stateful
   engine; first-hop redundancy, OSPF, LLDP and per-interface DHCP relay are
   published operations. NAT, QoS by intent, static/BGP routing and
   site-to-site VPN are published on **both** classes — and those the router
   shares with the appliance by reusing the same capabilities (§6).

### Over- and under-specification against the existing archetypes

Modelling this device against either existing WAN-edge archetype fails the same
way the appliance failed against the Linux twin:

- **Against the twin (`SdwanRouterDevice`)** — *over*-specified: a closed router
  exposes no `conntrack`, no iptables `nat`, no per-`netdev` `ip_interface`. It
  can satisfy only stubs, exactly as the appliance could not satisfy the host
  levers.
- **Against the appliance (`SdwanApplianceDevice`)** — *both*. *Under*: the
  appliance archetype has no interface-admin lever and no capture at all (both
  deliberately excluded), yet self-interface-admin is this class's defining
  capability. *Over in the wrong direction*: the appliance's mandatory members
  include a WAN-uplink object model (`uplinks`, `sdwan_policy`) and security
  bundles (`content_filtering`, `l7_firewall`, `security`) that a
  carrier-aggregation core cannot satisfy — on a router they are **optional
  tiers** (§5), not core; and its LAN surface folds VLAN, address and DHCP into
  one record where a router's interface set is not VLAN-keyed (§7).

The conclusion mirrors the appliance decision: **a third archetype**, composing
what an on-box-managed router genuinely exposes. Revision 2 sharpens the second
half of that sentence: after the zero-contract-change test in §7, the core
composes **existing capabilities only** — two need a model field or a
de-branded name, none needs a new protocol at seed. Revision 3 closes the
other direction: every one of the appliance's seventeen members is either
reused on the core or a tier, or derivable from them (§6), so a test written
against the shared subset runs on both archetypes.

---

## 2. Device-class definition and inventory

**On-box-managed router:** a closed network product that manages *itself*
through an on-box management plane (CLI / NETCONF / RESTCONF / gNMI), forwards
at L3, and runs traditional routing. Not a general-purpose Linux host (rules out
the twin); not a cloud-only controller-managed edge (rules out the appliance
class and, for the router review, Meraki/Cradlepoint/Peplink/Versa). A platform
that can run in *either* an on-box mode or a controller-managed mode belongs to
this archetype **only in its on-box mode** (see the Cisco baseline below).

### Device classes in scope

The archetype must cover the full on-box-managed router range, from the lean
carrier core to the feature-dense teleworker unit. Four broad classes recur
across every vendor's line-up:

- **Carrier / aggregation edge** — high-throughput L3 aggregation; a lean
  routing core with **no** LAN switching, voice, or access modems.
- **Enterprise branch** — full routing plus on-box security and services (NAT,
  firewall, QoS, VPN), and on many models a voice gateway.
- **Teleworker / small branch** — the branch feature set plus an **integrated
  switch**, **xDSL** and/or **cellular** access WAN, and voice on some models.
- **Industrial** — a ruggedized subset of the branch / teleworker classes.

Standalone switches sometimes present in the same estate — enterprise
access/distribution switches, carrier Metro-Ethernet switches, and EtherSwitch
service modules — are **out of scope** for this archetype; see §10.

### Trigger families and review baselines

The trigger estate spans three vendor families. Each is reviewed at a
**baseline generation**, stated as the vendor's public version line so the
record stays portable; no fleet inventory or SKU appears here (the
de-identification rule of the 2026-08-20 revision stands).

- **Cisco IOS-XE, release 17.9 and later, in autonomous mode.** The 17.9 train
  publishes release notes for the ISR 1000, ISR 4000, ASR 1000, Catalyst
  8000V/8200/8300/8500, ASR 900/920, and the Catalyst IR1101/IR1800/IR8100/
  IR8300 rugged routers, so all four device classes above sit inside one
  software line. Classic IOS platforms fall outside the floor. Since 17.2.1r
  one universalk9 image runs in either **autonomous mode** (IOS-XE via
  CLI/NETCONF/YANG, `configure terminal`) or **controller mode** (Catalyst
  SD-WAN via SD-WAN Manager, `config-transaction`); configuration does not
  survive a mode switch. A controller-mode box is an `SdwanApplianceDevice`
  (the Catalyst SD-WAN column of the appliance design), never an instance of
  this archetype. **Operating mode is a per-instance fact the driver asserts.**
- **Huawei VRP 5.170 — the VRP5 line (AR / NetEngine AR).** `display version`
  on NetEngine AR V300R019 reports `VRP (R) software, Version 5.170 (AR6300
  V300R019C00)`; the string identifies the VRP5 platform on the AR and
  NetEngine AR branch line, with V300R019, V300R021 and V300R022 documented.
  The carrier NetEngine 40E/8000 line runs the separate **VRP8** train
  (V800Rxxx) and is **out of scope pending confirmation** (§14). Where the
  programmatic-interface floor (below) matters, the release train is the
  better pin: the NETCONF/YANG API reference is published at V300R003 for the
  classic AR series and at V300R019 for NetEngine AR, while a classic-AR box
  on a V200R0xx train can report 5.170 and still be CLI-only.
- **Ekinops OneAccess ONE-series on OneOS6.** "One box" is Ekinops' solution
  positioning ("All-in-One Box": voice, data and access in one CPE), not a
  product name; the family is the OneAccess ONE-series pCPE running
  **OneOS6**, the operating system introduced December 2017 as the successor
  to OneOS5. Ekinops' own OneOS6 platform list covers the ONE4xx/5xx/6xx
  branch units, the ONE15xx/25xx/35xx enterprise units, the ONE-5G, and the
  ONEvRouter / OneOS6-LIM virtual forms. Public documentation exposes no
  version numbering (a 2025 product-change notice references a 6.15 line,
  unverified), so the working floor is **the OneOS6 generation, OneOS5
  excluded**, with the minor version pinned on first driver evidence — the
  same version-pinned re-verification the appliance design applied to
  Catalyst SD-WAN Manager 20.12.

Two structural facts follow from the baselines. **The carrier/aggregation
class is evidenced in the trigger estate by one family only** (IOS-XE on the
ASR 900/920/1000 and Catalyst 8500 class); the class stays in the neutral
review through the Juniper MX and Nokia 7750 competitor columns. And **every
trigger family carries voice** (§3, §5).

### Competitor families reviewed

Five further families were reviewed as the genuinely comparable, on-box-managed
set (the router-class analogue of the appliance review's five families):

- **Juniper Junos** — MX (carrier edge), ACX (aggregation/metro), SRX
  (branch/security router incl. switching, LTE, VDSL modules).
- **Nokia SR OS** — 7750 SR (carrier edge), 7250 IXR (aggregation), 7705 SAR
  (access/industrial, incl. cellular and xDSL variants).
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

**Ratified reviewed-family list (revision 2): eight families** — the three
trigger families at their baselines plus the five competitors. Every "N/8"
count in this document is against that list; a future family joins it by a
dated revision, as the appliance design's fifth-family review did.

A structural fact recurs across **every** family, trigger and competitor
alike: **capability presence is platform-scoped within a family.** A vendor's
carrier-metro platform omits the NAT, zone firewall, voice, and DSL that
concentrate on its branch platforms — the pattern holds across the set
(carrier-vs-branch platforms inside the IOS-XE line, VRP8-vs-VRP5 at Huawei,
SRX-vs-MX at Juniper, SAR-vs-7750 at Nokia), and licence gating adds a second
axis on OneOS6 (zone firewall and, on some models, the NETCONF server are
licence-flagged). The neutral contract therefore needs **per-method
unsupported-capability signalling even inside one vendor family**, and the
core/tier split (§5) carries the additive facets.

---

## 3. Cross-vendor concept check

✓ = fully present · ◐ = partial/caveated · ✗ = absent · ¹ = public datasheets
silent; verify against the OneOS6 command/YANG reference (customer portal)
before promoting to ✓ · ² = competitor cell from reviewer product knowledge
(revision-3 rows); citation-verify at implementation — the trigger-column
cells of those rows are sourced (§13)

| Capability | Cisco IOS-XE ≥ 17.9 | Huawei VRP 5.170 | Ekinops OneOS6 | Juniper | Nokia | HPE | Fortinet | MikroTik |
| --- | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Interface admin (shut/no-shut own interfaces) | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Static routes (per-entry) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| OSPF | ✓ | ✓ | ✓ v2 only | ✓ | ✓ | ✓ | ✓ | ✓ |
| BGP (config + operational read) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| EIGRP / proprietary IGP | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| On-box NAT (source/PAT, static 1:1, port-forward) | ✓ | ✓ | ✓ | ✓ | ◐ CGN/hw | ✓ | ✓ | ✓ |
| Stateful/zone firewall | ✓ ZBF | ✓ zones + ASPF | ◐ ZBF (licensed) | ✓ | ◐ stateful hw | ✓ | ✓ | ◐ chains, no zones |
| Security bundles (IPS, URL filtering, app-aware firewall) | ✓ UTD (licensed) | ✓ IPS + URL filtering | ◐ DPI / app-ID only | ✓² SRX UTM | ✗² | ◐² | ✓² | ✗² |
| ACL / packet filtering (interface + direction) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| QoS (classify, mark DSCP, shape/police, queue) | ✓ MQC | ✓ MQC-style policy | ✓ CBQ/CB-WFQ/LLQ | ✓ CoS | ✓ H-QoS | ✓ | ◐ shaping-policy | ◐ mangle+queues |
| IPsec site-to-site | ✓ | ✓ | ✓ | ✓ | ◐ hw on 7750 | ✓ | ✓ | ✓ |
| Dynamic-overlay VPN (spoke-to-spoke shortcut) | ✓ DMVPN | ✓ DSVPN | ✗ (DVTI is hub-dynamic only) | ✓ ADVPN | ✗ | ✓ ADVPN(VAM) | ✓ ADVPN | ✗ |
| SLA-conditioned path steering (probe + track + policy routing) | ✓ IP SLA + track + PBR | ✓ NQA + track + PBR | ◐ native under SD-WAN licence | ✓² RPM + ip-monitoring | ✗² | ✓² NQA + track + PBR | ✓² SD-WAN rules | ◐² netwatch + routing marks |
| DHCP server (on-box) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DHCP client | ✓ | ✓ | ✓ | ✓ | ◐ mgmt/ZTP | ✓ | ✓ | ✓ |
| NTP / syslog / SNMP | ✓ | ✓ | ◐¹ (syslog, SNMP ✓; NTP unlisted) | ✓ | ✓ | ✓ | ✓ | ✓ |
| FHRP (VRRP / HSRP-equivalent) | ✓ HSRP+VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP |
| IP SLA / reachability probing (configured probe + result read) | ✓ IP SLA | ✓ NQA + TWAMP | ◐¹ "QoS measurement probe" | ✓ RPM | ✓ OAM/TWAMP | ✓ NQA | ◐ link-monitor | ◐ netwatch |
| Flow telemetry (NetFlow/IPFIX-class) | ✓ FNF | ✓ NetStream | ✓ NetFlow | ✓ J-Flow/IPFIX | ✓ Cflowd/IPFIX | ✓ NetStream | ✓ IPFIX | ◐ Traffic-Flow |
| On-box packet capture to file | ✓ EPC | ✓ capture-packet | ◐¹ "flow capture and decoding" | ◐ SRX datapath ✓ / MX RE-bound | ✓ mirror-dest pcap | ✓ packet-capture | ◐ sniffer (text stream) | ✓ /tool sniffer |
| Discovery (LLDP) | ✓ (+CDP) | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Integrated L2 switching | ✓ | ✓ | ✓ | ✓ branch SRX | ◐ service-model | ✓ | ✓ | ✓ |
| Cellular / LTE / 5G WAN | ✓ | ✓ | ✓ LTE + 5G | ✓ LTE mPIM | ◐ SAR-Hm only | ✓ | ◐ select models | ✓ |
| xDSL WAN | ✓ | ✓ | ✓ model-scoped (VDSL2, ADSL2+, G.SHDSL EFM) | ✓ VDSL2 mPIM | ◐ SAR-M module | ✓ | ◐ 60E-DSL only | ✗ |
| Voice gateway (FXS/FXO/BRI/PRI, SIP trunk / SBC-class) | ✓ | ✓ | ✓ + embedded SBC | ✗ | ✗ | ✓ | ✗ | ✗ |

> **Citation status.** Every cell is backed by a source in §13. The trigger
> columns are version-pinned to the §2 baselines (IOS-XE 17.9 guides and
> release notes; NetEngine AR V300R019 configuration guides and NETCONF YANG
> reference; OneOS6 datasheets dated 2022–2026). The four Ekinops cells marked
> ¹ are the only cells where the public record is silent on the exact verb;
> they are ◐ until verified, not ✗. The Junos/Nokia/HPE/FortiOS/RouterOS
> capture cells were added in revision 2 with sources; the two revision-3 rows
> (path steering, security bundles) are sourced on the trigger columns and
> marked ² on the competitor columns; the remaining competitor cells carry
> over from the 2026-08-20 review.

**Management planes.** The floor is "on-box CLI plus ≥1 programmatic
interface". **NETCONF/YANG is that interface on six of eight families**
(IOS-XE, VRP, OneOS6, Junos, SR OS, Comware); IOS-XE additionally offers
RESTCONF and gNMI, OneOS6 a REST API; FortiOS and RouterOS are **vendor-REST
only**. Two consequences: all three trigger families are NETCONF-capable, so a
NETCONF-first *driver* family covers the whole trigger estate; and the
*contract* stays transport-agnostic because two reviewed families cannot speak
NETCONF at all. On OneOS6 the NETCONF server is licence-flagged on some
models — a per-instance fact, handled like any other unsupported method.

**Classification of the surface (of 8):**

- **Universal (mandatory baseline)** — interface admin (7 ✓ + 1 ◐¹);
  static/OSPF/BGP (8); ACL filtering (8); IPsec s2s (7 + 1 ◐); DHCP server
  (8) + client (7 + 1 ◐); NTP/syslog/SNMP (7 + 1 ◐¹); VRRP-shaped FHRP (8);
  QoS *by intent* (6 + 2 ◐); flow telemetry (7 + 1 ◐); LLDP discovery
  (7 + 1 ◐¹).
- **Strong-majority (baseline, per-method unsupported-capability)** — on-box
  NAT (7 + 1 ◐); stateful/zone firewall (5 ✓ + 3 ◐); dynamic-overlay VPN
  (5 ✓ + 3 ✗ — now ✗ on one trigger family); configured reachability probing
  (5 ✓ + 3 ◐); **on-box packet capture (5 ✓ + 3 ◐)**; **SLA-conditioned path
  steering (5 ✓ + 2 ◐ + 1 ✗ — WAN-edge tier, by composition, §7)**.
- **Minority / additive (optional tiers)** — integrated switching (7 + 1 ◐,
  model-scoped); cellular WAN (6 + 2 ◐); xDSL WAN (5 + 2 ◐ + 1 ✗); **voice
  gateway (4 ✓ — and 3 of 3 trigger families)**; **security bundles (4 ✓ +
  2 ◐ + 2 ✗ — security tier, §7)**.
- **Excluded from the neutral contract** — EIGRP (1/8).

---

## 4. Decision

Add a vendor-neutral **`ManagedRouterDevice`** archetype (registered
`managed_router`), **alongside** — not replacing — `SdwanRouterDevice` and
`SdwanApplianceDevice`. It composes what an on-box-managed router universally
exposes, carries interface-admin and on-box capture as first-class levers, and
grows the additive facets (the appliance's WAN-edge surface, integrated
switching, access-WAN, voice gateway, security bundles) as **optional tiers**.

Revision 2 changes two things about *how* the core is built, not *what* it
is: the core composes **existing capabilities only** (§5, §7), and the two
capabilities the 2026-08-20 revision seeded on scope-breadth alone
(`ReachabilityProbe`, `FlowExport`) are **GAPS-deferred** until a consumer
needs them, per the repo's first-consumer bar.

The excluded host-substrate levers (`conntrack`, `ip_interface`, iptables
`nat`) stay on the twin, exactly as for the appliance (§9). Packet capture is
**no longer excluded**: the traffic controller remains the wire vantage of
record, and the router adds the device vantage (§7).

---

## 5. The archetype — core plus optional tiers

The mandatory **core** is the lean universal surface — satisfiable by a
carrier-aggregation box that has no LAN switching, no access modems, no voice
ports, and no "active WAN uplink" concept. The additive facets are
**orthogonal axes**, not a linear superset chain (a teleworker unit has
switching **and** access-WAN **and** WAN-edge reads **and** possibly voice; a
carrier box has none), so they are modelled as independent optional tier
Protocols. Concrete *combined* tier archetypes are **composed on consumer
evidence** — plugin-local first, lifted to commons on a second consumer (the
`StreamingServerDevice` / `MaliciousHostDevice` playbook) — rather than
pre-enumerating the power set here.

```python
@runtime_checkable
class ManagedRouterDevice(BaseDeviceProtocol, Protocol):
    """On-box-managed router — universal core. Vendor-neutral; satisfiable by
    any CLI/NETCONF/RESTCONF/gNMI-managed router operated on-box (IOS-XE in
    autonomous mode, VRP, OneOS6, Junos, SR OS, Comware, FortiOS, RouterOS)."""

    interfaces: RoutedInterfaces         # reuse + `enabled` field (SPLITS) — admin state + L3 identity of own interfaces: the defining lever (§7)
    routing_read: RoutingRead            # reuse — RIB read (RouteEntry)
    static_routes: StaticRoutes          # reuse — per-entry CRUD
    ospf: Ospf                           # reuse — OspfVersion.V3 per-method
    bgp: Bgp                             # reuse — config + operational reads
    nat: ApplianceNat                    # reuse as-is — outcome-shaped; de-branded name on landing (SPLITS, §7)
    acl: SwitchAcl                       # reuse as-is — binding = interface name; de-branded name on landing (SPLITS, §7)
    firewall_zones: FirewallZones        # reuse — zone-shaped stateful admission; per-method unsupported (5 ✓ + 3 ◐) (§7)
    traffic_shaping: TrafficShaping      # reuse — QoS by intent via ShapingRule (classify/mark/limit/prioritise); appliance-shaped caps per-method (§7)
    vpn: SiteToSiteVpn                   # reuse — static IPsec s2s + overlay role model; overlay reads per-method (§7)
    interface_dhcp: InterfaceDhcp        # reuse — per-interface DHCP server/relay over the appliance DHCP sub-models (§7)
    dhcp_client: DhcpClient              # reuse — WAN-interface client
    fhrp: GatewayRedundancy              # reuse — VRRP-shaped
    network_probe: NetworkProbe          # reuse — on-box one-shot reachability (ping/traceroute); feeds `await_reachability` (§7)
    pcap: PcapCapture                    # reuse — on-box capture at the device vantage; per-method unsupported (§7, §9)
    ntp: NtpConfig                       # reuse
    syslog: SyslogConfig                 # reuse — telemetry path (as appliance)
    discovery: Discovery                 # reuse — LLDP-shaped (CDP is a driver detail)
    info: DeviceInfo                     # reuse — hardware model = coverage axis
    ownership: ConfigOwnership           # reuse — monitored-vs-managed

register_device_type("managed_router", ManagedRouterDevice)
```

**Zero net-new capabilities at seed.** Every member above exists today. Two
need a `SPLITS.md` entry (the `enabled` field on `RoutedInterface`; the
de-branded names for `ApplianceNat` / `SwitchAcl`), and `PcapCapture`'s
tool-named methods are a de-branding candidate (§7) — none needs a new
protocol. The evaluation order that produced each disposition is recorded in
§7 so an implementer who finds a derivation failing knows what the fallback is.

Optional tier Protocols (each a strict `(ManagedRouterDevice, Protocol)`
superset adding one facet):

```python
@runtime_checkable
class WanEdgeRouterDevice(ManagedRouterDevice, Protocol):
    """Adds the WAN-edge surface the appliance archetype publishes — uplink
    reads, the edge firewall triad, uplink wiring, and SD-WAN policy — so a
    test written against the appliance's shared subset runs here unchanged.
    Absent on carrier-aggregation cores (no 'active WAN uplink').
    `WanLinkAdmin` is deliberately NOT composed here: the lever is already
    encoded once on the core (`interfaces` + `enabled`), and a second
    label-scoped encoding would be the redundant-encoding smell SPLITS.md
    exists to catch."""
    routing: Router                      # reuse — WAN-uplink read surface (read-only)
    uplinks: ApplianceUplinks            # reuse — UplinkStatus (address, gateway, DNS, state) per uplink
    uplink_ports: UplinkPorts            # reuse — declared uplink→switch-port wiring (testbed topology fact)
    l3_firewall: L3Firewall              # reuse — outbound/inbound/VPN rule triad, derived as interface ACLs (§7)
    sdwan_policy: SdwanPolicyManager     # reuse — SLA policies + uplink selection by composition (probe + track + policy routing); per-method (§7)

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
    cellular_wan: CellularWan            # NEW (tier) — LTE/5G modem state + config
    dsl_wan: DslWan                      # NEW (tier) — xDSL line state + config
    ppp: PppSession                      # NEW (tier) — PPP/PPPoE session config + status (rides DSL/cellular)

@runtime_checkable
class VoiceGatewayRouterDevice(ManagedRouterDevice, Protocol):
    """Adds the voice-gateway facet — analog/digital voice ports (FXS/FXO/
    BRI/PRI), SIP trunk registration, and call-state reads. Present on the
    branch and teleworker platforms of 4/8 reviewed families and on all three
    trigger families; absent on carrier cores. (§7 Voice)"""
    voice: RouterVoice                   # NEW (tier) — port inventory + admin/oper state, trunk status, active calls

@runtime_checkable
class SecuredRouterDevice(ManagedRouterDevice, Protocol):
    """Adds the security bundles the appliance archetype carries as mandatory
    members — application-aware firewall, content filtering, intrusion and
    malware prevention — reused as-is. Present on 4/8 reviewed families (IOS-XE
    UTD, VRP IPS + URL filtering, Junos SRX UTM, FortiOS) and licence- or
    platform-scoped inside each; absent on carrier cores. (§7 Security bundles)"""
    l7_firewall: L7Firewall              # reuse — application-match rules; per-method where no app engine
    content_filtering: ContentFiltering  # reuse — category + URL rules
    security: ThreatPrevention           # reuse — IPS/IDS mode, anti-malware, security events; per-method
```

Registration of the tier archetypes is **deferred to consumer evidence**: which
facet combinations become named commons device types depends on which the test
environment actually instantiates. The `register_device_type` purity gate runs
downstream, so a testbed can register a combined archetype plugin-local until a
second consumer justifies lifting it.

---

## 6. Capabilities — reuse vs. net-new

Dispositions are the *evaluated* result of the §7 zero-contract-change test,
not a presumption: **reuse** (as-is), **reuse + field / rename** (a
`SPLITS.md` entry, no new protocol), **defer** (a `GAPS.md` entry until a
consumer), **new (tier)** (lands with the first consumer of the tier).

| Concern | Capability | Disposition | X-vendor (of 8) | Notes |
| --- | --- | --- | :--: | --- |
| Interface admin + L3 identity | `RoutedInterfaces` (+ `RoutedInterface.enabled`) | **reuse + field** | 7 + 1 ◐¹ | one encoding of the lever, mirrors `SwitchPort.enabled`; fallbacks in §7 |
| RIB read | `RoutingRead` | reuse | 8 | `get_routing_table() -> [RouteEntry]` |
| Static routes | `StaticRoutes` | reuse | 8 | per-entry CRUD |
| OSPF | `Ospf` | reuse | 8 | v3 per-method (OneOS6 lists v2 only) |
| BGP | `Bgp` | reuse | 8 | config + operational reads (per-method) |
| NAT | `ApplianceNat` | **reuse, rename on landing** | 7 + 1 ◐ | already outcome-shaped; §7 |
| ACL filtering | `SwitchAcl` | **reuse, rename on landing** | 8 | binding string = interface name; §7 |
| Stateful / zone firewall | `FirewallZones` | reuse | 5 + 3 ◐ | zone membership + zone-pair policy = the ZBF shape; per-method; §7 |
| QoS by intent | `TrafficShaping` | reuse | 6 + 2 ◐ | `ShapingRule` = classify + mark + limit + priority; caps per-method; §7 |
| IPsec s2s + dynamic overlay | `SiteToSiteVpn` | reuse | 7 + 1 ◐ / 5 + 3 ✗ | s2s universal; overlay per-method; §7 |
| Per-interface DHCP (server / relay) | `InterfaceDhcp` | reuse | 8 | `InterfaceDhcpConfig` shares the appliance DHCP sub-models (`DhcpMode`, `DhcpOption`, `DhcpReservation`, `ReservedRange`); §7 |
| DHCP client | `DhcpClient` | reuse | 7 + 1 ◐ | Nokia's is ZTP/mgmt-oriented (◐) |
| FHRP | `GatewayRedundancy` | reuse | 8 | **VRRP-shaped** (HSRP/GLBP are Cisco-local) |
| One-shot reachability | `NetworkProbe` | reuse | 8 | on-box ping/traceroute; feeds `await_reachability`; §7 |
| Configured probe + result series | `ReachabilityProbe` | **defer (GAPS)** | 5 + 3 ◐ | IP SLA/NQA/RPM/TWAMP-class; reuse `PathMetrics` when it lands; §7 |
| Flow telemetry | `FlowExport` | **defer (GAPS)** | 7 + 1 ◐ | exporter config intent; needs a collector-side consumer; §7 |
| On-box packet capture | `PcapCapture` | **reuse; de-brand candidate** | 5 + 3 ◐ | device-vantage capture; file fetched off-box by the driver; §7, §9 |
| NTP / syslog | `NtpConfig` / `SyslogConfig` | reuse | 7 + 1 ◐¹ | telemetry path = syslog (as appliance) |
| Discovery | `Discovery` | reuse | 7 + 1 ◐¹ | LLDP-shaped |
| Model identity | `DeviceInfo` | reuse | 8 | coverage axis; firmware/mode facts are driver facts (§8) |
| Config ownership | `ConfigOwnership` | reuse | n/a | monitored-vs-managed |
| WAN-uplink reads | `Router`, `ApplianceUplinks` | reuse (tier) | n/a | `WanEdgeRouterDevice`; the two status records already coexist on the appliance (§7) |
| Uplink wiring | `UplinkPorts` | reuse (tier) | n/a | `WanEdgeRouterDevice`; testbed topology fact |
| Edge firewall triad | `L3Firewall` | reuse (tier) | 8 | `WanEdgeRouterDevice`; derived as interface ACLs on WAN / tunnel interfaces (§7) |
| SD-WAN policy (SLA + uplink selection) | `SdwanPolicyManager` | reuse (tier), by composition | 5 + 2 ◐ + 1 ✗ | `WanEdgeRouterDevice`; probe + track + policy routing; per-method (§7) |
| Security bundles | `L7Firewall` / `ContentFiltering` / `ThreatPrevention` | reuse (tier) | 4 + 2 ◐ + 2 ✗ | `SecuredRouterDevice` (§7) |
| Integrated switching | `SwitchPorts`/`SwitchVlans`/`SpanningTree`/`PortPoe` | reuse (tier) | 7 + 1 ◐ | `SwitchedRouterDevice` |
| Cellular WAN | `CellularWan` | **new (tier)** | 6 + 2 ◐ | `AccessWanRouterDevice` |
| xDSL WAN | `DslWan` | **new (tier)** | 5 + 2 ◐ + 1 ✗ | `AccessWanRouterDevice` |
| PPP/PPPoE | `PppSession` | **new (tier)** | with access-WAN | rides DSL/cellular encapsulation |
| Voice gateway | `RouterVoice` | **new (tier)** | 4 | `VoiceGatewayRouterDevice`; 3/3 trigger families; §7 |

### Shared with the appliance

The functional overlap with the managed SD-WAN appliance is large, and the
management transport is not a protocol fact (§1). Read against
`SdwanApplianceDevice`'s seventeen members, the managed router covers every
one — by reuse, or by derivation from the capabilities it does compose:

| `SdwanApplianceDevice` member | Managed-router home | How |
| --- | --- | --- |
| `routing: Router` | `WanEdgeRouterDevice` | reuse as-is |
| `static_routes`, `bgp`, `vpn`, `traffic_shaping`, `appliance_nat`, `syslog`, `info`, `ownership` | core | reuse as-is |
| `uplinks`, `uplink_ports` | `WanEdgeRouterDevice` | reuse as-is |
| `l3_firewall` | `WanEdgeRouterDevice` | reuse; the driver derives the triad as interface ACLs (§7) |
| `sdwan_policy` | `WanEdgeRouterDevice` | reuse; behaviour by composition, per-method (§7) |
| `l7_firewall`, `content_filtering`, `security` | `SecuredRouterDevice` | reuse as-is (§7) |
| `lan: ApplianceVlans` | derivable | `RoutedInterfaces` + `InterfaceDhcp` over the same DHCP sub-models; `ApplianceVlans` satisfiable by derivation (§7) |

A test step typed against any capability in the first six rows runs on both
archetypes without change. The unit of reuse is the capability protocol under
structural typing (the operations already work that way — `await_reachability`
is typed against `NetworkProbe`, the failover operation against `Router`), so
no shared base archetype is introduced: a superset relation fails on carrier
cores, and a common base would only help a step that needs several capabilities
at once, which consumers already express as structural slices. Revisit only if
implementation shows the same multi-capability step written twice.

---

## 7. Modeling decisions on the reuse-boundary calls

Each call below was re-run in revision 2 under the rule the review skill
applies to every proposal: **test a zero-contract-change derivation in the
driver before accepting any contract change.** The recorded order is the
implementer's fallback ladder.

### Interface admin — one encoding, on the configured object
The universal, defining lever is "administratively bring **any** interface
up/down and read its state." Three existing surfaces already carry the verb:
`WanLinkAdmin` (`bring_wan_down(label)` / `bring_wan_up(label)`, an opaque
label a router driver could treat as an interface name), `SwitchPort.enabled`
(admin state on the switch's configured port object), and `RoutedInterfaces`
(`list/get/set_interface` over `RoutedInterface(name, mode, ip_address,
subnet, vlan_id)` — the SVI / routed-port / loopback surface of the L3-switch
archetype, which is exactly a router's interface surface). The 2026-08-20
revision proposed a new `InterfaceAdmin` and deferred "richer interface
config"; it did not consider `RoutedInterfaces` at all.

**Evaluation order and provisional pick:**

1. **`RoutedInterfaces` + a defaulted `enabled: bool = True` field on
   `RoutedInterface`** (provisional pick). One object carries L3 identity *and*
   admin state, mirroring `SwitchPort.enabled`; `get_interface` reads the
   configured state back; the previously deferred "richer interface config"
   arrives for free. A defaulted field is not source-breaking. Open point to
   settle on the first driver: a dynamically addressed WAN interface
   (DHCP-client / PPPoE) has no static `ip_address`; the read-side convention
   is "the current address, empty when unassigned", and the record's docstring
   says so.
2. **`WanLinkAdmin` with label = interface name** if (1) fails on the
   addressing fields. Zero contract change; the docstring's "host-substrate
   lever" framing becomes a `SPLITS.md` note ("on-box lever; the twin shells
   it, the router drives its management plane"). Costs the config read-back.
3. **A new `InterfaceAdmin`** only if both fail — and only for an
   admin-versus-operational state read neither carries. An operational-state
   read beyond the WAN-edge tier's `Router.get_wan_interface_status` is a
   `GAPS.md` entry (§11), not a seed member.

Whichever lands, the lever is encoded **once**; `WanEdgeRouterDevice` does not
add `WanLinkAdmin` on top (§5).

### LAN side — the L3-switch split; `ApplianceVlans` derivable
The appliance's `lan: ApplianceVlans` folds VLAN, gateway address and DHCP into
one `VlanConfig`. The L3-switch design split the same intent into
`RoutedInterfaces` (L3 identity) + `InterfaceDhcp` (`InterfaceDhcpConfig`) over
the **same DHCP sub-models** — `DhcpMode`, `DhcpOption`, `DhcpReservation`,
`ReservedRange`. The router takes the split: its interface set (routed ports,
loopbacks, SVIs) is not VLAN-keyed. Model-level reuse is therefore complete —
the 2026-09-03 `ReservedRange` work and any appliance DHCP test port to the
router unchanged — and a driver may additionally satisfy `ApplianceVlans` **by
derivation** (list the SVIs with their VLAN id and DHCP) if an appliance-written
LAN test needs it; no contract change. Revision 2 had mis-picked `DhcpServer`,
whose only method is `provision_cpe` — the CPE-provisioning server on a Linux
WAN host, not a router pool; revision 3 corrects it.

### WAN-edge surface — the appliance's, reused
Three appliance members fit a WAN-edge router unchanged and were missing from
revision 2:

- **`L3Firewall`** — the outbound / inbound / VPN rule triad over `L3Rule`. The
  2026-06-14 `SPLITS.md` entry kept the triad off switches as "gateway-shaped";
  a WAN edge *is* a gateway. A router driver derives it as ACLs: outbound =
  the LAN-to-WAN direction on the WAN interfaces, inbound = WAN ingress, VPN =
  the tunnel interfaces. This puts two rule records on one archetype
  (`SwitchAclRule` on the core's interface-bound ACL, `L3Rule` on the tier) —
  the price of appliance-test reuse, recorded in §11, and consistent with that
  entry's decision to keep the two records separate.
- **`ApplianceUplinks`** — `UplinkStatus` (address, gateway, DNS, state) per
  uplink; richer than `Router`'s `LinkStatus`. The appliance already composes
  both reads, so composing both here adds no new redundancy.
- **`UplinkPorts`** — the declared uplink→switch-port wiring, a testbed
  topology fact with no vendor in it; the placement work reads it on any WAN
  edge.

### SD-WAN policy — behaviour by composition, on the WAN-edge tier
`SdwanPolicyManager` has no *native object* on an autonomous-mode router: no
platform in the reviewed set carries an "SLA policy" or an "uplink selection
rule" as a single configuration entity. That does not exclude it. The contract
names **behaviour** — steer the flows matching `FlowMatch` to
`preferred_uplink` while `performance_class` (an `SLAPolicy` of latency /
jitter / loss thresholds) is met and fail over when it is not; carry
default-routed traffic on the default uplink — and every reviewed family but
one composes exactly that behaviour from primitives it *does* publish: a
configured probe (IP SLA / NQA / RPM), a track object bound to the probe's
threshold state, and policy routing whose next hop is conditioned on the track
(IOS-XE `set ip next-hop verify-availability … track`; VRP policy routing and
static routes with `track nqa`; Junos RPM + ip-monitoring; Comware NQA + track
+ PBR; RouterOS netwatch + routing marks, scripted). FortiOS carries the object
natively as SD-WAN rules; OneOS6 carries it natively under the SD-WAN licence
(§14 asks about the unlicensed base); SR OS has no track-conditioned policy
routing (✗). That is 5 ✓ + 2 ◐ + 1 ✗ — the bar the stateful firewall and
on-box capture clear — so `sdwan_policy` is composed on `WanEdgeRouterDevice`
with per-method unsupported-capability.

A sequence of CLI steps is a **mechanism**, and mechanisms never enter the
contract: this is the DMVPN / ADVPN / DSVPN argument again, and in truth every
capability on a CLI-managed router is "a sequence of CLI steps" (a NAT rule is
an ACL, a pool and an interface binding). What makes a composed implementation
legitimate is the general rule in §8; applied here:

- **Fidelity, not approximation.** `configure_sla_policy` maps onto probe
  thresholds and `set_uplink_selection` onto track-conditioned policy routing
  with the contract's meaning intact. The appliance review's VeloCloud finding
  draws the line: where a platform steers on fixed built-in classes only, the
  driver raises unsupported-capability rather than approximating with knobs
  that mean something else.
- **Read-back from device state.** `get_uplink_selection`, `get_sla_policies`
  and `get_default_uplink` reconstruct the applied policy from the primitives
  on the box — which requires the driver to name what it writes after the rule
  and policy names it was given (route-map entries, probes, tracks), a
  driver-contract note in §11. A driver-side ledger alone is not read-back: it
  lies after an out-of-band change, and `ConfigOwnership` exists precisely to
  say whether this session owns the writes.
- **No partial policy.** A multi-step apply on an immediate-apply CLI is not
  atomic. A step that fails midway raises, and the driver restores the prior
  state (a saved-configuration rollback, or the IOS-XE candidate datastore /
  OneOS6 NETCONF transaction where enabled) so the box never sits with half a
  rule set — verify-after-apply, §8.
- **Per-method.** `apply_policy(dict)` stays the vendor-shaped escape hatch
  (unsupported unless the driver documents a schema); `get_application_flows`
  needs an application engine (NBAR / NetStream application awareness / DPI —
  per platform); `set_active_active_vpn` maps onto concurrently active overlay
  tunnels with ECMP or policy routing, per platform.

### Security bundles — a tier, reused as-is
`L7Firewall`, `ContentFiltering` and `ThreatPrevention` are appliance members
the 2026-08-20 revision excluded as "not universal to the router class". They
are not universal — but they are not cloud-only either: IOS-XE publishes
Unified Threat Defense (Snort IPS/IDS, URL filtering) on the ISR 4000 /
Catalyst 8000 classes under a security licence; NetEngine AR V300R019 publishes
IPS and URL filtering ("Deep Security"); Junos SRX and FortiOS carry full UTM;
OneOS6 has DPI and application recognition but no IPS or anti-malware; Comware
is partial; RouterOS and SR OS have none. 4 ✓ + 2 ◐ + 2 ✗, platform- and
licence-scoped inside each family — a **tier**, `SecuredRouterDevice` (§5),
reusing the three capabilities as-is so that every appliance security test
ports unchanged. Lands on the first router security test (§11).

### Two levels — intent (sea-level) and mechanism (white-box)
The appliance capabilities were shaped by cloud management APIs: each is an
*aggregation* of what the cloud layer executes on the box, and a router with
console access can do more than that aggregate — and less. Neither access path
is a superset of the other: the console exposes the mechanism and the raw
state; the cloud API exposes network- and organisation-wide views and
cloud-aggregated telemetry (application flows, the org-scope overlay
advertisements) that no console has. The portable surface is the
**intersection**, and that intersection is the **intent level** — which is why
§6 reuses the appliance's aggregated surface as the router's black-box
interface unchanged.

The finer console granularity is real, but its axis is **intent versus
mechanism**, not cloud versus console, and the repo already has that axis:
`LEVELS.md` gives every capability a mandatory black-box "sea-level" surface
plus optional `<Capability>WhiteBox(<Capability>, Protocol)` extensions that
land on tracked evidence. Applied to this archetype, console granularity takes
three forms, of which two have merit:

- **Raw-state reads that prove a write landed** — white-box, per the
  packet-filter precedent in `LEVELS.md` (black-box operations show only that
  the driver *believes* the rule was added). For capabilities satisfied by
  composition (§8) this is worth more, not less: the §12 composition
  conformance wants typed reads of the primitives — the raw RIB/FIB, the zone
  session table, the NAT translation table, per-class shaping counters, probe
  statistics and track state behind `sdwan_policy`, IKE/IPsec security
  associations, a running-configuration section. Raw vendor text is allowed at
  this level (the raw PHY dump precedent). Candidates in §9.
- **Levers with no intent-level equivalent** — white-box, per the
  radar-injection precedent. Console access adds a class of them: reset a BGP
  session, clear NAT translations, clear IPsec security associations, force a
  track or probe state to simulate an SLA breach without touching the wire.
  They make convergence tests reproducible, are near-universal on routers, and
  are published by no cloud-managed appliance — so the sea-level surface
  cannot carry them without breaking substitutability for every appliance
  driver. A driver that cannot back the extension does not satisfy it; a test
  that needs it pins against the extension and collection-skips otherwise.
- **Mechanism-level configuration writes** (route-map entries, class-maps,
  track objects as protocol surface) — **no merit as protocols.** They are
  vendor-shaped by construction and fail the neutrality check, and they would
  open a second write path for behaviour the intent level already encodes —
  the redundant-encoding smell, and a `ConfigOwnership` problem (whose write
  is it?). The one exception is a primitive that is itself cross-vendor
  neutral — a configured probe is one, and it is already the deferred
  `ReachabilityProbe` (§7 Reachability). Such a primitive lands as a
  **sea-level** capability on its own evidence and the composed driver then
  builds on it; that is a sea-level question, not a white-box one.

**Selecting the level needs no mechanism of its own.** A driver either
satisfies a `WhiteBox` extension or does not; a test declares the level it
needs by pinning against the extension (`isinstance`), exactly as the existing
white-box tests do. No granularity flag. Two cautions: the whole-list-replace
semantics the appliance capabilities inherited from cloud APIs stay at the
black-box level and a console driver *diffs* — there is no case for a
white-box per-entry write path; and appliances that do have a console (a
Catalyst SD-WAN edge, a FortiGate) may satisfy router-style extensions while a
dashboard-only appliance cannot, which the convention already handles.

### NAT — reuse the outcome-shaped capability, rename on landing
The set exhibits **five attachment models** for the same outcomes: interface
inside/outside (IOS-XE / VRP / Comware / OneOS6), zone-pair rule-sets (Junos),
policy/VIP objects (FortiOS), a global rule chain (RouterOS), subscriber CGN
pools (Nokia). A neutral NAT contract must therefore be keyed to the
**outcome** — source/overload (PAT), static 1:1, destination/port-forward —
never the attachment. `ApplianceNat` (`OneToOneNatRule` / `OneToManyNatRule` /
`PortForwardRule`, each a list-replace) is *already* outcome-shaped, so the
first driver reuses it **as-is**; the de-branded name (`EdgeNat` / `NatRules`,
models shared, both edge archetypes migrated) is the `SPLITS.md` generalisation
that lands *with* this archetype rather than before it. Nokia's
CGN-on-hardware raises unsupported-capability per method.

### ACL filtering vs. zone firewall — two shapes, both already modelled
Two distinct concepts, kept separate (the `SwitchAcl`-vs-`FirewallZones`
precedent), and **both have an existing contract**:

- **ACL filtering** (8/8) — an ordered rule list bound to an interface +
  direction. `SwitchAcl.set_acl(binding, direction, rules)` binds to a
  free-form string documented as "a port or `vlan:<id>`"; binding to an
  interface name is a **zero-contract-change** derivation. Reuse as-is; the
  de-branded name (`PacketFilterAcl`) is a `SPLITS.md` rename on landing.
- **Stateful / zone firewall** (5 ✓ + 3 ◐) — return-traffic admission with
  per-session state, expressed by **behaviour**. `FirewallZones` already models
  zone CRUD, interface/network membership, zone defaults, and **zone-pair
  forwarding policy** (`set_forwarding(src_zone, dst_zone, action)`) — the
  shape IOS-XE zone-pairs, VRP zones/interzones with ASPF, and Junos security
  zones share. Reuse it; drivers on a zone-less stateful engine (RouterOS
  chains) or a licence-gated one (OneOS6) raise unsupported-capability per
  method, and the masquerade / MSS-clamp toggles on `set_zone_defaults` are
  per-method on routers. A new `StatefulFirewall` is introduced only if the
  zone shape fails on a trigger family at implementation. Keep it **distinct**
  from the ACL — stateless ordered filtering and stateful admission are
  different shapes on different subsets of the fleet.

### QoS — `TrafficShaping` already carries the intent
QoS is present on 8/8 but is the **most model-divergent** capability in the
set: MQC class/policy-maps (IOS-XE / VRP / Comware), CBQ/CB-WFQ/LLQ (OneOS6),
Junos CoS, Nokia H-QoS, FortiOS shaping-policies, RouterOS mangle+HTB. The
neutral contract must express **intent** — *classify on a match, mark DSCP,
rate-limit, prioritise* — and expose none of the policy-map / queue-tree
machinery. The 2026-08-20 revision proposed a new `Qos` and left folding
`TrafficShaping` "for later". Re-examined: `ShapingRule(name, match_type,
value, bandwidth_limit_kbps, dscp_tag, priority)` already carries **all four
verbs**, so `TrafficShaping.set_shaping_rules` *is* the intent-level QoS
contract. Reuse it. Per-method: the appliance-shaped `set_uplink_bandwidth`
maps to a WAN-interface shaper, `set_global_client_bandwidth` is unsupported
(already 2/5 on appliances), and application-ID `match_type` values are
supported only where the platform has an application engine (per-value
unsupported, as for the appliance). The name is a de-branding candidate, not a
blocker.

### VPN — reuse `SiteToSiteVpn` for both static and dynamic overlay
`SiteToSiteVpn` is already neutral (role/hubs/subnets + peer status,
name-referenced, crypto-param-free) and its hub/spoke role model fits
dynamic-overlay topologies. Static IPsec s2s is universal; the dynamic-overlay
*behaviour* (automatic spoke-to-spoke shortcut) is 5/8 via **four incompatible
mechanisms** — NHRP (DMVPN), IKEv2 shortcut exchange (ADVPN), VAM registration
(Comware ADVPN), FortiOS shortcut offers, DSVPN — and **absent on one trigger
family** (OneOS6 offers dynamic virtual tunnel interfaces and a group mode,
both hub-dynamic, not spoke-to-spoke). The contract carries the behaviour,
never a mechanism; Nokia, MikroTik and OneOS6 drivers raise
unsupported-capability for the overlay read. A shortcut-status read stays a
"grow on evidence" addition — the evidence got weaker in revision 2, not
stronger.

### Reachability — one-shot now, configured probes deferred
- **`NetworkProbe`** (reuse, on the core). Every reviewed family originates
  `ping`/`traceroute` from the box, so a router driver satisfies the one-shot
  `tcp_can_connect` / `icmp_can_reach` / `udp_can_reach` contract with no
  contract change — and `testoperations.waiting.await_reachability`, which is
  typed against `NetworkProbe`, then works from the router's vantage
  unchanged. This is the first-consumer path.
- **`ReachabilityProbe`** (**GAPS-deferred**). The configured-probe surface
  (IP SLA / NQA / RPM / TWAMP: a probe the router *keeps running* plus a result
  series) is a genuinely different shape — config + operational read — and
  5 ✓ + 3 ◐ across the set. It was seeded in the 2026-08-20 revision on
  scope-breadth alone, with no consumer. The repo's bar (`HeldPrefixes` landed
  on first consumer evidence, the BGP awaits were deferred without it) says
  defer. When it lands: the result record reuses **`PathMetrics`**
  (latency/jitter/loss, already the return type of `Router.get_wan_path_metrics`
  and `SiteToSiteVpn.get_vpn_path_metrics`), and the `SPLITS.md` 2026-08-10
  rule applies — two members may share one model, never one member two
  meanings.

### Flow telemetry — deferred
`FlowExport` (exporter config: collector, sampling, timeouts) is 7 ✓ + 1 ◐
and has no existing overlap — and no consumer. A test that asserts on exported
flows needs a collector on the harness side that does not exist either.
**GAPS-deferred** until that test appears; the design note (protocol is a
driver detail; sFlow's packet-sampling semantics are a driver note, not a
contract fork) carries over unchanged.

### On-box packet capture — composed, not excluded
The 2026-08-20 revision excluded `pcap` on two grounds inherited from the
appliance design: `PcapCapture` is "Linux-tool-shaped", and capture "is the
`TrafficControllerDevice`'s job" (`SPLITS.md` 2026-06-15). Re-examined against
this class, neither ground holds:

- The precedent's structural reason was that the *appliance* cannot capture
  and a *switch* only mirrors. An on-box-managed router **captures to a file
  on its own management plane**: Embedded Packet Capture on IOS-XE 17.x,
  `capture-packet` on VRP, mirror-destination pcap on SR OS (7750 SR and 7705
  SAR), `packet-capture` on Comware 7, `/tool sniffer` on RouterOS — five ✓ —
  with Junos (full datapath capture on SRX, RE-bound only on MX), FortiOS (a
  CLI sniffer that streams text; file capture via other paths) and OneOS6
  ("flow capture and decoding", file semantics unverified) as ◐. That is the
  same strong-majority bar the stateful firewall clears, and the same logic
  by which interface admin is *included* here while excluded on the
  appliance: a capability structurally present on the substrate rides on the
  archetype.
- `PcapCapture`'s contract is **lifecycle plus raw read**
  (`start_tcpdump(interface, port, output_file, filters) -> handle`,
  `stop_tcpdump(handle)`, `tshark_read_pcap(fname, …) -> str`) — the
  capture-analysis family design records exactly that framing. A router driver
  satisfies it with no contract change: `start`/`stop` drive the on-box
  capture session with the handle as the session name, and `tshark_read_pcap`
  **fetches the finished file off-box** (SCP/SFTP/TFTP, whatever the platform
  offers) and runs tshark on the harness host. The capture-analysis operations
  (`path_placement`, `marking_observation`) then run over a router vantage
  unchanged, and `capture_shared_window` can bracket a router capture beside
  a traffic-controller capture in one shared window.

**Why compose it rather than leave it to the traffic controller alone.** The
traffic controller sees every frame on the wire between two devices; the
router sees what *it* forwarded, marked, translated, or dropped — the two
vantages disagree exactly when a test cares (a DSCP remark applied on egress,
a NAT translation, a packet the zone firewall admitted or refused). The
traffic controller stays the **wire vantage of record**; the router adds the
**device vantage**. Limits are recorded as driver notes, not contract shape:
on-box capture is buffer- and count-bounded, may be CPU-punted and
rate-limited, is control-plane-only on some carrier platforms (Junos MX), and
is never a line-rate instrument.

**Shape.** Reuse `PcapCapture` as-is for the first driver. Its method names
carry a tool (`tcpdump`, `tshark`) the router never runs; de-branding them
(`start_capture` / `stop_capture` / `read_capture`) is a `SPLITS.md`
generalisation that touches every archetype composing `pcap`, so it lands on
its own evidence, not with this seed.

### Voice gateway — a fourth optional tier
Voice is 4/8 across the reviewed set (IOS-XE, VRP, Comware, OneOS6) — below
the core bar — but **present on every trigger family**: analog and digital
voice ports (FXS/FXO/BRI/PRI), SIP trunking, and on OneOS6 an embedded SBC;
on IOS-XE and VRP it is platform-scoped to the branch classes with voice DSP
hardware. The 2026-08-20 revision deferred it at low priority under the
second-consumer rule; that framing was wrong for this estate. Revision 2 adds
`VoiceGatewayRouterDevice` (§5) with one new tier capability, **`RouterVoice`**,
landing with the first voice-gateway consumer at `GAPS.md` priority medium.

Shape at that point (recorded now so the tier is self-documenting): voice-port
inventory with admin/oper state per port (FXS/FXO/BRI/PRI), SIP trunk /
registration status, and an active-call count — reads and the port admin
lever. **Call-routing configuration** (dial-peers / route patterns / number
manipulation) is the most vendor-divergent surface in the domain and is
**deferred** as a separate entry. The existing voice contracts do not fit:
`SipServer` is a registrar/PBX on a Linux host (users, voicemail, RTP-engine
stats), `SipPhone` an endpoint; `RouterVoice` reuses their SIP vocabulary
where it matches (e.g. the `get_active_calls` reading) and shares no
archetype.

---

## 8. Neutrality notes and quirks (for the driver layer)

- **Per-method, not per-vendor.** Presence is platform-scoped inside every
  family (a vendor's carrier-metro platform omits the NAT/ZBF/voice/DSL its
  branch platforms carry), and licence-scoped on some (OneOS6 zone firewall,
  and the NETCONF server on some OneOS6 models). Unsupported-capability
  signalling is per method, per the established convention — never "this
  whole capability is absent for vendor X."
- **Operating mode is an instance fact.** An IOS-XE platform on the same image
  is this archetype in autonomous mode and an `SdwanApplianceDevice` in
  controller mode. The driver asserts the mode at attach and refuses the
  wrong one; the archetype never carries a mode field. If a mode or firmware
  fact must cross the boundary, the boundary-fact rule of
  `capability-only-archetypes.md` puts it on `DeviceInfo` as a read-only
  property, never on the archetype.
- **Composition is a mechanism, not an approximation.** A capability is
  satisfied by a *sequence* of platform primitives — several CLI commands, a
  probe plus a track plus a policy route — on the same terms as by a single
  native object, provided (1) the composed behaviour has the contract's
  meaning, not a look-alike (the VeloCloud SLA precedent); (2) the `get_*`
  read-back reconstructs from device state, which means the driver names what
  it writes deterministically; (3) a sequence that fails midway raises and
  leaves no partial state; (4) the cross-vendor bar is judged on the
  behaviour, never on the existence of a native object. §7 applies this to
  `sdwan_policy` and `l3_firewall`; it applies equally to NAT, zones and QoS on
  a CLI-managed box.
- **VRRP is the only portable FHRP.** HSRP and GLBP are Cisco-local; the
  `GatewayRedundancy` contract stays VRRP-shaped, and a Cisco driver maps HSRP
  onto it.
- **EIGRP is Cisco-only** (informational RFC 7868; 1/8 in the reviewed set). It
  is **excluded from the neutral contract** — the router-world analogue of
  keeping vendor strike-ids out of `PacketInjector`/`ThreatPrevention`. A Cisco
  driver that must drive EIGRP does so through a plugin-local capability, never
  a commons method. Deferred entry in §11.
- **OSPFv3 is per-method.** `OspfConfig.version = OspfVersion.V3` is
  unsupported where the platform lists OSPFv2 only (OneOS6 datasheets).
- **Overlay-VPN mechanism names never enter the contract.** "DMVPN" / "ADVPN" /
  "DSVPN" / "VAM" are vendor terms for one behaviour; the contract names the
  behaviour.
- **Config-transaction semantics: assume immediate-apply, verify after apply.**
  All three trigger families are immediate-apply on the CLI (IOS-XE
  autonomous `configure terminal`; VRP5; OneOS6). Commit semantics exist but
  are optional or transport-bound: the IOS-XE NETCONF candidate datastore is
  off by default and enabled per device (`netconf-yang feature
  candidate-datastore`, running datastore otherwise; confirmed-commit since
  17.1.1); OneOS6 NETCONF is transactional; Junos and model-driven SR OS are
  commit-based throughout. A neutral driver **verifies after apply** rather
  than assuming either model — a driver-contract note, not a protocol shape.
- **Programmatic-transport floor.** CLI + ≥1 programmatic interface, and that
  interface is NETCONF/YANG on six of eight families — including all three
  trigger families — and vendor REST on the other two. Drivers own the
  transport choice (a NETCONF-first driver family covers the trigger estate);
  the protocol surface is transport-agnostic because two reviewed families
  are REST-only.
- **On-box capture is bounded.** Buffer/count limits, possible CPU punt and
  rate limiting, control-plane-only on some carrier platforms, and a file that
  must be fetched off-box before it is read. The traffic controller remains
  the line-rate wire vantage; the router capture is device-vantage evidence.
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
- `ip_interface` (`IpInterface`) — per-`netdev` `ip addr/link/mtu/mac`; the
  router's own interface surface is `RoutedInterfaces` (+ `enabled`) instead.
- iptables `nat` (`Nat`) — replaced by the outcome-shaped NAT capability (§7).

**No longer excluded — `pcap` (`PcapCapture`).** Revision 2 composes it on the
core (§7): the exclusion was inherited from a device class that cannot
capture, and the on-box router can. The 2026-06-15 `SPLITS.md` entry that
placed `pcap` on `TrafficControllerDevice` is unaffected — the traffic
controller keeps the wire vantage; this archetype adds the device vantage.

Unlike the appliance, the managed router **does** carry an interface-admin
lever and a capture lever — it administers and observes itself on-box. Those
are the archetype's defining inclusions.

**White-box extensions (§7 Two levels).** None is seeded with the archetype —
each lands on signal per `LEVELS.md` — but the console-granularity review
identified the candidates, in the two kinds the convention admits:

- *Raw-state reads* (prove a composed write landed; pin diagnostics):
  `RoutingReadWhiteBox` — raw RIB/FIB dump; `FirewallZonesWhiteBox` — session
  table (the router analogue of `ConntrackWhiteBox`); a NAT white-box on the
  de-branded NAT capability — translation table; `TrafficShapingWhiteBox` —
  per-class counters; `SdwanPolicyWhiteBox` — probe statistics, track state,
  policy-route hit counts; `SiteToSiteVpnWhiteBox` — IKE/IPsec security
  associations; `BgpWhiteBox` — per-neighbour received/advertised routes raw;
  a running-configuration section read (home — `ConfigOwnership` or
  `DeviceInfo` — to settle at seeding). Raw vendor text is permitted at this
  level.
- *Levers with no intent-level equivalent* (reproducible convergence tests):
  `BgpWhiteBox.reset_session(peer)`; a NAT white-box `clear_translations()`;
  `SiteToSiteVpnWhiteBox.clear_security_associations(peer)`;
  `SdwanPolicyWhiteBox.force_track_state(name, up | down)` — simulate an SLA
  breach without impairing the wire.

Each candidate is recorded in `LEVELS.md` when a consumer or reviewer signal
lands it, with the drivers expected to satisfy it (router drivers;
console-bearing appliances) and not (dashboard-only appliances).

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

- `ManagedRouterDevice` core (existing capabilities only) — with this doc as
  the design record and the §3 matrix as the evidence.
- **`ReachabilityProbe`** (configured probe + result series, `PathMetrics`
  result) [priority: medium] — 5 ✓ + 3 ◐; trigger: the first test that needs
  a probe the router keeps running (a series, not a one-shot).
- **`FlowExport`** (exporter config intent) [priority: low] — 7 ✓ + 1 ◐;
  trigger: the first test asserting on exported flows, which also needs a
  harness-side collector.
- **`RouterVoice` / `VoiceGatewayRouterDevice`** [priority: **medium**] —
  4/8, 3/3 trigger families; lands with the first voice-gateway test.
  Call-routing configuration is a separate, later entry.
- **`SecuredRouterDevice`** (security-bundle tier reusing `L7Firewall` /
  `ContentFiltering` / `ThreatPrevention`) [priority: medium] — 4 ✓ + 2 ◐ +
  2 ✗, licence-/platform-scoped; lands with the first router security test.
- **`CellularWan` / `DslWan` / `PppSession`** access-WAN tier — net-new but
  module-scoped; land with the first `AccessWanRouterDevice` consumer.
- **EIGRP-class proprietary IGP** [priority: low] — single-vendor; plugin-local
  capability only, never neutral. Trigger: a Cisco-only test that must drive
  EIGRP through a typed surface.
- **`CarrierEthernet` (EVC)** [priority: low] — for carrier Metro-Ethernet
  switches (§10); assess separately.
- **Interface operational-state read** beyond `Router.get_wan_interface_status`
  and **SNMP-agent config** [priority: low] — deferred; syslog is the telemetry
  path, the configured `enabled` state is the interface baseline.

**`SPLITS.md` (generalisations this archetype motivates):**

- `RoutedInterface` gains `enabled: bool = True` (admin state on the configured
  L3 interface object, mirroring `SwitchPort.enabled`; §7). Fallbacks recorded
  in §7 if the addressing fields do not fit dynamically addressed WAN
  interfaces.
- `ApplianceNat` → de-branded outcome-shaped NAT name reused on both edge
  archetypes (§7).
- `SwitchAcl` → de-branded `PacketFilterAcl` ordered-ACL shape; the binding
  docstring extended to "port, `vlan:<id>`, or interface name" (§7).
- `TrafficShaping` — name is a de-branding candidate; no shape change (§7).
- `PcapCapture` — tool-named methods (`start_tcpdump` / `stop_tcpdump` /
  `tshark_read_pcap`) are a de-branding candidate across every archetype
  composing `pcap`; lands on its own evidence (§7).
- If fallback (2) in §7 is taken instead: `WanLinkAdmin` docstring reframed
  from "host-substrate lever" to "on-box lever".
- Two rule records on one archetype (`SwitchAclRule` on the core,
  `L3Rule` on the WAN-edge tier) — recorded as an observation; the 2026-06-14
  decision to keep them separate stands until a consumer reconstructs one from
  the other.
- `SdwanPolicyManager` and `L3Firewall` by composition — the driver's naming
  convention for the primitives it writes (route-map entries, probes, tracks,
  ACLs named after the rule / policy they realise) is a driver-contract note
  so read-back reconstructs from device state; no protocol change.

**`LEVELS.md`:** none at seed. Candidates recorded in §9 in the two kinds the
convention admits — raw-state reads (`RoutingReadWhiteBox`,
`FirewallZonesWhiteBox`, the NAT translation table, `TrafficShapingWhiteBox`,
`SdwanPolicyWhiteBox`, `SiteToSiteVpnWhiteBox`, `BgpWhiteBox`, a
running-configuration section) and levers (`reset_session`,
`clear_translations`, `clear_security_associations`, `force_track_state`) —
each landing on signal with its satisfy / not-satisfy driver sets.

---

## 12. Verification approach (at implementation time)

Mirrors the appliance archetype: per-capability protocol-conformance tests;
archetype registration + `runtime_checkable` `isinstance` gate in the
device-types test; the `register_device_type` capability-only purity gate
(`test_archetype_purity.py`); `mypy --strict`; twin + appliance + CPE + L3-switch
regression (all unchanged by the reuse dispositions, save the defaulted
`RoutedInterface.enabled` field); and the **vendor-isolation grep** ensuring no
product name or vendor id appears anywhere in the `testprotocols` package
source. Product names appear only in this design doc, where they evidence the
cross-vendor concept check — never in a model, enum, or protocol.

Two additions in revision 2:

- **Version-pinned re-verification of the three trigger columns** at
  implementation, against the exact firmware the first drivers attach to
  (IOS-XE 17.9.x autonomous; NetEngine AR V300R0xx; the OneOS6 minor then in
  use) — resolving the four ◐¹ cells and the OneOS6 capture-file semantics.
- **Capture conformance includes the off-box fetch**: a router `pcap`
  conformance test must prove `tshark_read_pcap` reads the file the router
  wrote, through the driver's transfer path, and that a router capture can be
  bracketed in `capture_shared_window` beside a traffic-controller capture.
- **Composition conformance** (§8): for every capability a driver satisfies by
  a sequence of primitives, the conformance test proves read-back from device
  state (not from a driver ledger), and that a sequence failed midway raises
  and leaves no partial policy — exercised at least on
  `sdwan_policy.set_uplink_selection` and `l3_firewall.set_outbound_rules`.
  Where a `WhiteBox` read of the primitives exists (§9), the conformance test
  reads through it; until one lands, it reads the device state through the
  driver's own transport and records that as the evidence path.

---

## 13. Sources

Public vendor documentation consulted for the §2 baselines and the §3 concept
check. The vendor-isolation rule forbids vendor names and URLs in the
`testprotocols` package **source**, not in this design record — the same
convention the SD-WAN appliance doc follows.

**Cisco (IOS-XE 17.9 baseline)**

- IOS XE Cupertino 17.9.1 release-notes index (platform families):
  <https://www.cisco.com/c/en/us/support/ios-nx-os-software/ios-xe-cupertino-17-9-1/model.html>
- Release Notes for Cisco ISR 1000 Series, IOS XE 17.9.x:
  <https://www.cisco.com/c/en/us/td/docs/routers/access/1100/release/17-9/isr1k-rel-notes-xe-17-9-x.html>
- Release Notes for Cisco ASR 920 Series, IOS XE 17.9.x:
  <https://www.cisco.com/c/en/us/td/docs/routers/asr920/release/notes/17-9-1/b-rn-xe-17-9-1-asr920.html>
- Release Notes for Cisco ASR 900 Series, IOS XE 17.9.x:
  <https://www.cisco.com/c/en/us/td/docs/routers/asr903/release/notes/17-9-1/b-rn-xe-17-9-x-asr900.html>
- Release Notes for Catalyst IR1101, IR1800, IR8140, IR8340, IOS XE 17.9.1:
  <https://www.cisco.com/c/en/us/td/docs/routers/IIoT/release-notes/17-9-1/b-17-9-1-release-notes-iot-router.html>
- Catalyst SD-WAN onboarding guide — autonomous and controller modes:
  <https://www.cisco.com/c/en/us/td/docs/routers/sdwan/26x-later/onboarding/sdwan-onboarding-guide/device-install-upgrade-17-2-later/autonomous-and-controller-modes.html>
- Catalyst 8500 software configuration guide — deploy IOS-XE and SD-WAN:
  <https://www.cisco.com/c/en/us/td/docs/routers/cloud_edge/c8500/software-configuration-guide/c8500-software-config-guide/Autonomous-Controller.html>
- Programmability Configuration Guide, IOS XE Cupertino 17.9.x (NETCONF,
  RESTCONF, gNMI, model-driven telemetry, ZTP):
  <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/179/b_179_programmability_cg.html>
- NETCONF Protocol chapter, 17.9.x (candidate datastore, confirmed commit):
  <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/179/b_179_programmability_cg/m_179_prog_yang_netconf.html>
- Security and VPN Configuration Guide, IOS XE 17.x — Zone-Based Policy
  Firewalls:
  <https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/sec-vpn/b-security-vpn/m_sec-zone-pol-fw-xe.html>
- Network Services Configuration Guide, IOS XE 17.x — Embedded Packet Capture:
  <https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ntw-servs/b-network-services/m_nm-packet-capture-xe.html>
- CUBE Configuration Guide, IOS XE 17.6 onwards — supported platforms (voice
  platform scoping):
  <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/voice/cube/ios-xe/config/ios-xe-book/supported-platforms.html>
- Security Configuration Guide: Unified Threat Defense, IOS XE 17 — Snort IPS
  (security-bundle tier):
  <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_data_utd/configuration/xe-17/sec-data-utd-xe-17-book/snort-ips.html>
- IP Routing Configuration Guide, IOS XE 17.x — PBR support for multiple
  tracking options (IP SLA + track + `set ip next-hop verify-availability`;
  SD-WAN policy by composition):
  <https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-routing/b-ip-routing/m_iri-pbr-mult-track-0.html>

**Huawei (VRP 5.170 / NetEngine AR V300R019 baseline)**

- NetEngine AR V300R019 — displaying version information (`Version 5.170`):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112347/fd9eedcc/displaying-version-information>
- NetEngine AR V300R019 NETCONF YANG API Reference (firewall, NetStream, NQA,
  TWAMP, LLDP, SNMP):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112399>
- NetEngine AR V300R019 — QoS: configuring a traffic policy:
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112355/cd28133e/configuring-a-traffic-policy>
- NetEngine AR600/6100/6200/6300 V300R019 Command Reference — NAT configuration
  commands:
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112391/29a820da/nat-configuration-commands>
- NetEngine AR V300R019 — Security: example for configuring ASPF and port
  mapping (firewall zones / interzone):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112357/f571c524/example-for-configuring-aspf-and-port-mapping>
- NetEngine AR V300R019 — VPN configuration guide (IPsec, L2TP, DSVPN):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112360>
- NetEngine AR V300R019 — Reliability configuration guide (NQA, VRRP,
  interface backup):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112356>
- NetEngine AR V300R019 — Network Management and Monitoring: configuring
  NetStream sampling:
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112354/bd07da44/https&>
- NetEngine AR V300R019 — Interface Management: LTE links as primary WAN links:
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112349/1685693/lte-links-as-primary-wan-links>
- NetEngine AR V300R019 Web-based Configuration Guide — DSL interface
  (ADSL/VDSL/G.SHDSL cards):
  <https://support.huawei.com/enterprise/it/doc/EDOC1100112364/72651b2b/dsl-interface>
- NetEngine AR V300R019 — Voice configuration guide (PBX, voice ports):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112359>
- NetEngine AR V300R019 — packet capture (web guide) and configuring the
  device to capture packets (CLI guide):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112364/8d49ae6e/packet-capture>,
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112354/bd0e10ad/configuring-the-device-to-capture-packets>
- Classic AR (AR100–AR3600) V300R003 NETCONF YANG API Reference (programmatic
  floor on the classic line):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100022096>
- NE40E V800R023 configuration guide (the VRP8 carrier train, out of scope
  pending §14):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100335685/1b7bdeb9/upgrade-maintenance-configuration>
- AR600/AR6100/AR6200/AR6300 life-cycle bulletins (V300R019/R021/R022):
  <https://support.huawei.com/enterprise/en/routers/ar611-pid-253265923/bulletins?type=life-cycle-notices>
- NetEngine AR V300R019 — Security: configuration examples for URL filtering,
  and the web-guide Deep Security wizard (IPS + URL filtering; security-bundle
  tier):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112357/629f2418/configuration-examples-for-url-filtering>,
  <https://support.huawei.com/enterprise/kz/doc/EDOC1100112364/4cf1c502/deep-security-configuration-wizard>
- NetEngine AR V300R019 — IP Unicast Routing: routing policy and static-route
  configuration (policy routing and static routes tracked by NQA; SD-WAN
  policy by composition):
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112352/894629ea/configuring-a-routing-policy>,
  <https://support.huawei.com/enterprise/en/doc/EDOC1100112352/bfd73d2e/static-route-configuration>

**Ekinops (OneAccess ONE-series / OneOS6 baseline)**

- "All-in-One Box" solution page (the "one box" positioning):
  <https://www.ekinops.com/solutions/voice-data-access/all-in-one-box>
- OneOS6 announcement, 2017-12-18 (NETCONF and REST APIs, all functions in
  YANG):
  <https://www.ekinops.com/news/corporate/oneaccess-puts-choice-in-the-hands-of-operators-with-its-new-oneos6-operating-system>
- OneOS6 product page:
  <https://www.ekinops.com/products-services/products/compose/oneos6>
- Small & branch office data routers (ONE421/531/621/641; CLI, TR-069, SNMP,
  NETCONF/YANG):
  <https://www.ekinops.com/products-services/products/oneaccess/voice-data-routers/small-branch-office>
- Mid to large enterprise data routers (ONE2560/2561/3540):
  <https://www.ekinops.com/products-services/products/oneaccess/voice-data-routers/mid-to-large-enterprise>
- ONE621 datasheet (2026 — routing, NAT/NAPT, ACL, ZBF, CBQ/LLQ QoS, IPsec/
  IKEv2/DVTI, VRRP, NetFlow, QoS measurement probe, NETCONF 1.0/1.1, LTE Cat 6
  / 5G, 4/8-port switch, Wi-Fi 6, eSBC option):
  <https://www.ekinops.com/images/resources/datasheets/03ds-one621-ekinops.pdf>
- ONE2540 datasheet (2022 — stateful firewall rules, NAT rules, NETCONF
  server (licensed), flow capture and decoding, EEM, ONeSBC):
  <https://www.ekinops.com/images/resources/datasheets/03ds-one2540-ekinops.pdf>
- ONE421 / ONE521 / ONE531 datasheets (VDSL2 vectoring/bonding, ADSL2+,
  G.SHDSL.bis EFM bonding, LTE):
  <https://www.ekinops.com/images/resources/datasheets/03ds-one421-ekinops.pdf>,
  <https://www.ekinops.com/images/resources/datasheets/03ds-one521-ekinops.pdf>,
  <https://www.ekinops.com/images/resources/datasheets/03ds-one531-ekinops.pdf>
- ONE526 / ONE1526 datasheets (FXS/FXO/BRI, PRI E1/T1, embedded SBC):
  <https://www.ekinops.com/images/resources/datasheets/03ds-one526-ekinops.pdf>,
  <https://www.ekinops.com/images/resources/datasheets/03ds-one1526-ekinops.pdf>
- ONE-5G datasheet:
  <https://www.ekinops.com/images/resources/datasheets/03ds-one5g-ekinops.pdf>
- SD-WAN Xpress datasheet (the OneOS6 platform list; "one box solution"):
  <https://www.ekinops.com/images/resources/datasheets/04ds-sd-wan_xpress-ekinops.pdf>
- OneOS6-LIM datasheet (same OS on uCPE; NETCONF/YANG, embedded probes):
  <https://www.ekinops.com/images/resources/datasheets/04ds-oneos6_lim-ekinops.pdf>

**Juniper Junos**

- Use packet capture to analyze network traffic (SRX `forwarding-options
  packet-capture`):
  <https://www.juniper.net/documentation/en_US/junos/topics/example/security-packet-capture-device-enabling.html>
- Data path debugging and trace options:
  <https://www.juniper.net/documentation/us/en/software/junos/network-mgmt/topics/topic-map/data-path-debugging-and-trace-options.html>
- Consulted in the 2026-08-20 review (`juniper.net/documentation`): NETCONF /
  Junos XML API overview; ADVPN; SRX port-switching modes; SRX LTE and VDSL2
  Mini-PIMs; RPM.

**Nokia SR OS**

- 7750 SR OAM and Diagnostics Guide 22.5 — PCAP packet capture (mirror-dest
  pcap, `debug pcap … capture start`):
  <https://infocenter.nokia.com/public/7750SR225R1A/topic/com.nokia.OAM_Guide/pcap_packet_cap-ai9exgsu3c.html>
- 7705 SAR OAM guide 23.4 — packet capture:
  <https://infocenter.nokia.com/public/7705SAR234R1A/topic/com.nokia.oam-guide/packet_capture-ai9o99jjr7.html>
- Consulted in the 2026-08-20 review (`documentation.nokia.com`,
  `infocenter.nokia.com`): model-driven management interfaces; 7750 local DHCP
  server; Multiservice ISA/ESA (NAT/firewall); 7705 SAR-Hm (cellular), SAR-M
  xDSL module; OAM/TWAMP.

**HPE Comware (H3C MSR)**

- H3C MSR Comware 7 configuration guide — packet capture configuration
  (`packet-capture local interface … file`):
  <https://www.h3c.com/en/Support/Resource_Center/EN/Home/Routers/00-Public/Configure/Configuration_Guides/H3C_MSR_Comware_7_CG-R0615-6W100/17/202003/1277684_294551_0.htm>
- Consulted in the 2026-08-20 review (`hpe.com/psnow`, vendor manuals):
  Comware 7 Fundamentals / NETCONF; FlexNetwork MSR ADVPN (VAM); MSR LTE /
  ADSL2+ / G.SHDSL modules; FXS/FXO/E1 voice SICs; NQA; NetStream.

**Fortinet FortiOS**

- FortiOS 7.6 administration guide — performing a sniffer trace or packet
  capture:
  <https://docs.fortinet.com/document/fortigate/7.6.4/administration-guide/680228/performing-a-sniffer-trace-or-packet-capture>
- Consulted in the 2026-08-20 review (`docs.fortinet.com`): FortiOS REST
  Config/Monitor API; ADVPN and shortcut paths; VRRP; hardware switch;
  traffic-shaping policy; link-monitor; 60E-DSL datasheet.

**MikroTik RouterOS**

- RouterOS documentation — Packet Sniffer (`/tool/sniffer` start/stop/save to
  pcap):
  <https://help.mikrotik.com/docs/spaces/ROS/pages/8323088/Packet+Sniffer>
- Consulted in the 2026-08-20 review (`help.mikrotik.com`, `mikrotik.com`):
  RouterOS REST API; OSPF; BGP; mangle/queues; netwatch; Traffic-Flow; LTE/5G
  product group.

**In-repo precedents relied on**

- `SPLITS.md` 2026-05-02 (netem off the twin), 2026-06-12 (`WanLinkAdmin` off
  the appliance; `Router` read-only), 2026-06-15 (`pcap` composed on
  `TrafficControllerDevice`), 2026-08-10 (two members, one `PathMetrics`
  model), 2026-09-04 (`NetworkAttachment.test_interface`, boundary-fact rule).
- `GAPS.md` 2026-06-14 (`Bgp` on the L3 switch), 2026-09-04 (`HeldPrefixes`
  landed on first consumer; budgeted BGP awaits deferred).
- `docs/architecture/capture-analysis-operations-design.md` (`PcapCapture` as
  lifecycle-plus-raw-read; `capture_shared_window`).
- `docs/architecture/sdwan-appliance-protocol-design.md` (five-family review,
  version-pinned re-verification precedent; the VeloCloud SLA-fidelity
  finding), `docs/architecture/typed-path-steering-protocol-design.md`
  (`UplinkSelectionRule` / `SLAPolicy` semantics), `SPLITS.md` 2026-06-14
  (`SwitchAcl` vs the `l3_firewall` triad).

---

## 14. Open questions for the maintainers

Answers refine the §2 baselines; none blocks the design record.

1. **Huawei VRP8.** Are carrier NetEngine 40E/8000 routers in the estate? If so
   the Huawei column splits into a VRP5 and a VRP8 column and the carrier class
   gains a second trigger family.
2. **Cisco controller mode.** Are any IOS-XE boxes operated in controller mode?
   They are `SdwanApplianceDevice` instances, and the driver must refuse them
   here.
3. **OneOS6 minor floor.** Pin it when known; until then the OneOS6 generation
   is the floor.
4. **OneOS6 capture semantics.** Does "flow capture and decoding" write a
   retrievable file? Decides whether the OneOS6 `pcap` cell is ✓ or a
   per-method unsupported.
5. **OneOS6 steering without the SD-WAN licence.** Is probe-conditioned policy
   routing available on the base OneOS6, or only through the SD-WAN Xpress
   licence? Decides whether the OneOS6 `sdwan_policy` cell is ✓ or per-method.

---

## 15. Review record

**2026-09-07 — approval-team review against the three-family context.
Decision: accept-with-conditions; conditions applied in this revision.**

- Trigger restated as three families at public review-baseline generations;
  reviewed-family list ratified at eight; "market reference column" framing
  dropped (§2).
- Matrix re-run at eight columns with recounted denominators and per-cell
  sources; four Ekinops cells left ◐ pending verification (§3, §13).
- Cisco scoping recorded: autonomous mode only, controller mode is the
  appliance archetype, mode is an instance fact, classic IOS out, candidate
  datastore optional (§2, §8).
- Huawei scoping recorded: VRP5 reading of "5.17", VRP8 out pending
  confirmation, V200R0xx NETCONF caveat (§2, §14).
- Voice reframed from "deferred, low" to a fourth optional tier at priority
  medium (§5, §7, §11).
- Net-new list re-derived through the zero-contract-change test: core composes
  existing capabilities only; `ReachabilityProbe` and `FlowExport`
  GAPS-deferred; `InterfaceAdmin`, `StatefulFirewall`, `Qos`, `PacketFilterAcl`
  and `RouterNat` withdrawn as new protocols in favour of `RoutedInterfaces`
  (+ field), `FirewallZones`, `TrafficShaping`, `SwitchAcl` and `ApplianceNat`
  (§5, §6, §7).
- Management-plane and config-transaction notes rewritten (§3, §8).
- On-box packet capture moved from excluded to composed, with the traffic
  controller kept as the wire vantage of record (§7, §9) — a maintainer
  question at adoption ("why not support capture on these devices?") that
  the cross-vendor check answered in favour of inclusion.
- Sources section added (§13); open questions recorded (§14).

**2026-09-07 — appliance-overlap review (revision 3). Question put by the
maintainers: given the large functional overlap with the managed SD-WAN
appliance, and cloud management being an implementation aspect rather than a
protocol-shape aspect, are the shared capability protocols leveraged enough?
Answer: not yet; applied here.**

- §1 boundary restated by published operation set; management transport
  removed from the argument.
- `DhcpServer` (a CPE-provisioning server) replaced by `InterfaceDhcp`, which
  shares the appliance DHCP sub-models (§5, §6, §7).
- `WanEdgeRouterDevice` composes the appliance's WAN-edge surface: `uplinks`,
  `uplink_ports`, `l3_firewall` (derived as interface ACLs) and `sdwan_policy`
  (§5, §7).
- Second maintainer question — does the absence of a native SD-WAN policy
  object exclude implementing the surface for test purposes as a sequence of
  CLI steps? Answer: no; recorded as the general composition rule (§8) with
  its four conditions, applied to `sdwan_policy` (§7), verified by the
  composition-conformance test (§12).
- `SecuredRouterDevice` tier candidate reusing the appliance security bundles
  (§5, §7, §11); two matrix rows added with trigger-column sources (§3, §13).
- `ApplianceVlans` derivation note under LAN (§7); shared-with-appliance table
  (§6): all seventeen appliance members reused or derivable.

**2026-09-07 — two-level review (revision 4). Question put by the
maintainers: the appliance capabilities are aggregations of what a cloud
management layer executes, a subset of what console access allows; does it
have merit to design the shared functionality at the finer console
granularity as a white-box equivalent, letting a test suite select the
level? Answer: yes, in two of three forms; applied here.**

- The axis is intent versus mechanism, not cloud versus console; neither
  access path is a superset of the other, and the intent level is the
  intersection where tests port (§7 Two levels).
- Two forms with merit, both under the existing `LEVELS.md` convention:
  raw-state reads that prove a composed write landed, and console-only levers
  (session reset, clear translations / security associations, forced track
  state). Mechanism-level configuration writes declined as protocols;
  cross-vendor-neutral primitives land at sea level on their own evidence.
- Level selection through the existing `isinstance` pin on the extension; no
  granularity flag; whole-list-replace stays black-box and console drivers
  diff.
- White-box candidate list recorded in §9 and §11 in the two kinds; §12
  composition conformance reads through the white-box reads once they land.
