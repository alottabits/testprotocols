# SiteToSiteVpn Capability Seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seed the vendor-neutral `SiteToSiteVpn` capability protocol (overlay role/hubs/subnets config + peer-status read), add the VPN-scoped rule set to `L3Firewall`, and wire both into the `SdwanApplianceDevice` archetype.

**Architecture:** Follows the established testprotocols capability pattern: normalized `StrEnum` vocabularies + dataclass models in `models/sdwan_appliance.py`, a `@runtime_checkable` Protocol in its own module, whole-replace config semantics, exports through both `__init__.py` files, and parametrized conformance tests. Spec: `docs/superpowers/specs/2026-06-12-site-to-site-vpn-design.md`.

**Tech Stack:** Python 3.12+ (`StrEnum`, dataclasses, `typing.Protocol`), pytest, mypy --strict (root `pyproject.toml`), uv workspace.

**Working directory for all commands:** `/home/rjvisser/projects/req-tst/testprotocols` (repo root).

**Constraint (from spec):** No customer/test-suite names anywhere in this change — package source, tests, tracking files, and commit messages reference only public vendor-API documentation, and vendor product names are allowed **only** in `GAPS.md`/`docs/` (never in `packages/testprotocols/src/` or `tests/`).

---

### Task 1: VPN models + vocabularies

**Files:**
- Modify: `packages/testprotocols/src/testprotocols/models/sdwan_appliance.py` (append new section at end of file)
- Modify: `packages/testprotocols/src/testprotocols/models/__init__.py` (exports)
- Test: `packages/testprotocols/tests/test_sdwan_appliance_models.py`

- [ ] **Step 1: Write the failing tests**

In `packages/testprotocols/tests/test_sdwan_appliance_models.py`, extend the existing `from testprotocols.models.sdwan_appliance import (...)` block with six new names, keeping the block's ordering style:

```python
    SiteToSiteVpnConfig,
    VpnHub,
    VpnPeerState,
    VpnPeerStatus,
    VpnRole,
    VpnSubnet,
```

Append at the end of the file:

```python
def test_vpn_vocabularies_are_normalized_strenums() -> None:
    assert issubclass(VpnRole, StrEnum)
    assert issubclass(VpnPeerState, StrEnum)
    # members are strings; construction validates at the vendor-ingest boundary
    assert VpnRole.SPOKE == "spoke"
    assert VpnRole("hub") is VpnRole.HUB
    assert VpnPeerState.REACHABLE == "reachable"
    with pytest.raises(ValueError):
        VpnRole("mesh")  # not seeded — grows on evidence
    with pytest.raises(ValueError):
        VpnPeerState("degraded")


def test_site_to_site_vpn_config_models() -> None:
    hub = VpnHub(name="hub-1")
    assert hub.use_default_route is False
    subnet = VpnSubnet(subnet="192.168.10.0/24")
    assert subnet.advertise is True
    config = SiteToSiteVpnConfig(role=VpnRole.SPOKE, hubs=[hub], subnets=[subnet])
    assert config.role is VpnRole.SPOKE
    assert config.hubs[0].name == "hub-1"
    # role-only construction: hubs/subnets default to empty, instances independent
    a = SiteToSiteVpnConfig(role=VpnRole.DISABLED)
    b = SiteToSiteVpnConfig(role=VpnRole.HUB)
    a.hubs.append(hub)
    assert b.hubs == []


def test_vpn_peer_status_model() -> None:
    peer = VpnPeerStatus(name="hub-1", state=VpnPeerState.REACHABLE)
    assert peer.uplink == ""
    assert peer.state == "reachable"  # StrEnum: serializes as the plain string
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/testprotocols/tests/test_sdwan_appliance_models.py -q`
Expected: collection error — `ImportError: cannot import name 'SiteToSiteVpnConfig'`

- [ ] **Step 3: Implement the models**

Append at the end of `packages/testprotocols/src/testprotocols/models/sdwan_appliance.py`:

