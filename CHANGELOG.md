# Changelog

All notable changes to `testprotocols` and `testoperations` are recorded
here, in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) layout.
The two packages release in lockstep, so one section per version lists
both. Entries are written by the PR that makes the change, under
`[Unreleased]`, in the format CONTRIBUTING.md states (kind, merged symbol
path, one-line behaviour, proposal path and item, PR number, *proposed as*
where reshaped). A release PR renames `[Unreleased]` to the version and
adds a fresh empty `[Unreleased]` above it.

Sections 0.9.0 to 0.12.1 were reconstructed after the fact from the
release commits and PR pages. Versions before 0.9.0 are recorded only in
their tags and PR history.

## [Unreleased]

### testprotocols

#### Added

- **module** `testprotocols.deprecation` — `renamed_attribute` (for a module
  `__getattr__` that resolves a renamed symbol's old name, with a
  `DeprecationWarning`) and `warn_renamed` (for a renamed protocol member's
  old-name method that delegates to the new one); typed `object`, not `Any`.
  `tests/test_typing_ratchet.py` caps the explicit `Any` per package
  (testprotocols 40, testoperations 7); a change may lower a ceiling, never
  raise it. Migration: none. Design `docs/architecture/precise-types-design.md`; no
  proposal (contract infrastructure); PR pending.
- **function and constant** `testprotocols.deprecation:coerce_enum` and
  `MODEL_FRAMES` — `coerce_enum` normalises an `Enum | str` argument or field
  to the enum member, warning (`DeprecationWarning`) on a plain string naming
  a member and raising `ValueError` listing the legal values on any other; the
  helper behind the `E | str` deprecation shapes. Its keyword
  `skip_file_prefixes` is passed to `warnings.warn`, so a model's
  `__post_init__` or `__setattr__` can point the warning at the caller's
  construction site; `MODEL_FRAMES` is that value for the models of this
  package. Migration: none. Design `docs/architecture/precise-types-design.md`
  (shapes 1 and 3); PR pending.
- **function** `testprotocols.deprecation:coerce_int` — returns an `int` unchanged,
  converts a string of optionally signed decimal digits (`"443"`, `"-1"`, `"+5"`) with a `DeprecationWarning` (the helper for a
  released `str` parameter that is really a number), and raises `ValueError` for text
  that is not a decimal integer and `TypeError` for a `bool`, `float` or other type.
  Migration: none. Design `docs/architecture/precise-types-design.md` (shape 1i);
  PR pending.
- **model and functions** `testprotocols.models:PortRange` (`first`, `last`,
  inclusive, `1 <= first <= last <= 65535` else `ValueError`, a non-int
  `TypeError`; `PortRange.single(port)`), `parse_port_ranges`,
  `format_port_ranges` and `port_tuple` — the typed L4 port range, the pure
  converters for the released port text (`"any"` is `()`; `"80"`, `"80-90"`,
  comma lists; `ValueError` otherwise), and the check a typed port field
  applies (an iterable of `PortRange` becomes a tuple; a string, bytes, a
  non-iterable or an item that is not a `PortRange` raises `TypeError`).
  Migration: none. Design `docs/architecture/precise-types-design.md`
  (shape 4(ii)); PR pending.
- **enum** `testprotocols.models:DefaultAction` (`ACCEPT`, `DROP`, `REJECT`) —
  what a chain, zone or zone pair does with traffic no rule decides; a driver
  coerces a released plain string with `coerce_enum(DefaultAction, …)`.
  Migration: none. Design `docs/architecture/precise-types-design.md`;
  PR pending.
- **models and functions** `testprotocols.models:TrafficMatch`
  (`ApplicationMatch(name)`, `CategoryMatch(category: ApplicationCategory)`
  (a plain string is converted, an unknown one raises `ValueError`),
  `HostMatch(host)`, `PortMatch(ports: tuple[PortRange, ...])` (checked as a
  typed port field), `IpRangeMatch(cidr)` (a prefix or a `first-last` range);
  frozen; an empty name, host or range, or no port, raises `ValueError`),
  `traffic_match(match_type, value)` and `match_fields(match)` — what an L7 or
  shaping rule selects, as a tagged union, and the pure converters to and from
  the released `(L7MatchType, value)` pair (`"any"` for a port is every port,
  `1-65535`; `traffic_match` raises `ValueError` for a value that names no
  match: empty, an unknown category, a port text naming no port number).
  Migration: none. Design `docs/architecture/precise-types-design.md`
  (shape 4(ii)); PR pending.
