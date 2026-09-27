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
  read its state and its physical parameters;
- **capture of its own traffic** to a file that can be fetched off the box;
- **interface-bound filtering** and a zone-based stateful firewall;
- **on-box services** — NAT, QoS by class (classify, mark, queue, shape), DHCP
  server and relay, first-hop redundancy, on-box reachability probes;
- **routing state and levers** — routing tables per routing instance, peering
  state, peer resets;
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

Standalone switches that share an estate with these routers are out of scope:
they fold into the existing switch archetypes as a driver exercise.

### Boundary with the registered archetypes

- **`sdwan_appliance` (`SdwanApplianceDevice`)** — *under*-specified for this
  class: it publishes no interface administration and no own-traffic capture,
  both deliberately excluded because no cloud-managed appliance publishes them
  (`SPLITS.md`, 2026-06-12), yet interface administration is this class's
  defining operation. *Over*-specified in the other direction: its mandatory
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
  forwarding-tier archetypes keyed on VLANs and switch ports; they carry no
  WAN access, NAT, stateful firewall, QoS-by-class policy or routing-peer
  levers. A router's integrated switch reuses their capability layer; the
  router itself is not a switch.
- **`linux_cpe` (`CpeDevice`)** — a residential gateway on a Linux substrate,
  provisioned through device management; it publishes neither the routing
  levers nor the enterprise services of this class.
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
| Juniper Junos (MX, ACX, SRX) | competitor | carrier edge to branch security router in one OS |
| Nokia SR OS (7750 SR, 7250 IXR, 7705 SAR) | competitor | carrier and aggregation edge; access/industrial variants with cellular and xDSL |
| HPE Comware (MSR) | competitor | full branch router with voice, DSL and cellular |
| Fortinet FortiOS (FortiGate as a branch router) | competitor | branch router bridging to the SD-WAN review |
| MikroTik RouterOS | competitor | closed router product at the low end of the market; probes the neutrality envelope |

Excluded, with reasons: **Arista EOS** (aggregation and data-centre routing;
no branch set); **Cradlepoint, Peplink, Versa** (controller or cloud-managed —
they do not publish the defining operations, as the appliance review found
for its families); **Ubiquiti EdgeRouter** (effectively end of development);
**Palo Alto PAN-OS** (a firewall family, adjacent to the SD-WAN review).

Eight families give denominators with meaning (a core threshold of every
trigger family plus a majority of eight), and the set covers every device
class twice or more outside the trigger families.

### Demand

The demand evidence is held privately by the maintainers (a private request
under `docs/archetypes/README.md`, "The request"). It asks for the operations
listed under "The class" above and, in addition, for operations whose
placement the design decides — in the archetype, in a tier, or in a separate
operational capability outside the archetype shape:

- physical interface parameters (speed, duplex, negotiation);
- software image lifecycle (stage, activate, roll back);
- configuration export and import;
- security posture of the management plane (services, stored secrets);
- monitoring access, operator authorisation, time synchronisation;
- flow export, configured probes and tracking, overlay tunnel state;
- link aggregation, cellular radio and subscription state, backup-WAN
  failover.

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
