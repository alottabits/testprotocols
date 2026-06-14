# Capability granularity split log

Per the architecture rule: capability protocols bundle by coherent telco domain;
splits and merges land on tracked evidence (consumer signal, design review).
This file records the evidence.

Format per entry:

```
## YYYY-MM-DD — <protocol-or-method-set> moved <from> → <to>

**Signal:** <consumer-or-reviewer-quote-or-summary>
**Decision:** move / keep / defer
**Rationale:** <why>
**Migration impact:** <which consumers / tests / drivers needed updates>
```

---

## 2026-05-02 — `netem: NetemController` removed from `SdwanRouterDevice`

**Signal:** During Phase 5 cutover (sdwan-digital-twin example) the must-fix
review noted that `LinuxSdwanRouter` does not provide a `netem` capability
namespace. Inspection of the testbed showed netem is applied via separate
`LinuxTrafficController` devices sitting between the SDWAN router and its
WAN peers, not on the router itself.

**Decision:** Remove `netem: NetemController` from the `SdwanRouterDevice`
archetype. NetemController stays on `TrafficControllerDevice` where it
actually lives.

**Rationale:**
- The source palco-templates `linux_sdwan_router` registration listed
  `NetemController` as a template, but no driver implemented it on the
  router itself. The verbatim Task 8 conversion preserved the over-broad
  shape; the cutover surfaced that no consumer actually expected the
  router to shape its own traffic.
- Real-world testbeds put netem on intermediate traffic shapers (sitting
  between the device-under-test and its peers), not on the device itself.
  Asking an SDWAN router to also be its own traffic shaper conflates
  separate concerns.
- Tests requiring impaired WAN conditions still get them — via the
  `TrafficControllerDevice` archetype on `wan1_tc` / `wan2_tc` — which
  is exactly how the sdwan-digital-twin scenarios are written today.

**Methods affected:** none on the router itself (the netem attribute
was never wired up). Removing the requirement aligns the contract with
the de-facto driver shape.

**Migration impact at this point:**
- testprotocols `SdwanRouterDevice` shape narrowed from 7 attributes to 6.
- Per-archetype test in `test_device_types.py` updated.
- Plugin's `LinuxSdwanRouter` no longer needs to wrap or stub-out a
  netem capability that has no LinuxDevice methods to delegate to.
- Future tests that DO want a router with built-in impairment can
  define a plugin-local `<X>SdwanRouterDevice(SdwanRouterDevice,
  Protocol): netem: NetemController` extension and ship a driver that
  implements it.

---

## 2026-05-02 — MAC ACL methods moved `WifiStations` → `WifiBss`

**Signal:** During Task 9 (manual review and acceptance gate of the ABC →
Protocol migration), the reviewer flagged: *"Currently, set_acl_mode,
add_acl_entry, etc., live in WifiStations. While they do filter stations
(MACs), an ACL is fundamentally a configuration property of the BSS's
authorization scheme. It might conceptually belong in WifiBss alongside
set_security()."*

**Decision:** Move the 5 ACL methods from `WifiStations` to `WifiBss`.
Done as a separate commit on top of the Task 8 verbatim conversion.

**Rationale:**
- All 5 ACL methods were already keyed by BSS (`bss_name: str` was the first
  parameter on every one), not by station MAC. They configure the BSS's
  admission policy, not station state.
- Sit alongside `set_security` (WPA/WPA3/EAP authentication scheme) and
  `set_captive_portal` (post-association authorization) — same logical
  layer of "how does this BSS decide who gets in?".
- `WifiStations` retains only truly station-scoped operations:
  `list_associated_stations`, `get_station`, `disconnect_station`.
- Source ABCs in `palco-templates` had this granularity wrong; preserved
  verbatim by Task 8's mechanical conversion. The migration is the
  natural place to correct it before consumers depend on the bad shape.

**Methods moved (5):**
- `set_acl_mode` — `WifiStations.set_acl_mode(bss_name, mode)` → `WifiBss.set_acl_mode(name, mode)`
- `add_acl_entry` — `WifiStations.add_acl_entry(bss_name, mac)` → `WifiBss.add_acl_entry(name, mac)`
- `remove_acl_entry` — `WifiStations.remove_acl_entry(bss_name, mac)` → `WifiBss.remove_acl_entry(name, mac)`
- `clear_acl` — `WifiStations.clear_acl(bss_name)` → `WifiBss.clear_acl(name)`
- `get_acl` — `WifiStations.get_acl(bss_name) -> WifiAcl` → `WifiBss.get_acl(name) -> WifiAcl`