```python
# --- Site-to-site VPN overlay ---


class VpnRole(StrEnum):
    """Role a device plays in the site-to-site VPN overlay."""

    DISABLED = "disabled"
    HUB = "hub"
    SPOKE = "spoke"


class VpnPeerState(StrEnum):
    """Reachability of a site-to-site VPN peer."""

    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"
    UNKNOWN = "unknown"


@dataclass
class VpnHub:
    """A hub a spoke connects to.

    ``name`` is the testbed-level hub identifier; the plugin maps it to the
    vendor's id. ``use_default_route`` points the spoke's default route into
    the overlay via this hub.
    """

    name: str
    use_default_route: bool = False


@dataclass
class VpnSubnet:
    """A local subnet and whether it participates in the overlay."""

    subnet: str
    advertise: bool = True


@dataclass
class SiteToSiteVpnConfig:
    """Complete overlay-participation config — read and replaced whole.

    ``hubs`` is only meaningful for ``VpnRole.SPOKE`` and is ordered by
    priority. ``subnets`` lists the local subnets and whether each is
    advertised into the overlay.
    """

    role: VpnRole
    hubs: list[VpnHub] = field(default_factory=list)
    subnets: list[VpnSubnet] = field(default_factory=list)


@dataclass
class VpnPeerStatus:
    """Observed status of one site-to-site VPN peer (read-only).

    ``name`` is the peer's testbed-level site name (normalized; the plugin
    maps the vendor's peer identifier). ``uplink`` names the local uplink
    carrying the tunnel when the product reports it, else ``""``.
    """

    name: str
    state: VpnPeerState
    uplink: str = ""
```

In `packages/testprotocols/src/testprotocols/models/__init__.py`, add the same six names to the `from testprotocols.models.sdwan_appliance import (...)` block (alphabetical position within that block) and to `__all__` (alphabetical position):

```python
    SiteToSiteVpnConfig,
    VpnHub,
    VpnPeerState,
    VpnPeerStatus,
    VpnRole,
    VpnSubnet,
```

```python
    "SiteToSiteVpnConfig",
    "VpnHub",
    "VpnPeerState",
    "VpnPeerStatus",
    "VpnRole",
    "VpnSubnet",
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/testprotocols/tests/test_sdwan_appliance_models.py packages/testprotocols/tests/test_package_imports.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add packages/testprotocols/src/testprotocols/models/sdwan_appliance.py \
        packages/testprotocols/src/testprotocols/models/__init__.py \
        packages/testprotocols/tests/test_sdwan_appliance_models.py
git commit -m "feat(testprotocols): site-to-site VPN models + normalized vocabularies

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: `SiteToSiteVpn` protocol module

**Files:**
- Create: `packages/testprotocols/src/testprotocols/site_to_site_vpn.py`
- Modify: `packages/testprotocols/src/testprotocols/__init__.py` (exports)
- Test: `packages/testprotocols/tests/test_sdwan_appliance_templates.py`

- [ ] **Step 1: Write the failing test**

In `packages/testprotocols/tests/test_sdwan_appliance_templates.py`, add one entry to the `PROTOCOLS` list (after the `"SdwanPolicyManager"`-adjacent entries if present, otherwise append before the closing `]` — order is cosmetic, the tests are parametrized):

```python
    (
        "SiteToSiteVpn",
        "testprotocols.site_to_site_vpn",
        {
            "set_vpn_config",
            "get_vpn_config",
            "get_vpn_peers",
        },
    ),
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/testprotocols/tests/test_sdwan_appliance_templates.py -q -k SiteToSiteVpn`
Expected: FAIL — `ModuleNotFoundError: No module named 'testprotocols.site_to_site_vpn'`

- [ ] **Step 3: Write the protocol module**

Create `packages/testprotocols/src/testprotocols/site_to_site_vpn.py`:

```python
"""Site-to-site VPN template — managed SD-WAN appliance.

Defines the abstract contract for an appliance's participation in the
site-to-site VPN overlay: its role (hub / spoke / disabled), the hubs a
spoke connects to (including whether the default route points into the
overlay), the local subnets advertised into the overlay, and a read of peer
reachability.

The configuration is one ``SiteToSiteVpnConfig`` read and replaced whole —
role and hubs are semantically coupled (hubs are only meaningful for a
spoke), and a managed appliance exposes overlay participation as a single
configuration surface. "Point the default route into the overlay" is a
config edit: get, flip ``use_default_route`` on a hub entry, set.

In scope: overlay participation (role, hubs + default route, subnets) and
peer status.

Out of scope: VPN-scoped firewall rules (see ``l3_firewall``), IPsec crypto
parameters (no driving test; highly vendor-divergent — add on evidence),
path steering across the overlay (see ``sdwan_policy_manager``), and
third-party / non-overlay tunnels (add on evidence).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.sdwan_appliance import SiteToSiteVpnConfig, VpnPeerStatus


@runtime_checkable
class SiteToSiteVpn(Protocol):
    """Abstract contract for an appliance's site-to-site VPN overlay."""

    def set_vpn_config(self, config: SiteToSiteVpnConfig) -> None:
        """Replace the appliance's overlay participation with *config*.

        The config is complete — role, hubs (spoke only, priority order),
        and subnet advertisement — and replaces the previous state whole.
        """
        ...

    def get_vpn_config(self) -> SiteToSiteVpnConfig:
        """Return the current overlay-participation configuration."""
        ...

    def get_vpn_peers(self) -> list[VpnPeerStatus]:
        """Return the observed status of every site-to-site VPN peer.

        Empty list when the device participates in no overlay.
        """
        ...
