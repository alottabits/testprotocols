# Proposal: precise types for the released capability protocols and operations

| Field | Value |
| --- | --- |
| Date | 2026-10-05 |
| Use case | `—` (maintainer-originated, no consumer use-case id) — static conformance checking of driver implementations against the capability protocols |
| Round | 1 |
| Status | `under review` |

## Scope

Proposal question 9 asks every added or changed member to be typed precisely, so that
the structural check of a `Protocol` verifies something. Many members released before
that question existed are not typed that way: closed vocabularies are plain `str`,
grammars (port lists, time stamps, classifiers) are text, records are `dict`,
`tuple` or `Any`, and absent values are `""` or `0` sentinels. A type checker then
accepts a driver that returns the wrong shape, and a test reads keys it cannot check.

This proposal brings the released contracts of `testprotocols` and `testoperations` to
precise types, without breaking a caller or a driver in one step:

- every retype is a deprecation (widen, then narrow), stated and not implemented in
  `testprotocols`;
- every new record is a plain frozen dataclass;
- a closed vocabulary becomes an enum whose values are the released spellings;
- a grammar held as text gains an optional typed twin beside the released field
  ("either form");
- a `dict`, `tuple` or `Any` return gains a new member returning a record, and the old
  member is deprecated.

The release that carries it is a MINOR release: it adds 26 mandatory protocol members
(listed per item and under *Breaking for driver authors* in the changelog). An
implementer that cannot support one yet adds a one-line stub raising
`NotSupportedError`.

Item P1 is cross-cutting (the contract model, its dependency and its enforcement); P2 to
P11 are grouped by capability family; P12 is the `testoperations` side. Member and field names are exact, so the `feat:` PR can be checked
against this document item by item. The implementation is on the branch
`feat/precise-types`; the design record is `docs/architecture/precise-types-design.md`
on that branch, whose Deprecations table lists every deprecation one row each.

Existing members that no item touches and that are still imprecise are listed at the end
("Not touched by this proposal"), as question 9 asks.

## Items

### P1 — model the contract model for typing changes, deprecations and their enforcement

**Item**: `P1`, model (the rule set every retype in P2 to P12 follows; changes
`CONTRIBUTING.md` "Versioning" and the rung-5 text of `docs/proposals/README.md`; adds
the conditional `typing_extensions` dependency of `testprotocols` and the static
enforcement of question 9 over both packages).

**Need**: The recorded rung-5 rule (`docs/proposals/README.md`, "How rung 5 is done";
`CONTRIBUTING.md`, "Versioning") announces a deprecation with a runtime
`DeprecationWarning` and normalises an old input form "with a shared helper that emits a
`DeprecationWarning`". Applied to records and protocol modules of `testprotocols`, that
rule puts transition code in the contract package: a record that warns when a released
field is read, converts a released string, or keeps a text field and a typed field in sync
needs `__post_init__`, `__getattr__` or `__setattr__` logic. A first implementation on
the branch did exactly that and the evidence against it is recorded in the branch history:

- records stopped being plain dataclasses (equality, hashing, `dataclasses.replace`,
  truthiness and `dict(record)` each needed special handling, and each produced a fix);
- the warning's stack level named the wrong caller on one supported Python version,
  so the same test passed on 3.13 and failed on 3.12;
- a consumer running its tests with warnings as errors would fail at run time on
  upgrade, for code that type-checks, before it had a chance to migrate;
- the warning cannot tell a driver how to transition anyway: the driver knows its
  device, the contract does not.

This item reopens that recorded decision (question 1) on that evidence. The deprecation
period itself (at least six months and at least one MINOR release) is kept.

Two further needs follow from the rule.

- *The marker's dependency.* The `@deprecated` marker (C2 below) is in the standard
  library from Python 3.13 only. `testprotocols` supports Python 3.12
  (`requires-python = ">=3.12"`) and has no runtime dependency today
  (`dependencies = []`). Without a backport, a 3.12 consumer cannot import the marked
  modules.
- *Enforcement of no explicit `Any`.* Question 9 forbids `Any` in a signature or field.
  Without enforcement a later change can reintroduce one unnoticed. Some released
  signatures cannot drop `Any` without breaking released implementers, because a
  parameter is contravariant and `dict` is invariant: no narrower contract type accepts
  their declarations. The rule needs a precise, counted list of what stays.

**Proposed design**: Six rules.

- **C1. No runtime transition code in `testprotocols`.** No `DeprecationWarning`, no
  conversion, no sync and no field validation in a record or a protocol module.
