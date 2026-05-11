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
