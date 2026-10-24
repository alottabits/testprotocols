# Design: vendor-neutral **L2Switch** (managed access switch) protocol shape

| Field    | Value                                                                                                          |
| -------- | ------------------------------------------------------------------------------------------------------------- |
| Status   | Implemented; verified 2026-10-24 against the reference corpus                                                 |
| Author   | rjvisser                                                                                                       |
| Date     | 2026-06-14 (updated 2026-06-14: Arista EOS verification — CCS-720D Series cross-vendor check; AAA/RADIUS + FirstHopSecurity (concept-check 6/6) + NtpConfig added; Arista CDP cell corrected; updated 2026-06-15: StormControl found API-reachable on MS225 via a live hardware check — 5/6 → 6/6, no MS225 shortfall) |
| Related  | `packages/testprotocols/GAPS.md` (2026-05-02 `L2Bridge` HIGH — to be cross-referenced; new `IgmpSnooping` / `PortMirror` / `MulticastRouting` deferrals), `SPLITS.md` (`Router` RIB carve-out; `ApplianceVlans` SVI/DHCP reuse; unified `SwitchAcl`), `LEVELS.md` (`MacTableWhiteBox` candidate), `devices/switch.py` (new), `models/switch.py` (new), `models/l2_common.py` (new — STP/FDB vocab shared with the future CPE-side `L2Bridge`), `models/switch_routing.py` (new, L3 sibling), `docs/architecture/l3-switch-protocol-design.md` (sibling — composes this layer), `docs/architecture/sdwan-appliance-protocol-design.md` (precedent), `models/sdwan_appliance.py` (`RuleAction` / `RuleProtocol` / `DhcpMode` reuse), `syslog_config.py`, `ntp_config.py` (new — small NTP-server-config capability), `radius_client.py` (+ `models/radius.py` — 802.1X/MAB RADIUS backend reuse), `static_routes.py`, `router.py`, `bgp.py` |

This document explains why `testprotocols` carries a dedicated **managed
access switch** archetype — `L2Switch` — and records the shape proposed for it.
It defines the **shared L2 capability layer in full**: VLANs, switchports, STP,
link aggregation, PoE, port-security, AAA (RADIUS), first-hop security (DHCP
snooping + DAI), storm-control, L2 ACL, discovery, MAC table, port status, QoS,
syslog, and NTP. It deliberately does **not** carry any L3
layer; the routed-distribution archetype (`L3Switch`,
`docs/architecture/l3-switch-protocol-design.md`) composes everything here **plus** an L3
layer as a strict superset, and cross-references this document rather than
re-stating the L2 baseline.

The concrete peer/driver target for this archetype is a cloud-managed access
switch (Cisco Meraki MS225); the proposed shape was additionally verified
against the Arista CCS-720D Series² (Arista EOS, CloudVision/eAPI-managed) as a
cross-vendor verification point (see "Cross-vendor neutrality v2"). Those product
names appear **only** in the cross-vendor neutrality matrix and v2 prose below, as
the concept check — never in a proposed protocol, model, or enum name.

## Context and problem statement

`testprotocols` already carries several L2/L3 levers, but **none of them models
a managed switch**. The closest existing shapes were authored for a *Linux host
acting as a router or gateway* — a docker / FRR / iptables / netfilter twin —
and they leak that substrate. A managed access switch is a different kind of
device: it is not a Linux host you shell into, it is a closed product driven
through a **management plane** (a cloud controller, an on-box NETCONF/REST/CLI
plane, or both). Modelling it against the host-shaped levers is **both over- and
under-specified.**

**Over-specified — host-substrate levers a managed switch cannot satisfy.**
A driver for an API/controller-managed switch can only stub these:

- `conntrack` (+ `*WhiteBox`) — the Linux netfilter connection table. A switch
  is not a flow tracker; stateless bridges should not compose this.
- `pcap` (`PcapCapture`) — `tcpdump` / `tshark` on the box shell. Packet capture
  in this framework is the **`TrafficControllerDevice`'s** job (a separate
  device in the path), not the switch's (`SPLITS.md` netem precedent).
- `ip_interface` (`IpInterface`) — per-NIC `ip addr / link / mtu / mac`. A switch
  manages **switchports** and **VLANs** as first-class objects and satisfies
  almost none of the per-`netdev` host surface.
- `nat` (host iptables `Nat`), `packet_filter` / `PacketFilterWhiteBox`
  (netfilter INPUT / OUTPUT / FORWARD chains), `firewall_zones` (OpenWrt /
  firewalld zone + masquerade), `wan_link_admin` (forced link up/down) — all
  host- or gateway-shaped and structurally wrong for a switch.

**Under-specified — switch surfaces that have no capability protocol.**
The first-class object of a managed switch is the **switchport**
(access/trunk/PVID/allowed-VLANs/voice-VLAN/PoE/isolation) — and *nothing* in
the contract models one (`vlan_client` is host-NIC-shaped). Spanning-tree,
link aggregation, PoE, port-security, storm-control, per-port/VLAN L2 ACLs,
first-hop security (DHCP snooping / Dynamic ARP Inspection), LLDP neighbour
discovery, the MAC forwarding table, per-port link/counter status, and switch
QoS all sit on every reviewed access switch and have no home.

**The `L2Bridge` temptation — and why it is the wrong home.** `GAPS.md` carries
a deferred `L2Bridge` entry (2026-05-02, HIGH). It is explicitly
**Linux-bridge-shaped** (`brctl`, `ip link`, `nft table bridge`,
`bridge fdb show`, `br-lan`-is-both-a-bridge-and-an-interface) and its trigger
is the **CPE example**, not a switch. Reusing a substrate-shaped contract on a
different device class is exactly the mistake the SD-WAN appliance archetype
rejected for its four host levers. A managed switch's first-class object is the
*switchport*, not "add port to bridge"; and link aggregation and PoE have **no
home in `L2Bridge` at all**. So this archetype does **not** realize `L2Bridge`
— see §"The `L2Bridge` question" and the tracking-file obligations.

## Decision

Add a vendor-neutral **`L2Switch`** archetype — the managed access switch —
that composes the shared L2 capability layer in full, **excludes** the
host-substrate levers above, and authors the switch-native capabilities that
were missing. A sibling **`L3Switch`** archetype (separate doc) composes
`L2Switch` **plus** an L3 layer as a strict superset; `L3Switch(L2Switch,
Protocol)` makes that relationship explicit and `runtime_checkable`-verifiable.

This mirrors the SD-WAN appliance precedent recorded in `SPLITS.md`: a
capability that structurally belongs to another device does not ride on this one
(netem → traffic controller, 2026-05-02), and capabilities are bundled by
**coherent telco domain**, not by whatever a single substrate exposes together
(2026-05-11).

### Evidence convention — why these capabilities are proposed now

`GAPS.md` is firm that net-new protocols land on **tracked evidence — a test
that needs it, and the cross-vendor concept check**. Two framings apply, and
both point the same way:

- **Foundation baseline.** `testprotocols` is pre-1.0 and deliberately
  establishing a *sound, complete baseline* for the access-switch archetype —
  the same way the Wi-Fi capability family was built out ahead of any single
  consumer to anchor a stable shape. A capability that a **strong majority of
  the reviewed switch families expose** through their management plane belongs
  in that baseline; the per-capability cross-vendor concept check is what keeps
  it from collapsing into a one-vendor quirk.
- **Per-capability evidence.** Each capability maps to a concrete switch-test
  concern — VLAN membership, trunk/access port config, loop prevention, LAG
  bundling, PoE delivery, port authentication, broadcast-storm containment,
  port/VLAN-scoped filtering, neighbour discovery, MAC learning, link status,
  marking/queuing, and log export.

Guard against one-vendor shapes: **every capability carries a `K/6` cross-vendor
concept check** against the six reviewed access families. A net-new capability
enters the baseline only when the *concept* clears a strong-majority bar
(≥ 5/6) **and** is switch-native first-class. Where the design-target product
(MS225) cannot exercise a capability the concept otherwise passes, that
shortfall is expressed as a **per-method unsupported-capability error in the
driver, not a contract leak**. Two capabilities whose concept passes the bar but
which lack a driving test and straddle a device boundary are deferred to
`GAPS.md` rather than guessed at here.

## The archetype