- **C2. A deprecated protocol member or class** keeps its declaration and gets a docstring
  paragraph, "Deprecated: use `<new>`. Removal not before the first release 6 months
  after the release that deprecates it.", and `@deprecated("<the same sentence>",
  category=None)`, imported from the internal `testprotocols._compat`
  (`warnings.deprecated` on Python 3.13 and later, `typing_extensions.deprecated`
  before; see "The marker's dependency" below). Static type checkers report each use; nothing warns at run time. A
  deprecated parameter or field cannot carry the marker; its docstring states it.
- **C3. A released record field that holds a grammar as text** keeps its name and
  position during the period, its type widened to `<released type> | None`. A field that
  was required stays required; a field that had a default keeps its released default
  text, and `None` passed for it reads as that default. The typed twin is an optional
  keyword-only field defaulting to `None`. A driver fills either form, or both,
  describing the same value; for a field that was required, at least one is filled.
  - *Read a pair*: the typed field when filled, else the text parsed, else the released
    default's meaning; where the released field was required and the typed field cannot
    hold `None` as a value, `ValueError` naming the record and field. Where the typed
    field holds `None` as a value (`SecurityEvent.timestamp`: no time reported;
    `QosRule.classifier`: every frame), a record with both fields `None` reads as that
    `None`.
  - *Write a pair* (a record passed to a write member): the caller fills both forms until
    removal, because a driver not yet updated reads only the text. A driver implementing
    the member reads the typed form when filled, else the text. A caller that fills only
    the typed form leaves the text at its released default, and a driver not yet updated
    acts on that default.
  - *At removal*: the text field goes; the typed field becomes required, or, where the
    text field had a released default, defaults to the typed form of that default. For
    the released-defaulted port pairs (`NatRule` ports, released default `""`, no port;
    `L3Rule` ports, released default `"any"`, any port) that default is `()`, so a caller
    that never set the ports changes nothing, before or after removal.
- **C4. A released `str` field or parameter whose values form a closed vocabulary** is
  annotated `E | str` during the period, `E` a `StrEnum` (or `IntEnum`) whose values are
  the released spellings; the docstring announces the narrowing to `E`. Nothing converts
  at run time: a plain string is stored as given, and a member compares equal to its
  string. A driver converts a parameter once, at its boundary and before any device I/O;
  any other string raises `ValueError`. A new field or parameter, with no released form,
  is annotated `E`.
- **C5. A record new in this release** is a plain frozen dataclass with precise
  annotations: no `__post_init__` checks and no `__setattr__`. A constraint on a field
  (not negative, 1 to 65535, at most another field) is stated in its docstring.
- **C6. `testoperations` carries the transition**: fallback accessors (the new member when
  the driver has it, else the old one), the readers of a text/typed pair, the parsers of
  the released text forms, and the conversion of its own released `str` parameters with a
  `DeprecationWarning` at its caller (P12). Operations honour the period, as the recorded
  rule already requires.

Every deprecation is one row of a Deprecations table (item, replacement, kind,
deprecated in, earliest removal) in `docs/architecture/precise-types-design.md`; the
changelog *Deprecated* sections list exactly those rows. Removal is in the first release
6 months after the release that deprecates it; before tagging a release, every row whose
earliest removal has passed is removed or carried forward (a release-checklist line in
`CONTRIBUTING.md`).

Retype shapes used by the family items: shape 1 (a `str` parameter becomes `E | str`),
1i (a numeric `str` parameter becomes `int | str`), 3 (a model field becomes `E | str`),
4(ii) (a text grammar field gains a typed twin, C3), 4p (a free option string gains typed
keyword-only parameters; passing both raises `ValueError`), 5 (a `dict`, `tuple` or `Any`
return gains a new member returning a record; the old name is deprecated and delegates, or
keeps its released output where that holds more than the record), 6 (announced only: a
return narrowing or a `""` / `0` / `"any"` placeholder becoming `None`; the type changes
at the removal step).

*The marker's dependency.* `packages/testprotocols/pyproject.toml`:
`dependencies = ['typing_extensions>=4.6; python_version < "3.13"']`. The internal module
`testprotocols._compat` re-exports `deprecated` from `warnings` on 3.13 and later and from
`typing_extensions` before; it is the only import site. `4.6` is the first release that
both provides `deprecated` and imports on Python 3.12. On 3.13 and later the package keeps
no runtime dependency; `testoperations` gains none (it depends on `testprotocols`). A
dev-only typing-stub dependency, for the `Console` conformance test in P11, is added to
the workspace, not to either package.

*The explicit-`Any` exemption policy.*

- The static checker runs with "no explicit `Any`" on `testprotocols.*` and
  `testoperations.*` (a per-module override in the workspace `pyproject.toml`). A
  test (`packages/testprotocols/tests/test_typing_ratchet.py`) is the second line of
  defence, because the other checker has no such rule: it counts the non-exempt `Any`
  (ceiling 0 in each package) and pins the exempt lines per class, so a new exemption
  needs a reviewed change. `Callable[..., X]` counts as `Any`; the two in
  `testoperations` become call protocols (P12).
- Exemptions are released signatures only, marked on the `def` line, in two classes.
  - **(a) Deprecation period, 8 lines**, marker `# type: ignore[explicit-any]  # released
    signature kept until removal`: the deprecated forms whose released `dict[str, Any]` /
    `list[Any]` output stays readable until removal: `IpRouting.ping`
    (`json_output=True`), `DnsClient.dns_lookup`, `NmapScanner.nmap`,
    `DeviceManagement.get_running_processes`, `DeviceManagement.read_event_logs`,
    `SipServer.get_rtpengine_stats`, `get_mwi_status`, `get_offline_messages` (deprecated
    in P7, P8 and P11). Each line goes with its member at removal, and the pinned count
    drops with it.
  - **(b) Compatibility, 14 lines**, live members, not tied to a removal.
    `HwConsole.flash_via_bootloader` (two framework-object parameters) and
    `PcapCapture.start_tcpdump(filters: dict[str, Any])`, marker `# released parameter
    kept: implementers declare their own types` (2 lines). The 12 released TR-069 RPCs of
    `Tr069Server` (`GPV`, `SPV`, `GPA`, `SPA`, `FactoryReset`, `Reboot`, `AddObject`,
    `DelObject`, `GPN`, `ScheduleInform`, `GetRPCMethods`, `Download`), marker `# released
    signature kept: vendors extend the parameter model` (12 lines). They keep their
    released signatures: the parameter model is extended per device, so the contract does
    not enumerate it, and a typed layer over it would be a guess.
- If `start_tcpdump` is later deprecated in favour of a renamed member, its exemption
  moves to class (a).

**Mechanism**: deprecate
The rule governs how every retype in this proposal is done (rung 5, rename or retype
with a deprecation period). It adds no member itself; the members it governs are
counted in their family items. The dependency exists only to carry the deprecation
marker. The exemption policy is repository tooling: its 14 compatibility lines keep their
released signatures as they are, and its 8 deprecation-period lines are governed by the
family items that deprecate them.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) — to
`CONTRIBUTING.md` ("Versioning", release checklist), `docs/proposals/README.md` (rung-5
text: Rename, Retype values going in, The deprecation period) and
`docs/architecture/precise-types-design.md`; the `testprotocols` package metadata (the
dependency); the checker configuration in the workspace `pyproject.toml`, the ratchet test
in `testprotocols` and the markers on the exempt lines. The `feat:` PR touches decision
files and takes the second review that implies.

**Affected**: every consumer that pins the next MINOR (type checkers report each use of a
deprecated name; a consumer whose checker treats deprecated use as an error sees errors on
upgrade, not test failures); every driver of a capability named in P2 to P11; the
`testoperations` operations named in P12. The rung-5 *values coming out* rule (opt-in
selector) is unchanged and unused here: returns change by new member names (shape 5).
Consumers on Python 3.12 get `typing_extensions` installed (already a transitive
dependency of most typed environments); on 3.13 and later, nothing. Unchanged by the
exemption policy: `Tr069Server` (12 RPCs), `HwConsole.flash_via_bootloader` and
`PcapCapture.start_tcpdump`. Contributors: a change that adds `Any` fails the checker and
the ratchet.

**Neutrality evidence**:
- No device family is involved in the rule itself; it concerns the Python typing surface.
  The marker is the standard one (PEP 702, `warnings.deprecated` from
Python 3.13, backported in `typing_extensions`). Both static checkers this repository
runs report it: mypy under the `deprecated` error code, pyright under
`reportDeprecated` (an error by default in strict mode). The stack-level failure cited
under Need was observed on CPython 3.12 against 3.13.
- `typing_extensions` is the reference backport of the standard `typing` additions,
  maintained alongside CPython's typing module; PEP 702 names it as the backport of
  `deprecated`.
- TR-069 (Broadband Forum CWMP): the RPC methods carry parameter names from the TR-098 /
  TR-181 data models, which explicitly allow vendor-specific objects and parameters
  under an `X_<OUI>_` or `X_<CompanyName>_` prefix; a CPE's supported parameter set is
  discovered at run time with `GetParameterNames`. A contract that enumerated the
  parameter model would be wrong for every device that extends it.
- `flash_via_bootloader`: every implementer seen (a released open-source implementer
  framework's CPE hardware classes and downstream implementers) raises "not supported" and
  declares the framework's own device types (a dict of TFTP-server objects, a
  termination-system object) for the arguments; `Mapping[str, object]` and `object` were
  tried and break those declarations.
- `start_tcpdump(filters)`: implementers declare `dict` parameters; `Mapping` would break
  them for the same reason.
- The checkers: mypy has `disallow_any_explicit`; pyright has no equivalent rule, hence the
  ratchet test.

### P2 — capability protocol packet filter, firewall, NAT and connection tracking

**Item**: `P2`, capability protocol (`PacketFilter`, `Firewall`, `Nat`, `Conntrack`) and
models (`FirewallRule`, `NatRule`, `PortMapping`, `Connection`).

**Need**: Chains, rule actions, NAT modes, mapping protocols and default policies are
closed sets typed as `str`. Port fields are free text (`"80"`, `"1000-2000"`, `"any"`,
`""`) with no stated grammar, so a type checker cannot tell a port list from a name. The
rule counters return a bare `(int, int)` tuple. The existing `RuleProtocol` covers the
transport and is reused; no other existing model holds a port range or a counter pair.

**Proposed design**:

- New enums in `testprotocols.models`: `Chain` (`INPUT`, `OUTPUT`, `FORWARD`),
  `FirewallRuleAction` (`ALLOW`, `DENY`, `REJECT`, `LOG`), `NatMode` (`SNAT`, `DNAT`,
  `ONE_TO_ONE = "1to1"`), `PortMappingProtocol` (`TCP`, `UDP`, `TCP_UDP = "tcp-udp"`),
  `DefaultAction` (`ACCEPT`, `DROP`, `REJECT`). Every value is the released spelling.
- New records: `PortRange(first: int, last: int)` (frozen, inclusive, `1 <= first <= last
  <= 65535` stated; `PortRange.single(port)`); `RuleCounters(packets: int, bytes: int)`
  (frozen, not negative).
- New mandatory members:
  - `PacketFilter.get_rule_counter_values(chain: Chain | str, name: str) -> RuleCounters`
    (so also `Firewall`, which inherits `PacketFilter`);
  - `Nat.get_nat_rule_counter_values(name: str) -> RuleCounters`.
- Deprecated members (shape 5): `PacketFilter.get_rule_counters`,
  `Nat.get_nat_rule_counters`.
- Parameters (shape 1): every `PacketFilter` `chain` is `Chain | str`;
  `set_default_policy(policy: DefaultAction | str)`;
  `Nat.list_nat_rules(mode: NatMode | str | None)`; `Conntrack` `protocol` on
  `list_connections`, `count_connections`, `get_connection`, `drop_connection` is
  `RuleProtocol | str` (a `protocol` of `any` is refused: a flow has one transport). The
  `state` filters stay `str`.
- Fields (shape 3): `FirewallRule.action: FirewallRuleAction | str`,
  `FirewallRule.protocol: RuleProtocol | str`, `NatRule.mode: NatMode | str`,
  `NatRule.protocol: RuleProtocol | str = "any"`,
  `PortMapping.protocol: PortMappingProtocol | str`,
  `Connection.protocol: RuleProtocol | str`. `Connection.state` stays `str`: the released
  contract listed the TCP states, `UNREPLIED` and `ASSURED` "or driver-specific values",
  so the device's own word is kept and the docstring lists the common ones.
- Port pairs (shape 4(ii), C3):
  - `FirewallRule.dst_port: str | None` (required, released position) beside
    `dst_ports: tuple[PortRange, ...] | None = None` (keyword-only). `"any"` reads as
    any port. At removal `dst_ports` becomes required. With neither filled the reader
    raises `ValueError`.
  - `NatRule.dst_port: str | None = ""` and `translated_port: str | None = ""` beside
    `dst_ports` and `translated_ports: tuple[PortRange, ...] | None = None`
    (keyword-only). `""` (and `"any"`) read as no port. At removal the typed fields
    default to `()`.
  - The empty tuple means no port restriction.
- Announced only (shape 6): `get_default_policy -> str` narrows to `DefaultAction`;
  `NatRule.src_cidr`, `dst_cidr`, `translated_src`, `translated_dst` `""` placeholders
  become `str | None`.
- Every write here (`add_rule`, `add_nat_rule`, `set_default_policy`, the conntrack drop)
  already has a read in the contract (`list_rules` / the rule getters, `list_nat_rules`,
  `get_default_policy`, `get_connection`); the new counter members are reads.

**Mechanism**: extend
Two new mandatory members (`get_rule_counter_values`, `get_nat_rule_counter_values`).
The vocabulary and port retypes in the same item are rung-5 `deprecate` changes (widen,
then narrow) and ride the same MINOR release. No lower rung fits: the counter tuple is a
return type, which only a new member name can change without breaking implementers.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.packet_filter`, `testprotocols.nat`, `testprotocols.conntrack`,
`testprotocols.models` (`firewall.py`, `ports.py`).

**Affected**: implementers of `PacketFilter`, `Firewall` and `Nat` (two new members; a
stub raising `NotSupportedError` is allowed); readers of `FirewallRule.dst_port`,
`NatRule.dst_port` / `translated_port` (now `str | None`); callers building rules for
`PacketFilter.add_rule` and `Nat.add_nat_rule` (fill both forms until removal);
`testoperations.segmentation` (P12). `testoperations` calls neither deprecated counter
member.

**Neutrality evidence**: Reviewed families: the host packet filters (Linux netfilter
through iptables and nftables) and the managed security appliances of the SD-WAN
appliance design (Meraki MX, Catalyst SD-WAN, FortiGate, Prisma SD-WAN, Arista VeloCloud
Edge).
- Chains and default policies: `INPUT` / `OUTPUT` / `FORWARD` and `ACCEPT` / `DROP` are
  netfilter's own built-in chains and policy targets; `PacketFilter` is a host-filter
  capability and uses that vocabulary as released. `REJECT` is the netfilter target and
  the appliance action alike.
- Ports: every family expresses a set of single ports and inclusive ranges, with its own
  separator. iptables uses `--dport 1000:2000` and `-m multiport --dports 80,443`;
  nftables `dport { 80, 443, 1000-2000 }`; the Meraki MX firewall API takes a
  comma-separated list or `any`; FortiGate service objects take `tcp-portrange` entries
  `low[-high]`. A tuple of inclusive `PortRange` holds each without a grammar. The
  documentation of Catalyst SD-WAN, Prisma SD-WAN and VeloCloud policy port fields was
  not checked line by line for this item; the evidence there is thin.
