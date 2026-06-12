# Design: `SiteToSiteVpn` capability seed (+ `L3Firewall` VPN rule set)

| Field   | Value                                                              |
| ------- | ------------------------------------------------------------------ |
| Status  | Approved for implementation                                         |
| Author  | rjvisser                                                            |
| Date    | 2026-06-12                                                          |
| Related | `docs/sdwan-appliance-protocol-design.md`, `docs/kpn-test-scope-validation.md` §5.1–§5.2, `GAPS.md`, `models/sdwan_appliance.py`, `l3_firewall.py`, `devices/sdwan.py` |

## Purpose

Seed the vendor-neutral **site-to-site / overlay VPN** capability for the
`sdwan_appliance` archetype, and add the **VPN-scoped firewall rule set** to
`L3Firewall`. Driving evidence: operator acceptance-test scope for managed
SD-WAN appliances requires API control of overlay participation (role,
default route into the overlay, advertised subnets), a peer-reachability
read, and a firewall policy applied to overlay traffic. Both capabilities
pass the four-vendor concept check (see Cross-vendor section).

## Constraints

- **No customer/test-suite names** in package source, tracking files, or
  enum/model vocabulary. Evidence in `GAPS.md` and docstrings is phrased
  generically ("operator acceptance scope") and cites **public vendor API
  documentation** only.
- All existing conventions hold: normalized `StrEnum` vocabularies,
  dataclass models in `models/sdwan_appliance.py`, `runtime_checkable`
  Protocols, vendor-isolation grep, `mypy --strict`.
- Adding `vpn:` to `SdwanApplianceDevice` is conformance-safe: no driver
  implements the archetype yet (verified 2026-06-12).

## Models (`models/sdwan_appliance.py`)

```python
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
    """A hub a spoke connects to. ``name`` is the testbed-level hub
    identifier; the plugin maps it to the vendor's id."""
    name: str
    use_default_route: bool = False

@dataclass
class VpnSubnet:
    """A local subnet and whether it participates in the overlay."""
    subnet: str           # CIDR
    advertise: bool = True

@dataclass
class SiteToSiteVpnConfig:
    """Complete overlay participation config — read and replaced whole."""
    role: VpnRole
    hubs: list[VpnHub] = field(default_factory=list)      # spoke: priority order
    subnets: list[VpnSubnet] = field(default_factory=list)

@dataclass
class VpnPeerStatus:
    """Observed status of one VPN peer (read-only)."""
    name: str             # peer site name (normalized; plugin maps)
    state: VpnPeerState
    uplink: str = ""      # uplink carrying the tunnel, when known
```

Decisions recorded:

- **No `MESH` role member.** Mesh-capable products exist, but not all four
  reviewed families can express it through the same surface; grows on
  evidence per the enum rule.
- **No IPsec crypto parameters** (proposals, lifetimes, PSKs). No driving
  test; highly vendor-divergent. Out of scope until evidenced.
- **Peers/hubs by testbed-level name**, never vendor ids — same
  normalized-vocabulary-vs-plugin-mapping rule as content categories.
- New normalized `VpnPeerStatus` is used; `wan_edge.VPNPeerStatus`
  (free-string reachability, zero consumers) is left untouched for the twin.

## Protocol (`site_to_site_vpn.py`, new)

```python
@runtime_checkable
class SiteToSiteVpn(Protocol):
    """Abstract contract for an appliance's site-to-site VPN overlay."""

    def set_vpn_config(self, config: SiteToSiteVpnConfig) -> None: ...
    def get_vpn_config(self) -> SiteToSiteVpnConfig: ...
    def get_vpn_peers(self) -> list[VpnPeerStatus]: ...
```

In scope: overlay participation (role, hubs + default route, subnets) as one
whole-replace config object, and the peer-status read. Out of scope (module
docstring states each): VPN-scoped firewall rules (`l3_firewall`), IPsec
crypto parameters (deferred), path steering (`sdwan_policy_manager`), and
third-party/non-overlay tunnels (deferred).

Whole-config replace was chosen over per-facet setters because role and hubs
are semantically coupled (hubs are only meaningful for a spoke) and the
management planes expose participation as one object; "toggle default route
into overlay" = get → modify hub entry → set.

## `L3Firewall` extension (`l3_firewall.py`)

