# Design: Python Protocol Adoption — palco-commons Architecture

> **HISTORICAL CONTEXT (2026-05-02):** This document was written *before* the migration
> it proposes. It uses pre-migration names throughout: `palco-templates` (the source
> ABC package, now → `testprotocols`), `palco-operations` (now → `testoperations`),
> `palco-bases` (now → `palco-linux-bases`, in a separate repo), and `palco-commons`
> (the original monorepo, now archived; protocols + operations live in this
> `testprotocols` repo, bases live in `palco-linux-bases`).
>
> The migration was executed on 2026-05-02 following this design. The current
> architecture spec is at
> [palco-bdd/docs/architecture/palco-architecture.md](https://github.com/alottabits/palco-bdd/blob/main/docs/architecture/palco-architecture.md);
> tracking files for follow-up work are at:
>
> - `packages/testprotocols/SPLITS.md` — granularity changes within existing protocols
> - `packages/testprotocols/LEVELS.md` — white-box extension signals
> - `packages/testprotocols/GAPS.md` — missing capabilities (deferred net-new protocols)
>
> Read this document for the **design rationale**; consult the architecture spec
> for the **current shape**.

| Field       | Value                                                                                                                                                                                                          |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Status      | Implemented (migration executed 2026-05-02)                                                                                                                                                                    |
| Author(s)   | rjvisser                                                                                                                                                                                                       |
| Reviewer(s) | TBD                                                                                                                                                                                                            |
| Date        | 2026-04-30 (design); migrated 2026-05-02                                                                                                                                                                       |
| Related     | `docs/superpowers/specs/2026-04-15-palco-commons-design.md`, `demo/` (the working sketch this design generalizes), [PEP 544 / typing spec — Protocols](https://typing.python.org/en/latest/spec/protocol.html) |

## Context and Problem Statement

The current `palco-templates` design (commons design spec §2a, §6) —
which this document proposes to rename to `palco-protocols` — makes
each domain-role contract a Python ABC inheriting from a shared
`Template` base, and asks every driver to implement the contract by
**compiling inner classes** under namespaced attributes:

```python
class FrrSdwanRouter(LinuxDevice):
    device_type = "linux_sdwan_router"

    class router(Router):                # ABC inner-class composition
        def get_active_wan_interface(self): ...
    class sdwan_policy(SdwanPolicyManager): ...
    class netem(NetemController): ...
```

This shape works, but it has three frictions that surface every time a
new template ships:

1. **Boilerplate.** Every driver re-states the namespace name + the ABC
   to inherit from. The "namespace" is structural (`device.router.<method>`),
   yet the ABC inheritance is nominal — drivers must do both.
2. **No structural composition.** Multiple compilation (commons spec §8)
   needs the same template implemented twice (`tr069_server` for REST
   API, `tr069_server_gui` for browser-driven). An object that *happens*
   to expose the same shape (e.g. `device.gui` already has its own
   `tr069_server`) cannot be reused — it would need to inherit the
   template ABC explicitly.
3. **Operations are typed against ABCs they don't actually need.**
   `palco-operations` functions accept `Router` instances, but only call
   one or two methods on them. The ABC dependency is heavier than the
   actual contract the operation requires.

The `demo/` tree (added by `e1ab3f3`) sketches the alternative: declare
each capability as a `typing.Protocol`, declare a device as a
`Protocol` of named attributes, and let drivers structurally implement
the device shape without any inheritance. This document tightens that
sketch into a coherent architecture covering protocols, drivers,
operations, step definitions, and the `devices/` registry.

## Why `typing.Protocol`

Two language-level reasons make `typing.Protocol` the right primitive
for palco's contract layer:

- **Duck typing with type hints.** Protocols are Python's way of
  expressing structural typing — "any object that has these
  attributes / methods" — while still giving editors and type
  checkers something to verify. This matches the Pythonic style of
  the standard library (`Iterable`, `Sized`, `Hashable`, …) and the
  duck-typed surface palco already relies on at the L2 step layer.
- **Interface Segregation by construction.** A capability Protocol
  names exactly the methods a caller depends on. Operations narrow
  to the smallest Protocol they need, so a function that only calls
  `router.get_active_wan_interface()` does not pull in the rest of
  the `Router` ABC's surface as part of its declared contract.

> See [PEP 544 / typing spec — Protocols](https://typing.python.org/en/latest/spec/protocol.html)

## Adoption objectives

The redesign is graded against three objectives. Every convention in
this document either advances one of them or is rejected:

| # | Objective | How Protocols deliver it |
|---|-----------|--------------------------|
| **1** | **Standardize test APIs across testbed implementations.** Every example (sdwan, sip-telephony, cpe-gateway, future) must expose the same call shape for the same capability — `device.routing.get_active_wan_interface()` reads identically whether the driver is `LinuxSdwanRouter`, `FrrCpe`, or a docker stub. | **Capability protocols** ([L4a](#l4a--capability-protocols)) live in `palco-protocols` once and are bundled by [coherent telco domain](#capability-granularity-bundle-by-coherent-telco-domain-split-on-evidence) (one `Firewall`, one `Routing`, one `Nat`, …). Industry-standard **device protocols** ([L4b](#where-device-protocols-live-archetype-in-commons-vs-plugin-local)) — `LinuxCpe`, `LinuxAcs`, etc. — also live in commons; testbed-specific device shapes stay in plugins. Drivers in any plugin satisfy the same protocols structurally; tests, operations, and step defs depend only on those protocols, never on driver classes. |
| **2** | **Keep testbed-plugin authoring lean.** A test-automation engineer adding a new driver should write methods, not scaffolding, and the contract surface they're satisfying should match how real systems group their controls. | Drivers shed inner-class ABC inheritance. A driver becomes a plain class whose `__init__` assigns capability implementations to namespaced attributes; satisfaction is checked by mypy / pyright (static) and `isinstance(driver, DeviceProtocol)` at registration (runtime). The bundle-by-coherent-domain rule means the cpe-gateway-firewall driver implements **one** `Firewall` impl per route instead of three (`PacketFilter` + `PortForwarding` + `FirewallZones`). No `class router(Router):` ceremony, no `Template` base. |
| **3** | **Express "same capability, multiple transports" with a default + opt-in alternatives.** A CPE that exposes its firewall via UCI *and* TR-069 must let tests call the default route ergonomically (`device.firewall.add_rule(...)`) and pin a specific route when needed (`device.tr069.firewall.add_rule(...)`). | A first-class **route convention** (see [L4c](#l4c--route-convention-default--alternative-transports)). Each transport becomes a sub-namespace on the device (`device.tr069`, `device.uci`, `device.gui`, `device.api`, …); the device root forwards selected attributes to one route as the default. Each route sub-namespace is itself a structural shape, so call sites can swap `device` for `device.<route>` without changing what they call. |

The remainder of the document maps each design choice back to one of
these objectives.

## Goals and Non-Goals

### Goals

- Replace the ABC-based template hierarchy with **`typing.Protocol`**
  contracts at every layer: capability protocols (per-domain), device
  protocols (per device type), and route protocols (per transport, for
  multi-transport devices).
- **Rename the package `palco-templates` → `palco-protocols`** and
  adopt protocol terminology throughout the codebase (modules,
  docstrings, tests, related architecture docs). The old "template"
  vocabulary is replaced by the two-tier model: *capability protocol*
  (atomic, one domain-role capability) and *device protocol*
  (aggregate, one device shape composed of capability-typed
  attributes). Since `palco-commons` has no third-party consumers
  yet, this is a one-shot rename — no compatibility shim, no alias
  module, no period of dual support.
- Eliminate the inner-class boilerplate from drivers. A driver becomes
  a plain class whose attributes structurally match the device protocol.
- Preserve the namespace-composition model exactly as designed (commons
  spec §2a) — `device.routing.get_active_wan_interface()` still works.
- Promote multi-transport support (commons spec §8) from a
  suffix-naming convention (`tr069_server` + `tr069_server_gui`) to a
  first-class **route convention** (`device.api.tr069_server`,
  `device.gui.tr069_server`, with `device.tr069_server` aliasing the
  default route). See [§L4c](#l4c--route-convention-default--alternative-transports).
- Pick **capability granularity by coherent telco domain, not by
  minimal sub-concern.** One Protocol per telco-natural cluster
  (e.g. one `Firewall` covering packet rules + port forwards + zones,
  not three protocols). Bundle by default; split on evidence tracked
  in `SPLITS.md`. See
  [Capability granularity](#capability-granularity-bundle-by-coherent-telco-domain-split-on-evidence).
  This collapses today's ~50 ABCs to roughly 15–20 capability
  protocols.
- **Two-level capability tiering** (black-box mandatory + white-box
  optional). Each capability protocol is the mandatory sea-level
  contract every conforming driver implements; deep-introspection
  methods live in an optional `<Capability>WhiteBox` extension
  Protocol that inherits from the mandatory one. Drivers implement
  WhiteBox only when their image / transport actually backs the
  introspection. See
  [Capability levels](#capability-levels-black-box-mandatory--white-box-optional).
  Commons archetypes declare the mandatory tier only; richer
  contracts surface via route protocols (`UciRoute.firewall:
  FirewallWhiteBox`) or plugin-local extended archetypes.
- Place device protocols by a **three-tier rule**: industry-standard
  archetypes (`LinuxCpe`, `LinuxAcs`, …) in commons; cross-testbed
  shapes promoted to commons when a second consumer appears; testbed-
  specific device shapes stay in plugins. See
  [Where device protocols live](#where-device-protocols-live-archetype-in-commons-vs-plugin-local).
  This is the bloat valve that prevents `palco-protocols` from
  becoming the boardfarm-style monolith we're moving away from.
- Keep operations transport-agnostic and assertion-free; the call-site
  contract is now a Protocol parameter type, not an ABC parameter type.
- Provide a **runtime safety net** — devices fail loudly at registration
  time when they do not satisfy the protocols their `device_type`
  declares.

### Non-Goals

- **Changing the operations layer's responsibilities.** Operations stay
  pure functions in `palco-operations`, receiving resolved
  template/protocol instances. Only their type annotations change.
- **Changing Palco's framework hooks.** `palco_add_devices` keeps mapping
  a `device_type` string to a driver class. The driver's internal
  organization changes; Palco's contract with the driver does not.
- **Migrating the L2 step-definition layer.** Step definitions already
  use duck-typed `getattr(device, namespace)` access; they get better
  IDE support after the migration but no semantic change is required.
- **Replacing dataclasses or models.** `palco_protocols.models.*` stays
  as dataclasses — Protocols cover behaviour, dataclasses cover
  structure-with-fields.
- **Rewriting the architecture spec from scratch.** The 2026-04-15
  design document remains the canonical narrative; this document is an
  amendment that revises §2a (composition mechanism), §2c (bases),
  §6 (package architecture), §7 (template design principles), §8
  (transport selection), and §9 (testbed plugin structure).

## Proposed Solution

### Layered architecture

Seven layers. L4 fans out into L4a (capability protocols), L4b (device
protocols), and L4c (route convention) so each concern has its own
home:

```
┌──────────────────────────────────────────────────────────────────────┐
│  L1   Feature files (Gherkin)               [testbed repo]           │  unchanged
│  L2   Step definitions                       [testbed repo]          │  unchanged
│  L3   Operations                             [palco-operations]      │  type annotations only
│  L4a  Capability protocols (per domain-role) [palco-protocols]       │  ABC → Protocol
│  L4b  Device protocols (per device type)     [palco-protocols]       │  device_type() → DeviceProtocol
│  L4c  Route convention (transport selection) [palco-protocols +      │  NEW — formalises
│       device.<route>.<capability> + default   driver convention]     │  multiple compilation
│  L5   Implementation bases                   [palco-bases]           │  unchanged
│  L6   Device drivers                         [testbed plugin]        │  inner-class scaffolding dropped;
│                                                                       │  routes wired in __init__
└──────────────────────────────────────────────────────────────────────┘
```

The substantive change is L4a / L4b / L4c. L6 changes shape because
L4 no longer requires inheritance and because the route convention
moves transport selection out of attribute-name suffixes and into
sub-namespaces. L3 changes only its type annotations. L1, L2, L5 are
unchanged.

### L4a — Capability Protocols

Each existing domain-role template (today an ABC) becomes a
`typing.Protocol` with the same method set, made
`@runtime_checkable` so registration-time validation is possible
(see [Runtime safety](#runtime-safety) below).

```python
# packages/palco-protocols/src/palco_protocols/router.py
from __future__ import annotations
from typing import Protocol, runtime_checkable

from palco_protocols.models.wan_edge import LinkStatus

@runtime_checkable
class Router(Protocol):
    """Capability protocol for a routing-aware WAN-path device."""

    def get_active_wan_interface(self) -> str: ...
    def bring_wan_down(self, label: str) -> None: ...
    def bring_wan_up(self, label: str) -> None: ...
    def get_wan_interface_status(self) -> dict[str, LinkStatus]: ...
    # ... rest of the existing surface ...
```

Notes on the per-protocol pattern:

- **`@runtime_checkable`.** The standard library decorator allows
  `isinstance(obj, Router)` to test attribute existence at runtime. It
  does *not* check method signatures (PEP 544 §runtime_checkable),
  which is why the static type-check gate remains essential.
- **No `_device` back-reference.** The current `Template` base class
  stores a `_device` reference on `__init__` so inner-class methods
  can call `self._device.execute_command(...)`. Under Protocols there
  is no shared base. Drivers either:
  - Keep using nested classes that hold a back-reference (compatible
    with today's pattern; the inner class is just no longer inheriting
    from `Template`), or
  - Switch to standalone classes that take the device in `__init__`
    explicitly: `Tr069ServerImpl(device).gpv()`. See
    [Driver patterns](#l6--device-drivers-testbed-plugins).
- **Method signatures stay identical** to the current ABC surface, so
  the migration is mechanical for the contract methods themselves.
- **Models continue to live in `palco_protocols.models.*`** and are
  imported by the protocols that return / accept them.
- **`@runtime_checkable` with non-trivial signatures has known
  footguns** (no signature checking; performance overhead with
  `isinstance` on hot paths). We use it only in `device_manager`
  registration (cold path) and in tests; never inside operations.

#### Capability granularity: bundle by coherent telco domain, split on evidence

**Default rule:** one capability protocol per **coherent capability
cluster** as recognised in telco / network-engineering vocabulary —
matching how standards bodies and admin tooling group methods. Bundle
*by default*; split *on evidence*. This deliberately rejects the
extreme of one protocol per minimal sub-concern (which the original
five-firewall-templates split was an example of) and the extreme of
one protocol per device (which collapses interface segregation).

**Why telco-natural grouping over minimal-decomposition:**

- A real CPE's firewall is one subsystem — UCI puts packet rules,
  port forwards, and zones in one `firewall` config; TR-181 puts them
  in one `Device.Firewall.*` subtree; admins reason about them as one
  thing. Splitting them into separate Protocols was decomposition for
  its own sake, and it's what was driving us toward needing a
  "molecular" mixin tier to recompose.
- Drivers implementing every method of a small bundle is the common
  case. `NotImplementedError` for the rare unsupported method is
  cheaper than `NotImplementedError` for whole protocols a driver
  doesn't support at all.
- Operations rarely touch only one sub-concern of a domain. A
  port-forward operation that happens to want to also clear a stale
  packet-filter rule already has both methods reachable through one
  bundle attribute.

**Seed capability inventory** (working set for the three current
example testbeds — `sdwan-digital-twin`, `sip-telephony`,
`cpe-gateway`). About 15–20 protocols, replacing today's ~50 ABCs.
Wifi, fully-fledged QoS, cellular, etc. land later as their domains
ship.

| Domain                     | Capability protocol                | Notes                                                                                                  |
| -------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------ |
| L2/L3 plumbing             | `IpInterface`                      | Link state, MAC, IPv4 / IPv6 addrs, link up/down. Universal.                                           |
| Routing                    | `Routing`                          | Static + default + policy routes, WAN-iface state, path metrics. One routing table → one bundle.       |
| Firewall                   | `Firewall`                         | Packet rules + port forwards + zones. One UCI section / one TR-181 subtree.                            |
| NAT                        | `Nat`                              | Separate — TR-181 splits `Device.NAT.*`; SNAT/DNAT semantics distinct from rule filtering.             |
| Conntrack                  | `Conntrack`                        | Separate — read-mostly observability, different lifecycle from rule mgmt.                              |
| SD-WAN policy              | `SdwanPolicy`                      | PBR + SLA + traffic shaping + L7 firewall extensions. Coherent because they're all "policy".           |
| Impairment                 | `NetemController`                  | Single-purpose.                                                                                        |
| Packet capture             | `PcapCapture`                      | Single-purpose observability.                                                                          |
| TR-069 (CWMP)              | `Tr069Server` + `Tr069Client`      | Split by role — different actors (ACS NBI vs CPE CWMP), different transports. `Tr069Server` covers CWMP RPCs plus ACS-side state (inventory, per-CPE connection status). Drivers may fulfil the server surface over any transport — CWMP NBI, REST, GUI scrape — as a driver-internal choice. |
| SIP                        | `SipPhone` + `SipServer`           | Split by role.                                                                                         |
| HTTP                       | `HttpClient` + `HttpServer`        | Split by role.                                                                                         |
| Device lifecycle           | `DeviceLifecycle`                  | Boot / reboot / factory-reset / wait-for-online.                                                       |
| Device management          | `DeviceManagement`                 | Steady-state health (`is_online`, version queries, telemetry). Split from lifecycle by lifecycle phase. |
| NTP                        | `NtpClient`                        | Small single-purpose; clock discipline.                                                                |
| Hardware console           | `HwConsole`                        | Serial / on-device console for boot capture and emergency repair.                                      |
| File transfer              | `FileTransfer`                     | scp / sftp / curl-style file movement.                                                                 |
| nmap                       | `NmapScanner`                      | Single-purpose probe.                                                                                  |
| Wi-Fi                      | `WifiRadio` + `WifiSteering` (TBD) | Defer until the wifi example lands; split likely warranted by 802.11r/k/v lifecycle.                   |

**Split / merge triggers.** Adjustment is evidence-based, not
aesthetic. The signals that justify a change:

| Signal                                                                                                  | Trigger                                                       | Action                                                                                                                                |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| ≥2 drivers raise `NotImplementedError` on the same method group within a bundle                         | Partial-only is the norm, not the exception                   | **Split** the bundle along the missing-methods seam.                                                                                  |
| An operation's parameter type pulls in many methods it doesn't call, AND the mismatch repeats in ≥2 ops | Interface-segregation pressure                                | **Define a narrower ad-hoc Protocol** alongside the bundle. The bundle stays for device typing; the narrow Protocol types operations. |
| A new domain ships with two clearly distinct sub-roles (server vs client, control vs observation)       | Server-vs-client / control-vs-observe is structurally obvious | **Start split** from day one.                                                                                                         |
| Methods in a bundle diverge in transport (one is CLI-only, one is ACS-only)                             | This is a route concern, not a granularity concern            | Use the [route convention](#l4c--route-convention-default--alternative-transports), **not** a protocol split.                         |
| "Feels tidier as separate" with no concrete consumer signal                                             | Premature abstraction                                         | **Don't split.**                                                                                                                      |

**Tracking.** Driver authors who hit a `NotImplementedError` need or
an awkward operation parameter type log a one-line entry in
`packages/palco-protocols/SPLITS.md` (date, capability, signal,
referencing UC or driver). Splits are acted on when the file shows
≥2 entries pointing at the same seam. Merges follow the same
discipline in reverse — a tracked entry with ≥2 examples of two
adjacent protocols always being passed together.

**Migration is cheap.** Splitting `Firewall` → `Firewall` +
`PortForwardingExtensions` later is backwards-compatible for drivers
that implement the full bundle (they automatically satisfy both
narrower Protocols structurally). Operations that wanted the narrow
contract migrate one signature at a time. This is what makes
"start coarse, split on evidence" the right risk profile — wrong
grouping costs less than for inheritance hierarchies.

#### Capability levels: black-box mandatory + white-box optional

Tests come in two perspectives that map cleanly to a two-tier
capability model:

- **Black-box / grey-box tests** drive the device through its
  standard control surface and assert outcomes via standard
  observation methods. These are the portable tests that run against
  any conforming driver — production CPE, docker stub, RDK-B build,
  prplOS RPi.
- **White-box tests** additionally need deep introspection: kernel
  iptables dumps, FRR zebra RIB walks, vendor-NBI internals, raw
  protocol traces. They only run against drivers whose underlying
  image / transport actually exposes these hooks.

Cockburn's three use-case altitudes (kite / sea / clam) are well-known
but don't all map to device methods cleanly: outcome-level "kite"
assertions ("did the call connect?") are *test assertions* built from
sea-level observations like `phone.is_connected()`, not separate
methods on the device. So the practical split is two levels — sea
(black-box) + clam (white-box) — with the standard surface mandatory
and the deep-introspection surface opt-in.

**Pattern: optional `<Capability>WhiteBox` extension Protocol.** Per
capability that has a meaningful introspection layer, define an
extension that inherits from the mandatory Protocol:

```python
@runtime_checkable
class Firewall(Protocol):
    """Mandatory sea-level surface. Black-box and grey-box tests use this.
    Every conforming driver implements every method (NotImplementedError
    only for individual unsupported method per the granularity rule)."""
    def add_rule(self, chain: str, rule: FirewallRule, ...) -> None: ...
    def add_port_mapping(self, m: PortMapping) -> None: ...
    def list_rules(self, chain: str) -> list[FirewallRule]: ...
    def list_port_mappings(self) -> list[PortMapping]: ...
    # ... full standard surface ...

@runtime_checkable
class FirewallWhiteBox(Firewall, Protocol):
    """Optional white-box extension. Only drivers with kernel / raw access implement it.

    A driver that satisfies FirewallWhiteBox is, by Liskov, also a
    Firewall — the standard surface is included.
    """
    def get_kernel_iptables_dump(self) -> str: ...
    def get_uci_raw_config(self) -> str: ...
    def get_fw4_internal_state(self) -> dict: ...
```

**Properties:**

1. **Liskov-safe.** `FirewallWhiteBox` *is a* `Firewall`. Any
   operation typed against `Firewall` runs against either kind of
   driver. White-box methods are reachable only when the test
   explicitly asks for the extended type.
2. **Loud, early failure.** A driver that can't do white-box
   implements just `Firewall` and is *not* type-compatible with
   `FirewallWhiteBox` — so a test typed against `FirewallWhiteBox`
   fails at the static gate or at `device_manager` registration, not
   mid-test.
3. **No fake stubs.** Drivers don't implement
   `get_kernel_iptables_dump` to raise `NotImplementedError` just to
   "satisfy" a fat Protocol — the extension Protocol doesn't apply at
   all to drivers that can't back it.
4. **Composes with the route convention.** Different routes can
   declare different levels — a UCI route always has kernel access,
   a TR-069 route never does. See [§L4c](#l4c--route-convention-default--alternative-transports)
   and the [worked example](#worked-example-cpe-gateway-firewall).

**Apply selectively.** Most capabilities don't need a white-box tier
— `NetemController`, `NtpClient`, `HwConsole`, `NmapScanner`,
`IpInterface`, `PcapCapture` are already at one natural level.
Add `<Capability>WhiteBox` only where the introspection methods have
meaningful debug value across ≥2 drivers and aren't already covered
by an adjacent capability. (`Conntrack` already plays the
introspection role for firewall flow inspection — don't add
`FirewallWhiteBox.dump_conntrack`.)

**Trigger conditions for adding a white-box tier:**

| Signal                                                                                  | Action                                                                                             |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| ≥2 tests want the same vendor-neutral debug method that's not in the standard Protocol | **Add** to `<Capability>WhiteBox`.                                                                 |
| Methods are vendor-specific (only one driver could ever implement them)                | **Don't add to commons.** Keep as a plugin-private narrow Protocol.                                |
| Methods exist in `<Capability>` already and "the test wants more detail"               | **Don't add.** Either improve the existing return shape or accept the test is grey-box.            |
| Black-box tests would break if a method was needed but missing                         | **Don't add to `<Capability>`.** Keep it WhiteBox so the test fails at the type gate, not at runtime. |

**Tracking.** New entries go in `packages/palco-protocols/LEVELS.md`
(date, capability, requested method, signal). Promotion from
plugin-private narrow Protocol to commons WhiteBox requires the same
≥2-consumer evidence as the granularity-split discipline.

**Graceful degradation (allowed but discouraged).** Because
`FirewallWhiteBox` is `@runtime_checkable`, code can branch:

```python
def deep_inspect_if_supported(fw: Firewall) -> str | None:
    if isinstance(fw, FirewallWhiteBox):
        return fw.get_kernel_iptables_dump()
    return None  # driver doesn't support white-box; skip
```

Allowed: it's straight Python and the runtime check is genuine.
**Discouraged**: tests should declare upfront what they need by
typing against the right level. Runtime branching obscures the
contract and lets a "white-box" assertion silently no-op when the
driver can't back it. Prefer the route-pinning path
(`cpe.uci.firewall.get_kernel_iptables_dump()`, where `UciRoute`
declares `firewall: FirewallWhiteBox`) over `isinstance` branching;
prefer scenario-level skips (`@pytest.mark.skip_if_no_whitebox`)
over silent no-ops.

#### White-box tier in the seed capability inventory

Updated working set marking which capabilities currently merit a
WhiteBox extension. The `<Capability>WhiteBox` Protocols are
*optional* additions in commons — drivers that don't back them simply
implement the standard `<Capability>` Protocol.

| Capability                                          | WhiteBox tier?                          | Rationale                                                                                                         |
| --------------------------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `Firewall`                                          | **Yes** — `FirewallWhiteBox`            | Kernel iptables, UCI raw config, fw4 state. High debug value across multiple driver types.                       |
| `Routing`                                           | **Yes** — `RoutingWhiteBox`             | FRR zebra RIB, vtysh passthrough, kernel route metrics, raw `ip rule` policy DB.                                  |
| `SipPhone`                                          | **Yes** — `SipPhoneWhiteBox`            | pjsua log tail, local SDP dump, RTCP stats. Useful when call setup fails for non-obvious reasons.                |
| `SipServer`                                         | **Yes** — `SipServerWhiteBox`           | Kamailio dispatcher state, registrar table dump, dialog list.                                                     |
| `Tr069Server`, `Tr069Client`                       | **Defer**                               | The standard surface (GPN/GPV/SPV/AddObject/DelObject) already covers introspection; revisit if a real test needs vendor-NBI internals. |
| `Nat`, `Conntrack`                                  | **No**                                  | `Conntrack` already plays the introspection role for `Nat`. Adding a NatWhiteBox would duplicate Conntrack's surface. |
| `NetemController`, `NtpClient`, `HwConsole`, `NmapScanner`, `IpInterface`, `PcapCapture`, `HttpClient`/`Server`, `FileTransfer`, `DeviceLifecycle`, `DeviceManagement` | **No** | Already at one natural level. Single-purpose; no meaningful "deeper" surface.                                     |

About 4 capabilities get a WhiteBox tier (4 extensions). Total
Protocol count: ~17 → ~21. Modest, and each addition is justified by
real debug surfaces.

### L4b — Device Protocols

`devices/` shifts from a *registry of `DeviceTypeSpec` records
listing classes to compose* to a set of *Protocol classes naming the
attributes a device must expose*. The names match today's
`device_type()` declarations one-to-one.

```python
# packages/palco-protocols/src/palco_protocols/devices/sdwan.py
from __future__ import annotations
from typing import Protocol, runtime_checkable

from palco_protocols.routing import Routing
from palco_protocols.sdwan_policy import SdwanPolicy
from palco_protocols.netem_controller import NetemController
from palco_protocols.ip_interface import IpInterface
from palco_protocols.pcap_capture import PcapCapture

@runtime_checkable
class LinuxSdwanRouter(Protocol):
    """Device protocol for a linux_sdwan_router."""

    routing:      Routing
    sdwan_policy: SdwanPolicy
    netem:        NetemController
    ip_interface: IpInterface
    pcap:         PcapCapture
```

Attribute names match the bundled capability protocols from the
[seed inventory](#capability-granularity-bundle-by-coherent-telco-domain-split-on-evidence).
This is the structural equivalent of today's:

```python
linux_sdwan_router = device_type(
    "linux_sdwan_router",
    bases=["LinuxDevice"],
    templates=[Router, SdwanPolicyManager, NetemController, IpInterface, PcapCapture],
)
```

Two pragmatic notes:

- **`bases=["LinuxDevice"]` does not become a Protocol.** The base is
  a mixin of communication facilities (SSH / pexpect / command
  execution); it stays an inheritance relationship in `palco-bases`.
  The device protocol describes *what attributes a device exposes*,
  not *how it talks*.
- **The `device_type()` registry survives** as a runtime table mapping
  type-string → device protocol class, so `device_manager` can check
  drivers against the right protocol at registration time. Its
  signature changes from `device_type(name, *, bases, templates)` to
  `device_type(name, protocol)`.

#### Where device protocols live: archetype-in-commons vs plugin-local

Device protocols are *much* cheaper than capability protocols — they
have no methods, just typed attribute declarations. They also do less
work: they narrow `device_manager.get_device(name)` return types,
drive the runtime registration `isinstance` gate, and document the
expected attribute shape. Operations consume *capability* protocols,
not device protocols. So the bloat risk of accumulating device
protocols in `palco-protocols` is real but manageable — and structural
typing means a plugin's local `MyTestbedCpe` automatically satisfies
commons' `LinuxCpe` if the shapes match (no inheritance needed).

The rule for **where a device protocol belongs** is three-tier:

| Tier                                              | Lives in                                                       | Examples                                                           | Promotion / demotion                                                                                                                                                                       |
| ------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **1 — Industry-standard archetype**               | `palco-protocols/devices/<archetype>.py`                       | `LinuxCpe`, `LinuxAcs`, `LinuxRouter`, `LinuxCmts`, `LinuxOlt`, `LinuxOnu`, `LinuxAp` | Always commons. These shapes are recognised across testbeds and standards bodies; declaring them once prevents N plugins reinventing the same attribute set.                               |
| **2 — Cross-testbed shape**                       | `palco-protocols/devices/<archetype>.py`                       | A shape that ≥2 example testbeds in this monorepo reuse exactly    | Promoted from a plugin to commons when a second consumer appears. Until then it stays in tier 3. Promotion is a `git mv` + import update; structural typing means existing drivers don't change. |
| **3 — Testbed-specific device shape**             | `<plugin>/protocols/<device>.py` (or inline in the driver module) | Anything bespoke to one example                                    | Plugin-owned. Plugins also call `device_type("my_cpe", MyTestbedCpe)` from their own `__init__.py` to register the type-string mapping with the same registry commons archetypes use.      |

**Promotion bar = a second consumer.** The bloat valve: a device
protocol stays in the plugin until *someone else* needs the same
shape. Until then, having three CPE plugins with three slightly-
different `Cpe` device protocols is *correct* — they're testbed-
specific and structural typing makes them interoperable where their
shapes overlap. Forcing premature commonality is what produces the
boardfarm-style monolith we're avoiding.

**Registration is unified.** Whether a device protocol lives in
commons or in a plugin, registration goes through the same
`palco_protocols.devices.device_type(name, protocol)` helper. Commons
archetypes are registered in commons' `__init__`; plugin device
protocols are registered in the plugin's `__init__`. The resulting
runtime registry is one dict; inventory configs reference whatever
type-string the plugin registered. Standard archetype strings
(`linux_cpe`, `linux_acs`, …) are reserved by `palco-protocols`.

**No "molecular" tier of role mixins.** An earlier sketch of this
design proposed `HasFirewall` / `HasRouting` mixin Protocols sitting
between capability protocols and device protocols. We rejected that:
under the [bundle-by-coherent-domain rule](#capability-granularity-bundle-by-coherent-telco-domain-split-on-evidence)
each capability protocol *is* the bundle the mixin would have wrapped,
so there's nothing left for a mixin tier to do. Two tiers
(capability → device), not three.

#### Capability levels in commons archetypes: black-box only

Commons device archetypes (`LinuxCpe`, `LinuxAcs`, `LinuxSdwanRouter`,
…) declare the **mandatory black-box tier** for capability attributes
— `firewall: Firewall`, never `firewall: FirewallWhiteBox`. The
reasoning ties back to the
[capability-levels rule](#capability-levels-black-box-mandatory--white-box-optional):
archetypes are broad-portability contracts. Many real driver
implementations can't expose deep introspection — locked-down vendor
images, RDK-B over CCSP, docker stubs, ACS-only management. Demanding
WhiteBox in the archetype would exclude all of them from satisfying
`LinuxCpe`, defeating the archetype's purpose.

**Three rules for placing the white-box tier in the type system:**

| Rule                                      | Where the WhiteBox-typed attribute lives                                                                                | Effect                                                                                                                                                                                                                                                                            |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Commons archetypes — black-box only** | `LinuxCpe.firewall: Firewall` (never `FirewallWhiteBox`)                                                                | Any driver implementing the standard surface satisfies the archetype. White-box-only methods are unreachable through the archetype-typed handle.                                                                                                                                  |
| **2. Route protocols — richer when guaranteed** | `UciRoute.firewall: FirewallWhiteBox` (UCI always has kernel access); `Tr069Route.firewall: Firewall` (TR-069 doesn't) | Tests pin the route to get the richer contract: `cpe.uci.firewall.get_kernel_iptables_dump()` is type-checked. Drivers without a `uci` route still satisfy `LinuxCpe` (black-box only).                                                                                          |
| **3. Plugin-local extended archetypes — narrower than commons** | `MyTestbedCpe(LinuxCpe, Protocol)` declaring `firewall: FirewallWhiteBox`                                              | When all drivers in a plugin guarantee white-box but the device isn't multi-transport. Plugin-private; promotes to commons (e.g. as `LinuxCpeFullAccess`) only when a second testbed needs the same shape, per the [scope rule](#where-device-protocols-live-archetype-in-commons-vs-plugin-local). |

The route-protocol path (rule 2) is the preferred mechanism. It
matches how white-box access naturally manifests in real systems —
attached to a transport, not to the device as a whole — and it lets a
single archetype serve drivers across the white/black-box spectrum
without forking it.

### L4c — Route convention: default + alternative transports

Many devices expose the same capability through multiple transports —
a CPE that lets you set firewall rules via UCI / `fw4` (local) *or* via
TR-069 (ACS-driven); an ACS that talks both REST NBI and a GUI; an
SD-WAN edge with a CLI and a NETCONF interface. Today this is handled
by **multiple compilation** — declaring the same template twice under
suffixed names (`packet_filter` + `packet_filter_tr069`,
`tr069_server` + `tr069_server_gui`, …). It works, but the suffix
convention scales poorly: every new capability that ships via two
transports adds two top-level attributes to the device, and a parity
test that wants to drive *every* available route ends up doing string
manipulation on attribute names.

The Protocol redesign promotes transport selection to a first-class
convention. The rules:

1. **Each transport-distinct route is a sub-namespace on the device.**
   Use a stable, lowercase, transport-identifying name:
   `tr069`, `uci`, `cli`, `api`, `gui`, `netconf`, `serial`, …. These
   names are part of the public surface — feature files and step defs
   reference them — so a plugin must not rename them on a whim.
2. **Each route is a small object whose attributes are
   capability-Protocol typed.** A route exposes only the capabilities
   it can actually drive; capabilities the route does not support are
   simply absent from that route's attribute set. (Missing capability
   on a route = `AttributeError`. This is the natural failure mode and
   is checked by tests.)
3. **The device root carries a *default route* by aliasing selected
   capabilities to one route.** `device.packet_filter` is then
   `device.<default_route>.packet_filter`. The default route is
   declared per device-type and is part of the device-type's
   contract — it is the route a test gets when it does not pin one.
4. **Per-device-type Protocol declares the route attributes it
   guarantees.** `LinuxCpe` declares `tr069: Tr069Route` and
   `uci: UciRoute` (each typed against its own per-route Protocol);
   `device_manager` checks at registration that every declared route
   exists.
5. **Routes are discoverable.** Each device class exposes
   `routes: ClassVar[tuple[str, ...]]` — a tuple of the route names
   that exist on instances of that class. Parity tests iterate this
   tuple to drive every route without hard-coding names.
6. **Routes are not required to be exhaustive.** A driver may expose
   only `uci` if the device has no other transport. Tests that depend
   on a specific route fail loudly when the route is absent — this is
   intentional, because portability has limits and "this scenario
   needs TR-069" is a meaningful precondition.

#### Type shape

```python
# packages/palco-protocols/src/palco_protocols/devices/cpe.py
from typing import Protocol, runtime_checkable
from palco_protocols.packet_filter import PacketFilter
from palco_protocols.port_forwarding import PortForwarding

@runtime_checkable
class UciRoute(Protocol):
    """Capabilities reachable via UCI / fw4 (local config plane)."""
    packet_filter: PacketFilter
    port_forwarding: PortForwarding

@runtime_checkable
class Tr069Route(Protocol):
    """Capabilities reachable via TR-069 (ACS-driven config plane).

    Subset of UciRoute — firewall_zones is intentionally absent if the
    prplOS image does not expose Device.Firewall.Chain.{i}.
    """
    packet_filter: PacketFilter
    port_forwarding: PortForwarding

@runtime_checkable
class LinuxCpe(Protocol):
    """Device protocol for a Linux-based CPE.

    Declares both the *default-route attributes* (packet_filter,
    port_forwarding) and the *route sub-namespaces* (uci, tr069).
    """
    # Default-route attributes (alias to the device's default route)
    packet_filter: PacketFilter
    port_forwarding: PortForwarding
    # Route sub-namespaces
    uci: UciRoute
    tr069: Tr069Route
```

#### Driver shape

```python
class RpiPrplosCpe(LinuxDevice):
    device_type = "linux_cpe"
    routes = ("uci", "tr069")              # discoverable, ordered
    default_route = "uci"

    def __init__(self, config, cmdline_args):
        super().__init__(config, cmdline_args)
        self.uci   = _UciImpls(self)
        self.tr069 = _Tr069Impls(self)
        # Default-route aliasing — single source of truth: default_route
        default = getattr(self, self.default_route)
        self.packet_filter   = default.packet_filter
        self.port_forwarding = default.port_forwarding
```

#### Call-site shape

```python
# Default route — terse
device.packet_filter.add_rule(chain, rule)

# Pinned route — explicit
device.tr069.packet_filter.add_rule(chain, rule)

# Parity over all routes — driven by the discovered tuple
for route_name in device.routes:
    getattr(device, route_name).packet_filter.add_rule(chain, rule)
```

The route is a structural shape, so step defs that take a
`PacketFilter`-typed argument accept either `device.packet_filter`
or `device.tr069.packet_filter` — the type checker confirms; the
runtime call dispatches identically. This is what makes objective #3
("default + opt-in alternatives") a thin convention rather than a
parallel API.

This also generalises the demo's `special_test(device_ut=device.gui, ...)`
pattern: the demo's `_Gui` and `_Api` sub-objects *are* route
sub-namespaces; what the demo calls "structurally satisfies the device
protocol" is what this section calls "is itself typed as a route
Protocol that overlaps the device protocol's capability set".

### L5 — Implementation bases (unchanged)

`palco-bases.linux_device.LinuxDevice` keeps its current responsibility:
SSH / serial / `local_cmd` connections, `pexpect` plumbing, command
execution, prompt handling. It remains a concrete (non-protocol) class
that drivers inherit from. Protocols describe the *capability* surface;
the implementation base describes *how to talk to the device*.

The `IptablesHelper` parser helper (renamed from `IptablesFirewall`
in commit `90b8f75`) stays where it is.

### L6 — Device drivers (testbed plugins)

Drivers shed the inner-class boilerplate. Two equally-valid patterns:

**Pattern A — Composition root.** Keep nested classes if the
implementation is small and the back-reference is convenient:

```python
class FrrSdwanRouter(LinuxDevice):
    device_type = "linux_sdwan_router"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        outer = self
        class _RouterImpl:
            def get_active_wan_interface(self_inner) -> str:
                return outer.execute_command("ip route show default | head -1").split()[4]
            def bring_wan_down(self_inner, label):
                outer.execute_command(f"ip link set {outer._config['wan_interfaces'][label]} down")

        self.router = _RouterImpl()
        self.sdwan_policy = _SdwanPolicyImpl(self)
        self.netem = _NetemImpl(self)
        self.ip_interface = _IpInterfaceImpl(self)
        self.pcap = _PcapCaptureImpl(self)
```

**Pattern B — Standalone classes.** Best when the implementation is
large enough to warrant its own module:

```python
# my_plugin/impls/router_frr.py
class FrrRouter:
    def __init__(self, device): self._device = device
    def get_active_wan_interface(self) -> str: ...
    def bring_wan_down(self, label: str) -> None: ...
    # ...

# my_plugin/devices/frr_sdwan_router.py
class FrrSdwanRouter(LinuxDevice):
    device_type = "linux_sdwan_router"
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.router = FrrRouter(self)
        self.sdwan_policy = FrrSdwanPolicy(self)
        self.netem = TcNetem(self)
        self.ip_interface = LinuxIpInterface(self)
        self.pcap = TcpdumpCapture(self)
```

Both patterns produce an object that **structurally** matches
`LinuxSdwanRouter`. There is no `class router(Router)` ABC inheritance
in either. The static type checker confirms the shape; the runtime
check (next section) confirms it again at registration.

### Runtime safety

ABCs fail loudly at instantiation when a method is missing. Protocols
do not. To preserve the loud-failure guarantee we add **two gates**:

1. **Static gate (CI).** `mypy` and / or `pyright` runs on every
   testbed plugin against the `palco-protocols` Protocol surface.
   Missing methods, wrong signatures, and wrong return types are
   caught here. This gate **must** be wired into testbed-plugin CI
   pipelines for the design to remain safe.
2. **Runtime gate (registration).** When `device_manager` registers
   a driver instance for a `device_type` string, it looks up the
   matching device protocol from the registry and runs an
   `isinstance(driver, DeviceProtocol)` check. Missing attributes
   raise immediately with a clear message naming the missing
   attribute, the device protocol it violates, and the driver class.
   `@runtime_checkable` Protocols only verify attribute *existence*,
   not signatures — but combined with the static gate this is enough
   to keep the loud-failure invariant.

```python
# Inside device_manager (palco / palco-bases) — pseudocode
from palco_protocols.devices import get_device_type

def _verify_driver(driver, type_string: str) -> None:
    proto = get_device_type(type_string)
    if proto is None:
        raise UnknownDeviceType(type_string)
    if not isinstance(driver, proto):
        missing = [
            name for name in proto.__protocol_attrs__   # introspection helper
            if not hasattr(driver, name)
        ]
        raise DriverContractViolation(
            f"{type(driver).__name__} declares device_type={type_string!r} "
            f"but does not satisfy {proto.__name__} — missing attributes: {missing}"
        )
```

### Operations

Operations stay pure functions in `palco-operations`, accepting
resolved template / protocol instances and orchestrating across them.
Type annotations narrow to the *minimum* protocols a function actually
needs:

```python
# packages/palco-operations/src/palco_operations/sdwan.py
from __future__ import annotations
from palco_protocols.netem_controller import NetemController
from palco_protocols.router import Router

def measure_failover_convergence(
    netem: NetemController,
    router: Router,
    impaired_wan: str,
    timeout_ms: int = 5000,
) -> float:
    """Inject blackout and measure path switch time."""
    netem.inject_transient("blackout", timeout_ms)
    start = time.monotonic()
    while (time.monotonic() - start) * 1000 < timeout_ms:
        if router.get_active_wan_interface() != impaired_wan:
            return (time.monotonic() - start) * 1000
        time.sleep(0.05)
    raise TimeoutError("path did not switch")
```

The function signature *was* `def measure_failover_convergence(netem:
NetemController, router: Router, ...)` against ABCs and *is* the same
function signature against Protocols. The migration is invisible to
operation authors and to step-definition authors.

### Step definitions

Step definitions remain the resolution layer — they translate Gherkin
context into resolved template instances and pass them to operations.
The *only* concrete improvement under Protocols is editor support: a
step definition that writes `dev.router.get_active_wan_interface()`
gets full autocompletion / type-checking once `dev`'s type is
narrowed to a device protocol via the `device_manager.get_device`
return-type annotation.

```python
@when('"{edge}" experiences a complete link failure on "{wan}"')
def step_link_failure(device_manager, edge, wan):
    dev: LinuxSdwanRouter = device_manager.get_device(edge)  # narrowed
    dev.router.bring_wan_down(wan)

@then('"{edge}" converges to "{wan}" within {ms:d} ms')
def step_convergence(device_manager, edge, wan, ms):
    edge_dev: LinuxSdwanRouter        = device_manager.get_device(edge)
    tc_dev:   LinuxTrafficController  = device_manager.get_device("wan1_tc")
    elapsed = sdwan.measure_failover_convergence(
        tc_dev.netem, edge_dev.router, "wan1", ms,
    )
    assert elapsed <= ms
```

`device_manager.get_device(name)` returns a `PalcoDevice`-typed object
in the framework today; the testbed repo's conftest can introduce a
narrower typed wrapper (or a `Generic` helper) without changing
`palco`'s contract.

### Data Model

No data-model changes. `palco_protocols.models.*` dataclasses are
returned by Protocol methods exactly as they are returned by ABC
methods today. The dataclasses themselves do not become Protocols —
they describe values, not capabilities.

### API Changes

Public API surface changes summarised. Two orthogonal changes —
**package rename** (`palco-templates` → `palco-protocols`,
`palco_templates` → `palco_protocols`, `device_types/` → `devices/`)
and **contract mechanism** (ABC → Protocol). They land together in a
single coordinated PR; there is no compatibility alias.

| Surface | Today | After |
|---------|-------|-------|
| Package distribution name | `palco-templates` | `palco-protocols` |
| Python import package | `palco_templates` | `palco_protocols` |
| Capability contracts (per domain-role) | `palco_templates.<domain>.<Template>` — `class X(Template, ABC): ...` | `palco_protocols.<domain>.<X>` — `class X(Protocol): ...` (decorated `@runtime_checkable`) |
| Capability contract base | `palco_templates._template.Template` (ABC with `_device` back-reference) | **Removed** — back-reference is the driver's implementation detail |
| Device-type recipes / aggregates | `palco_templates.device_types.<linux_xxx>` — `DeviceTypeSpec` instance built by `device_type(name, *, bases, templates)` | `palco_protocols.devices.<linux_xxx>` — `Protocol` class registered via `device_type(name, protocol)` |
| Route sub-namespaces (multi-transport devices) | Suffixed top-level attributes: `device.tr069_server`, `device.tr069_server_gui` | Sub-namespaces: `device.api.tr069_server`, `device.gui.tr069_server`, with `device.tr069_server` aliasing `device.<default_route>.tr069_server` |
| Driver capability composition | Inner classes inheriting ABCs: `class router(Router): ...` | Plain attribute assignment in `__init__`: `self.router = _RouterImpl(self)` |
| Driver registration check | ABC instantiation (raises if abstract methods missing) | `isinstance(driver, DeviceProtocol)` at `device_manager.register_device(...)`, plus mypy / pyright in CI |
| Operations parameter types | `palco_operations.<m>.<fn>(t1: T1Abc, ...)` | `palco_operations.<m>.<fn>(t1: T1Protocol, ...)` — same signature text, narrower meaning |
| `palco_add_devices` hookimpl | Returns `dict[str, type[Device]]` | Same — unchanged |
| `device_manager.get_device(name)` | Returns `PalcoDevice` | Same — testbed conftest may narrow with `cast` to a device protocol |
| Models (`palco_*.models.*`) | Dataclasses | Same — unchanged role; just live under `palco_protocols.models` now |

### Key Interactions

#### Bringing up a device — registration & verification

```
1. Palco reads inventory.json + environment.json, merges configs per
   device name, and looks up the driver class via palco_add_devices.
2. Palco instantiates the driver:    driver = MyDriver(config, args)
3. The driver's __init__ assigns its template attributes
   (self.router = ...; self.netem = ...; etc.).
4. device_manager looks up the device protocol for the configured
   device_type string and runs isinstance(driver, DeviceProtocol).
5. On success, driver is registered. On failure, DriverContractViolation
   is raised, naming the missing attributes.
```

#### A test step calling an operation

```
1. Step def receives device_manager and Gherkin params.
2. Step def resolves devices by name. The conftest typing makes
   dev a (narrowed) device-protocol type.
3. Step def passes dev.router and dev.netem (typed as Router and
   NetemController capability protocols) to the operation.
4. Operation calls only the methods declared on those capability
   protocols. Static type-check confirms; runtime call dispatches
   to the driver's plain attributes.
5. Operation returns; step def asserts.
```

#### Route selection (default + alternative transports)

```
1. Driver __init__ assigns route sub-namespaces and the default-route
   aliases:
       self.uci   = _UciImpls(self)
       self.tr069 = _Tr069Impls(self)
       default = getattr(self, self.default_route)   # default_route = "uci"
       self.firewall = default.firewall
2. Step def reads the route qualifier from Gherkin (defaulting to None
   when the scenario does not pin a route):
       target = dev if route is None else getattr(dev, route)
3. Step def calls target.firewall.add_rule(chain, rule). When route
   is None the call dispatches via the default-route alias; when
   route="tr069" the call dispatches via the tr069 sub-namespace.
4. Parity tests iterate dev.routes:
       for r in dev.routes:
           getattr(dev, r).firewall.add_rule(chain, rule)
```

## Worked example: cpe-gateway-firewall

The `cpe-gateway-firewall` example
([2026-04-29-cpe-gateway-firewall-design.md](../../palco-bdd/docs/superpowers/specs/2026-04-29-cpe-gateway-firewall-design.md))
is the most demanding test case for both the route convention and the
[bundle-by-coherent-domain capability rule](#capability-granularity-bundle-by-coherent-telco-domain-split-on-evidence):
a CPE drives its firewall through two different transports (UCI /
`fw4` locally, TR-069 via an ACS), and one of its UCs (UC-CPE-FW-04)
asserts that a rule applied via either route is observable on the
other. This section walks the same example in both the current ABC
shape and the Protocol shape so the contrast is explicit.

### Capability protocols (palco-protocols)

This is also where the granularity rule visibly cashes out. Today's
ABC design splits the firewall surface across **five** templates
(`PacketFilter`, `PortForwarding`, `FirewallZones`, `Nat`,
`Conntrack`). The Protocol redesign collapses the three rule-
management concerns into one bundled `Firewall` capability — they
share a UCI section, a TR-181 subtree, and an admin mental model —
while keeping `Nat` and `Conntrack` separate per the seed inventory's
split rule (TR-181 splits NAT; conntrack is read-mostly observability).

```python
# Today (5 ABCs)
class PacketFilter(Template, ABC):
    @abstractmethod
    def add_rule(self, chain: str, rule: FirewallRule, ...) -> None: ...
    @abstractmethod
    def list_rules(self, chain: str) -> list[FirewallRule]: ...
    # ...
class PortForwarding(Template, ABC):
    @abstractmethod
    def add_port_mapping(self, mapping: PortMapping) -> None: ...
    # ...
class FirewallZones(Template, ABC): ...
class Nat(Template, ABC): ...
class Conntrack(Template, ABC): ...
```

```python
# After (3 Protocols — bundled by coherent telco domain)
@runtime_checkable
class Firewall(Protocol):
    """Packet rules + port forwards + zones — one config domain."""
    # Packet-filter surface
    def add_rule(self, chain: str, rule: FirewallRule, position: int | None = None) -> None: ...
    def list_rules(self, chain: str) -> list[FirewallRule]: ...
    def remove_rule(self, chain: str, name: str) -> None: ...
    def set_default_policy(self, chain: str, policy: str) -> None: ...
    def get_default_policy(self, chain: str) -> str: ...
    # Port-forwarding surface
    def add_port_mapping(self, mapping: PortMapping) -> None: ...
    def list_port_mappings(self) -> list[PortMapping]: ...
    def remove_port_mapping(self, name: str) -> None: ...
    # Zone surface
    def list_zones(self) -> list[Zone]: ...
    def get_zone_policy(self, zone: str) -> ZonePolicy: ...
    # ... full bundled surface ...

@runtime_checkable
class Nat(Protocol):
    def add_nat_rule(self, rule: NatRule) -> None: ...
    def list_nat_rules(self, mode: str | None = None) -> list[NatRule]: ...
    # ...

@runtime_checkable
class Conntrack(Protocol):
    def get_stats(self) -> ConntrackStats: ...
    def list_connections(self, **filters) -> list[Connection]: ...
    # ...
```

No model changes; `FirewallRule`, `PortMapping`, `Zone`, `ZonePolicy`,
`NatRule`, `Connection`, `ConntrackStats` remain dataclasses imported
by the protocols that return / accept them. A driver that genuinely
cannot implement one method of `Firewall` (e.g. an image without zone
support) raises `NotImplementedError` from that one method per the
[partial-implementation rule](#capability-granularity-bundle-by-coherent-telco-domain-split-on-evidence) —
two such drivers in `SPLITS.md` would justify carving zones back out.

### Device protocol & route protocols

The current design's `linux_cpe` device-type spec lists templates to
compose:

```python
# Today
linux_cpe = device_type(
    "linux_cpe",
    bases=["LinuxDevice"],
    templates=[
        PacketFilter, PortForwarding, FirewallZones, Nat, Conntrack,
        Tr069Client, DeviceManagement, DeviceLifecycle, IpInterface,
        IpRouting, NtpClient, HwConsole,
    ],
)
```

Under Protocols this becomes a device Protocol that names *both* the
default-route attributes *and* the route sub-namespaces. Where the
five firewall templates contributed five attributes, the bundled
`Firewall` capability contributes one:

```python
# packages/palco-protocols/src/palco_protocols/devices/cpe.py

@runtime_checkable
class UciRoute(Protocol):
    """Capabilities reachable via UCI / fw4 (local config plane).

    Declares FirewallWhiteBox because UCI access on a Linux CPE
    structurally implies kernel-level introspection (we own the box,
    we can read /proc, /sys, iptables -S, fw4 internals). Drivers
    satisfying this route therefore commit to providing the white-box
    methods.
    """
    firewall: FirewallWhiteBox

@runtime_checkable
class Tr069Route(Protocol):
    """Capabilities reachable via TR-069 / ACS NBI.

    Black-box only — TR-069 NBI is a remote management plane that
    exposes only what the data model declares. No kernel access, no
    raw config dumps. Drivers satisfying this route commit only to
    the standard Firewall surface.

    Individual standard-surface methods may still raise
    NotImplementedError if the prplOS image's TR-181 subtree omits
    them (e.g. zone management on minimal builds) — that's a
    per-method gap inside the standard contract, not a level
    difference.
    """
    firewall: Firewall

@runtime_checkable
class LinuxCpe(Protocol):
    """linux_cpe device protocol — industry-standard archetype, lives in commons.

    Per the level rule (§L4b — Capability levels in commons archetypes:
    black-box only), the default-route attribute is typed against the
    mandatory Firewall, not FirewallWhiteBox. Drivers that can do
    white-box advertise it via their route protocols (here: UciRoute);
    drivers that can't (docker stubs, RDK-B-only, TR-069-only) still
    satisfy LinuxCpe.
    """
    # Default-route attribute — aliases the configured default route's firewall
    firewall: Firewall          # ← black-box only at the archetype level

    # Route sub-namespaces — may declare richer levels per route
    uci:   UciRoute             # ← UciRoute.firewall: FirewallWhiteBox
    tr069: Tr069Route           # ← Tr069Route.firewall: Firewall

    # Single-route capabilities (no transport variants)
    nat:          Nat
    conntrack:    Conntrack
    lifecycle:    DeviceLifecycle
    management:   DeviceManagement
    ip_interface: IpInterface
    routing:      Routing
    tr069_client: Tr069Client
    ntp_client:   NtpClient
    hw_console:   HwConsole
```

`LinuxCpe` is a tier-1 industry-standard archetype per
[§L4b — device protocol scope](#where-device-protocols-live-archetype-in-commons-vs-plugin-local),
so it lives in commons. A second-vendor CPE driver (e.g. an OpenWrt
build instead of prplOS) satisfies the same `LinuxCpe` Protocol
structurally — no inheritance edge needed. A docker-stub CPE that
can't back the `uci` route at all still satisfies `LinuxCpe` (no
white-box guarantee at the archetype level), and white-box scenarios
skip on it via type-gate failure when they try to access
`cpe.uci.firewall.get_kernel_iptables_dump()`.

### Driver — current shape (ABC, multiple compilation by suffix)

The cpe-gateway-firewall design (§5.1) compiles each firewall template
twice under transport-suffixed names. With five firewall templates,
that produces a lot of inner-class scaffolding:

```python
class RpiPrplosCpe(LinuxDevice):
    device_type = "linux_cpe"

    # Default transport — UCI / fw4 (5 inner classes)
    class packet_filter(PacketFilter): ...
    class port_forwarding(PortForwarding): ...
    class firewall_zones(FirewallZones): ...
    class nat(Nat): ...
    class conntrack(Conntrack): ...

    # Alternative transport — TR-069 (3 more, suffixed)
    class packet_filter_tr069(PacketFilter): ...
    class port_forwarding_tr069(PortForwarding): ...
    # firewall_zones_tr069 omitted — no TR-181 backing
    # nat / conntrack — single-transport, no _tr069 variant
```

Eight inner classes for the firewall surface alone, plus seven more
top-level `device.<name>` attributes the test author has to keep
straight (`packet_filter`, `port_forwarding`, `firewall_zones`,
`packet_filter_tr069`, `port_forwarding_tr069`, `nat`, `conntrack`).

### Driver — Protocol shape (route convention + bundled capability)

Same driver. Three protocols, one inner impl per route, one default-
route alias:

```python
class _UciImpls:
    """UCI / fw4 route — local config plane."""
    def __init__(self, device: "RpiPrplosCpe") -> None:
        self.firewall = _FirewallUci(device)

class _Tr069Impls:
    """TR-069 route — ACS-driven config plane."""
    def __init__(self, device: "RpiPrplosCpe") -> None:
        self.firewall = _FirewallTr069(device)

class RpiPrplosCpe(LinuxDevice):
    device_type   = "linux_cpe"
    routes        = ("uci", "tr069")
    default_route = "uci"

    def __init__(self, config, cmdline_args):
        super().__init__(config, cmdline_args)
        self.uci   = _UciImpls(self)
        self.tr069 = _Tr069Impls(self)

        # Single-route capabilities (no transport variants)
        self.nat          = _NatImpl(self)
        self.conntrack    = _ConntrackImpl(self)
        self.lifecycle    = _LifecycleImpl(self)
        self.management   = _ManagementImpl(self)
        self.ip_interface = _IpInterfaceImpl(self)
        self.routing      = _RoutingImpl(self)
        self.tr069_client = _Tr069ClientImpl(self)
        self.ntp_client   = _NtpClientImpl(self)
        self.hw_console   = _HwConsoleImpl(self)

        # Default-route alias — single source of truth: default_route
        default = getattr(self, self.default_route)
        self.firewall = default.firewall

    @hookimpl
    def palco_device_boot(self, config, cmdline_args, device_manager):
        self._connect()
        # Wire ACS reference into Tr069 route impls that need it
        self._acs    = device_manager.get_device_by_type(Tr069Server)
        self._cwmp_id = config["cwmp_device_id"]
```

`_FirewallUci` and `_FirewallTr069` are plain classes whose method set
is the union of the three former templates (`add_rule`,
`add_port_mapping`, `list_zones`, …) — they take the device in
`__init__` and dispatch each method to the right UCI command or ACS
RPC. `_FirewallTr069` may raise `NotImplementedError` from
`list_zones` / `get_zone_policy` if the prplOS image's TR-181 surface
doesn't back zones; that's a per-method gap, not a missing protocol.

### Step definitions — transport selection

Compare the two shapes side by side. The Gherkin is identical.

```gherkin
Scenario Outline: Operator opens an inbound port forward
  Given a LAN host runs an HTTP service on port 80
  When the operator adds a port forward "lan_http" via <route>
  Then a WAN client can reach the LAN service on the CPE's WAN IP
  And the rule is observable on the CPE via <route>
  When the operator removes the port forward "lan_http" via <route>
  Then the WAN client cannot reach the LAN service

  Examples:
    | route |
    | uci   |
    | tr069 |
```

```python
# Today — string-suffix dispatch on top-level attributes
@when('the operator adds a port forward "{name}" via {route}')
def step_add_port_forward(device_manager, bf_context, name, route):
    cpe = device_manager.get_device_by_type(PortForwarding)
    ns  = "port_forwarding" if route == "uci" else "port_forwarding_tr069"
    pf: PortForwarding = getattr(cpe, ns)
    pf.add_port_mapping(_make_mapping(name, bf_context))
    bf_context.applied_via = ns
```

```python
# After — route is a sub-namespace; default falls through the device root
@when('the operator adds a port forward "{name}" via {route}')
def step_add_port_forward(device_manager, bf_context, name, route):
    cpe: LinuxCpe = device_manager.get_device(bf_context.cpe_name)
    target: Firewall = (
        cpe.firewall                            # default route
        if route in (None, cpe.default_route)
        else getattr(cpe, route).firewall       # pinned route
    )
    target.add_port_mapping(_make_mapping(name, bf_context))
    bf_context.applied_via = route or cpe.default_route
```

The Protocol form has three concrete improvements:
- The step does not encode the suffix-string convention. Adding a
  third route (e.g. `netconf`) requires no step-def change — only the
  feature-file Examples table grows.
- The type checker narrows `target` to `Firewall`, so calls to
  `add_rule`, `add_port_mapping`, `list_zones`, etc. are all valid and
  type-checked under one variable. A typo like `add_port_mappng` is
  caught statically.
- One bundled `Firewall` capability replaces three (`PacketFilter` +
  `PortForwarding` + `FirewallZones`) at the call site. Step authors
  reach for `cpe.firewall.<method>` regardless of which UCI section
  the rule maps to.

### Cross-route parity (UC-CPE-FW-04)

The hardest UC in the example is the parity assertion — a rule applied
via one route is observable via the other. The current shape pairs
suffixed attributes manually:

```python
# Today
remote: PortForwarding = cpe.port_forwarding_tr069
local:  PortForwarding = cpe.port_forwarding         # implicit "uci"
remote.add_port_mapping(mapping)
seen = local.list_port_mappings()
assert any(m == mapping for m in seen)
```

Under the route convention + bundled `Firewall`, the same scenario
reads as a routes-cross-product, with no string surgery and one
capability instead of three:

```python
# After — both routes addressable, default route still ergonomic
remote: Firewall = cpe.tr069.firewall
local:  Firewall = cpe.uci.firewall
remote.add_port_mapping(mapping)
seen = local.list_port_mappings()
assert any(m == mapping for m in seen)

# … or, generically, every (apply_route, read_route) pair:
for apply_route in cpe.routes:
    for read_route in cpe.routes:
        if apply_route == read_route:
            continue
        getattr(cpe, apply_route).firewall.add_port_mapping(mapping)
        seen = getattr(cpe, read_route).firewall.list_port_mappings()
        assert any(m == mapping for m in seen)
        getattr(cpe, apply_route).firewall.remove_port_mapping(mapping.name)
```

This is the convention earning its keep on its hardest case: the
parity claim becomes a dimension of the routes tuple, not a manually
maintained pair of attribute names.

### White-box variant of UC-CPE-FW-04

The standard parity scenario (above) is grey-box — it asserts that
both routes report the same canonical `PortMapping`. A complementary
**white-box variant** asserts a stronger claim: the rule observable
via UCI also exists in the **kernel iptables table** that fw4
generates, with no orphan rules left behind. This catches a class of
bugs the grey-box assertion misses (UCI says "rule applied"; fw4
silently failed to reload; kernel state is stale).

The white-box variant pins the UCI route to access
`FirewallWhiteBox.get_kernel_iptables_dump()`:

```python
# White-box variant — types against FirewallWhiteBox
remote: Firewall          = cpe.tr069.firewall   # standard surface
local:  FirewallWhiteBox  = cpe.uci.firewall     # ↑ richer type from UciRoute

remote.add_port_mapping(mapping)

# Standard readback (parity)
seen = local.list_port_mappings()
assert any(m == mapping for m in seen)

# White-box readback (additional invariant: kernel state matches)
ipt_dump = local.get_kernel_iptables_dump()
assert _expected_dnat_line(mapping) in ipt_dump, \
    "TR-069-applied rule not visible in kernel iptables — fw4 reload failed?"
```

Two type-system properties make this safe:

1. **The static gate enforces white-box availability.** `local`'s
   declared type is `FirewallWhiteBox`. If a driver's `uci` route
   only satisfies `Firewall` (no kernel access), the assignment fails
   at registration / static-check time — the test cannot run against
   that driver, no silent no-ops.
2. **The grey-box scenario still runs against every driver.** Its
   types stay at `Firewall`, so any conforming `LinuxCpe` driver —
   including thin / docker / TR-069-only stubs — exercises it.

In feature-file terms, this lands as a separate scenario marked with
a tag the runner uses to gate execution against driver capability
classes:

```gherkin
@white_box
Scenario: UC-CPE-FW-04-WB: cross-route parity also matches kernel iptables
  When a port forward "kernel_check" is added via tr069
  Then the rule is observable on the CPE via uci
  And the kernel iptables DNAT chain contains the rule
```

`@white_box` scenarios are skipped at collection time on testbeds
whose driver registration declares no white-box route; on the prplOS
RPi (which satisfies `UciRoute` with `firewall: FirewallWhiteBox`)
they run.

### Mapping back to objectives

| Objective | How this example demonstrates it |
|-----------|----------------------------------|
| **1 — Standardize APIs** | `Firewall`, `Nat`, `Conntrack`, `Routing`, etc. are unchanged across cpe-gateway-firewall, sip-telephony, and sdwan-digital-twin. A step def written against `Firewall` works against any driver in any plugin that exposes one. `LinuxCpe` is the tier-1 archetype; future CPE drivers (OpenWrt, RDK-B, docker) satisfy it structurally. |
| **2 — Lean plugin authoring** | `RpiPrplosCpe.__init__` is plain attribute assignment. The bundled `Firewall` Protocol collapses three former inner classes into one impl per route. No inner ABCs, no `Template` base, no `class packet_filter(PacketFilter):` ceremony. Eight firewall inner classes today → two route-scoped `_FirewallUci`/`_FirewallTr069` classes after. |
| **3 — Default + opt-in routes** | `device.firewall.add_rule(...)` resolves to the default (UCI) route. `device.tr069.firewall.add_rule(...)` pins TR-069. `for r in device.routes:` iterates every route a driver provides. The convention is one rule, not a per-driver naming scheme. |
| **Granularity discipline** | The cpe-gateway-firewall design's original five firewall templates are bundled to one `Firewall` per the bundle-by-coherent-domain rule, and `Nat` / `Conntrack` are kept separate by that same rule. Future evidence (≥2 drivers raising `NotImplementedError` on the same method group) tracked in `SPLITS.md` would justify carving methods back out. |
| **Black-box vs white-box levels** | `LinuxCpe.firewall: Firewall` keeps the archetype broad (any conforming driver satisfies it). `UciRoute.firewall: FirewallWhiteBox` declares the richer contract on the route that always supports it. The standard parity scenario runs anywhere; the `@white_box` parity variant runs only against drivers whose UCI route satisfies `FirewallWhiteBox`. The level distinction is enforced at the type gate, not via runtime branching. |

## Alternatives Considered

### Alternative 1 — Keep ABCs; do nothing

Status quo. Cost is the recurring boilerplate (every driver, every
template, every multiple-compilation case) and the structural mismatch
between "namespace composition" (the design's intent) and "ABC
inheritance" (the mechanism implementing it).

Rejected because the mechanism is heavier than the intent. The demo
demonstrates that the intent is expressible without the mechanism.

### Alternative 2 — Keep ABCs; type operations against `typing.Protocol` parameter types

Hybrid: ABCs survive on the contract surface, but operations type
against narrow Protocols structurally satisfied by the ABCs. This is a
known mypy / pyright pattern.

Rejected because it adds a *parallel* hierarchy (one Protocol per ABC)
while leaving the original boilerplate intact. The fix to "I want
Protocol-style type hints in operations" is at the wrong layer.

### Alternative 3 — Replace ABCs with Protocols, but keep the `Template` base class as a `Protocol` of `_device`

A Protocol with a `_device: Any` attribute, inherited by every
capability protocol. Captures today's "every template implementation
holds a `_device` back-reference" invariant.

Rejected because the back-reference is an *implementation detail* of
how a driver wants to talk to itself. Some drivers (Pattern A above)
keep it; some (Pattern B) take the device in `__init__`. Encoding the
back-reference into the contract leaks driver-internal organization
into the public surface.

### Alternative 4 — Adopt `attrs` / `dataclasses` + `Protocol`s simultaneously

Use `attrs`-decorated classes for the driver shells (auto-generates
`__init__`) and Protocols for the contracts. Considered cosmetically
attractive.

Rejected as out-of-scope. Drivers that want `attrs` can opt in;
forcing a framework-level decorator choice on every plugin would be
disruptive without enabling anything Protocols don't already.

## Trade-offs and Risks

| Concern                                                                                                                                                                    | Impact                                                                                                  | Mitigation                                                                                                                                                                                                                                                 |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Loss of ABC instantiation-time enforcement.** Drivers missing a method don't fail at construction; they fail at first call.                                              | A driver missing `Router.get_active_wan_interface` would silently boot, then `AttributeError` mid-test. | (a) `isinstance(driver, DeviceProtocol)` runtime gate at `device_manager` registration. (b) `mypy` / `pyright` CI gate on every testbed plugin. Both gates **must** be in place.                                                                           |
| **`@runtime_checkable` Protocols don't check method signatures.** A driver could provide `get_active_wan_interface(self, x, y)` instead of `(self)` and pass `isinstance`. | Would break at first call; static gate catches it earlier.                                              | Static gate (mypy / pyright) is non-optional. Document this in plugin templates.                                                                                                                                                                           |
| **`_template.py`'s `Template` ABC base disappears, removing `_device` back-reference convention.** Drivers using Pattern A had `_device` for free.                         | Pattern-A drivers must wire the back-reference manually (one line per impl, see §L6).                   | The architecture spec amendment documents both patterns and recommends Pattern B for non-trivial implementations.                                                                                                                                          |
| **`device_type()` registry signature change** — `bases=` and `templates=` kwargs are gone.                                                                                 | Anyone holding a reference to `DeviceTypeSpec` records breaks.                                          | Internal API only (no external consumers in current palco-bdd / palco-commons tree). One-shot migration.                                                                                                                                                   |
| **`isinstance(obj, RuntimeCheckableProtocol)` is slow on hot paths.**                                                                                                      | Performance impact if used per call.                                                                    | Use only at registration time and in tests. Operations and step definitions never `isinstance`-check protocols.                                                                                                                                            |
| **Cyclic-import risk.** Device protocols import capability protocols which import models.                                                                                  | Same as today, no worse.                                                                                | Existing `from __future__ import annotations` discipline is preserved; protocol annotations are forward references.                                                                                                                                        |
| **Migration window.** Splitting the change across multiple PRs invites a half-Protocol, half-ABC repository, or a state where some imports point at `palco_templates` and others at `palco_protocols`. | Confusion + double-maintenance.                                                                         | One coordinated PR across the monorepo: rename `packages/palco-templates/` → `packages/palco-protocols/` (directory + `pyproject.toml` name); convert capability + device protocols (registry included); add `palco-bases` registration gate; update `palco-operations` annotations and imports; update every example testbed plugin's imports and inner-class scaffolding; update tests. Released as **`palco-protocols` 1.0.0** — new package name, no compatibility alias to `palco-templates`. |
| **Import-site fan-out.** Every file that imports from `palco_templates` (drivers, operations, step defs, tests) needs its import line rewritten.                          | Mechanical churn across ~all source files.                                                              | One-shot rewrite is mechanical (`sed`-able); the static gate catches any miss at CI. The single-PR migration model means there is no period where both names are valid.                                                                                                                                                                                                                                                                                                                       |
| **Drivers in third-party testbed plugins need a one-time edit.**                                                                                                           | Out-of-tree friction.                                                                                   | The current state has zero production plugins (palco-bdd examples are scaffolding). The migration is essentially free of compatibility concerns *now* and will not be later.                                                                                                                                                                                                                                                                                                                  |
| **Documentation churn.** Architecture spec (§2a, §2c, §6, §7, §8, §9), the five-layer model doc, and the wifi + firewall briefs reference both "ABC" / "compose templates as inner classes" *and* the old `palco-templates` package name.                                                                                                                                                | Stale prose, stale paths in code blocks.                                                                | This document is the canonical amendment. The implementing PR updates: (a) the 2026-04-15 commons design spec in place; (b) `palco-bdd/docs/architecture/palco-five-layer-model.md` (rewrite L4 — capability/device protocols replace templates; `palco-templates` → `palco-protocols`); (c) the wifi / firewall domain briefs (one-paragraph implementation note); (d) any example READMEs that mention `palco-templates`.                                                                                                                                                                            |

## Implementation Plan

A separate Implementation Plan document will detail phases. The high-
level sketch:

1. **Phase 0 — Spike on one capability + one device.** On a throwaway
   branch, convert `router.py` from ABC to Protocol and
   `device_types/sdwan.py` to a device Protocol *without* the package
   rename (so the diff is small enough to read). Update the
   `LinuxSdwanRouter` driver in `palco-bdd/examples/sdwan-digital-twin`
   to satisfy the new shape; run the existing test suite. Confirm the
   runtime gate triggers when a method is removed. Discard the branch.
2. **Phase 1 — Package rename.** In a single coordinated PR:
   - `git mv packages/palco-templates packages/palco-protocols`
   - Rename the package's distribution name in `pyproject.toml`
     (`name = "palco-protocols"`), version → `1.0.0`.
   - `git mv src/palco_templates src/palco_protocols`
   - `git mv src/palco_protocols/device_types src/palco_protocols/devices`
   - Delete `src/palco_protocols/_template.py` (the old `Template`
     ABC base; no longer needed).
   - Rewrite imports across the monorepo
     (`palco_templates` → `palco_protocols`,
     `palco_templates.device_types` → `palco_protocols.devices`).
   - Update `palco-operations`, `palco-bases`, every example plugin
     (`palco-bdd/examples/*/palco_plugins/`), and every test file's
     imports in the same PR.
   - At this point the suite still passes against ABCs — only names
     have changed.
3. **Phase 2 — Convert capability protocols + apply the granularity
   and levels rules.** Convert ABCs to `@runtime_checkable` Protocols
   inside the `palco_protocols.<domain>` modules **and** collapse to
   the seed capability inventory at the same time (today's ~50 ABCs
   → ~15–20 bundled Protocols per the
   [granularity rule](#capability-granularity-bundle-by-coherent-telco-domain-split-on-evidence)).
   Notable bundling: `PacketFilter` + `PortForwarding` + `FirewallZones`
   → `Firewall`; `Router` + `IpRouting` → `Routing`;
   `SdwanPolicyManager` → `SdwanPolicy`. Single-purpose protocols
   (`Nat`, `Conntrack`, `NetemController`, `IpInterface`,
   `PcapCapture`, `NtpClient`, `HwConsole`, `FileTransfer`,
   `NmapScanner`) carry forward one-to-one. Role-split protocols
   (`Tr069Server`/`Tr069Client`, `SipPhone`/`SipServer`,
   `HttpClient`/`HttpServer`, `DeviceLifecycle`/`DeviceManagement`)
   carry forward one-to-one. **Also** add the four optional WhiteBox
   extensions per the [levels rule](#capability-levels-black-box-mandatory--white-box-optional):
   `FirewallWhiteBox`, `RoutingWhiteBox`, `SipPhoneWhiteBox`,
   `SipServerWhiteBox` — each declared with `class X(<Capability>,
   Protocol)` so it inherits the mandatory surface plus white-box
   methods. Add `packages/palco-protocols/SPLITS.md` and
   `packages/palco-protocols/LEVELS.md` as empty tracking files.
   Tests in `packages/palco-protocols/tests/` verify the expected
   method set per level; the `expected_methods` parametrization uses
   `proto.__protocol_attrs__` instead of `abc.abstractmethods`.
4. **Phase 3 — Convert device protocols + apply the scope rule.**
   Replace each `palco_protocols/devices/<group>.py` `device_type(...)`
   declaration with a `Protocol` class typed against the bundled
   capability protocols. Update the registry to hold `(name, protocol)`
   pairs. Audit each archetype against the
   [three-tier scope rule](#where-device-protocols-live-archetype-in-commons-vs-plugin-local):
   industry-standard archetypes (`LinuxCpe`, `LinuxAcs`,
   `LinuxSdwanRouter`, `LinuxSipPhone`, `LinuxSipServer`, …) stay in
   commons; anything testbed-specific moves to its plugin's
   `protocols/` directory and registers via the same
   `device_type(name, protocol)` helper from the plugin's `__init__`.
   Where a device is multi-transport, add per-route Protocols and the
   device protocol's route attribute declarations per
   [§L4c](#l4c--route-convention-default--alternative-transports).
5. **Phase 4 — Wire the runtime gate.** Add the `_verify_driver`
   call in `palco-bases` (or `palco` framework) device-registration
   path. Add a unit test that a deliberately-incomplete driver raises
   `DriverContractViolation`.
6. **Phase 5 — Update operations.** No semantic changes; protocol
   parameter types replace ABC parameter types in annotations.
   Touch every file in `palco-operations/src/palco_operations/`.
7. **Phase 6 — Update example testbed plugins.**
   - **6a — sdwan-digital-twin.** Drops inner-class inheritance;
     switches to Pattern A or Pattern B per driver. Single-route
     drivers — no route sub-namespaces needed.
   - **6b — sip-telephony.** Same shape as 6a (single-route, no
     transport variants). Validates that the `SipPhone` and
     `SipServer` capability protocols cover both `PjsuaPhone` and
     `KamailioSipServer` drivers.
   - **6c — cpe-gateway (firewall).** Implements the route convention
     end-to-end: `RpiPrplosCpe` exposes `uci` and `tr069` routes with
     `default_route = "uci"`. Validates UC-CPE-FW-04 (cross-route
     parity) as the route convention's most demanding case. The
     [Worked example: cpe-gateway-firewall](#worked-example-cpe-gateway-firewall)
     section is the design target for this phase.
8. **Phase 7 — Documentation.** Amend
   `docs/superpowers/specs/2026-04-15-palco-commons-design.md` §2a,
   §2c, §6, §7, §8, §9 in place (rename + protocol adoption). Rewrite
   the L4 layer in `palco-bdd/docs/architecture/palco-five-layer-model.md`
   to describe capability/device protocols (and route protocols where
   applicable) instead of templates and inner-class composition.
   Add an "implementation note" paragraph to
   `docs/wifi-domain-brief.md` and `docs/firewall-domain-brief.md`.
   Add a `CHANGELOG.md` entry under `packages/palco-protocols/` marking
   the 1.0.0 release with a clear "renamed from `palco-templates`;
   ABCs replaced by Protocols" note.

## Open Questions

- [ ] **Static-gate enforcement.** Do testbed-plugin CI pipelines all
  
      run `mypy` / `pyright`? If not, what's the agreed minimum bar
      before this design ships? (The runtime gate alone catches
      missing attributes; only the static gate catches signature
      drift.)
- [x] ~~**Versioning.**~~ **Resolved.** The package is renamed
      `palco-templates` → `palco-protocols` and released as
      **`palco-protocols` 1.0.0** (new package, new name; no
      compatibility alias). Captured in [Goals](#goals) and the
      [API Changes](#api-changes) table.
- [x] ~~**`Template` base class.**~~ **Resolved.** Deleted. The old
      `_template.py` module goes away in Phase 1; drivers either hold
      a `_device` back-ref locally (Pattern A) or take the device in
      `__init__` (Pattern B). See [§L6](#l6--device-drivers-testbed-plugins).
- [ ] **`device_type()` API shape.** Settle the new signature —
  
      `device_type(name, protocol)` returning the protocol class
      itself, or `(name, protocol)` returning a registry record? The
      former is terser; the latter mirrors the current
      `DeviceTypeSpec` shape for any downstream code that introspects.
      (The function lives at `palco_protocols.devices.device_type`
      under the rename.)
- [x] ~~**Naming.**~~ **Resolved.** Package renamed to
      `palco-protocols`; the term-of-art across code, docstrings,
      tests, and architecture docs is **capability protocol**
      (atomic) and **device protocol** (aggregate). The
      2026-04-15 commons design doc is updated in Phase 7
      (≈200 instances of "template"); other docs follow on the same
      PR.
- [x] ~~**Cross-domain protocol composition.**~~ **Resolved** by the
      [bundle-by-coherent-domain rule](#capability-granularity-bundle-by-coherent-telco-domain-split-on-evidence).
      Cross-domain "molecular" mixins (`IpStack` =
      `IpInterface` + `IpRouting` + `DhcpClient`, `HasFirewall`,
      `HasRouting`) were considered as an intermediate tier between
      capability protocols and device protocols, and rejected: under
      the bundle-by-domain rule each capability protocol is already
      the bundle a mixin would have wrapped, so there's nothing for a
      mixin tier to do. Two tiers (capability → device), not three.
- [x] ~~**Multiple-compilation alias convention.**~~ **Resolved** by
      the route convention in [§L4c](#l4c--route-convention-default--alternative-transports).
      Suffixed top-level attributes (`packet_filter_tr069`) are
      replaced by route sub-namespaces (`device.tr069.firewall`)
      with default-route aliasing on the device root
      (`device.firewall` resolves to `device.<default_route>.firewall`).
- [ ] **Standardised route names.** The route convention reserves a
      
      small lowercase vocabulary (`uci`, `tr069`, `cli`, `api`, `gui`,
      `netconf`, `serial`, …). Should this list be enumerated in
      `palco-protocols` as a `Literal` type / module-level constant,
      or left informal? Enforcing the vocabulary helps cross-plugin
      consistency for parity tests; leaving it informal lowers the
      bar for one-off transports.
- [ ] **Per-device-type `default_route` declaration site.** The route
      
      convention puts `default_route` on the driver class. Should it
      instead live on the device-type spec (so it is part of the
      contract every driver of that type satisfies), or stay on the
      driver (so each driver can pick its own ergonomic default)?
      Argument for the spec: portability — every `linux_cpe` test
      sees the same default. Argument for the driver: realism — a
      docker CPE may not even have TR-069 plumbing.