- NAT modes: source NAT, destination NAT (port forwarding) and 1:1 NAT are the three
  forms on Meraki MX (`1:1 NAT`, port forwarding) and on FortiGate (IP pools, virtual
  IPs); netfilter has `SNAT` / `MASQUERADE` and `DNAT`.
- Counters: iptables `-L -v -x` and nftables `counter` report packets and bytes per rule;
  FortiGate reports per-policy packet and byte counts. The Meraki MX dashboard API was not
  found to report per-rule counters; a driver there raises `NotSupportedError`.
- Connection states: the netfilter conntrack table reports TCP states plus `UNREPLIED` /
  `ASSURED`; appliance session tables use their own words, hence `str`.

### P3 — model SD-WAN appliance rules, security events and placeholders

**Item**: `P3`, model (`L3Rule`, `SecurityEvent`, `UplinkStatus`,
`NetworkAttachment`) and capability protocol (`SdwanPolicyManager.apply_policy`).

**Need**: `L3Rule.src_port` / `dst_port` hold port text (`"any"` by default) and
`SecurityEvent.ts` holds ISO-8601 text: grammars a type checker cannot check.
`SdwanPolicyManager.apply_policy` takes `dict[str, Any]`, an escape hatch that the typed
steering and SLA members already cover. Several fields use `""` or `"any"` for absent.
`PortRange` (P2) and `datetime` are the existing types that fit; no new record is needed.

**Proposed design**:

- `L3Rule.src_port: str | None = "any"`, `dst_port: str | None = "any"` beside
  `src_ports`, `dst_ports: tuple[PortRange, ...] | None = None` (keyword-only; the empty
  tuple means any port). At removal the typed fields default to `()`.
- `SecurityEvent.ts: str | None` (required, released position) beside
  `timestamp: datetime | None = None` (keyword-only; `None`: the product reports no
  time). The text parser is `datetime.fromisoformat`; a timezone-naive value stays naive
  and no zone is assumed. At removal `timestamp` becomes required.
- `SdwanPolicyManager.apply_policy(policy: dict[str, object]) -> None`: deprecated with no
  successor (the typed members `configure_sla_policy`, `set_uplink_selection`,
  `set_default_uplink`, `set_active_active_vpn` cover it). The parameter stays a `dict`:
  a `Mapping` parameter would make an implementer declaring `dict` fail to conform.
- Announced only (shape 6): `L3Rule.src_cidr` / `dst_cidr` (`"any"`),
  `UplinkStatus.ip`, `gateway`, `public_ip`, `primary_dns` and
  `NetworkAttachment.segment` (`""`) become `str | None`.
- Writes: the `L3Firewall.set_*_rules` members already have their list reads; callers fill
  both port forms until removal (C3).

**Mechanism**: deprecate
Retypes with a deprecation period only (field twins, announced narrowings, one
deprecated member with no successor); no new mandatory member.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.models` (`sdwan_appliance.py`, `network_attachment` model),
`testprotocols.sdwan_policy_manager`; the SD-WAN appliance design document gains the
`timestamp` note.

**Affected**: readers of `L3Rule` ports and `SecurityEvent.ts` (now `… | None`); callers
of the `L3Firewall.set_*_rules` members; implementers of `SdwanPolicyManager` (no new
member; a caller's `dict[str, str]` variable passed to `apply_policy` no longer
type-checks). `testoperations` (`segmentation`, P12) builds rules with both forms.

**Neutrality evidence**: Reviewed families, as recorded in the SD-WAN appliance design:
Meraki MX, Catalyst SD-WAN, FortiGate, Prisma SD-WAN, Arista VeloCloud Edge.
- Ports: as in P2. The Meraki MX L3 firewall API's `srcPort` / `destPort` take a
  comma-separated list or `any`; FortiGate uses service objects with port ranges.
- Security-event time: the Meraki security-events API reports `ts` as ISO-8601 text with
  a zone; FortiGate logs carry `date` and `time` fields and an `eventtime` epoch value;
  Catalyst SD-WAN event records carry an epoch time in milliseconds. A `datetime` holds
  each; the text form only fits the first. The Prisma SD-WAN and VeloCloud event time
  formats were not checked for this item.
- `apply_policy`: no reviewed family's policy shape is a single free dictionary; the
  typed members were derived from the shared concepts in the design.

### P4 — capability protocol WAN edge links and router telemetry

**Item**: `P4`, capability protocol (`Router`) and models (`LinkStatus`,
`LinkHealthReport`, `UplinkState`, `VPNPeerStatus`, `TrafficShapingRule`, `Telemetry`).

**Need**: `LinkStatus.state` and `LinkHealthReport.state` are `str` over a closed set.
`Router.get_telemetry` returns `dict[str, Any]` and names no key. `VPNPeerStatus` and
`TrafficShapingRule` have no capability using them. The existing `UplinkState` holds the
link vocabulary and is reused (it gains one member); `VpnPeerStatus` and `ShapingRule` are
the existing typed models for the concerns the two orphans describe, but `ShapingRule` is
not a drop-in (its match is one `(match_type, value)` pair, not a dict match).

**Proposed design**:

- `LinkStatus.state` and `LinkHealthReport.state`: `UplinkState | str` (shape 3).
  `UplinkState` gains `UNKNOWN` (a link with no health data, a value a released
  implementer reports).
- New record `Telemetry(uptime_seconds: float, cpu_load_percent: float | None = None,
  mem_used_percent: float | None = None)` (frozen; each finite and not negative, stated).
- New mandatory member `Router.read_telemetry() -> Telemetry`.
- `Router.get_telemetry` is deprecated in its favour and its return narrows to
  `Mapping[str, float]` (was `dict[str, Any]`): a driver returns the reported fields of
  `read_telemetry()`.
- `VPNPeerStatus` and `TrafficShapingRule`: deprecated classes with no successor, still
  exported; `TrafficShapingRule.match` is `Mapping[str, object]`.
- Announced only: `LinkStatus.ip_address` (`""`: no address) becomes `str | None`.
- `AppFlow.category` stays `str`: the product's own word, with the `ApplicationCategory`
  values listed as the common ones.

**Mechanism**: extend
One new mandatory member (`Router.read_telemetry`). The return-type narrowing of
`get_telemetry` is breaking for an implementer whose declared values are not floats and is
listed under *Breaking for driver authors*; the field and class changes are rung-5
`deprecate`. A defaulted field cannot replace a `dict` return.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.router`, `testprotocols.models` (`wan_edge.py`); the site-to-site VPN and
SD-WAN appliance design documents record the two orphan deprecations.

**Affected**: implementers of `Router` (one new member; `get_telemetry` declarations must
be float-valued); readers of `LinkStatus.state` / `LinkHealthReport.state`; any consumer
importing `VPNPeerStatus` or `TrafficShapingRule` (type checkers report the use).
`testoperations` calls neither `get_telemetry` nor the orphans.

**Neutrality evidence**:
- Telemetry: the evidence is thin and the record is deliberately small. The released
  docstring named no key; the only released implementer (a Linux router)
  returns `uptime_seconds`, `cpu_load_percent`, `mem_used_percent` as floats and omits CPU
  when it cannot read it. Those three are also the common subset of what the reviewed
  SD-WAN families report (Meraki MX device performance score and uptime, FortiGate system
  resource usage, Catalyst SD-WAN device CPU and memory statistics), but no further field
  (temperature, load average) is added without an implementer reporting it.
- Uplink state: Meraki MX reports `active`, `ready`, `failed`, `not connected`; Catalyst
  SD-WAN reports interface and tunnel up/down; FortiGate SD-WAN health checks report
  alive/dead with SLA status. Each maps to `up`, `down`, `degraded` or `unknown` in the
  driver.

### P5 — capability protocol switch QoS classification

**Item**: `P5`, capability protocol (`SwitchQos.set_rules`) and models (`QosRule`,
`QosClassifier`, `StormControlConfig`, `StormControlUnit`).

**Need**: `QosRule.match` is a free text "classifier expression" with no grammar, so a
rule's selection cannot be checked or compared across drivers. `StormControlConfig`
carries a threshold with no unit. No existing model expresses a classifier; `RuleProtocol`
and `PortRange` (P2) are reused for its parts.

**Proposed design**:

- New record `QosClassifier(vlan: int | None = None, protocol: RuleProtocol | None =
  None, src_ports: tuple[PortRange, ...] = (), dst_ports: tuple[PortRange, ...] = ())`
  (frozen; a field left out places no restriction; `vlan` 1 to 4094; at most one source and
  one destination range, stated).
- `QosRule.match: str | None` (required, released position) beside
  `classifier: QosClassifier | None = None` (keyword-only; `None`: every frame). At removal
  `classifier` becomes required.
- The text parser (in `testoperations`, C6) reads a comma list of `key=value` terms over
  `vlan`, `protocol` (any letter case; `any` is `RuleProtocol.ANY`), `src_port`,
  `dst_port` (a port or an `a-b` range). Text that is not such a list has no classifier:
  the reader gives `None` and `match` keeps the text as given. A term given twice raises
  `ValueError`.
- New enum `StormControlUnit` (`PERCENT`, `PPS`) and field
  `StormControlConfig.unit: StormControlUnit | None = None` (`None`: as the driver reads
  it; released drivers ignore it).
- Write: `SwitchQos.set_rules` has its list read; callers fill both forms until removal.