```python
@runtime_checkable
class L2Switch(BaseDeviceProtocol, Protocol):
    switch_ports: SwitchPorts            # new — per-port mode/PVID/allowed-VLANs/enabled/voice/isolation
    switch_vlans: SwitchVlans            # new — per-VLAN id/name registry (distinct from ApplianceVlans)
    spanning_tree: SpanningTree          # new — global mode + per-port guard/edge/cost/priority
    link_aggregation: LinkAggregation    # new — LAG group CRUD by member ports + mode
    port_poe: PortPoe                    # new — per-port enable + draw/status read
    port_security: PortSecurity          # new — per-port access policy + MAC allow/sticky limits
    radius: RadiusClient                 # reuse-as-is — RADIUS server registry (802.1X/MAB backend), referenced by name
    first_hop_security: FirstHopSecurity # new — DHCP snooping + Dynamic ARP Inspection (rogue-DHCP / ARP-spoof prevention)
    storm_control: StormControl          # new — per-port broadcast/multicast/unknown-unicast thresholds
    switch_acl: SwitchAcl                # new (reuses RuleAction/RuleProtocol enums) — new L2 match + port/VLAN/direction binding
    discovery: Discovery                 # new (read-only) — LLDP neighbour read per port
    mac_table: MacTable                  # new (read-only) — FDB read (MAC/port/VLAN)
    port_status: PortStatus              # new (read-only) — link/speed/duplex/counters per port
    switch_qos: SwitchQos                # new — QoS rule list + DSCP→CoS map
    syslog: SyslogConfig                 # reuse-as-is — remote logging destinations
    ntp: NtpConfig                       # new — NTP server config (small/generic, the time-sync sibling of syslog)

register_device_type("managed_switch_l2", L2Switch)
```

Excluded host-substrate levers (kept on host-shaped twins, never on this
archetype): `conntrack` (+ `*WhiteBox`), `pcap` (`PcapCapture`), `ip_interface`
(`IpInterface`), `nat`, `packet_filter` (+ `*WhiteBox`), `firewall_zones`,
`wan_link_admin`. See §"Excluded host-substrate levers".

**Registration:** a new `switch` module is added to the auto-import tuple in
`devices/__init__.py`. `L2Switch` registers `managed_switch_l2`; the sibling
`L3Switch(L2Switch, Protocol)` registers `managed_switch_l3` (its doc).

## Reuse notes — capabilities taken from existing protocols

Two capabilities reuse an existing `testprotocols` shape as-is (`syslog`,
`radius`); a third (`switch_acl`) is **net-new** but reuses existing **enums**:

- **`switch_acl: SwitchAcl` — NEW capability, reuses the rule enums.** The
  reviewed switches use **one ACL engine** matching L2 (src/dst MAC, VLAN) and
  L3/L4 (5-tuple) fields — on the design-target it is literally the *same*
  endpoint for both. So the archetype models **one** `SwitchAcl` capability, not
  separate L2 and L3 protocols. What is **reused** is precisely the two
  enums — `RuleAction{ALLOW,DENY}` and `RuleProtocol` from
  `models/sdwan_appliance.py` — rather than duplicating them. What is **new** is
  the **record** and the **binding surface**: the existing `L3Rule`
  (`models/sdwan_appliance.py`) is a *pure IP 5-tuple* (action, protocol,
  src/dst CIDR + port, comment, syslog flag) and carries **no** src/dst MAC and
  **no** VLAN match field, so it cannot carry the L2 match a switch ACL needs.
  A new `SwitchAclRule` record is therefore defined in `models/switch.py` with
  the optional L2 match fields (`src_mac` / `dst_mac` / `vlan`) plus the optional
  IP 5-tuple, typed by the reused `RuleAction` / `RuleProtocol` enums. (The
  legacy bare-`str` `FirewallRule` in `models/firewall.py` is **not** the reuse
  target — it is the host chain shape `GAPS.md` is migrating away from.) On top
  of the record, the binding is also new: rules bind to a port or VLAN, in an
  ingress or egress direction, as an ordered whole-list-replace. It deliberately
  does **not** compose `l3_firewall` (the appliance LAN/WAN/VPN triad) or
  `packet_filter` (host chains) — those are gateway/host-shaped. The L3 match
  fields are present in `SwitchAclRule` from day one so the sibling `L3Switch`
  reuses the **same** `SwitchAcl` (see its doc); at the L2 layer the L3 fields
  are simply optional.

- **`syslog: SyslogConfig` — REUSE-AS-IS.** Generic remote-logging destination
  list (`SyslogServer` host/port/normalized roles). It satisfies the switch's
  log-export concern directly with no change; `syslog_config.py` is shared
  unchanged with the appliance archetype.

- **`radius: RadiusClient` — REUSE-AS-IS.** The existing `radius_client.py`
  capability — *"a device that authenticates upstream to one or more RADIUS
  servers … a wired switch doing port-based authentication"* (its own docstring)
  — is the RADIUS-server registry that `port_security`'s 802.1X / MAB policy
  depends on. Without it the archetype would compose 802.1X port-security with
  nowhere to point its authenticator. Servers are held by logical **name**; the
  access policy references them by name (the `WifiBss` precedent), and
  address/port/secret resolution stays driver-side. Models reuse
  `models/radius.py` (`RadiusServerConfig`) — no new model. **Cross-vendor: every
  reviewed access family exposes RADIUS-server configuration through its
  management plane (6/6).**

- **The strict-superset spine** — the L3 reuse map (`RoutedInterfaces` reshaping
  `ApplianceVlans`' SVI/DHCP fields, `static_routes` / `bgp` reuse-as-is, the
  `Router` RIB carve-out, `DhcpMode` reuse) belongs to the **sibling `L3Switch`
  doc** and is only summarised in the tracking-file obligations here, because
  this archetype carries no L3 layer.

## New capabilities

Each capability below is intent-level: it describes *what a switch can be asked
to do*, not how any product's API spells it. Models live in `models/switch.py`
(new). The cross-vendor concept check for each is the `K/6` figure from the
matrix; per-method shortfalls are driver-side unsupported-capability errors, not
contract changes.

### `switch_ports: SwitchPorts` — NEW (6/6)
The first-class object of a switch. Per-port `mode` (access/trunk), native VLAN
(PVID), allowed-VLAN list, `enabled`, description, voice VLAN, and isolation.
Read via a port listing; configured per port (whole-port-object replace where a
product is list-replace-only). No existing protocol models a switchport —
`vlan_client` is host-NIC-shaped. **Concept check 6/6** (every reviewed family
exposes per-port mode + VLAN membership through its management plane).

### `switch_vlans: SwitchVlans` — NEW (6/6 present; ◐ on one family)
Per-VLAN id/name registry — the L2 membership target, modeled as a normalized
VLAN table. Distinct from the appliance's `ApplianceVlans` (which is SVI + DHCP,
reused only at L3). **Concept check 6/6 present**, but one family (the
design-target, MS225) treats VLANs as *implicit / controller objects* with no
first-class CRUD (◐). A product
without VLAN create/delete raises unsupported-capability on those methods while
still satisfying the read / membership view — the cross-vendor data confirms
naming and enumeration are always reachable even where CRUD is not.

### `spanning_tree: SpanningTree` — NEW (6/6)
Global STP mode + bridge priority, and per-port guard / edge / path-cost /
priority. Genuinely cross-substrate: the STP vocabulary is **shared with the
future `L2Bridge`** (see §"The `L2Bridge` question") and is therefore authored
in commons. RSTP is universal; MSTP is present on most families but absent on
the cloud-thin / RSTP-only ones, so `MSTP` is a normalized enum member that
raises unsupported-capability where absent. **Concept check 6/6** (RSTP
universal across the reviewed set).

### `link_aggregation: LinkAggregation` — NEW (6/6)
LAG group CRUD by member ports + `mode` (LACP / STATIC). LACP is universal; the
static-vs-LACP toggle is not separable on every product, so `AggregationMode` is
a normalized enum that the plugin maps. **Concept check 6/6.**

### `port_poe: PortPoe` — NEW (6/6)
Per-port PoE enable plus a read of live draw and status; priority / budget where
exposed. PoE has **no home in `L2Bridge`** — it is switch-native. Two reviewed
families lack a per-port PoE-priority knob, so that field raises
unsupported-capability there while enable + draw/status read remain universal.
**Concept check 6/6.**

### `port_security: PortSecurity` — NEW (6/6)
Per-port access-policy reference plus MAC allow / sticky / limit controls
(802.1X / MAB everywhere, MAC-limit / sticky everywhere). Its `firewall_zones` /
`packet_filter` cousins are gateway/host-shaped and are not reused; the RADIUS
backend the 802.1X / MAB policy points at is the composed `radius: RadiusClient`
registry (servers referenced **by name**, the `WifiBss` precedent — see §Reuse
notes), not server addresses inlined here. **Concept check 6/6.**

