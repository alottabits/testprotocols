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
  filtering, log export, time synchronisation, operator authentication.

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
  with stubs.
- **`managed_switch_l2`, `managed_switch_l3`, `managed_switch_l3_routed`** —
  *under*-specified: forwarding-tier archetypes keyed on VLANs and switch
  ports, with no WAN access, NAT, stateful firewall, QoS-by-class policy or
  routing-peer reset. *Over*-specified: every one of them mandates the switch
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
| Fortinet FortiOS ≥ 7.2 (FortiGate as a branch router) | competitor | branch router bridging to the SD-WAN review |
| MikroTik RouterOS v7 | competitor | closed router product at the low end of the market; probes the neutrality envelope; v6 is out |

Excluded, with reasons: **Arista EOS** (aggregation and data-centre routing
without the branch service set — NAT, zone firewall, voice, xDSL or cellular
access); **Ubiquiti EdgeRouter** (effectively end of development);
**Palo Alto PAN-OS** (a firewall family, reviewed as a security product rather
than a router).

Not reviewed: **Cradlepoint, Peplink, Versa**. They are outside the triggering
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

- physical interface parameters (speed, duplex, negotiation);
- software image lifecycle (stage, activate, roll back);
- configuration export and import;
- security posture of the management plane (services, stored secrets);
- monitoring access, operator authorisation, time synchronisation;
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
  (`monitor capture … export` to a PCAP file), Network Services Configuration
  Guide, Cisco IOS XE 17.x, cisco.com.

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