**Mechanism**: deprecate
`QosRule.match` is retyped by a typed twin with a deprecation period. The
`StormControlConfig.unit` addition is a `defaulted field` (rung 3) and needs nothing
further.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.models` (`switch.py`); the L2 switch design document gains the classifier
note.

**Affected**: readers of `QosRule.match` (now `str | None`); callers of
`SwitchQos.set_rules`; switch drivers (no new member).

**Neutrality evidence**: Reviewed families, as recorded in the L2 switch design: Meraki
MS225, Aruba 1960, Catalyst 9200L, Juniper EX2300, Omada, UniFi (Arista EOS as a confirming
check).
- The Meraki MS QoS rules API has exactly these selectors: `vlan`, `protocol`
  (`TCP`, `UDP`, `ANY`), source and destination port or port range, with a DSCP marking.
- Catalyst 9200L and Arista EOS classify through class maps matching an access list
  (protocol, ports) and, where supported, a VLAN; Juniper EX classifies through firewall
  filter terms (`protocol`, `source-port`, `destination-port`) setting a forwarding
  class. A driver composes the classifier into those constructs.
- Aruba 1960, Omada and UniFi expose QoS mainly as port or DSCP/802.1p trust settings;
  classifier support by port and protocol was not confirmed for them, so the evidence
  there is thin and a driver may raise `NotSupportedError` for a classifier it cannot
  express.
- Storm-control units: Catalyst and Arista take a level in percent or packets per
  second; Juniper EX takes bandwidth or percent; hence `PERCENT` / `PPS` with `None` for
  "as the driver reads it".

### P6 — capability protocol Wi-Fi vocabularies and channels

**Item**: `P6`, capability protocol (`WifiBss`, `WifiRadio`, `WifiRf`, `WifiMesh`,
`WifiClient`, `WifiRadioWhiteBox`) and models (`WifiBssConfig`, `WifiStation`,
`WifiNeighbor`, `WifiChannelUtilization`, `WifiRadioStats`, `WifiMeshLink`, `WifiAcl`,
`WifiMeshStatus`, `WifiMeshNode`).

**Need**: Bands, security modes, management-frame protection, ACL modes, PHY modes,
channel widths and mesh roles are closed sets typed `str` (or `int`).
`WifiClient.iwlist_supported_channels` returns channel numbers as text. No existing enum
covers any of them.

**Proposed design**:

- New enums, every value the released string: `WifiBand` (`GHZ_2_4 = "2.4GHz"`,
  `GHZ_5`, `GHZ_6`), `WifiSecurityMode` (`OPEN`, `OWE`, `WPA2_PSK`, `WPA2_EAP`,
  `WPA3_SAE`, `WPA3_EAP`, `WPA3_EAP_192 = "WPA3-EAP-192"` (WPA3-Enterprise 192-bit),
  `WPA2_WPA3_PSK_MIXED`, `WPA2_WPA3_EAP_MIXED`), `MfpMode` (`OFF`,
  `OPTIONAL`, `REQUIRED`), `WifiAclMode` (`DISABLED`, `ALLOW`, `DENY`), `WifiPhyMode`
  (`A`, `B`, `G`, `N`, `AC`, `AX`, `BE`), `ChannelWidth` (`IntEnum`: 20, 40, 80, 160,
  320), `MeshRole` (`CONTROLLER`, `AGENT`, `CONTROLLER_AND_AGENT`, `UNCOMMISSIONED`).
- New mandatory members (shape 5):
  - `WifiClient.supported_channels(band: WifiBand) -> list[int]`;
    `iwlist_supported_channels` deprecated;
  - `WifiRadio.get_modes(band: WifiBand | str) -> frozenset[WifiPhyMode]`: the set of PHY
    modes the radio on *band* currently operates (a radio runs several at once; TR-181
    `OperatingStandards` is a list). `WifiRadio.get_mode(band: WifiBand | str) -> str` is
    deprecated in its favour and keeps its released `str` return (a driver may return a
    compound form such as `"n/ac/ax"`) until removal.
- Parameters (shape 1): every `band` of `WifiBss.create_bss`, `WifiRadio`, `WifiRf`,
  `WifiRadioWhiteBox.inject_radar_event` and `WifiMesh.set_backhaul_band` is
  `WifiBand | str`; `WifiBss.create_bss(security_mode, mfp)` and
  `set_security(mode, mfp)` are `WifiSecurityMode | str`, `MfpMode | str` (`mfp` default
  stays `"optional"`); `WifiBss.set_acl_mode(mode: WifiAclMode | str)`;
  `WifiRadio.set_mode(mode: WifiPhyMode | str)` (a compound mode such as `"n/ac/ax"`
  names no member and stays the driver's own `str`; after it the radio may operate further
  modes as well, which `get_modes` reports); `WifiRadio.set_bandwidth` takes
  `ChannelWidth | int`. Shape 1i: `WifiClient.set_wlan_scan_channel(channel: int | str)`.
- Fields (shape 3): `band` of `WifiBssConfig`, `WifiStation`, `WifiNeighbor`,
  `WifiChannelUtilization`, `WifiRadioStats`, `WifiMeshLink`; `WifiBssConfig.security_mode`
  / `mfp`; `WifiAcl.mode`; `role` of `WifiMeshStatus`, `WifiMeshNode`.
- Management-frame protection forced by the security mode (a docstring rule on
  `WifiBss.create_bss` and `set_security`): `WPA3_SAE`, `WPA3_EAP`, `WPA3_EAP_192` (the
  WPA3-only modes), `OWE`, and any security mode on a BSS on 6 GHz require MFP. For these a
  driver applies `REQUIRED` whatever *mfp* says, and the read-back (`get_bss_config`)
  reports `REQUIRED`.
- `WifiRadioStats.tx_retries` and `tx_failed` become `int | None` (released: `int`), still
  required and in their released positions; `None` means the device reports no per-radio
  count, and `0` is never a stand-in. This is a type change of a released field with **no
  deprecation period**: a reader must handle `None` from this release on. The reason is
  that the standard data models define no such count (TR-181 keeps retry counters per SSID;
  Wi-Fi Data Elements has no radio counters), and several access-point family APIs report
  none, so a required `int` forced drivers to invent a value.
- Announced only (shape 6): `WifiRadio.list_radios -> list[WifiBand]`,
  `get_bandwidth -> ChannelWidth`.
- Left as text on evidence: `WifiNeighbor.security_mode` (a best-effort identification of
  a foreign network); `WifiClient.wifi_client_connect(security_mode: str | None)` (a client
  key-management word, not an access-point mode); `iwlist_supported_channels(wifi_band:
  str)` (released callers pass `"2.4"` / `"5"`); `WifiStation.capability_flags:
  list[str]` (the device's own words); `WifiMeshWhiteBox.get_raw_easymesh_tlvs
  (message_type)` (no source lists the message names yet).

**Mechanism**: extend
Two new mandatory members (`WifiClient.supported_channels`, `WifiRadio.get_modes`). The
vocabulary retypes and the `get_mode` deprecation are rung-5 `deprecate` changes in the
same release. The `WifiRadioStats` counter widening is breaking for readers with no
deprecation period, listed under *Breaking for driver authors*: no lower rung fits,
because a field whose released type cannot hold the absent value has no form to keep.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.wifi_bss`, `wifi_radio`, `wifi_rf`, `wifi_mesh`, `wifi_client`,
`testprotocols.models` (`wifi.py`).

**Affected**: implementers of `WifiClient` and `WifiRadio` (one new member each); drivers
of every Wi-Fi capability (convert at the boundary); `WifiBss` drivers (apply `REQUIRED`
MFP for the WPA3-only modes, `OWE` and 6 GHz, and read it back so); readers of the listed
fields (now `E | str`); readers of `WifiRadioStats.tx_retries` / `tx_failed` (handle
`None`) and drivers whose device reports no per-radio count (fill `None`); callers of
`get_mode` (type checkers report the use). `testoperations` calls none of the changed
members.

**Neutrality evidence**: No reviewed-family list was recorded for the Wi-Fi domain before
this proposal; this list is the reviewed-family list it records:
- hostapd-based access points (OpenWrt; prplOS with prplMesh);
- a Broadcom- or Qualcomm-based residential gateway stack;
- managed enterprise access points: Meraki MR (Dashboard API) and Aruba (AOS 8 and AOS 10,
  Instant, Central);
- Airties: its mesh controller and agent software on gateways and extenders, including
  prplOS-based gateways, reached through Wi-Fi EasyMesh and Wi-Fi Data Elements (TR-181
  `Device.WiFi.DataElements.`, over TR-369/USP) and its cloud management;
- a Linux station using wpa_supplicant.

The reference is the standard data model, checked first: Wi-Fi Data Elements (JSON schema
v3.0), Wi-Fi EasyMesh v6.1 and TR-181 Device:2.21 (`Device.WiFi.Radio`, `AccessPoint`,
`AssociatedDevice`, `NeighboringWiFiDiagnostic()` and `DataElements`). Each family was then
compared to it from its public material. Airties publishes no field-level API of its own:
its public material names EasyMesh controller software for gateways and extenders, an
integration on a prplMesh agent under prplOS, TR-369/TR-181 management of gateways, and
cloud APIs for operators that are not published; its public code is the EasyMesh
controller it contributes to an open-source gateway stack, which serves
`Device.WiFi.DataElements.` with `X_AIRTIES_` extensions. Its evidence is therefore Data
Elements and EasyMesh. The Broadcom and Qualcomm SDKs are not public; that family is
evidenced through TR-181 only.
The vocabularies themselves come from IEEE 802.11 (bands; widths up to 320 MHz from
802.11be; the a to be amendments; MFP from 802.11w) and the Wi-Fi Alliance security
programmes (WPA2, WPA3, Enhanced Open).

- Bands: TR-181 `Radio.SupportedFrequencyBands` uses exactly `2.4GHz`, `5GHz`, `6GHz`.
  Data Elements (`band_t`), Meraki and Aruba write `2.4`, `5` (`5.0`), `6`: a spelling
  difference mapped in the driver. Data Elements also has `All`, the UNII sub-bands and
  `Sub_1GHz`; a radio per 5 GHz sub-band (dual 5 GHz) is the known one-radio-per-band gap
  of `WifiRadio`.