### `first_hop_security: FirstHopSecurity` — NEW (6/6 present)
Switch-native L2 first-hop security — **DHCP snooping** (block rogue DHCP
servers) and **Dynamic ARP Inspection** (block ARP spoofing) — the two controls
that keep an access edge honest. Distinct from `port_security` (802.1X / MAC
limits) and `switch_acl` (port/VLAN ACLs). Intent-level methods: DHCP-snooping
enable per scope (`FhsScope{GLOBAL,PER_VLAN}`), per-port trust
(`FhsTrustState{TRUSTED,UNTRUSTED}`), an optional rate-limit, and a binding-table
read; DAI enable per scope, per-port ARP trust, an optional rate-limit, and a
`BindingSource{DYNAMIC_SNOOPING,STATIC}` selector. Rogue-DHCP control is modeled
as the DHCP-snooping *intent* so divergent vendor shapes normalize onto one
surface — Meraki DHCP Guard / RA Guard (server allow/block), UniFi DHCP Guarding,
IOS / Junos / EOS port-trust snooping, and Aruba / Omada IMPB all map in.
**Concept check 6/6 present** (DHCP snooping 6/6; DAI 5/6 — UniFi has no DAI),
established by a dedicated cross-vendor concept-check (2026-06-14). The
design-target (MS225) exposes both via Dashboard **and** Dashboard API (DAI
switch-wide + per-port trusted; rogue-DHCP via DHCP Server Policy), so this is a
**baseline** capability, not a deferral. Granularity gaps are driver-side
unsupported-capability errors: MS225 has no per-port snooping trust / rate-limit
/ binding-table read and DAI is switch-wide (not per-VLAN); UniFi raises it
across the whole DAI surface. **IP Source Guard** (5/6 hardware, absent/uncertain
on the cloud targets) is **not** in the baseline shape — a deferred optional
extension (see §"Tracking-file entries").

### `storm_control: StormControl` — NEW (6/6; MS225 corrected 2026-06-15)
Per-port enable plus broadcast / multicast / unknown-unicast suppression
thresholds. **Concept check 6/6.** The pre-implementation review recorded the
design-target (MS225) as controller-UI-only with no API endpoint (a 5/6
"platform-capable" framing). A **live read/write check against real MS225 and
MS355 hardware (2026-06-15) corrected this**: storm control **is** exposed via
the Dashboard API at *network* scope (`getNetworkSwitchStormControl` /
`updateNetworkSwitchStormControl`, the three broadcast/multicast/unknown-unicast
percentage thresholds), so the count is **6/6** and there is no MS225 shortfall
to surface as unsupported-capability. The one divergence from the per-*port*
contract shape is that Meraki applies the thresholds **network-wide** — a
plugin-side mapping concern, not a contract leak. (One other family normalizes to
rate/ratio rather than discrete per-type thresholds — likewise plugin-side.)

### `discovery: Discovery` — NEW, read-only (6/6 LLDP)
Per-port link-layer neighbour read. **Concept check 6/6** for LLDP (the open
IEEE 802.1AB standard, universal). The only normalized `DiscoveryProtocol`
member is `LLDP`; a vendor-proprietary discovery protocol is **not** a contract
enum member — a driver for a family that also runs its own proprietary discovery
maps that neighbour data onto the same LLDP-shaped read, so the vendor term
stays in the plugin and the matrix, not the package. Read-only — a single
neighbour per port on the thinnest families.

### `mac_table: MacTable` — NEW, read-only (5/6)
FDB read (MAC / port / VLAN). **Concept check 5/6** — present on every reviewed
family except the design-target (MS225 exposes no FDB / MAC-address-table read
endpoint; port status returns connected-client and LLDP/CDP info, not the L2
forwarding table). The *concept* clears the bar, so it is in the baseline and the
MS225 gap is a per-method unsupported-capability error. A `MacTableWhiteBox`
raw-dump extension is a `LEVELS.md` candidate (see below).

### `port_status: PortStatus` — NEW, read-only (6/6)
Per-port link state, speed/duplex, and counters (errors / discards / usage).
Replaces the host-shaped `ip_interface` read for this archetype — the same move
the appliance made when it replaced `ip addr` with `appliance_uplinks` (a
port-table read instead of per-NIC introspection). **Concept check 6/6.**

### `switch_qos: SwitchQos` — NEW (6/6)
A QoS rule list (classification by VLAN / protocol / port) plus a DSCP→CoS map
and a trust mode. **Concept check 6/6** for classification + DSCP/CoS. One family
limits scheduler control (◐), so the capability normalizes to rules + trust/map;
explicit queue-scheduler / per-port-rate-limit tuning is **not** modeled now
(deferred — surfaces unevenly and no test drives it).

*Classifier typing:* `QosRule.classifier` (`QosClassifier | None`: VLAN, protocol,
source and destination ports; beside the deprecated `match` text) types the
classification; free text stays legal and has no classifier. See
`precise-types-design.md` ("Switch QoS classifier").

### `ntp: NtpConfig` — NEW (5/6)
NTP-server configuration — `set_ntp_servers` / `get_ntp_servers` over a small
`NtpServer(host, prefer)` model (whole-list replace), the time-sync sibling of
`syslog`. Small and generic — any networked device can sync time — but it clears
the cross-vendor bar on switches: every reviewed family except the design-target
exposes it. **Concept check 5/6** — Aruba 1960, Catalyst 9200L, Juniper EX2300,
Omada (✓) and UniFi (◐ controller-level) expose NTP-server config; the
design-target (MS225) manages time via the Meraki cloud (timezone-only, **no
custom NTP-server config**), so a driver raises unsupported-capability there. New
model `NtpServer` lives in `models/switch.py`; no new enum. (`ntp_client.py`
already exists but is the *operational* surface — get/set/sync time — a different
shape; `NtpConfig` is server-list config, like `SyslogConfig`.)

## Normalized vocabulary

All new vocabularies are `StrEnum` authored from day one (per the legacy-`str` →
`StrEnum` `GAPS.md` rule). Most live in `models/switch.py`; the four shared with
the future CPE-side `L2Bridge` (`StpMode`, `StpGuard`, `StpPortState`, and the
`MacTableEntry` record) live in the neutral `models/l2_common.py` so both
archetypes can import them (see §"The `L2Bridge` question" → Module placement).
The **vocabulary lives in
`testprotocols`; the vendor⇄normalized mapping entries live in the testbed
plugin** — `testprotocols` neither imports nor knows the mapping. Records are
plain `@dataclass`es composing these enums; **no `native` bucket**, no
vendor-tagged ids. Where a vocabulary is a standardized protocol set (IEEE STP
modes, PoE status), it is **seeded in full** up front (the BGP-FSM precedent —
which seeds only standardized vocabularies); where it
is an open vendor taxonomy, it grows by adding members **on test evidence**.

**L2 value vocabularies (`models/switch.py`, except the shared STP/FDB set noted
above which lives in `models/l2_common.py`):**

- `PortMode(StrEnum)`: `ACCESS`, `TRUNK`, `ROUTED` — `ROUTED` appears only at
  L3; access/trunk universal. Vendor taxonomy — grows on evidence (e.g. `STACK`,
  `SVL`).