**Parameter rename:** `bss_name` → `name` for consistency with the rest of
`WifiBss` (every other method uses `name: str` as the BSS identifier).
No semantic change.

**Import migration:** `WifiAcl` (from `testprotocols.models.wifi`) moved
its only consumer from `wifi_stations.py` to `wifi_bss.py`.

**Migration impact at this point in the migration:**
- No drivers or operations consume these methods yet (testprotocols is
  pre-1.0; consumers will be updated in Phase 4-5 when palco-bdd
  examples flip to the new stack).
- Tests for `WifiStations` and `WifiBss` (Task 13's scope) will need to
  be split accordingly.

**Module docstrings updated** in both `wifi_stations.py` and `wifi_bss.py`
to reflect the new boundaries; the wifi_stations docstring includes a
forward reference: *"Per-BSS MAC ACL administration (set_acl_mode,
add_acl_entry, etc.) lives on the WifiBss template — see SPLITS.md
for the rationale."*

---

## 2026-05-11 — `PortForwarding` folded into a new `Firewall(PacketFilter, Protocol)` bundle

**Signal:** Architecture / code divergence review (palco-bdd
`docs/architecture/palco-architecture.md` describes a single `Firewall`
protocol bundling packet rules, port forwards, and zones, with `Nat` /
`Conntrack` as separate siblings; the actual code inherited the verbatim
five-way split from the source palco-templates ABCs — `PacketFilter`,
`PortForwarding`, `FirewallZones`, `Nat`, `Conntrack`). Design review
landed on a four-bundle / five-symbol shape: bundle packet rules + port
forwards by coherent telco domain, keep zones / NAT / conntrack split
on structural-shape grounds, and retain `PacketFilter` as the universal
narrow base for non-gateway archetypes.

**Decision:** Create `Firewall(PacketFilter, Protocol)` and
`FirewallWhiteBox(Firewall, Protocol)`. Delete the standalone
`PortForwarding` protocol. Migrate `CpeDevice` from `packet_filter` +
`port_forwarding` attributes to a single `firewall: Firewall` attribute.
Other archetypes (`ClientDevice`, `WanDevice`, `InfraDevice` variants,
`AcsDevice`, `ProvisionerDevice`, `LanClientDevice`, `WanServerDevice`)
keep their existing `packet_filter: PacketFilter` attribute — they are
not gateways and do not provide port forwarding.

**Rationale:**
- UCI's `firewall` config and TR-181's `Device.Firewall.*` subtree both
  treat packet rules and port forwards as one subsystem; an
  `iptables-save` dump captures both in one stream. Admins reason about
  them together. No realistic gateway driver implements one without the
  other.
- Zones, NAT, conntrack remain split because zone-aware vs flat-chain,
  gateway vs host, stateful vs stateless are real structural shape
  differences — the registration-gate `isinstance` check flags missing
  capability at startup rather than at first call.
- Non-gateway devices (clients, DHCP servers, ACS instances) have
  iptables rules but no port forwarding. Keeping `PacketFilter` as the
  narrow base preserves clean shape for endpoints; the gateway tier sits
  one Liskov step above as `Firewall(PacketFilter, Protocol)`.
- Protocol inheritance mirrors the existing
  `class FirewallWhiteBox(Firewall, Protocol)` pattern: tier
  relationships use Protocol inheritance, cross-domain mixins do not.

**Methods affected (7 moved):**
- `add_port_mapping` — `PortForwarding.add_port_mapping(mapping)` → `Firewall.add_port_mapping(mapping)`
- `remove_port_mapping` — `PortForwarding.remove_port_mapping(name)` → `Firewall.remove_port_mapping(name)`
- `list_port_mappings` — `PortForwarding.list_port_mappings()` → `Firewall.list_port_mappings()`
- `get_port_mapping` — `PortForwarding.get_port_mapping(name)` → `Firewall.get_port_mapping(name)`
- `set_port_mapping_enabled` — `PortForwarding.set_port_mapping_enabled(name, enabled)` → `Firewall.set_port_mapping_enabled(name, enabled)`
- `set_dmz_host` — `PortForwarding.set_dmz_host(host)` → `Firewall.set_dmz_host(host)`
- `get_dmz_host` — `PortForwarding.get_dmz_host()` → `Firewall.get_dmz_host()`