- **internal module** `testprotocols.models._sync` (`SyncedField`,
  `SyncedFields`, `settle`, `assign`) — keeps a deprecated text field, or
  several fields spelling one value, in agreement with its typed successor:
  at construction the typed side fills the text and the text alone warns;
  through `dataclasses.replace` and assignment the side that changed wins;
  malformed text raises before it warns; a hidden provenance field, which must
  be the model's last field, tells a changed side from an unchanged one; a
  subclass of a synced model that is not itself decorated with `@dataclass`
  raises `TypeError` naming the class (it would silently drop its own fields). Not
  public API; listed because later retypes build on it. Migration: none.
  Design `docs/architecture/precise-types-design.md`; PR pending.
- **enums** `testprotocols.models:Chain` (`INPUT`, `OUTPUT`, `FORWARD`),
  `FirewallRuleAction` (`ALLOW`, `DENY`, `REJECT`, `LOG`), `NatMode` (`SNAT`,
  `DNAT`, `ONE_TO_ONE`), `PortMappingProtocol` (`TCP`, `UDP`, `TCP_UDP`) and the
  open `ConnState` (the nine TCP states, `UNREPLIED`, `ASSURED` and `OTHER`; its
  values are the released upper-case words, so `conn.state == "ESTABLISHED"` is
  true).
  Migration: none. Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.
- **field** `testprotocols.models:Connection.state_raw` — the device's own state
  word, held only while `state` is `ConnState.OTHER`; the pair agrees after
  construction, `replace` and assignment, and the side that changed wins (a raw
  word with a named state raises `ValueError`). Migration: none. Same design
  section; PR pending.
- **function** `testprotocols.deprecation:coerce_open_enum` — for an open enum:
  a member is returned as is, a string naming a member converts with a
  `DeprecationWarning`, and any other string gives `(other, word)` without a
  warning (an exact match: `"close"` is not `"CLOSE"`). Migration: none.
  Design `docs/architecture/precise-types-design.md` (shape 3o); PR pending.
- **internal module** `testprotocols.models._open_enum:OpenEnumPair` — an
  open-enum field and its raw-word companion as a `_sync` pair, driven by
  `settle` (so it also serves a frozen record, through `__post_init__`) and
  `assign`, with the same hidden provenance field. Not public API; listed because
  later retypes build on it. Migration: none. Design
  `docs/architecture/precise-types-design.md` (shape 3o); PR pending.

- **model** `testprotocols.models:RuleCounters` (`packets`, `bytes`; frozen;
  a negative number raises `ValueError`, a non-int, bool included, `TypeError`) —
  what a rule has matched since it was added. Migration: none. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **fields** `testprotocols.models:FirewallRule.dst_ports`, `NatRule.dst_ports`
  and `NatRule.translated_ports` — `tuple[PortRange, ...]`, the empty tuple
  meaning no port restriction, kept in agreement with the deprecated text
  fields `dst_port` / `translated_port` (typed fills text; text alone warns and
  fills typed; disagreeing raises `ValueError`; the side that changed wins under
  `replace` and assignment). Migration: pass `PortRange` tuples. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **fields** `testprotocols.models:L3Rule.src_ports` and `dst_ports` —
  `tuple[PortRange, ...]`, the empty tuple meaning any port, kept in agreement
  with the deprecated text fields `src_port` / `dst_port` (typed fills text;
  text alone warns and fills typed; disagreeing raises `ValueError`; the side
  that changed wins under `replace` and assignment). Migration: pass `PortRange`
  tuples. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **field** `testprotocols.models:SecurityEvent.timestamp` — `datetime | None`
  (`None`: the product reports no time), kept in agreement with the deprecated
  ISO-8601 text `ts` by the same rule. A timezone-naive value stays naive; a
  text that parses is kept as given (`"…Z"` reads back `"…Z"`), a typed value
  writes `datetime.isoformat()`. Migration: pass `timestamp`. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **internal option** `testprotocols.models._sync:SyncedField.keep_text` — a text
  that parses to the agreed value stays exactly as given instead of being
  rewritten to the canonical form (for a text with several equal spellings, such
  as an ISO-8601 `Z` or `+00:00`); used by `SecurityEvent.ts`. Not public API.
  Migration: none. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.

