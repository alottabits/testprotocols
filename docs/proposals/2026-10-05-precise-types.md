# Proposal: precise types for the released capability protocols and operations

| Field | Value |
| --- | --- |
| Date | 2026-10-05 |
| Use case | `—` (maintainer-originated, no consumer use-case id) — static conformance checking of driver implementations against the capability protocols |
| Round | 2 |
| Status | `accepted with conditions` |

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
`NotSupportedError`. The same section records, each with its migration line, the other
changes an implementer must follow without a period: the new keyword-only parameters on
three released members (P8), the widened `send_mldv2_report` parameter (P8) and P1's one
no-period field widening (P6).

Item P1 is cross-cutting (the contract model and its enforcement); P2 to
P11 are grouped by capability family; P12 is the `testoperations` side. Member and field names are exact, so the `feat:` PR can be checked
against this document item by item. The implementation is on the branch
`feat/precise-types`; the design record is `docs/architecture/precise-types-design.md`
on that branch, whose Deprecations table lists every deprecation one row each, and the
reviewed-family lists and substrate surveys of P6 to P11 are recorded in
`docs/architecture/precise-types-families.md` (merging the `feat:` PR ratifies them).

Existing members that no item touches and that are still imprecise are listed at the end
("Not touched by this proposal"), as question 9 asks, and folded into `GAPS.md`.

## Items

### P1 — model the contract model for typing changes, deprecations and their enforcement

**Item**: `P1`, model (the rule set every retype in P2 to P12 follows; changes
`CONTRIBUTING.md` "Versioning" and "Releases" and the rung-5 text of
`docs/proposals/README.md`; adds the static enforcement of question 9, over explicit `Any`
and `object`, in both packages; adds no runtime dependency to either package).

**Need**: The recorded rung-5 rule (`docs/proposals/README.md`, "How rung 5 is done";
`CONTRIBUTING.md`, "Releases") announces a deprecation with a runtime
`DeprecationWarning` and normalises an old input form "with a shared helper that emits a
`DeprecationWarning`". Applied to records and protocol modules of `testprotocols`, that
rule puts transition code in the contract package: a record that warns when a released
field is read, converts a released string, or keeps a text field and a typed field in sync
needs `__post_init__`, `__getattr__` or `__setattr__` logic. A first implementation on
the branch did exactly that. The four findings against it are recorded in
`docs/architecture/precise-types-design.md` ("Why the runtime warning left
`testprotocols`"):

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

- *The marker without a dependency.* The `@deprecated` marker (C2 below) is in the
  standard library from Python 3.13 only. `testprotocols` supports Python 3.12
  (`requires-python = ">=3.12"`) and has no runtime dependency (`dependencies = []`),
  which this item keeps.
- *Enforcement of no explicit `Any` and no `object`.* Question 9 forbids `Any` in a
  signature or field, and `object` is as imprecise. Without enforcement a later change can
  reintroduce either unnoticed. Some released signatures cannot drop `Any` without
  breaking released implementers, because a parameter is contravariant and `dict` is
  invariant: no narrower contract type accepts their declarations. Some values are open
  by nature (a vendor-extensible option map). The rule needs a precise, counted list of
  what stays.

**Proposed design**: Six rules and one stated exception.

- **C1. No runtime transition code in `testprotocols`.** No `DeprecationWarning`, no
  conversion, no sync and no field validation in a record or a protocol module.
- **C2. A deprecated protocol member or class** keeps its declaration and gets a docstring
  paragraph, "Deprecated: use `<new>`. Removal not before the first release 6 months
  after the release that deprecates it.", and `@deprecated("<the same sentence>",
  category=None)`, imported from the internal `testprotocols._compat` (see "The marker
  without a dependency" below). The type checkers report each use: pyright in strict
  mode, and mypy with the `deprecated` error code, which this workspace's
  `pyproject.toml` enables (see "The checker configuration" below). Nothing warns at run
  time. A deprecated parameter or field
  cannot carry the marker; its docstring states it. A released plain attribute
  (`HTTPResult.code`, P8) cannot carry it either, because a property in its place would
  make it read-only; its docstring and the Deprecations table state it, and the checkers
  do not report its use.
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
  the driver has it, else the old one; internal); the readers of a text/typed pair and
  the parsers of the released text forms, which are public API in the module
  `testoperations.pairs` (so a consumer that otherwise depends on `testprotocols` alone
  reads a pair by the C3 rule there; each reader and parser goes in the release that
  removes the text fields it reads); and the conversion of its own released `str`
  parameters with a `DeprecationWarning` at its caller (P12; internal). Operations honour
  the period, as the recorded rule already requires.
- **The no-period exception.** A released record field whose values a reviewed family
  cannot report at all, and of which no form can be kept through a period, may be widened
  to `T | None` at once, without a deprecation period. Both conditions must hold: a
  reviewed family reports no value for the field (so a driver for it can only invent
  one), and neither a twin field (C3) nor a rename-then-reclaim keeps the released form
  usable (a twin would leave the released field required and still unfillable). The
  change is recorded under *Breaking for driver authors* with its migration line. The one
  instance is `WifiRadioStats.tx_retries` / `tx_failed` (P6).

C4 and C5 settle the gating question that GAPS 2026-06-11 ("migrate legacy bare-`str`
value fields to typed vocabularies") records to "decide before writing code": (A)
annotation plus checker only, as `models/sdwan_appliance.py` already does, or (B)
`__post_init__` coercion in every record. This item decides (A): a typed vocabulary is an
annotation the checkers enforce, a record converts and validates nothing at run time, and a
driver converts once at its boundary.

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

*The marker without a dependency.* `packages/testprotocols/pyproject.toml` keeps
`dependencies = []`. The internal module `testprotocols._compat` is the only import site
of the marker, in three steps: under `TYPE_CHECKING` it imports `deprecated` from
`typing_extensions`, which the type checkers resolve from their bundled stubs; at run time
it imports `warnings.deprecated` (Python 3.13 and later); where that import fails
(Python 3.12) it defines an identity marker with the same signature that returns the
decorated object unchanged. A test imports every `testprotocols` module with
`typing_extensions` unavailable and warnings as errors, checks that the package metadata
declares no dependency, and checks which marker is in use on each Python version.
`testoperations` gains no dependency either. A dev-only typing-stub dependency, for the
`Console` conformance test in P11, is added to the workspace, not to either package.

*The exemption policy for explicit `Any` and `object`.*

- The static checker runs with "no explicit `Any`" on `testprotocols.*` and
  `testoperations.*` (a per-module override in the workspace `pyproject.toml`). A
  test (`packages/testprotocols/tests/test_typing_ratchet.py`) is the second line of
  defence, because the other checker has no such rule and neither checker flags
  `object`: it counts the non-exempt `Any` and `object` (ceiling 0 for each, in each
  package) and pins the exempt lines per class and package, so a new exemption needs a
  reviewed change. `Callable[..., X]` counts as `Any`; the two in `testoperations`
  become call protocols (P12).
- `Any` exemptions are released signatures only, marked on the `def` line, in two
  classes.
  - **(a) Deprecation period, 10 lines**, marker `# type: ignore[explicit-any]  # released
    signature kept until removal`: the deprecated forms whose released `dict[str, Any]` /
    `list[Any]` output stays readable until removal: `IpRouting.ping`
    (`json_output=True`), `DnsClient.dns_lookup`, `NmapScanner.nmap`,
    `DeviceManagement.get_running_processes`, `DeviceManagement.read_event_logs`,
    `SipServer.get_rtpengine_stats`, `get_mwi_status`, `get_offline_messages` and
    `Router.get_telemetry` (deprecated in P4, P7, P8 and P11); and the released parameter
    `SipServer.verify_sip_message(since: Any = None)`, whose narrowing to `datetime | None`
    is announced (P7; marked on the `def` line that opens the multi-line signature). Each
    line goes with its member, form or narrowing at removal, and the pinned count drops
    with it.
  - **(b) Compatibility, 16 lines**, live members, not tied to a removal.
    `HwConsole.flash_via_bootloader` (two framework-object parameters) and
    `PcapCapture.start_tcpdump(filters: dict[str, Any])`, marker `# released parameter
    kept: implementers declare their own types` (2 lines). The 12 released TR-069 RPCs of
    `Tr069Server` (`GPV`, `SPV`, `GPA`, `SPA`, `FactoryReset`, `Reboot`, `AddObject`,
    `DelObject`, `GPN`, `ScheduleInform`, `GetRPCMethods`, `Download`), marker `# released
    signature kept: vendors extend the parameter model` (12 lines): the parameter model is
    extended per device, so the contract does not enumerate it, and a typed layer over it
    would be a guess. `HwConsole.get_console` and `get_interactive_consoles`, marker
    `# released return kept: implementers return their own types` (2 lines): the
    narrowing to `Console` is announced (P11), and these lines go at that narrowing.
- `object` is counted in a public parameter or return annotation, a class- or
  module-level field and a module-level type alias, including inside a generic; the
  parameter of `__eq__`, `__ne__` and `__contains__` and every `object` outside an
  annotation are not counted. An exempt line carries a plain comment marker (mypy reports
  no error to ignore), in two classes:
  - **(a) Deprecated form**, marker `# object: deprecated form kept until removal`: 4 lines
    in `testprotocols` (`SdwanPolicyManager.apply_policy`, `TrafficShapingRule.match`,
    the `dict` form of `NetemController.set_impairment_profile` and
    `set_interface_profile`) and 6 in `testoperations` (the released-dict reads of
    `ReleasedMapping` and `HomeDetails.released_form`, P12).
  - **(b) Open value**, marker `# object: open value: the contract does not enumerate it`:
    3 lines in `testprotocols` (`DhcpServer.provision_cpe`, `DHCPTraceData.dhcp_packet`,
    `DHCPV6TraceData.dhcpv6_packet`), 0 in `testoperations`.
  - Replaced rather than marked, because a precise type exists: `Console.sendline` returns
    `int` (P11), `iter_json_docs` returns `list[dict[str, JsonValue]]`, and the released
    public alias `testoperations.throughput.JsonObj` keeps its name as
    `Mapping[str, JsonValue]` (was `Mapping[str, object]`) (P12).
- Removed rather than exempted: the one explicit `Any` outside a signature, the
  `cast("Any", protocol)` with which the device registry (`testprotocols.devices`) read a
  protocol's member names. It reads them with `typing.get_protocol_members` on Python 3.13
  and later, and on 3.12 through a cast to a one-member private protocol over
  `__protocol_attrs__`, the attribute that function reads; the member sets are identical
  on both versions.
- The counts per package, as the ratchet pins them: `testprotocols` has 10 class (a) and
  16 class (b) `Any` lines and no other explicit `Any`, and 4 class (a) and 3 class (b)
  `object` lines; `testoperations` has no `Any` line and 6 class (a) `object` lines.
- If `start_tcpdump` is later deprecated in favour of a renamed member, its exemption
  moves to class (a).

*The checker configuration.* The workspace `pyproject.toml` runs pyright in strict mode
with `reportDeprecated = "error"`, and mypy in strict mode with `enable_error_code =
["explicit-override", "exhaustive-match", "deprecated"]` and `disallow_any_explicit` for
both packages. The dev group requires `mypy>=1.17` (was `>=1.10`): `deprecated` came in
mypy 1.14 and `exhaustive-match` in 1.17, and an unknown code in `enable_error_code` fails
the run. `CONTRIBUTING.md` and the design record state the floor.

