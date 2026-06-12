# Design: typed path-steering surface on `SdwanPolicyManager`

| Field   | Value                                                              |
| ------- | ------------------------------------------------------------------ |
| Status  | Approved for implementation                                         |
| Author  | rjvisser                                                            |
| Date    | 2026-06-12                                                          |
| Related | `GAPS.md` (2026-06-11 typed path-steering deferral — resolved by this), `docs/sdwan-appliance-protocol-design.md` (incl. cross-vendor v2), `sdwan_policy_manager.py`, `models/sdwan_appliance.py`, `models/wan_edge.py::SLAPolicy` |

## Purpose

Replace the generic `apply_policy(dict)` escape hatch with a **typed**
uplink-steering surface for the two intents every reviewed appliance family
exposes: *steer flows matching M to uplink U*, optionally *subject to a
performance class* (fail over when thresholds are breached). Driving
evidence: operator acceptance scope requires (a) steering matching internet
flows to a named uplink and (b) steering overlay/default-route flows to a
named uplink with failover when latency exceeds a configured threshold.

This resolves the GAPS.md deferral of 2026-06-11 ("typed `SdwanPolicyManager`
path-steering surface"). The deferral's stated trigger — path-steering /
route-decision tests driving the exact shape — has fired.

## Constraints

- No customer/test-suite names in package source, tests, tracking files, or
  commit messages; vendor names only in `docs/` and `GAPS.md`/`SPLITS.md`
  with public-API citations.
- `mypy --strict`; established conventions (StrEnum vocabularies, dataclass
  models in `models/sdwan_appliance.py`, whole-list-replace semantics,
  parametrized conformance tests).
- **Adding required methods to `SdwanPolicyManager` is conformance-breaking**
  for its two existing implementations — the Linux digital twin
  (`LinuxSdwanPolicyImpl`, vitro-bdd `examples/sdwan-digital-twin`) and the
  MX driver (kpn-sdwan `impls/sdwan_policy.py`). Both are migrated **in
  step** (same working session); testprotocols must not be left published
  with un-migrated consumers across the three repos.
- All python via each repo's `.venv-3.12`.

## Models (`models/sdwan_appliance.py`)

```python
class SteeringScope(StrEnum):
    """Traffic domain an uplink-selection rule steers."""

    INTERNET = "internet"   # underlay / local-breakout-bound traffic
    OVERLAY = "overlay"     # site-to-site VPN / default-route-into-overlay traffic


@dataclass
class FlowMatch:
    """5-tuple traffic match for steering rules (match only — no action).

    Field semantics mirror ``L3Rule``'s match half: ``"any"`` when
    unconstrained; ports may be a single port, a range, or a comma list.
    """

    protocol: RuleProtocol = RuleProtocol.ANY
    src_cidr: str = "any"
    src_port: str = "any"
    dst_cidr: str = "any"
    dst_port: str = "any"


@dataclass
class UplinkSelectionRule:
    """One ordered uplink-steering rule.

    With ``performance_class`` set (the *name* of an ``SLAPolicy`` configured
    via ``configure_sla_policy``), traffic matching ``match`` is steered to
    ``preferred_uplink`` while the class is met and fails over when it is
    breached. With ``performance_class=None`` the preference is static —
    failover occurs only on uplink loss.
    """

    name: str
    scope: SteeringScope
    match: FlowMatch
    preferred_uplink: str
    performance_class: str | None = None
```

Decisions recorded:

- **Performance class = `SLAPolicy` referenced by name.** No new
  `PerformanceClass` model or `configure_performance_class` method —
  `SLAPolicy(name, max_latency_ms, max_jitter_ms, max_loss_percent)` already
  carries exactly the thresholds, configured via the existing
  `configure_sla_policy` / `remove_sla_policy`.
- **Explicit `SteeringScope`, no default and no `ANY`.** The acceptance
  scope distinguishes internet steering from overlay steering, and at least
  one product exposes them as separate configuration surfaces; the test
  author states the intent. Unified-surface products ignore the field.
- **No application/category match.** The driving tests match by destination
  only; application-based steering grows on evidence (the `L7MatchType`
  vocabulary exists if it comes). `FlowMatch` is its own dataclass — a
  match has no action/log semantics, so reusing `L3Rule` would be wrong.
- **No `FailoverCriterion` enum.** Both evidenced cases are covered by
  `performance_class` present/absent; grow on evidence.

## Protocol (`sdwan_policy_manager.py` — two methods added)

```python
def set_uplink_selection(self, rules: list[UplinkSelectionRule]) -> None:
    """Replace the ordered uplink-selection rule list with *rules*.

    The list is the complete steering policy in evaluation order. Rules
    referencing a ``performance_class`` require the named ``SLAPolicy`` to
    be configured (``configure_sla_policy``); products that cannot express
    arbitrary performance thresholds raise unsupported-capability when a
    rule carries a performance class, rather than approximating.
    """

def get_uplink_selection(self) -> list[UplinkSelectionRule]:
    """Return the uplink-selection rules in evaluation order."""
```

Module docstring updated: typed steering is now in scope; `apply_policy`
remains the escape hatch for vendor-shaped policies beyond this surface;
the GAPS.md cross-reference paragraph is rewritten accordingly.

## Cross-vendor concept check (public API references — docs only)

| Intent | Meraki MX | Catalyst SD-WAN | FortiGate | Prisma SD-WAN | Arista (VeloCloud) |
|---|---|---|---|---|---|
| flow → preferred uplink | `trafficShaping/uplinkSelection` wanTrafficUplinkPreferences (INTERNET) / vpnTrafficUplinkPreferences (OVERLAY) | app-route / data policy `set preferred-color` | `system/sdwan` service rules → priority members | `networkpolicyrules` paths_allowed by label | QOS module business rules, WAN-link steering |
| performance-class failover | `customPerformanceClasses` + `failOverCriterion: poorPerformance` | SLA-class lists referenced by app-route sequences | health-check SLA thresholds on service rules | `perfmgmtpolicyrules` thresholds | **✗** — fixed per-class DMPO SLAs (driver raises unsupported when `performance_class` set; cross-vendor v2 finding) |

5/5 for steering; 4/5 for arbitrary performance thresholds — handled by the
unsupported-capability convention, consistent with the design doc's v2
subsection.

## Consumer migration (in step, same session)

1. **Twin** — vitro-bdd `examples/sdwan-digital-twin`,
   `LinuxSdwanPolicyImpl`: implement `set_uplink_selection` /
   `get_uplink_selection` as a thin translation onto the impl's existing
   policy machinery (exact mechanics decided in that repo; unit tests
   added there; suite green with its own `.venv-3.12`).
2. **MX driver** — kpn-sdwan `impls/sdwan_policy.py`: real implementation —
   `SteeringScope.INTERNET` → WAN traffic uplink preferences;
   `SteeringScope.OVERLAY` → VPN traffic uplink preferences with the
   performance class resolved to a custom-performance-class id
   (created/looked up from the referenced `SLAPolicy`). Unit tests with
   mocked dashboard client; suite green.
3. Neither repo may pin/upgrade across this change without its migration.

## Tests (testprotocols)

1. Model tests: `SteeringScope` validation; `FlowMatch` defaults;
   `UplinkSelectionRule` defaults (`performance_class is None`).
2. Conformance: `SdwanPolicyManager` expected-method set gains the two
   methods in `tests/test_wan_edge_templates.py`.
3. `mypy --strict`; vendor-isolation grep; full suite green.

## Tracking & docs

- **GAPS.md**: move the 2026-06-11 typed path-steering entry to a resolved
  disposition per the file's Workflow section (trigger fired; shape driven
  by the acceptance tests; consumers migrated in step).
- **`docs/sdwan-appliance-protocol-design.md`**: short addition under the
  capability sections noting the typed steering surface and the 4/5
  performance-threshold caveat (cross-reference the v2 subsection).
- **kpn-sdwan validation addendum**: §5.7 row flips to Implemented once the
  MX migration lands.
- **`SPLITS.md`**: no entry (addition, not a split).

## Error handling

Drivers raise the framework's unsupported-capability error where the
product cannot satisfy a rule (notably: `performance_class` set on a
product with fixed per-class SLAs). No new error types.

## Acceptance

- testprotocols: full suite + mypy --strict + vendor grep green.
- vitro-bdd twin and kpn-sdwan MX suites green with the new methods.
- GAPS.md entry resolved; docs updated as listed.