```

In `packages/testprotocols/src/testprotocols/__init__.py`:
- add `from testprotocols.site_to_site_vpn import SiteToSiteVpn` in alphabetical import position (between the `sip_server` and `snmp_client` imports);
- add `"SiteToSiteVpn"` to `__all__` in alphabetical position.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/testprotocols/tests/test_sdwan_appliance_templates.py packages/testprotocols/tests/test_package_imports.py -q`
Expected: all PASS (both parametrized tests now cover `SiteToSiteVpn`)

- [ ] **Step 5: Commit**

```bash
git add packages/testprotocols/src/testprotocols/site_to_site_vpn.py \
        packages/testprotocols/src/testprotocols/__init__.py \
        packages/testprotocols/tests/test_sdwan_appliance_templates.py
git commit -m "feat(testprotocols): SiteToSiteVpn capability protocol

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: `L3Firewall` VPN-scoped rule set

**Files:**
- Modify: `packages/testprotocols/src/testprotocols/l3_firewall.py`
- Test: `packages/testprotocols/tests/test_sdwan_appliance_templates.py` (existing `L3Firewall` entry)

- [ ] **Step 1: Extend the conformance expectation (failing test)**

In `packages/testprotocols/tests/test_sdwan_appliance_templates.py`, extend the existing `"L3Firewall"` entry's method set:

```python
    (
        "L3Firewall",
        "testprotocols.l3_firewall",
        {
            "set_outbound_rules",
            "get_outbound_rules",
            "set_inbound_rules",
            "get_inbound_rules",
            "set_vpn_rules",
            "get_vpn_rules",
        },
    ),
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/testprotocols/tests/test_sdwan_appliance_templates.py -q -k L3Firewall`
Expected: FAIL — `L3Firewall missing: {'set_vpn_rules', 'get_vpn_rules'}`

- [ ] **Step 3: Implement the two methods**

In `packages/testprotocols/src/testprotocols/l3_firewall.py`, append inside the `L3Firewall` class after `get_inbound_rules`:

```python
    def set_vpn_rules(self, rules: list[L3Rule]) -> None:
        """Replace the ordered site-to-site VPN policy with *rules*.

        The list is the complete policy, in evaluation order, governing
        traffic traversing the site-to-site VPN overlay. On some products
        this rule set is scoped wider than a single device (e.g.
        fleet-wide); that is a driver/testbed concern, not a contract one.
        """
        ...

    def get_vpn_rules(self) -> list[L3Rule]:
        """Return the site-to-site VPN rules in evaluation order."""
        ...
```

Also update the module docstring's "In scope:" line to read:

```
In scope: read and replace the outbound, inbound, and site-to-site VPN
ordered rule lists.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/testprotocols/tests/test_sdwan_appliance_templates.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add packages/testprotocols/src/testprotocols/l3_firewall.py \
        packages/testprotocols/tests/test_sdwan_appliance_templates.py
git commit -m "feat(testprotocols): L3Firewall gains the site-to-site VPN rule set

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Wire `vpn: SiteToSiteVpn` into the archetype

**Files:**
- Modify: `packages/testprotocols/src/testprotocols/devices/sdwan.py`
- Test: `packages/testprotocols/tests/test_device_types.py:191` (`test_sdwan_appliance_aggregates_expected_capabilities`)

- [ ] **Step 1: Extend the archetype gate (failing test)**

In `test_sdwan_appliance_aggregates_expected_capabilities` (`packages/testprotocols/tests/test_device_types.py`), add `"vpn"` to the `expected` set:

```python
    expected = {
        "routing",
        "sdwan_policy",
        "traffic_shaping",
        "l3_firewall",
        "l7_firewall",
        "content_filtering",
        "appliance_nat",
        "security",
        "uplinks",
        "lan",
        "syslog",
        "vpn",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/testprotocols/tests/test_device_types.py -q -k aggregates_expected`
Expected: FAIL — `missing: {'vpn'}`

- [ ] **Step 3: Add the attribute**

In `packages/testprotocols/src/testprotocols/devices/sdwan.py`:
- add to the imports (alphabetical position): `from testprotocols.site_to_site_vpn import SiteToSiteVpn`
- in `SdwanApplianceDevice`, add after `uplinks: ApplianceUplinks` (grouping with the other overlay/WAN attrs is cosmetic; place after `sdwan_policy` line for thematic adjacency):

```python
    vpn: SiteToSiteVpn
```