- Widths: TR-181 `OperatingChannelBandwidth` is text (`20MHz` to `320MHz`), mapped to the
  number. TR-181 also has `80+80MHz`, `320MHz-1`/`320MHz-2` and `Auto`; Meraki writes
  `0` or `auto`. `ChannelWidth` has none of them: 80+80 reads back as 160, the two 320 MHz
  channelisations collapse, and an automatic width can be neither set nor read (a
  recorded gap, like automatic channel).
- PHY modes: TR-181 `SupportedStandards` and `OperatingStandards` use exactly `a`, `b`,
  `g`, `n`, `ac`, `ax`, `be` (hostapd: `hw_mode` plus `ieee80211n/ac/ax/be` flags), but
  `OperatingStandards` is a list: the released compound text (`n/ac/ax`) is that list.
  Meraki exposes only an 802.11ax switch per band, Aruba per-SSID HT/VHT/HE switches: a
  single-generation `set_mode` raises `NotSupportedError` there. `get_modes` returns the
  `OperatingStandards` list as a set.
- Security modes, against TR-181 `Security.ModesSupported`: `None`, `OWE`,
  `WPA2-Personal`, `WPA2-Enterprise`, `WPA3-Personal`, `WPA3-Enterprise`,
  `WPA3-Personal-Transition` map one to one. TR-181 has no WPA2/WPA3-Enterprise transition
  value, so a TR-181-only driver cannot express `WPA2_WPA3_EAP_MIXED`. WPA3-Enterprise
  192-bit (Meraki `WPA3 192-bit Security`, Aruba `wpa3-cnsa`) is `WPA3_EAP_192`. No member
  covers per-client PSKs (Meraki iPSK, Aruba MPSK), the DPP key management of Data Elements and EasyMesh
  (`dpp`, `dpp+sae`), TR-181 `WPA3-Personal-Compatibility`, or legacy WPA and WEP; a
  device read in such a mode keeps the plain `str` form until the field narrows. Meraki
  splits the mode into `authMode` and `wpaEncryptionMode`, Aruba into `opmode` and
  `opmode-transition` (on by default, so `wpa3-sae-aes` reads back as the transition
  mode unless it is turned off); hostapd uses `wpa_key_mgmt`.
- MFP: TR-181 and Data Elements `MFPConfig` (`Disabled`, `Optional`, `Required`), hostapd
  and wpa_supplicant `ieee80211w=0/1/2`, Meraki `dot11w.enabled`/`required` and Aruba
  `mfp-capable`/`mfp-required` all give the three values. The standards tie MFP to the
  mode: WPA3-Personal only, WPA3-Enterprise, OWE and 6 GHz require it, the WPA3
  transition mode makes it optional, and Aruba ignores the MFP settings under any WPA3
  mode. A device therefore reads back `required` where `optional` was passed with such a
  mode, which the `create_bss` / `set_security` rule now states.
- ACL modes: hostapd `macaddr_acl` (0: accept unless denied; 1: deny unless accepted)
  gives all three. TR-181 `AccessPoint` has only an allow list (`MACAddressControlEnabled`,
  `AllowedMACAddress`), so `DENY` has no standard TR-181 form; Data Elements blocks
  stations network-wide (`Network.STABlock`), and the Airties controller adds a per-BSS
  block (`X_AIRTIES_ClientAssocControl()`). Meraki has no per-SSID MAC list (client policy
  `Blocked` is network-wide; `Whitelisted` bypasses the splash page, not association), so
  `ALLOW` raises `NotSupportedError` there and `DENY` is network-wide. Aruba restricts by
  MAC authentication and a client deny list (`blacklist`).
- Mesh roles: EasyMesh 4.1 defines a Multi-AP device holding a Controller only, an Agent
  only, or both, which `CONTROLLER`, `AGENT`, `CONTROLLER_AND_AGENT` mirror; an agent
  not yet onboarded is the EasyMesh "Enrollee Multi-AP Agent" (`UNCOMMISSIONED`). Data
  Elements gives the role as two fields, `EasyMeshControllerOperationMode` and
  `EasyMeshAgentOperationMode` (`NotSupported`, `SupportedNotEnabled`, `Running`); the
  driver combines them. prplMesh and the Airties controller use these roles. Meraki
  (gateway, repeater) and Aruba Instant (mesh portal, mesh point) have a cloud or virtual
  controller, so their root node has no `MeshRole` member (a known gap; hop count 0
  still identifies it).
- Mesh link (`WifiMeshLink`): Data Elements backhaul `SignalStrength` is RCPI
  (0 to 220) and rates are in kbit/s, converted to dBm (RCPI / 2 − 110) and Mbit/s. An
  EasyMesh backhaul may be wired (Data Elements `LinkType` `Ethernet`, `MoCA`, `G.hn`);
  `WifiMeshLink` cannot express one, and `backhaul_link=None` reads as "no uplink". Meraki
  reports route throughput (`latestMeshPerformance.mbps`), not band, channel or signal.
- Supported channels (`list[int]`): TR-181 `PossibleChannels` is a text list with `n-m`
  ranges, expanded by the driver; Data Elements, Meraki (`validAutoChannels`) and Aruba
  give integers; a Linux station reads them from nl80211.
- `WifiNeighbor`: TR-181 `NeighboringWiFiDiagnostic()` gives SSID, BSSID, channel,
  `SignalStrength` in dBm, `OperatingFrequencyBand` and a closed `SecurityModeEnabled`
  list (`None`, `WEP`, `WPA`, `WPA2`, …, `WPA3-SAE`, `OWE`), whose spellings a driver
  passes through as `security_mode`. Data Elements `NeighborBSS` gives signal as RCPI,
  no security mode (the driver passes `""`) and the band through the operating class;
  `last_seen` comes from the scan time stamp. Meraki Air Marshal gives channels without a
  band (a 6 GHz channel number is ambiguous) and Aruba Instant gives SNR, not signal
  (signal = SNR + noise floor).
- `WifiChannelUtilization` (percent): Data Elements `Utilization`, `Transmit`,
  `ReceiveSelf` and `ReceiveOther` are 0 to 255 (255 = 100 %), converted as
  `round(v * 100 / 255)`, with `rx_pct` their sum and no interference term; hostapd's BSS
  load and the nl80211 busy, transmit and receive times convert the same way. TR-181
  `Radio` has no utilisation outside `DataElements`. Meraki gives total, Wi-Fi and
  non-Wi-Fi percentages as decimals: `busy_pct` and `interference_pct` are filled, the
  Wi-Fi share has no field. Aruba Central documents transmit, receive and non-Wi-Fi
  interference shares per radio.
- `WifiRadioStats`: TR-181 `Radio.Stats` gives bytes and packets but its retry counters
  are per SSID (`SSID.Stats.RetransCount`, `FailedRetransCount`); Data Elements has no
  radio counters (BSS byte counters in KiB or MiB, `ByteCounterUnits`); Aruba Instant
  gives frames, bytes and drops without retries; Meraki has no radio counters. The required
  `tx_retries` and `tx_failed` therefore have no source on most of these families, hence
  `int | None`.
- `WifiStation`: TR-181 `AssociatedDevice` gives signal in dBm, SNR in dB, rates in kbit/s
  (`LastDataDownlinkRate`, converted to Mbit/s) and `AssociationTime` as a date-time;
  Data Elements gives signal as RCPI, `LastConnectTime` in seconds since association and
  no SNR. The band comes from the radio the BSS runs on. Meraki gives per-client RSSI
  and SNR history but no association counters; Aruba Instant gives SNR, rate in Mbit/s,
  bytes, frames and retries.

These differences are resolved as recorded: a spelling, unit or encoding difference is a
driver mapping; a value or source that a family lacks is a known gap, for which the
driver raises `NotSupportedError` or, for a read, keeps the plain `str` form while the
field accepts it.

Resolved on the branch: PHY modes as a set (`get_modes`, `get_mode` deprecated);
WPA3-Enterprise 192-bit (`WPA3_EAP_192`); MFP forced by the security mode and 6 GHz (the
`create_bss` / `set_security` rule); per-radio retry and failed counts that a family does
not report (`WifiRadioStats.tx_retries` / `tx_failed` as `int | None`).

Known gaps, kept as recorded:
- MAC ACL mode: `DENY` has no standard TR-181 form, and on a cloud-managed family with no
  per-SSID MAC list `ALLOW` is unsupported and `DENY` is network-wide;
- one radio per band: a radio per 5 GHz sub-band (dual 5 GHz) has no `WifiRadio` form;
- channel widths: 80+80 MHz, the two 320 MHz channelisations and an automatic width;
- security modes with no member: the WPA2/WPA3-Enterprise transition on a TR-181-only
  driver, per-client PSKs, DPP key management, WPA3-Personal compatibility mode, legacy
  WPA and WEP;
- a mesh root on a cloud- or virtually-managed family has no `MeshRole` member;
- a wired mesh backhaul has no `WifiMeshLink` form;
- a neighbour on a family that reports channels without a band, and signal given as SNR,
  need a driver derivation;
- the Wi-Fi share of channel utilisation on a family that reports only total and
  non-Wi-Fi shares has no field.

### P7 — capability protocol voice and SIP

**Item**: `P7`, capability protocol (`SipPhone`, `SipServer`) and models (`PhoneState`,
`RtpStats`, `MwiStatus`, `OfflineMessage`).

**Need**: `SipPhone.wait_for_state` takes a free `str` over the closed set of call states
its own `is_*` predicates define. `SipServer.get_rtpengine_stats`, `get_mwi_status` and
`get_offline_messages` return dicts, the last with a time stamp as text.
`SipServer.verify_sip_message(since: Any)`. No existing model covers any of them.

**Proposed design**:

- New enum `PhoneState` (`IDLE`, `DIALING`, `INCALL_DIALING`, `RINGING`, `CONNECTED`,
  `INCALL_CONNECTED`, `HOLD = "hold"`, `DIALTONE`, `INCALL_DIALTONE`, `CALL_ENDED`,
  `CODE_ENDED`, `CALL_WAITING`, `CONFERENCE`, `BUSY`, `NOT_ANSWERED`): one per `is_*`
  predicate of `SipPhone`. `SipPhone.wait_for_state(state: PhoneState | str)`; an unknown
  word raises `ValueError`.