#### Breaking for driver authors

- **protocol members** `testprotocols.packet_filter:PacketFilter.get_rule_counter_values(chain, name) -> RuleCounters`
  and `testprotocols.nat:Nat.get_nat_rule_counter_values(name) -> RuleCounters`
  (so also `Firewall`, which inherits `PacketFilter`) — new mandatory members,
  taking the parameters of the old counter members. Migration: implement them
  and make `get_rule_counters` / `get_nat_rule_counters` warn with
  `warn_renamed` and delegate. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.

#### Changed

- **protocol members** `testprotocols.packet_filter:PacketFilter` (every `chain`
  parameter; `set_default_policy(policy)`), `testprotocols.nat:Nat.list_nat_rules(mode)`
  and `testprotocols.conntrack:Conntrack` (`protocol` on `list_connections`,
  `count_connections`, `get_connection`, `drop_connection`; `state` on the two
  filters) — now annotated `Chain | str`, `DefaultAction | str`,
  `NatMode | str | None`, `RuleProtocol | str` and `ConnState | str | None`. A
  driver coerces each once at its boundary with `coerce_enum(…, what=…)`; the
  `state` filter uses `coerce_open_enum`, and a word that names no member
  filters on `Connection.state_raw`. An unknown chain, policy, mode or
  protocol raises `ValueError`; a conntrack `protocol` of `any` is refused,
  because no flow has it. Migration: pass the members; a driver adds the
  annotations and the coercion. Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.
- **models** `testprotocols.models:FirewallRule` (`action`, `protocol`),
  `NatRule` (`mode`, `protocol`), `PortMapping` (`protocol`) and `Connection`
  (`protocol`, `state`) — each field is now `Enum | str` and always holds the
  enum after construction, `replace` and assignment; the enums are
  `FirewallRuleAction`, `RuleProtocol`, `NatMode`, `PortMappingProtocol` and
  `ConnState`. `NatRule.protocol` defaults to `RuleProtocol.ANY`. An unknown
  string raises `ValueError`, except `Connection.state`: the set is open, so an
  unknown word becomes `ConnState.OTHER` plus `state_raw`, without a warning. A
  plain string naming a `ConnState` warns and converts. The `ConnState` values
  are the released upper-case words (`"ESTABLISHED"`, `"SYN_SENT"`, …,
  `"OTHER"`), so no reading idiom changes: `conn.state == "ESTABLISHED"` holds.
  `Connection.protocol` refuses `RuleProtocol.ANY` with `ValueError`, as its
  docstring says (a flow has one transport). Migration: pass the members. Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.

- **models** `testprotocols.models:FirewallRule.dst_port` — now defaults to
  `"any"`, so a rule can be built from `dst_ports` alone (released: required).
  `NatRule.dst_port` and `translated_port` read `""` for no port, as released,
  including after `"any"` was given (it is accepted and reads back `""`). A
  malformed port text (for example `"http"`, or `""` on `FirewallRule`) raises
  `ValueError`, and a non-text `dst_port` or a non-`PortRange` `dst_ports`
  raises `TypeError`; no value the released documentation allowed raises.
  A text is canonical (`"22, 80"` reads `"22,80"`).
  Accepted port forms are `"any"` (and `""` on `NatRule`), numbers, `a-b` ranges and
  comma lists; colon or slash forms (`"80:90"`, `"tcp/80"`) and a trailing comma
  raise `ValueError`, so a driver that reads them back must convert them.
  Static only, no runtime change: unpacking a loosely typed dict (for example
  `FirewallRule(**dict[str, str])`) into `FirewallRule` or `NatRule` now fails
  type-checking, because `dst_ports` and the private `_ports_seen` are keyword
  parameters (`_ports_seen` shows in signatures and error text); type the dict or
  pass the fields explicitly. Listed in the design doc's "Effective now". Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **models** `testprotocols.models:L3Rule` ports and `SecurityEvent` timestamp —
  `L3Rule.src_port` / `dst_port` now raise `ValueError` for malformed text
  (`""`, `"http"`, `"80:90"`, a trailing comma; the released contract allowed
  `"any"`, a number, `a-b` or a comma list) and `TypeError` for a non-text
  value; text normalises to its canonical form (`"22, 80"` reads `"22,80"`).
  `SecurityEvent.ts` now raises `ValueError` for text that
  `datetime.fromisoformat` does not parse (released: any string) and `TypeError`
  for a non-text value; it defaults to `""` (no time), so the fields after it
  take a required-argument placeholder and omitting one still raises
  `TypeError`. Static only, no runtime change: unpacking a loosely typed dict
  (for example `L3Rule(**dict[str, str])`) into `L3Rule` or `SecurityEvent` now
  fails type-checking, because `src_ports`, `dst_ports`, `timestamp` and the
  private provenance fields (`_ports_seen`, `_ts_seen`; not API) are keyword
  parameters; type the dict or pass the fields explicitly. Listed in the design
  doc's "Effective now". Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.