No signature changes. The `PortMapping` data model in
`models/firewall.py` is unchanged.

**Migration impact at this point:**
- `testprotocols`:
  - `port_forwarding.py` deleted.
  - `firewall.py` created.
  - `__init__.py` exports updated.
  - `devices/cpe.py` swapped `packet_filter` + `port_forwarding` for `firewall: Firewall`.
  - `tests/test_firewall_templates.py` swapped `PortForwarding` row for `Firewall` row + added inheritance assertions.
  - `tests/test_device_types.py` updated for new CpeDevice attribute set.
  - Sibling-module docstring cross-references refreshed.
- `palco-bdd`:
  - Architecture doc edits per the design spec.
  - No driver in any example currently imported `PortForwarding` — zero-cost migration on the consumer side.
- `palco-commons`, `palco`, `pytest-palco`, `boardfarm`, `boardfarm-bdd`,
  `palco-linux-bases`: no references — out of scope.

**Design spec:**
palco-bdd `docs/superpowers/specs/2026-05-11-firewall-protocol-bundling-design.md`.

---

## 2026-05-12 — `Tr069Gui` deleted; ACS-side inventory/state folded into `Tr069Server`

**Signal:** Usefulness review of `Tr069Gui` against `Tr069Server`. Of the 16
methods on `Tr069Gui`, six were pure `_via_gui` duplicates of existing CWMP
RPCs (`reboot_device_via_gui` ↔ `Reboot`, `get_device_parameter_via_gui` ↔
`GPV`, `set_device_parameter_via_gui` ↔ `SPV`, `trigger_firmware_upgrade_via_gui`
↔ `Download`, `factory_reset_via_gui` ↔ `FactoryReset`,
`verify_firmware_version_via_gui` ↔ `GPV` + compare). `verify_device_online`
was already covered by the operations-layer helper `is_cpe_online` in
`testoperations/tr069_server.py:13` (probe-by-GPV plus a poll). The remaining
methods (session control, ACS inventory, per-CPE connection state) were either
genuinely ACS-side server state — not GUI-specific — or driver-internal
concerns that no protocol consumer needs to type.

**Decision:**
1. Delete `Tr069Gui` entirely.
2. Fold the genuinely-new ACS-side methods into `Tr069Server` under
   capability-shaped names (no `_via_gui` suffix; no GUI vocabulary).
3. Treat "GUI" as a driver-internal route — like CWMP NBI or REST. Tests
   call `acs.tr069_server.list_cpes()`; the driver decides which transport
   fulfils it. Session lifecycle (login/logout) is therefore a
   driver-internal concern, not a protocol surface. `GuiSession` is *not*
   added to `testprotocols` — YAGNI until ≥2 consumers reinvent it
   independently.
4. Drop `tr069_gui: Tr069Gui` from `AcsDevice` without replacement.

**Rationale:**
- CWMP has no concept of an ACS-side device registry — `search_device`,
  `get_device_count`, `filter_devices`, `delete_device_via_gui` filled a
  genuine gap, but conflating that gap with "GUI" obscured what the
  methods actually do. They belong on the server protocol, named for
  the capability, not the transport.
- The BDD usage at `boardfarm-bdd/tests/step_defs/acs_gui_steps.py`
  confirmed that `get_device_status` is ACS-side connection state plus
  cached metadata (the offline scenario reads the same fields after the
  CPE drops off), not CPE-side parameters. The new `CpeConnectionStatus`
  dataclass models this with `online: bool`, `last_inform_time`, and
  cached `manufacturer` / `model` / `serial_number` / `hardware_version` /
  `software_version` — all `Optional` so an ACS that has never seen the
  CPE can still return a valid object.
- `last_inform_time` was originally a separate method on the GUI; folded
  into `CpeConnectionStatus` since it shares the same ACS-side bookkeeping
  bucket and the BDD details-page view always queries both pieces
  together.