- New records (frozen, counts not negative): `RtpStats(engaged, sessions)`,
  `MwiStatus(waiting, new, old)`, `OfflineMessage(sender, body, stored_at: datetime)`.
- New mandatory members: `SipServer.read_rtpengine_stats() -> RtpStats`,
  `read_mwi_status(user: str) -> MwiStatus`,
  `read_offline_messages(user: str) -> list[OfflineMessage]`. The three old names are
  deprecated; a driver keeps them, returning the record's fields as the released dict
  (`get_offline_messages` may keep returning the stored time text unchanged).
- `SipServer.verify_sip_message(message_type: str, since: datetime | None)` (was
  `since: Any`; an implementer may keep `Any`, which still conforms).
- Left as `str` on evidence: presence statuses (`set_presence`, `notify_presence`,
  `get_user_presence`) and `verify_sip_message(message_type)` (SIP methods, response codes
  and log markers): the provider's own words, listed in the docstrings. An `int` for a
  response code was considered and deferred: widening the parameter makes an implementer
  declaring `str` fail to conform.

**Mechanism**: extend
Three new mandatory members. The `PhoneState` and `since` retypes are rung-5 `deprecate`
changes in the same release.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.sip_phone`, `testprotocols.sip_server`, `testprotocols.models`
(`voice.py`).

**Affected**: implementers of `SipServer` (three new members); callers of
`wait_for_state`; a caller that passed a text marker as `since` (outside the typed
contract; no longer type-checks). `testoperations` calls none of these members.

**Neutrality evidence**: No reviewed-family list was recorded for the voice domain before
this proposal; the reviewed-family list it records: a SIP proxy/registrar (Kamailio or OpenSIPS) with an RTP
relay (rtpengine), a PBX (Asterisk), and SIP user agents (a softphone such as PJSUA and a
residential gateway's FXS port).
- `MwiStatus(waiting, new, old)` follows RFC 3842 message-summary bodies
  (`Messages-Waiting: yes`, `Voice-Message: new/old`), which every SIP family above emits
  or consumes.
- Offline messages: the stored-message modules of the SIP proxies (Kamailio `msilo`)
  store sender, body and time; the time is a database time stamp, hence `datetime`.
- RTP relay statistics: the evidence is one relay; `RtpStats` holds only the two figures
  the one implementer returns and its callers read.
- Call states: the set is the contract's own predicates, not a vendor vocabulary.
  Presence words (RFC 3863 basic status plus provider extensions) and SIP methods (RFC
  3261 and extensions) are open sets, hence `str`.

### P8 — capability protocol host network tools

**Item**: `P8`, capability protocol (`HttpClient`, `HttpServer`, `NmapScanner`,
`DnsClient`, `ArpClient`, `IpRouting`, `IpInterface`, `UpnpClient`, `VlanClient`,
`MulticastClient`, `DhcpServer`, `HeldPrefixes`) and models (`HTTPResult`, `DnsRecord`,
`PingResult`, `NmapResult`, `NmapPort`, `ArpEntry`, `GroupRecord`, `DHCPTraceData`,
`DHCPV6TraceData`).

**Need**: The host-side tool members return `dict[str, Any]` parses or raw text, take
free option strings, take closed sets as `str` (URL scheme, IP version, record type,
link state, mapping protocol), and `HTTPResult` is a plain mutable class with a text
status code. No existing record covers a DNS answer, a ping result, a scan result or an
ARP entry.

**Proposed design**:

- New enums: `IpVersion` (`IPV4 = "ipv4"`, `IPV6 = "ipv6"`), `IpFamily` (`IntEnum`:
  `V4 = 4`, `V6 = 6`), `DnsRecordType` (`A`, `AAAA`, `CNAME`, `MX`, `NS`, `PTR`, `SOA`,
  `SRV`, `TXT`), `HttpScheme` (`HTTP`, `HTTPS`), `LinkAdminState` (`UP`, `DOWN`),
  `NmapPortState` (`open`, `closed`, `filtered`, `unfiltered`, `open|filtered`,
  `closed|filtered`). `PortMappingProtocol` (P2) is reused for UPnP.
- New records (frozen): `DnsRecord(name, record_type: str, ttl, data)`,
  `PingResult(destination, transmitted, received, packet_loss_percent, duplicates,
  rtt_*_ms)`, `NmapResult(up, addresses, ports)`, `NmapPort(port, protocol:
  TransportProtocol, state: NmapPortState, service)`, `ArpEntry(address: IPv4Address,
  hw_type, hw_address, flags, interface)`, `GroupRecord(sources, group, record_type)` (a
  `NamedTuple`, so it is the released tuple).
- New mandatory members:
  - `DnsClient.resolve(domain_name: str, record_type: DnsRecordType | str) ->
    list[DnsRecord]`;
  - `IpRouting.ping_stats(ping_ip: str, ping_count: int = 4, ping_interface: str | None =
    None, timeout: int = 50) -> PingResult`;
  - `NmapScanner.scan_ports(target: str, ip_version: IpFamily, *, ports:
    Sequence[PortRange] = (), protocol: TransportProtocol | None = None, max_retries: int
    | None = None, min_rate: int | None = None, timeout: int = 30, fast: bool = False) ->
    NmapResult`;
  - `ArpClient.read_arp_table() -> list[ArpEntry]`;
  - `IpInterface.is_link_admin_up(interface: str) -> bool` (administratively up, whether
    or not a carrier is present).
- New keyword-only parameters (shape 4p): `HttpClient.curl(url, protocol: HttpScheme |
  str, port, options: str = "", *, no_proxy: bool = False, insecure: bool = False,
  follow_redirects: bool = False) -> bool` and `http_get(url, timeout, options, *,
  no_proxy, insecure, follow_redirects) -> HTTPResult`; `NmapScanner.nmap(..., opts, ...,
  *, fast: bool = False)`. Passing both the option string and a typed parameter raises
  `ValueError`.
- Deprecated (shape 5 or parameter): `DnsClient.dns_lookup` (with `opts`; `opts` has no
  successor), `NmapScanner.nmap` (with `opts`; `fast` replaces `-F`, any other has no
  successor), `ArpClient.get_arp_table`, `IpRouting.ping(json_output=True)` (at removal
  `ping` returns `bool`), `IpRouting.ping` and `traceroute` `options` (no successor),
  `HttpClient.curl` / `http_get` `options`, `IpInterface.is_link_up(pattern)`. The
  deprecated readers keep their released output (a tool's full parse, which the record
  cannot rebuild).
- Parameters (shape 1): `curl(protocol: HttpScheme | str)`, `nmap(ip_type: IpVersion |
  str)`, `dns_lookup(record_type: DnsRecordType | str)`, `IpInterface.set_link_state(state:
  LinkAdminState | str)`, `UpnpClient.create_upnp_rule` / `delete_upnp_rule(protocol:
  PortMappingProtocol | str)` (`tcp-udp` is refused: not a UPnP protocol).
- `HTTPResult`: a frozen dataclass `(status: int, body: str, raw: str)` whose constructor
  still takes the response text (`HTTPResult(response)`); `status` is `0` with no numeric
  code (announced to become `None`); the released `code` (text) and `beautified_text`
  properties are deprecated in favour of `status` and `body`.
- Static only: `DhcpServer.provision_cpe(dhcpv4_options, dhcpv6_options: dict[str,
  dict[str, object]])` (was `dict[str, Any]`); `DHCPTraceData.dhcp_packet` /
  `DHCPV6TraceData.dhcpv6_packet: Mapping[str, object]`;
  `MulticastClient.send_mldv2_report` records as plain tuples deprecated in favour of
  `GroupRecord`.
- Announced only: `HttpServer.start_http_service` / `stop_http_service(port: str)` and
  `start_http_service(ip_version: str)` narrow to `int` and `IpFamily`;
  `UpnpClient` `int_port` / `ext_port` and `VlanClient` `vlan_id` narrow to `int`;
  `IpRouting.traceroute(version: str)` narrows to `IpFamily | None`;
  `HeldPrefixes.hold(address: str)` narrows to `IPv4Interface | IPv6Interface`. They stay
  `str` now because released implementers declare `str`, and widening a parameter breaks
  an implementer declared narrower.
- Writes: `set_link_state` is read back by the new `is_link_admin_up` (the released
  `is_link_up` reads the operational state); UPnP rules are read by the existing port
  mapping list.
- Open on purpose (recorded in `packages/testprotocols/GAPS.md`): typed `dns_lookup`
  options, and `ping` / `traceroute` options, need caller evidence or a decision to drop
  them before the strings are removed.

**Mechanism**: extend
Five new mandatory members and new keyword-only parameters on three members (a
declaration without them is reported by the checkers). The vocabulary, option-string and
placeholder changes are rung-5 `deprecate` changes in the same release.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.http_client`, `http_server`, `nmap_scanner`, `dns_client`, `arp_client`,
`ip_routing`, `ip_interface`, `upnp_client`, `vlan_client`, `multicast_client`,
`dhcp_server`, `held_prefixes`, `testprotocols.models` (`networking.py`, `dhcp.py`,
`multicast.py`).

**Affected**: implementers of `DnsClient`, `IpRouting`, `NmapScanner`, `ArpClient`,
`IpInterface` (new members) and of `HttpClient` / `NmapScanner` (new parameters); any
driver that assigns attributes of an `HTTPResult` (now frozen: `FrozenInstanceError`) or
subclasses it as a non-frozen dataclass; `testoperations.http_server` (P12).

**Neutrality evidence**: The "families" here are the host tools the drivers run. No list
was recorded before this proposal; the reviewed-family list it records: Linux hosts with iproute2, curl, nmap,
bind9 `dig`, iputils `ping` and net-tools `arp`; BusyBox equivalents on embedded hosts.
The released implementers are the Linux host and LAN devices of a released open-source
implementer framework and the released example implementers.
- `no_proxy`, `insecure`, `follow_redirects`: curl `--noproxy`, `-k` / `--insecure`, `-L`
  / `--location`, the only flags callers were seen to pass.