#### Deprecated

- **parameters and fields** `PacketFilter` (`chain`, `set_default_policy(policy)`),
  `Nat.list_nat_rules(mode)`, `Conntrack` (`protocol`, `state`), `FirewallRule.action` /
  `protocol`, `NatRule.mode` / `protocol`, `PortMapping.protocol` and
  `Connection.protocol` / `state` — a plain `str` naming a member (`"FORWARD"`,
  `"drop"`, `"snat"`, `"tcp"`, `"allow"`, `"tcp-udp"`, `"ESTABLISHED"`) is
  deprecated: it warns and is converted. The annotations narrow to the enums in
  a later release. Use `Chain`, `DefaultAction`, `NatMode`, `RuleProtocol`,
  `FirewallRuleAction`, `PortMappingProtocol` and `ConnState`. Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.
- **return type** `PacketFilter.get_default_policy` — announced only: it returns
  `str` today and narrows to `DefaultAction` in a later release (a
  `DefaultAction` is a `str`, so comparisons with the plain words keep working).
  Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.
- **fields** `FirewallRule.dst_port`, `NatRule.dst_port` and
  `NatRule.translated_port` — the port text; assigning or constructing from it
  warns. Use `dst_ports` / `translated_ports`. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **protocol members** `PacketFilter.get_rule_counters` and
  `Nat.get_nat_rule_counters` — deprecated names of `get_rule_counter_values` and
  `get_nat_rule_counter_values`; they return `RuleCounters` from the new names.
  Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **placeholders** `NatRule.src_cidr`, `dst_cidr`, `translated_src` and
  `translated_dst` — announced only: `""` means absent today and becomes `None`
  in a later release. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **fields** `L3Rule.src_port` and `dst_port`, `SecurityEvent.ts` — the port and
  timestamp text; assigning or constructing from it warns. Use `src_ports` /
  `dst_ports` and `timestamp`. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **placeholders** `L3Rule.src_cidr` and `dst_cidr` (`"any"`),
  `UplinkStatus.ip`, `gateway`, `public_ip` and `primary_dns` (`""`), and
  `NetworkAttachment.segment` (`""`) — announced only: they mean
  unconstrained or not reported today and become `str | None` (`None`) in a
  later release. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.

### testoperations

- no entries yet

## [0.12.1] — 2026-09-09

### testprotocols

- no API change (version bump only)

### testoperations

#### Added

- **operation** `testoperations.homing:set_subnet_advertised` — flip one
  overlay subnet's advertise flag in place over the whole-replace
  site-to-site VPN configuration: an existing entry keeps its position and
  takes the flag, an absent entry is appended on advertise and left absent
  on withdraw, role and hubs pass through; exact-string subnet match; no
  write when the rebuilt configuration equals the one read.
  No proposal; PR #28.

## [0.12.0] — 2026-09-05

### testprotocols

#### Breaking for driver authors

- **model field** `testprotocols.models:VlanConfig.reserved_ranges` —
  `list[tuple[str, str]]` becomes `list[ReservedRange]`. Migration: readers
  build `ReservedRange(r["start"], r["end"], r.get("comment", ""))`;
  writers emit `{"start": r.start, "end": r.end, "comment": r.comment}`,
  supplying a label where the management plane requires one.
  No proposal; PR #27.
- **model field** `testprotocols.models:InterfaceDhcpConfig.reserved_ranges`
  — the same retype and migration as `VlanConfig.reserved_ranges`.
  No proposal; PR #27.
