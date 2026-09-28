# Design: vendor-neutral **managed router** archetype

| Field | Value |
| --- | --- |
| Status | chartered |
| Author | rjvisser |
| Date | 2026-09-27 |
| Related | `docs/archetypes/README.md` (the track), `docs/architecture/sdwan-appliance-protocol-design.md` (the precedent), `docs/architecture/capability-only-archetypes.md`, `packages/testprotocols/SPLITS.md`, `packages/testprotocols/LEVELS.md`, `packages/testprotocols/GAPS.md` |

## 1. Charter

### The class, by the operations it publishes

A **managed router** is a closed network product — not a general-purpose
host — that forwards at layer 3, runs traditional routing (static routes, an
IGP, BGP), and publishes on its own management plane the operations that
define the class:

- **administration of its own interfaces** — take an interface down and up,
  read its state;
- **capture of its own traffic** to a file that can be fetched off the box;
- **interface-bound filtering** and a zone-based stateful firewall;
- **on-box services** — NAT, QoS by class (classify, mark, queue, shape), DHCP
  server and relay, first-hop redundancy, on-box reachability probes;
- **routing state and levers** — routing tables per routing instance, peering
  state, resets of a routing peer and of a wired access session;
- **device and management-plane operations** — reload, management-access
  filtering, log export, time synchronisation, operator authentication
  (central server with a local fallback).

How that management plane is reached — CLI, NETCONF/YANG, RESTCONF, gNMI, or a
controller that fronts it — is a driver concern and plays no part in the
definition. Management mode (on-box or controller-owned) is not a shape fact
either: a controller-owned instance publishes the same operations and differs
only in who may write configuration, which the existing `ConfigOwnership`
capability already carries. An instance belongs to the archetype when its
driver publishes the members; the `isinstance` gate decides.

The class spans four device classes that recur across every vendor's line-up:
the **carrier / aggregation edge** (a lean routing core, no LAN switching,
voice or access modems); the **enterprise branch** (routing plus on-box
security, services and, on many models, voice); the **small branch /
teleworker** unit (the branch set plus an integrated switch and xDSL and/or
cellular access); and the **industrial** router (a ruggedised subset of the
branch classes). Capability presence is platform-scoped inside every family —
a carrier platform omits what a branch platform carries — so the contract
needs per-method unsupported signalling even inside one family, and the
design (not this charter) decides the core and the tiers.

**Own-traffic capture reopens a recorded placement, in one respect.**
`SPLITS.md` (2026-06-15) placed `PcapCapture` on the inline
`TrafficControllerDevice` because that device sees every frame crossing the
path under test, and the host, appliance and switch archetypes exclude capture
on that ground. That placement stands: the traffic controller remains the wire
vantage of record. What it cannot see is the router's own vantage — traffic the
router originates or terminates on its control and management planes, traffic
between two of its interfaces that never crosses the inline point, and traffic
on the inside of the router's own translation or encryption. The class
publishes capture of exactly that traffic to a file on its own management
plane: IOS-XE's Embedded Packet Capture exports a capture file, and VRP on the
AR series captures packets to a file (`capture-packet`); OneOS6 is to be
verified. The design carries the per-family evidence in its matrix. This
charter therefore adds capture as a device-vantage operation of this class
without moving the traffic controller's.

Standalone switches that share an estate with these routers are out of scope:
they fold into the existing switch archetypes as a driver exercise.

### Boundary with the registered archetypes

- **`sdwan_appliance` (`SdwanApplianceDevice`)** — *under*-specified for this
  class: it publishes no interface administration, excluded because none of
  the reviewed appliance families publishes it (`SPLITS.md`, 2026-06-12), yet
  interface administration is this class's defining operation; and it carries
  no capture, which is placed on the traffic controller (`SPLITS.md`,
  2026-06-15; see the capture paragraph above). *Over*-specified in the other direction: its mandatory
  members include a WAN-uplink object model, SD-WAN policy and security
  bundles that a carrier/aggregation router cannot satisfy — on a router they
  are optional facets. A tier or extension of the appliance cannot fix both:
  adding interface administration to it would contradict the recorded
  appliance decision, and demoting its mandatory members would break its
  drivers. The router and the appliance share most service capabilities by
  **reuse of the same capability protocols**, not by one archetype extending
  the other.
- **`linux_sdwan_router` (`SdwanRouterDevice`, the Linux twin)** —
  *over*-specified: its members include host-substrate levers (connection
  table, per-netdev interface configuration, iptables NAT, host capture) that
  a closed router does not expose; a router driver could satisfy them only
  with stubs. No tier or extension closes that: a router tier on the twin
  would still inherit the mandatory host levers, and demoting them would
  break the twin's drivers, whose host levers are the reason the twin exists.
- **`managed_switch_l2`, `managed_switch_l3`, `managed_switch_l3_routed`** —
  *under*-specified: forwarding-tier archetypes keyed on VLANs and switch
  ports, with no WAN access, NAT, stateful firewall or routing-peer reset;
  their `switch_qos` classifies and marks (trust mode, DSCP↔CoS map,
  match→mark rules) but carries no queueing, shaping or per-class counters. *Over*-specified: every one of them mandates the switch
  port layer — `switch_ports`, `switch_vlans`, `spanning_tree`,
  `link_aggregation`, `port_poe`, `port_security`, `storm_control`,
  `mac_table`, `placement` — which a carrier/aggregation router with no LAN
  switching cannot satisfy. No tier or extension closes that: a router tier on
  `managed_switch_l3_routed` would still inherit the mandatory port layer, and
  demoting it would break the switch drivers. A router's integrated switch
  reuses the switch capability layer as an optional facet of this archetype
  instead.
- **`linux_cpe` (`CpeDevice`)** — *under*-specified: a residential gateway
  that publishes neither the routing-peer levers nor the enterprise services
  of this class. *Over*-specified: it mandates the Wi-Fi stack (`wifi_radio`,
  `wifi_bss`, `wifi_stations`, `wifi_rf`, `wifi_transitions`,
  `wifi_onboarding`), device management and lifecycle, a hardware console and
  the host levers (`ip_interface`, `conntrack`, host `nat`), which a closed
  router does not publish. No tier or extension closes that for the same
  reason as the switches: the mandatory members stay mandatory.
- **The remaining archetypes** (LAN, WLAN and QoE clients, SIP phone and
  server, WAN server, traffic controller and generator, ACS, provisioner,
  TFTP) are test-bed hosts, not network elements under test; none overlaps.

The conclusion is a separate archetype that composes what a managed router
publishes, reusing existing capability protocols wherever their shape holds.

### Trigger families

The triggering estate spans three vendor families, reviewed at these public
version lines:

- **Cisco IOS-XE, release 17.9 and later.** One software line across the
  enterprise branch, small branch, industrial and carrier/aggregation classes
  (the 17.9 train publishes release notes for the ISR 1000 and ISR 4000, the
  ASR 900/920 and ASR 1000, the Catalyst 8000 edge platforms and the Catalyst
  IR rugged routers). Classic IOS is out.
- **Huawei VRP 5.170, the VRP5 line on the AR / NetEngine AR series.** The
  carrier NetEngine 40E/8000 routers run the separate VRP8 train and are out
  of scope.
- **Ekinops OneAccess ONE-series on OneOS6.** The OneOS6 generation is the
  floor (OneOS5 excluded); no public minor-version numbering exists, so the
  minor version is pinned on first driver evidence.

Every trigger family covers the branch classes with xDSL and cellular access
options; the carrier/aggregation class is evidenced by the IOS-XE family.

### Reviewed-family list (proposed for ratification)

Eight families: the three trigger families plus five competitors.

| Family | Role | Reason in |
| --- | --- | --- |
| Cisco IOS-XE ≥ 17.9 | trigger | triggering estate; spans all four device classes |
| Huawei VRP 5.170 (AR / NetEngine AR) | trigger | triggering estate; branch and small-branch classes |
| Ekinops OneOS6 (ONE-series) | trigger | triggering estate; branch and small-branch classes with voice |
| Juniper Junos OS ≥ 22.4 (MX, ACX on Junos OS, SRX) | competitor | carrier edge to branch security router in one OS; Junos OS Evolved is a separate line and out |
| Nokia SR OS ≥ 22 (7750 SR; 7250 IXR platforms on SR OS — the SR Linux IXR models are out); 7705 SAR Gen 2 on SR OS ≥ 25.3 | competitor | carrier and aggregation edge; access/industrial variants with cellular |
| HPE Comware 7 (MSR) | competitor | full branch router with voice, DSL and cellular; Comware 5 is out |
| Fortinet FortiOS ≥ 7.2 (FortiGate as a branch router) | competitor | branch router; FortiGate is also a family of the SD-WAN appliance review, so the router and appliance matrices share one column for comparison |
| MikroTik RouterOS v7 | competitor | closed router product at the low end of the market; probes the neutrality envelope; v6 is out |

Excluded, with reasons: **Arista EOS** (aggregation and data-centre routing
without the branch service set — NAT, zone firewall, voice, xDSL or cellular
access); **Ubiquiti EdgeRouter** (effectively end of development).

Not reviewed: **Cradlepoint, Peplink, Versa, Palo Alto PAN-OS**. They are outside the triggering
estate and this charter makes no claim about their published operations; any
of them can join the list by a dated revision, as the appliance design's
fifth-family review did.

Eight families give denominators with meaning (a core threshold of every
trigger family plus a majority of eight), and the set covers every device
class twice or more outside the trigger families.

### Demand

The demand evidence is held privately by the maintainers (a private request
under `docs/archetypes/README.md`, "The request"). It asks for the operations
listed under "The class" above except two, which this charter carries on
family evidence rather than on demand: **own-traffic capture** and the
**zone-based stateful firewall with interface-bound data-plane filtering**.
The design's matrix carries the per-family evidence for both, and either is
dropped there if the evidence does not hold.

In addition, the demand asks for operations whose placement the design
decides — in the archetype, in a tier, or in a separate operational
capability outside the archetype shape:

- physical interface parameters (speed, duplex, negotiation, MTU) and header
  transparency in transit;
- software image lifecycle (stage, activate, roll back);
- configuration export and import;
- security posture of the management plane (services, stored secrets) and
  protection of the router's own control plane under load;
- monitoring access; command authorisation levels and accounting for
  operators (authentication itself — central server with a local fallback —
  is in the class list);
- flow export, configured probes and tracking, overlay tunnel state;
- link aggregation, cellular radio and subscription state, backup-WAN
  failover.

### Sources for the trigger version lines and for capture

- Cisco IOS XE 17.9 on the rugged IR platforms: "Release Notes for Cisco
  Catalyst IR1101, IR1800, IR8140, and IR8340 Routers (Cisco IOS XE Cupertino
  17.9.5)", cisco.com.
- Huawei VRP 5.170 on NetEngine AR: "Displaying Version Information",
  NetEngine AR V300R019 CLI-based Configuration Guide, support.huawei.com
  (`VRP (R) software, Version 5.170 (AR6300 V300R019C00)`), and the Common
  Criteria Security Target for the NetEngine AR6121 V300R019,
  commoncriteriaportal.org.
- Huawei VRP8 on the carrier NE40E: the Common Criteria Security Target for
  NE40E/CX600/ME60/NE20E V800R008, commoncriteriaportal.org.
- Own-traffic capture to a file: "Packet Capture Configuration Command"
  (`capture-packet … destination file`), NetEngine AR V300R019 Command
  Reference, support.huawei.com; "Embedded Packet Capture Overview"
  (`monitor capture … export` to a PCAP file), Embedded Packet Capture
  Configuration Guide, Cisco IOS XE 17, cisco.com.

### Sources for the competitor version lines

- Junos OS 22.4 on the ACX, MX and SRX Series: "Release Notes: Junos OS Release
  22.4R1", juniper.net.
- SR OS 22 on the 7750 SR: "SR OS 22.10" documentation suite; 7705 SAR Gen 2 on
  SR OS: "7705 SAR Gen 2" documentation releases (25.3.R2 and later),
  documentation.nokia.com.
- Comware 7 on the MSR series: "HPE FlexNetwork MSR Router Series Comware 7
  Fundamentals Configuration Guide", hpe.com.
- FortiOS 7.2 (and capture to a PCAP file): "Using the packet capture tool",
  FortiGate / FortiOS 7.2.0 Administration Guide, docs.fortinet.com.
- RouterOS v7: "Upgrading to v7", RouterOS documentation, help.mikrotik.com.

### Open questions carried into exploration

- The OneOS6 minor version, pinned on first driver evidence.
- Whether software and configuration lifecycle belong to the archetype or to
  a separate operational capability shared with other archetypes.

## 2. Cross-family matrix

✓ = fully present · ◐ = partial/caveated · ✗ = absent · ¹ = no official
public source at command level (Ekinops publishes datasheets only); verify
against the OneOS6 command/YANG reference or on first driver evidence before
promoting to ✓; every ◐¹ cell is a stage-4 verification item (§9)