- `fast`: nmap `-F` (fewer ports than the default scan). `NmapPortState`: the six states
  in the nmap reference guide. The record fields come from `nmap -oX` output.
- `PingResult`: the summary lines of iputils and BusyBox `ping` (transmitted, received,
  loss, duplicates, rtt min/avg/max/mdev).
- `DnsRecordType`: the common types of the IANA DNS RR registry; `DnsRecord.record_type`
  stays `str` because an answer can hold any registered type (`dig` prints the type
  word).
- `ArpEntry`: the columns of `arp -n` (address, HW type, HW address, flags, interface);
  `ip neigh` gives the same facts.
- `is_link_admin_up`: the `UP` flag of `ip link show`, distinct from `LOWER_UP`
  (carrier).
- UPnP: the IGD `AddPortMapping` `NewProtocol` argument is `TCP` or `UDP`, hence
  `tcp-udp` is refused there.

### P9 — capability protocol SNMP and NTP clients

**Item**: `P9`, capability protocol (`SnmpClient`, `NtpClient`).

**Need**: `SnmpClient.execute_snmp_command` takes a whole command line as text;
`NtpClient.set_date(opt, date_string)` takes an option string and a date as text;
`NtpClient.get_date` returns device text. None can be checked by a type checker.

**Proposed design**:

- New enum `SnmpValueType` in `testprotocols.models.networking`, exported from
  `testprotocols.models`: `INTEGER = "integer"`, `UNSIGNED = "unsigned"` (Unsigned32 /
  Gauge32), `OCTET_STRING = "octet-string"`, `OBJECT_IDENTIFIER = "object-identifier"`,
  `IP_ADDRESS = "ip-address"`, `TIMETICKS = "timeticks"`, `BITS = "bits"` (the RFC 2578
  §7.1.4 construct, carried as an octet string). Left out on purpose: Counter32 and
  Counter64 (RFC 2578 §7.1.6 and §7.1.10: a counter only increments, so no object takes a
  SET); Opaque (obsolete); hex and decimal strings (tool input notations, not SMI types; a
  value beginning `0x` is still sent as hex). A driver maps each member to its tool's type
  code.
- New mandatory members:
  - `SnmpClient.snmp_get(host: str, oid: str, community: str, *, timeout_s: int = 10,
    retries: int = 3, command_timeout: int = 30) -> str`;
  - `snmp_walk(host, oid, community, *, timeout_s: int = 100, retries: int = 3,
    command_timeout: int = 30) -> str` (an empty `oid` walks from the root);
  - `snmp_set(host, oid, community, value: str, value_type: SnmpValueType, *, timeout_s: int = 10,
    retries: int = 3, command_timeout: int = 30) -> str`;
  - `snmp_bulk_get(host, oid, community, *, non_repeaters: int = 0, max_repetitions: int =
    10, timeout_s: int = 100, retries: int = 3, command_timeout: int = 30) -> str`;
  - `NtpClient.set_date_time(value: datetime) -> bool`;
  - `NtpClient.read_date() -> datetime | None`.
- Deprecated: `execute_snmp_command` (any other command has no successor), `set_date`,
  `get_date` (keeps its released text output).
- Writes: `snmp_set` is read back by `snmp_get`; `set_date_time` by `read_date`.
- `value_type` is annotated with the bare enum (no `| str`): the member is new and has no
  released form (C4).
- Types left open, with the reason: the SNMP members return the tool's output text, as
  the released member did; a typed varbind record is not proposed here for lack of a
  second implementer's parse.

**Mechanism**: extend
Six new mandatory members; the deprecations ride the same release.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.snmp_client`, `testprotocols.ntp_client`, `testprotocols.models`
(`networking.py`, `SnmpValueType`).

**Affected**: implementers of `SnmpClient` and `NtpClient` (six new members; an
`snmp_set` implementer maps each `SnmpValueType` member to its tool's type code and raises
`NotSupportedError` for one its tool cannot set); callers of `snmp_set` pass a
`SnmpValueType` member. `testoperations` calls none of these members.

**Neutrality evidence**: Reviewed-family list recorded by this proposal: Net-SNMP
command-line tools on Linux hosts, as the one SNMP client family; the SNMP library of a released implementer framework drives exactly `snmpget`,
`snmpwalk`, `snmpset` and `snmpbulkget` with `-v 2c -On -c <community> -t <seconds> -r
<retries>`, the parameters typed here. `SnmpValueType` follows the SMI base types of RFC 2578
(plus the BITS construct), and the Net-SNMP `snmpset` type letters map one to one onto it
(`i`, `u`, `s`, `o`, `a`, `t`, `b`). The one `set_date`
option seen is `date -s`; `set_date_time` leaves the formatting to the driver. A second SNMP
client family is not required: the members carry the SNMP operations and SMI types of
RFC 3416 and RFC 2578, not a tool's syntax, so another client maps onto them the same way.

### P10 — capability protocol traffic generation, impairment and QoE measurement

**Item**: `P10`, capability protocol (`IperfClient`, `IperfServer`, `NetemController`,
`QoeBrowser`) and models (`IperfProcess`, `TransportProtocol`, `TrafficSpec`,
`MeasurementSpec`, the transient events).

**Need**: `IperfClient.start_traffic_sender` / `IperfServer.start_traffic_receiver`
return untyped process information and take the window as size text;
`NetemController.inject_transient` takes an event word and a free keyword bag; the impairment
profile is `dict[str, Any]`; QoE tools, completions and scenarios and the traffic
protocol are closed sets typed `str`. `ImpairmentProfile` exists and is reused as the
profile's typed form.

**Proposed design**:

- New enums: `TransportProtocol` (`TCP`, `UDP`), `QoeTool` (`BROWSER`, `HTTP_CLIENT`,
  `WEBRTC`, `TCP_PROBE`), `PageCompletion` (`LOAD`, `DOMCONTENTLOADED`, `NETWORKIDLE`,
  `COMMIT`), `QoeCompletion` (those four and `DURATION`, `RESPONSE`, `CONNECT`),
  `QoeScenario` (`PAGE_LOAD`). `IpFamily` (P8) for iperf `ip_version`.
- New records (frozen): `IperfProcess(pid, log_file)`; transient events `Blackout()`,
  `Brownout(latency_ms, jitter_ms, loss_percent)`, `LatencySpike(latency_ms,
  jitter_ms)`, `PacketStorm(loss_percent, latency_ms, jitter_ms, duplicate_percent)` and
  the union `TransientEvent` (every field optional: `None` is the driver's default;
  `PacketStorm` keeps the released meaning, a loss burst).
- New mandatory members (two names, because one class implements both protocols):
  - `IperfClient.start_sender_session(host: str, traffic_port: int, *, bandwidth: int |
    None = None, bind_to_ip: str | None = None, ip_version: IpFamily | None = None,
    udp_protocol: bool = False, time: int = 10, client_port: int | None = None, udp_only:
    bool | None = None, reverse: bool = False, omit_s: int | None = None, json_output:
    bool = False, window_bytes: int | None = None, parallel: int | None = None,
    datagram_bytes: int | None = None, report_interval_s: int | None = None) ->
    IperfProcess`;
  - `IperfServer.start_receiver_session(traffic_port: int, *, bind_to_ip: str | None =
    None, ip_version: IpFamily | None = None, udp_only: bool | None = None) ->
    IperfProcess`;
  - `NetemController.inject_event(event: TransientEvent, duration_ms: int) -> None`.
- Deprecated: `start_traffic_sender`, `start_traffic_receiver` (return the record's fields
  in the released shape), `inject_transient` (applies the event the new member would);
  `NetemController.set_impairment_profile` / `set_interface_profile(profile:
  ImpairmentProfile | dict[str, object])` as a `dict`.
- Parameters: `start_traffic_sender` / `start_traffic_receiver(ip_version: IpFamily |
  int | None)`; `QoeBrowser.measure_productivity(scenario: QoeScenario | str, wait_until:
  PageCompletion | str)`.
- Fields (shape 3): `TrafficSpec.protocol: TransportProtocol | str`;
  `MeasurementSpec.tool: QoeTool | str`, `completion: QoeCompletion | PageCompletion |
  str`; the defaults stay the released words (`"udp"`, `"browser"`, `"networkidle"`).
  `QoEResult.protocol` stays `str` (the HTTP version as reported).
- Lever: `inject_event` has no state to read back; the observation that confirms it is the
  impairment seen on the path (the `testoperations` measurement around it), as for the
  released member.

**Mechanism**: extend
Three new mandatory members. The vocabulary and profile retypes ride the same release as
rung-5 `deprecate` changes.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.iperf_client`, `iperf_server`, `netem_controller`, `qoe_browser`,
`testprotocols.models` (`traffic.py`, `impairment.py`, `qoe.py`).

**Affected**: implementers of `IperfClient`, `IperfServer`, `NetemController` (new
members); `testoperations.throughput`, `netem_controller`, `sdwan`, `iperf_client`,
`iperf_generator` (P12), which call the new names with a fallback to the released ones.

**Neutrality evidence**: Reviewed-family list recorded by this proposal: iperf3 and iperf2 for
traffic, Linux `tc` with `netem` for impairment, and a headless browser driver for
QoE.
- Session parameters: iperf3 `-c`, `-p`, `-b`, `-B`, `-4` / `-6`, `-u`, `-t`, `--cport`,
  `-R`, `-O`, `-J`, `-w`, `-P`, `-l`, `-i`; iperf2 shares most and lacks `-J` and
  `--cport`, so a driver for it raises on those. The window is in bytes because iperf
  size suffixes are binary (`8M` is 8388608) and the text grammar differs between tools.
- Transient events: netem `delay <latency> <jitter>`, `loss`, `duplicate`; a blackout is
  100 % loss. The field names are what the released implementers read.
- Page completions: the four load states of the Playwright `wait_until` option; the
  other completions (`duration`, `response`, `connect`) come from the QoE specification's
  tool-by-completion matrix of a released implementer framework.

