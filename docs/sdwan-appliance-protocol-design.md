# Design: vendor-neutral SD-WAN **appliance** protocol shape

| Field    | Value                                                                                                          |
| -------- | ------------------------------------------------------------------------------------------------------------- |
| Status   | Implemented                                                                                                   |
| Author   | rjvisser                                                                                                       |
| Date     | 2026-06-11 (updated 2026-06-12: `vpn: SiteToSiteVpn` + L3Firewall VPN rule set)                                |
| Related  | `packages/testprotocols/SPLITS.md` (2026-05-02 netem removal; 2026-05-11 firewall fold; 2026-06-11 sdwan_policy firewall split), `GAPS.md` (2026-06-11 appliance follow-ons; 2026-06-12 static-route + BGP entries), `LEVELS.md`, `devices/sdwan.py`, `models/sdwan_appliance.py`, `models/wan_edge.py`, `site_to_site_vpn.py` |

This document explains why `testprotocols` carries a dedicated **managed
SD-WAN appliance** archetype alongside the existing SD-WAN *router* archetype,
and records the shape that was chosen. It is a clarification of the chosen
implementation as the base starting point for supporting SD-WAN appliances —
not a proposal; the code described here lives in the modules cited above.

## Context and problem statement

The first SD-WAN device archetype in `testprotocols` was `SdwanRouterDevice`,
registered `linux_sdwan_router` (`devices/sdwan.py`). It composes six of a Linux
digital twin's L3 levers: `routing`, `sdwan_policy`, `ip_interface`, `pcap`,
`nat`, `conntrack`. That shape was driven by a docker / FRR / iptables twin —
a *router built from a Linux host* — and is exactly right for that substrate.

A **managed SD-WAN appliance** is a different kind of device. It is not a Linux
host you shell into; it is a closed product driven through a **management API**
(a cloud controller or an on-box REST/CLI plane). Modelling such an appliance
against the Linux-router shape is **both over- and under-specified**:

**Over-specified — four host-substrate levers a managed appliance cannot satisfy.**
A driver for an API-managed appliance can only stub these:

- `conntrack` — the Linux netfilter connection table. A managed appliance has
  no equivalent API surface; connection state is internal.
- `pcap` (`PcapCapture`) — `start_tcpdump` / `tshark_read_pcap`. This is
  Linux-tool-shaped, and packet capture in this framework is the
  **traffic-controller's** job (a separate device sitting in the path), not the
  device-under-test's.
- `ip_interface` (`IpInterface`) — per-interface `ip addr / link / mtu / mac`.
  An appliance manages **WAN uplinks** and **LAN VLANs** as first-class objects
  and satisfies almost none of the per-`netdev` surface.
- `nat` (`Nat`) — iptables `snat / dnat / 1to1`. An appliance exposes
  **appliance-native** 1:1 / 1:Many / port-forwarding NAT, not iptables chains.

**Under-specified — surfaces an appliance exposes that have no capability protocol.**
Traffic shaping, content filtering, L7 (application-aware) firewalling,
intrusion prevention / anti-malware, syslog configuration, and per-VLAN LAN /
DHCP all sit on every managed appliance and had no home in the contract. Even
the "reusable" L3 capabilities leak host assumptions: the firewall protocols
(`PacketFilter` / `Firewall`) are iptables-**chain**-based, whereas an appliance
L3 firewall is a **flat, ordered policy** (not INPUT / OUTPUT / FORWARD chains);
`DhcpServer` is provisioning-shaped, not per-VLAN appliance DHCP; and
`SdwanPolicyManager` had folded firewall rules into SD-WAN steering.

## Decision

Add a vendor-neutral **`SdwanApplianceDevice`** archetype, **alongside** (not
replacing) `SdwanRouterDevice`. It composes what an API-managed SD-WAN appliance
genuinely exposes, excludes the four host-substrate levers, and adds the missing
capabilities. `linux_sdwan_router` is untouched — the twin keeps
`conntrack` / `pcap` / `ip_interface` / `nat` (and their `*WhiteBox` extensions).
Any vendor's appliance driver can target the new archetype.