- `PortAdminState(StrEnum)`: `ENABLED`, `DISABLED`.
- `LinkState(StrEnum)`: `UP`, `DOWN`, `DISABLED` — reuses the `UplinkState`
  normalization principle (don't collapse a degraded/disabled link into `UP`).
- `Duplex(StrEnum)`: `FULL`, `HALF`, `AUTO`.
- **`LinkSpeed` is an int Mbps field, not an enum** — an open numeric domain, per
  the "don't enum an open set" principle.
- `StpMode(StrEnum)`: `STP`, `RSTP`, `MSTP`, `UNKNOWN` catch-all — the
  **IEEE** spanning-tree set (802.1D / 802.1w / 802.1s), seeded in full because
  it is a standardized vocabulary. Vendor-proprietary per-VLAN STP variants are
  **not** members: a driver for a family that runs per-VLAN STP normalizes it
  onto `RSTP` / `MSTP`, or raises unsupported-capability for the per-VLAN
  distinction. If a test ever genuinely needs to distinguish per-VLAN STP, a
  **neutral** member is added on that evidence — never a vendor brand name.
  RSTP-only vendors raise unsupported-capability on `MSTP`.
- `StpGuard(StrEnum)`: `NONE`, `ROOT`, `BPDU`, `LOOP` — the plugin normalizes
  vendor terms (e.g. a `bpdu-block` / `no-root-port` family) onto these.
- `StpPortState(StrEnum)`: `FORWARDING`, `BLOCKING`, `LEARNING`, `LISTENING`,
  `DISABLED` — **shared with the future `L2Bridge` STP/FDB read.**
- `AggregationMode(StrEnum)`: `LACP`, `STATIC`.
- `PoeStatus(StrEnum)`: `DELIVERING`, `DISABLED`, `FAULT`, `SEARCHING`, `OFF`.
- `PoePriority(StrEnum)`: `CRITICAL`, `HIGH`, `LOW` — unsupported-capability on
  families lacking a per-port priority knob.
- `AccessPolicyType(StrEnum)`: `OPEN`, `MAC_ALLOW_LIST`, `STICKY_MAC`, `DOT1X`.
- `AclDirection(StrEnum)`: `INGRESS`, `EGRESS`. The ACL **action** reuses
  `RuleAction{ALLOW,DENY}` and the protocol field reuses `RuleProtocol` (both
  from `models/sdwan_appliance.py`) rather than duplicating. The match itself is
  carried by the new `SwitchAclRule` record (see §Reuse notes): optional L2
  fields (`src_mac` / `dst_mac` / `vlan`) plus the optional IP 5-tuple — these
  are genuinely new fields, not present on the reused `L3Rule`.
- `DiscoveryProtocol(StrEnum)`: `LLDP` only. LLDP is the one open
  (IEEE 802.1AB) link-layer discovery standard, so it is the only normalized
  member. A vendor-proprietary discovery protocol (e.g. a Cisco family's own
  discovery) is **not** an enum member — its driver maps the proprietary
  neighbour data onto the same LLDP-shaped read, and the vendor term lives only
  in the plugin mapping and the cross-vendor matrix, never in the contract.
- `StormControlType(StrEnum)`: `BROADCAST`, `MULTICAST`, `UNKNOWN_UNICAST`.
- `QosTrustMode(StrEnum)`: `DSCP`, `COS`, `UNTRUSTED`.
- `FhsTrustState(StrEnum)`: `TRUSTED`, `UNTRUSTED` — per-port DHCP-snooping / ARP
  trust (first-hop security).
- `FhsScope(StrEnum)`: `GLOBAL`, `PER_VLAN` — a driver that only supports a
  switch-wide toggle (e.g. MS225 DAI) maps `PER_VLAN` → `GLOBAL` or raises
  unsupported-capability.
- `BindingSource(StrEnum)`: `DYNAMIC_SNOOPING`, `STATIC` — what DAI validates
  against; some platforms (e.g. EOS on certain hardware) validate against static
  bindings rather than a dynamically-snooped table.

**Unsupported-capability exceptions surfaced by the cross-vendor data
(driver-side, not contract leaks):** the design-target (MS225) raises
unsupported-capability for `MacTable` / FDB read
(no endpoint) and `SwitchVlans` create/delete (VLANs implicit); for `FirstHopSecurity` it raises
on per-port DHCP-snooping trust / rate-limit / binding-table read (rogue-DHCP is
MAC allow/block) and DAI is switch-wide, not per-VLAN — and UniFi raises it across
the whole DAI surface; for `NtpConfig` MS225 raises it (Meraki-cloud time,
timezone-only). Families without a per-port PoE-priority
knob raise it on `PoePriority`. Families with no public/automatable API at all
(noted in the matrix) are recorded as effectively unsupported for programmatic
config — recorded, **not** modeled away.

## Cross-vendor neutrality

Every capability is a concept the **reviewed access-switch families expose
through their management plane** — none is specific to one product. Endpoint and
feature *names* differ across products; the Protocol is intent-level, so the
differences live entirely in driver translation. Vendor terms appear **only
here**, for the concept check, and never in the package source. The
design-target (Cisco Meraki MS225) is the first column; it is the concrete driver
target, not a privileged shape.

`✓` full · `◐` partial / divergent · `✗` absent.

| Capability        | Meraki MS225            | Aruba Instant On 1960   | UniFi Pro 48        | Catalyst 9200L        | Juniper EX2300            | TP-Link Omada SG3452P | Arista CCS-720D²        |
| ----------------- | :---------------------: | :---------------------: | :-----------------: | :-------------------: | :-----------------------: | :-------------------: | :---------------------: |
| `SwitchPorts`     | ✓ (per-port port object) | ✓ (port VLAN membership) | ✓ (port profile)    | ✓ (switchport)        | ✓ (ethernet-switching)    | ✓ (Port Config)       | ✓ (switchport mode/trunk) |
| `SwitchVlans`     | ◐ (implicit + profiles) | ✓ (VLAN Wizard)          | ✓ (Virtual Networks) | ✓ (802.1Q)            | ✓ (`[vlans]`)             | ✓ (802.1Q)            | ✓ (vlan/name DB)        |
| `SpanningTree`    | ◐ (RSTP only)           | ◐ (MSTP local-web only)  | ◐ (RSTP, no MSTP)   | ✓ (MSTP/RSTP/PVST)    | ✓ (RSTP/MSTP)             | ✓ (STP/RSTP/MSTP)     | ✓ (rapid-pvst/mstp/rstp + full guards) |
| `LinkAggregation` | ✓ (LAG object)          | ✓ (LACP/static)          | ✓ (LACP)            | ✓ (EtherChannel)      | ✓ (`ae`/LACP)             | ✓ (LACP/static)       | ✓ (Port-Channel LACP/static; MLAG layered) |
| `PortPoe`         | ✓ (poe-enabled)         | ✓ (PoE priority/sched)   | ✓ (PoE++)           | ✓ (power inline)      | ✓ (`[poe]`)               | ✓ (PoE+ priority)     | ✓ (802.3bt + Dynamic PoE priority) |
| `PortSecurity`    | ✓ (access policy/sticky) | ✓ (802.1X/port-sec)      | ✓ (802.1X/MAC)      | ✓ (port-security/dot1x) | ✓ (dot1x/sticky)         | ✓ (port-sec/802.1X)   | ✓ (port-security max/sticky; 802.1X/MAB; MACsec) |
| `RadiusClient` (AAA) | ✓ (access-policy RADIUS) | ✓ (RADIUS servers)   | ✓ (RADIUS profiles) | ✓ (radius-server host) | ✓ (access radius)        | ✓ (RADIUS profile)    | ✓ (radius-server / aaa group) |
| `FirstHopSecurity` | ✓ (DHCP Guard/RA Guard + DAI) | ✓ (snoop + ARP-protect + IPSG) | ◐ (DHCP Guarding; no DAI) | ✓ (snoop + DAI + IPSG) | ✓ (dhcp-security tree) | ✓ (IMPB + snoop + ARP-insp) | ◐ (snoop full; DAI static-binding) |
| `StormControl`    | ◐ (network-wide API; corrected 2026-06-15) | ✓ (global storm ctrl)    | ✓ (storm + rate-limit) | ✓ (storm-control)   | ✓ (storm-control profiles) | ✓ (storm control)    | ✓ (per-iface bcast/mcast/unknown-ucast) |
| `SwitchAcl` (L2)  | ◐ (combined, full-replace) | ✓ (MAC+IP ACL)        | ✓ (MAC ACL/isolation) | ✓ (MAC/port ACL)    | ✓ (eth-switching filter)  | ✓ (MAC ACL)           | ✓ (MAC + IP ACLs, one engine) |
| `Discovery`       | ✓ (LLDP+CDP)            | ◐ (LLDP only)            | ◐ (LLDP only)       | ✓ (LLDP+CDP)          | ◐ (LLDP only)             | ◐ (LLDP only)         | ✓ (LLDP+CDP)            |
| `MacTable`        | ✗ (no FDB API)          | ✓ (FDB GUI)              | ✓ (controller FDB)  | ✓ (mac addr-table)    | ✓ (eth-switching table)   | ✓ (FDB table)         | ✓ (show mac address-table) |
| `PortStatus`      | ✓ (ports statuses)      | ✓ (GUI/SNMP)             | ✓ (port_table)      | ✓ (show interfaces)   | ✓ (show interfaces RPC)   | ✓ (port stats)        | ✓ (show interfaces + telemetry) |
| `SwitchQos`       | ✓ (QoS rules + DSCP/CoS) | ✓ (CoS/DSCP, SP/WRR)    | ◐ (DSCP, limited sched) | ✓ (MQC)            | ✓ (Junos CoS)             | ✓ (8-queue QoS)       | ✓ (CoS/DSCP trust + SP/WRR/DWRR) |
| `SyslogConfig`    | ✓ (syslog servers)      | ✓ (remote syslog)        | ◐ (controller-level) | ✓ (logging host)      | ✓ (`[system syslog]`)     | ✓ (syslog)            | ✓ (logging host)        |
| `NtpConfig`       | ✗ (cloud time; tz only) | ✓ (SNTP/NTP)             | ◐ (controller-level) | ✓ (ntp server)        | ✓ (system ntp)            | ✓ (NTP settings)      | ✓ (ntp server)          |
| *`IgmpSnooping`* (deferred) | ✗ (no API)    | ✓                        | ✓                   | ✓                     | ✓                         | ✓                     | ✓ (per-VLAN snooping + querier) |
| *`PortMirror`* (deferred)   | ◐ (per-port)  | ✓                        | ✓                   | ✓                     | ✓                         | ✓                     | ✓ (SPAN/ERSPAN + sFlow/IPFIX divergent path) |

The reviewed set spans cloud-managed (Meraki, Aruba Instant On, UniFi, Omada),
on-box NETCONF/YANG (Juniper EX2300), dual-plane (Catalyst 9200L), and — as an
additional verification point — full-NOS / CloudVision-managed (Arista
CCS-720D²) access families — named here only to show the concept is genuinely
shared rather than borrowed from one product. The vendor terms in parentheses are each product's
spelling of the same intent; they live only in the per-driver mapping. A
capability that did not clear the strong-majority concept bar across the
reviewed families would not have entered the baseline.

Two rows below the rule are **deferred** (see §"Tracking-file entries"):
`IgmpSnooping` (concept clears 5–6/6 but the design-target has no API config and
no test drives it) and `PortMirror` (concept is 6/6 present but straddles the
traffic-controller / pcap boundary).

² Seventh column added by the v2 review below as an **additional cross-vendor
verification point**, not a re-count: the `K/6` concept bars stay the primary
measure against the original six families, and Arista is presented as a
confirming check. `✓` / `◐` / `✗` carry the same meaning as the other columns;
per-method divergences are handled via the unsupported-capability convention and
listed in the v2 subsection.

### Cross-vendor neutrality v2 (2026-06-14 — Arista EOS verification)

A seventh access family — the **Arista CCS-720D Series (campus access switch,
running full Arista EOS, managed via CloudVision state-streaming telemetry, the
eAPI JSON-RPC plane, NETCONF/OpenConfig, and CLI)** — was reviewed against the
proposed protocol set as an additional cross-vendor verification point. The
original `K/6` concept bars against the first six families remain the primary
measure; Arista is the confirming column, exactly as the appliance doc kept its
original counts and footnoted its fifth family. **No protocol, model, or enum was
invalidated, and no capability's mandatory/optional/deferred status changes on
this evidence.** What HELD:

- **The full L2 capability set is present and first-class.** Every proposed
  protocol — `SwitchPorts`, `SwitchVlans`, `SpanningTree`, `LinkAggregation`,
  `PortPoe`, `PortSecurity`, `RadiusClient`, `StormControl`, `SwitchAcl`, `Discovery`,
  `MacTable`, `PortStatus`, `SwitchQos`, `SyslogConfig`, `NtpConfig` — maps to a published EOS
  management-plane surface (CLI/eAPI/NETCONF/OpenConfig). Notably, the
  capabilities the design-target (MS225) cannot exercise — `MacTable`/FDB read
  and `SwitchVlans` create/delete — are **all fully present
  on Arista**, so the verification strengthens the case that those concepts are
  genuinely switch-native (the MS225 shortfalls stay driver-side
  unsupported-capability errors, not contract changes). `Discovery` reinforces the
  `LLDP`-only normalization: Arista EOS supports **both LLDP and CDP** (`cdp run`),
  but a driver maps its CDP neighbour data onto the same LLDP-shaped read, so the
  single `DiscoveryProtocol.LLDP` member still fits without addition.
- **The `SwitchAcl` one-engine decision is confirmed.** EOS uses one ACL engine
  matching both MAC (src/dst) and IP/L4 fields, bound per-interface/VLAN by
  direction — exactly the unified-`SwitchAcl` + `AclDirection` shape, reusing
  `RuleAction` / `RuleProtocol`.
- **The host-substrate exclusions hold.** EOS is a routed/managed network OS, not
  a Linux host you model via `conntrack` / `pcap` / `ip_interface` / `nat` /
  `packet_filter` / `firewall_zones` / `wan_link_admin`; none of the excluded
  levers is the right shape, and `PortStatus` (not `ip_interface`) is the port
  read.
- **Incremental config confirms the contract is not whole-replace-bound.** Unlike
  a controller-only cloud switch, EOS supports targeted per-object updates and
  transactional candidate/commit batches natively (eAPI command lists, NETCONF,
  configuration sessions), so the intent-level per-object protocols translate
  directly — see the divergence note on whole-config below.

Arista-specific shapes, handled via driver translation / the
unsupported-capability convention (named here and in the matrix **only**, never
in a proposed protocol/model/enum name):

- **Multi-chassis LAG.** Beyond plain single-switch LACP/static Port-Channel, the
  720D can dual-home a downstream device to two peer switches presenting one
  logical bundle. From the downstream link's perspective this still satisfies a
  `LinkAggregation` intent (member ports + `AggregationMode{LACP,STATIC}`); the
  multi-chassis pairing (peer-link + domain) is a distinct topology concept
  layered on top. A driver maps the member-port + mode LAG intent onto either a
  plain Port-Channel or the multi-chassis variant per topology. **Decision: do
  NOT add a multi-chassis `AggregationMode` member** — the existing
  `{LACP,STATIC}` suffices for the link-level aggregation intent, and the
  multi-chassis nature is better modeled (if/when a test drives it) as a separate
  redundancy/topology attribute than as a new mode. Kept as a driver-side topology
  mapping.
- **First-hop redundancy with an all-active variant (an L3-layer concern,
  recorded here for the family).** Alongside VRRPv2/VRRPv3 (active-standby), EOS
  offers an active-active virtual-ARP scheme where every switch answers the same
  virtual IP / virtual MAC simultaneously, with no single elected master. This is
  an `L3Switch` gateway-redundancy concern, not an L2 one — the L2 design proper
  defines **no** gateway-redundancy vocabulary, so nothing changes here. It is
  noted for the sibling `L3Switch` doc: a `RedundancyRole` vocabulary, **if/when
  authored there**, should be able to express an `ACTIVE_ACTIVE` (all-active)
  role distinct from the VRRP `MASTER`/`BACKUP` roles, because collapsing the
  all-active scheme into `MASTER`/`BACKUP` loses information. Conservative: add
  only when a `GatewayRedundancy` vocabulary is authored.
- **Sampled-flow visibility (deferred-`PortMirror` family).** In addition to
  SPAN/ERSPAN monitor sessions (and tap aggregation), EOS offers sampled-flow and
  IPFIX/flow-tracking visibility — a divergent visibility path. A sampled-flow
  intent maps to the flow mechanism; a full-copy mirror intent maps to a monitor
  session; the driver picks per the visibility intent. This sits entirely within
  the already-deferred `PortMirror` boundary (it straddles the
  traffic-controller / pcap line) — no new contract surface.
- **Whole-config vs incremental.** EOS is **not** whole-config-replace-only; it
  supports incremental config (eAPI CLI command lists, NETCONF/OpenConfig) and
  transactional candidate/commit sessions, plus state-streamed telemetry. The
  whole-port-object-replace fallback noted on `SwitchPorts` is for
  list-replace-only products; on EOS a driver can do targeted per-object updates,
  so the intent-level protocols translate without the fallback.

A separate `FirstHopSecurity` concept-check (DHCP snooping + DAI, 2026-06-14)
added that capability to the L2 baseline (6/6 present) with its own vocabulary;
Arista's DAI behaviour — validating against static `ip source binding` rather than
a dynamically-snooped table on some hardware — is the specific evidence for the
`BindingSource{DYNAMIC_SNOOPING,STATIC}` member. No other normalized vocabulary
gains a member on the Arista evidence proper. The two vocabulary
candidates raised by the review — an `ACTIVE_ACTIVE` `RedundancyRole` and a
multi-chassis `AggregationMode` — are both declined for the L2 design: the
former belongs to a not-yet-authored `L3Switch` `GatewayRedundancy` vocabulary
(recorded above for that doc), and the latter is rejected outright in favor of a
driver-side topology mapping. The L2 `AggregationMode{LACP,STATIC}`,
`DiscoveryProtocol{LLDP}`, `StpMode`, `StpGuard`, and the rest stand unchanged.

### Data-model neutrality — vocabulary in commons, mappings in the plugin

The same rule the appliance archetype established applies here unchanged:

> **The normalized *vocabulary* lives in `testprotocols`; the
> vendor⇄normalized *mapping entries* live in the testbed plugin.** A driver
> translates on the way in/out of its API; `testprotocols` neither imports nor
> knows the mapping.

Concretely: every value vocabulary is a normalized `StrEnum` in
`models/switch.py` (listed above); the plugin ships the translation table
(e.g. `{StpGuard.ROOT: "<vendor-guard-term>", …}`) and the capability impl maps
normalized→vendor on write and vendor→normalized on read. A vendor lacking a
mapped entry surfaces as a clear unsupported-capability error in the driver — a
coverage gap, **not** a contract leak. Read models carry only normalized fields
(e.g. a `MacTableEntry(mac, port, vlan)`, a `PortStatusEntry(name, link_state,
speed_mbps, duplex, counters)`); if a test needs a vendor-only datum, that is the
signal to add a normalized field on evidence, never to smuggle a dict.

## Excluded host-substrate levers (explicit)

Mirroring the SD-WAN appliance exclusion: a managed switch is API/controller-
managed, not a Linux host. None of the following is on `L2Switch`.

| Excluded lever                              | File                 | Why excluded |
| ------------------------------------------- | -------------------- | ------------ |
| `conntrack` (+ `*WhiteBox`)                 | `conntrack.py`       | Stateful-host/firewall connection table; a switch is not a flow tracker — stateless bridges should not compose this. |
| `pcap` (`PcapCapture`)                       | `pcap_capture.py`    | `tcpdump`/`tshark` on the box shell; packet capture is the `TrafficControllerDevice`'s job (`SPLITS.md` netem precedent). |
| `ip_interface` (`IpInterface`)              | `ip_interface.py`    | Host `ip addr/link/mtu/mac` per-NIC admin; replaced by `PortStatus` read (and SVI config at L3), exactly as the appliance replaced it with `appliance_uplinks`. |
| `nat` (host iptables `Nat`)                 | `nat.py`             | iptables SNAT/DNAT primitives; a switch is not a NAT box. |
| `packet_filter` (+ `*WhiteBox`)             | `packet_filter.py`   | netfilter INPUT/OUTPUT/FORWARD chains + kernel dumps; switch ACLs are port/VLAN-bound, not host chains. |
| `firewall_zones`                            | `firewall_zones.py`  | OpenWrt/firewalld zone + masquerade model; not a switch ACL surface. |
| `wan_link_admin` (`WanLinkAdmin`)           | `wan_link_admin.py`  | Forced link up/down is a host-substrate lever; a switch *reads* port state. Port enable/disable is intent on `SwitchPorts` (`PortAdminState`), not a forced-link lever. |

No `*WhiteBox` extension is added for the L2 capabilities now except the
`MacTableWhiteBox` candidate recorded in `LEVELS.md` (below) — no other
switch-only deep-introspection surface has been identified; one would be added on
signal per `LEVELS.md`.

## The `L2Bridge` question

**Resolution: the switch archetypes do NOT realize the deferred `L2Bridge`
`GAPS.md` entry.** They define switch-native capabilities (`SwitchPorts`,
`SpanningTree`, `LinkAggregation`, `PortPoe`, `MacTable`) distinct from the
Linux-bridge-shaped `L2Bridge`. The justification, grounded in the architecture
rules:

1. The `L2Bridge` 2026-05-02 entry is explicitly **Linux-bridge-shaped**
   (`brctl`, `ip link`, `nft table bridge`, `bridge fdb show`,
   `br-lan`-is-both-a-bridge-and-an-interface) and its trigger is the **CPE
   example**, not a switch. Reusing a substrate-shaped contract on a different
   device class is exactly the mistake the appliance archetype rejected for the
   four host levers.
2. A managed switch's first-class object is the **switchport**
   (access/trunk/PVID/allowed-list/LAG/PoE), not "add port to bridge." Link
   aggregation and PoE have **no home in `L2Bridge` at all** — forcing them in
   would under-specify the switch.
3. **But the cross-vendor check cuts both ways:** STP/RSTP/MSTP modes, port
   guards / edge / path-cost / priority, and the FDB read **are** shared between
   a Linux bridge and a hardware switch. Those shared normalized vocabularies
   (`StpMode`, `StpGuard`, `StpPortState`, and the `MacTableEntry` fields) are
   therefore **authored in a neutral commons module** (`models/l2_common.py`,
   imported by `models/switch.py`) so the eventual `L2Bridge` seeding (CPE
   consumer) reuses them rather than re-inventing divergent enums — see "Module
   placement" below.

This keeps the two from silently diverging: the switch owns the switch-native
shape; the future CPE-side `L2Bridge` owns the bridge-native shape; the shared
STP/FDB vocabulary is owned once, in commons.

**Module placement.** Because the future CPE-side `L2Bridge` (`GAPS.md` ties
`L2Bridge` to the `CpeDevice` archetype — `cpe.py` has no `l2_bridge` attribute
yet) must import this shared vocabulary without depending on a switch-specific
module, the shared enums (`StpMode`, `StpGuard`, `StpPortState`, `MacTableEntry`)
should live in a **neutral commons module** — e.g. `models/l2_common.py` — rather
than being buried in `models/switch.py`; `models/switch.py` then imports them for
the switch-only vocabularies. (This doc refers to them as authored "in commons"
throughout; `l2_common.py` is the concrete neutral home so neither `switch.py`
nor `cpe.py` has to depend on the other.)

## Tracking-file entries

**`GAPS.md` (net-new, deferred):**

- **`IgmpSnooping` [HIGH]** — concept clears the 5–6/6 cross-vendor bar, but the
  design-target (MS225) has **no API config** (snooping runs by default, toggled
  in UI only) and no switch BDD test drives it yet. *Trigger:* the first switch
  scenario asserting multicast group containment. *Design notes:* a snooping
  vocabulary (enable / querier / group-membership) would be seeded when
  `IgmpSnooping` is picked up — `models/multicast.py` currently holds only the
  IGMPv3 record-type codes (`MulticastGroupRecordType`, RFC 3376) and the
  `McastSource` / `McastGroup` aliases, **not** a snooping vocabulary; cross-reference
  `MulticastRouting`.
- **`PortMirror` [MEDIUM]** — the SPAN-session concept is 6/6 present, but it
  **straddles the `TrafficControllerDevice` / pcap boundary** (`SPLITS.md`:
  capture is the traffic device's job; the design-target exposes only per-port
  mirror, no multi-source SPAN object). *Trigger:* a test needing switch-side
  mirror config distinct from host pcap. Record the boundary explicitly.
- **`MulticastRouting` [MEDIUM]** — (L3-layer concern, recorded here for the
  family) PIM-SM + RP clears 4/6 but has high surface area and no driving test;
  reuse `RouteEntry` / multicast vocab when seeded. Carried in full by the
  `L3Switch` doc.
- **`SwitchStacks` / stack-scoped config [LOW]** — most reviewed families expose
  physical stacking and stack-level state; no current test. Defer.
- **`IpSourceGuard` (`FirstHopSecurity` optional extension) [LOW]** — IP Source
  Guard is present on 5/6 reviewed hardware families (Aruba 1960, Catalyst 9200L,
  Juniper EX2300, Omada, Arista) but absent/uncertain on the cloud targets
  (Meraki MS225, UniFi), so it is **kept out of the baseline `FirstHopSecurity`
  shape**. *Trigger:* a test asserting source-IP filtering against the
  DHCP-snooping binding table. *Design notes:* add as an optional
  `FirstHopSecurity` method (or a sibling) reusing the binding-table model;
  drivers lacking it raise unsupported-capability.
- **`L2Bridge` HIGH entry [UPDATE — mandatory]** — the existing 2026-05-02
  `L2Bridge` entry must be updated to (a) cross-reference this switch design and
  record the **realize-as-switch-native** decision explicitly so the two are not
  silently divergent; (b) point its "Design notes (when picked up)" at the
  shared STP/FDB vocabulary in `models/l2_common.py` (`StpMode`, `StpGuard`,
  `StpPortState`, `MacTableEntry`) so the CPE consumer reuses it without
  depending on `models/switch.py`; and (c) honor
  and extend its existing cross-reference list (`vlan_client.py`,
  `firewall_zones.py`) — coordinate tagged-port semantics with `vlan_client`
  (host side) and note that the switch's `SwitchPorts` / `SwitchVlans` are the
  switch-side analog.

**`SPLITS.md` (granularity changes to existing protocols):**

- **`SwitchAcl` unified L2+L3** — `SwitchAcl` itself is a **net-new** capability
  (its `GAPS.md`/new-capability evidence is the per-port/VLAN filtering concern,
  6/6 concept), so it is not a SPLITS reshape of an existing protocol. The
  SPLITS entry records only the **decision to model one ACL surface** (not
  separate L2/L3 protocols) and the **enum reuse** of `RuleAction` /
  `RuleProtocol`, since the reviewed switches use one ACL engine. The new
  `SwitchAclRule` record (optional MAC/VLAN + optional 5-tuple) lives in
  `models/switch.py`; `L3Rule` is **not** extended. Log Signal / Decision
  (new capability, enum reuse) / Rationale.
- **`Router` RIB carve-out** and **`ApplianceVlans` SVI/DHCP reuse** — these
  reshapes are driven by the **sibling `L3Switch`** doc (carving
  `get_routing_table()` / `RouteEntry` into a read-only `RoutingRead`; sharing
  `VlanConfig`'s SVI + DHCP fields into `RoutedInterfaces` / `InterfaceDhcp` with
  the `appliance_ip → svi_ip` rename). They are noted here only because the L3
  archetype composes this L2 layer; the binding `SPLITS.md` entries live with the
  L3 design.

**`LEVELS.md` (white-box extensions):**

- **`MacTableWhiteBox(MacTable, Protocol)`** — raw FDB dump (the
  `show mac address-table` / `show ethernet-switching table` equivalent) for
  kernel/ASIC-level FDB pinning; analogous to the `L2Bridge` `bridge fdb show`
  WhiteBox note. Black-box impact: base `MacTable` returns normalized entries;
  the raw dump is on the WhiteBox only (LSP rule). Drivers expected to satisfy
  the raw dump: the on-box / structured-RPC families; **not** the design-target
  (no FDB API). For the other L2 capabilities, record "none yet."

## Verification

Protocol-conformance tests per capability; archetype registration +
`runtime_checkable` `isinstance` gate in the device-types test (including the
`L3Switch(L2Switch, Protocol)` strict-superset relationship, verified once the
sibling lands); `mypy --strict`; and a vendor-isolation grep ensuring no product
name or vendor id appears anywhere in the `testprotocols` **package source** (the
contract surface). Product names appear only in design docs like this one, where
they document the cross-vendor concept check — never in a model, enum, or
protocol.

## Verification record (2026-10-24)

The L2 layer was verified against one reference driver per column of the neutrality table
in the maintainers' private reference corpus, at corpus `main` commit
`d4cf5c46ffc431e0a53535f5500b3bf204a48144`. Each driver maps every member of the 18 capabilities `L2Switch`
composes as shipped — the 16 the archetype block lists, plus `placement: PlacementPorts`
and `info: DeviceInfo`; 55 members — onto the family's published machine-readable or
scripted management plane, citing the document and section it follows, or raises
unsupported-capability citing where the absence is documented, or, where the product has
the feature and the published plane does not reach it, where the feature is documented. A
cell is graded by that published plane, never by a web UI. The shape was taken as fixed: nothing in the package
changed, and the findings below are held for the harmonisation review.

**Families and version lines.**

| Column | Family | Management plane and version line |
| --- | --- | --- |
| 1 | Meraki MS225 | Dashboard API v1 (reference v1.75.1); MS firmware line, not contradicted |
| 2 | Aruba Instant On 1960 | no published machine-readable or scripted plane: web GUI only (Management and Configuration Guide, Edition 3.1.0; firmware 3.x line). The table grades this column in web-UI terms ("FDB GUI", "GUI/SNMP", "MSTP local-web only"), and no published plane reaches them; the guide lists an SNMP agent, but the vendor publishes no MIB reference, so SNMP is not a graded plane |
| 3 | UniFi Pro 48 | UniFi Network application Integration API, 9.4 line (reference 9.4.19: fifteen operations, none of them a configuration endpoint); the PoE variant, as the column's `PortPoe` cell (PoE++) names it |
| 4 | Catalyst 9200L | IOS-XE 17.12 CLI over SSH |
| 5 | Juniper EX2300 | Junos OS 23.4 CLI (ELS) over SSH, `configure private` and `commit` |
| 6 | TP-Link Omada SG3452P | Omada Controller Open API reference 6.2.0, the earliest the vendor publishes; which cited endpoints a 5.x controller serves is not established |
| 7 | Arista CCS-720D | EOS 4.33 eAPI (JSON-RPC over HTTPS); the EOS manual read at its current release, 4.36.2F, where the two absences below are read |

**Counts over the 55 members.** Mapped; mapped with a stated gap (a `partial:` line on the
member, or on the capability's implementation as a whole, which counts for each of its
members); unsupported (the product lacks the member, or its classification is unverified:
in parentheses); unsupported, plane reach (the product has the feature — its UI
shows it — and the published plane does not reach it).

| Family | Mapped | Mapped with a stated gap | Unsupported | Unsupported, plane reach | Total |
| --- | --- | --- | --- | --- | --- |
| Meraki MS225 | 35 | 9 | 11 | 0 | 55 |
| Aruba Instant On 1960 | 1 | 0 | 5 (4) | 49 | 55 |
| UniFi Pro 48 | 7 | 1 | 15 (10) | 32 | 55 |
| Catalyst 9200L | 54 | 0 | 1 | 0 | 55 |
| Juniper EX2300 | 53 | 1 | 1 | 0 | 55 |
| TP-Link Omada SG3452P | 48 | 3 | 4 (2) | 0 | 55 |
| Arista CCS-720D | 51 | 2 | 2 | 0 | 55 |
| **All seven** | **249** | **16** | **39 (16)** | **81** | **385** |

Across the seven drivers: 162 `lossy:` lines (a rendering that loses information), 16
`partial:` lines (a gap in a supported member) and 86 `unverified:` lines (a field, reply
shape or classification the cited page does not print), counting a line whose first
token, after an optional comment marker, is the annotation.

**Unsupported cells.**

| Member | Families | Where the absence is documented |
| --- | --- | --- |
| `DeviceInfo.manufacturer` | Meraki MS225, Aruba Instant On 1960, UniFi Pro 48, Catalyst 9200L, Juniper EX2300, TP-Link Omada SG3452P | each plane's device read publishes no manufacturer field; the 1960 guide's device information shows none |
| `SwitchVlans.create_vlan`, `delete_vlan` | Meraki MS225 | VLANs are implicit: no VLAN object is published |
| `PortPoe.set_priority` | Meraki MS225, UniFi Pro 48; TP-Link Omada SG3452P (classification unverified) | no per-port PoE priority field (Dashboard API; datasheet); the Open API carries PoE on and off only, and no published user guide settles the UI |
| `RadiusClient.test_server_reachable` | Meraki MS225, UniFi Pro 48, TP-Link Omada SG3452P, Arista CCS-720D; Aruba Instant On 1960 (classification unverified) | Meraki and Arista publish periodic server testing, not an on-demand test (the access-policy settings; EOS "User Security", `monitor server radius`); no test is published on UniFi and Omada; the 1960 guide shows none and no datasheet was reached |
| `FirstHopSecurity.set_dhcp_snooping_trust` | Meraki MS225, Arista CCS-720D; UniFi Pro 48 (classification unverified) | no per-port snooping trust (Dashboard API: the DHCP server policy); EOS snooping is option-82 insertion with no trust command (EOS "IPv4"); no snooping-trust endpoint (Integration API reference), and whether the application shows one is not published |
| `FirstHopSecurity.get_dhcp_bindings` | Meraki MS225; UniFi Pro 48 (classification unverified) | no binding-table read is published |
| `FirstHopSecurity.set_dai`, `set_arp_trust` | UniFi Pro 48 | no ARP inspection (datasheets: "DHCP Snooping & Guarding" only) |
| `SwitchQos.set_trust_mode` | Meraki MS225; UniFi Pro 48 (classification unverified) | no per-port trust field: DSCP trust is a QoS rule's, and a rule selects by VLAN, protocol and port (Dashboard API); no QoS endpoint (Integration API reference), and whether the application shows a port trust mode is not published |
| `SwitchQos.set_dscp_cos_map` | UniFi Pro 48 (classification unverified) | no endpoint; the QoS article names no switch-wide map |
| `SwitchQos.get_rules`, `set_rules` | Aruba Instant On 1960 (classification unverified) | the guide's QoS rules assign queues through ACL bindings and mark no DSCP or CoS |
| `NtpConfig.set_ntp_servers`, `get_ntp_servers`, `get_sync_state` | Meraki MS225; UniFi Pro 48 (classification unverified) | cloud time: no NTP call or field (Dashboard API); no time endpoint and no article naming a device NTP setting (UniFi) |
| `NtpConfig.get_sync_state` | TP-Link Omada SG3452P (classification unverified) | no NTP status read (the status operation answers an untyped object) |
| `Discovery.get_neighbors`, `MacTable.get_mac_table` | UniFi Pro 48 (classification unverified) | no neighbour or forwarding-table endpoint; the clients read prints no port or VLAN |
| `DeviceInfo.serial_number` | UniFi Pro 48 (classification unverified) | the device reads print no serial number |
| `DeviceInfo.hardware_version` | Aruba Instant On 1960 (classification unverified) | the guide's device information carries no hardware version |

**Unsupported, plane reach.** Aruba Instant On 1960: every member except
`placement.ports` and the five cells above (49), each sourced to the guide's section and
page that shows the feature in the web GUI. UniFi Pro 48: `SwitchPorts` (3), `SwitchVlans`
(3), `SpanningTree` (6), `LinkAggregation` (3), `PortPoe.set_enabled`, `PortSecurity` (2),
the `RadiusClient` registry (5), `FirstHopSecurity.set_dhcp_snooping`, `StormControl` (2),
`SwitchAcl` (2), `SwitchQos.get_rules` and `set_rules`, `SyslogConfig` (2) — 32, each
sourced to the Integration API reference (no endpoint) and the vendor's help article that
shows the feature in the application.

`QosRule.match`, deprecated in 0.13.0, is filled beside `classifier` on every rule read,
and every rule write reads `classifier` first.

**Corrections to the neutrality table.** One rule for every column: a capability cell that
changes, and a member graded ✗ where the design's cell does not already say ✗, is listed;
a member graded ◐ is counted above under "mapped with a stated gap" and listed only where
it lowers a design cell that reads plain ✓ (a cell already ◐ keeps its ◐ members to the
count). A plane-reach ✗ records the published plane's coverage, not the product's: the
family has the member. A classification-unverified ✗ is counted as unsupported with its
classification open: the published material settles neither a product absence nor a UI
feature (16 cells: four in column 2, ten in column 3, two in column 6). The archetype block
above lists 16 capabilities; `L2Switch` composes 18 as shipped (`placement:
PlacementPorts`, `info: DeviceInfo`). All columns but 7: `DeviceInfo.manufacturer` ✗ (no
row). Column 1: `SwitchVlans.create_vlan` and `delete_vlan` ✗ (as the exception paragraph
says); `PortPoe.set_priority` ✗ and `get_status` ◐; `RadiusClient.test_server_reachable`
✗; `FirstHopSecurity.set_dhcp_snooping_trust` and `get_dhcp_bindings` ✗ (as the exception
paragraph says) and `set_dhcp_snooping` ◐ (the DHCP server policy); storm control ◐ → ✓
(the network's thresholds, written with the sharing stated); MAC table ✗ → ✓ with a stated
gap (a job read once, refused until complete); `SwitchQos.set_trust_mode` ✗; syslog ✓ with
a stated gap (the network-scope call is marked deprecated by the family). Column 2: no
published plane reaches the cells the table grades in web-UI terms (above); every cell
becomes ✗, plane reach, except
`DeviceInfo.manufacturer` ✗ and the four classification-unverified cells; the MSTP
per-value refusal does not arise (the whole member is plane reach). Column 3: switch ports,
VLANs, spanning tree, link aggregation, port security, the RADIUS registry, DHCP guarding,
storm control, ACL, QoS rules and syslog ✗, plane reach; PoE ✓ → ◐ (the status read; the
enable plane reach; the priority ✗); the RADIUS test, DAI and ARP trust ✗ (DAI as the cell
says); snooping trust and bindings, discovery, MAC table, QoS trust and map, NTP and the
serial number ✗, classification unverified; port status ✓ stands. Column 4: the capability
cells stand; `PoePriority.CRITICAL` is refused per value (two levels). Column 5: the
capability cells stand; `SwitchQos.set_rules` ◐ (the rules are held unbound: a port's one
input filter belongs to the ACL); `PoePriority.CRITICAL` refused per value. Column 6: graded on
the Open API reference 6.2.0 (above); `SpanningTree.get_mode` and `get_port_state` ◐;
`PortPoe.set_priority` ✗ (classification unverified); `RadiusClient.test_server_reachable`
✗; MAC table ✓ → ◐ (the controller's wired clients, not the forwarding database);
`NtpConfig.get_sync_state` ✗ (classification unverified). Column 7:
`RadiusClient.test_server_reachable` ✗; `FirstHopSecurity.set_dhcp_snooping_trust` ✗
(against the cell's "snoop full").

**Findings for the harmonisation review.** Each changes no shape here.

- `DeviceInfo.manufacturer` is published on one column (Arista CCS-720D), and on two of the seven columns of the L3 table.
- The archetype block lists 16 capabilities; `placement` and `info` were composed after it was written (18 shipped).
- `DeviceInfo`: `hardware_version` is not published (Meraki MS225, UniFi Pro 48), `oui` is derived from the base MAC wherever it is read, and the serial number is not published (UniFi Pro 48, classification unverified).
- `MacTable.get_mac_table` over an asynchronous plane has no pending outcome: the table is a job the driver reads once (Meraki MS225); the controller's wired clients stand in for the forwarding database (TP-Link Omada SG3452P).
- `RadiusClient.test_server_reachable`: periodic server probes, not an on-demand test (Meraki MS225, Arista CCS-720D); the `timeout` parameter has no counterpart in the published test (Catalyst 9200L, Juniper EX2300).
- `RadiusClient` names servers where the plane keys them by access policy (Meraki MS225) or by address (Juniper EX2300, Arista CCS-720D); accounting off on one server (`acct_port=None`) has no per-server form and is refused (Arista CCS-720D); `AccessPolicy` cannot name the policy a port uses (Meraki MS225).
- `PoePriority`: two levels (Catalyst 9200L, Juniper EX2300), four (Arista CCS-720D), no knob (Meraki MS225, UniFi Pro 48; TP-Link Omada SG3452P classification unverified).
- `LinkAggregationGroup.name` is a numbered interface (Catalyst 9200L, Juniper EX2300, Arista CCS-720D) or an id (Meraki MS225, TP-Link Omada SG3452P).
- `SwitchQos` has no attachment: rules, trust and map take effect through interface policies (Catalyst 9200L, Juniper EX2300, Arista CCS-720D), switch-scoped rules (TP-Link Omada SG3452P) or network rules (Meraki MS225).
- `QosRule`: no name field and no CoS mark (Meraki MS225), no CoS mark (Juniper EX2300); `QosClassifier` is all-of where the class map is any-of (Arista CCS-720D).
- `SwitchQos.set_trust_mode`: no per-port trust where DSCP trust is a rule's (Meraki MS225).
- `StormControlConfig`: one level over the types (Juniper EX2300), network-wide thresholds (Meraki MS225); a unit the plane cannot honour is the model's `ValueError`.
- `FirstHopSecurity`: the `DYNAMIC_SNOOPING` default is refused where inspection validates static bindings (Arista CCS-720D); no per-port snooping trust (Meraki MS225, Arista CCS-720D); `PER_VLAN` refused on switch-wide planes (Meraki MS225, TP-Link Omada SG3452P); the docstring does not say what a per-VLAN call without its VLAN is (the drivers raise `ValueError`).
- `SwitchAcl`: the binding is free text, and a VLAN binding with a direction means different things — one network list (Meraki MS225), a VLAN map without direction (Catalyst 9200L), the SVI's list for routed traffic (Arista CCS-720D), no direction field (TP-Link Omada SG3452P).
- `SwitchAclRule`: no comment (Juniper EX2300); MAC and IP matches live in separate lists (Catalyst 9200L, Arista CCS-720D); port lists refused (TP-Link Omada SG3452P).
- `SwitchPort.isolated` is a private-VLAN membership, not a port flag (Juniper EX2300, Arista CCS-720D); port mode follows the allowed VLANs (TP-Link Omada SG3452P); `PortMode.ROUTED` is refused on this layer by the model's docstring though three of these platforms take it.
- `PortSecurity`: no sticky form (Arista CCS-720D); no MAC list, sticky or limit field (TP-Link Omada SG3452P).
- `PortStatusEntry` error and discard counters are `0` where the plane publishes none: no counter on the port read (UniFi Pro 48), no input-discard counter (Catalyst 9200L), error counts only per kind over a time window and no discard kind (Meraki MS225); candidate `int | None`, the twin of the appliance's `loss_percent`.
- `StpMode` has no "off" (Meraki MS225 reads `UNKNOWN`); per-VLAN modes map lossily (Catalyst 9200L, Arista CCS-720D); RSTP only (Meraki MS225), no 802.1D (Arista CCS-720D).
- `NtpConfig.get_sync_state` is published on the on-box planes; Meraki MS225 has no NTP; TP-Link Omada SG3452P and UniFi Pro 48 publish no state (classification unverified); a preferred server is refused (TP-Link Omada SG3452P).
- `SyslogServer` roles are not carried (Catalyst 9200L, Juniper EX2300, Arista CCS-720D); one server only (TP-Link Omada SG3452P); the network call is family-deprecated (Meraki MS225).
- Write scope: network objects (Meraki MS225: 15 members), site objects (TP-Link Omada SG3452P: seven capabilities), and on-box named objects shared between ports (Catalyst 9200L, Juniper EX2300, Arista CCS-720D); each written with the sharing stated, none graded unsupported.

**Migration already announced (0.13.0, removal 2027-04-15).** A consumer pinned below
0.13.0 already faces `QosRule.match` → `classifier` (at removal `match` goes and
`classifier` becomes required). The findings propose that a harmonisation change land
beside this migration, so a consumer migrates once; its deprecation period is set by that
change.

**`GAPS.md` entries.** `PortStatusEntry` error and discard counters: `0` where a family
publishes none (new, low: no counter, no input-discard counter, or windowed counts only, on
one column each); `RadiusClient.test_server_reachable`: a server-status read where a
family publishes periodic probes, not an on-demand test (new, low); the 2026-06-15 per-port RADIUS-server selection
entry gains an update (a port's 802.1X bound to a network access policy on one column).
`DeviceInfo.manufacturer` and the other findings are harmonisation candidates on existing
members and have no entry of their own.