- **boundary-view member**
  `testprotocols.network_attachment:NetworkAttachment.test_interface` — new
  mandatory read-only property: the name of the endpoint's leg on the test
  segment, as the endpoint's own `IpInterface` keys it; `""` when there is
  no test leg. Migration: implement it on every `NetworkAttachment` view
  before bumping the pin; consumers replace structural reads of the
  attribute. No proposal; PR #27.

#### Added

- **model** `testprotocols.models:ReservedRange` — a reserved DHCP range
  with its label: `start`, `end`, `comment=""`. No proposal; PR #27.
- **capability protocol** `testprotocols.held_prefixes:HeldPrefixes` — a
  testbed instrument holds a caller-supplied `host/prefixlen` on a
  loopback-class interface it allocates (`hold` / `release` / `held`,
  address-keyed, idempotent); holding is not advertising.
  No proposal; PR #27.

### testoperations

- no API change (version bump only)

## [0.11.3] — 2026-08-30

### testprotocols

#### Breaking for driver authors

- **archetype member**
  `testprotocols.devices.client:QoeMeasurementClientDevice.http_client` —
  the QoE measurement client archetype composes `http_client: HttpClient`,
  as both sibling client archetypes already do. Migration: wire an
  `HttpClient` implementation on every driver of this archetype before
  bumping the pin. No proposal; PR #26.

#### Added

- **capability protocol** `testprotocols.packet_injector:PacketInjector` —
  put caller-supplied bytes on the wire (`emit_signature`; `port` required
  for TCP and UDP, `None` for portless transports) and replay a
  caller-supplied capture (`replay_pcap`); a substrate capability, distinct
  from a device-under-test threat-prevention subsystem.
  No proposal; PR #26.
- **model** `testprotocols.models:EmitResult` — the normalized result of
  `PacketInjector.emit_signature`. No proposal; PR #26.
- **model** `testprotocols.models:ReplayResult` — the normalized result of
  `PacketInjector.replay_pcap`. No proposal; PR #26.

### testoperations

- no API change (version bump only)

## [0.11.2] — 2026-08-23

### testprotocols

- no API change (version bump only)

### testoperations

#### Added

- **operation** `testoperations.waiting:await_reachability` — the
  result-returning sibling of `wait_for_reachability`: returns a
  `ReachabilityAwait` carrying what the probe actually read and the poll
  loop's bounds, never an echo of the expectation on budget expiry;
  `wait_for_reachability` is unchanged. No proposal; PR #25.
- **model** `testoperations.waiting:ReachabilityAwait` — the probe's last
  reading (`reachable`) plus the poll loop that found it: `elapsed_s`,
  `polls`, `poll_interval_s`, `not_converged_at_s`. No proposal; PR #25.
- **operation** `testoperations.segmentation:derive_decoy_target` — derive
  an inert deny target from a documentation range, with a fail-closed
  non-collision check against the caller's in-use CIDRs; returns a
  `DecoyDerivation`, assertion-free. No proposal; PR #25.
- **model** `testoperations.segmentation:DecoyDerivation` — a derived
  decoy deny-target (`subnet`, its first-host `host`) plus `collisions`,
  the in-use CIDRs it overlaps; empty means safe. No proposal; PR #25.
- **constant** `testoperations.segmentation:DECOY_RANGE` — the fixed
  RFC 5737 TEST-NET-2 range (`198.51.100.0/24`) `derive_decoy_target`
  derives its decoy target from; reserved for documentation, never
  routable in a production overlay. No proposal; PR #25.

## [0.11.1] — 2026-08-22

### testprotocols

- no API change (version bump only)

### testoperations

#### Added

- **operation**
  `testoperations.throughput:measure_concurrent_throughput_with_retry` — an
  engine over the one-shot `measure_concurrent_throughput` that re-runs the
  whole overlapping flow set on fresh ports when the caller's `retry_when`
  predicate accepts a `NonCompletion`, within a budget; the default
  `retry_when=None` never retries. `measure_concurrent_throughput` stays
  one-shot. No proposal; PR #24.

## [0.11.0] — 2026-08-12

### testprotocols

- no API change (version bump only)

### testoperations

#### Added

- **operation** `testoperations.marking_observation:observe_flow_dscp` —
  per-flow DSCP histograms (`{flow: {dscp: frames}}`) over one shared
  capture window at a capture vantage, flows selected by `FlowSelector`
  (fail-loud at construction); on an encapsulated vantage the outer header
  wins. No proposal; PR #22.