This mirrors two existing precedents recorded in `SPLITS.md`:

- **2026-05-02** — netem was removed from the SD-WAN archetype because traffic
  impairment is a separate device's concern (the traffic controller). Same
  principle: a capability that structurally belongs to another device does not
  ride on this one.
- **2026-05-11** — capabilities are bundled by **coherent telco domain**, not by
  whatever a single substrate happens to expose together.

### Evidence convention — why these capabilities are built now

`GAPS.md` is firm that net-new protocols land on **tracked evidence — a test
that needs it, ideally two consumers agreeing on the shape**. Two framings apply
to this archetype, and both point the same way:

- **Foundation baseline.** `testprotocols` is pre-1.0 and deliberately
  establishing a *sound, complete baseline* for the managed-appliance archetype
  — the same way the Wi-Fi capability family was built out ahead of any single
  consumer to anchor a stable shape. A capability that **every reviewed
  appliance exposes** belongs in that baseline; the cross-vendor concept check
  (below) is what keeps it from collapsing into a one-vendor convenience.
- **Per-capability evidence.** Each capability maps to a concrete
  appliance-test concern — path/SLA steering, per-link and per-app shaping,
  L3/L7 filtering, content filtering, intrusion/anti-malware behaviour, uplink
  status, LAN/DHCP validation, syslog export.

Guard against one-vendor shapes: **every capability carries a cross-vendor
concept check** — it must be a concept that *all four* reviewed appliance
families expose through their management plane, not a quirk of one. All
capabilities below cleared that bar and are built now. The follow-ons that did
**not** yet have a driving test (typed path-steering methods, an
individual-application registry) are recorded as deferred in `GAPS.md` rather
than guessed at here.

## The archetype

```python
@runtime_checkable
class SdwanApplianceDevice(BaseDeviceProtocol, Protocol):
    routing: Router                       # reuse — read + static/BGP surface
    sdwan_policy: SdwanPolicyManager      # reuse (reshaped — firewall methods out)
    vpn: SiteToSiteVpn                    # new (2026-06-12 — overlay role/hubs/subnets + peer status)
    traffic_shaping: TrafficShaping       # new
    l3_firewall: L3Firewall               # new
    l7_firewall: L7Firewall               # new
    content_filtering: ContentFiltering   # new
    appliance_nat: ApplianceNat           # new
    security: ThreatPrevention            # new
    uplinks: ApplianceUplinks             # new (replaces ip_interface WAN-read)
    lan: ApplianceVlans                   # new (replaces ip_interface LAN + DhcpServer)
    syslog: SyslogConfig                  # new
    device_management: DeviceManagement   # reuse

register_device_type("sdwan_appliance", SdwanApplianceDevice)
```

Excluded (kept on `linux_sdwan_router`): `conntrack`, `pcap`, `ip_interface`,
`nat`.

## Reshape — `SdwanPolicyManager`

The firewall methods (`apply_firewall_rule` / `remove_firewall_rule` /
`get_firewall_rules`) were removed: firewall is now a separate coherent domain
owned by `L3Firewall` / `L7Firewall`. `SdwanPolicyManager` retains SD-WAN policy,
SLA policy, and application-flow visibility:

```python
class SdwanPolicyManager(Protocol):
    def apply_policy(self, policy: dict[str, Any]) -> None: ...   # generic escape hatch
    def remove_policy(self, name: str) -> None: ...
    def configure_sla_policy(self, policy: SLAPolicy) -> None: ...
    def remove_sla_policy(self, name: str) -> None: ...
    def get_application_flows(self, since_s: int = 60, app_filter: str | None = None) -> list[AppFlow]: ...
```

This split is recorded in `SPLITS.md` (2026-06-11). The twin's
`SdwanRouterDevice` is unaffected at the conformance level — its driver still
*has* the methods, so removing them from the Protocol cannot break it. A typed
path-steering surface (`set_uplink_selection` / `configure_performance_class`)
is deferred in `GAPS.md` because adding *required* methods to a Protocol is not
conformance-safe for existing implementations the way removing them is — it
lands when a test drives the exact shape and the twin can migrate in step.

