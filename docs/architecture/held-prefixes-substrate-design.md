# Held-Prefixes Substrate Capability (`HeldPrefixes`)

**Status:** proposed (2026-09-04) — substrate survey (§3) **to ratify on
landing** · **Kind:** substrate/tool capability (a routing-instrument
behaviour, **not** a device-under-test contract) · **Enforced by:**
`tests/test_network_tool_templates.py` (method-set shape) + the vendor-isolation
grep guarantee (§6)

## 1. What this is

`HeldPrefixes` is the contract for a testbed instrument that **holds a prefix
behind itself**: it takes a caller-supplied host address (`host/prefixlen`) on a
loopback-class interface it allocates, so the prefix becomes a connected,
locally-originated network the instrument answers for. A routing peer that must
advertise, or be the static next hop for, a network that exists only behind it
uses this to make that network real — the "network behind the peer" that a
device under test learns and forwards to.

Three members, one coherent domain (a locally-originated prefix on the
instrument):

- `hold(address) -> None` — hold `address` on an interface of the device's own;
  idempotent on the normalized address.
- `release(address) -> None` — stop holding exactly that address; a no-op when
  not held; other held addresses stay in force.
- `held() -> list[str]` — every held address, normalized `host/prefixlen`.

No interface name crosses the contract in either direction: the device
allocates, names and frees the interface; the caller speaks only addresses.

## 2. Class: substrate/tool, not a DUT contract

`HeldPrefixes` is a **router-substrate instrument** behaviour — the class of
`PacketInjector`, `NetworkProbe`, `NetemController`: a thing the testbed *uses
to exercise* a device under test, not a management-plane contract *of* one.
Its neutrality is proven by **substrate universality** (§3), not by the
cross-vendor family sweep that gates device-under-test contracts. The device
under test never implements it; the instrument beside the DUT does.

## 3. Substrate-family survey (proposed, not a conformance matrix)

The "families" are the independent routing substrates that can **back** the
contract. Recorded as substrate evidence; the Linux dummy interface is the
vendor-free reference. Only the first consumer's substrate has an
implementation today; the other rows are recorded from published vendor
documentation and are illustrative of substrate universality, not a
supported-backends list.

| Substrate | Allocation unit | Multiple addresses per unit | Independent of physical link state | Note |
|---|---|:--:|:--:|---|
| Linux iproute2 dummy interface (reference) | one `dummyN` per address, or several addresses on one | ✓ | ✓ | `ip link add … type dummy`; the OS interface FRR and every Linux-based router substrate see |
| VyOS dummy interface | `dummyN` under the routing config | ✓ | ✓ | documented as operating like the loopback interface |
| FRR on Linux | the OS dummy/loopback interfaces | ✓ | ✓ | same substrate as the reference row; the routing daemon originates whatever is connected |
| Cisco IOS-XE Loopback interface | `LoopbackN` | ✓ (secondary) | ✓ | virtual interface, independent of physical state |
| Junos `lo0` | `lo0` unit 0 | ✓ | ✓ | accepts multiple addresses including subnet addresses |

Every substrate offers an interface whose address makes the prefix connected
without a physical link, and every one supports more than one such address —
the two properties the contract relies on (allocation, address-keyed release).
No substrate vocabulary appears in the method signatures.

## 4. Scope boundary — holding is not advertising

Holding a prefix makes it connected on the instrument. **Making it reachable
from elsewhere is a different contract**: advertising over a routing protocol
is `Bgp` (`BgpConfig.advertised_networks`), a static next hop is a static route
on the device that must reach it (`StaticRoutes`), and the return path is the
instrument's own routing (`StaticRoutes` on the instrument). `HeldPrefixes`
composes with those; it does not fold them in. It also names no route
attributes (metric, tag, community) — those belong to the advertising contract.

## 5. Address contract

Addresses are `host/prefixlen` strings and are compared **normalized** (the
implementation canonicalizes before comparing and before reporting), so
`hold("203.0.113.1/24")` twice is one held address, `release` matches the same
string form, and `held()` returns the canonical form regardless of how the
caller spelled it. The host part is the address the instrument answers on
(the reachability target a consumer probes); the prefix length is the network
the instrument holds.

## 6. Neutrality (vendor-isolation) guarantee

No substrate or product name appears in the package source — not in
`held_prefixes.py`, not in the method or parameter names. Substrates are cited
**only in this design doc**. Enforced by convention and re-checkable:

```
grep -RiE 'vyos|frr|ios-xe|junos|iproute2' src/testprotocols/held_prefixes.py
# expected: no matches
```

"loopback-class interface" in the docstring is the generic networking term for
the allocation unit, not a product's interface name.

## 7. Overlap analysis

- `IpInterface` — addresses an interface the **caller names** (`set_static_ip(
  interface, ip, netmask)` / `remove_static_ip(interface)`). `HeldPrefixes`
  delegates to the same kind of mutation underneath, but the new part is
  **allocation** (the device chooses and creates the interface) and
  **address-keyed release** (one address released, the others kept). Neither is
  expressible through a name-keyed contract.
- `RoutedInterfaces` (switch L3, `InterfaceMode.LOOPBACK`) — a device-under-test
  configuration surface on a managed switch, not an instrument behaviour;
  different class, no overlap.
- `StaticRoutes`, `Bgp` — the advertising/return-path contracts §4 keeps
  separate.
- `NetworkAttachment` — declared/discovered homing facts; the held address is
  not an attachment (the instrument's test leg is), so it does not belong there.

## 8. Rejected alternative — a caller-named interface

Reviewed and rejected: have the instrument's `IpInterface` implementation
dispatch on the interface-name kind (a loopback-class name routes to the
loopback-class configuration path) and publish the chosen interface name on a
boundary view for the caller to pass back in.

- **Vendor names cross the contract.** The caller would have to carry a
  substrate-specific interface name (`dummy0`, `Loopback0`, `lo0.0`) through
  the test layer.
- **Release safety.** A name-keyed `remove_static_ip` on at least one substrate
  deletes the interface's *whole* address node, so a shared loopback holding
  two addresses cannot release one of them. Address-keyed release is the
  guarantee the contract exists to give.

## 9. Orchestration is downstream, not here

Composing hold → advertise → await-learned is a natural future
`testoperations` operation, where cross-capability glue belongs. The capability
only holds.

## 10. Archetype deferral

No upstream archetype member ships with the capability. A routing-instrument
archetype composing `HeldPrefixes` with `Bgp`, `StaticRoutes`, `IpInterface`,
`NetworkProbe` and the boundary views is a real shape, but it is **derivable
downstream today** (a consumer registers its own archetype via
`register_device_type`; the purity gate runs downstream). It lifts to commons
when a second router instrument materializes — the archetype's own recorded
trigger. `GAPS.md` records the capability's evidence as **one written consumer
and one planned**.