Conformance-safety note (verified 2026-06-12): no driver implements
`SdwanApplianceDevice` yet, so adding a required attribute breaks nothing.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/testprotocols/tests/test_device_types.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add packages/testprotocols/src/testprotocols/devices/sdwan.py \
        packages/testprotocols/tests/test_device_types.py
git commit -m "feat(testprotocols): SdwanApplianceDevice composes SiteToSiteVpn

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Tracking files, design doc, and full verification

**Files:**
- Modify: `packages/testprotocols/GAPS.md` (two new entries, inserted before the `## Workflow` section)
- Modify: `docs/sdwan-appliance-protocol-design.md` (archetype block, capability section, cross-vendor table, L3Firewall mention)
- No `SPLITS.md` / `LEVELS.md` changes (addition, not a split; no white-box surface)

- [ ] **Step 1: Add the two GAPS.md entries**

Insert before the `## Workflow` section of `packages/testprotocols/GAPS.md` (matching the existing entry format; note: generic "operator acceptance scope" phrasing, public vendor-API references only):

```markdown
## 2026-06-12 — Router static-route configuration [priority: high]

**Signal:** Operator acceptance scopes for managed SD-WAN appliances require
configuring a static route on the appliance toward a downstream LAN router
via the management API and verifying traffic follows it. `Router` today is
read-only (`get_routing_table`); neither it nor any appliance capability has
a static-route write surface.

**Trigger to act:** First appliance driver or testbed implementing a
static-routing acceptance case.

**Out of scope right now because:** the 2026-06-12 seeding round prioritized
`SiteToSiteVpn` (the larger blocking surface); static routes are a small,
separable follow-up.

**Design notes (when picked up):** per-entry CRUD, not list-replace — all
four reviewed appliance families expose static routes as individual objects
(Meraki Dashboard API `staticRoutes` CRUD; Catalyst SD-WAN Manager VPN
feature-template rows; FortiOS `router/static`; Prisma SD-WAN element
`staticroutes`). Shape sketch: `add_static_route(destination_cidr, next_hop,
name)` / `remove_static_route(name)`; reads stay on `get_routing_table`.
Decide at design time whether this lands on `Router` or a sibling capability
(adding required methods to `Router` is not conformance-safe for the twin —
migrate it in step).

**Cross-references:** `router.py`, `models/wan_edge.py::RouteEntry`,
`devices/sdwan.py`.

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
```

- [ ] **Step 2: Update `docs/sdwan-appliance-protocol-design.md`**

Four edits:

1. Archetype code block — add one line after `sdwan_policy`:

```python
    vpn: SiteToSiteVpn                    # new (2026-06-12 — overlay role/hubs/subnets + peer status)
```

2. Under `## New capabilities`, append a subsection:

```markdown
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
```

3. Cross-vendor table — add a row after `sdwan_policy`:

```markdown
| vpn (overlay config + peer status) | ✓         | ✓ (topology policy)  | ✓ (IPsec + monitor) | ✓ (vpnlinks)     |
```

4. In the `### l3_firewall: L3Firewall` section, append to the paragraph:

```markdown
As of 2026-06-12 the protocol also carries the site-to-site VPN rule set
(`set_vpn_rules` / `get_vpn_rules`) — same flat-ordered-list contract,
applied to overlay traffic.
```

- [ ] **Step 3: Full verification**

```bash
uv run pytest packages/testprotocols -q
uv run mypy packages/testprotocols/src/testprotocols
grep -rniE "meraki|fortinet|fortigate|viptela|vmanage|catalyst|prisma|cloudgenix|palo.alto" \
  packages/testprotocols/src/ packages/testprotocols/tests/
```

Expected: full suite PASS; mypy `Success: no issues found`; grep produces **no output** (vendor isolation holds — vendor names exist only in `GAPS.md` and `docs/`).

- [ ] **Step 4: Commit**

```bash
git add packages/testprotocols/GAPS.md docs/sdwan-appliance-protocol-design.md
git commit -m "docs(testprotocols): record SiteToSiteVpn in design doc; GAPS entries for static routes + BGP

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Self-review notes

- **Spec coverage:** models (Task 1), protocol (Task 2), L3Firewall extension (Task 3), archetype (Task 4), tracking/docs + vendor-isolation/mypy/full-suite acceptance (Task 5). Error-handling section of the spec requires no code (drivers' concern). ✓
- **Type consistency:** `SiteToSiteVpnConfig`/`VpnPeerStatus` imported in Task 2 exactly as defined in Task 1; method names `set_vpn_config`/`get_vpn_config`/`get_vpn_peers` consistent across Tasks 2, and `set_vpn_rules`/`get_vpn_rules` across Tasks 3/5. ✓
- **No placeholders:** every code step carries the full content. ✓