## New capabilities

Each capability below is intent-level: it describes *what an appliance can be
asked to do*, not how any product's API spells it. Models live in
`models/sdwan_appliance.py` (new) or reuse `models/wan_edge.py`.

### `traffic_shaping: TrafficShaping`
Per-uplink and global per-client bandwidth caps plus an ordered list of shaping
rules (whole-list replace). Reuses `wan_edge.TrafficShapingRule` (match, DSCP
tag, bandwidth limit, priority), covering DSCP marking and per-application
shaping. Cross-vendor: per-link + per-app shaping and DSCP marking exist on
every reviewed appliance.

### `l3_firewall: L3Firewall`
An appliance L3 policy is a **flat ordered list replaced whole**, with separate
outbound and inbound rule sets — deliberately distinct from the chain-based
`PacketFilter`. `L3Rule` carries `policy` (allow/deny), protocol, src/dst CIDR
and ports, a comment, and a per-rule syslog flag. Cross-vendor: all four use
ordered allow/deny rule sets.
As of 2026-06-12 the protocol also carries the site-to-site VPN rule set
(`set_vpn_rules` / `get_vpn_rules`) — same flat-ordered-list contract,
applied to overlay traffic.

### `l7_firewall: L7Firewall`
Application-aware deny rules: `set_rules` / `get_rules` over `L7Rule`
(`match_type` ∈ application / application-category / host / port / IP-range /
URL-pattern, plus a normalized value). Cross-vendor: app-aware firewalling is
universal (app-route + deep inspection, app-control, app-ID).

### `content_filtering: ContentFiltering`
Blocked categories and allow/block URL rules, plus a category listing. Uses the
normalized `ContentCategory` taxonomy. Cross-vendor: URL / category filtering is
universal.

### `appliance_nat: ApplianceNat`
The appliance-native NAT surface — 1:1, 1:Many, and port-forwarding rule sets
(each list-replace), with vendor-neutral models (`OneToOneNatRule`,
`OneToManyNatRule`, `PortForwardRule`). Built now as part of the sound baseline:
1:1 / 1:Many / port-forwarding NAT is present on **all four** reviewed
appliances, so it belongs in the baseline even ahead of a driving test — the
same rationale as the Wi-Fi protocols predating a single consumer.

### `security: ThreatPrevention`
Intrusion (disabled / detection / prevention) and malware (disabled / enabled)
configuration, plus a security-event read. Cross-vendor: IPS + anti-malware/AMP
+ a security-event log are universal. The event read lives here as the
deferred-API augmentation surface; real-time assertions still flow through
`syslog`. Crucially, **IPS signature ids are not modelled** — tests assert
*behaviour* (an attempt was detected/blocked) via `SecurityEvent.action` +
`category`, never "signature N fired."

### `uplinks: ApplianceUplinks`
Read-only WAN uplink status (`get_uplinks` / `get_uplink`). `UplinkStatus`
carries name, normalized `state`, IP, gateway, public IP. Replaces the
`ip_interface` WAN-read for this archetype; WAN *config* is a setter to add on
evidence. Cross-vendor: all expose WAN link state.

### `lan: ApplianceVlans`
Per-VLAN LAN config (`list_vlans` / `get_vlan` / `set_vlan`) and DHCP lease
reads. `VlanConfig` carries subnet, appliance IP, normalized `dhcp_mode`
(server / relay / disabled), lease time, options, reservations, and fixed
assignments. Replaces `ip_interface` LAN + `DhcpServer` for this archetype.
Cross-vendor: LAN VLAN + DHCP config is universal on SD-WAN edges.

### `syslog: SyslogConfig`
Syslog server configuration (`set_syslog_servers` / `get_syslog_servers`).
`SyslogServer` carries host, port, and normalized `roles`. A small,
arguably-generic capability (any networked device can have syslog), scoped to
the appliance archetype but reusable.