- **model** `testoperations.marking_observation:FlowSelector` — one
  observed flow selected by on-wire address facts (`dst_host`,
  `src_host`, `protocol`, `dst_port`); fail-loud at construction on an
  inconsistent host or port/transport combination. No proposal; PR #22.

## [0.10.0] — 2026-08-11

### testprotocols

#### Breaking for driver authors

- **protocol member**
  `testprotocols.iperf_client:IperfClient.start_traffic_sender` — gains
  `datagram_bytes: int | None = None` (a fixed on-wire datagram size) and
  `report_interval_s: int | None = None` (periodic interval reports);
  absent means no flag and unchanged behaviour. Migration: implementers add
  both parameters; callers need no change. No proposal; PR #20.

### testoperations

- no API change (version bump only)

## [0.9.0] — 2026-08-10

### testprotocols

#### Breaking for driver authors

- **archetype member**
  `testprotocols.devices.sdwan:SdwanApplianceDevice.uplink_ports` — the
  SD-WAN appliance archetype composes `uplink_ports: UplinkPorts`.
  Migration: provide an `UplinkPorts` view on every driver of this
  archetype. No proposal; PR #19.
- **protocol member**
  `testprotocols.sdwan_policy_manager:SdwanPolicyManager.get_sla_policies`
  — read-back for the SLA-policy write/remove pair. Migration: implement it
  on every `SdwanPolicyManager`. No proposal; PR #19.
- **protocol member**
  `testprotocols.sdwan_policy_manager:SdwanPolicyManager.get_uplink_selection_settings`
  — the scalar half of the uplink-selection surface, read as one
  `UplinkSelectionSettings` snapshot. Migration: implement it on every
  `SdwanPolicyManager`. No proposal; PR #19.
- **protocol member**
  `testprotocols.sdwan_policy_manager:SdwanPolicyManager.set_active_active_vpn`
  — the matching write. Migration: implement it on every
  `SdwanPolicyManager`. No proposal; PR #19.
- **protocol member**
  `testprotocols.site_to_site_vpn:SiteToSiteVpn.get_vpn_path_metrics` —
  observed overlay path quality per local uplink, distinct from the
  underlay probe metrics of `Router.get_wan_path_metrics`. Migration:
  implement it on every `SiteToSiteVpn`. No proposal; PR #19.

#### Added

- **boundary view** `testprotocols.uplink_ports:UplinkPorts` — a WAN edge's
  declared uplink-to-switch-port wiring; the switch's placement ports stay
  the write authorization. No proposal; PR #19.
- **model** `testprotocols.uplink_ports:UplinkPortRef` — one uplink's
  switch-port reference in `UplinkPorts`. No proposal; PR #19.
- **model** `testprotocols.models.sdwan_appliance:UplinkSelectionSettings`
  — the uplink-selection scalars read and written by
  `SdwanPolicyManager`. No proposal; PR #19.

### testoperations

#### Added

- **operation** `testoperations.path_placement:count_signature_on_path` —
  count frames of one packet-size signature on a wire vantage.
  No proposal; PR #19.
- **model** `testoperations.path_placement:SizeBand` — an inclusive
  on-the-wire frame-length band (`min_bytes`, `max_bytes`) identifying one
  stream by its packet-size signature. No proposal; PR #19.
- **operation** `testoperations.path_placement:locate_streams_by_size` —
  locate each stream's path by its size signature, one shared window across
  paths. No proposal; PR #19.
- **operation** `testoperations.path_placement:await_stream_on_path` — a
  caller-anchored bounded await returning a `ConvergenceRecord`; the budget
  verdict stays with the caller. No proposal; PR #19.
- **model** `testoperations.path_placement:ConvergenceRecord` — the
  recorded outcome of one bounded placement await: `elapsed_s`,
  `converged`, and the full `samples` trace of `(elapsed_s, located_path)`
  polls; facts only, no verdict. No proposal; PR #19.
- **operation** `testoperations.iperf_client:sender_life_record` — parse a
  stopped sender's interval reports into a `SenderLifeRecord` (intervals,
  gaps, total bytes). No proposal; PR #19.
- **model** `testoperations.iperf_client:SenderLifeRecord` — a stopped
  sender's life parsed from its interval reports: `intervals`, `gaps`
  (transmission holes), `total_bytes`; the end-of-run summary line is
  excluded from all three. No proposal; PR #19.