- "CPE" follows TR-069 §2 (any CWMP-managed device). A one-line docstring
  clarification at the top of `tr069_server.py` records this for readers
  who might assume the term is narrower.

**Methods affected:**

Net-new on `Tr069Server` (3 additions):
- `list_cpes(criteria=None) -> list[str]` — replaces `search_device`,
  `get_device_count`, and `filter_devices` from `Tr069Gui` (count via
  `len(...)`, existence via `cpe_id in ...`).
- `delete_cpe_record(cpe_id) -> bool` — replaces `delete_device_via_gui`.
  Dropped the GUI-only `confirm=True` flag.
- `get_cpe_connection_status(cpe_id) -> CpeConnectionStatus` — replaces
  `get_device_status` and `get_last_inform_time` (folded into the model).

Deleted with no replacement (driver-internal or covered elsewhere):
- `login`, `logout`, `is_logged_in` — driver-internal session lifecycle.
- `reboot_device_via_gui`, `factory_reset_via_gui`,
  `get_device_parameter_via_gui`, `set_device_parameter_via_gui`,
  `trigger_firmware_upgrade_via_gui`, `verify_firmware_version_via_gui`
  — already covered by `Reboot`, `FactoryReset`, `GPV`, `SPV`, `Download`,
  `GPV` on `Tr069Server`. Use those via whichever route the driver chose.
- `verify_device_online` — covered by `testoperations/tr069_server.py:13`
  `is_cpe_online` plus a poll-loop at the operations layer.

**Migration impact at this point:**
- `testprotocols`:
  - `tr069_gui.py` deleted.
  - `models/tr069.py` created with `CpeConnectionStatus`.
  - `models/__init__.py` exports `CpeConnectionStatus`.
  - `tr069_server.py` gains 3 methods + a clarifying docstring on "CPE".
  - `__init__.py` exports updated (drop `Tr069Gui`).
  - `devices/infra.py` drops `tr069_gui: Tr069Gui` from `AcsDevice`.
  - `tests/test_cpe_templates.py` removes the `Tr069Gui` row, adds the
    three new methods to the `Tr069Server` expected-method set.
  - `tests/test_device_types.py` updates `AcsDevice` expected attrs.
  - `docs/python-protocol-adoption-architecture.md` collapses the
    separate "TR-069 GUI" row into the `Tr069Server` notes.
- `boardfarm-bdd`:
  - Step definitions and feature scenarios under
    `tests/features/ACS GUI Device Management.feature` reference the
    removed protocol; out of scope for this commit, will be updated
    when those drivers are migrated. Tests that exercise login
    behaviour specifically (`UC-ACS-GUI-01-2a` Invalid Credentials) will
    need the driver to expose `login` as a concrete method — not via a
    typed `testprotocols` contract.
- Other consumers: no production driver yet implements `Tr069Gui`.

---

## 2026-06-11 — firewall-rule methods removed from `SdwanPolicyManager`

**Signal:** Designing the vendor-neutral managed-appliance archetype
(`SdwanApplianceDevice`) surfaced that `SdwanPolicyManager` bundled firewall-rule
administration (`apply_firewall_rule` / `remove_firewall_rule` /
`get_firewall_rules`) alongside SD-WAN path/SLA policy. Firewall is a separate
coherent domain — a managed appliance models it as L3 and L7 policy surfaces, not
as an attribute of its SD-WAN steering.

**Decision:** move — remove the three firewall methods from `SdwanPolicyManager`.
Firewall administration is owned by the new `l3_firewall.L3Firewall` (ordered L3
policy) and `l7_firewall.L7Firewall` (application-aware) capabilities.
`SdwanPolicyManager` retains generic policy, SLA policy, and application-flow
visibility.

**Rationale:**
- Coherent-domain bundling: path/SLA steering and packet/application firewalling
  are distinct subsystems a driver may implement independently.
- The new `SdwanApplianceDevice` composes `l3_firewall` / `l7_firewall` as
  first-class attributes; leaving firewall methods on `sdwan_policy` too would be
  redundant and ambiguous.