### `vpn: SiteToSiteVpn` (added 2026-06-12)
Overlay participation as one whole-replace config object —
`SiteToSiteVpnConfig(role, hubs, subnets)` with `VpnRole{DISABLED,HUB,SPOKE}`,
per-hub `use_default_route`, per-subnet `advertise` — plus a peer-status read
(`VpnPeerStatus` / `VpnPeerState{REACHABLE,UNREACHABLE,UNKNOWN}`). Hubs and
peers are referenced by testbed-level name; the plugin maps name⇄vendor id.
No `MESH` role and no IPsec crypto parameters yet — both grow on evidence.
Cross-vendor: overlay role/topology control and a peer-reachability read are
published-API surfaces on all four reviewed families. The VPN-scoped firewall
rule set deliberately lives on `L3Firewall` (`set_vpn_rules`/`get_vpn_rules`),
keeping firewall one coherent domain.

## Cross-vendor neutrality

Every capability is a concept that **all four reviewed managed-appliance
families — Meraki MX, Catalyst SD-WAN, FortiGate, and Prisma SD-WAN — expose
through their management plane** — none is specific to one product. Endpoint
*names* differ across products; the Protocol is intent-level, so the differences
live entirely in driver translation.

| Capability                     | Meraki MX | Catalyst SD-WAN     | FortiGate        | Prisma SD-WAN   |
| ------------------------------ | :-------: | :-----------------: | :--------------: | :-------------: |
| routing / BGP / static         | ✓         | ✓                   | ✓                | ✓               |
| sdwan_policy (steering, SLA)   | ✓         | ✓ (app-route, SLA)  | ✓ (SD-WAN rules) | ✓ (path policy) |
| vpn (overlay config + peer status) | ✓         | ✓ (topology policy)  | ✓ (IPsec + monitor) | ✓ (vpnlinks)     |
| traffic_shaping (+DSCP)        | ✓         | ✓ (QoS policer)     | ✓                | ✓ (QoS profile) |
| l3_firewall (ordered)          | ✓         | ✓                   | ✓                | ✓               |
| l7_firewall (app-aware)        | ✓         | ✓ (app-route/Snort) | ✓ (app-control)  | ✓ (app-ID)      |
| content_filtering              | ✓         | ✓ (UTD URL-F)       | ✓                | ✓               |
| appliance_nat (1:1/1:N/PF)     | ✓         | ✓                   | ✓ (VIPs)         | ✓               |
| security (IPS / AV)            | ✓         | ✓ (Snort)           | ✓ (IPS/AV)       | ✓               |
| uplinks (WAN status)           | ✓         | ✓                   | ✓                | ✓               |
| lan (VLANs + DHCP)             | ✓           | ✓                      | ✓                  | ✓               |
| syslog                         | ✓           | ✓                      | ✓                  | ✓               |

The reviewed set spans four of the major commercial managed-SD-WAN appliance
families; they are named here only to show the concept is genuinely shared
rather than borrowed from one product. The endpoint and feature names in
parentheses are each vendor's term for the same intent — they never leak into
`testprotocols`; they live only in the per-driver mapping. A capability that did
not appear across all four would not have entered the baseline.

### Data-model neutrality — vocabulary in commons, mappings in the plugin

`testprotocols` is **completely vendor-agnostic — a model must not name, encode,
or even hint at any specific product.** That rules out the usual leak patterns
(`native_id`, `native: dict`, opaque vendor strings, vendor-tagged ids). One
rule applies everywhere:

> **The normalized *vocabulary* lives in `testprotocols`; the
> vendor⇄normalized *mapping entries* live in the testbed plugin.** A driver
> translates on the way in/out of its API; `testprotocols` neither imports nor
> knows the mapping.

Concretely:

- **Every value vocabulary is a normalized `StrEnum` in `testprotocols`** —
  e.g. `RuleAction{ALLOW,DENY}`, `IntrusionMode{DISABLED,DETECTION,PREVENTION}`,
  `IntrusionSensitivity{LOW,MEDIUM,HIGH}`,
  `UplinkState{UP,DOWN,STANDBY,NOT_CONNECTED}`,
  `DhcpMode{SERVER,RELAY,DISABLED}`, `ShapingPriority{LOW,NORMAL,HIGH}`,
  `L7MatchType{APPLICATION,APPLICATION_CATEGORY,HOST,PORT,IP_RANGE,URL_PATTERN}`,
  `SecurityAction{ALLOWED,BLOCKED,DETECTED}`, `ThreatCategory{…}`,
  `SyslogRole{…}`. Enums grow by adding members **on test evidence**, never per
  vendor.
- **Taxonomies are normalized key sets owned by `testprotocols`** —
  `ContentCategory` and `ApplicationCategory`. A test blocks
  `ContentCategory.GAMBLING` or an `ApplicationCategory` member — **never a
  vendor id**. These registries grow on evidence.
- **The plugin holds the mapping.** A testbed plugin ships a translation table
  `{ContentCategory.GAMBLING: "<vendor-category-id>", …}`; the capability impl
  maps normalized→vendor on write and vendor→normalized on read. A vendor
  lacking a mapped entry surfaces as a clear *unsupported-capability* error in
  the driver — a coverage gap, **not** a contract leak. `testprotocols` stays
  clean.
- **Read models carry only normalized fields.** e.g. `SecurityEvent(ts, src_ip,
  dst_ip, protocol, action: SecurityAction, category: ThreatCategory,
  description)`; `UplinkStatus(name, state: UplinkState, ip, gateway,
  public_ip)`. **No `native` bucket.** If a test needs a vendor-only datum with
  no normalized field, that is the signal to **add a normalized field on
  evidence** — not to smuggle a dict.

The two hardest cases were resolved without any vendor leak:

- **L7 applications** → matched at the `ApplicationCategory` level today (an
  individual-`Application` registry is deferred in `GAPS.md` until a test needs
  named-application granularity); the plugin maps the normalized value to the
  vendor app-id. `L7Rule` carries `match_type` + a normalized value, never a
  vendor string.
- **IPS signatures** → **not modelled at all.** Behaviour is asserted via
  `SecurityEvent.action` + `category`; raw signature ids never enter the
  contract.

## Excluded host-substrate levers (explicit)

`conntrack`, `pcap` (`PcapCapture`), `ip_interface` (`IpInterface`), and `nat`
(`Nat`) are **not** on `SdwanApplianceDevice`. They remain on
`SdwanRouterDevice` (`linux_sdwan_router`) for the twin, with their existing
`*WhiteBox` extensions. No `*WhiteBox` is added for the new appliance
capabilities yet — no appliance-only deep-introspection surface has been
identified; one would be added on signal per `LEVELS.md`.

Forced link-down (admin-down an uplink) is likewise **not** on the appliance: a
managed appliance generally cannot admin-down its own uplink via API, so that is
a traffic-controller / infra-controller concern — the same boundary as the netem
precedent. The appliance keeps the Router *read* surface and `uplinks` status.

## Tracking-file entries

- **`SPLITS.md`** — `SdwanPolicyManager` firewall-method removal (2026-06-11):
  coherent-domain split; firewall now owned by `L3Firewall` / `L7Firewall`.
- **`GAPS.md`** — appliance follow-ons recorded as deferred (2026-06-11): the
  individual-`Application` registry and the typed `SdwanPolicyManager`
  path-steering surface; plus any future `*WhiteBox` candidates if
  appliance-only introspection surfaces later. Added 2026-06-12: static-route
  configuration and BGP config + operational read (deferred follow-ups from
  the `SiteToSiteVpn` seeding round).
- **`LEVELS.md`** — none yet (no white-box extensions added for this archetype).

## Verification

Protocol-conformance tests per capability; archetype registration +
`runtime_checkable` `isinstance` gate in the device-types test; `mypy --strict`;
twin regression (`linux_sdwan_router` unchanged); and a vendor-isolation grep
ensuring no product name or vendor id appears anywhere in the `testprotocols`
**package source** (the contract surface). Product names appear only in design
docs like this one, where they document the cross-vendor concept check — never
in a model, enum, or protocol.