**Mechanism**: deprecate
P1 adds no protocol member. It amends the rung-5 deprecation procedure
(`docs/proposals/README.md`, "How rung 5 is done"; `CONTRIBUTING.md`, "Releases") that the
retypes of P2 to P12 use; `deprecate` is the rung whose procedure it changes. The members
it governs are counted in their family items. The exemption policy is repository tooling:
its 16 `Any` compatibility lines and 3 `object` open-value lines keep their signatures as
they are, and its deprecation-period lines are governed by the family items that
deprecate them.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) — to
`CONTRIBUTING.md` ("Versioning", "Releases", release checklist),
`docs/proposals/README.md` (rung-5 text: Rename, Retype values going in, The deprecation
period) and `docs/architecture/precise-types-design.md` (the rules, the no-period
exception, the four findings, the exemption policy); `testprotocols._compat`; the checker
configuration in the workspace `pyproject.toml` (no explicit `Any`; the `deprecated` and
`exhaustive-match` error codes; the dev group's `mypy>=1.17`); the ratchet test in `testprotocols` and the markers on the exempt lines. The
`feat:` PR touches decision files and takes the second review that implies.

**Affected**: every consumer that pins the next MINOR (type checkers report each use of a
deprecated name; a consumer whose checker treats deprecated use as an error sees errors on
upgrade, not test failures); every driver of a capability named in P2 to P11; the
`testoperations` operations named in P12. The rung-5 *values coming out* rule (opt-in
selector) is unchanged and unused here: returns change by new member names (shape 5).
No consumer gains a runtime dependency on any supported Python version. Unchanged by the
exemption policy: `Tr069Server` (12 RPCs), `HwConsole.flash_via_bootloader`,
`HwConsole.get_console` / `get_interactive_consoles` (until their announced narrowing) and
`PcapCapture.start_tcpdump`. Contributors: a change that adds `Any` or `object` to a
public signature fails the ratchet (and, for `Any`, the checker).

**Neutrality evidence**:
- No device family is involved in the rule itself; it concerns the Python typing surface.
  The marker is the standard one (PEP 702, `warnings.deprecated` from Python 3.13,
  backported in `typing_extensions`, whose stubs the type checkers bundle). pyright
  reports it under `reportDeprecated` (an error by default in strict mode); mypy reports
  it under the `deprecated` error code (mypy 1.14 and later), which is not on by default
  (not under strict either) and which this workspace enables. mypy's `exhaustive-match`
  error code is mypy 1.17 and later. The stack-level failure cited under Need was
  observed on CPython 3.12 against 3.13.
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
- The checkers: mypy has `disallow_any_explicit`; pyright has no equivalent rule, and
  neither flags `object`, hence the ratchet test.

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
  `FirewallRuleAction` (`ALLOW`, `DENY`, `REJECT`, `LOG`, `ALERT`), `NatMode` (`SNAT`, `DNAT`,
  `ONE_TO_ONE = "1to1"`), `PortMappingProtocol` (`TCP`, `UDP`, `TCP_UDP = "tcp-udp"`),
  `DefaultAction` (`ACCEPT`, `DROP`, `REJECT`). Every value is the released spelling.
- `FirewallRuleAction` is a vocabulary of its own, not the existing `RuleAction`
  (`models/sdwan_appliance.py`: `allow`, `deny`) extended with `REJECT` and `LOG`:
  `RuleAction` types `L3Rule.action`, `L7Rule.action` and `SwitchAclRule.action`, and
  extending it would widen what those rules may carry for every appliance and switch
  driver. `DefaultAction` is the third vocabulary because it is a different set: what a
  chain or zone does with traffic no rule decides (`accept`, `drop`, `reject`, the words
  `set_default_policy` takes as released), not what a rule does. `SecurityAction`
  (`allowed`, `blocked`, `detected`) is what the appliance did about a security event, an
  observation rather than a rule action. Each enum's values are the released spellings of
  the fields it types. The separate enums follow the line GAPS 2026-06-11 ("migrate legacy
  bare-`str` value fields to typed vocabularies") already records: "Do not unify the
  action vocabularies: `FirewallRule.action` (…), `Zone`/`ZonePolicy.action` (…), and
  appliance `RuleAction` (…) are three distinct sets — keep separate enums."
- `FirewallRuleAction.ALERT` settles the reconciliation the same GAPS entry records: a
  released implementer emits an undocumented `"alert"` for `FirewallRule.action`, and "a
  strict enum must include `ALERT` or [the implementer] must change to `LOG`". The enum
  includes it, with a docstring line saying a released implementer reports this value, so
  the value stays valid when `FirewallRuleAction | str` narrows to `FirewallRuleAction`;
  no implementer has to change its output.
- New records: `PortRange(first: int, last: int)` (frozen, inclusive, `1 <= first <= last
  <= 65535` stated; `PortRange.single(port)`); `RuleCounters(packets: int, bytes: int)`
  (frozen, not negative).
- `RuleCounters` is returned by new members rather than as a `NamedTuple` retyped in place
  on the released members: the released members return `tuple[int, int]`, and an
  implementer declaring that return no longer conforms once the protocol's return narrows
  to a `NamedTuple` subtype. `GroupRecord` (P8) is the opposite case: it is passed in, as a
  parameter, where the released tuple stays accepted.
- New mandatory members:
  - `PacketFilter.get_rule_counter_values(chain: Chain | str, name: str) -> RuleCounters`
    (so also `Firewall`, which inherits `PacketFilter`);
  - `Nat.get_nat_rule_counter_values(name: str) -> RuleCounters`.

  A driver without per-rule counters raises `NotSupportedError` from the new members (the
  stub of the `extend` rule); their docstrings say so.
- Deprecated members (shape 5): `PacketFilter.get_rule_counters`,
  `Nat.get_nat_rule_counters`. Their released docstrings, which name
  `NotImplementedError` for an unsupported driver, stay as released until removal.
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
`testoperations.segmentation` (P12); readers of a pair use `testoperations.pairs` (P12).
`testoperations` calls neither deprecated counter member. `Zone.default_input`,
`default_forward`, `default_output`, `ZonePolicy.action` and
`FirewallRule.application_category` are not retyped (see "Not touched by this proposal").

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
  a `Mapping` parameter would make an implementer declaring `dict` fail to conform. Its
  `object` is an exempt line of class (a) (P1).
- Announced only (shape 6): `L3Rule.src_cidr` / `dst_cidr` (`"any"`),
  `UplinkStatus.ip`, `gateway`, `public_ip`, `primary_dns` and
  `NetworkAttachment.segment` (`""`) become `str | None`.
- Writes: the `L3Firewall.set_*_rules` members (`set_outbound_rules`, `set_inbound_rules`,
  `set_vpn_rules`) already have their list reads; callers fill both port forms until
  removal (C3). Each is a list replace, and its docstring now states the failure outcome:
  a write that fails at any step, rejected or not verified, leaves the as-found state (the
  rule list as it was before the call), in the wording of `docs/proposals/README.md` and
  `docs/archetypes/README.md`.

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

**Need**: `LinkStatus.state` and `LinkHealthReport.state` are `str` over a closed set;
GAPS 2026-06-11 ("migrate legacy bare-`str` value fields to typed vocabularies") names
these fields and `TrafficShapingRule.priority` / `match`. `Router.get_telemetry` returns
`dict[str, Any]` and names no key. `VPNPeerStatus` and `TrafficShapingRule` have no
capability using them. The existing `UplinkState` holds the link vocabulary and is reused
(it gains one member); `VpnPeerStatus` and `ShapingRule` are the existing typed models
for the concerns the two orphans describe, but `ShapingRule` is not a drop-in (its match
is one `(match_type, value)` pair, not a dict match).

**Proposed design**:

- `LinkStatus.state` and `LinkHealthReport.state`: `UplinkState | str` (shape 3).
  `UplinkState` gains `UNKNOWN` (a state the product could not determine, such as a link
  with no health data; a value a released implementer reports).
- New record `Telemetry(uptime_seconds: float | None, cpu_load_percent: float | None =
  None, mem_used_percent: float | None = None)` (frozen; each value given finite and not
  negative, stated). `uptime_seconds` is required, so a driver states the absence:
  `None` means the device reports no uptime. It is not a required `float` because GAPS
  2026-06-11 ("appliance health / online capability") kept host-shaped health off the
  cloud-managed appliance and gives an uptime read there the shape `float | None`, and
  `SdwanApplianceDevice` composes `routing: Router`; a required `float` would force a
  host-shaped read onto that archetype.
- New mandatory member `Router.read_telemetry() -> Telemetry`.
- `Router.get_telemetry` is deprecated in its favour and keeps its released
  `dict[str, Any]` return until removal, under exemption class (a) of P1, as the other
  deprecated readers do; a driver returns the reported fields of `read_telemetry()`.
- Boundary with `DeviceManagement`. `DeviceManagement.get_seconds_uptime`,
  `get_load_avg` and `get_memory_utilization` (and P11's `MemoryUtilization`) carry
  related facts. The boundary runs between the two archetype shapes:
  `DeviceManagement` is host access to a device whose operating system the test reaches
  (uptime, load average, the memory byte columns, processes, logs, files), and only
  `CpeDevice` composes it; `Router.read_telemetry` is the summary health a routing
  device's management interface reports (uptime, CPU and memory as percentages), and
  `SdwanRouterDevice` and `SdwanApplianceDevice` compose `Router`. An API-managed
  appliance composes `Router`, not `DeviceManagement`, of which it can satisfy only a
  couple of methods (GAPS 2026-06-11). `Telemetry` adds no load average and no byte
  columns, and neither record is derived from the other in the contract.
- `VPNPeerStatus` and `TrafficShapingRule`: deprecated classes with no successor, still
  exported; `TrafficShapingRule.match` is `Mapping[str, object]` (an `object` line of
  class (a), P1). `TrafficShapingRule.priority` / `match` are not retyped and go with the
  class at its removal (recorded in the GAPS 2026-06-11 update).
- Announced only: `LinkStatus.ip_address` (`""`: no address) becomes `str | None`.
- `AppFlow.category` stays `str`: the product's own word, with the `ApplicationCategory`
  values listed as the common ones.

**Mechanism**: extend
One new mandatory member (`Router.read_telemetry`). The field and class changes are rung-5
`deprecate`; `get_telemetry` keeps its released return, so nothing here breaks without a
period. A defaulted field cannot replace a `dict` return.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.router`, `testprotocols.models` (`wan_edge.py`, `sdwan_appliance.py` for
`UplinkState.UNKNOWN`); the site-to-site VPN and SD-WAN appliance design documents record
the two orphan deprecations; `GAPS.md` updates the two 2026-06-11 entries.

**Affected**: implementers of `Router` (one new member); readers of `LinkStatus.state` /
`LinkHealthReport.state`; any consumer importing `VPNPeerStatus` or `TrafficShapingRule`
(type checkers report the use). `UplinkState.UNKNOWN` also widens the published
`UplinkStatus.state`, which the appliance-side readers receive from
`ApplianceUplinks.get_uplinks` and `get_uplink`. The widening is safe at run time: a
reader that compares against named members is unchanged, the released `UplinkState` had
no unknown member (so a released driver that type-checks does not produce one there), and
an `UplinkState` member is still its string. A reader that matches every member exhaustively (mypy's
`exhaustive-match` error code, mypy 1.17 and later, which this workspace enables and whose
version the dev group's `mypy>=1.17` floor guarantees (P1), or a pyright exhaustiveness
check) is told statically to handle the new case. `testoperations` calls neither
`get_telemetry` nor the orphans, and reads no `UplinkState`.

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
  It is a list replace, and its docstring now states the failure outcome: a write that
  fails at any step, rejected or not verified, leaves the as-found state (the rule list as
  it was before the call).

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
- `WifiBssConfig.security_mode` lifts a recorded deferral. GAPS 2026-06-11 ("migrate
  legacy bare-`str` value fields to typed vocabularies") lists it among the
  "vendor-divergent / undocumented fields … not enum-safe … defer until a test needs
  them". The lift is argued on three points. The entry's own trigger is met: "touching a
  given legacy capability for other reasons", and this item retypes the `WifiBss`
  parameters that write the same value (`create_bss(security_mode)`, `set_security(mode)`)
  and the other fields of the same record. `WifiSecurityMode | str` leaves every unmatched
  value readable: a mode no member names stays the driver's own `str`, stored as given,
  and only the narrowing step (after the period) needs a member for it. The modes with no
  member are recorded as gaps (the security-mode line of "Known gaps" below, in `GAPS.md`
  2026-10-05), so the narrowing is decided on that record, not assumed.
  `WifiNeighbor.security_mode`, a best-effort identification of a foreign network, stays
  deferred (left as text, below).
- Management-frame protection forced by the security mode (a docstring rule on
  `WifiBss.create_bss` and `set_security`): `WPA3_SAE`, `WPA3_EAP`, `WPA3_EAP_192` (the
  WPA3-only modes), `OWE`, and any security mode on a BSS on 6 GHz require MFP. For these a
  driver applies `REQUIRED` whatever *mfp* says, and the read-back (`get_bss_config`)
  reports `REQUIRED`. This changes what a driver that today reads back `optional` for such
  a BSS reports, so it is a *Changed* changelog entry with a migration line: the driver
  reports `REQUIRED`, and a test that compared the read-back with the `mfp` it passed
  expects `REQUIRED` for these modes.
- `WifiRadioStats.tx_retries` and `tx_failed` become `int | None` (released: `int`), still
  required and in their released positions; `None` means the device reports no per-radio
  count, and `0` is never a stand-in. This is a type change of a released field with **no
  deprecation period**, the one instance of P1's stated no-period exception: a reader must
  handle `None` from this release on. The reason is
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
deprecation period, listed under *Breaking for driver authors* with its migration line. It
falls under P1's no-period exception, whose two conditions hold: the reviewed families
below report no per-radio count, and neither a twin field nor a rename-then-reclaim keeps
the released form usable (a twin would leave the released `int` required and still
unfillable for the whole period).

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
this proposal; this list is the reviewed-family list it records, in
`docs/architecture/precise-types-families.md` §2 with one line of rationale per family:
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

Known gaps, entered in `GAPS.md` (2026-10-05, "Wi-Fi: concepts the reviewed families have
and the contract cannot express"):
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
`SipServer.verify_sip_message(since: Any)` is documented as a timestamp or marker. No
existing model covers any of them.

**Proposed design**:

- New enum `PhoneState` (`IDLE`, `DIALING`, `INCALL_DIALING`, `RINGING`, `CONNECTED`,
  `INCALL_CONNECTED`, `HOLD = "hold"`, `DIALTONE`, `INCALL_DIALTONE`, `CALL_ENDED`,
  `CODE_ENDED`, `CALL_WAITING`, `CONFERENCE`, `BUSY`, `NOT_ANSWERED`): one per `is_*`
  predicate of `SipPhone`. `SipPhone.wait_for_state(state: PhoneState | str)`; an unknown
  word raises `ValueError`.
- New records (frozen, counts not negative): `RtpStats(engaged, sessions)`,
  `MwiStatus(waiting, new, old)`, `OfflineMessage(sender, body, stored_at: datetime |
  None)`. `stored_at` is required; `None` means the store reports no time for the message,
  and a driver never invents one. A driver parses the store's text as ISO 8601 the way
  `datetime.fromisoformat` does, with a `T` or a space between date and time
  (`2026-04-22 10:00:00`); the result is naive, in the store's local time, unless the text
  carries an offset; text that is not a time is a driver error.
- New mandatory members: `SipServer.read_rtpengine_stats() -> RtpStats`,
  `read_mwi_status(user: str) -> MwiStatus`,
  `read_offline_messages(user: str) -> list[OfflineMessage]`. The three old names are
  deprecated; a driver keeps them, returning the record's fields as the released dict
  (`get_offline_messages` may keep returning the stored time text unchanged).
- `SipServer.verify_sip_message(message_type: str, since: Any = None)` keeps its
  released parameter annotation under exemption class (a) of P1, as `HwConsole.get_console`
  keeps its released return (P11). The narrowing to `datetime | None` is announced (shape
  6): a docstring line and a Deprecations table row, earliest removal the first release 6
  months after the release that deprecates it. Until then a caller passing a text marker
  and an implementer declaring a narrower or other type both still type-check. Its
  docstring no longer names a product's log path or a testbed's log path: the channel is
  the log the SIP server itself writes, or a testbed log that collects it.
- Left as `str` on evidence: presence statuses (`set_presence`, `notify_presence`,
  `get_user_presence`) and `verify_sip_message(message_type)` (SIP methods, response codes
  and log markers): the provider's own words, listed in the docstrings. An `int` for a
  response code was considered and deferred: widening the parameter makes an implementer
  declaring `str` fail to conform.

**Mechanism**: extend
Three new mandatory members. The `PhoneState` retype and the announced `since` narrowing
are rung-5 `deprecate` changes in the same release; nothing in this item changes a
released signature without a period.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.sip_phone`, `testprotocols.sip_server`, `testprotocols.models`
(`voice.py`).

**Affected**: implementers of `SipServer` (three new members); callers of
`wait_for_state`; at the announced narrowing (not now), a caller that passes a text
marker as `since` and an implementer whose declared `since` does not accept
`datetime | None`. `testoperations` calls none of these members.

**Neutrality evidence**: No reviewed-family list was recorded for the voice domain before
this proposal; the reviewed-family list it records, in
`docs/architecture/precise-types-families.md` §3: a SIP proxy/registrar (Kamailio or OpenSIPS) with an RTP
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
link state, mapping protocol), and `HTTPResult` exposes the status code only as text. No existing record covers a DNS answer, a ping result, a scan result or an
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
- `HTTPResult` stays the released class: the released constructor
  (`HTTPResult(response)`) and parser, plain assignable `raw`, `code` and
  `beautified_text` attributes, identity equality. It is not made a frozen dataclass: that
  would need conversion code in its constructor (C5 forbids it) and would break attribute
  assignment and non-frozen subclasses with no period. It gains two read-only properties
  computed from the released attributes, so they follow an assignment: `status -> int |
  None` (an `int` when `code` is a number from 100 to 599, else `None`; a new name has no
  released form, so no `0` sentinel) and `body -> str`. `code` and `beautified_text` are
  deprecated in their favour by docstring and the Deprecations table only: they are plain
  attributes, and a `@deprecated` property in their place would make them read-only, so the
  checkers do not report their use.
- Static only: `DhcpServer.provision_cpe(dhcpv4_options, dhcpv6_options: dict[str,
  dict[str, object]])` (was `dict[str, Any]`); `DHCPTraceData.dhcp_packet` /
  `DHCPV6TraceData.dhcpv6_packet: Mapping[str, object]`; these three are the `object`
  open-value lines of P1, class (b).
- `MulticastClient.send_mldv2_report(mcast_group_record: Sequence[tuple[list[McastSource],
  McastGroup, MulticastGroupRecordType]], count)`: the parameter is widened from the
  released `MulticastGroupRecord` (an invariant `list` of that tuple), so both a
  caller's `list[GroupRecord]` and the released list of tuples type-check; plain tuples
  are deprecated in favour of `GroupRecord`, with the narrowing to `Sequence[GroupRecord]`
  announced. The cost, recorded under *Breaking for driver authors*: an implementer
  declaring the parameter as `list[...]` or `MulticastGroupRecord` no longer conforms
  statically and widens its declaration to `Sequence[...]`; nothing changes at run time.
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
declaration without them is reported by the checkers), and the widened `send_mldv2_report`
parameter, which an implementer declaring `list` widens too. The keyword-only parameters
take no period: every released implementer of `HttpClient.curl`, `http_get` or
`NmapScanner.nmap` stops conforming statically on upgrade. They are recorded under
*Breaking for driver authors*, in the style of the `send_mldv2_report` entry, with the
exact parameters (`curl` and `http_get`: `no_proxy: bool = False`, `insecure: bool =
False`, `follow_redirects: bool = False`; `nmap`: `fast: bool = False`) and the migration
line "add the keyword-only parameters to the implementation's signature (with the
protocol's defaults); a declaration without them is reported by the checkers". The vocabulary, option-string
and placeholder changes are rung-5 `deprecate` changes in the same release.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.http_client`, `http_server`, `nmap_scanner`, `dns_client`, `arp_client`,
`ip_routing`, `ip_interface`, `upnp_client`, `vlan_client`, `multicast_client`,
`dhcp_server`, `held_prefixes`, `testprotocols.models` (`networking.py`, `dhcp.py`,
`multicast.py`).

**Affected**: implementers of `DnsClient`, `IpRouting`, `NmapScanner`, `ArpClient`,
`IpInterface` (new members) and of `HttpClient` / `NmapScanner` (new keyword-only
parameters, breaking for their declarations; *Breaking for driver authors*);
implementers of `MulticastClient` that declare `list` (widen to `Sequence`); readers of
`HTTPResult` (`status` and `body` added; `HTTPResult` itself unchanged);
`testoperations.http_server` (P12).

**Neutrality evidence**: The "families" here are the host tools the drivers run. No list
was recorded before this proposal; the reviewed-family list it records, in
`docs/architecture/precise-types-families.md` §4: Linux hosts with iproute2, curl, nmap,
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
  - `NtpClient.read_date() -> datetime | None`. `None` means the device gave no date to
    read (its date command produced no output holding a date and time, the case in which
    the released `get_date` returned `None`); it never means "not synchronised", because
    an unsynchronised clock still has a date, which is returned. The value is naive, in
    the device's local time, unless the device reports its offset.
- Deprecated: `execute_snmp_command` (any other command has no successor), `set_date`,
  `get_date` (keeps its released text output).
- Writes: `snmp_set` is read back by `snmp_get`; `set_date_time` by `read_date`.
- `value_type` is annotated with the bare enum (no `| str`): the member is new and has no
  released form (C4).
- Types left open, with the reason: the SNMP members return the tool's output text, as
  the released member did; a typed varbind record is not proposed here for lack of a
  second implementer's parse, and is entered in `GAPS.md` (2026-10-05, "`SnmpClient`
  typed varbind return").

**Mechanism**: extend
Six new mandatory members; the deprecations ride the same release.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.snmp_client`, `testprotocols.ntp_client`, `testprotocols.models`
(`networking.py`, `SnmpValueType`).

**Affected**: implementers of `SnmpClient` and `NtpClient` (six new members; an
`snmp_set` implementer maps each `SnmpValueType` member to its tool's type code and raises
`NotSupportedError` for one its tool cannot set); callers of `snmp_set` pass a
`SnmpValueType` member. `testoperations` calls none of these members.

**Neutrality evidence**: `SnmpClient` and `NtpClient` are host-substrate instruments. The
recorded substrate-tool rule (`packet-injection-substrate-design.md` §2) lets a
single-substrate host-tool wrapper clear the bar; the substrate survey it asks for is
recorded in `docs/architecture/precise-types-families.md` §5, as substrate evidence, not a
supported-backends list.
- Vendor-free reference: RFC 3416 (the SNMP operations: get, get-next as walked, set,
  get-bulk with `non-repeaters` and `max-repetitions`) and RFC 2578 (the SMI base types,
  which `SnmpValueType` follows, plus the BITS construct). The members carry those
  operations and types, not a tool's syntax.
- Net-SNMP command-line tools on Linux hosts, the released implementers' family: the SNMP
  library of a released implementer framework drives exactly `snmpget`, `snmpwalk`,
  `snmpset` and `snmpbulkget` with `-v 2c -On -c <community> -t <seconds> -r <retries>`,
  the parameters typed here; the `snmpset` type letters (`i`, `u`, `s`, `o`, `a`, `t`,
  `b`) map one to one onto `SnmpValueType`.
- pysnmp, the second, independent client family (a pure-Python SNMP engine with no shared
  code): its get, set, next (walk) and bulk commands take a v2c community, a transport
  timeout and retry count, and the RFC 2578 value types (`Integer32`, `Unsigned32`,
  `Gauge32`, `OctetString`, `ObjectIdentifier`, `IpAddress`, `TimeTicks`, `Bits`), so a
  driver maps the members onto it the same way.
- NTP: the reference is the device's own date. The one `set_date` option seen is
  `date -s`; `set_date_time` takes a `datetime` and leaves the formatting to the driver.

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
- `MeasurementSpec.completion` lifts a recorded deferral. GAPS 2026-06-11 ("migrate legacy
  bare-`str` value fields to typed vocabularies") lists it among the "vendor-divergent /
  undocumented fields … not enum-safe … defer until a test needs them". The lift is argued
  as for `WifiBssConfig.security_mode` (P6). The entry's own trigger is met ("touching a
  given legacy capability for other reasons"): this item retypes `MeasurementSpec.tool`
  and `QoeBrowser.measure_productivity(wait_until)`, which carries the same completion
  words, in the same change. `QoeCompletion | PageCompletion | str` leaves every unmatched
  value readable: a completion no member names stays the driver's own `str`, stored as
  given. The completions with no member, or no form on a reviewed family, are recorded
  (Families §6: Puppeteer's `networkidle2` has no `PageCompletion` counterpart, and
  `commit` has no Puppeteer form), so the narrowing is decided on that record.
  `QoEResult.protocol`, deferred by the same line, stays `str`.
- Lever: `inject_event` has no state to read back; the observation that confirms it is the
  impairment seen on the path (the `testoperations` measurement around it), as for the
  released member. The member's docstring states this.
- The deprecated `dict` form of the impairment profile (`dict[str, object]`) is the `object`
  line of class (a) in P1.

**Mechanism**: extend
Three new mandatory members. The vocabulary and profile retypes ride the same release as
rung-5 `deprecate` changes.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.iperf_client`, `iperf_server`, `netem_controller`, `qoe_browser`,
`testprotocols.models` (`traffic.py`, `impairment.py`, `qoe.py`).

**Affected**: implementers of `IperfClient`, `IperfServer`, `NetemController` (new
members); `testoperations.throughput`, `netem_controller`, `sdwan`, `iperf_client`,
`iperf_generator` (P12), which call the new names with a fallback to the released ones.

**Neutrality evidence**: `IperfClient`, `IperfServer`, `NetemController` and `QoeBrowser`
are host-substrate instruments of the class the recorded substrate-tool rule
(`packet-injection-substrate-design.md` §2) covers; the substrate survey is recorded in
`docs/architecture/precise-types-families.md` §6: iperf3 and iperf2 for traffic, Linux
`tc` with `netem` and FreeBSD `dummynet` for impairment, Playwright and Puppeteer for QoE.
Vendor-free references: RFC 6349 (TCP throughput testing), RFC 7679 (one-way delay),
RFC 7680 (one-way loss) and RFC 3393 (delay variation, the jitter field), and the HTML
standard's `DOMContentLoaded` and `load` events.
- Session parameters: iperf3 `-c`, `-p`, `-b`, `-B`, `-4` / `-6`, `-u`, `-t`, `--cport`,
  `-R`, `-O`, `-J`, `-w`, `-P`, `-l`, `-i`; iperf2 shares most and lacks `-J` and
  `--cport`, so a driver for it raises on those. The window is in bytes because iperf
  size suffixes are binary (`8M` is 8388608) and the text grammar differs between tools.
- Transient events: netem `delay <latency> <jitter>`, `loss`, `duplicate`; a blackout is
  100 % loss. The field names are what the released implementers read. A `dummynet` pipe
  gives `delay` (milliseconds) and a packet-loss rate (`plr`, 0 to 1), so `Blackout` and a
  loss-only `PacketStorm` map onto it directly; it has no duplication option (a driver
  raises when duplication is requested), and variable delay exists there only as a
  `profile` file (an empirical extra-delay distribution), not as a jitter value.
- Page completions: the four load states of the Playwright `wait_until` option (`load`,
  `domcontentloaded`, `networkidle`, `commit`). Puppeteer's `waitUntil` gives `load`,
  `domcontentloaded` and `networkidle0` (no network connections for 500 ms, Playwright's
  `networkidle` definition); `commit` has no form there and a driver raises for it. The
  other completions (`duration`, `response`, `connect`) come from the QoE specification's
  tool-by-completion matrix of a released implementer framework.

### P11 — capability protocol device management, content filtering, consoles and RADIUS status

**Item**: `P11`, capability protocol (`DeviceManagement`, `ContentFiltering`,
`HwConsole`, `RadiusServer`), the returned-object contract `Console`, and models
(`MemoryUtilization`, `ProcessInfo`, `EventLogEntry`, `SyslogSeverity`, `UrlRules`,
`ServiceStatus`).

**Need**: The device-management readers return dicts and lists of dicts; the event log
mixes parsed entries with `{"unparsable": line}`; `get_running_processes` takes a free
process-listing option string; `ContentFiltering.get_url_rules` returns a bare
`tuple[list[str], list[str]]` (allowed, blocked), which question 9 forbids;
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
  output, unparsable lines included), `get_url_rules` (keeps its released tuple, the
  fields of `read_url_rules()` as lists).
- New returned-object contract `Console` (`runtime_checkable`): `execute_command(command:
  str, /, timeout: int = -1) -> str`, `sendline(text: str = "", /) -> int` (the bytes
  written), a read-only `before: str | bytes | None`, `start_interactive_session() ->
  None`. `expect` / `expect_exact` are not members: no single contract type matches a
  console library's own pattern types; a caller that matches patterns keeps the concrete
  console type.
- `HwConsole.get_console` (`Any`) and `get_interactive_consoles` (`dict[str, Any]`) keep
  their released returns under the compatibility exemption (P1, class (b), 2 lines). Their
  docstrings state that the returned objects satisfy `Console`, and the narrowing to
  `Console` / `Mapping[str, Console]` is announced in the Deprecations table (shape 6),
  with the period kept: a console lacking a `Console` member stops conforming only then.
- `Console` is a returned-object contract, not a capability, recorded so in
  `docs/architecture/precise-types-families.md` §8: no device archetype composes it and
  none gains a `Console` attribute; it is counted in no capability inventory and its
  members under no capability's new-mandatory-member total; a driver never implements it
  as a capability of a device, because the console it returns satisfies it structurally.
  The capability-only-archetypes rule is untouched.
- Announced only: `RadiusServer.get_status -> ServiceStatus`.
- Left as text on evidence: `EventLogEntry.timestamp` (the syslog date has no year; a
  `datetime` would invent one); `ProcessInfo.tty`.

**Mechanism**: extend
Four new mandatory members. `Console` is not a capability and adds no counted member; the
`HwConsole` narrowing is announced only, and the retypes ride the same release.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testprotocols.device_management`, `content_filtering`, `hw_console`, `radius_server`,
`testprotocols.models` (`device_management.py`, `radius.py`); `Console` is also exported
as `testprotocols.Console`; the reviewed-family list and the `Console` record in
`docs/architecture/precise-types-families.md` §7 and §8.

**Affected**: implementers of `DeviceManagement`, `ContentFiltering` (new members);
implementers of `HwConsole` (nothing now; at the announced narrowing their returned
consoles must have the `Console` members); a console whose `sendline` is declared to
return something other than `int` does not satisfy `Console` statically. `testoperations`
never touches a console and calls none of these readers.

**Neutrality evidence**: Reviewed-family list recorded by this proposal in
`docs/architecture/precise-types-families.md` §7: Linux hosts and gateways (procps `ps`,
`free`, BSD syslog), the SD-WAN appliance families for content filtering, and
pexpect-based consoles (serial, SSH, telnet) for `Console`.
- `MemoryUtilization`: the columns of `free -b` (total, used, free, shared, buff/cache,
  available); older kernels report no `available`, hence the all-or-none rule.
- `ProcessInfo`: `ps -A` (procps) gives PID, TTY, TIME (`[DD-]hh:mm:ss`), CMD.
- `EventLogEntry`: RFC 3164 (BSD syslog) priority, timestamp without a year, hostname,
  tag, message; severity derived from the priority (RFC 5424 table).
- `UrlRules`: the Meraki MX content-filtering API has `allowedUrlPatterns` and
  `blockedUrlPatterns`; FortiGate web-filter URL filter entries carry allow / block
  actions; the two lists are the shared shape. Catalyst SD-WAN, Prisma SD-WAN and VeloCloud
  URL filtering were not checked for this item and are the first to check when the member
  next changes.
- Forward note, not a change of this item: `ContentFiltering.set_url_rules` replaces two
  pattern lists, which a reviewed appliance family realises in more than one device step.
  It wants the failure-outcome sentence P3 and P5 give their list replaces (a write
  failing at any step, rejected or not verified, leaves the as-found state). This item
  changes only the read side (`read_url_rules`), so the sentence is added when the write
  is next touched.
- `Console`: the members the callers of returned consoles were seen to use
  (`execute_command`, `sendline`, `before`, `start_interactive_session`) in a released
  implementer framework's CPE libraries and the released example implementers; a
  type-checked test checks that a `pexpect.spawn` subclass with those members satisfies
  `Console` under `types-pexpect`, whose `sendline` returns `int`.

### P12 — operation `testoperations` typed records and the transition

**Item**: `P12`, operation (`testoperations` operations and their records, and the
public pair readers `testoperations.pairs`).

**Need**: Several operations return `dict` or `Any`, take closed sets as `str`, or take
`Callable[..., X]` stand-ins; and P1 (C6) puts the transition between released and new
forms in `testoperations`, so its operations keep working with a driver that has only the
released form for the whole period.

**Proposed design**:

- Transition, internal: fallback accessors (`_renamed.py`: the new member when the driver
  has it, else the old) for `start_sender_session`, `start_receiver_session`,
  `inject_event`; `coerce_enum(E, value, what=…)` in `_compat` for the operations' own
  released `str` parameters (a member passes; a plain string naming a member warns at the
  caller and converts; any other string raises `ValueError` listing the legal values;
  another type raises `TypeError`); the parser of traffic-generator window sizes.
- Transition, public: the module `testoperations.pairs` (with `__all__`), the readers of
  every text/typed pair of P2, P3 and P5 with the read rule of C3 —
  `firewall_rule_dst_ports`, `nat_rule_dst_ports`, `nat_rule_translated_ports`,
  `l3_rule_src_ports`, `l3_rule_dst_ports` (each `-> tuple[PortRange, ...]`),
  `security_event_timestamp -> datetime | None`, `qos_rule_classifier -> QosClassifier |
  None` — and the parsers of the released text forms (`parse_port_ranges`,
  `parse_nat_port_ranges`, `parse_timestamp`, `parse_qos_classifier`). Each reader and
  parser is removed in the release that removes the text fields it reads; its docstring
  says so.
- New records (frozen), each over a shared `ReleasedMapping` mixin that keeps the released
  dict readable with a `DeprecationWarning` for the period: `IperfSession(sender,
  receiver)` (from `start_iperf`), `HomeVerification(vlan_defined, subnet_advertised,
  peers_reachable, details: HomeDetails)` and `HomeDetails(defined_subnet,
  defined_gateway, peer_states)` (from `verify_home`), `FlowPair(a_to_b, b_to_a)` (from
  `saturate_link`). The operations keep their names. The released-dict reads are the
  `object` lines of class (a) in `testoperations` (P1).
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
  recorded under *Changed* and under *Consumer action* with the migration line
  `start_iperf(client, server, port, host="<receiver address>")`.
- `inject_packet_storm` gains keyword-only `loss_percent`; `duplicate_percent` defaults to
  `None` and reaches a new-name driver only when the caller passes it.
- Fixes that ride along, recorded under *Fixed*: `tcpdump` makes the protocol's calls
  (typed `PcapCapture`); `start_http_server`'s default `ip_version` becomes `"4"`;
  `inject_latency_spike(latency_ms)` takes effect with a new-name driver.
- `iter_json_docs -> list[dict[str, JsonValue]]` (was `list[Any]`): each document is a
  JSON object, and `JsonValue` (new and public in `testoperations.throughput`) is the
  recursive type of a parsed JSON value; `sender_life_record(iperf_client: IperfClient)`.
  The released public alias `JsonObj` (`Mapping[str, object]`, a module-level `object`
  that P1 counts) keeps its name and becomes `Mapping[str, JsonValue]`: `JsonValue` types
  it precisely, so it needs no exemption. A value of the alias still passes where
  `Mapping[str, object]` is expected (recorded under *Changed*).

**Mechanism**: deprecate
The released `str` parameters and dict returns are retyped with a deprecation period
(widen, then narrow; the dict reads warn until removal). The required `host` on
`start_iperf` is the one breaking signature change; it repairs an operation that could not
work with any driver.

**Placement**: promote (maintainer change; implementation on `feat/precise-types`) —
`testoperations` (`pairs`, `_compat`, `_renamed`, `_released`, `segmentation`,
`netem_controller`, `throughput`, `iperf_client`, `iperf_generator`, `homing`, `sdwan`,
`pcap_capture`, `http_server`, `_capture`, `marking_observation`, `path_placement`).

**Affected**: callers of `start_iperf` (pass `host=`), `verify_home`, `saturate_link`
(read the fields), `build_deny_rule`, `apply_preset`, `NonCompletion` (pass members);
stand-ins passed as `measure` / `measure_flow`; consumers that read a text/typed pair
(use `testoperations.pairs`). Drivers with only the released names keep receiving exactly
the released calls.

**Neutrality evidence**: No device family is involved beyond those of P2, P3, P5 and P10,
whose evidence applies; the operations are tool-neutral. A search of the released
implementers found no caller of `start_iperf`, `verify_home`, `saturate_link` or
`iter_json_docs`. The reference corpus holds no reference driver for the capabilities
this proposal touches, so the search covers the released implementers only.

## Not touched by this proposal

Question 9 notes these existing members, which stay imprecise and are not retyped here:

- `ZonePolicy.action: str` and `Zone.default_input`, `default_forward` and
  `default_output` (`"accept"`, `"drop"`, `"reject"`), which `DefaultAction` (P2) could
  type;
- `FirewallRule.application_category: str | None`, whose common values are those of
  `ApplicationCategory`;
- `FlowMatch.src_port` / `dst_port: str = "any"`, port text that `PortRange` (P2) could
  type;
- the 12 TR-069 RPCs and the four compatibility signatures of P1 (exemption policy), and
  the three `object` open values of P1.

The first two lines, and `TrafficShapingRule.priority` / `match` (which go with their
deprecated class), are folded into `GAPS.md` 2026-06-11 ("migrate legacy bare-`str` value
fields to typed vocabularies") as the fields of that entry that remain afterwards, with
its trigger: retype them when `firewall_zones` or the firewall models are next touched.
Further imprecise members found later go into that entry, not into this list.

## Reference implementations and verification

The reference corpus holds no reference driver and no capability matrix for any
capability this proposal touches, so no reference driver is changed before the `feat:` PR
merges. This is a forward condition on the archetypes that later reach these
capabilities: each implements every new mandatory member, or stubs it with
`NotSupportedError` and a cited source, with the plugin driver shape, verified writes and
acknowledged calls that `docs/archetypes/README.md` requires (question 7). Each new
member and changed field has a test for the positive and the negative or edge path; the
`feat:` PR runs the test suites and both static checkers on Python 3.12 (the minimum,
including an environment without `typing_extensions`) and on a current Python release.

## Round 2 — response to conditions

Every item above is revised in place to describe the branch `feat/precise-types` as it now
is. "Design" is `docs/architecture/precise-types-design.md`; "Families" is
`docs/architecture/precise-types-families.md`.

| Condition | Resolution | Where |
| --- | --- | --- |
| C1 (P1) | Moot: `testprotocols` takes no runtime dependency. The marker is imported from `typing_extensions` under `TYPE_CHECKING` only (the checkers' bundled stubs), from `warnings` on Python 3.13 and later, and is an identity marker on 3.12; `dependencies = []` as released. | P1 "The marker without a dependency"; `testprotocols/_compat.py`, `testprotocols/pyproject.toml`, `tests/test_compat_marker.py`; Design C2 |
| C2 (P1) | mypy's `deprecated` error code is enabled in the workspace `enable_error_code`; the text says pyright reports in strict mode and mypy with that code. | P1 C2 and Neutrality evidence; root `pyproject.toml`; Design C2, CONTRIBUTING "Releases", `docs/proposals/README.md` |
| C3 (P1) | Taken: the zero-dependency alternative, with the identity fallback on 3.12. | as C1 |
| C4 (P1) | `object` in public signatures, fields and type aliases is counted by the ratchet, ceiling 0, exempt lines pinned per class: (a) deprecated form, 4 lines in `testprotocols` and 6 in `testoperations`; (b) open value, 3 lines in `testprotocols`. `Console.sendline` and `iter_json_docs` are given precise types instead. | P1 exemption policy; `tests/test_typing_ratchet.py`; Design "Exemption policy for explicit `Any` and `object`" |
| C5 (P1) | Pair reading is published `testoperations` surface: the module `testoperations.pairs` holds the readers and the released-text parsers. | P1 C6, P12; `testoperations/pairs.py`; CHANGELOG *Added*; CONTRIBUTING "Versioning"; `docs/proposals/README.md` |
| C6 (P1) | Mechanism stays `deprecate`, the rung whose procedure P1 amends (the hygiene check requires a rung value); the text says P1 adds no member and amends the rung-5 procedure P2–P12 use. The four findings are recorded. | P1 Mechanism and Need; Design "Why the runtime warning left `testprotocols`" |
| C7 (P6–P11) | The reviewed-family lists are recorded with one line of rationale per family; merging the `feat:` PR ratifies them. | Families §2–§7; each item's Neutrality evidence |
| C8 (P2) | `RuleAction` is not extended: it types `L3Rule`, `L7Rule` and `SwitchAclRule` actions, which `REJECT` / `LOG` would widen. `DefaultAction` and `SecurityAction` are different sets (unmatched traffic; an event's outcome). | P2 Proposed design; branch `docs/architecture/precise-types-design.md` (Vocabulary and boundary decisions) |
| C9 (P2) | `RuleCounters` comes from new members because narrowing the released return to a `NamedTuple` breaks implementers declaring `tuple[int, int]`; `GroupRecord` is a parameter, where the tuple stays accepted. | P2 Proposed design; branch `docs/architecture/precise-types-design.md` (Vocabulary and boundary decisions) |
| C10 (P2) | `Zone.default_input` / `default_forward` / `default_output` and `FirewallRule.application_category` are added to "Not touched"; the remainder is folded into GAPS 2026-06-11. | "Not touched by this proposal"; `GAPS.md` 2026-06-11 update |
| C11 (P2) | The new members require `NotSupportedError`; the deprecated members keep their released `NotImplementedError` text. | P2 Proposed design; `packet_filter.py`, `nat.py` docstrings; CHANGELOG *Breaking for driver authors* |
| C12 (P3, P5) | `L3Firewall.set_outbound_rules` / `set_inbound_rules` / `set_vpn_rules` and `SwitchQos.set_rules` state that a write failing at any step, rejected or not verified, leaves the as-found state. | P3, P5 Writes; `l3_firewall.py`, `switch_qos.py` docstrings |
| C13 (P4) | `Telemetry.uptime_seconds: float \| None`, required, `None` meaning no uptime reported; GAPS 2026-06-11 "appliance health / online capability" cited and updated. | P4 Proposed design; `models/wan_edge.py`; Design (Telemetry and policy); `GAPS.md` |
| C14 (P4) | `Router.get_telemetry` keeps its released `dict[str, Any]` under exemption class (a) until removal; the class (a) count is 9. | P4; P1 exemption policy; `router.py`; Design |
| C15 (P4) | Boundary stated: `DeviceManagement` is host access, composed only by `CpeDevice`; `Router` telemetry is the routing device's summary health, composed by the SD-WAN archetypes; an API-managed appliance composes `Router`, not `DeviceManagement`. | P4 Proposed design; branch `docs/architecture/precise-types-design.md` (Vocabulary and boundary decisions) |
| C16 (P4) | The readers of `UplinkStatus.state` (`ApplianceUplinks.get_uplinks` / `get_uplink`) are listed under Affected, with why the widening is safe at run time and where an exhaustive match is told statically. | P4 Affected |
| C17 (P6) | Recorded as P1's stated no-period exception, with both conditions; `WifiRadioStats.tx_retries` / `tx_failed` is its one instance. | P1, P6; Design "The no-period exception"; CHANGELOG *Breaking for driver authors* |
| C18 (P6) | The MFP read-back rule has a *Changed* changelog entry with a migration line. | P6; CHANGELOG *Changed* |
| C19 (P6) | The listed Wi-Fi gaps are entered in `GAPS.md`. | P6 Known gaps; `GAPS.md` 2026-10-05 Wi-Fi entry |
| C20 (P7) | `verify_sip_message`'s docstring no longer names a product's or a testbed's log path. | P7; `sip_server.py` |
| C21 (P7) | `OfflineMessage.stored_at: datetime \| None`, `None` when the store reports no time; the accepted text form is ISO 8601 as `datetime.fromisoformat` reads it. | P7; `models/voice.py` |
| C22 (P8) | `HTTPResult` stays the released parsing class; `status` and `body` are read-only properties over the released attributes. | P8; `models/networking.py`; Design (Host-tier records) |
| C23 (P8) | `status -> int \| None`, no `0` sentinel; its deprecation row is removed. | P8; Design Deprecations table |
| C24 (P8) | Moot: nothing is frozen, so attribute assignment, subclassing and equality are as released; no breaking entry is needed. | P8; CHANGELOG |
| C25 (P8) | `send_mldv2_report` takes a `Sequence` of the released tuple, accepting `list[GroupRecord]`; the cost to an implementer declaring `list` is recorded. | P8; `multicast_client.py`; CHANGELOG *Breaking for driver authors* |
| C26 (P9) | SNMP / NTP substrate survey recorded, citing the substrate-tool rule, with RFC 3416 / RFC 2578 and a second independent client family; `read_date`'s `None` defined; the varbind gap entered. | P9; Families §5; `ntp_client.py`; `GAPS.md` 2026-10-05 varbind entry |
| C27 (P10) | Traffic / impairment / QoE substrate survey recorded the same way; `inject_event`'s confirming observation is in its docstring. | P10; Families §6; `netem_controller.py` |
| C28 (P11) | Need corrected: `get_url_rules` returns `tuple[list[str], list[str]]`. | P11 Need |
| C29 (P11) | `HwConsole.get_console` / `get_interactive_consoles` keep their released returns under the compatibility exemption (class (b), now 16 lines); the narrowing to `Console` is announced in the Deprecations table. | P11; P1 exemption policy; `hw_console.py`; Design Deprecations table; CHANGELOG *Deprecated* |
| C30 (P11) | Recorded that `Console` is a returned-object contract, not a capability. | P11; Families §8 |
| C31 (P12) | `start_iperf`'s required `host=` has a *Consumer action* entry with a migration line. | P12; CHANGELOG *Consumer action* |
| C32 (P12) | The caller search covers the released implementers only; the closing section is a forward condition on the archetypes that later reach these capabilities. | P12 Neutrality evidence; "Reference implementations and verification" |

## Round 2 — response to the round-two conditions

The round-two review approved with conditions C1–C6. Each is resolved on the branch
`feat/precise-types` and in the items above, revised in place. "Design" is
`docs/architecture/precise-types-design.md`; "Families" is
`docs/architecture/precise-types-families.md`.

| Condition | Resolution | Where |
| --- | --- | --- |
| C1 (P1, P12) | Inventory completed. The device registry's `cast("Any", protocol)` is removed: it reads a protocol's members with `typing.get_protocol_members` on Python 3.13 and later and through a cast to a one-member private protocol over `__protocol_attrs__` on 3.12, with identical member sets on both. The released public alias `JsonObj` keeps its name as `Mapping[str, JsonValue]` (was `Mapping[str, object]`), so it needs no exemption. Counts restated per package: `testprotocols` 10 class (a) and 16 class (b) `Any` lines, 4 class (a) and 3 class (b) `object` lines; `testoperations` no `Any` line and 6 class (a) `object` lines (class (a) `Any` is 10 after C4). | P1 exemption policy; P12; `testprotocols/devices/__init__.py`, `testoperations/throughput.py`; `tests/test_typing_ratchet.py`; Design "Exemption policy for explicit `Any` and `object`"; CHANGELOG *Changed* (`JsonObj`) |
| C2 (P1, P4) | The dev group requires `mypy>=1.17` (was `>=1.10`; `deprecated` is mypy 1.14, `exhaustive-match` 1.17); `enable_error_code` lists `explicit-override`, `exhaustive-match` and `deprecated`, and P1's checker configuration now lists `exhaustive-match`; `uv.lock` updated. | P1 "The checker configuration", Placement, Neutrality evidence; P4 Affected; root `pyproject.toml`, `uv.lock`; `CONTRIBUTING.md`; Design (the rule list) |
| C3 (P2, P6, P10, P1) | GAPS 2026-06-11 settled where this proposal executes it. `FirewallRuleAction` gains `ALERT` (the value a released implementer reports; a docstring line says so), so no implementer moves to `LOG`. Its "do not unify the action vocabularies" line is cited for the three-enum answer. P1 states that C4/C5 decide the entry's gating (A)-vs-(B) question as (A), annotation and checker only. P6 and P10 argue the lift of the entry's deferral of `WifiBssConfig.security_mode` and `MeasurementSpec.completion`: the entry's own trigger is met, `E \| str` leaves every unmatched value readable, and the values with no member are recorded. | P1 (after the no-period exception); P2 Proposed design; P6 and P10 Proposed design; `models/firewall.py`; `tests/test_firewall_vocabularies.py`; CHANGELOG *Added*; Design (firewall vocabularies) |
| C4 (P7) | `verify_sip_message` keeps its released `since: Any = None` under exemption class (a), marked on the `def` line of the multi-line signature; the narrowing to `datetime \| None` is announced (shape 6) in a docstring line and a Deprecations table row with the usual earliest removal. The text that narrowed it at once is removed; the docstring keeps the cleanup of the product and testbed log paths. The ratchet pins 10 class (a) lines. | P7; P1 exemption policy; `sip_server.py`; `tests/test_voice_precise_types.py`, `tests/test_typing_ratchet.py`; Design Deprecations table and (Voice vocabularies); CHANGELOG *Deprecated* |
| C5 (P8) | *Breaking for driver authors* records the keyword-only parameters on `HttpClient.curl` / `http_get` (`no_proxy`, `insecure`, `follow_redirects`, each `bool = False`) and `NmapScanner.nmap` (`fast: bool = False`), in the style of the `send_mldv2_report` entry, with the migration line "add the keyword-only parameters to the implementation's signature (with the protocol's defaults); a declaration without them is reported by the checkers". The Scope paragraph names them beside the 26 new members. | P8 Mechanism and Affected; Scope; CHANGELOG *Breaking for driver authors* |
| C6 (P6–P11) | Carried to the `feat:` PR: merging it, which takes the decision-file review, ratifies `docs/architecture/precise-types-families.md`. Until then each item's evidence stands on the proposed list. | Families; Scope; the `feat:` PR |

The review's observation on `ContentFiltering.set_url_rules` (a multi-step list replace
that wants the failure-outcome sentence) is recorded as a forward note in P11, not as a
change here.

## Outcome

| Item | Decision | Date |
| --- | --- | --- |
| P1 | accepted with conditions | 2026-10-05 |
| P2 | accepted with conditions | 2026-10-05 |
| P3 | accepted | 2026-10-05 |
| P4 | accepted with conditions | 2026-10-05 |
| P5 | accepted | 2026-10-05 |
| P6 | accepted with conditions | 2026-10-05 |
| P7 | accepted with conditions | 2026-10-05 |
| P8 | accepted with conditions | 2026-10-05 |
| P9 | accepted with conditions | 2026-10-05 |
| P10 | accepted with conditions | 2026-10-05 |
| P11 | accepted with conditions | 2026-10-05 |
| P12 | accepted with conditions | 2026-10-05 |

The conditions of both rounds (round one C1–C32, round two C1–C6) are carried to the
`feat:` PR, which cites this document's path (`docs/proposals/2026-10-05-precise-types.md`)
and the item ids P1–P12; the code reviewer checks each implemented item against them.

---

## Review response (testprotocols review team, 2026-10-05)

| Item | Decision | Reason |
| --- | --- | --- |
| P1 | accept with conditions | The reopening of the runtime-`DeprecationWarning` rule is argued explicitly on concrete evidence and the period is kept; the dependency floor is wrong, mypy's `deprecated` code is not on by default, and the `Any` ratchet does not cover the `object` this proposal substitutes for it. |
| P2 | accept with conditions | Sound against the recorded appliance list; the existing `RuleAction` and `Zone`'s policy fields are not accounted for, and the new-member-vs-`NamedTuple` choice is unargued. |
| P3 | accept with conditions | Twin fields and announced narrowings are right; the list-replace writes the reshaped records feed state no failure outcome. |
| P4 | accept with conditions | `read_telemetry` is earned, but a required `uptime_seconds` lands host-shaped health on the appliance archetype that GAPS 2026-06-11 kept it off, the `get_telemetry` narrowing is a break with no period, and the `DeviceManagement` overlap is unnamed. |
| P5 | accept with conditions | `QosClassifier` is well evidenced against the recorded switch list; `set_rules` is a list replace with no stated failure outcome. |
| P6 | accept with conditions | Thorough standards-first evidence; the `WifiRadioStats` retype takes no deprecation period, the MFP read-back change needs a migration line, and the family list must be recorded in a design document. |
| P7 | accept with conditions | Records and `PhoneState` are right; the family list needs recording and the retyped member's docstring carries a neutrality defect to clean. |
| P8 | accept with conditions | Mostly well-grounded in the host tools; `HTTPResult` as written contradicts P1's own C1/C5, its `status` sentinel is avoidable, and `list[GroupRecord]` cannot satisfy the released invariant `list` parameter. |
| P9 | accept with conditions | A single-substrate host-tool wrapper is in line with the recorded substrate rule, but the survey must be recorded and the `None` of `read_date` defined. |
| P10 | accept with conditions | Records and enums are precise and the lever is named; the substrate survey must be recorded. |
| P11 | accept with conditions | The records are the right shape; the Need misstates `get_url_rules`, the `HwConsole` narrowings break with no period, and `Console`'s class must be recorded. |
| P12 | accept with conditions | The transition layer is the right home and `start_iperf` is a real repair; its caller break needs the right changelog section and the corpus half of the caller search does not exist. |

### 0. Neutrality

Met. No organisation, customer, site, hostname, address, person or ticket
identifier appears anywhere in the document; no IP literal appears at all. The
Use case field is `—` (maintainer-originated), which the rule allows. Device
vendor and product names — Meraki, FortiGate, Catalyst, Prisma, VeloCloud,
Aruba, Juniper, Omada, UniFi, Arista, Airties, Broadcom, Qualcomm, prplOS and
the rest — appear only inside **Neutrality evidence** blocks; the consumer
frameworks are referred to indirectly ("a released open-source implementer
framework", "the released example implementers"), which is the right handling.

Two judgement calls, recorded so the next round does not relitigate them:

- Python toolchain names (`typing_extensions`, `warnings`, mypy, pyright) appear
  in P1's Proposed design, outside Neutrality evidence. This is not a violation:
  `CONTRIBUTING.md` ("Development workflow") names the same tools in the open,
  and the rule's "vendor and tool names" means the device families and test
  instruments the contracts abstract, not the repository's own build chain.
- Released public symbols that embed a tool name (`NmapScanner.nmap`,
  `PcapCapture.start_tcpdump`, `HttpClient.curl`, `IperfClient`,
  `NetemController`, `iwlist_supported_channels`) are named throughout. They are
  the contract's own API and unavoidable here.

One neutrality defect is in the *existing* contract, on a member P7 retypes:
`SipServer.verify_sip_message`'s docstring names a vendor tool's log path and a
named testbed's log path. It is not this document's violation, so it does not
block; it is C20, to be cleaned by the `feat:` PR that touches the member.

### 1. Recorded decisions

P1 reopens one recorded decision and does so explicitly, which is what question 1
asks: `docs/proposals/README.md` ("How rung 5 is done") and `CONTRIBUTING.md`
("Releases") both require a runtime `DeprecationWarning`, and C1 removes it from
`testprotocols` while C6 keeps it in `testoperations`. The four pieces of
evidence are concrete and the deprecation period itself (one MINOR and six
months) is kept, as is the operations-honour-the-period rule. The evidence is
cited to a branch history rather than to a tracked record, which C6 fixes.

Two recorded entries the proposal does not cite and should:

- **GAPS 2026-06-11, "migrate legacy bare-`str` value fields to typed
  vocabularies"** names `LinkStatus.state` and `TrafficShapingRule.priority` /
  `match` — P4's fields exactly — sets the trigger as "touching a given legacy
  capability for other reasons", and records that `StrEnum` migration is
  low-risk because a member *is* its string. That entry supports the sweep; its
  design note ("one capability per change", "not as one sweep") is the one line
  this proposal departs from, and the departure is defensible because every
  family item is separable and separately mechanised. Cite the entry, say which
  of its fields remain afterwards, and update it at merge.
- **GAPS 2026-06-11, "appliance health / online capability"** records that
  host-shaped health was deliberately left off the managed appliance, that a
  cloud-managed appliance "can satisfy only a couple of" `DeviceManagement`'s
  methods, and that the shape, when picked up, is a separate `ApplianceHealth`
  with `get_uptime_seconds() -> float | None`. `SdwanApplianceDevice` composes
  `routing: Router` (`devices/sdwan.py`), so P4's new mandatory
  `read_telemetry() -> Telemetry` with a **required** `uptime_seconds: float`
  pushes a host-shaped read onto that archetype. The released
  `Router.get_telemetry` already sits there, so this is not a silent reopening —
  it is a tightening of a member the appliance already carries — but the
  required field is the part the recorded entry argues against, and the recorded
  entry's own answer (`float | None`) is the fix. C13.

Nothing else in `docs/architecture/` is contradicted. The SPLITS and LEVELS
records are untouched by every item.

### 2. Vendor and tool neutrality

Resolved per domain, in the order the method requires.

**Lists already recorded, and correctly used.** P2 and P3 run against the
SD-WAN appliance list recorded in `sdwan-appliance-protocol-design.md` — Meraki
MX, Catalyst SD-WAN, FortiGate, Prisma SD-WAN, Arista (VeloCloud), the fifth
added by that document's v2 review. P5 runs against the L2 switch list recorded
in `l2-switch-protocol-design.md` — Meraki MS225, Aruba Instant On 1960, UniFi
Pro 48, Catalyst 9200L, Juniper EX2300, TP-Link Omada SG3452P, with Arista
CCS-720D as the confirming column. Both checks hold. Three thin cells are
admitted rather than papered over (appliance port grammars on three of five;
Aruba / Omada / UniFi classifier support; Prisma and VeloCloud event-time
formats), which is the right way to report them.

**Domains with no recorded list.** P6 (Wi-Fi), P7 (voice), P8 (host tools), P9
(SNMP / NTP), P10 (traffic, impairment, QoE) and P11 (device management,
content filtering, consoles) each propose one. Each is representative,
independent and documentation-published, and P6's is standards-first (Wi-Fi Data
Elements v3.0, EasyMesh v6.1, TR-181 Device:2.21 as the reference, families
compared to it) — the strongest form. They are **proposed, not ratified**, and
they live only in this proposal: ratifying them into a design document under
`docs/architecture/` is C7.

For P8, P9 and P10 the right bar is not the cross-vendor sweep. The recorded
rule in `packet-injection-substrate-design.md` §2 is that a host-substrate
instrument — the class of `NmapScanner`, `PcapCapture`, `NetemController`,
`IperfGenerator`, `NetworkProbe` — proves neutrality by tool universality, and
"every substrate tool in this class landed as a single-substrate host-tool
wrapper with no cross-vendor sweep". `SnmpClient` is that class, so P9's
one-family argument clears the recorded bar; what it misses is that the same
document still records a **substrate survey** with a vendor-free reference. P9's
vendor-free reference is RFC 3416 and RFC 2578, which is a good one. Record the
survey and name a second independent client (C26); do the same for P10 (C27).

### 3. Placement ladder walked

Every item above rung 2 names a Mechanism, and the rung-5-before-rung-6 rule is
respected throughout: `Console` is the only new `Protocol` and it is not a
capability (C30). I searched `PUBLIC_MAIN` and the index for cheaper rungs the
items missed.

- **Rung 1 / 2 does not reach the need.** A driver cannot make a type checker
  verify a `Protocol` member it does not declare, so no driver-local path exists
  for any item; this is the one need where the zero-contract-change path fails
  by construction, and the proposal is right not to belabour it.
- **Mechanism matches the design**, item by item, with one exception. P2, P4,
  P6, P7, P8, P9, P10 and P11 name `extend` and each adds the mandatory members
  it claims (2, 1, 2, 3, 5, 6, 3, 4 — 26 in total, matching the Scope line);
  P3, P5 and P12 name `deprecate` and add no member. The exception is **P1**,
  which names `deprecate` for a change that adds no member at all: it is a
  decision-file and tooling change governing the rung-5 items of P2–P12. C6.
- **Cheaper rungs I found and the items missed.** P2's `RuleCounters` could have
  been a `NamedTuple` retyped in place — the shape P8 itself uses for
  `GroupRecord` — instead of a new member plus a deprecation. The conclusion is
  probably still the new member (a `NamedTuple` return breaks an implementer
  declaring `tuple[int, int]`), but the two items answer the same question two
  ways and only one of them argues it (C9). P5's `StormControlConfig.unit` is
  correctly taken at rung 3.
- **Renames and retypes with no deprecation procedure.** Four changes retype or
  reshape a released form with no period at all, while P1 explicitly keeps the
  period: `Router.get_telemetry`'s return (C14), `WifiRadioStats.tx_retries` /
  `tx_failed` (C17), `HTTPResult` becoming frozen (C24) and `HwConsole`'s two
  return narrowings (C29). Three of the four are avoidable — the deprecated
  reader can simply keep its released output under P1's own exemption class (a),
  which is what the item does for seven other readers. The fourth
  (`WifiRadioStats`) may genuinely have no form to keep; then it belongs in P1's
  rule set as a stated exception, not as an ad-hoc one in a family item.
- **Protocol method renames** are all named `extend`, correctly: every "new
  member, old name deprecated" pair (`get_rule_counter_values`,
  `read_telemetry`, `supported_channels`, `get_modes`, `read_rtpengine_stats`,
  `resolve`, `ping_stats`, `scan_ports`, `read_arp_table`, `snmp_*`,
  `start_sender_session`, `inject_event`, `read_memory_utilization`,
  `read_log_entries`, `read_url_rules`) adds a member to a structural protocol
  and rides a release that carries that `extend`.
- **`testoperations` callers of renamed members** are covered: P12's `_renamed`
  fallback accessors name `start_sender_session`, `start_receiver_session` and
  `inject_event`, and each family item states whether `testoperations` calls its
  changed members. I checked the index's operation list against the deprecated
  names and found no uncovered caller.
- **No new capability where an existing protocol owns the concern.** `Console`
  is the only candidate and it is a returned-object contract, composed by no
  archetype.

### 4. Correct home

Correct throughout. Contract vocabulary, records and members go to
`testprotocols`; the transition machinery — fallback accessors, pair readers,
released-text parsers, enum coercion — goes to `testoperations` (P1 C6, P12),
which is where logic belongs. Nothing proposed is a forwarder or test plumbing.
`testprotocols._compat` is an internal module carrying a re-export, not logic.

One consequence of that split is unaddressed: because the pair readers and
parsers of P2, P3 and P5 live only in `testoperations`, a consumer that depends
on `testprotocols` alone has no supported way to read a text/typed pair, and C1
forbids giving it one in the record. C5.

### 5. Overlap with capability protocols

Checked against the index's 100-odd protocols and the contract modules.

- **`FirewallRule.action` (P2) against `RuleAction`.** `models/sdwan_appliance.py`
  already owns `RuleAction` (`allow`, `deny`). The released `FirewallRule.action`
  takes `allow` / `deny` / `reject` / `log`, a strict superset, so a new enum is
  defensible — extending `RuleAction` would silently widen what an `L3Rule` or a
  `SwitchAclRule` may carry. The item does not say this, and the result is three
  action vocabularies plus `SecurityAction`. C8.
- **`DefaultAction` (P2) against `Zone` / `ZonePolicy`.** `ZonePolicy.action` is
  listed under "Not touched"; `Zone.default_input`, `default_forward` and
  `default_output` carry the same closed set and are listed nowhere. C10.
- **`Telemetry` (P4) against `DeviceManagement`.** `get_seconds_uptime()`,
  `get_load_avg()` and `get_memory_utilization()` already carry all three facts
  `Telemetry` holds, and P11 gives the third a typed record of its own
  (`MemoryUtilization`). The honest answer is probably that an API-managed
  appliance composes `Router` and not `DeviceManagement`, but the item must say
  so and say where the boundary runs. C15.
- **`PingResult` (P8) against `NetworkProbe`.** No overlap: `NetworkProbe` is a
  boolean reachability instrument with no statistics, deliberately so per its
  module docstring. Checked and clear.
- **`UrlRules` (P11), `RtpStats` / `MwiStatus` / `OfflineMessage` (P7),
  `ArpEntry` / `NmapResult` / `DnsRecord` (P8), `IperfProcess` (P10)** — no
  existing protocol or model carries any of them under another name.
- **`UplinkState.UNKNOWN` (P4)** is not an overlap but a widening of a published
  enum: `UplinkStatus.state` is typed `UplinkState` today and gains a value its
  appliance-side readers do not expect. C16.

### 6. Overlap with operations

No proposed operation duplicates an existing one. P12 keeps every operation name
and adds records and enums beside them; `coerce_enum` and the fallback accessors
are internal. The index's operation list shows no second implementation of the
pair reading, parsing or fallback that P12 centralises — today each operation
does without, which is the gap.

The reverse case question 6 asks about — a consumer reconstructing a model field
by field — is exactly what P12's `IperfSession`, `HomeVerification` /
`HomeDetails` and `FlowPair` replace: `start_iperf`, `verify_home` and
`saturate_link` return dicts that every caller unpacks by key. Right call.

### 7. One consumer, and why now

Every item is a **capability protocol** or **model** item, so the accepted
substitute for the second consumer is neutrality evidence across the domain's
reviewed-family list. Recorded per item:

- **P2, P3, P5** — substitute accepted: the recorded appliance and switch lists,
  checked above, with the thin cells admitted.
- **P6** — substitute accepted: a standards-first list with a per-concept
  mapping that is the most thorough in the document, and a known-gaps section
  that reads like a conformance note rather than a sales sheet. It is proposed,
  not ratified (C7), and its gaps belong in `GAPS.md` (C19).
- **P7, P11** — substitute accepted but thinner. `RtpStats` rests on one relay
  and holds only the two figures that implementer returns, which is the right
  conservatism; `UrlRules` rests on two of five appliance families with three
  unchecked.
- **P8, P9, P10** — substitute accepted under the recorded substrate-tool rule
  (`packet-injection-substrate-design.md` §2), not under a cross-vendor sweep.
- **P1, P12** — no device family is involved; the substitute does not apply, and
  the item's warrant is the rule set it serves.
- **Why now** is answered the same way for all twelve: question 9 exists, the
  released contracts predate it, and `GAPS.md` 2026-06-11 sets the trigger as
  touching a legacy capability for other reasons.

**Corpus impact.** The reference corpus (`main`, commit `fb9343e`) carries no
reference driver and no capability matrix for any capability this proposal
touches; the one archetype it holds material for is chartered, not verified. So
the count is zero for every item and the corpus is not the argument here. Two
consequences:

- The closing promise that "every new mandatory member is implemented by the
  reference driver implementations of the affected capabilities … before the
  `feat:` PR merges" cannot be met today, because no such driver exists. It
  should read as a forward condition on the archetypes that later reach these
  capabilities, with the plugin driver shape, verified writes and acknowledged
  calls that `docs/archetypes/README.md` requires.
- P12's claim to have searched "the reference driver implementations" for
  callers of `start_iperf`, `verify_home`, `saturate_link` and `iter_json_docs`
  has no corpus to have searched. Restate it as covering the released
  implementers. C32.

### 8. Every write verifiable

Every member that changes device state, item by item, with the read that shows
its effect.

- **P2** — no new write. `add_rule`, `remove_rule`, `flush_chain`,
  `set_default_policy`, `add_nat_rule` and `drop_connection` keep their released
  reads (`list_rules` / `get_rule`, `get_default_policy`, `list_nat_rules`,
  `get_connection`); the two new members are reads. Met.
- **P3** — no new write. The reshaped `L3Rule` feeds `L3Firewall.set_*_rules`,
  whose list reads exist. **Met with conditions**: `set_*_rules` is a list
  replace, and the appliance design records whole-list rewrite semantics on two
  of the five reviewed families; the failure outcome of a partial replace is not
  stated for the records this item reshapes. C12.
- **P4** — no write; `read_telemetry` is a read. Met.
- **P5** — no new write. `QosRule` feeds `SwitchQos.set_rules`, a list replace
  with the same unstated failure outcome. **Met with conditions**, C12.
- **P6** — `WifiBss.create_bss` / `set_security` / `set_acl_mode`,
  `WifiRadio.set_mode` / `set_bandwidth`, `WifiMesh.set_backhaul_band` and
  `WifiRadioWhiteBox.inject_radar_event` are released writes with released
  reads; the item adds the MFP read-back rule explicitly, which strengthens the
  verification (`get_bss_config` must report `REQUIRED`). `get_modes` and
  `supported_channels` are reads. Met.
- **P7** — no new write; the three new members are reads. Met.
- **P8** — `IpInterface.set_link_state` gains the read it lacked: the released
  `is_link_up(pattern)` reads the operational state through a flag-text pattern,
  and the new `is_link_admin_up` reads the administrative state the write sets.
  This is the item's best single change. `UpnpClient.create_upnp_rule` /
  `delete_upnp_rule` are read by the existing port-mapping list. Met.
- **P9** — `snmp_set` is read back by `snmp_get`; `set_date_time` by
  `read_date`. Met.
- **P10** — `inject_event` is a **lever** (a transient impairment leaves no
  state to read back), and the item names the confirming observation: the
  impairment seen on the path by the `testoperations` measurement around it, as
  for the released member. Met; state the observation in the member docstring
  rather than only in the proposal (C27).
- **P11** — no new write; the four new members are reads. Met.
- **P12** — operations only; the writes they drive are the contract members
  above.

### 9. Precise types

The rule set is the right one and the shapes are well chosen: `StrEnum` and
`IntEnum` make `E | str` and `ChannelWidth | int` a true widen-then-narrow (a
member compares equal to its string, so nothing converts at run time), new
members with no released form take the bare enum (C4), and new records are plain
frozen dataclasses. Where the item leaves a value open it says why, and the
reasons are good ones: `Connection.state`, `AppFlow.category`,
`DnsRecord.record_type`, `WifiStation.capability_flags`, SIP presence words and
methods, `EventLogEntry.timestamp` (a syslog date has no year).

Imprecise members the items add or change, each a condition:

- **`object` replacing `Any`, uncounted.** `SdwanPolicyManager.apply_policy`
  (P3), `TrafficShapingRule.match` (P4), `DhcpServer.provision_cpe`,
  `DHCPTraceData.dhcp_packet`, `DHCPV6TraceData.dhcpv6_packet` (P8),
  `Console.sendline -> object` (P11) and `iter_json_docs -> list[object]` (P12)
  all move from `Any` to `object`. Question 9 forbids both; P1's ratchet and
  exemption policy count only `Any`, so `object` becomes an unmeasured escape
  hatch in the same release that measures the other one. Several of these are
  defensible (an extensible TR-069-style parameter bag, a capture filter an
  implementer declares itself), which is precisely why they belong in the
  counted, per-line exemption list. C4.
- **`HTTPResult.status: int` with a `0` sentinel** (P8). `status` is a new field
  name; there is no released form to keep, so the sentinel is gratuitous and the
  "announced to become `None`" step unnecessary. `int | None` now. C23.
- **`HTTPResult` as a frozen dataclass that parses in its constructor** (P8)
  cannot be built without `__post_init__` or `object.__setattr__` — the
  conversion logic P1's C1 and C5 forbid in a record. C22.
- **`NtpClient.read_date() -> datetime | None`** (P9) does not say what `None`
  means. C26.
- **`OfflineMessage.stored_at`** (P7) does not say what is stored when the
  message store reports no time. C21.
- **`Telemetry.uptime_seconds: float`** (P4) is required on a protocol a
  cloud-managed archetype composes; `float | None` with the absence meaning
  stated. C13.
- **`list[GroupRecord]` against `MulticastGroupRecord`** (P8): the released
  alias is `list[tuple[...]]`, and `list` is invariant, so a caller passing
  `list[GroupRecord]` does not type-check even though a `NamedTuple` *is* the
  released tuple. The transition does not work as written. C25.

Existing imprecise members the items do not touch are listed under "Not touched
by this proposal", as question 9 asks, and are noted, not blocking. The list is
incomplete by at least `Zone.default_input` / `default_forward` /
`default_output` and `FirewallRule.application_category` (C10); fold the
remainder into GAPS 2026-06-11 rather than growing the list.

**Factual checks.** I verified the four claims a verdict turned on, against
published documentation:

- `warnings.deprecated` is Python 3.13 and `category=None` suppresses the
  runtime warning while keeping the static report (Python library docs,
  `warnings`). P1's C2 is correct as written.
- `typing_extensions` added `deprecated` in **4.5.0** (2023-02-14) and declared
  Python 3.12 support in **4.7.0** (4.6.3 only skipped a 3.12.0b1 test)
  — the typing_extensions changelog. P1's "4.6 is the first release that both
  provides `deprecated` and imports on Python 3.12" is wrong on both halves.
  C1.
- pyright's `reportDeprecated` is `"none"` in off, basic and standard and
  `"error"` in strict (pyright configuration docs). P1 is correct.
- mypy has an `explicit-any` error code enabled by `--disallow-any-explicit`, so
  the suppression marker is valid; but its `deprecated` error code is **not**
  enabled by default, including under strict (mypy error-code docs). "Both
  static checkers this repository runs report it" holds only once the workspace
  enables it. C2.

I did not independently verify P6's TR-181 and Data Elements claims about
per-radio retry counters; the P6 verdict does not hinge on them (it hinges on
the missing deprecation procedure, C17), and the claims are consistent with the
published data models as far as checked.

### Conditions

- C1 (P1): pin `typing_extensions>=4.7; python_version < "3.13"`, or justify 4.6
  against the changelog. `deprecated` landed in 4.5.0; Python 3.12 support was
  declared in 4.7.0.
- C2 (P1): add mypy's `deprecated` error code to the workspace configuration
  (`enable_error_code`), or say that pyright alone enforces C2 — strict mypy does
  not report it.
- C3 (P1): name the zero-dependency alternative and reject it on record or take
  it: `testprotocols._compat` importing `deprecated` under `try: … except
  ImportError:` with an identity fallback keeps `dependencies = []` on every
  supported Python.
- C4 (P1): extend the explicit-`Any` policy and the ratchet test to `object` in
  public signatures and fields. Count the occurrences, pin them per class with
  the same marker discipline, and record the count; the members are listed under
  question 9 above.
- C5 (P1): say how a consumer that depends on `testprotocols` alone reads a
  text/typed pair of P2, P3 or P5, given that C1 forbids the reader in the
  record and C6 puts it in `testoperations` — or state that pair reading is part
  of the published `testoperations` surface.
- C6 (P1): P1 adds no protocol member; name the rung it actually occupies (a
  decision-file change governing the rung-5 items of P2–P12) instead of
  `deprecate`, and record the four findings cited under *Need* in
  `docs/architecture/precise-types-design.md` so the reopening rests on tracked
  evidence rather than on a branch history.
- C7 (P6, P7, P8, P9, P10, P11): record each proposed reviewed-family list in a
  design document under `docs/architecture/`, one line of rationale per family;
  merging the `feat:` PR ratifies them. They are proposed, not ratified, today.
- C8 (P2): say why `RuleAction` (`models/sdwan_appliance.py`) is not extended
  with `REJECT` / `LOG` for `FirewallRule.action`, and why `DefaultAction` is a
  third action vocabulary beside it and `SecurityAction`.
- C9 (P2): say why `RuleCounters` is a new member rather than a `NamedTuple`
  retyped in place — the shape P8 uses for `GroupRecord`.
- C10 (P2): add `Zone.default_input` / `default_forward` / `default_output` and
  `FirewallRule.application_category` to "Not touched by this proposal", or
  retype them; fold the remainder into GAPS 2026-06-11 rather than growing the
  list.
- C11 (P2): the released `get_rule_counters` docstring says an unsupported
  driver raises `NotImplementedError`; the item says `NotSupportedError`. State
  which the new member requires.
- C12 (P3, P5): state the failure outcome of the list-replace writes the
  reshaped records feed — `L3Firewall.set_*_rules` and `SwitchQos.set_rules` —
  namely that a write failing at any step, rejected or not verified, leaves the
  as-found state.
- C13 (P4): cite GAPS 2026-06-11 "appliance health / online capability" and make
  `Telemetry.uptime_seconds` `float | None` with the absence meaning stated.
  `SdwanApplianceDevice` composes `routing: Router`, so a required
  `uptime_seconds` forces a host-shaped read on the archetype that entry kept it
  off; the entry's own design note gives `float | None`.
- C14 (P4): do not narrow `get_telemetry` to `Mapping[str, float]`. Keep the
  released `dict[str, Any]` under exemption class (a) until removal, as the item
  does for the other seven deprecated readers; the narrowing is a break with no
  deprecation period on a member that is being deprecated anyway.
- C15 (P4): name the overlap with `DeviceManagement.get_seconds_uptime` /
  `get_load_avg` / `get_memory_utilization` and with P11's `MemoryUtilization`,
  and say where the boundary runs.
- C16 (P4): `UplinkState.UNKNOWN` widens an enum `UplinkStatus.state` already
  publishes; list the appliance-side readers under *Affected*, or give
  `LinkStatus` / `LinkHealthReport` a state vocabulary of their own.
- C17 (P6): give the `WifiRadioStats.tx_retries` / `tx_failed` retype a
  deprecation procedure — the C3 twin shape, or rename-then-reclaim — or record
  it in P1's rule set as a stated no-period exception with the argument that no
  form can be kept. P1 keeps the period; a family item should not drop it alone.
- C18 (P6): the MFP rule changes what `get_bss_config` reads back for a driver
  that today reports `optional` under a WPA3-only mode, `OWE` or 6 GHz. Give it
  a *Changed* changelog entry with a migration line.
- C19 (P6): enter the listed known gaps in `GAPS.md` — a radio per 5 GHz
  sub-band, 80+80 / the two 320 MHz channelisations / automatic width, the
  security modes with no member, the wired mesh backhaul, the mesh root with no
  role on a cloud-managed family, and the Wi-Fi share of channel utilisation.
- C20 (P7): the `feat:` PR that retypes `verify_sip_message` cleans its
  docstring, which names a vendor tool's log path and a named testbed's log
  path in a public contract.
- C21 (P7): say what `OfflineMessage.stored_at` holds when the store reports no
  time, and which text form the parse accepts.
- C22 (P8): `HTTPResult` cannot be both a frozen dataclass and a constructor
  that parses the response text — that is the conversion logic C1 and C5 forbid
  in a record. Keep it a parsing class with precise read-only properties, or add
  a `from_response` classmethod and leave the released constructor deprecated.
- C23 (P8): type `HTTPResult.status` as `int | None` now. It is a new field with
  no released form, so the `0` sentinel and its later narrowing are avoidable.
- C24 (P8): freezing `HTTPResult` breaks attribute assignment and non-frozen
  subclasses with no deprecation period; record it under *Breaking for driver
  authors* with a migration line.
- C25 (P8): `MulticastGroupRecord` is `list[tuple[...]]` and `list` is
  invariant, so `list[GroupRecord]` does not satisfy `send_mldv2_report`.
  Widen the parameter so the typed form is passable, and state the cost to an
  implementer that declares `list`.
- C26 (P9): record the SNMP substrate survey in a design document, citing the
  recorded substrate-tool rule (`packet-injection-substrate-design.md` §2) that
  permits a single-substrate wrapper, with RFC 3416 / RFC 2578 as the
  vendor-free reference and a second independent client family named; say what
  `read_date() -> datetime | None` means by `None`; enter the untyped varbind
  return in `GAPS.md`.
- C27 (P10): record the traffic / impairment / QoE substrate survey the same
  way, and state `inject_event`'s confirming observation in the member docstring,
  not only in the proposal.
- C28 (P11): `ContentFiltering.get_url_rules` returns `tuple[list[str],
  list[str]]`, not a dict. Correct the Need; the `UrlRules` record is still the
  right answer, since question 9 forbids a bare tuple.
- C29 (P11): the `HwConsole.get_console` and `get_interactive_consoles`
  narrowings break a console lacking the `Console` members, with no deprecation
  period; record them under *Breaking for driver authors* with a migration line,
  or keep the released `Any` under exemption class (a).
- C30 (P11): record in the design document that `Console` is a returned-object
  contract and not a capability — composed by no archetype, counted in no
  capability inventory — so the capability-only-archetypes rule is untouched.
- C31 (P12): `start_iperf`'s new required `host=` breaks every caller; record it
  under *Consumer action* with a migration line, not only under *Changed*.
- C32 (P12): restate the caller search. The reference corpus holds no reference
  driver for these capabilities, so the search covers the released implementers
  only; and the closing promise that every new mandatory member is implemented
  by a reference driver before the `feat:` PR merges should read as a forward
  condition on the archetypes that later reach these capabilities.

---

## Review response (testprotocols review team, 2026-10-05)

| Item | Decision | Reason |
| --- | --- | --- |
| P1 | accept with conditions | The zero-dependency marker, the `object` ratchet and the recorded no-period exception answer round one; the exempt inventory misses two released lines and the checker floor is below the versions the enabled error codes need. |
| P2 | accept with conditions | The three-enum answer, the `RuleCounters` argument and the `NotSupportedError` statement all land; GAPS 2026-06-11's own reconciliations for these fields are still unsettled. |
| P3 | accept | Twin fields, announced narrowings and the stated as-found failure outcome for the list replaces. |
| P4 | accept with conditions | `uptime_seconds: float \| None`, the kept `dict[str, Any]`, the `DeviceManagement` boundary and the `UplinkState` readers are all now recorded; the exhaustiveness claim rests on an error code the workspace does not enable. |
| P5 | accept | `QosClassifier` is well evidenced, `unit` is correctly rung 3, and `set_rules` states its failure outcome. |
| P6 | accept with conditions | The no-period retype is now P1's stated exception with both conditions, the MFP change has a migration line and the gaps are entered; a recorded deferral of `WifiBssConfig.security_mode` is lifted without citing it, and the family list is not yet ratified. |
| P7 | accept with conditions | Records, `PhoneState` and the cleaned docstring are right; the `since` narrowing drops the period that the parallel `HwConsole` case now keeps. |
| P8 | accept with conditions | `HTTPResult`, `status` and the `Sequence` widening all resolve; the three new keyword-only parameters break implementer conformance with no period and no changelog entry. |
| P9 | accept with conditions | The substrate survey, the second independent client and the defined `None` answer round one; the survey is recorded only on the branch. |
| P10 | accept with conditions | The survey and the lever's observation land; `MeasurementSpec.completion` is on the recorded defer list, and the survey is not yet ratified. |
| P11 | accept with conditions | The Need is corrected, the `HwConsole` returns keep their released form and `Console`'s class is recorded; the family list is not yet ratified. |
| P12 | accept with conditions | The transition layer, the `host=` migration line and the restated caller search are right; one public `object` alias in the package is outside the pinned inventory. |

This is round two. Round one's C1–C32 are each answered in the document's
resolution table; I checked every row against `PUBLIC_MAIN` and against the
published documentation where a claim could be verified. Twenty-nine rows are
resolved outright. The conditions below are the three that are not yet fully
discharged (C1/C4 of round one, on inventory completeness; C7, which only the
`feat:` PR can discharge) and three findings of this round, each a fixable gap
in a design that is otherwise sound.

### 0. Neutrality

Met. No organisation, customer, site, hostname, address, person or ticket
identifier appears in the document, and no IP literal appears at all. Vendor
and tool names stay inside **Neutrality evidence**; the Round 2 resolution
table adds none. The Use case field is `—` (maintainer-originated), which the
rule allows.

Two judgement calls carried from round one, unchanged: the Python toolchain
names in P1 (`typing_extensions`, `warnings`, mypy, pyright) are the
repository's own build chain, which `CONTRIBUTING.md` names in the open, not
the device families the contracts abstract; and released public symbols that
embed a tool name (`NmapScanner.nmap`, `HttpClient.curl`,
`iwlist_supported_channels`, …) are the contract's own API.

One new one: the round-one response block appended at the end of the document
carries vendor names outside a Neutrality evidence heading. That block is
appended verbatim as `docs/proposals/README.md` ("The review response")
directs, and the names are the review team's own, so it is not this document's
violation. A formatting nit, not a condition: the README asks for the block to
follow a `---` rule, and there is none before `## Review response`.

The neutrality defect in the *existing* `SipServer.verify_sip_message`
docstring — it names a product log path and a named testbed log path in a
public contract — is confirmed in `PUBLIC_MAIN`
(`testprotocols/sip_server.py`), and P7 now states that the retyped member's
docstring drops both. Round-one C20 resolved.

### 1. Recorded decisions

The reopening in P1 is argued as question 1 asks, and round two strengthens it:
the four findings against runtime transition code in `testprotocols` are now
recorded in a tracked design document rather than cited to a branch history,
and the deprecation period itself (one MINOR and six months) and the
operations-honour-the-period rule are kept. The two GAPS 2026-06-11 entries
round one asked for are now cited — "appliance health / online capability" in
P4, with `Telemetry.uptime_seconds` taking that entry's own `float | None`
shape, and "migrate legacy bare-`str` value fields" in P4's Need and in "Not
touched". `SdwanApplianceDevice` composes `routing: Router` and only
`CpeDevice` composes `DeviceManagement`, as P4 states.

What the proposal still does not account for is the rest of the
"migrate legacy bare-`str` value fields" entry, the single recorded entry this
proposal most directly executes:

- Its *vocabulary reconciliations to settle* record that a released consumer
  emits an **undocumented `"alert"`** for `FirewallRule.action`, and that "a
  strict enum must include `ALERT` or [the consumer] must change to `LOG`".
  P2's `FirewallRuleAction` has no `ALERT` and the document does not say which
  way the reconciliation goes. During the period `E | str` carries the value;
  at the narrowing it fails. Settle it now (C3).
- The same list records the **gating (A)-vs-(B) decision** — annotation plus
  checker only, or `__post_init__` coercion — as the thing to "decide before
  writing code". P1's C4 and C5 decide it as (A), consistently with
  `models/sdwan_appliance.py`; the document should say that it is deciding that
  recorded question (C3).
- The same list defers `WifiBssConfig.security_mode` and
  `MeasurementSpec.completion` explicitly: "vendor-divergent / undocumented
  fields … not enum-safe … defer until a test needs them". P6 and P10 retype
  both. The lift is defensible — the entry's own trigger ("touching a given
  legacy capability for other reasons") is met, `E | str` leaves every
  unmatched value readable, and P6 records the modes with no member as gaps —
  but it is a recorded deferral, and question 1 wants it argued rather than
  passed over (C3).
- One line of that entry *supports* the proposal and is worth citing rather
  than re-deriving: "**Do not unify the action vocabularies**:
  `FirewallRule.action`, `Zone`/`ZonePolicy.action` and appliance `RuleAction`
  are three distinct sets — keep separate enums." That is C8's answer, already
  on the record.

Nothing in `docs/architecture/` is contradicted. SPLITS and LEVELS stay
untouched by every item.

### 2. Vendor and tool neutrality

Unchanged from round one in substance. P2 and P3 run against the recorded
SD-WAN appliance list and P5 against the recorded L2 switch list; all three
checks hold, with the thin cells (appliance port grammars, two unchecked
event-time formats, Aruba / Omada / UniFi classifier support, three unchecked
families for `UrlRules`) admitted in the text rather than papered over.

P6–P11 propose lists where none was recorded, which is the right procedure.
Round two records them in `docs/architecture/precise-types-families.md` with
one line of rationale per family, and P9 and P10 now cite the recorded
substrate-tool rule (`packet-injection-substrate-design.md` §2) with a
vendor-free reference (RFC 3416 / RFC 2578; RFC 6349 / 7679 / 7680 / 3393 and
the HTML load events) and, for P9, a second independent client family. That
answers round-one C26 and C27 on substance.

They remain **proposed, not ratified**: the families document lives on
`feat/precise-types`, and `PUBLIC_MAIN` has no such file. Ratifying it is what
merging the `feat:` PR does, so round-one C7 is carried forward as C6 rather
than closed.

### 3. Placement ladder walked

The member counts tally: P2 2, P4 1, P6 2, P7 3, P8 5, P9 6, P10 3, P11 4 —
26 mandatory members, matching the Scope line and the MINOR claim. Rung 5
before rung 6 is respected; `Console` is the only new `Protocol` and is
recorded as a returned-object contract composed by no archetype (C30).
`testoperations` callers of every renamed member are covered by P12's fallback
accessors, and each family item states whether `testoperations` calls its
changed members.

Round one found four retypes with no deprecation procedure. Three are now
fixed by keeping the released form: `Router.get_telemetry` keeps
`dict[str, Any]` under exemption class (a) (C14), `HTTPResult` is no longer
frozen (C22/C24), and `HwConsole.get_console` / `get_interactive_consoles`
keep their released `Any` with the narrowing announced (C29). The fourth,
`WifiRadioStats.tx_retries` / `tx_failed`, is now P1's stated no-period
exception with both conditions spelled out, and the argument holds: the
released fields are *required*, no reviewed family reports the value, and
neither a twin nor rename-then-reclaim can keep a required-and-unfillable
field usable (C17).

Two signature changes still take no period, and both are the same class as the
four above:

- **P7**, `verify_sip_message(since: Any = None)` → `datetime | None`. Round
  two notes that an implementer declaring `Any` still conforms, but one
  declaring a narrower type does not, and a caller passing the "timestamp or
  marker" the released docstring invites stops type-checking. This is the
  `HwConsole` case the same document now handles by keeping the released `Any`
  and announcing the narrowing. C4.
- **P8**, the new keyword-only parameters on `HttpClient.curl`, `http_get` and
  `NmapScanner.nmap`. The item is right that "a declaration without them is
  reported by the checkers" — which is to say every released implementer stops
  conforming on upgrade, with no period. The ladder's `extend` pays for that
  with a *Breaking for driver authors* entry and a migration line; the Scope
  line promises one only for the 26 new members. C5.

No cheaper rung was missed. The `RuleCounters`-versus-`GroupRecord` asymmetry
round one flagged is now argued on both sides (C9), and the argument is
correct: narrowing a released `tuple[int, int]` return to a `NamedTuple`
subtype breaks an implementer that declares the tuple, while a `NamedTuple`
*passed in* is the released tuple.

### 4. Correct home

Correct throughout, and round two closes the one consequence round one raised:
pair reading is published `testoperations` surface (`testoperations.pairs`,
with `__all__`), so a consumer that depends on `testprotocols` alone has a
supported way to read a text/typed pair without putting conversion code in the
record (round-one C5). Each reader and parser is scheduled for removal with the
text field it reads, which is the right lifetime.

### 5. Overlap with capability protocols

Every overlap round one named is answered in the document: `RuleAction` (C8),
`Zone`'s policy fields (C10 — confirmed present in `models/firewall.py` as
`default_input` / `default_forward` / `default_output`), the
`DeviceManagement` boundary (C15) and the `UplinkState.UNKNOWN` widening with
its appliance-side readers (C16). I re-checked `UplinkState` in
`models/sdwan_appliance.py`: the released members are `UP`, `DEGRADED`,
`DOWN`, `STANDBY`, `NOT_CONNECTED`, so `UNKNOWN` is a genuine addition and the
"a released driver that type-checks does not produce one" argument holds.

No new overlap. `PingResult` against `NetworkProbe`, `UrlRules`, the voice
records, the host-tool records and `IperfProcess` are each the only carrier of
their fact.

### 6. Overlap with operations

No duplication. P12 keeps every operation name, and the records it introduces
(`IperfSession`, `HomeVerification` / `HomeDetails`, `FlowPair`) replace exactly
the dict-unpacking question 6 asks about — `verify_home` returns
`dict[str, object]` and `start_iperf` a four-key dict in `PUBLIC_MAIN` today.
`start_iperf`'s repair is confirmed against the released source: the operation
calls `start_receiver` / `start_sender`, which no protocol declares, so it
cannot work with any conforming driver, and it never received the receiver's
address. The required `host=` is a real fix and now carries a *Consumer action*
entry with a migration line (C31).

### 7. One consumer, and why now

Unchanged and accepted: every item is a capability-protocol or model item, so
neutrality evidence across the domain's reviewed-family list is the substitute,
and it is supplied per item (recorded lists for P2 / P3 / P5; proposed lists
for P6–P11; the substrate-tool rule for P8 / P9 / P10). P1 and P12 involve no
device family, and their warrant is the rule set they serve. "Why now" is the
GAPS 2026-06-11 trigger plus the existence of question 9.

**Corpus impact.** The reference corpus (`main`, commit `fb9343e`) holds no
reference driver and no capability matrix for any capability this proposal
touches, so the count is zero for every item and the corpus is not the argument
here. Round two restates the caller search as covering the released
implementers only, and the closing section as a forward condition on the
archetypes that later reach these capabilities, carrying the plugin driver
shape, verified writes and acknowledged calls `docs/archetypes/README.md`
requires (C32). Both restatements are accurate; the forward condition stands as
written and needs no condition of its own.

### 8. Every write verifiable

Re-checked per item against the contract modules. P2, P4, P6, P7, P9, P10 and
P11 are as in round one: every released write keeps its read, the new members
are reads, `set_link_state` gains the administrative read it lacked
(`is_link_admin_up`, distinct from the released operational `is_link_up`),
`snmp_set` reads back through `snmp_get` and `set_date_time` through
`read_date`.

The two **met with conditions** rows of round one are now met: P3's
`L3Firewall.set_outbound_rules` / `set_inbound_rules` / `set_vpn_rules` and
P5's `SwitchQos.set_rules` state that a write failing at any step, rejected or
not verified, leaves the as-found state (C12). P10's `inject_event` is a lever
and its confirming observation moves into the member docstring (C27).

One observation, not a condition: `ContentFiltering.set_url_rules` replaces two
pattern lists, and a reviewed appliance family realises that in more than one
device step, so it wants the same failure-outcome sentence. P11 changes only
the read side (`read_url_rules`), so the rule does not bite here; state it when
the write is next touched.

### 9. Precise types

The rule set is right, and round two fixes the two places it was
self-contradictory. `HTTPResult` stays the released parsing class with
read-only `status -> int | None` and `body -> str` computed from the released
attributes — no conversion in a record, no `0` sentinel, no freezing, which
answers C22, C23 and C24 together and is consistent with C1 and C5.
`send_mldv2_report` now takes `Sequence[tuple[list[McastSource], McastGroup,
MulticastGroupRecordType]]`; since `GroupRecord` is a `NamedTuple` over those
field types and `Sequence` is covariant, `list[GroupRecord]` passes, and the
cost to an implementer declaring the released invariant `list` is recorded
(C25). `OfflineMessage.stored_at` and `NtpClient.read_date` both define their
`None` (C21, C26). `Telemetry.uptime_seconds` is `float | None` (C13).

The `object`-for-`Any` substitution is now counted, which was round one's C4,
and the per-class pinning is the right mechanism. The inventory is two lines
short of what the stated ceiling needs, both verifiable in `PUBLIC_MAIN`:

- `testprotocols/src/testprotocols/devices/__init__.py:26` —
  `frozenset(cast("Any", protocol).__protocol_attrs__)`. This is an explicit
  `Any` in released source and falls in neither exempt class, both of which are
  defined as "released signatures only". Whether mypy's
  `--disallow-any-explicit` reaches a `cast` is not settled by its
  documentation ("explicit `Any` in type positions such as type annotations and
  generic type parameters"), but the ratchet test is the stated second line of
  defence and counts the package's non-exempt `Any` against a ceiling of 0, so
  this line has to be removed (`typing.get_protocol_members` on 3.13 with a
  3.12 fallback is the obvious route, and the comment there already anticipates
  it) or given a third exempt class with its own marker and pinned count.
- `testoperations/src/testoperations/throughput.py:118` —
  `JsonObj = Mapping[str, object]`, a public module-level type alias, which is
  precisely one of the three positions P1 says it counts `object` in. It is not
  among the six pinned `testoperations` lines, and P12 names only
  `iter_json_docs`. If `JsonValue` subsumes it, say so; otherwise pin it.

Both are C1.

The exemption counts I could check are right: the nine class-(a) `Any` lines
are exactly the nine released members named, and the sixteen class-(b) lines
are `flash_via_bootloader`, `start_tcpdump`, the twelve TR-069 RPCs and the two
`HwConsole` returns, one marker per `def` line. Every other released `Any` in
either package is retyped by a named item; I enumerated them against the source
and found no third category beyond the two lines above.

Existing imprecise members the items do not touch are listed under "Not touched
by this proposal" and the remainder folded into GAPS 2026-06-11 (C10). Noted,
not blocking.

**Factual checks.** Verified against published documentation, since P1's
verdict turns on them:

- `warnings.deprecated` is Python 3.13, and `category=None` suppresses the
  runtime warning while keeping the static diagnostic (Python library docs,
  `warnings`). The three-step `_compat` scheme — `typing_extensions` under
  `TYPE_CHECKING` (both checkers resolve it from bundled typeshed stubs),
  `warnings.deprecated` at run time on 3.13 and later, an identity marker on
  3.12 — keeps `dependencies = []` on every supported version and is the
  alternative round one's C3 named. Taken; round one's C1 is moot with it.
- mypy's `deprecated` error code: introduced in **mypy 1.14** ("Support for
  `@deprecated` decorator (PEP 702)"; the same release made the note an error,
  disabled by default), enabled by `--enable-error-code deprecated` (mypy
  changelog; optional error codes documentation). mypy's `exhaustive-match`:
  introduced in **mypy 1.17**. The workspace dev group in
  `PUBLIC_MAIN/pyproject.toml` pins `mypy>=1.10`, and an unknown code in
  `enable_error_code` makes mypy fail outright, so the floor has to move with
  the policy; and P4's Affected claims `exhaustive-match` is enabled by this
  workspace, while P1's Placement lists only the explicit-`Any` rule and the
  `deprecated` code. C2.
- `--disallow-any-explicit` exists and enables the `explicit-any` error code,
  so the suppression marker P1 uses is valid (mypy command-line documentation).
- pyright reports `reportDeprecated` as an error in strict mode only (round
  one's check, unchanged).

I did not re-verify P6's TR-181 and Wi-Fi Data Elements claims; the P6 verdict
does not hinge on them, and they remain consistent with the published data
models as far as checked.

### Conditions

- C1 (P1, P12): complete the `Any` / `object` inventory the ratchet pins.
  `cast("Any", protocol)` in `testprotocols/devices/__init__.py` is a
  non-exempt explicit `Any` in released source, and
  `JsonObj = Mapping[str, object]` in `testoperations.throughput` is an
  `object` in a public module-level type alias — one of the positions P1 says
  it counts. Remove each, or add a third exempt class with its marker and its
  pinned count, and restate the per-package counts.
- C2 (P1, P4): raise the workspace's mypy floor to the version that provides
  the error codes the policy enables. `deprecated` is mypy 1.14 and
  `exhaustive-match` is mypy 1.17, while the dev group pins `mypy>=1.10`; an
  unknown code in `enable_error_code` fails the run. Then either add
  `exhaustive-match` to the checker configuration P1's Placement lists, or drop
  P4's claim that the workspace enables it.
- C3 (P2, P6, P10): settle the recorded reconciliations of GAPS 2026-06-11,
  citing the entry where this proposal lifts it. Say which way the undocumented
  `"alert"` action goes (an `ALERT` member, or the consumer moves to `LOG`
  before the narrowing); record that P1's C4/C5 settle that entry's gating
  (A)-vs-(B) decision as (A), annotation and checker only; and argue the lift
  of its explicit deferral of `WifiBssConfig.security_mode` (P6) and
  `MeasurementSpec.completion` (P10) as "not enum-safe … defer until a test
  needs them". Cite its "do not unify the action vocabularies" line in P2,
  which already records the three-enum answer.
- C4 (P7): `verify_sip_message(since: Any)` → `datetime | None` narrows a
  released parameter with no deprecation period. Keep the released `Any` under
  exemption class (a) and announce the narrowing (shape 6), as the document now
  does for `HwConsole.get_console`, or record the break under *Breaking for
  driver authors* and *Consumer action* with a migration line.
- C5 (P8): the new keyword-only parameters on `HttpClient.curl`, `http_get` and
  `NmapScanner.nmap` make every released implementer's declaration
  non-conforming on upgrade. Record them under *Breaking for driver authors*
  with a migration line (as round one's C25 does for `send_mldv2_report`), or
  carry the typed flags on new member names so the released signatures survive
  the period.
- C6 (P6, P7, P8, P9, P10, P11): the reviewed-family lists and substrate
  surveys of `docs/architecture/precise-types-families.md` live on
  `feat/precise-types` and are proposed, not ratified. Merging the `feat:` PR,
  which takes the decision-file review, ratifies them; until then each item's
  evidence stands on a proposed list. (Round one's C7, carried.)