**Methods affected (3 removed):**
- `apply_firewall_rule(rule)` → `L3Firewall.set_outbound_rules` / `L7Firewall.set_rules`.
- `remove_firewall_rule(name)` → list-replace via the same setters.
- `get_firewall_rules()` → `L3Firewall.get_outbound_rules` / `L7Firewall.get_rules`.
The `FirewallRule` model import was dropped from `sdwan_policy_manager.py`.

**Migration impact:**
- `testprotocols`: `sdwan_policy_manager.py` slimmed; `tests/test_wan_edge_templates.py`
  expected-method set updated + an absence assertion added; docstring cross-refs
  in `packet_filter.py` and `models/firewall.py` repointed.
- `SdwanRouterDevice` (the digital twin's `linux_sdwan_router`) is unaffected at
  the **conformance** level — its `sdwan_policy` driver still *has* the methods, so
  removing them from the Protocol cannot break it. The sdwan-digital-twin example
  may need step-def migration only if it calls the removed methods *through the
  typed `sdwan_policy` attribute* (mypy-only; runtime unaffected) — separate repo,
  pre-1.0, out of scope here.

**Related:** new `SdwanApplianceDevice` archetype (`devices/sdwan.py`, registered
`sdwan_appliance`); the appliance capability family is logged in `GAPS.md`
(2026-06-11 entries) for the deferred follow-ons.

---

## 2026-06-12 — `bring_wan_down` / `bring_wan_up` moved `Router` → `WanLinkAdmin`

**Signal:** Granularity review of the appliance protocol work: *"API-managed
appliances like managed SD-WAN edges cannot administratively down their own
uplinks. Split Router into a pure read protocol and a separate link-admin
protocol implemented only by the Linux digital twin."* Corroborated by the
2026-06-12 capability validation: no reviewed managed-appliance API publishes
an admin-down operation for its own uplink, yet `Router` rides on **both**
WAN-edge archetypes, so the appliance archetype demanded two methods its
device class cannot implement.

**Decision:** move

**Rationale:** The read surface (interface status, path metrics, link health,
telemetry, routing table) is universal across WAN-edge archetypes; forced
link-down is a host-substrate lever (the twin shells `ip link set … down`).
Same boundary as the netem precedent: a capability that structurally belongs
to a different substrate does not ride on the shared protocol. `Router` is now
read-only; `WanLinkAdmin` (`wan_link_admin.py`) carries `bring_wan_down` /
`bring_wan_up` and is composed only by `SdwanRouterDevice` (`wan_admin:`).

**Migration impact:**
- `testprotocols`: `router.py` slimmed (read-only); new `wan_link_admin.py`;
  `SdwanRouterDevice` gains `wan_admin: WanLinkAdmin`; `SdwanApplianceDevice`
  unchanged (its archetype gate now asserts `wan_admin` absent);
  `tests/test_wan_edge_templates.py` expected sets updated + absence assertion.
- `testoperations`: unaffected — `measure_failover_convergence` only reads
  `get_active_wan_interface` (impairment is injected via `NetemController`).
- The external digital-twin driver must add a `wan_admin` attribute exposing
  its existing `bring_wan_down`/`bring_wan_up` implementations before
  upgrading (pre-1.0 coordinated migration; methods themselves are unchanged).

---

## 2026-06-14 — `Router` RIB read shared into a switch-scoped `RoutingRead` (planned)

**Signal:** Managed-switch design round
(`docs/l3-switch-protocol-design.md`). A managed distribution switch routes
east-west between local SVIs; it needs the RIB **read** surface of `Router`
(`get_routing_table() -> list[RouteEntry]`) but **none** of `Router`'s
WAN-uplink methods. The RIB read is currently buried inside the WAN-edge
`Router`.

**Decision:** defer (executes when the switch protocols are implemented). Carve
the RIB-read kernel into a switch-scoped `RoutingRead` capability that shares the
`RouteEntry` model with `Router`; `Router` keeps its WAN-uplink methods. Bundled
with this carve-out, `RouteEntry` (`models/wan_edge.py`) is **reshaped**: it
gains an `origin: RouteOrigin` field (new `RouteOrigin` StrEnum:
`STATIC/CONNECTED/OSPF/BGP/LOCAL`) so a switch route read can report the route
source.

**Rationale:** Read surface is universal across routed archetypes; WAN-uplink
admin is WAN-edge-specific — the same structural-shape boundary as the
2026-06-12 `WanLinkAdmin` split. Modelling the switch against the full `Router`
shape would over-specify it with uplink methods it does not have.

**Migration impact:** none yet — design-review record only. When implemented:
the `origin` field carries a **default** so both existing `RouteEntry`
producers — `Router.get_routing_table()` (WAN edge) and
`Bgp.get_learned_routes()` — stay source-compatible (no call-site change). The
method carve-out leaves `Router` consumers unaffected (`Router` keeps its
methods); the switch composes the new `RoutingRead`. The dynamic-/learned-RIB
*facet* is 3/6 across the reviewed distribution families and is admitted as a
per-method best-effort read (the `bgp.py` operational-read discipline), while
the config-view read is 6/6. Design record:
`docs/l3-switch-protocol-design.md`.

---

## 2026-06-14 — `ApplianceVlans` SVI/DHCP fields shared into `RoutedInterfaces` / `InterfaceDhcp` (planned)

**Signal:** Managed-switch design round
(`docs/l3-switch-protocol-design.md`). `appliance_vlans.VlanConfig` already
carries an SVI IP plus the `DhcpMode{SERVER,RELAY,DISABLED}` field and per-VLAN
DHCP config — almost exactly the L3-switch SVI + per-SVI DHCP shape — but it is
named and scoped for the WAN edge.

**Decision:** defer (executes at switch-protocol implementation). Share the SVI
+ DHCP fields of `VlanConfig` into the switch's `RoutedInterfaces` (SVI / routed
port) and `InterfaceDhcp` (per-SVI server/relay) capabilities, renaming
`appliance_ip → svi_ip`. `DhcpMode` is reused, not re-declared.

