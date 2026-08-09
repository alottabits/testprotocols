# Capability-Only Device Archetypes

**Status:** accepted (2026-08-09) · **Enforced by:** `register_device_type`
(import-time) + `tests/test_archetype_purity.py` (merge gate, required CI check)

## Rule

A device archetype Protocol in `testprotocols.devices.*` declares **only**
members whose annotation is itself a capability Protocol. The sole exception
is the universal identity pair `device_name` / `device_type` inherited from
`BaseDeviceProtocol` (see its docstring for why identity is device-level).

Boundary-facing facts a driver resolves from its own config or discovers at
runtime — addresses, segment labels, ports, models, ownership flags — belong
in a capability protocol as read-only properties (`NetworkAttachment`,
`PlacementPipe`/`PlacementPorts`, `DeviceInfo`, `ConfigOwnership`, or the
domain capability itself, as with `SipPhone.number`). Declare data members
as `@property`: an implementer's plain attribute still satisfies a property
member, while the reverse rejects read-only implementations.

## Why

Bare scalars on archetypes accreted twice through normal review (0.6.x
"appliance-model / client test-IP", 0.7.2 "boundary-facing device-shape
members") before being reworked in 0.8.0. Scalars fragment the design's one
idea — a device is a composition of capability namespaces — and, declared as
plain annotations, they statically reject drivers exposing read-only
properties. The gate makes the invariant self-enforcing, including for
plugin-local archetypes registered downstream via `register_device_type`.

## Adding an exception

Extend `IDENTITY_MEMBERS` in `testprotocols/devices/__init__.py` — in the
open, in a reviewable diff, with this document updated to say why.

## Adoption guidance for the boundary capabilities

Archetype membership stays evidence-driven: compose a capability where a
driver already resolves the fact and a consumer reads it. Current deferrals
and their triggers:

- `NetworkAttachment` beyond the QoE measurement client — trigger: first
  driver implementing guest attachment on another archetype. Note the
  boundary: archetypes answering addressing via `NetworkEndpoint`
  (`data_plane_endpoint`) do not also compose `NetworkAttachment`.
- `PlacementPipe` beyond the QoE measurement client — trigger: first other
  client with a declared access-port pipe.
- `DeviceInfo` beyond the appliance and switches — trigger: first
  model-parameterised test on that archetype (CPE is the likely next).
- `ConfigOwnership` beyond the appliance — trigger: first
  monitored-but-not-managed switch/CPE in an inventory.