| Capability | Cisco IOS-XE ≥ 17.9 | Huawei VRP 5.170 | Ekinops OneOS6 | Junos OS ≥ 22.4 | SR OS ≥ 22 | Comware 7 | FortiOS ≥ 7.2 | RouterOS v7 |
| --- | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| Interface admin (shut/no-shut own interfaces) | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Static routes (per-entry) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| OSPF | ✓ | ✓ | ✓ v2 only | ✓ | ✓ | ✓ | ✓ | ✓ |
| BGP (config + operational read) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| EIGRP / proprietary IGP | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| On-box NAT (source/PAT, static 1:1, port-forward) | ✓ | ✓ | ✓ | ✓ | ◐ CGN/hw | ✓ | ✓ | ✓ |
| Stateful/zone firewall | ✓ ZBF | ✓ zones + ASPF | ◐ ZBF (licensed) | ✓ | ◐ stateful hw | ✓ | ✓ | ◐ chains, no zones |
| Security bundles (IPS, URL filtering, app-aware firewall) | ✓ UTD (licensed) | ✓ IPS + URL filtering | ◐ DPI / app-ID only | ✓ SRX UTM (licensed) | ◐ 7750 / VSR with ISA Application Assurance (app-ID, URL filtering; no IPS); not SAR Gen 2 | ✓ IPS + URL filtering (licensed, model-scoped) | ✓ | ✗ (absence) |
| ACL / packet filtering (interface + direction) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| QoS (classify, mark DSCP, shape/police, queue) | ✓ MQC | ✓ MQC-style policy | ✓ CBQ/CB-WFQ/LLQ | ✓ CoS | ✓ H-QoS | ✓ | ◐ shaping-policy | ◐ mangle+queues |
| IPsec site-to-site | ✓ | ✓ | ✓ | ✓ | ◐ 7750 / VSR with ISA or ESA; not SAR Gen 2 | ✓ | ✓ | ✓ |
| Dynamic-overlay VPN (spoke-to-spoke shortcut) | ✓ DMVPN | ✓ DSVPN | ✗ (DVTI is hub-dynamic only) | ✓ ADVPN | ✗ | ✓ ADVPN(VAM) | ✓ ADVPN | ✗ |
| SLA-conditioned path steering (probe + track + policy routing) | ✓ IP SLA + track + PBR | ✓ NQA + track + PBR | ◐ native under SD-WAN licence | ✓ RPM + ip-monitoring | ◐ BFD- / ping-tracked static routes | ✓ NQA + track + PBR | ✓ SD-WAN rules | ◐ netwatch + routing marks |
| DHCP server (on-box) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DHCP client | ✓ | ✓ | ✓ | ✓ | ◐ mgmt/ZTP | ✓ | ✓ | ✓ |
| NTP / syslog / SNMP | ✓ | ✓ | ◐¹ (syslog, SNMP ✓; NTP unlisted) | ✓ | ✓ | ✓ | ✓ | ✓ |
| FHRP (VRRP / HSRP-equivalent) | ✓ HSRP+VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP | ✓ VRRP |
| IP SLA / reachability probing (configured probe + result read) | ✓ IP SLA | ✓ NQA + TWAMP | ◐¹ "QoS measurement probe" | ✓ RPM | ✓ OAM/TWAMP | ✓ NQA | ✓ SD-WAN performance SLA | ◐ netwatch |
| Flow telemetry (NetFlow/IPFIX-class) | ✓ FNF | ✓ NetStream | ✓ NetFlow | ✓ J-Flow/IPFIX | ✓ Cflowd/IPFIX | ✓ NetStream | ✓ IPFIX | ◐ Traffic-Flow |
| On-box packet capture to file | ✓ EPC | ✓ capture-packet | ◐¹ "flow capture and decoding" | ◐ SRX datapath ✓ / MX RE-bound | ✓ mirror-dest pcap | ✓ packet-capture | ✓ packet capture tool (PCAP) | ✓ /tool sniffer (PCAPNG) |
| Discovery (LLDP) | ✓ (+CDP) | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Integrated L2 switching | ✓ | ✓ | ✓ | ✓ branch SRX | ◐ service-model | ◐ fixed MSR95x; module on MSR4000 | ✓ | ✓ |
| Cellular / LTE / 5G WAN | ◐ ISR and IR platforms | ✓ | ✓ LTE + 5G | ✓ LTE mPIM | ✗ not on the pinned platforms | ✓ | ◐ select models | ✓ |
| xDSL WAN | ◐ ISR with an xDSL module | ✓ | ✓ model-scoped (VDSL2, ADSL2+, G.SHDSL EFM) | ✓ VDSL2 mPIM | ✗ not on the pinned platforms | ✓ | ◐ 60E-DSL only | ✗ |
| Voice gateway (FXS/FXO/BRI/PRI, SIP trunk / SBC-class) | ◐ ISR with voice modules | ✓ | ✓ + embedded SBC | ✗ | ✗ | ✓ | ✗ | ✗ |
| **Charter operations** | | | | | | | | |
| Device reload (+ uptime / readiness read) | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Management-access filtering (an ordered filter on traffic to the device's own management services) | ✓ service-level ACLs | ✓ user ACL | ◐¹ zone policy to the management zone | ✓ lo0 filter | ✓ management access filter | ✓ per-service ACLs | ✓ local-in policy | ✓ input chain |
| Operator authentication via RADIUS / TACACS+ with local fallback | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ◐ fallback via a local account | ✓ |
| Routing-table read per routing instance | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Routing-peer reset (operator command) | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Wired access-session reset (PPPoE reconnect / WAN DHCP renew) | ✓ | ✓ | ◐¹ | ✓ | ◐ subscriber side only | ✓ | ✓ | ✓ |
| Physical interface parameters (speed, duplex, auto-negotiation) | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Interface MTU | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Software image lifecycle (stage, activate, roll back) | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ physical units | ✓ |
| Configuration export / import | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Management-plane posture (unused services, stored secrets) | ◐ checklist | ✓ | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Control-plane protection | ✓ CoPP | ✓ cpu-defend | ◐¹ | ✓ | ✓ | ✓ | ✓ local-in policy | ✓ input chain |
| SNMP agent access (communities / v3 users, source-restricted) | ✓ | ✓ | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Command authorisation and accounting | ✓ | ✓ | ◐¹ | ✓ | ✓ | ✓ | ◐ no TACACS+ accounting | ✓ |
| Overlay / IPsec tunnel state read | ✓ | ✓ | ◐¹ | ◐ SRX, MX with services card | ◐ 7750 / VSR | ✓ | ✓ | ✓ |
| Link aggregation (LACP) on routed interfaces | ◐ documented for ASR | ✓ | ◐¹ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Cellular radio and subscription state read | ◐ ISR and IR platforms | ✓ | ◐¹ | ◐ SRX with LTE mPIM | ✗ | ✓ | ✓ model-scoped | ✓ |
| Backup-WAN failover and fail-back | ✓ | ✓ | ✓ | ✓ | ◐ tracked static routes | ✓ | ✓ | ✓ |

> **Citation status.** Every cell is backed by a source in §10, assessed at
> the version lines the charter pins (§1): IOS-XE ≥ 17.9, VRP 5.170 on
> NetEngine AR (V300R019 guides), the OneOS6 generation, Junos OS ≥ 22.4,
> SR OS ≥ 22 (7705 SAR Gen 2 ≥ 25.3), Comware 7, FortiOS ≥ 7.2, RouterOS v7.
> Ekinops publishes datasheets and brochures only, so the OneOS6 cells marked
> ¹ have no official command-level source; they are ◐ until verified, not ✗.
> A few cells rest on the existence of the cited document rather than a quoted
> passage, and a few ✗ cells on the absence of any documented section; §10
> marks both (*(existence)*, *(absence)*).

**What a cell asserts.** A ✓ records that the family *publishes the
operations* behind the row — a configuration write with read-back, an
operational read, or an exec-level lever — through some management plane of
its own. Which plane (CLI, NETCONF/YANG, RESTCONF, gNMI, vendor REST, or a
controller fronting the box), whether a licence gates it, and whether a given
instance exposes it are driver facts, recorded in §8; they never decide a cell.

**Classification of the surface (of 8):**

- **Universal (mandatory baseline)** — interface admin (7 ✓ + 1 ◐¹);
  static/OSPF/BGP (8); ACL filtering (8); IPsec s2s (7 + 1 ◐); DHCP server
  (8) + client (7 + 1 ◐); NTP/syslog/SNMP (7 + 1 ◐¹); VRRP-shaped FHRP (8);
  QoS *by intent* (6 + 2 ◐); flow telemetry (7 + 1 ◐); LLDP discovery
  (7 + 1 ◐¹).
- **Strong-majority (baseline, per-method unsupported-capability)** — on-box
  NAT (7 + 1 ◐); stateful/zone firewall (5 ✓ + 3 ◐); configured reachability
  probing (6 ✓ + 2 ◐); **on-box packet capture (6 ✓ + 2 ◐)**;
  dynamic-overlay VPN (5 ✓ + 3 ✗, ✗ on one trigger family); **SLA-conditioned
  path steering (5 ✓ + 3 ◐ — WAN-edge tier, by composition, §6)**.
- **Minority / additive (optional tiers)** — integrated switching (6 + 2 ◐,
  model-scoped); cellular WAN (5 + 2 ◐ + 1 ✗); xDSL WAN (4 + 2 ◐ + 2 ✗);
  **voice gateway (3 ✓ + 1 ◐ + 4 ✗ — on all three trigger families, ◐ on one)**;
  **security bundles (5 ✓ + 2 ◐ + 1 ✗ — security tier, §6)**.
- **Excluded from the neutral contract** — EIGRP (1/8).

**Charter operations (of 8)** — placement in §6 and §12:

- **Present on every family** (✓ or ◐, no ✗) — device reload (7 + 1 ◐¹);
  routing table per routing instance (7 + 1 ◐¹); routing-peer reset
  (7 + 1 ◐¹); physical interface parameters (7 + 1 ◐¹); interface MTU
  (7 + 1 ◐¹); software image lifecycle (7 + 1 ◐¹); configuration export and
  import (7 + 1 ◐¹); control-plane protection (7 + 1 ◐¹); operator
  authentication with local fallback (7 + 1 ◐); SNMP agent access (7 + 1 ◐);
  backup-WAN failover (7 + 1 ◐); management-access filtering (7 + 1 ◐¹);
  command authorisation and accounting (6 + 2 ◐); wired access-session reset
  (6 + 2 ◐); link aggregation (6 + 2 ◐); management-plane posture (6 + 2 ◐);
  tunnel state read (5 + 3 ◐).
- **Access-WAN facet** — cellular radio and subscription state (4 ✓ + 3 ◐ +
  1 ✗).

**How a ◐¹ counts.** A ◐¹ cell records presence that the family's official
material claims (a datasheet or brochure feature line) without a
command-level source; it is not a partial implementation. The classification
counts it as present, which is weaker than a ✓, and the design does not hide
that: much of the core rests on ◐¹ cells in the OneOS6 column. Every ◐¹ is a
stage-4 verification item (§9). A ◐¹ that proves ✗ makes the member a
documented per-method unsupported case on OneOS6, and the member is
re-assessed against the evidence bar ("supported on every trigger family")
before the design lands; one that proves ✓ closes.

## 3. Decision

Add a vendor-neutral **`ManagedRouterDevice`** archetype (registered
`managed_router`), **alongside** — not replacing — `SdwanRouterDevice` and
`SdwanApplianceDevice`. It composes what a managed router universally
exposes, carries interface-admin and on-box capture as first-class levers, and
grows the additive facets (the appliance's WAN-edge surface, integrated
switching, access-WAN, voice gateway, security bundles) as **optional tiers**.

The core composes existing capabilities except two, each argued on the
placement ladder (§4, §6): `OperatorLogin`, a concern no protocol owns, and
`DeviceHealth`, a read-only base split off `DeviceManagement`; the two
capabilities without a consumer (`ReachabilityProbe`, `FlowExport`) are
**GAPS-deferred** until one needs them, per the repo's first-consumer bar.
The host-substrate levers (`conntrack`, `ip_interface`, iptables `nat`) stay
on the twin; the boundary with the twin is tabulated in §5. Packet capture is
on the core: the traffic controller remains the wire vantage of record, and
the router adds the device vantage (§6).

## 4. The archetype

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
    """Managed router — universal core. Vendor-neutral; satisfiable by
    any router whose driver publishes the members below. The reviewed
    families and their evidence are in
    docs/architecture/managed-router-protocol-design.md (§2, §10);
    management mode and transport are driver concerns."""

    interfaces: RoutedInterfaces         # reuse + `enabled` field (SPLITS) — admin state + L3 identity of own interfaces: the defining lever (§6)
    routing_read: RoutingRead            # reuse — RIB read (RouteEntry, + defaulted `vrf` field) (§6)
    static_routes: StaticRoutes          # reuse — per-entry CRUD
    ospf: Ospf                           # reuse — OspfVersion.V3 per-method
    bgp: Bgp                             # reuse — config + operational reads
    nat: ApplianceNat                    # reuse as-is — outcome-shaped; de-branded name on landing (SPLITS, §6)
    acl: SwitchAcl                       # reuse — binding = interface name, or `management` for traffic to the device's own services; de-branded name on landing (SPLITS, §6)
    firewall_zones: FirewallZones        # reuse — zone-shaped stateful admission; per-method unsupported (5 ✓ + 3 ◐) (§6)
    traffic_shaping: TrafficShaping      # reuse — QoS by intent via ShapingRule (classify/mark/limit/prioritise); appliance-shaped caps per-method (§6)
    vpn: SiteToSiteVpn                   # reuse — static IPsec s2s + overlay role model; overlay reads per-method (§6)
    interface_dhcp: InterfaceDhcp        # reuse — per-interface DHCP server/relay over the appliance DHCP sub-models (§6)
    dhcp_client: DhcpClient              # reuse — WAN-interface client
    fhrp: GatewayRedundancy              # reuse — VRRP-shaped
    network_probe: NetworkProbe          # reuse — on-box one-shot reachability (ping/traceroute); feeds `await_reachability` (§6)
    pcap: PcapCapture                    # reuse — on-box capture at the device vantage; tool-named methods renamed (extend); per-method unsupported (§6)
    ntp: NtpConfig                       # reuse
    syslog: SyslogConfig                 # reuse — telemetry path (as appliance)
    discovery: Discovery                 # reuse — LLDP-shaped (CDP is a driver detail)
    info: DeviceInfo                     # EXTENDED — hardware model = coverage axis; `firmware_version` added (§6)
    ownership: ConfigOwnership           # reuse — monitored-vs-managed
    port_status: PortStatus              # reuse as-is — link state, speed, duplex, error counters per physical port (§6 Placement of the charter operations)
    link_aggregation: LinkAggregation    # reuse as-is — LACP groups on routed interfaces (§6)
    device_lifecycle: DeviceLifecycle    # EXTENDED — reload and readiness as today; software image lifecycle and configuration export and import added (§6)
    health: DeviceHealth                 # NEW (split off DeviceManagement) — uptime and online state (§6)
    aaa: AaaClient                       # reuse, renamed from RadiusClient; TACACS+ added (extend) — the device's one AAA-server registry (§6)
    operator_login: OperatorLogin        # NEW — operator login policy over registry servers: login order with local fallback, command authorisation, accounting (§6)

register_device_type("managed_router", ManagedRouterDevice)
```

**Two new capabilities at seed, both argued in §6:** `OperatorLogin`, a
concern no existing protocol owns, and `DeviceHealth`, a read-only base split
off `DeviceManagement` (the `Router`→`RoutingRead` precedent). Every other
member exists today; each change to an existing one is placed on the
placement ladder in §6 and listed in §12. Where a disposition has a fallback,
§6 states the condition that would move to it.

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
    uplinks: ApplianceUplinks            # reuse — UplinkStatus (address, gateway, DNS, state) per uplink; de-branded name on landing (SPLITS, §6)
    uplink_ports: UplinkPorts            # reuse — declared uplink→switch-port wiring (testbed topology fact)
    l3_firewall: L3Firewall              # reuse — outbound/inbound/VPN rule triad, derived as interface ACLs (§6)
    sdwan_policy: SdwanPolicyManager     # reuse — SLA policies + uplink selection by composition (probe + track + policy routing); per-method (§6)

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
    trigger families; absent on carrier cores. (§6 Voice)"""
    voice: RouterVoice                   # NEW (tier) — port inventory + admin/oper state, trunk status, active calls

@runtime_checkable
class SecuredRouterDevice(ManagedRouterDevice, Protocol):
    """Adds the security bundles the appliance archetype carries as mandatory
    members — application-aware firewall, content filtering, intrusion and
    malware prevention — reused as-is. Licence- or platform-scoped where
    present; absent on carrier cores. The family evidence is in
    docs/architecture/managed-router-protocol-design.md (§2, §6)."""
    l7_firewall: L7Firewall              # reuse — application-match rules; per-method where no app engine
    content_filtering: ContentFiltering  # reuse — category + URL rules
    security: ThreatPrevention           # reuse — IPS/IDS mode, anti-malware, security events; per-method
```

Registration of the tier archetypes is **deferred to consumer evidence**: which
facet combinations become named commons device types depends on which the test
environment actually instantiates. The `register_device_type` purity gate runs
downstream, so a testbed can register a combined archetype plugin-local until a
second consumer justifies lifting it.

### Standalone switches — scoping note

Standalone switches sometimes present in the same estate are **not** modelled by
this archetype. Expectation:

- **Enterprise access/distribution switches** fold into the existing
  vendor-neutral `L2Switch` / `L3Switch` / `L3SwitchRouted` archetypes via a
  CLI/NETCONF driver. Those archetypes are capability-shaped and already
  anticipate on-box/structured-RPC switch families in `LEVELS.md`
  (`MacTableWhiteBox` note), so this is primarily a **driver** exercise, not a
  commons change.
- **EtherSwitch service modules** are the integrated-switch facet of a
  *router* — covered here by the `SwitchedRouterDevice` tier (§4), which reuses
  the same switch capability layer.
- **Carrier Metro-Ethernet switches** (EVC, QinQ, service-instance / pseudowire,
  MPLS L2VPN) exceed the enterprise `L2Switch`/`L3Switch` shape and are recorded
  as a **candidate `GAPS.md` entry** (`CarrierEthernet` / EVC capability) to
  assess separately on real test evidence.

## 5. Reuse vs. net-new

Dispositions are the *evaluated* result of the §6 zero-contract-change test,
not a presumption: **reuse** (as-is), **reuse + field / rename** (a
`SPLITS.md` entry, no new protocol), **extend** (a member added to an
existing protocol, rung 5), **new** (a capability no existing protocol owns,
rung 6), **defer** (a `GAPS.md` entry until a consumer), **new (tier)**
(lands with the first consumer of the tier).

| Concern | Capability | Disposition | X-vendor (of 8) | Notes |
| --- | --- | --- | :--: | --- |
| Interface admin + L3 identity | `RoutedInterfaces` (+ `RoutedInterface.enabled`) | **reuse + field** | 7 + 1 ◐¹ | one encoding of the lever, mirrors `SwitchPort.enabled`; fallbacks in §6 |
| RIB read | `RoutingRead` | reuse | 8 | `get_routing_table() -> [RouteEntry]`; per-VRF tagging in the row below |
| Static routes | `StaticRoutes` | reuse | 8 | per-entry CRUD |
| OSPF | `Ospf` | reuse | 8 | v3 per-method (OneOS6 lists v2 only) |
| BGP | `Bgp` | reuse | 8 | config + operational reads (per-method) |
| NAT | `ApplianceNat` | **reuse, rename on landing** | 7 + 1 ◐ | already outcome-shaped; §6 |
| ACL filtering | `SwitchAcl` | **reuse, rename on landing** | 8 | binding string = interface name, or `management`; §6 |
| Stateful / zone firewall | `FirewallZones` | reuse | 5 + 3 ◐ | zone membership + zone-pair policy = the ZBF shape; per-method; §6 |
| QoS by intent | `TrafficShaping` | reuse | 6 + 2 ◐ | `ShapingRule` = classify + mark + limit + priority; caps per-method; §6 |
| IPsec s2s + dynamic overlay | `SiteToSiteVpn` | reuse | 7 + 1 ◐ / 5 + 3 ✗ | s2s universal; overlay per-method; §6 |
| Per-interface DHCP (server / relay) | `InterfaceDhcp` | reuse | 8 | `InterfaceDhcpConfig` shares the appliance DHCP sub-models (`DhcpMode`, `DhcpOption`, `DhcpReservation`, `ReservedRange`); §6 |
| DHCP client | `DhcpClient` | reuse | 7 + 1 ◐ | Nokia's is ZTP/mgmt-oriented (◐) |
| FHRP | `GatewayRedundancy` | reuse | 8 | **VRRP-shaped** (HSRP/GLBP are Cisco-local) |
| One-shot reachability | `NetworkProbe` | reuse | 8 | on-box ping/traceroute; feeds `await_reachability`; §6 |
| Configured probe + result series | `ReachabilityProbe` | **defer (GAPS)** | 5 + 3 ◐ | IP SLA/NQA/RPM/TWAMP-class; reuse `PathMetrics` when it lands; §6 |
| Flow telemetry | `FlowExport` | **defer (GAPS)** | 7 + 1 ◐ | exporter config intent; needs a collector-side consumer; §6 |
| On-box packet capture | `PcapCapture` | **reuse; methods renamed (extend)** | 6 + 2 ◐ | device-vantage capture; the file is fetched off-box or pushed to the harness; §6 |
| NTP / syslog | `NtpConfig` / `SyslogConfig` | reuse | 7 + 1 ◐¹ | telemetry path = syslog (as appliance) |
| Discovery | `Discovery` | reuse | 7 + 1 ◐¹ | LLDP-shaped |
| Model identity, running version | `DeviceInfo` (+ `firmware_version`) | **extend** | 8 / 7 + 1 ◐¹ | the model is the coverage axis; the running version is an identity fact, the extension `DeviceInfo` nominates (§6); management mode stays a driver fact (§8) |
| Config ownership | `ConfigOwnership` | reuse | n/a | monitored-vs-managed |
| Physical link state, speed, duplex (read) | `PortStatus` | reuse | 7 + 1 ◐¹ | the switch archetype's status read, unchanged; setting speed and duplex deferred (GAPS) |
| Interface MTU | `RoutedInterface.mtu` | **reuse + field** | 7 + 1 ◐¹ | defaulted `int | None = None` beside `enabled` |
| Routing table per routing instance | `RouteEntry.vrf` | **reuse + field** | 7 + 1 ◐¹ | defaulted `str \| None = None` (the global table), the shape `GAPS.md` 2026-06-14 pre-designed; a router returns every VRF's entries, tagged (§6) |
| Link aggregation | `LinkAggregation` | reuse | 6 + 2 ◐ | the switch archetype's LACP groups, on routed interfaces |
| WAN DHCP release / renew | `DhcpClient` | reuse | with the access-session row | already on the core |
| Tunnel state | `SiteToSiteVpn.get_vpn_peers` | reuse | 5 + 3 ◐ | already on the core |
| Routing-peer reset | `BgpWhiteBox.reset_session` | **white-box, seeded** | 7 + 1 ◐¹ | a console lever no appliance publishes (§7) |
| Reload and readiness | `DeviceLifecycle.reset`, `wait_for_boot` | reuse | 7 + 1 ◐¹ | the CPE archetype's reset and boot wait, unchanged |
| Uptime, online state | `DeviceHealth` | **new (split)** | 7 + 1 ◐¹ | read-only base split off `DeviceManagement`, which inherits it (§6) |
| Software image, configuration archive | `DeviceLifecycle` | **extend** | 7 + 1 ◐¹ | the device's lifecycle concern, generalised from CPE to any device (§6) |
| Management-access filtering | `SwitchAcl` binding `management` | reuse, binding documented | 7 + 1 ◐¹ | an ordered filter on traffic to the device's own services (§6) |
| AAA-server registry | `AaaClient` (renamed `RadiusClient`, + `protocol`) | **extend + rename** | 8 | the one registry, per `SPLITS.md` 2026-06-15 (§6) |
| Operator login policy | `OperatorLogin` | **new** | 7 + 1 ◐ / 6 + 2 ◐ | login order with local fallback; command authorisation and accounting (§6) |
| Backup-WAN failover | `Router` + composition | reuse (tier) | 7 + 1 ◐ | `WanEdgeRouterDevice`; floating / tracked routes (§6 SD-WAN policy) |
| Cellular radio state, PPPoE session reset | `CellularWan`, `PppSession` | new (tier) | 4 + 3 ◐ + 1 ✗ / 6 + 2 ◐ | `AccessWanRouterDevice` |
| WAN-uplink reads | `Router`, `ApplianceUplinks` | reuse (tier); `ApplianceUplinks` renamed on landing | n/a | `WanEdgeRouterDevice`; the two status records already coexist on the appliance (§6) |
| Uplink wiring | `UplinkPorts` | reuse (tier) | n/a | `WanEdgeRouterDevice`; testbed topology fact |
| Edge firewall triad | `L3Firewall` | reuse (tier) | 8 | `WanEdgeRouterDevice`; derived as interface ACLs on WAN / tunnel interfaces (§6) |
| SD-WAN policy (SLA + uplink selection) | `SdwanPolicyManager` | reuse (tier), by composition | 5 + 2 ◐ + 1 ✗ | `WanEdgeRouterDevice`; probe + track + policy routing; per-method (§6) |
| Security bundles | `L7Firewall` / `ContentFiltering` / `ThreatPrevention` | reuse (tier) | 5 + 2 ◐ + 1 ✗ | `SecuredRouterDevice` (§6) |
| Integrated switching | `SwitchPorts`/`SwitchVlans`/`SpanningTree`/`PortPoe` | reuse (tier) | 7 + 1 ◐ | `SwitchedRouterDevice` |
| Cellular WAN | `CellularWan` | **new (tier)** | 6 + 2 ◐ | `AccessWanRouterDevice` |
| xDSL WAN | `DslWan` | **new (tier)** | 5 + 2 ◐ + 1 ✗ | `AccessWanRouterDevice` |
| PPP/PPPoE | `PppSession` | **new (tier)** | with access-WAN | rides DSL/cellular encapsulation |
| Voice gateway | `RouterVoice` | **new (tier)** | 4 | `VoiceGatewayRouterDevice`; 3/3 trigger families; §6 |

### Shared with the appliance

The functional overlap with the managed SD-WAN appliance is large, and the
management transport is not a protocol fact (§1). Read against
`SdwanApplianceDevice`'s seventeen members, the managed router covers every
one — by reuse, or by derivation from the capabilities it does compose:

| `SdwanApplianceDevice` member | Managed-router home | How |
| --- | --- | --- |
| `routing: Router` | `WanEdgeRouterDevice` | reuse as-is |
| `static_routes`, `bgp`, `vpn`, `traffic_shaping`, `appliance_nat`, `syslog`, `info`, `ownership` | core | reuse as-is |
| `uplinks` | `WanEdgeRouterDevice` | reuse; de-branded name on landing, by the NAT rule (§6, §12) |
| `uplink_ports` | `WanEdgeRouterDevice` | reuse as-is |
| `l3_firewall` | `WanEdgeRouterDevice` | reuse; the driver derives the triad as interface ACLs (§6) |
| `sdwan_policy` | `WanEdgeRouterDevice` | reuse; behaviour by composition, per-method (§6) |
| `l7_firewall`, `content_filtering`, `security` | `SecuredRouterDevice` | reuse as-is (§6) |
| `lan: ApplianceVlans` | derivable | `RoutedInterfaces` + `InterfaceDhcp` over the same DHCP sub-models; `ApplianceVlans` satisfiable by derivation (§6) |

A test step typed against any capability in the first six rows runs on both
archetypes without change. The unit of reuse is the capability protocol under
structural typing (the operations already work that way — `await_reachability`
is typed against `NetworkProbe`, the failover operation against `Router`), so
no shared base archetype is introduced: a superset relation fails on carrier
cores, and a common base would only help a step that needs several capabilities
at once, which consumers already express as structural slices. Revisit only if
implementation shows the same multi-capability step written twice.

### Boundary with the Linux twin

The mirror of the §5 "shared with the appliance" table. The twin
(`SdwanRouterDevice`, `linux_sdwan_router`) is a general-purpose host; the
managed router is a closed product (§1). Each row names a lever one side has
and what the other side uses instead.

| Lever | Linux twin | Managed router |
| --- | --- | --- |
| Connection table | `conntrack` (+ `ConntrackWhiteBox`) | none at sea level; nearest analogue a zone-firewall session-table white-box read (§12) |
| Per-`netdev` interface config (`ip addr/link/mtu/mac`) | `ip_interface` (`IpInterface`) | `interfaces: RoutedInterfaces` (+ `enabled`), the configured L3 object (§6) |
| NAT | iptables `nat` (`Nat`) | the outcome-shaped NAT capability (§6) |
| Interface administration | via host shell, `wan_admin: WanLinkAdmin` | published on the box, `interfaces` + `enabled` (§6) |
| Own-traffic capture | host `pcap: PcapCapture` (tcpdump) | `pcap: PcapCapture` on the box, file fetched off-box (§6); the traffic controller stays the wire vantage of record (`SPLITS.md` 2026-06-15) |

The twin keeps its host levers and their `*WhiteBox` extensions unchanged.

## 6. Modelling decisions

Each call below runs under three rules: **test a zero-contract-change
derivation in the driver before accepting any contract change** (the rule the
review skill applies to every proposal); the archetype boundary is the
published operation set (§1, §1); management mode and transport are driver
facts that never enter a shape (§8). Where a call records fallbacks, the order
is the implementer's ladder and the condition that would move down it is
stated.

### Interface admin — one encoding, on the configured object
The universal, defining lever is "administratively bring **any** interface
up/down and read its state." Three existing surfaces carry the verb:
`WanLinkAdmin` (`bring_wan_down(label)` / `bring_wan_up(label)`, an opaque
label a router driver could treat as an interface name), `SwitchPort.enabled`
(admin state on the switch's configured port object), and `RoutedInterfaces`
(`list/get/set_interface` over `RoutedInterface(name, mode, ip_address,
subnet, vlan_id)` — the SVI / routed-port / loopback surface of the L3-switch
archetype, which is exactly a router's interface surface).

**Decision: `RoutedInterfaces`, with a defaulted `enabled: bool = True` field
on `RoutedInterface`.** One object carries L3 identity *and* admin state,
mirroring `SwitchPort.enabled`; `get_interface` reads the configured state
back; interface configuration (address, mode, VLAN) comes with it. A defaulted
field is not source-breaking for the L3 switch that already composes the
capability. Two conventions travel with the field, in the same `SPLITS.md`
entry (§12):

- **Dynamically addressed interfaces.** A DHCP-client or PPPoE WAN interface
  has no static address. `ip_address` / `subnet` read back as the current
  address, empty when unassigned; a write with empty addressing leaves the
  interface's addressing untouched, so admin state can be set on any interface
  without inventing an address.
- **One encoding.** `WanEdgeRouterDevice` does not add `WanLinkAdmin` on top
  (§4); the lever exists once, on the configured object.

**What would overturn it.** The §9 conformance run of the first driver over
the four interface kinds — a routed port with a static address, a DHCP-client
or PPPoE WAN interface, a loopback, an SVI or sub-interface — must round-trip
`enabled` on each without the driver writing an address it was not given. If
that fails, the fallbacks in order are `WanLinkAdmin` with the label as the
interface name (zero contract change; its docstring's "host-substrate lever"
framing becomes a `SPLITS.md` note; costs the configuration read-back), and
only then a new `InterfaceAdmin`, justified solely by an admin-versus-
operational state read neither surface carries. An operational-state read
beyond the WAN-edge tier's `Router.get_wan_interface_status` is a `GAPS.md`
entry (§12), not a seed member.

Two consequences of a *configured* object as the lever (§8): a
controller-owned instance can satisfy it through a controller push — faithful,
but a configuration transaction at controller latency, never an operational
lever — and a convergence measurement therefore keeps its act on the traffic
controller regardless of who owns the box, the `SPLITS.md` 2026-06-12
rationale unchanged.

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
LAN test needs it; no contract change. The derivation is the
portable direction that exists today; the end-state reshape in the other
direction — the appliance composing the pair and `ApplianceVlans` retired — is
recorded as a `SPLITS.md` candidate with its trigger and prerequisites (§12),
and `ApplianceVlans` keeps its name until then (§6 WAN-edge surface).

### WAN-edge surface — the appliance's, reused
Three appliance members fit a WAN-edge router unchanged; a fourth,
`sdwan_policy`, fits by composition and has the next subsection to itself:

- **`L3Firewall`** — the outbound / inbound / VPN rule triad over `L3Rule`. The
  2026-06-14 `SPLITS.md` entry kept the triad off switches as "gateway-shaped";
  a WAN edge *is* a gateway. A router driver derives it as ACLs: outbound =
  the LAN-to-WAN direction on the WAN interfaces, inbound = WAN ingress, VPN =
  the tunnel interfaces. This puts two rule records on one archetype
  (`SwitchAclRule` on the core's interface-bound ACL, `L3Rule` on the tier) —
  the price of appliance-test reuse, recorded in §12, and consistent with that
  entry's decision to keep the two records separate.
- **`ApplianceUplinks`** — `UplinkStatus` (address, gateway, DNS, state) per
  uplink; richer than `Router`'s `LinkStatus`. The appliance already composes
  both reads, so composing both here adds no new redundancy. The router
  composes it as its **own** surface, so the NAT rule applies: the name is
  de-branded on landing (§12). `ApplianceVlans` is the contrast case — the
  router only derives it as a view, so it keeps its name.
- **`UplinkPorts`** — the declared uplink→switch-port wiring, a testbed
  topology fact with no vendor in it; the placement work reads it on any WAN
  edge.

### SD-WAN policy — behaviour by composition, on the WAN-edge tier
`SdwanPolicyManager` has no *native object* on a managed router: no platform
in the reviewed set carries an "SLA policy" or an "uplink selection rule" as a
single configuration entity on its own management plane (a controller fronting
the box may — that is the appliance archetype's driver path, §8). That does not exclude it. The contract
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
(§11 asks about the unlicensed base); SR OS has no track-conditioned policy
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
  driver-contract note in §12. A driver-side ledger alone is not read-back: it
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
`L7Firewall`, `ContentFiltering` and `ThreatPrevention` are appliance members.
They are not universal on routers — but they are not cloud-only either: IOS-XE publishes
Unified Threat Defense (Snort IPS/IDS, URL filtering) on the ISR 4000 /
Catalyst 8000 classes under a security licence; NetEngine AR V300R019 publishes
IPS and URL filtering ("Deep Security"); Junos SRX and FortiOS carry full UTM;
Comware 7 publishes licensed IPS and URL filtering on its larger MSR models;
OneOS6 has DPI and application recognition but no IPS or anti-malware; SR OS
has Application Assurance (application identification, URL filtering) on the
7750 and VSR with an ISA, and no IPS; RouterOS has none. 5 ✓ + 2 ◐ + 1 ✗,
platform- and licence-scoped inside each family, and only partial on one
trigger family (OneOS6) — a **tier**, `SecuredRouterDevice` (§4),
reusing the three capabilities as-is so that every appliance security test
ports unchanged. Lands on the first router security test (§12).

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

**Management-access filtering is a binding of the same ACL.** Every reviewed
family restricts who reaches its own management services with an ordered
filter on traffic *to the device*, and the filter matches the service by
protocol and port: IOS-XE, VRP and Comware 7 bind an ACL per service
(service-level ACLs for NETCONF/RESTCONF, `access-class` on the VTY lines,
the HTTP/HTTPS and SNMP ACL options); Junos filters on the loopback, SR OS
with its management access filter, FortiOS with local-in policy, RouterOS
with the input chain, and OneOS6 with a zone policy toward its management
zone — each one ordered list for the whole device. So the binding
**`management`** on the de-branded ACL capability carries it:
`set_acl("management", AclDirection.INGRESS, rules)`, the service expressed by
each `SwitchAclRule`'s `protocol` and `dst_port`, which the rule already has.
A per-service platform's driver splits the rules by service; the narrower
binding `management:<service>` is accepted where a test needs one service
alone. Nothing about the contract changes but the documented binding values,
which the M6 docstring already touches (rung 1: a driver mapping, recorded).
The rung-6 alternative — a per-service prefix list on a new capability —
fails on the evidence: only RouterOS publishes a plain per-service prefix list
as its primary form (and it has the input chain as well), and a prefix list
cannot say "deny this source, permit the rest of its subnet" the way the
families' ordered filters can.

The WAN-edge tier's `L3Firewall` triad (§6 WAN-edge surface) is not a third
filtering shape: it is a derivation over this interface-bound ACL, with the
triad's three lists mapped onto WAN and tunnel interfaces, kept so that
appliance-written firewall tests run on a WAN-edge router unchanged.

### QoS — `TrafficShaping` already carries the intent
QoS is present on 8/8 but is the **most model-divergent** capability in the
set: MQC class/policy-maps (IOS-XE / VRP / Comware), CBQ/CB-WFQ/LLQ (OneOS6),
Junos CoS, Nokia H-QoS, FortiOS shaping-policies, RouterOS mangle+HTB. The
neutral contract must express **intent** — *classify on a match, mark DSCP,
rate-limit, prioritise* — and expose none of the policy-map / queue-tree
machinery. `ShapingRule(name, match_type, value, bandwidth_limit_kbps,
dscp_tag, priority)` already carries **all four verbs**, so `TrafficShaping.set_shaping_rules` *is* the intent-level QoS
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
"grow on evidence" addition; with a trigger family absent, the evidence does
not support seeding it.

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
  5 ✓ + 3 ◐ across the set — and it has no consumer. The repo's bar
  (`HeldPrefixes` landed on first consumer evidence, the BGP awaits were
  deferred without it) says defer. When it lands: the result record reuses **`PathMetrics`**
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

### On-box packet capture — the device vantage
**Decision: `pcap: PcapCapture` on the core, its tool-named methods renamed
(an `extend`, §12), per-method unsupported.**

Own-traffic capture is one of the operations that define the class (§1). A
managed router captures to a file on its own management plane: Embedded
Packet Capture on IOS-XE 17.x, `capture-packet` on VRP, mirror-destination
pcap on SR OS (7750 SR and 7705 SAR), `packet-capture` on Comware 7, the
packet capture tool on FortiOS (saved as a PCAP file; `diagnose sniffer` is
the text-only CLI path), `/tool sniffer` on RouterOS — six ✓ — with Junos
(full datapath capture on SRX, RE-bound only on MX) and OneOS6 ("flow capture
and decoding", file semantics unverified — §11) as ◐. That clears the
strong-majority bar; the ◐ families raise unsupported-capability per method.

**The OneOS6 cell and the core threshold.** No public official source settles
whether OneOS6's capture writes a retrievable file: the datasheets list "flow
capture and decoding" and nothing more, and the configuration guides are
behind the vendor's support extranet. The design does not wait on it, and
says why: capture on the core does not rest on that cell. At 6 ✓ + 2 ◐ it is
supported on two of the three trigger families and a clear majority of the
eight whatever OneOS6 answers; if OneOS6 cannot, its driver raises `NotSupportedError` on the three
methods — the evidence bar's "documented per-method unsupported case" — and
the class definition, which carries capture on family evidence (§1), is not
narrowed by one family. The cell is verified at stage 4 from the OneOS6
command reference, and a ✗ there is recorded as that per-method case, not as
a reason to move capture to a tier.

**Why the router carries it beside the traffic controller.** The traffic
controller sees every frame on the wire between two devices; the router sees
what *it* forwarded, marked, translated or dropped. The two vantages disagree
exactly when a test cares — a DSCP remark applied on egress, a NAT
translation, a packet the zone firewall admitted or refused. The traffic
controller stays the **wire vantage of record** (`SPLITS.md` 2026-06-15); the
router adds the **device vantage**. Archetypes that do not publish capture —
the dashboard-only appliance families, switches that only mirror — do not
compose it; a console-bearing edge that publishes it may satisfy the same
capability (§7).

**Shape.** `PcapCapture` is a lifecycle-plus-raw-read contract
(`start_tcpdump(interface, port, output_file, filters) -> handle`,
`stop_tcpdump(handle)`, `tshark_read_pcap(fname, …) -> str`; the
capture-analysis family design records that framing). A router driver
satisfies its shape: `start`/`stop` drive the on-box capture session with the
handle as the session name, and the read obtains the finished file and runs
tshark on the harness host. The file reaches the harness one of two ways:
**pulled** — the box keeps the file and the driver fetches it (SCP/SFTP/TFTP,
whatever the platform offers: IOS-XE, VRP, Comware 7 local files, RouterOS,
FortiOS) — or **pushed** — the box streams the capture to a file URL it is
given (SR OS `mirror-dest` pcap, which buffers on the CPM and transfers over
FTP or TFTP; Comware 7's `write url` form), in which case the driver passes a
harness-side file server as the destination and reads the file there. The capture-analysis operations
(`path_placement`, `marking_observation`) then run over a router vantage
unchanged, and `capture_shared_window` can bracket a router capture beside a
traffic-controller capture in one shared window.

**The method names are de-branded here.** They carry tools a router never
runs, and the rule that de-brands `ApplianceNat`, `ApplianceUplinks` and
`SwitchAcl` with this archetype (rename when the archetype composes the
capability as its own surface, §12 M7) applies to `PcapCapture` equally.
`start_capture`, `stop_capture` and `read_capture` are added with the current
signatures; `start_tcpdump`, `stop_tcpdump` and `tshark_read_pcap` stay
declared for the deprecation period and delegate. A protocol method rename
adds a member, so the row is an `extend`: every `PcapCapture` implementer
(the host, client, traffic and voice archetypes' drivers) adds the three new
names, each a one-line delegation, in the release that lands it (§12 M37).

**Limits (driver notes, not contract shape).** On-box capture is buffer- and
count-bounded, may be CPU-punted and rate-limited, is control-plane-only on
some carrier platforms (Junos MX), and is never a line-rate instrument; the
file must be fetched off-box before it is read (§8).

### Placement of the charter operations — the placement ladder

Every operation the charter adds is placed on the cheapest rung of the
placement ladder (`docs/archetypes/README.md`) that genuinely fits:

| Operation | Rung | Home | Why no cheaper rung |
| --- | --- | --- | --- |
| Link state, speed, duplex (read) | 2 reuse | `PortStatus` | — |
| Link aggregation | 2 reuse | `LinkAggregation` | — |
| WAN DHCP release / renew | 2 reuse | `DhcpClient` | — |
| Tunnel state | 2 reuse | `SiteToSiteVpn.get_vpn_peers` | — |
| Backup-WAN failover | 2 reuse (tier) | `Router` + composition | — |
| Routing table per routing instance | 3 defaulted field | `RouteEntry.vrf: str \| None = None` | no capability reads another VRF's table; a defaulted field keeps every `RoutingRead` implementer compiling. It is the field `GAPS.md` 2026-06-14 pre-designed, landing ahead of the rest of that design (below) |
| Interface MTU | 3 defaulted field | `RoutedInterface.mtu: int \| None = None` | the configured L3 interface already carries `enabled`; the MTU is one more attribute of it |
| Routing-peer reset | 4 white-box | `BgpWhiteBox.reset_session(peer)` | a lever, not an intent; no appliance publishes it, so a `Bgp` member would break every appliance driver |
| Reload and readiness | 2 reuse | `DeviceLifecycle.reset(method)`, `wait_for_boot(timeout_s)` | — |
| Image stage / activate / roll back; configuration export / import | 5 extend | `DeviceLifecycle` | no capability carries them; `DeviceLifecycle` owns the device's lifecycle concern, and every archetype composing it (CPE today) can implement them, so no archetype is left permanently unsupported and a new capability is not earned. CPE drivers add `NotSupportedError` stubs until they implement them |
| Running version | 5 extend | `DeviceInfo.firmware_version` | an identity fact, and the extension `DeviceInfo`'s docstring nominates ("serial, firmware version"); §8 already routes firmware facts that must cross the boundary to `DeviceInfo`. The appliance and switch drivers composing `DeviceInfo` implement it from their management APIs or stub it |
| Uptime, online state | 6 new capability (split) | `DeviceHealth`, inherited by `DeviceManagement` | `DeviceManagement.get_seconds_uptime` and `is_online` already publish both reads, but the rest of `DeviceManagement` is host-shaped (processes, files, load average) and a closed router cannot satisfy it. The two reads move to a read-only base that `DeviceManagement` inherits — the `Router`→`RoutingRead` split — so CPE drivers change nothing and the router composes the base alone; no second uptime read exists |
| Management-access filtering | 1 driver-only | `SwitchAcl` binding `management` (and `management:<service>`) | an ordered filter on traffic to the device, the shape every family publishes (above); only the documented binding values change, in the M6 docstring |
| AAA-server registry (RADIUS and TACACS+) | 3 defaulted field + 5 extend + 5 deprecate | `RadiusServerConfig.protocol`; `add_server` / `update_server` gain `protocol`; `RadiusClient` → `AaaClient` | `RadiusClient` is the device's AAA-server registry (`SPLITS.md` 2026-06-15), not a switch-only one; a second registry would be two points of control over one backing object, the clobber that decision exists to prevent. TACACS+ enters as a protocol value; `L2Switch` drivers accept the keyword and reject TACACS+ where the family has none |
| Operator login order with local fallback; command authorisation; accounting | 6 new capability | `OperatorLogin` | no protocol owns operator login policy: the registry owns which servers exist, not how operators log in. It references registry servers by name, as `WifiBss` does, so the registry stays single. Placing it on the registry instead would push three permanent stubs onto every `L2Switch` driver whose family keeps operator login in a cloud dashboard |
| SNMP agent access (communities, v3 users) | deferred | `GAPS.md` (M19) | the source restriction is the `management` binding; community and user configuration waits for a test that needs it |
| Capture method names | 5 extend | `PcapCapture.start_capture` / `stop_capture` / `read_capture` | the de-brand rule of M7 (above, On-box packet capture); a method rename adds members |
| Boot detection | 5 deprecate | `DeviceLifecycle.verify_cpe_is_booting` → `verify_booting` | the only CPE-branded name the router would implement. Both names are declared for the deprecation period and the old one delegates; it lands in the same release as the extension, whose migration line already has every implementer adding members, so it costs nothing beyond that |
| PPPoE session reset; cellular radio state | 6 new capability (tier) | `PppSession`, `CellularWan` | the access-WAN tier's own capabilities (§4) |
| Setting speed and duplex; control-plane protection; management-plane posture | deferred | `GAPS.md` (M39–M41) | the demand reads negotiation from both ends; control-plane policies differ in shape per family; posture is a checklist, verified from the test host |

**`DeviceLifecycle`, extended** (sketch; the design review settles the signatures; the existing members are unchanged except for the rename):

```python
class DeviceLifecycle(Protocol):
    # existing: wait_for_boot, factory_reset, reset, finalize_boot
    def verify_booting(self) -> None: ...                   # new name
    def verify_cpe_is_booting(self) -> None: ...            # deprecated; delegates to verify_booting
    # added
    def stage_image(self, source_url: str) -> str: ...        # returns an image id
    def activate_image(self, image_id: str) -> None: ...      # takes effect at the next reload
    def rollback_image(self) -> None: ...
    def export_configuration(self) -> str: ...                # opaque substrate text
    def import_configuration(self, content: str, replace: bool = True) -> None: ...
```

The configuration payload is opaque substrate text, like a white-box raw read:
a test round-trips it (export, change, import, compare), it never interprets it.
The module docstring loses its CPE framing: the contract is any device's
boot, reset and software lifecycle.

**`DeviceHealth`** (split; `DeviceManagement` inherits it, unchanged for its
implementers):

```python
class DeviceHealth(Protocol):
    def get_seconds_uptime(self) -> float: ...
    def is_online(self) -> bool: ...

class DeviceManagement(DeviceHealth, Protocol):
    # get_load_avg, get_memory_utilization, get_running_processes, … as today
```

**`DeviceInfo`, extended:**

```python
class DeviceInfo(Protocol):
    @property
    def model(self) -> str: ...
    @property
    def firmware_version(self) -> str: ...     # the running software version, as the device reports it
```

**`AaaClient`** (`RadiusClient` renamed, the old name a deprecated alias;
`RadiusServerConfig` → `AaaServerConfig` likewise):

```python
class AaaProtocol(StrEnum):
    RADIUS = "radius"
    TACACS_PLUS = "tacacs+"

class AaaClient(Protocol):
    def add_server(self, name: str, address: str, secret: str,
                   port: int | None = None,            # None = the protocol's default port
                   acct_port: int | None = None,
                   protocol: AaaProtocol = AaaProtocol.RADIUS) -> None: ...
    def update_server(self, name: str, *, …, protocol: AaaProtocol | None = None) -> None: ...
    # remove_server, list_servers, get_server, test_server_reachable as today
```

`AaaServerConfig` gains `protocol: AaaProtocol = AaaProtocol.RADIUS`. The
`port` default widens from `1812` to "the protocol's default", so a TACACS+
server does not inherit a RADIUS port; callers passing a port are unaffected.

**`OperatorLogin`** (sketch; the review settles the signatures):

```python
LOCAL_ACCOUNTS = "local"   # the reserved name for the device's own accounts

class OperatorLogin(Protocol):
    def get_login_order(self) -> list[str]: ...
    def set_login_order(self, order: list[str]) -> None: ...          # registry server names, then LOCAL_ACCOUNTS as the fallback
    def get_command_authorisation(self) -> list[str]: ...             # [] = local privilege levels only
    def set_command_authorisation(self, order: list[str]) -> None: ...
    def get_accounting(self) -> list[str]: ...                        # [] = no accounting
    def set_accounting(self, servers: list[str]) -> None: ...
```

Every name is a server registered on `AaaClient` or `LOCAL_ACCOUNTS`; the
driver builds the family's method list or server group from them. Per-method
unsupported where a family lacks one (FortiOS: no TACACS+ accounting, and the
local fallback is a local administrator account rather than a method-list
step).

**What became of `ManagementAccess`.** The round-1 design proposed one new
capability for four things. The review traced each to an owner: source
restriction is a binding of the ACL capability, the server registry is
`RadiusClient`'s (renamed), SNMP agent configuration stays deferred with
M19, and what remains — how operators log in, what their commands are
authorised against, where their sessions are accounted — is one concern with
no owner, **operator login policy**. That residue is `OperatorLogin`, a
consumer of the registry rather than a second registry.

**The per-VRF read and the pre-designed VRF shape.** `GAPS.md` 2026-06-14
pre-designed multi-VRF as an optional `vrf: str | None = None` field on the
routed interfaces, static routes, routing reads and OSPF, plus a `vrf`
selector on the reads. This design lands the field on `RouteEntry` only, in
that entry's name and type, and leaves the selector and the configuration
fields to that entry's trigger (a test asserting per-VRF segmentation). What
the read means meanwhile: a router's driver returns every VRF's routes, each
tagged, so a test can assert what a VRF holds; it cannot place an interface
in a VRF through the contract, because `RoutedInterfaces` stays scoped to the
global table until the gap lands. The `GAPS.md` entry is updated at landing
to record that the read field arrived first (§12 M42).

### Voice gateway — a fourth optional tier
Voice is 4/8 across the reviewed set (IOS-XE, VRP, Comware, OneOS6) — below
the core bar — but **present on every trigger family**: analog and digital
voice ports (FXS/FXO/BRI/PRI), SIP trunking, and on OneOS6 an embedded SBC;
on IOS-XE and VRP it is platform-scoped to the branch classes with voice DSP
hardware. Below the core bar but universal on the trigger set, it is an
optional tier: `VoiceGatewayRouterDevice` (§4) with one new tier capability,
**`RouterVoice`**, landing with the first voice-gateway consumer at `GAPS.md`
priority medium.

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

## 7. Levels

### Intent (sea-level) and mechanism (white-box)
The appliance capabilities were shaped by cloud management APIs: each is an
*aggregation* of what the cloud layer executes on the box, and a router with
console access can do more than that aggregate — and less. Neither access path
is a superset of the other: the console exposes the mechanism and the raw
state; the cloud API exposes network- and organisation-wide views and
cloud-aggregated telemetry (application flows, the org-scope overlay
advertisements) that no console has. The portable surface is the
**intersection**, and that intersection is the **intent level** — which is why
§5 reuses the appliance's aggregated surface as the router's black-box
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
  composition (§8) this is worth more, not less: the §9 composition
  conformance wants typed reads of the primitives — the raw RIB/FIB, the zone
  session table, the NAT translation table, per-class shaping counters, probe
  statistics and track state behind `sdwan_policy`, IKE/IPsec security
  associations, a running-configuration section. The neutrality rule holds
  here as everywhere: the verb and the return type stay vendor-neutral (a raw
  RIB dump is a legitimate verb, a vendor command name is not), and no vendor
  name enters a method, model or enum at any level. What is substrate-specific
  is the *payload* — that is what "raw" means — so it is opaque to the
  contract, and a test that interprets it is pinned to that substrate, which
  is exactly why such reads are white-box (the `LEVELS.md` 2026-05-02
  precedents: the raw PHY dump, the kernel filter dumps, the raw conntrack
  table, all opaque `str` on the vendor-free Linux reference substrate). For
  this class, structured operational state (NETCONF/YANG, OpenConfig where
  the platform publishes it) is preferred over CLI text; text is the floor,
  not the norm. Candidates in §12.
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
  `ReachabilityProbe` (§6 Reachability). Such a primitive lands as a
  **sea-level** capability on its own evidence and the composed driver then
  builds on it; that is a sea-level question, not a white-box one.

**Selecting the level needs no mechanism of its own.** A driver either
satisfies a `WhiteBox` extension or does not; a test declares the level it
needs by pinning against the extension (`isinstance`), exactly as the existing
white-box tests do. No granularity flag. Which levels an instance offers is
therefore the set of extensions its driver satisfies, and for white box the
enabling fact is **console availability**: a controller-managed edge keeps its
console and offers both levels; a dashboard-only appliance offers sea level
only. Management mode never enters (§8). Two cautions: the whole-list-replace
semantics the appliance capabilities inherited from cloud APIs stay at the
black-box level and a console driver *diffs* — there is no case for a
white-box per-entry write path; and appliances that do have a console (a
Catalyst SD-WAN edge, a FortiGate) may satisfy router-style extensions while a
dashboard-only appliance cannot, which the convention already handles.

### White-box candidates

**`LEVELS.md` (white-box candidates, §7):** one extension is seeded with the
archetype — `BgpWhiteBox`, below — and every other candidate lands on signal
per the convention. The console-granularity review identified them in the two
kinds the convention admits:

- *Raw-state reads* (prove a composed write landed; pin diagnostics):
  `RoutingReadWhiteBox` — raw RIB/FIB dump; `FirewallZonesWhiteBox` — session
  table (the router analogue of `ConntrackWhiteBox`); a NAT white-box on the
  de-branded NAT capability — translation table; `TrafficShapingWhiteBox` —
  per-class counters; `SdwanPolicyWhiteBox` — probe statistics, track state,
  policy-route hit counts; `SiteToSiteVpnWhiteBox` — IKE/IPsec security
  associations; `BgpWhiteBox` — per-neighbour received/advertised routes raw;
  a running-configuration section read (home — `ConfigOwnership` or
  `DeviceInfo` — to settle at seeding). Payloads are substrate state, opaque
  to the contract; verbs and return types stay vendor-neutral, and structured
  operational state is preferred over CLI text where published (§7).
- *Levers with no intent-level equivalent* (reproducible convergence tests):
  `BgpWhiteBox.reset_session(peer)` — **seeded with this archetype**, on the
  charter's demand for routing-peer resets (§6 Placement of the charter
  operations); a NAT white-box `clear_translations()`;
  `SiteToSiteVpnWhiteBox.clear_security_associations(peer)`;
  `SdwanPolicyWhiteBox.force_track_state(name, up | down)` — simulate an SLA
  breach without impairing the wire.

Each candidate is recorded in `LEVELS.md` when a consumer or reviewer signal
lands it, with the drivers expected to satisfy it (router drivers;
console-bearing appliances) and not (dashboard-only appliances). The seeded
one lands with this entry (§12 M38):

> **`BgpWhiteBox` seeded.**
> **Signal:** the managed-router charter's demand for resets of a routing
> peer, to make convergence tests reproducible (§1, §6 Placement of the
> charter operations).
> **Methods:** `reset_session(peer: str) -> None` — a hard reset of the BGP
> session to *peer*, the operator command every reviewed family publishes.
> **Black-box impact:** none; `Bgp` keeps its configuration and operational
> reads, and no method moves out of it.
> **Rationale:** a lever with no intent-level equivalent; no appliance family
> publishes it, so a `Bgp` member would leave every appliance driver
> permanently unsupported.
> **Drivers expected to satisfy:** managed-router drivers; console-bearing
> appliances; L3-switch drivers on families with an operator reset.
> **Drivers expected NOT to satisfy:** dashboard-only appliances.

## 8. Driver-facing neutrality notes

- **Per-method, not per-vendor.** Presence is platform-scoped inside every
  family (a vendor's carrier-metro platform omits the NAT/ZBF/voice/DSL its
  branch platforms carry), and licence-scoped on some (OneOS6 zone firewall,
  and the NETCONF server on some OneOS6 models). Unsupported-capability
  signalling is per method, per the established convention — never "this
  whole capability is absent for vendor X."
- **Configuration ownership is an instance fact; management mode is not a
  shape fact.** Whether this session may write the device's configuration is
  published by `ConfigOwnership.manages_network` — true for a driver that owns
  the writes (locally, or through a controller), false for a console driver
  attached to a controller-owned box, which is then a reads-plus-white-box
  driver and tests that write skip on that fact. Controller-managed instances
  exist in all three trigger families (Catalyst SD-WAN controller mode; the
  OneOS6 SD-WAN Director; iMaster NCE for NetEngine AR); in each, the write
  path and its latency (a controller push is a configuration transaction,
  never an operational lever) are driver notes, and no method changes shape.
  A driver must not mix planes silently — a controller overwrites
  console-side configuration and vice versa — so a driver refuses *local
  writes* on a controller-owned box; it never refuses an archetype on mode.
  If a firmware or ownership fact beyond the boolean must cross the boundary,
  the boundary-fact rule of `capability-only-archetypes.md` puts it on
  `DeviceInfo` / `ConfigOwnership` as a read-only property, never on the
  archetype.
- **Composition is a mechanism, not an approximation.** A capability is
  satisfied by a *sequence* of platform primitives — several CLI commands, a
  probe plus a track plus a policy route — on the same terms as by a single
  native object, provided (1) the composed behaviour has the contract's
  meaning, not a look-alike (the VeloCloud SLA precedent); (2) the `get_*`
  read-back reconstructs from device state, which means the driver names what
  it writes deterministically; (3) a sequence that fails midway raises and
  leaves no partial state; (4) the cross-vendor bar is judged on the
  behaviour, never on the existence of a native object. §6 applies this to
  `sdwan_policy` and `l3_firewall`; it applies equally to NAT, zones and QoS on
  a CLI-managed box.
- **White-box extensions: satisfy or do not; console availability enables
  them.** A driver either satisfies a `<Capability>WhiteBox` extension or does
  not — never raises at call time — and a test that needs one pins against it
  and collection-skips otherwise (`LEVELS.md`). The enabling fact is a console
  or equivalent raw-state and exec-level access, which a controller-owned edge
  keeps and a dashboard-only appliance lacks; management mode never enters.
  Verbs and return types stay neutral; the payload is opaque substrate state
  that pins the reading test; structured operational state is preferred over
  CLI text where the platform publishes it (§7, §12).
- **VRRP is the only portable FHRP.** HSRP and GLBP are Cisco-local; the
  `GatewayRedundancy` contract stays VRRP-shaped, and a Cisco driver maps HSRP
  onto it.
- **EIGRP is Cisco-only** (informational RFC 7868; 1/8 in the reviewed set). It
  is **excluded from the neutral contract** — the router-world analogue of
  keeping vendor strike-ids out of `PacketInjector`/`ThreatPrevention`. A Cisco
  driver that must drive EIGRP does so through a plugin-local capability, never
  a commons method. Deferred entry in §12.
- **OSPFv3 is per-method.** `OspfConfig.version = OspfVersion.V3` is
  unsupported where the platform lists OSPFv2 only (OneOS6 datasheets).
- **Vendor and mechanism names never enter the contract — at either level.**
  "DMVPN" / "ADVPN" / "DSVPN" / "VAM" are vendor terms for one behaviour; the
  contract names the behaviour. The same holds for white-box extensions: a
  raw-dump verb is neutral, a vendor command name is not, and the
  substrate-specific part is confined to the opaque payload (§7).
  The §9 vendor-isolation grep enforces it over the package source.
- **Config-transaction semantics: assume immediate-apply, verify after apply.**
  The on-box CLI of all three trigger families is immediate-apply (IOS-XE
  `configure terminal`; VRP5; OneOS6). Commit semantics exist but are optional
  or path-bound: the IOS-XE NETCONF candidate datastore is off by default and
  enabled per device (`netconf-yang feature candidate-datastore`, running
  datastore otherwise; confirmed-commit since 17.1.1); OneOS6 NETCONF is
  transactional; a controller-owned instance's writes are controller
  transactions (ownership bullet above); Junos and model-driven SR OS are
  commit-based throughout. A neutral driver **verifies after apply** rather
  than assuming either model — a driver-contract note, not a protocol shape.
  The whole-list-replace semantics several reused capabilities carry stay at
  the contract level; a driver on a per-entry management plane *diffs* — there
  is no per-entry write path beside the list write.
- **Programmatic-transport floor (driver fact, never a cell).** CLI + ≥1
  programmatic interface, and that interface is NETCONF/YANG on six of eight
  families (IOS-XE, VRP, OneOS6, Junos, SR OS, Comware — all three trigger
  families among them); IOS-XE additionally offers RESTCONF and gNMI, OneOS6 a
  REST API; FortiOS and RouterOS are vendor-REST only. On some OneOS6 models
  the NETCONF server is licence-flagged — a per-instance fact handled like any
  other unsupported method. Drivers own the transport choice (a NETCONF-first
  driver family covers the trigger estate); the protocol surface is
  transport-agnostic because two reviewed families are REST-only.
- **On-box capture is bounded.** Buffer/count limits, possible CPU punt and
  rate limiting, control-plane-only on some carrier platforms, and a file that
  must be fetched off-box before it is read. The traffic controller remains
  the line-rate wire vantage; the router capture is device-vantage evidence.
- **Service-scoped platforms.** On Nokia SR OS an L3 interface lives inside an
  IES/VPRN service and L2 is VPLS/Epipe, not a global-scope interface or an
  EtherSwitch. A driver maps the neutral per-interface / per-port surface onto
  the service model; the contract assumes neither global-scope interfaces nor a
  hardware switch.

## 9. Verification

The design is verified against the reference corpus (`docs/archetypes/README.md`,
"The reference corpus and the `conformance` check") before it lands, and by
the usual gates after.

**Reference drivers (stage 4).** One reference driver per ratified family —
eight — in the maintainers' private corpus, in the shape a real driver takes:
a `VitroDevice` with the family's published transports as routes, one
implementation per capability, every method carrying out the family's
published operation with a `source:` citation, and every unsupported cell
raising `NotSupportedError` with the source of the absence. They are written
against the core code on this design's `archetype:` PR and prove that each
member maps onto each family's way of working; they are never run against a
device. What they must show for this archetype in particular:

- **Interface admin over the four interface kinds** (§6 Interface admin): a
  routed port with a static address, a DHCP-client or PPPoE WAN interface, a
  loopback, and an SVI or sub-interface — `enabled` round-trips on each without
  the driver writing an address it was not given, for every family that
  publishes the kind. A family that cannot is the overturn condition of §6.
- **The per-method unsupported cells** of §2: every ◐ and ✗ cell is an explicit
  `NotSupportedError` with a source, or a mapping with a source that settles it
  as ✓, and the generated reference matrix agrees with §2 cell by cell
  (verification question 3). The checkable list is every ◐ and ✗ cell of §2
  as it stands when Status moves to `accepted for verification`, every ◐¹ of
  the OneOS6 column among them.
- **Capture with its transfer path** (§6 On-box packet capture): the capture
  mapping names how the file reaches the harness on each family — pulled
  off-box by the driver, or pushed by the box to a harness-side file server
  (SR OS, and Comware 7's URL form).
- **Composition read-back** (§6 SD-WAN policy): for every member a family
  satisfies by a sequence of primitives, the mapping names the primitives it
  writes after the rule and policy names it was given, so read-back
  reconstructs from device state.

**Package gates (stage 4 and after).** Per-capability protocol-conformance
tests; archetype registration and the `runtime_checkable` `isinstance` gate
in the device-types test; the `register_device_type` capability-only purity
gate (`test_archetype_purity.py`); strict mypy and pyright; the twin,
appliance, CPE, switch and host regressions, unchanged by the reuse
dispositions except the defaulted fields, the de-branding renames (with their
deprecated aliases) and the `extend` rows, whose added members every existing
implementer carries (§12); the neutrality scan and the review
of every public text.

**Real drivers (after landing, in consumer plugins).** The version-pinned
re-verification of the three trigger columns against the exact firmware the
first drivers attach to, every ◐¹ cell of the OneOS6 column and the OneOS6
capture-file semantics among them; a capture conformance run proving the file the router
wrote is read through the driver's transfer path and can be bracketed beside
a traffic-controller capture; and a composition conformance run proving
read-back from device state and that a sequence failed midway raises and
leaves no partial policy, at least on `sdwan_policy.set_uplink_selection` and
`l3_firewall.set_outbound_rules`. Those are driver facts; a failure that
changes the shape returns through a `delta:`.

## 10. Sources

The charter (§1) carries the sources for the trigger version lines, capture and the competitor version lines. The matrix sources follow.

Public vendor documentation consulted for the §1 baselines and the §2 concept
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
  pending §11):
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

- H3C MSR610–3600 Comware V7 R6749, Network Management and Monitoring
  Configuration Guide — packet capture configuration (`packet-capture local
  interface … write { filepath | url url }`; "save the captured packets to a
  .pcap file"; "to a remote file on an FTP server or to a local file"). The
  R0615 chapter cited before no longer resolves:
  <https://www.h3c.com/en/d_202604/2810660_294551_0.htm>
- Consulted in the 2026-08-20 review (`hpe.com/psnow`, vendor manuals):
  Comware 7 Fundamentals / NETCONF; FlexNetwork MSR ADVPN (VAM); MSR LTE /
  ADSL2+ / G.SHDSL modules; FXS/FXO/E1 voice SICs; NQA; NetStream.

**Fortinet FortiOS**

- FortiOS 7.2 administration guide — using the packet capture tool ("The
  capture can be saved as a PCAP file"; Network > Diagnostics, Save as pcap):
  <https://docs.fortinet.com/document/fortigate/7.2.0/administration-guide/462154/using-the-packet-capture-tool>
- FortiOS 7.6 administration guide — performing a sniffer trace or packet
  capture (`diagnose sniffer packet`, text output — the CLI path):
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

### Sources for the charter-operation rows and the re-checked cells

Cells marked *(existence)* rest on the cited document's existence and title
rather than a quoted passage.

**Cisco IOS-XE ≥ 17.9** (cisco.com) — reload: Configuration Fundamentals
Command Reference (cf_r1); management-access filtering: "Service-Level ACLs
for NETCONF-YANG and RESTCONF", Programmability Configuration Guide, IOS XE
17.9.x ("connection requests are filtered based on the source IP address";
https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/179/b_179_programmability_cg/m_179_prog_service-level_acls.html),
and the IOS XE Software Hardening Guide (`access-class` on the VTY lines, SNMP
community ACLs; https://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html)
— the Management Plane Protection chapter cited in round 1 restricts
management traffic to designated interfaces, not sources, and no longer
supports the cell;
AAA and fallback: "Configuring Authentication", AAA Configuration Guide;
per-VRF routing table and DHCP release/renew: IP Addressing Services Command
Reference [4000 Series ISRs]; BGP peer reset: "BGP 4 Soft Configuration", IP
Routing Configuration Guide 17.x; speed, duplex, MTU: Interface and Hardware
Component Command Reference [4000 Series ISRs]; image lifecycle: "Installing
the Software using install Commands", ISR 4000 and ASR 1000 Software
Configuration Guides, IOS XE 17; configuration replace: "Configuration Replace
and Rollback", System Management Configuration Guide 17.x; posture: Cisco IOS
XE Software Hardening Guide; control-plane protection: "Control Plane
Policing", QoS Configuration Guide 17.x; SNMP: "Configuring SNMP Support",
SNMP Configuration Guide IOS XE 17; command authorisation and accounting:
"Configuring Authorization" and "Configuring Accounting", AAA Configuration
Guides; tunnel state: `show crypto session`, Security Command Reference, and
the DMVPN Configuration Guide; link aggregation: "Configuring IEEE 802.3ad
Link Bundling", Carrier Ethernet Configuration Guide [ASR 1000]
*(existence)*; cellular state: "LTE Support on Cisco 4000 Series ISR", ISR
4000 Software Configuration Guide, IOS XE 17; backup-WAN failover: "Basic IP
Routing", IP Routing Configuration Guide 17.x; platform scoping of voice and
xDSL: "Configuring Voice Functionality", ISR 4000 Software Configuration
Guide, IOS XE 17, and the Broadband Access Aggregation and DSL Configuration
Guide; security bundles: "Snort IPS", Security Configuration Guide: Unified
Threat Defense, IOS XE 17 ("available only in Security Packages which
require a security license"), with UTD present on the 17.9 train per the ISR
1000 17.9.x release notes; dynamic-overlay VPN: the ISR 1000 17.9.x release
notes (DMVPN caveats on the 17.9 train) *(existence)* — no 17.9-specific
DMVPN configuration-guide page resolved.

**Huawei VRP 5.170** (support.huawei.com, NetEngine AR600/AR6100/AR6200/AR6300
V300R019 Command Reference EDOC1100112391 and topic configuration guides) —
reload: "Device Status Checking Commands"; management-access filtering:
"Configuring and Applying a User ACL"; AAA: "AAA Configuration Commands";
per-instance routing table: "IP Routing Basic Configuration Commands"; peer
reset: "BGP Configuration Commands"; access session: "Resetting PPPoE
Sessions" and "DHCP Configuration Commands"; physical parameters: "Configuring
the Auto-Negotiation Function"; MTU: "Configuring the MTU on an Interface";
image lifecycle: "Configuring System Startup Commands" and "Upgrade Commands";
configuration export: "Saving the Configuration File" and "Backing Up the
Configuration File"; posture: AR Router Security Hardening and Maintenance
Guide, "Device Login Security"; control-plane protection: "Default Settings
for Local Attack Defense"; SNMP: "Setting SNMP Parameters on a Managed
Device", V300R019 MIB Reference; command authorisation: "AAA Configuration
Commands"; tunnel state: "IPSec VPN", Web Configuration Guide; link
aggregation: "Creating an Eth-Trunk"; cellular state: "Cellular Interface
Configuration Commands"; backup-WAN failover: "Configuring Interface Backup in
Active/Standby Mode". Huawei's pages render empty to automated fetches;
these citations were taken from the indexed page titles and excerpts.

**Ekinops OneOS6** (official material only) — operator authentication with
RADIUS and TACACS+: ONE621 datasheet
(https://www.ekinops.com/images/resources/datasheets/03ds-one621-ekinops.pdf);
management-plane posture (secure boot, secure management protocols, password
policies) and management-access filtering (a zone policy between an
interface zone and the management zone — a solution brief, so the cell stays
◐¹): Ekinops security brochure
(https://www.ekinops.com/images/resources/brochures/03sb_security-ekinops.pdf);
SNMP v1/v2c/v3: ONE621 datasheet; backup-WAN failover: "Ethernet Backup over
4G or 5G" (https://www.ekinops.com/solutions/voice-data-access/ethernet-backup-over-4g-or-5g).
All other OneOS6 cells of the charter-operation rows are ◐¹.

**Juniper Junos OS ≥ 22.4** (juniper.net TechLibrary) — `request system
reboot`; "Example: Control Management Access on Juniper Networking Devices";
"Authentication Order for RADIUS, TACACS+, and Local Password"; `show route
table` and `show route instance`; `clear bgp neighbor`; `clear pppoe sessions`
and `clear dhcp client binding`; `auto-negotiation` and `mtu (interfaces)`;
`request system software add` and `rollback`; "Loading Configuration Files";
"Master Password for Configuration Encryption"; "Configuring Control Plane
DDoS Protection"; "SNMP Communities" and "Configure SNMPv3"; "TACACS+
Authentication"; "IKE for IPsec VPN" and "Service Sets for Static Endpoint
IPsec Tunnels"; `show lacp interfaces`; "Configuring the LTE Mini-PIM on SRX
Series Devices"; "Static Route Preferences and Qualified Next Hops" and
"Real-Time Performance Monitoring Overview"; re-checked cells: UTM feature
notes (22.2R1) and "Enhanced Web Filtering"; "Auto Discovery VPNs"; "Use
Packet Capture to Analyze Network Traffic"; management-access filtering:
"Example: Configure a Stateless Firewall Filter to Accept Traffic from
Trusted Sources" (a filter on the loopback) and SNMP `clients`; path
steering: `show services ip-monitoring status` and "Real-Time Performance
Monitoring"; security bundles: "Content Security overview" (formerly UTM;
licensed) and "IDP overview".

**Nokia SR OS ≥ 22 / 7705 SAR Gen 2 ≥ 25.3** (documentation.nokia.com) —
"Model-driven management interfaces" (24.7); 7705 SAR Gen 2 System Management
and Interface Configuration Guides (25.3); System Management Guide, security
(RADIUS / TACACS+, authorisation profiles, accounting); L3 Services Guide,
VPRN show commands; BGP command reference; Triple Play Guide, PPPoE (subscriber
side); "Boot Options" (22.10); "System Management" (23.10.1, rollback);
Advanced Configuration Guide, "Distributed CPU Protection"; SNMP (23.3.1);
Multiservice ISA and ESA Guide, "IP tunnels" (25.7, IPsec scope); 7705 SAR Gen 2
documentation suite (25.3; its one hardware guide is for a single fixed chassis); BFD and VRRP
configuration; DHCPv4 server; TWAMP Light and STAMP (OAM Guide 22.7); Cflowd /
IPFIX; "Mirror services" (22.10.3); DHCP client: "Zero Touch Provisioning",
Basic System Configuration Guide 22.10 (DHCP discovery on the management
port, then in-band — the ◐); ACL: "Filter Policies", Router Configuration
Guide 22.10 ("associated with interfaces, services, or subscribers
separately in the ingress and egress directions"); management-access
filtering: "Management Access Filters", System Management Guide 23.10.1 ("an
ordered list of entries");
security bundles: "Application Assurance", Multiservice ISA and ESA Guide
22.10 (application identification, URL filtering, AA stateful firewall; no
IPS/UTM content inspection); path steering: IP Router Configuration Guide
22.10 (BFD- and CPE-check-tracked static next hops).

**HPE Comware 7 (MSR)** — HPE's TechHub library no longer resolves; the cells
cite H3C's MSR Comware 7 manuals (h3c.com; the same Comware 7 CLI) and HPE
MSR Comware 7 manuals as published: Fundamentals Command Reference (reboot,
boot-loader, `save`, `configuration replace`); Comware 7 Configuration Guides
R0615 (management-access ACLs, AAA with local fallback); MSR5600 IP Routing and
BGP configuration guides (per-instance routing table, `reset bgp`); Layer 2 —
WAN Access Configuration Guide (`reset pppoe-client`); Interface Command
Reference R0305 (speed, duplex, negotiation) *(existence)*; Layer 3 — IP
Services Configuration Guide (MTU, NAT, DHCP, ADVPN); MSR5600 Command Reference
V7-R6749 (login management, attack defence, SNMP, RBAC, AAA); IPsec and IKE
command reference (MSR810/2600/3600); Layer 2 — LAN Switching Command
Reference (route aggregation); mobile communication modem management commands
(MSR5600); High Availability Command Reference (`backup interface`, `backup
track`); MSR954 Network Management and Monitoring Command Reference (NQA,
NetStream, NTP, SNMP, `packet-capture … write`); Security Configuration Guide
(ASPF, IPsec); IPS and URL filtering: MSR610–3600 V7 R6749 Security
Configuration Guide, IPS and URL filtering chapters ("The IPS module requires
a license"; model-scoped — not the MSR810-SI); management-access filtering:
MSR V7 "Login management configuration" (`telnet server acl`, `ssh server
acl`, `ip http acl`, `ip https acl`, SNMP ACLs; https://www.h3c.com/en/d_201904/1166158_294551_0.htm);
path steering: R6749 policy-based routing with track (NQA + track + PBR);
VRRP and LLDP *(existence)*; platform scoping of integrated switching: MSR4000
QuickSpecs and the FlexNetwork Router Series datasheet.

**Fortinet FortiOS ≥ 7.2** (docs.fortinet.com) — `execute reboot`;
"Hardening" (7.2.0 best practices); "Remote authentication for
administrators" (7.2.4); inter-VDOM routing example; `execute router clear
bgp`; `execute interface` (DHCP renew, PPPoE reconnect); "Interface MTU packet
size"; "Upgrading individual device firmware" (7.2.0) and `execute
set-next-reboot`; "Configuration backups"; `config firewall local-in-policy`
(7.2.4); "SNMP v3 users" (7.2.4); "Remote administrators with TACACS+ VSA
attributes" (7.2.4); "IPsec monitor" (7.2.4); "Aggregation and redundancy"
(7.2.0); "Checking the modem status" (7.2.0); "Link monitoring and failover"
(7.2.4) and "SD-WAN performance SLA"; path steering: "SD-WAN rules" (7.2.0);
security bundles: "Security profiles" and "Intrusion prevention" (7.2.0);
management-access filtering: "Local-in policy" (7.2.0; trusted hosts are the
per-administrator form); re-checked cells: "Using the packet
capture tool" (7.2.0), "Security profiles", "ADVPN and shortcut paths"
(7.2.0), `config system netflow`, "LLDP reception", "Hardware switch" (7.2.0),
"VRRP".

**MikroTik RouterOS v7** (manual.mikrotik.com, help.mikrotik.com) — system
reboot and resource; "Services"; AAA user and RADIUS; "VRF"; BGP session;
DHCP and pppoe-client; interface ethernet (speed, auto-negotiation, MTU);
system package (update, downgrade); configuration management and backup;
"Securing your router" and the list of menus with sensitive parameters;
firewall filter (input chain); SNMP; IPsec (active peers, installed SAs);
bonding; LTE/5G; IP route (check-gateway) and Netwatch; re-checked cells:
packet sniffer (PCAPNG), traffic flow, neighbour discovery, switch-chip
features, OSPF, queues; path steering: "Netwatch" and "Policy Routing";
management-access filtering: firewall filter (input chain) and "Services"
(`address=`, the per-service prefix list). The ✗ cells for EIGRP, xDSL, voice
and security bundles rest on the absence of any manual section *(absence)*.

## 11. Open questions

Answers refine the design before the design review; none blocks the
restructure.

1. **Controller-owned instances — resolved (maintainer, 2026-09-27).** The
   first drivers assume no controller-owned instances. Adding them later is
   additive and changes no contract: a `controller` route in the consumer's
   driver beside `cli`, `ConfigOwnership.manages_network` set accordingly,
   per-method unsupported where a controller does not publish an operation,
   and the existing waiting operations for push latency (§8).
2. **OneOS6 minor version** — pinned on first driver evidence (charter).
3. **OneOS6 capture semantics — decided for the design (round 2).** No
   public official source settles whether its capture writes a retrievable
   file. The core placement of capture does not depend on the answer (§6 On-box
   packet capture): the cell decides only whether OneOS6 implements the three
   methods or raises `NotSupportedError` on them, and it is verified at stage
   4 from the command reference.
4. **OneOS6 steering without the SD-WAN licence.** Is probe-conditioned policy
   routing on the base OneOS6? Decides the OneOS6 `sdwan_policy` cell.
5. **De-branded names — resolved (maintainer, 2026-09-27).** `ApplianceNat`
   → `NatRules`, `ApplianceUplinks` → `WanUplinks`, `SwitchAcl` →
   `PacketFilterAcl`, each with a deprecated alias for the deprecation period
   (at least one MINOR and six months; §12).
6. **Competitor cells against the pinned version lines — resolved
   (2026-09-27).** Every column was re-checked at its pinned line (§2, §10).
7. **Placement of the charter operations — revised in round 2
   (2026-09-28).** Each operation is placed on the placement ladder in §6,
   with the reason no lower rung fits; round 1's conditions moved the AAA
   registry to `RadiusClient`, source restriction to the ACL, uptime to a
   split base, the running version to `DeviceInfo`, and withdrew
   `ManagementAccess` (§6, §12 M21–M42).

## 12. Landing manifest

Every symbol change the body proposes. `core` rows land on this design's
`archetype:` PR at stage 4 with changelog entries citing this document and
the row id; `tier-staged` rows become `GAPS.md` pointers at merge. Outcomes
record the design review: round 1 (2026-09-28) returned conditions C1–C15,
and every row carries the conditions that bind it; round 2 confirms or
revises them.

| Id | Kind | Symbol | Mechanism | Placement | Breaking | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | new archetype | `testprotocols.devices:ManagedRouterDevice` (registered `managed_router`) | archetype | core | no | accepted with conditions (C1), 2026-09-28 |
| M2 | new field | `testprotocols.models:RoutedInterface.enabled` (`bool = True`) | defaulted field | core | no | accepted, 2026-09-28 |
| M3 | SPLITS entry | `RoutedInterface.enabled` and the addressing convention (§6 Interface admin) | record | core | no | accepted, 2026-09-28 |
| M4 | rename | `testprotocols:ApplianceNat` → `testprotocols:NatRules`, deprecated alias for the deprecation period | deprecate | core | no | accepted, 2026-09-28 |
| M5 | rename | `testprotocols:ApplianceUplinks` → `testprotocols:WanUplinks`, deprecated alias for the deprecation period | deprecate | core | no | accepted, 2026-09-28 |
| M6 | rename | `testprotocols:SwitchAcl` → `testprotocols:PacketFilterAcl`, deprecated alias for the deprecation period; binding docstring "port, `vlan:<id>`, interface name, or `management` (traffic to the device's own services; `management:<service>` for one service)" | deprecate | core | no | accepted with conditions (C10), 2026-09-28 |
| M7 | SPLITS entry | the four de-brandings (M4–M6, M37) and the rule that only a shared shape is de-branded (`ApplianceVlans` keeps its name) | record | core | no | accepted with conditions (C13), 2026-09-28 |
| M8 | SPLITS entry | observations recorded without a change: two rule records on one archetype (`SwitchAclRule` core, `L3Rule` tier); composition read-back as a driver-contract note; `TrafficShaping` a de-brand candidate; the `ApplianceVlans` reshape candidate with its trigger and prerequisites | record | core | no | accepted with conditions (C13), 2026-09-28 |
| M9 | GAPS entry | `ManagedRouterDevice` design record and matrix (this document) | record | core | no | accepted, 2026-09-28 |
| M10 | new tier | `testprotocols.devices:WanEdgeRouterDevice` (`Router`, `WanUplinks`, `UplinkPorts`, `L3Firewall`, `SdwanPolicyManager`) | archetype | tier-staged — a WAN-edge router test from a second consumer or trigger family | no | accepted, 2026-09-28 |
| M11 | new tier | `testprotocols.devices:SwitchedRouterDevice` (the switch capability layer) | archetype | tier-staged — a router test that drives the integrated switch | no | accepted, 2026-09-28 |
| M12 | new tier + capabilities | `testprotocols.devices:AccessWanRouterDevice`, `testprotocols:CellularWan`, `testprotocols:DslWan`, `testprotocols:PppSession` | archetype | tier-staged — the first access-WAN router test | no | accepted, 2026-09-28 |
| M13 | new tier + capability | `testprotocols.devices:VoiceGatewayRouterDevice`, `testprotocols:RouterVoice` | archetype | tier-staged — the first voice-gateway test | no | accepted, 2026-09-28 |
| M14 | new tier | `testprotocols.devices:SecuredRouterDevice` (`L7Firewall`, `ContentFiltering`, `ThreatPrevention`) | archetype | tier-staged — the first router security test | no | accepted with conditions (C1, C6), 2026-09-28 |
| M15 | GAPS entry | `testprotocols:ReachabilityProbe` (configured probe + result series, `PathMetrics`) | record | tier-staged — a test that needs a probe the router keeps running | no | accepted, 2026-09-28 |
| M16 | GAPS entry | `testprotocols:FlowExport` (exporter configuration intent) | record | tier-staged — a test asserting on exported flows, with a harness-side collector | no | accepted, 2026-09-28 |
| M17 | GAPS entry | an EIGRP-class proprietary IGP (plugin-local, never neutral) | record | tier-staged — a single-vendor test that must drive it through a typed surface | no | accepted, 2026-09-28 |
| M18 | GAPS entry | `CarrierEthernet` (EVC) for carrier Metro-Ethernet switches | record | tier-staged — assessed separately on test evidence | no | accepted, 2026-09-28 |
| M19 | GAPS entry | interface operational-state read beyond `Router.get_wan_interface_status`, and SNMP-agent configuration (communities, v3 users; the source restriction is the `management` ACL binding, M6) | record | tier-staged — a test that needs either | no | accepted with conditions (C14), 2026-09-28 |
| M20 | LEVELS entry | the open white-box candidates of §7, recorded as candidates, not seeded (the seeded `BgpWhiteBox` is M38) | record | core | no | accepted with conditions (C14), 2026-09-28 |
| M21 | new field | `testprotocols.models:RouteEntry.vrf` (`str \| None = None`, the global table), the `GAPS.md` 2026-06-14 shape | defaulted field | core | no | accepted with conditions (C2), 2026-09-28 |
| M22 | new field | `testprotocols.models:RoutedInterface.mtu` (`int \| None = None`) | defaulted field | core | no | accepted, 2026-09-28 |
| M23 | composition | `testprotocols:PortStatus` on `ManagedRouterDevice` | reuse | core | no | accepted, 2026-09-28 |
| M24 | composition | `testprotocols:LinkAggregation` on `ManagedRouterDevice` | reuse | core | no | accepted, 2026-09-28 |
| M25 | white-box extension | `testprotocols:BgpWhiteBox` with `reset_session(peer)` | white-box | core | no | accepted with conditions (C14), 2026-09-28 |
| M26 | protocol extension | `testprotocols:DeviceLifecycle`: `stage_image`, `activate_image`, `rollback_image`, `export_configuration`, `import_configuration`; module docstring generalised | extend | core | yes | accepted with conditions (C3, C11), 2026-09-28 |
| M27 | new protocol | `testprotocols:ManagementAccess` with `ManagementService`, `AuthMethod`, `AaaServer`, `SnmpAccess` — withdrawn; its concerns are placed by M6, M19, M33–M36 | new capability | core | no | declined (C9, C10), 2026-09-28 |
| M28 | SPLITS entry | `DeviceLifecycle` generalised from CPE to any device (M26, M29) rather than split: the extension leaves no composing archetype permanently unsupported | record | core | no | accepted, 2026-09-28 |
| M29 | method rename | `testprotocols:DeviceLifecycle.verify_cpe_is_booting` → `verify_booting`, both declared for the deprecation period, the old delegating; lands with M26 | deprecate | core | no | accepted, 2026-09-28 |
| M30 | protocol extension | `testprotocols:DeviceInfo.firmware_version` (read-only property); module docstring's "firmware version" extension point taken | extend | core | yes | accepted with conditions (C3), 2026-09-28 |
| M31 | new protocol (split) | `testprotocols:DeviceHealth` (`get_seconds_uptime`, `is_online`), inherited by `DeviceManagement`, whose implementers are unchanged | new capability | core | no | accepted with conditions (C11), 2026-09-28 |
| M32 | SPLITS entry | `DeviceHealth` split off `DeviceManagement` so a closed device composes the health reads without the host-shaped members (the `Router`→`RoutingRead` precedent) | record | core | no | accepted with conditions (C11), 2026-09-28 |
| M33 | protocol extension | `testprotocols:RadiusClient.add_server` / `update_server` gain `protocol: AaaProtocol`; `add_server`'s `port` default widens to the protocol's default | extend | core | yes | accepted with conditions (C9), 2026-09-28 |
| M34 | new field | `testprotocols.models:RadiusServerConfig.protocol` (`AaaProtocol = AaaProtocol.RADIUS`), with the `AaaProtocol` enum | defaulted field | core | no | accepted with conditions (C9), 2026-09-28 |
| M35 | rename | `testprotocols:RadiusClient` → `testprotocols:AaaClient`, `RadiusServerConfig` → `AaaServerConfig`, deprecated aliases for the deprecation period; lands with M33 | deprecate | core | no | accepted with conditions (C9), 2026-09-28 |
| M36 | new protocol | `testprotocols:OperatorLogin` (login order with local fallback, command authorisation, accounting; servers named from the `AaaClient` registry; `LOCAL_ACCOUNTS`) | new capability | core | no | accepted with conditions (C9, C10), 2026-09-28 |
| M37 | method rename | `testprotocols:PcapCapture.start_tcpdump` / `stop_tcpdump` / `tshark_read_pcap` → `start_capture` / `stop_capture` / `read_capture`, both names declared for the deprecation period, the old delegating | extend | core | yes | accepted with conditions (C13), 2026-09-28 |
| M38 | LEVELS entry | `BgpWhiteBox` seeded (the entry in §7): signal, methods, black-box impact, rationale, drivers expected to satisfy and not | record | core | no | accepted with conditions (C14), 2026-09-28 |
| M39 | GAPS entry | setting interface speed, duplex and auto-negotiation (the read is `PortStatus`, M23) | record | tier-staged — a test that must force a negotiation outcome from the router side | no | accepted with conditions (C14), 2026-09-28 |
| M40 | GAPS entry | control-plane protection (policy shapes differ per family) | record | tier-staged — a test that needs the router's own control-plane policy | no | accepted with conditions (C14), 2026-09-28 |
| M41 | GAPS entry | management-plane posture (unused services, stored secrets), verified from the test host meanwhile | record | tier-staged — a posture check that needs the device's own read | no | accepted with conditions (C14), 2026-09-28 |
| M42 | GAPS entry | update to `GAPS.md` 2026-06-14 (`Vrf`): the read field landed first (M21); the `vrf` selector on the reads and the configuration fields wait for that entry's trigger | record | core | no | accepted with conditions (C2), 2026-09-28 |

M12's `PppSession` carries the PPPoE session reset (§6 Placement of the
charter operations).

## Review record

- **2026-08-20 to 2026-09-07 — exploration before the track existed.** Five
  revisions on branch `explore/managed-router-archetype` (the three-family
  context, the appliance-overlap review, the two-level review, management mode
  removed from the shape argument, definition by published operations). That
  branch becomes `archetype/<slug>` after this charter merges; its history is
  summarised here and carried into the design's record.
- **2026-09-27 — chartered under the archetype track.** VRP8 out; the OneOS6
  generation is the floor; the family list above is proposed for
  ratification by this charter's review.
- **2026-09-27 — charter review, round 1: approve with conditions (C1–C8).**
  Applied in round 2: C1 capture argued as reopening the SPLITS 2026-06-15
  placement for the device vantage only, and the appliance citation
  corrected; C2 the switch and CPE boundaries argued on their mandatory
  members; C3 competitor version lines pinned; C4 the Cradlepoint / Peplink /
  Versa exclusion replaced by "not reviewed", without a claim about their
  operations; C5 capture and the zone firewall carried on family evidence, not
  on demand; C6 physical interface parameters kept only in the deferred list;
  C7 wired access-session reset added to the routing levers; C8 public sources
  for the trigger version lines added.
- **2026-09-27 — charter review, round 2: approve with conditions (C1–C6);
  charter merged (#62), family list ratified.** Applied as the first commit of
  the exploration branch: C1 the Cisco capture source is the Embedded Packet
  Capture Configuration Guide; C2 the switch under-specification restated
  (`switch_qos` classifies and marks but has no queueing, shaping or per-class
  counters); C3 the no-tier-or-extension argument added for the Linux twin;
  C4 FortiOS kept for its shared column with the appliance review, PAN-OS
  moved to "not reviewed"; C5 MTU and header transparency, and control-plane
  protection, placed in the deferred list; C6 time synchronisation kept in
  the class list only, and operator authentication (class) split from
  command authorisation and accounting (deferred) deliberately.
- **2026-09-28 — design review, round 1: request changes (C1–C15, seven
  blocking).** Applied in round 2:
  - C1 family names removed from the `ManagedRouterDevice` and
    `SecuredRouterDevice` docstrings, which cite this record instead.
  - C2 the per-VRF field takes the shape `GAPS.md` 2026-06-14 pre-designed
    (`RouteEntry.vrf: str | None = None`), and what the read means while
    `RoutedInterfaces` is global-table-scoped is stated (§6, M21, M42).
  - C3 the running version moves to `DeviceInfo.firmware_version` (M30).
  - C4 the IOS-XE management-access cell re-cited to the service-level ACLs
    and the hardening guide, and the row restated as an ordered filter on
    traffic to the device (§2, §10).
  - C5 the Comware capture citation replaced; FortiOS capture confirmed ✓
    (the packet capture tool saves a PCAP file); one count, 6 ✓ + 2 ◐, in §2,
    §5 and §6.
  - C6 the stale ² legend removed; the path-steering and security-bundle
    competitor cells cited; SR OS security bundles ✗ → ◐ (Application
    Assurance) and Comware ◐ → ✓ (licensed IPS and URL filtering); the SR OS
    DHCP-client and ACL cells and the IOS-XE UTD and DMVPN cells cited, the
    last *(existence)*.
  - C7 §9 states the rule: every ◐ and ✗ cell, every OneOS6 ◐¹ among them, is
    a stage-4 verification item; §2 says how a ◐¹ counts.
  - C8 the pushed-capture case recorded (SR OS, Comware's URL form).
  - C9 the AAA-server registry stays single on `RadiusClient`, renamed
    `AaaClient`, with TACACS+ as a protocol value (M33–M35); operator login
    policy is the new `OperatorLogin`, a consumer of the registry by name
    (M36).
  - C10 source restriction is the ACL's `management` binding (M6);
    `ManagementAccess` is withdrawn (M27 declined) and its residue named.
  - C11 uptime is `DeviceManagement.get_seconds_uptime`, shared through the
    split base `DeviceHealth` (M31, M32); `get_uptime_s` dropped.
  - C12 the OneOS6 capture cell does not decide the core placement of
    capture, argued in §6; the cell itself is a stage-4 verification item.
  - C13 the `PcapCapture` methods de-branded as an `extend` (M37).
  - C14 M20 no longer contradicts M25, and the `BgpWhiteBox` `LEVELS.md` entry
    is written out (§7, M38); M19 and the SNMP placement agree; M39–M41
    record the three deferrals.
  - C15 every row carries its round-1 outcome.

### Exploration before the track (2026-08-20 to 2026-09-07)

**2026-09-07 — approval-team review against the three-family context.
Decision: accept-with-conditions; conditions applied in this revision.**

- Trigger restated as three families at public review-baseline generations;
  reviewed-family list ratified at eight; "market reference column" framing
  dropped (§1).
- Matrix re-run at eight columns with recounted denominators and per-cell
  sources; four Ekinops cells left ◐ pending verification (§2, §10).
- Cisco scoping recorded: autonomous mode only, controller mode is the
  appliance archetype, mode is an instance fact, classic IOS out, candidate
  datastore optional (§1, §8).
- Huawei scoping recorded: VRP5 reading of "5.17", VRP8 out pending
  confirmation, V200R0xx NETCONF caveat (§1, §11).
- Voice reframed from "deferred, low" to a fourth optional tier at priority
  medium (§4, §6, §12).
- Net-new list re-derived through the zero-contract-change test: core composes
  existing capabilities only; `ReachabilityProbe` and `FlowExport`
  GAPS-deferred; `InterfaceAdmin`, `StatefulFirewall`, `Qos`, `PacketFilterAcl`
  and `RouterNat` withdrawn as new protocols in favour of `RoutedInterfaces`
  (+ field), `FirewallZones`, `TrafficShaping`, `SwitchAcl` and `ApplianceNat`
  (§4, §5, §6).
- Management-plane and config-transaction notes rewritten (§2, §8).
- On-box packet capture moved from excluded to composed, with the traffic
  controller kept as the wire vantage of record (§6, §5) — a maintainer
  question at adoption ("why not support capture on these devices?") that
  the cross-vendor check answered in favour of inclusion.
- Sources section added (§10); open questions recorded (§11).

**2026-09-07 — appliance-overlap review (revision 3). Question put by the
maintainers: given the large functional overlap with the managed SD-WAN
appliance, and cloud management being an implementation aspect rather than a
protocol-shape aspect, are the shared capability protocols leveraged enough?
Answer: not yet; applied here.**

- §1 boundary restated by published operation set; management transport
  removed from the argument.
- `DhcpServer` (a CPE-provisioning server) replaced by `InterfaceDhcp`, which
  shares the appliance DHCP sub-models (§4, §5, §6).
- `WanEdgeRouterDevice` composes the appliance's WAN-edge surface: `uplinks`,
  `uplink_ports`, `l3_firewall` (derived as interface ACLs) and `sdwan_policy`
  (§4, §6).
- Second maintainer question — does the absence of a native SD-WAN policy
  object exclude implementing the surface for test purposes as a sequence of
  CLI steps? Answer: no; recorded as the general composition rule (§8) with
  its four conditions, applied to `sdwan_policy` (§6), verified by the
  composition-conformance test (§9).
- `SecuredRouterDevice` tier candidate reusing the appliance security bundles
  (§4, §6, §12); two matrix rows added with trigger-column sources (§2, §10).
- `ApplianceVlans` derivation note under LAN (§6); shared-with-appliance table
  (§5): all seventeen appliance members reused or derivable.

**2026-09-07 — two-level review (revision 4). Question put by the
maintainers: the appliance capabilities are aggregations of what a cloud
management layer executes, a subset of what console access allows; does it
have merit to design the shared functionality at the finer console
granularity as a white-box equivalent, letting a test suite select the
level? Answer: yes, in two of three forms; applied here.**

- The axis is intent versus mechanism, not cloud versus console; neither
  access path is a superset of the other, and the intent level is the
  intersection where tests port (§7).
- Two forms with merit, both under the existing `LEVELS.md` convention:
  raw-state reads that prove a composed write landed, and console-only levers
  (session reset, clear translations / security associations, forced track
  state). Mechanism-level configuration writes declined as protocols;
  cross-vendor-neutral primitives land at sea level on their own evidence.
- Level selection through the existing `isinstance` pin on the extension; no
  granularity flag; whole-list-replace stays black-box and console drivers
  diff.
- White-box candidate list recorded in §5 and §12 in the two kinds; §9
  composition conformance reads through the white-box reads once they land.

**2026-09-07 — mode-versus-levels correction (revision 5). Maintainer
observation: whether controller mode uses a controller and autonomous mode a
management plane is not relevant to the shape of the protocol; what is
relevant is the type of methods available to control the device, and that is
what the levels represent. Accepted; applied here.**

- Mode removed from the shape argument: the §1 class definition and the Cisco
  baseline no longer make mode an archetype boundary ("verified in autonomous
  mode" stays as provenance for the §2 cells); the core docstring and §1 drop
  the mode qualifier.
- The levels carry the type-of-methods distinction — sea-level intent writes
  and reads; white-box raw reads and exec levers. Which levels an instance
  offers is the set of extensions its driver satisfies; console availability,
  not mode, enables white box (§7).
- The residual per-instance fact is configuration ownership, published by
  `ConfigOwnership.manages_network`; write path and push latency are driver
  notes; a driver refuses local writes on a controller-owned box, never an
  archetype (§8).
- §11 question 2 now asks whether tests need writes on controller-owned boxes.
- Follow-up in the same review: the §1 device-class definition rewritten to
  define the class by the operations it publishes (interface administration,
  own-traffic capture, interface-bound filtering, on-box services), with the
  host-substrate exclusion stated by substrate and the review set separated
  from archetype membership; management transport moved out of the definition.
- Label sweep: "on-box-managed" dropped from the title and prose in favour of
  "managed router" (the registered name is already `managed_router`); the
  historical review records keep their wording.
- Maintainer observation: the §2 "management planes" paragraph described the
  implementation of an interface, not the methods the interfaces offer.
  Replaced by a note on what a matrix cell asserts (published operations,
  whichever plane); the transport facts and the OneOS6 licence flag folded
  into the §8 programmatic-transport bullet.
- `ApplianceUplinks` added to the de-brand-on-landing list beside
  `ApplianceNat`, with the rule stated: rename when the router composes the
  capability as its own surface; keep the name when it only derives a view
  (`ApplianceVlans`).
- Maintainer question: restructure `ApplianceVlans` onto `RoutedInterfaces` +
  `InterfaceDhcp`? Answer: yes as the end state, not now, never as an
  addition beside the folded record. Recorded in §12 as a SPLITS reshape
  candidate with its trigger and five prerequisites.
- Consistency pass over §6 against revisions 3–5: the chapter intro names the
  two later rules it now runs under; the interface-admin call records the
  consequences of a *configured* lever for controller-owned instances and
  act anchoring; the LAN side cross-references the reshape candidate; the
  WAN-edge surface counts `sdwan_policy` as its fourth member; the SD-WAN
  policy call drops the mode qualifier; the ACL call states that the tier's
  `L3Firewall` triad is a derivation, not a third shape; the capture call
  attributes the precedent to dashboard-only families, not the appliance
  class.
- Journey commentary removed from §6 (this section holds the record): each
  call now states its decision and, where one exists, the condition that
  would overturn it. The interface-admin pick is no longer "provisional":
  `RoutedInterfaces` + `enabled` is the decision, with the dynamic-addressing
  convention recorded and the §9 conformance run over four interface kinds
  as the overturn condition.
- Maintainer observation: "raw vendor text is allowed at the white-box level"
  conflicts with vendor-agnostic capability protocols. Traced to the
  `LEVELS.md` 2026-05-02 precedents (raw PHY dump, kernel filter dumps, raw
  conntrack table — opaque `str` on the Linux reference substrate) and
  restated precisely in §6 and §5: neutrality governs the contract at every
  level (verbs, return types, models, enums); a white-box payload is opaque
  substrate state and pins the test that reads it; structured operational
  state is preferred over CLI text where published.
- Consistency pass over §8: the overlay-name bullet generalised to "vendor
  and mechanism names never enter the contract, at either level"; the
  config-transaction bullet drops the mode qualifier, adds controller-owned
  writes as transactions and the list-replace-versus-diff note; a white-box
  bullet added for driver authors (satisfy or do not; console availability;
  opaque payload; structured state preferred).
- The on-box packet-capture call (§6) and the matching §5 paragraph rewritten
  to state the decision and its intent (device vantage beside the wire
  vantage of record) without the exclusion-and-reversal narrative.
- §5 restructured from "excluded host-substrate levers" into the boundary
  with the Linux twin, a two-way table mirroring the §5 appliance table; the
  white-box candidate list moved to §12 under `LEVELS.md`; §3 states the
  decision without the revision narrative; cross-references updated.

- **2026-09-27 — exploration: the charter operations and the pinned version
  lines.** Eighteen matrix rows added for the charter's class and deferred
  operations, and every column re-checked at its pinned version line, with a
  public source per cell (§2, §10). Maintainer decisions: the OneOS6 column
  cites official Ekinops material only — cells with no official
  command-level source are ◐¹ — and the OneOS6 floor stays the OneOS6
  generation.
