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

## 2026-06-12 — BGP configuration + operational read [priority: medium]

**Signal:** Operator acceptance scopes require BGP peering between the
appliance and a LAN-side router, asserting advertised routes on the peer and
learned routes on the appliance. No capability protocol covers BGP
configuration or BGP operational state.

**Trigger to act:** First appliance driver or testbed implementing a BGP
acceptance case.

**Out of scope right now because:** same prioritization as the static-route
entry; BGP additionally needs a config/read split decision (below) that
deserves its own design pass.

**Design notes (when picked up):** model **config and operational read as
separate methods** — configuration is available on all four reviewed
families (Meraki Dashboard API `appliance/vpn/bgp`; Catalyst SD-WAN Manager
BGP feature template; FortiOS `router/bgp`; Prisma SD-WAN element
`bgppeers`), but at least one family publishes **no** BGP operational/
learned-route read, so a driver must be able to support config while raising
unsupported-capability on the status read. Read side elsewhere: FortiOS
routing monitor, SD-WAN Manager `/device/bgp/*`, Prisma `bgppeers/status` +
`reachableprefixes`.

**Cross-references:** `router.py`, `site_to_site_vpn.py` (overlay vs
LAN-side routing boundary), `devices/sdwan.py`.

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