### P11 — capability protocol device management, content filtering, consoles and RADIUS status

**Item**: `P11`, capability protocol (`DeviceManagement`, `ContentFiltering`,
`HwConsole`, `Console`, `RadiusServer`) and models (`MemoryUtilization`, `ProcessInfo`,
`EventLogEntry`, `SyslogSeverity`, `UrlRules`, `ServiceStatus`).

**Need**: The device-management readers return dicts and lists of dicts; the event log
mixes parsed entries with `{"unparsable": line}`; `get_running_processes` takes a free
process-listing option string; `ContentFiltering.get_url_rules` returns a dict;
`HwConsole.get_console` returns `Any` and `get_interactive_consoles` `dict[str, Any]`;
`RadiusServer.get_status` returns `str` over a closed set. No existing protocol models a
text console.

**Proposed design**:

- New records (frozen): `MemoryUtilization(total_bytes, used_bytes, free_bytes,
  shared_bytes, cache_bytes, available_bytes)` (the last three all given or all `None`;
  used and free at most total), `ProcessInfo(pid, tty, cpu_time: timedelta, command)`,
  `EventLogEntry(timestamp: str, hostname, tag, message, priority, severity:
  SyslogSeverity)`, `UrlRules(allowed, blocked)`.
- New enums: `SyslogSeverity` (`IntEnum`, RFC 5424 severities 0 to 7), `ServiceStatus`
  (`RUNNING`, `STOPPED`, `ERROR`).
- New mandatory members: `DeviceManagement.read_memory_utilization() ->
  MemoryUtilization`, `read_running_processes() -> list[ProcessInfo]`,
  `read_log_entries() -> list[EventLogEntry]`; `ContentFiltering.read_url_rules() ->
  UrlRules`.
- Deprecated: `get_memory_utilization`, `get_running_processes` (with `ps_options`; a value
  other than the default `"-A"` has no successor), `read_event_logs` (keeps its released
  output, unparsable lines included), `get_url_rules`.
- New protocol `Console` (`runtime_checkable`): `execute_command(command: str, /, timeout:
  int = -1) -> str`, `sendline(text: str = "", /) -> object`, a read-only `before: str |
  bytes | None`, `start_interactive_session() -> None`. `HwConsole.get_console(console_name:
  str) -> Console`, `get_interactive_consoles() -> Mapping[str, Console]` (were `Any` /
  `dict[str, Any]`). `expect` / `expect_exact` are not members: no single contract type
  matches a console library's own pattern types; a caller that matches patterns keeps the
  concrete console type.
- Announced only: `RadiusServer.get_status -> ServiceStatus`.
- Left as text on evidence: `EventLogEntry.timestamp` (the syslog date has no year; a
  `datetime` would invent one); `ProcessInfo.tty`.

**Mechanism**: extend
Four new mandatory members, plus a return narrowing on `HwConsole` that breaks a console
lacking a `Console` member. `Console` is a new protocol used only as a return type of an
existing capability, not a new capability of a device; the retypes ride the same release.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.device_management`, `content_filtering`, `hw_console`, `radius_server`,
`testprotocols.models` (`device_management.py`, `radius.py`); `Console` is also exported
as `testprotocols.Console`.

**Affected**: implementers of `DeviceManagement`, `ContentFiltering` (new members) and
`HwConsole` (returned consoles must have the `Console` members; a `dict` return still
conforms); callers of returned consoles that use other members (keep the concrete type or
narrow). `testoperations` never touches a console and calls none of these readers.

**Neutrality evidence**: Reviewed-family list recorded by this proposal: Linux hosts and gateways
(procps `ps`, `free`, BSD syslog), the SD-WAN appliance families for content filtering, and
pexpect-based consoles (serial, SSH, telnet) for `Console`.
- `MemoryUtilization`: the columns of `free -b` (total, used, free, shared, buff/cache,
  available); older kernels report no `available`, hence the all-or-none rule.
- `ProcessInfo`: `ps -A` (procps) gives PID, TTY, TIME (`[DD-]hh:mm:ss`), CMD.
- `EventLogEntry`: RFC 3164 (BSD syslog) priority, timestamp without a year, hostname,
  tag, message; severity derived from the priority (RFC 5424 table).
- `UrlRules`: the Meraki MX content-filtering API has `allowedUrlPatterns` and
  `blockedUrlPatterns`; FortiGate web-filter URL filter entries carry allow / block
  actions; the two lists are the shared shape. Catalyst SD-WAN, Prisma SD-WAN and VeloCloud
  URL filtering were not checked for this item.
- `Console`: the members the callers of returned consoles were seen to use
  (`execute_command`, `sendline`, `before`, `start_interactive_session`) in a released
  implementer framework's CPE libraries and the released example implementers; a mypy-backed test checks that a
  `pexpect.spawn` subclass with those members satisfies `Console` under `types-pexpect`.

### P12 — operation `testoperations` typed records and the transition

**Item**: `P12`, operation (`testoperations` operations and their records).

**Need**: Several operations return `dict` or `Any`, take closed sets as `str`, or take
`Callable[..., X]` stand-ins; and P1 (C6) puts the transition between released and new
forms in `testoperations`, so its operations keep working with a driver that has only the
released form for the whole period.

**Proposed design**:

- Transition (internal, not public API): fallback accessors (`_renamed.py`: the new member
  when the driver has it, else the old) for `start_sender_session`,
  `start_receiver_session`, `inject_event`; readers of every text/typed pair of P2, P3 and
  P5, with the read rule of C3; parsers of the released text forms (ports, ISO-8601 time,
  the QoS classifier list, traffic-generator window sizes); `coerce_enum(E, value, what=…)` for the
  operations' own released `str` parameters (a member passes; a plain string naming a
  member warns at the caller and converts; any other string raises `ValueError` listing the
  legal values; another type raises `TypeError`).
- New records (frozen), each over a shared `ReleasedMapping` mixin that keeps the released
  dict readable with a `DeprecationWarning` for the period: `IperfSession(sender,
  receiver)` (from `start_iperf`), `HomeVerification(vlan_defined, subnet_advertised,
  peers_reachable, details: HomeDetails)` and `HomeDetails(defined_subnet,
  defined_gateway, peer_states)` (from `verify_home`), `FlowPair(a_to_b, b_to_a)` (from
  `saturate_link`). The operations keep their names.
- New enums: `DenyScope` (`HOST`, `SUBNET`; `build_deny_rule(scope: DenyScope | str,
  proto: RuleProtocol | str)`), `NetemPreset` (the preset table's keys; `apply_preset
  (preset_name: NetemPreset | str)`), `NonCompletionSide`, `NonCompletionKind` (replacing
  the `Literal` aliases; `NonCompletion(which_side, what)` takes `E | str`).
  `saturate_link(protocol: TransportProtocol | str = "udp")`.
- Call protocols replacing `Callable[..., X]`: `MeasureFn` (flows, then keyword-only
  `duration_s`, `result_timeout_s`, `poll_interval_s`) and the `measure_flow` stand-in of
  `measure_external_path_until` (`(flow: ExternalFlow, /, *, duration_s: int,
  result_timeout_s: float, poll_interval_s: float) -> FlowThroughput`).
- `start_iperf(iperf_client: IperfClient, iperf_server: IperfServer, ..., *, host: str)`:
  the released body called `start_sender` / `start_receiver`, which no protocol declares
  and no driver implements, and it could not name the receiver's address; it now calls the
  protocol members and takes the required keyword-only `host`. Breaking for callers,
  recorded under *Changed*.
- `inject_packet_storm` gains keyword-only `loss_percent`; `duplicate_percent` defaults to
  `None` and reaches a new-name driver only when the caller passes it.
- Fixes that ride along, recorded under *Fixed*: `tcpdump` makes the protocol's calls
  (typed `PcapCapture`); `start_http_server`'s default `ip_version` becomes `"4"`;
  `inject_latency_spike(latency_ms)` takes effect with a new-name driver.
- `iter_json_docs -> list[object]`; `sender_life_record(iperf_client: IperfClient)`.

**Mechanism**: deprecate
The released `str` parameters and dict returns are retyped with a deprecation period
(widen, then narrow; the dict reads warn until removal). The required `host` on
`start_iperf` is the one breaking signature change; it repairs an operation that could not
work with any driver.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testoperations` (`_compat`, `_renamed`, `_released`, `segmentation`, `netem_controller`,
`throughput`, `iperf_client`, `iperf_generator`, `homing`, `sdwan`, `pcap_capture`,
`http_server`, `_capture`, `marking_observation`, `path_placement`).

**Affected**: callers of `start_iperf` (pass `host=`), `verify_home`, `saturate_link`
(read the fields), `build_deny_rule`, `apply_preset`, `NonCompletion` (pass members);
stand-ins passed as `measure` / `measure_flow`. Drivers with only the released names keep
receiving exactly the released calls.

**Neutrality evidence**: No device family is involved beyond those of P2, P3, P5 and P10,
whose evidence applies; the operations are tool-neutral. A search of the released implementers
and the reference driver implementations found no caller of
`start_iperf`, `verify_home`, `saturate_link` or `iter_json_docs`.

## Not touched by this proposal

Question 9 notes these existing members, which stay imprecise and are not retyped here:

- `ZonePolicy.action: str` (`"accept"`, `"drop"`, `"reject"`), which `DefaultAction` (P2)
  could type;
- `FlowMatch.src_port` / `dst_port: str = "any"`, port text that `PortRange` (P2) could
  type;
- the 12 TR-069 RPCs and the two compatibility signatures of P1 (exemption policy).

## Reference implementations and verification

Every new mandatory member is implemented by the reference driver implementations of the
affected capabilities, or stubbed there with `NotSupportedError` and a cited source,
before the `feat:` PR merges (question 7). Each new member and changed field has a test for
the positive and the negative or edge path; the `feat:` PR runs the test suites and both static
checkers on Python 3.12 (the minimum) and on a current Python release.