**Rationale:** Same coherent concept (an L3 interface over a VLAN with optional
DHCP) on two device classes; one model, two accessors beats a greenfield
duplicate. The rename de-WAN-edges the field name.

**Migration impact:** none yet — design-review record only. When implemented:
the `appliance_ip → svi_ip` rename touches the appliance consumer(s) of
`VlanConfig`; log the appliance-side migration at that point. Design record:
`docs/l3-switch-protocol-design.md`.

---

## 2026-06-14 — unified `SwitchAcl` (one L2+L3 ACL surface, not two protocols)

**Signal:** Managed-switch design round
(`docs/l2-switch-protocol-design.md`, `docs/l3-switch-protocol-design.md`). The
reviewed switches enforce L2 (MAC/VLAN) and L3/L4 (5-tuple) ACLs through **one
engine** — on the design-target, literally the same endpoint — so modelling
separate L2 and L3 ACL protocols would not match any reviewed product.

**Decision:** implement as a net-new `SwitchAcl` capability. One surface
carrying both L2 and L3 match fields, bound by port/VLAN and
`AclDirection{INGRESS,EGRESS}` as an ordered whole-list-replace. Enum reuse of
`RuleAction{ALLOW,DENY}` / `RuleProtocol` (`models/sdwan_appliance.py`); new
`SwitchAclRule` record (optional `src_mac`/`dst_mac`/`vlan` + optional IP
5-tuple) in `models/switch.py`; the existing `L3Rule` (pure IP 5-tuple) is **not**
extended. Composed on `L2Switch` as `switch_acl: SwitchAcl`.

**Rationale:** Match the real device shape (one ACL engine); reuse the rule
vocabularies rather than duplicating them; keep host-chain shapes
(`packet_filter`) and the appliance LAN/WAN/VPN triad (`l3_firewall`) out — both
are gateway/host-shaped.

**Migration impact (implemented 2026-06-14):**
- `switch_acl.py` — new `SwitchAcl` protocol with `set_acl` / `get_acl`.
- `models/switch.py` — new `SwitchAclRule` record.
- `devices/switch.py` — `L2Switch.switch_acl: SwitchAcl`.
- `L3Rule` and its consumers unchanged.
- Plan 2 (`L3Switch`) composes the same `SwitchAcl` unchanged — the L2+L3
  unified surface already covers the L3 superset.
- Design record: `docs/l2-switch-protocol-design.md` (Status: Implemented).

---