```python
def set_vpn_rules(self, rules: list[L3Rule]) -> None:
    """Replace the ordered site-to-site VPN policy with *rules*."""

def get_vpn_rules(self) -> list[L3Rule]:
    """Return the site-to-site VPN rules in evaluation order."""
```

Same whole-list-replace contract and `L3Rule` model as outbound/inbound.
Docstring notes: the rule set governs traffic traversing the site-to-site
VPN; on some products it is broader than one device (e.g. fleet-wide) —
a driver/testbed concern, not a contract one. Firewall stays one coherent
domain (consistent with the 2026-06-11 `SdwanPolicyManager` split; this is
an addition, not a split — **no `SPLITS.md` entry**).

## Archetype (`devices/sdwan.py`)

Add `vpn: SiteToSiteVpn` to `SdwanApplianceDevice`. `SdwanRouterDevice`
(twin) is untouched.

## Cross-vendor concept check (public API references)

| Intent | Meraki MX | Catalyst SD-WAN | FortiGate | Prisma SD-WAN |
|---|---|---|---|---|
| role / hubs / default route / subnets | `GET/PUT …/appliance/vpn/siteToSiteVpn` (mode, hubs[].useDefaultRoute, subnets[].useVpn) | hub-and-spoke / mesh topology policy + OMP advertised routes (SD-WAN Manager policy API) | `vpn.ipsec/phase1-interface` + `phase2-interface` + static route into tunnel | service labels / binding maps + network-policy `service_context`; vpnlink admin state |
| peer status read | `GET /organizations/{org}/appliance/vpn/statuses` | `GET /device/bfd/sessions` | `GET /api/v2/monitor/vpn/ipsec` | `GET …/vpnlinks/{id}/status` |
| VPN-scoped firewall rules | `GET/PUT /organizations/{org}/appliance/vpn/vpnFirewallRules` | ZBFW zone-pairs over service VPNs | policies with tunnel interfaces as src/dst | security zones bound to WAN overlays (`wanoverlay_ids`) |

All cells are published-API surfaces (developer.cisco.com/meraki/api-v1,
developer.cisco.com/sdwan, docs.fortinet.com, pan.dev/sdwan). Endpoint names
stay in docs; only normalized intent enters the package.

## Tests

Following the existing per-capability pattern:

1. **Model tests** (`test_sdwan_appliance_models.py`): `VpnRole` /
   `VpnPeerState` construct-from-value validation; `VpnHub` / `VpnSubnet` /
   `SiteToSiteVpnConfig` / `VpnPeerStatus` defaults and field types.
2. **Protocol-conformance test** (`test_sdwan_appliance_templates.py`
   pattern): a minimal fake satisfying `SiteToSiteVpn` passes
   `isinstance`; a fake missing a method fails.
3. **`L3Firewall` conformance** updated for the two new methods.
4. **Archetype gate**: device-types test asserts `SdwanApplianceDevice`
   requires `vpn`.
5. **Vendor-isolation grep** stays green (no product names in package
   source).
6. `mypy --strict` clean.

## Tracking-file changes

- **`GAPS.md`** — two new deferred entries from the same validation effort
  (no customer references; public vendor-API citations only):
  - *Static-route configuration on `Router`* — operator acceptance scope
    requires creating a static route toward a downstream LAN router;
    all four reviewed families expose it (Meraki `staticRoutes` CRUD,
    SD-WAN Manager VPN feature template, FortiOS `router/static`,
    Prisma element `staticroutes`).
  - *BGP configuration + operational read* — operator acceptance scope
    requires BGP peering with a LAN-side router and verifying learned
    routes; config is 4/4, operational read 3/4 (one family publishes no
    BGP state read — model config and status as separate methods so a
    driver can support one without the other).
- **`SPLITS.md`** — no entry (addition, not a split/merge).
- **`LEVELS.md`** — no entry (no white-box extension).
- **`docs/sdwan-appliance-protocol-design.md`** — add `vpn: SiteToSiteVpn`
  to the archetype block, a `## New capabilities` subsection, and a
  cross-vendor table row.

## Error handling

Protocols define intent only; drivers raise the framework's
unsupported-capability error where a product cannot satisfy a method (e.g.
a product whose overlay role is fixed by the controller). No new error
types are introduced.

## Acceptance

- All new/changed tests pass; full suite green; `mypy --strict` clean.
- Vendor-isolation grep passes over package source.
- Archetype registration test covers the new attribute.
