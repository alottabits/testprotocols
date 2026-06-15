# Missing-capability log

Tracks capability protocols that should exist but don't yet — adjacent to
`SPLITS.md` (granularity changes within existing protocols) and `LEVELS.md`
(white-box extension signals on existing protocols), this file logs whole
*new* protocol shapes that have been signalled but deferred.

The architecture rule is the same as elsewhere: protocols land on tracked
evidence. For a brand-new capability, the bar is **a test that needs it** —
ideally two consumers agreeing on the shape before the design freezes.

Format per entry:

```
## YYYY-MM-DD — <CapabilityName> [priority: high / medium / low]

**Signal:** <reviewer-or-consumer-quote-or-summary>
**Trigger to act:** <what concrete event makes this stop being deferred>
**Out of scope right now because:** <why we're not building it during the migration>
**Design notes (when picked up):** <bulleted hints — not a binding spec>
**Cross-references:** <related capabilities, models, or architecture sections>
```

---

## 2026-05-02 — `L2Bridge` [priority: HIGH]

**Signal:** During Task 9 review: *"I see vlan_client.py and ip_routing.py,
but no protocol for configuring L2 bridges, assigning physical Ethernet
ports to bridges, or managing STP/RSTP. This is a common requirement for
CPEs."*

**Trigger to act:** First commit on the planned CPE example (`examples/cpe-gateway/`,
Domain #1 in palco-bdd README). A CPE without a bridge protocol is anomalous —
LAN-side topology testing, port-isolation tests, and STP / loop-prevention
validation all assume one. The CPE example's first BDD scenario that touches
LAN-side bridging should drive the API shape.

**Out of scope right now because:** Neither sip-telephony nor sdwan-digital-twin
needs L2 bridging. The architecture rule "splits and merges happen on tracked
evidence" applies in reverse for net-new capabilities — speculative shapes
without a real consumer tend to need rework on first use.

**Design notes (when picked up):**
- Per-bridge: create / delete / list, set STP/RSTP/MSTP mode, set ageing time,
  set forward-delay, set hello-time, set max-age.
- Per-port-membership: add port to bridge, remove port from bridge, set port
  priority, set port path-cost, set port edge / BPDU-guard / root-guard flags.
- Read-side: `list_bridge_ports`, `get_stp_state` (root MAC, root port, blocked
  ports, designated ports), `get_bridge_table` (FDB entries: MAC, port, vlan,
  ageing time).
- Implementation substrates differ widely: brctl (legacy), iproute2 / `ip link`
  (modern Linux), `nft / table bridge` (nftables-based), vendor-CLI bridges,
  TR-181 `Device.Bridging.*`. Drivers must abstract; design Protocol around
  *intent* (port-in-bridge with this priority and these flags) not vendor command.
- Coordinates with `vlan_client.py` for tagged ports; with `firewall_zones.py`
  for zone membership; with `ip_interface.py` for the bridge-as-L3-interface
  lifecycle (`br-lan` is both a bridge and an interface).
- WhiteBox extension at design time: raw `bridge fdb show` / `bridge link show`
  output for kernel-level FDB pinning.

**Cross-references:** `vlan_client.py`, `ip_interface.py`, `ip_routing.py`,
`firewall_zones.py`. CPE archetype protocol (`testprotocols/devices/cpe.py`)
will need an `l2_bridge: L2Bridge` attribute once seeded.

**Update 2026-06-14 (managed-switch design round) — realize-as-switch-native
decision:** The managed-switch design docs
(`docs/l2-switch-protocol-design.md`, `docs/l3-switch-protocol-design.md`)
deliberately do **not** realize this `L2Bridge` entry. A managed switch's
first-class object is the *switchport* — modeled by switch-native capabilities
(`SwitchPorts`, `SpanningTree`, `LinkAggregation`, `PortPoe`, `MacTable`) — not
"add port to bridge"; and link aggregation and PoE have no home in the
Linux-bridge shape at all. Reusing this substrate-shaped contract on a
hardware-switch device class would be the same mistake the SD-WAN appliance
archetype rejected for its host levers. `L2Bridge` therefore stays scoped to
its original **CPE / Linux-bridge** trigger. To stop the two from diverging,
the STP/FDB *vocabulary* genuinely shared between a Linux bridge and a hardware
switch — `StpMode`, `StpGuard`, `StpPortState`, and the `MacTableEntry` record
— is authored by the switch work in a neutral commons module
`models/l2_common.py`; when this `L2Bridge` entry is picked up it must
**import that shared vocabulary** rather than re-inventing divergent enums.
Cross-reference both switch design docs.

---

## 2026-05-02 — `WifiMlo` (or `WifiBss` / `WifiStations` extension for MLO) [priority: low]

**Signal:** During Task 9 review: *"The WifiStation data model has a
capability_flags field that might include 'MLO'. However, there are no
protocol methods to manage or observe Multi-Link operations (e.g.,
querying which links/bands an MLO-capable station is actively using, or
setting primary/secondary links)."*

**Trigger to act:** First Wi-Fi 7 testbed in palco-bdd, OR a customer
asking for MLO-related test coverage. Wi-Fi 7 stacks are still hardening
across vendors as of 2026 H1; designing speculatively risks landing the
wrong abstractions.

**Out of scope right now because:** No current testbed runs Wi-Fi 7. The
`capability_flags` field on `WifiStation` already lets observation code
*notice* MLO presence without a Protocol; that's enough for the current
black-box tests. Protocol methods become valuable once tests want to
*assert* MLO behaviour (link selection, EMLSR/EMLMR/STR mode, primary-
link failover).

**Design notes (when picked up):**
- Decision: separate `WifiMlo` Protocol vs. extension on `WifiBss` /
  `WifiStations`. Most operations are observation-side (which links is
  this STA using, what mode, what TID-to-link map), so a sibling Protocol
  to `WifiStations` may be cleaner — leave `WifiBss` for AP-side config
  not specific to MLO.
- Observation: `get_mlo_status(mac) -> MloStationStatus` with fields
  `(active_links: list[LinkInfo], mode: "EMLSR"|"EMLMR"|"STR", primary_link:
  str, tid_to_link_map: dict[int, str], ...)`. `LinkInfo` has band, channel,
  bandwidth, RSSI per link.
- Configuration: AP-side enable/disable per band (`enable_mlo(bands: list[str])`),
  client-side primary-link hint (vendor-specific; may not be portable).
- `WifiStation.capability_flags` already carries MLO presence — keep that;
  add MLO observation as separate Protocol so non-MLO drivers don't need
  to satisfy the new interface.
- WhiteBox extension at design time: raw 802.11be capability frames,
  per-link beacon dumps.

**Cross-references:** `wifi_stations.py`, `wifi_bss.py`, `wifi_radio.py`
(per-radio MLO mode setting), `models/wifi.py::WifiStation.capability_flags`.

---

## 2026-05-02 — `WifiQos` (WMM / Access Categories) [priority: low]

**Signal:** During Task 9 review: *"There is currently no representation
of Wi-Fi Multimedia (WMM) Access Categories (Voice, Video, Best Effort,
Background). You may want to add methods to WifiBss to configure DSCP-to-AC
mappings, and add per-AC packet statistics to WifiStation or WifiRadioStats."*

**Trigger to act:** First palco-bdd test that asserts QoS behaviour — voice-
quality tests under contended Wi-Fi load, video-streaming AC prioritisation,
or DSCP-marking-survives-bridge tests. The voice-telephony domain (Domain #3
in README) is likely first: voice scenarios under contention need WMM
prioritisation working correctly to pass.

**Out of scope right now because:** sip-telephony's current scenarios run on
an unloaded Kamailio testbed without contention; sdwan-digital-twin's QoE
metrics measure end-to-end performance through netem, not Wi-Fi WMM. No
current scenario fails for lack of QoS observation.

**Design notes (when picked up):**
- Naming: `WifiQos` is the obvious name; possibly `WifiWmm` to be specific
  to 802.11e. `WifiQos` reads better and leaves room for non-WMM extensions
  (Wi-Fi 7 multi-link QoS, vendor-specific schedulers).
- Configuration on `WifiBss` (or new sibling `WifiQos` Protocol):
  `set_wmm_enabled(name, enabled)`, `set_dscp_to_ac_map(name, map: dict[int, str])`
  where AC is one of `"VO" | "VI" | "BE" | "BK"`.
- Per-AC EDCA parameters (`set_edca_params(name, ac, cwmin, cwmax, aifsn,
  txop_limit_us)`) typically vendor-divergent — start without these, add
  on tracked evidence.
- Per-AC stats on `WifiStation` (extend the dataclass) or on a new
  `WifiRadioQosStats` model with fields `(ac, tx_packets, tx_bytes,
  tx_retries, tx_dropped, rx_packets, rx_bytes)` per AC.
- DSCP markings cross with firewall (`firewall_zones.py` has `set_zone_defaults`
  but not DSCP rewrite); coordinate.
- WhiteBox extension: raw hostapd `wmm_param_set` output, vendor EDCA tables.

**Cross-references:** `wifi_bss.py`, `wifi_stations.py`, `models/wifi.py`,
`firewall_zones.py` (DSCP marking is partially a firewall concern).

---

## 2026-05-02 — `WifiSpectrum` [priority: low — already deferred upstream]

**Signal:** During Task 9 review: *"The WifiRf template explicitly defers
FFT/CleanAir spectral scanning to a future WifiSpectrum template. This is
a good decision given vendor divergence, but ensures you don't forget it
if deep RF testing is a requirement."*

**Trigger to act:** First palco-bdd scenario that needs spectral analysis —
typically interference-investigation tests, hidden-network discovery tests,
or radar-detection-correctness verification beyond the synthetic injection
already covered by `WifiRadioWhiteBox.inject_radar_event`.

**Out of scope right now because:** The deferral is already documented in
`wifi_rf.py`'s module docstring as an upstream design decision in palco-templates.
This entry exists only to ensure visibility once tests require it.

**Design notes (when picked up):**
- Heavy vendor divergence: Atheros / ath10k / ath11k spectral_scan, Intel
  CleanAir, Broadcom-specific tooling, mac80211_hwsim simulated spectra.
- Likely pure WhiteBox from day one — there's almost no portable contract
  available across substrates.
- Possible methods: `start_spectral_scan(band, duration_s)`, `read_spectral_scan_buffer()`,
  `get_channel_utilization(band) -> dict`. Latter may merit graduating from
  WhiteBox to base if all substrates can produce *some* channel-busy estimate.
- Coordinate with `wifi_radio.py` (per-band radio control) and `wifi_rf.py`
  (the existing template that points to this gap).

**Cross-references:** `wifi_radio.py`, `wifi_rf.py` (module-docstring deferral
comment).

---

## 2026-05-02 — `StreamingServerDevice` [priority: low — currently plugin-local]

**Signal:** During Phase 5 cutover (sdwan-digital-twin example), the must-fix
review noted that `StreamingServer` exists as a capability protocol but no
`StreamingServerDevice` archetype was defined. Per the architecture's
three-tier scope rule, plugin-local until a second consumer materialises.

**Trigger to act:** Second consumer (a different example or testbed) needing
a streaming server. At that point lift the plugin-local definition from
`palco-bdd/examples/sdwan-digital-twin/palco_plugins/sdwan/sdwan_plugin/protocols/streaming.py`
into `testprotocols/devices/infra.py` (or a new `streaming.py`) and align
both consumers on the same shape.

**Out of scope as a commons archetype because:** sdwan-digital-twin is the
only consumer today. Plugin-local definition lets the example move forward
without forcing a speculative shape into commons.

**Current plugin-local shape (minimal):** `streaming_server: StreamingServer`
— that's it. No `ip_interface` / `pcap` / `file_transfer` requirement at
this tier. A second consumer may push for those; design when the evidence
arrives.

**Cross-references:** plugin-local definition at
`palco-bdd/examples/sdwan-digital-twin/palco_plugins/sdwan/sdwan_plugin/protocols/streaming.py`;
`testprotocols/streaming_server.py` (the underlying capability protocol).

---

## 2026-06-11 — `Application` (individual-application registry) [priority: low]

**Signal:** The managed-appliance L7 firewall (`l7_firewall.L7Firewall`) matches by
`ApplicationCategory` (a seeded normalized taxonomy) but not by *individual
application*. `L7Rule.value` for `match_type=APPLICATION` is a vendor-mapped string
meanwhile.

**Trigger to act:** First test that must allow/deny/steer a *named* application
rather than a category.

**Out of scope right now because:** No consumer needs individual-app granularity yet;
categories cover the evidenced cases. An individual-application catalog is large and
more vendor-divergent than categories — seed on real evidence to avoid churn.

**Design notes (when picked up):** a normalized `Application` StrEnum (commons owns the
keys; plugins map to vendor app-ids), grown on evidence; `L7Rule.value` for
`APPLICATION` then carries an `Application` member.

**Cross-references:** `models/sdwan_appliance.py` (`ApplicationCategory`, `L7MatchType`,
`L7Rule`), `l7_firewall.py`.

---

## 2026-06-11 — migrate legacy bare-`str` value fields to typed vocabularies [priority: low]

**Signal:** The SD-WAN appliance models (`models/sdwan_appliance.py`) express their
normalized value vocabularies as `StrEnum`s (static + runtime checking). The
pre-existing models — e.g. `models/wan_edge.py`'s `LinkStatus.state`,
`TrafficShapingRule.priority` / `match`, and similar bare-`str`-with-comment fields
across the older capabilities — are *under-typed*, a verbatim artifact of the
ABC→Protocol migration. A typed vocabulary catches an invalid / unmapped vendor value
statically; bare `str` does not.

**Trigger to act:** Touching a given legacy capability for other reasons, or a consumer
hitting a vendor-value mismatch the type system would have caught.

**Out of scope right now because:** Broad and cross-cutting; best done incrementally
per-capability on evidence, not as one sweep. Pre-1.0, so migratable without external
breakage.

**Design notes (when picked up):** introduce `StrEnum`s for the value sets, keep them
string-valued (serialization-clean), update consumers/tests; one capability per change
with its own SPLITS/LEVELS note as needed.

**Review findings (2026-06-11 — blast-radius assessment, no action taken yet):**

*Why this is low-risk at runtime:* `StrEnum` **is** `str` (subclass), so members
compare / hash / format / `isinstance`-check as their string value. The sole current
consumer (`vitro-bdd`) keeps working unchanged for `==` comparisons, str-keyed dict
lookups (vendor-mapping tables), `.upper()`, `in (...)` membership, `isinstance(x, str)`,
and `json.dumps`. The SD-WAN appliance testbed consumer only touches the
appliance surface (already `StrEnum`) → **zero impact** there.

*Where it actually breaks — static typing + vocabulary mismatches, not runtime:*
- A dataclass does **not** coerce: a field typed `FooEnum` that receives a bare runtime
  `str` is flagged by `mypy --strict` (vitro-bdd runs mypy). Breakage is at **constructor
  call sites** and **reverse-mapping reads** (`dict.get(...) -> str`), each needing the
  producer to wrap the value as `FooEnum(raw)` — which *adds* validation but introduces a
  new `ValueError`-on-unmapped-value failure mode.
- **Gating design decision:** (A) match the appliance pattern (annotation + mypy only;
  validation only holds where producers build enums) **vs** (B) add `__post_init__`
  coercion (`self.x = FooEnum(self.x)`) — guarantees validation at every construction and
  makes the vitro migration nearly free (it can keep passing strings), at the cost of a
  few lines per dataclass and divergence from `models/sdwan_appliance.py`. **Decide this
  before writing code — it gates everything.**

*Vocabulary reconciliations to settle (the real work):*
- `FirewallRule.action` doc says `allow/deny/reject/log`, but vitro `frr_router.py` emits
  an **undocumented `"alert"`** (mapped to LOG). A strict enum must include `ALERT` or
  vitro must change to `LOG`.
- **Do not unify the action vocabularies:** `FirewallRule.action`
  (`allow/deny/reject/log`), `Zone`/`ZonePolicy.action` (`accept/drop/reject`), and
  appliance `RuleAction` (`allow/deny`) are three distinct sets — keep separate enums.
- **Protocol vocabularies also differ:** `FirewallRule` (`tcp/udp/icmp/any`), `PortMapping`
  (`tcp/udp/tcp-udp`), appliance `RuleProtocol` (`+icmp6`), `TrafficSpec` (`tcp/udp`) — no
  single shared enum fits all (`tcp-udp`, `icmp6` are the odd ones).
- `Connection.state` is **explicitly open-ended** ("…or driver-specific values") — **not
  enum-safe**; leave as `str`. Same for vendor-divergent / undocumented fields
  (`WifiBssConfig.security_mode`, `VPNPeerStatus.reachability`, `QoEResult.protocol`,
  `MeasurementSpec.completion`) — defer until a test needs them.

*Candidate inventory (tiered):*
- **Firewall domain — do first (highest vitro usage):** `FirewallRule.action`
  (`FirewallAction`), `FirewallRule.protocol`, `NatRule.mode` (`NatMode`),
  `NatRule.protocol`, `PortMapping.protocol`, `Zone`/`ZonePolicy.action` (`ZoneAction`).
- **`WifiBand` — best value/effort:** one enum (`2.4GHz/5GHz/6GHz`) reused across 6+ wifi
  models (`WifiBssConfig.band`, `WifiStation.band`, `WifiNeighbor.band`,
  `WifiChannelUtilization.band`, `WifiRadioStats.band`, `WifiMeshLink.band`); no consumer
  impact.
- **Then:** `LinkStatus.state` / `LinkHealthReport.state` (`LinkState`, ≠ appliance
  `UplinkState`), `TrafficShapingRule.priority` (reuse `ShapingPriority`),
  `TrafficSpec.protocol`, `WifiBssConfig.mfp`, `WifiAcl.mode`, `WifiMesh*.role`,
  `RadiusAccountingRecord.record_type`.
- **Leave alone:** `Connection.state`; `MulticastGroupRecordType` (already an int `Enum` —
  correctly not a `StrEnum`).

*Suggested sequencing:* settle (A)-vs-(B) → firewall domain (migrate `testprotocols` +
the ~6 vitro files in one branch, mypy-strict green on both) → `WifiBand` → the rest,
incrementally, on evidence.

**Cross-references:** `models/wan_edge.py`, `models/firewall.py`, `models/wifi.py`,
`models/traffic.py`, `models/radius.py`, `models/sdwan_appliance.py` (the pattern to
follow), `packet_filter.py` (`chain` / `policy` strings). Consumer blast-radius:
`vitro-bdd` examples `cpe-gateway` + `sdwan-digital-twin` (firewall steps, uci /
linux_firewall / frr_router impls, unit tests).

---

## 2026-06-11 — appliance health / online capability [priority: medium]

**Signal:** Composing `SdwanApplianceDevice` wanted an online/uptime check, but the
existing `device_management.DeviceManagement` is **Linux-host-shaped** (ps options,
memory, board logs, boot-time log, arbitrary file content) — a cloud-managed
appliance can satisfy only a couple of its methods via its management API. Putting
it on the appliance archetype would be the same substrate mismatch the appliance
reshape removed (conntrack / pcap / ip_interface / nat), so it was **left off**.

**Trigger to act:** First test that needs to assert an appliance is reachable /
report uptime / reboot it through the typed contract.

**Out of scope right now because:** No current test needs it; `ApplianceUplinks`
status already implies reachability, and provisioning/health checks can use a
driver-internal call meanwhile. Designing a health capability speculatively risks
the wrong shape.

**Design notes (when picked up):** a small `ApplianceHealth` (or similar) Protocol —
`is_online() -> bool`, `get_uptime_seconds() -> float | None`, `reboot() -> None`,
maybe `read_event_log(since_s) -> list[...]` — mapping to the vendor's device-status
/ event endpoints. Add `health: ApplianceHealth` to `SdwanApplianceDevice` once
seeded. Do **not** reuse the host-shaped `DeviceManagement`.

**Cross-references:** `devices/sdwan.py` (`SdwanApplianceDevice`),
`device_management.py` (the host-shaped one to NOT reuse), `appliance_uplinks.py`.

---

## 2026-06-14 — `IgmpSnooping` [priority: HIGH]

**Signal:** The managed-switch design round
(`docs/l2-switch-protocol-design.md`) cross-vendor review found IGMP snooping
clears the strong-majority bar (5–6/6) across the reviewed access-switch
families, but the design-target (Meraki MS225) exposes **no API config** —
snooping runs by default and is toggled in the controller UI only — and no
switch test drives it yet.

**Trigger to act:** First switch scenario asserting multicast group containment
/ snooping behaviour at L2.

**Out of scope right now because:** No consumer test, and the design-target has
no programmatic surface to drive; a speculative shape would need rework on first
real use.

**Design notes (when picked up):** a snooping vocabulary (enable / querier /
group-membership read) seeded then. `models/multicast.py` currently holds only
the IGMPv3 record-type codes (`MulticastGroupRecordType`, RFC 3376) and the
`McastSource` / `McastGroup` aliases — **not** a snooping vocabulary. Coordinate
with `MulticastRouting` (below) for shared multicast vocab.

**Cross-references:** `docs/l2-switch-protocol-design.md`, `models/multicast.py`,
`MulticastRouting` (this file).

---

## 2026-06-14 — `PortMirror` (SPAN) [priority: medium]

**Signal:** Managed-switch design round: the SPAN-session concept is 6/6 present
across the reviewed access families, but it **straddles the
`TrafficControllerDevice` / `pcap` boundary** (capture is the traffic device's
job — the netem precedent in `SPLITS.md`), and the design-target exposes only a
per-port mirror, not a multi-source SPAN object.

**Trigger to act:** A test needing switch-side mirror-session config that is
distinct from host packet capture.

**Out of scope right now because:** No driving test, and the device-boundary
decision (switch-owned mirror vs traffic-controller capture) needs to be settled
on real evidence rather than guessed.

**Design notes (when picked up):** a `PortMirror` protocol (session: source
ports + direction → destination port) on the switch archetype; record the
boundary with `pcap` / `TrafficControllerDevice` explicitly.

**Cross-references:** `docs/l2-switch-protocol-design.md`, `pcap_capture.py`,
`SPLITS.md` (2026-05-02 netem precedent).

---

## 2026-06-14 — `MulticastRouting` (PIM) [priority: medium]

**Signal:** L3-switch design round (`docs/l3-switch-protocol-design.md`):
PIM-SM + RP reaches 5/6 present across the distribution review set
(Meraki / Aruba CX / Juniper / Catalyst full, FortiSwitch ◐ standalone-only,
UniFi ✗) — the **same headcount** as the admitted `GatewayRedundancy` — but is
deferred on the **driving-test discriminator**: high surface area and no switch
test drives it, whereas `GatewayRedundancy` carries a first-hop-failover test.

**Trigger to act:** A switch scenario asserting routed multicast distribution.

**Out of scope right now because:** Large, vendor-divergent surface admitted on
a real test, not on headcount alone.

**Design notes (when picked up):** reuse `RouteEntry` (`models/wan_edge.py`) and
a multicast vocab; coordinate with `IgmpSnooping` for shared multicast
vocabulary.

**Cross-references:** `docs/l3-switch-protocol-design.md`, `IgmpSnooping` (this
file), `models/multicast.py`.

---

## 2026-06-14 — `Bgp` on the mandatory `L3Switch` [priority: low / note]

**Signal:** L3-switch design round: the existing `Bgp` protocol (`bgp.py`) is
reusable as-is, but BGP **fails the L3-switch majority bar** (4/6 under the
◐-counts-as-present convention — Aruba CX / Juniper / Catalyst full, FortiSwitch
◐ standalone-only, absent on the design-target MS355 and on UniFi). It is
therefore composed only on the optional `L3SwitchRouted(L3Switch, Protocol)`
variant, never on the mandatory `L3Switch`.

**Trigger to act:** A switch test (across more than the routed minority) that
drives BGP into the mandatory baseline.

**Out of scope right now because:** Forcing a minority-of-segment capability onto
every L3 switch is exactly the one-vendor-shape risk the cross-vendor bar guards
against; the optional variant covers the routed deployments meanwhile.

**Design notes (when picked up):** promote `bgp: Bgp` from `L3SwitchRouted` to
the mandatory `L3Switch` only on test evidence; no model change needed
(`BgpConfig` / `BgpPeerStatus` / `BgpNeighbor` / `BgpSessionState` already live
in `models/sdwan_appliance.py`, imported by `bgp.py`).

**Cross-references:** `docs/l3-switch-protocol-design.md`, `bgp.py`,
`models/sdwan_appliance.py`.

---

## 2026-06-14 — `SwitchStacks` / stack-scoped config [priority: low]

**Signal:** Managed-switch design round: most reviewed families expose physical
stacking and stack-level state (and stack-level L3 on the distribution set); no
current test exercises it.

**Trigger to act:** A test asserting stack membership, stack-scoped config, or
stack-member failover.

**Out of scope right now because:** No consumer, and the surface is
vendor-divergent — seed on evidence.

**Design notes (when picked up):** a stack-membership read plus stack-scoped
config accessors; design the shape against the first consumer.

**Update 2026-06-15 (driver evidence — trigger NOT yet fired):** a Meraki
L3-switch driver hit the stack-scope endpoint divergence (per-device routing
endpoints return 400 on stack members) and absorbed it **driver-side** via
stack-scoped vs per-device endpoint selection (a `_stack.py` helper across
`routed_interfaces` / `static_routes` / `routing_read` / `interface_dhcp`); the
contract method shape was preserved. A driver needing stack membership
*internally* is **not** the trigger — the trigger remains a **test** asserting
stack membership / stack-scoped config / member failover. If/when it fires, the
shape is a composed `SwitchStacks` capability (optionally a
`L3SwitchStacked(L3Switch, Protocol)` tier that adds it, mirroring
`L3SwitchRouted`/`bgp`) — **not** a role-defined device type, since stacked/
standalone is mutable state, not a capability superset.

**Cross-references:** `docs/l2-switch-protocol-design.md`,
`docs/l3-switch-protocol-design.md`.

---

## 2026-06-14 — `IpSourceGuard` (`FirstHopSecurity` optional extension) [priority: low]

**Signal:** Spec-review feedback on the switch design proposed first-hop security;
the dedicated concept-check landed `FirstHopSecurity` (DHCP snooping + DAI) as an
`L2Switch` baseline capability, but **IP Source Guard** is present on only 5/6
reviewed hardware families (Aruba 1960, Catalyst 9200L, Juniper EX2300, Omada,
Arista) and is absent/uncertain on the cloud targets (Meraki MS225, UniFi), so it
was kept **out** of the baseline `FirstHopSecurity` shape.

**Trigger to act:** First test asserting source-IP filtering against the
DHCP-snooping binding table.

**Out of scope right now because:** Borderline cross-vendor and unproven on the
cloud design-target; the baseline DHCP-snooping + DAI surface covers the evidenced
cases.

**Design notes (when picked up):** add as an optional `FirstHopSecurity` method
(or a sibling capability) reusing the snooping binding-table model; drivers
lacking it raise unsupported-capability.

**Cross-references:** `docs/l2-switch-protocol-design.md` (`FirstHopSecurity`).

---

## 2026-06-14 — `Vrf` / multi-VRF awareness [priority: medium]

**Signal:** Spec-review feedback: modern distribution switches use VRFs for
segmentation. VRF is present on the enterprise on-box families (Catalyst 9300,
Aruba CX 6300, Juniper EX4400, Arista CCS-720XP) but **absent on the design-target
— Meraki MS225/MS355 have a single global routing table** (VRF on Meraki is
IOS-XE-only: MS390 / Cloud-Managed Catalyst, 17.18+) — and absent on UniFi. ~4/6
(5/7 with Arista), patterning exactly like `Bgp`.

**Trigger to act:** A VRF-capable driver **and** a test asserting per-VRF
segmentation / overlapping addressing.

**Out of scope right now because:** The design-target cannot exercise it, so the
L3 models are scoped to the default VRF (stated explicitly in the L3 design);
adding speculative multi-table fields ahead of a consumer violates the
grow-on-evidence rule.

**Design notes (when picked up):** add an optional `vrf: str | None = None` field
(default → global table, back-compatible) to `RoutedInterfaces` / `StaticRoutes`
/ `RoutingRead` / `Ospf` and a `vrf` selector on the reads; a driver without VRF
ignores it or raises unsupported-capability for a non-default value. This is a
`SPLITS.md`-worthy reshape of those models when it lands — pre-designed here to
keep the future change clean.

**Cross-references:** `docs/l3-switch-protocol-design.md` (§New capabilities →
*Scope — default VRF only*; Arista v2 VRF note), `models/switch_routing.py`,
`static_routes.py`, `models/wan_edge.py` (`RouteEntry`).

---

## 2026-06-14 — `Vxlan` / EVPN fabric [priority: low–medium]

**Signal:** Spec-review feedback: VXLAN + EVPN campus fabric is a defining
modern-distribution feature (Catalyst 9300, Aruba CX 6300, Arista 720XP).

**Trigger to act:** A campus-fabric test scenario (overlay reachability, VNI
mapping, EVPN peering).

**Out of scope right now because:** Massive, vendor-divergent surface area and no
driving test — same bucket as `MulticastRouting`.

**Design notes (when picked up):** a dedicated capability (VNI↔VLAN mapping, VTEP
config, EVPN address family) seeded on real evidence — large enough to warrant
its own design doc.

**Cross-references:** `docs/l3-switch-protocol-design.md`, `MulticastRouting`
(this file).

---

## 2026-06-14 — `RoutingPolicy` (route redistribution / route-maps / prefix-lists) [priority: medium]

**Signal:** Spec-review feedback: L3 switches running OSPF/BGP commonly
redistribute connected/static routes into the IGP via route-maps / prefix-lists.
Present on the on-box families, limited on the cloud target.

**Trigger to act:** A test asserting route redistribution or route filtering.

**Out of scope right now because:** The route-map / prefix-list **expression** is
highly vendor-divergent and there is no driving test; an intent-level shape needs
real evidence to avoid baking in one vendor's grammar.

**Design notes (when picked up):** either a `RoutingPolicy` capability (normalized
match/set predicates + redistribution rules) or bounded redistribution fields on
`Ospf` / `Bgp`; design the normalized expression on the first consumer.

**Cross-references:** `docs/l3-switch-protocol-design.md`, `bgp.py`,
`models/switch_routing.py` (`Ospf`).

---

## 2026-06-14 — `Bfd` (Bidirectional Forwarding Detection) [priority: low]

**Signal:** Spec-review feedback: BFD is standard for fast convergence on
distribution uplinks alongside OSPF/BGP. Present on the on-box families,
limited/absent on the cloud target.

**Trigger to act:** A convergence-time test.

**Out of scope right now because:** No driving test; a speculative toggle adds
surface without evidence.

**Design notes (when picked up):** model as an optional toggle (interval /
multiplier) on `OspfInterfaceSettings` and `BgpNeighbor` — **not** a standalone
capability.

**Cross-references:** `docs/l3-switch-protocol-design.md`
(`OspfInterfaceSettings`), `bgp.py` (`BgpNeighbor`).

---

## 2026-06-15 — explicit per-port RADIUS-server selection on `AccessPolicy` [priority: low]

**Signal:** During the MD225 (Meraki MS-class) switch-driver implementation, the
`port_security.py` module docstring states the access policy *"references RADIUS
servers by name from the composed `radius` (`RadiusClient`) registry"* — but the
`AccessPolicy` record (`models/switch.py`) carries **no field naming which
servers** a port's policy should use. Today the link is implicit: a `DOT1X`
policy authenticates against whatever is registered in the composed
`RadiusClient`, with no per-port subset selection.

**Trigger to act:** First test or driver that must point different ports at
**different** registered RADIUS server sets (i.e. more than one server group in
play across the switch's access policies), rather than a single implicit
registry.

**Out of scope right now because:** No consumer needs per-port server selection;
the single implicit-registry link covers every evidenced 802.1X/MAB case, and the
reviewed design-target inlines one server set per access policy. Adding the field
speculatively ahead of a driving test risks the wrong shape (e.g. names vs group
ids).

**Design notes (when picked up):** add an optional
`radius_server_names: list[str] = field(default_factory=list)` to `AccessPolicy`
— empty meaning "driver uses the default/whole registry" so the change is
back-compatible. Drivers map the names → vendor server refs; on Meraki the names
resolve to the bound access policy's inline `radiusServers` array (see the
SPLITS.md shared-backing-object entry). This is a `SPLITS.md`-worthy model reshape
when it lands.

**Cross-references:** `port_security.py` (`PortSecurity`, the docstring claim),
`models/switch.py` (`AccessPolicy`), `radius_client.py` (`RadiusClient`),
`SPLITS.md` (2026-06-15 `RadiusClient`/`PortSecurity` shared-backing-object
entry).

---

## Implemented

- **2026-06-12 — `SdwanPolicyManager` typed path-steering surface** (deferred
  2026-06-11): trigger fired — operator acceptance steering/route-decision
  tests drove the exact shape. Landed as `SteeringScope` / `FlowMatch` /
  `UplinkSelectionRule` + `set_uplink_selection` / `get_uplink_selection`;
  performance classes reuse `SLAPolicy` by name (no separate
  `PerformanceClass`). Both existing implementations migrated in step.
  Design record: `docs/superpowers/specs/2026-06-12-typed-path-steering-design.md`.

- **2026-06-12 — Static-route configuration** (deferred earlier the same
  day): landed as the sibling `StaticRoutes` capability
  (`add_static_route` / `remove_static_route` / `list_static_routes` over
  `StaticRoute(name, destination_cidr, next_hop)`), composed on **both**
  WAN-edge archetypes — `Router` stays read-only. Per-entry CRUD (all five
  reviewed families store static routes as individual objects); config-view
  read-back deliberately added beyond the original sketch. Both existing
  implementations migrated in step.
  Design record: `docs/superpowers/specs/2026-06-12-static-routes-design.md`.

- **2026-06-12 — BGP configuration + operational read** (the last entry of
  the SD-WAN seeding round): landed as the sibling `Bgp` capability on both
  WAN-edge archetypes — `set_bgp_config` / `get_bgp_config` (whole-replace
  `BgpConfig(enabled, as_number, neighbors, advertised_networks)`) plus the
  operational reads `get_bgp_neighbors` (`BgpPeerStatus` with the RFC 4271
  `BgpSessionState` vocabulary) and `get_learned_routes`. Config is 5/5
  across the reviewed families; the operational reads are 4/5 and carry the
  unsupported-capability convention per method. Both existing
  implementations migrated in step.
  Design record: `docs/superpowers/specs/2026-06-12-bgp-design.md`.

---

## Workflow

When picking up a deferred capability:

1. Confirm the **trigger to act** has fired (consumer signal exists, not just
   speculative want).
2. Move the entry from this file's main section to a new "Implemented" section
   at the bottom (or delete it; git history preserves the design notes).
3. Implement: protocol module, dataclass models if needed, WhiteBox extension
   if appropriate, tests asserting the protocol shape.
4. Cross-reference any new device archetypes that should aggregate the new
   capability (e.g. `CpeDevice` should grow `l2_bridge: L2Bridge` once seeded).
