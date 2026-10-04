# Design: precise types across the released contracts

| Field   | Value                                                                 |
| ------- | --------------------------------------------------------------------- |
| Status  | In progress                                                           |
| Author  | rjvisser                                                              |
| Date    | 2026-10-04                                                            |
| Related | `docs/proposals/README.md` (question 9, precise types), `CONTRIBUTING.md` (Versioning), `testprotocols.deprecation`, `testprotocols.models._sync`, `packages/testprotocols/tests/test_typing_ratchet.py` |

## Purpose

The proposal review asks every added or changed member to be typed precisely
(question 9). Members released before that question existed are not all typed
that way: closed vocabularies are plain `str`, grammars are text, absent values
are `""` or `0`, and some records are `Any`. This document records how the
released contracts are brought to precise types without breaking a caller or a
driver in one step: every retype is a deprecation (widen, then narrow), and the
shapes below are the only ones used.

## The precise-types rule

- A value from a closed set (a mode, state, action, direction, protocol) is an
  `Enum` (`StrEnum` or `IntEnum`), never a free-form `str` and never a
  `Literal`. A set a registry closes is a pure enum.
- A vocabulary a device may legitimately extend is an enum with an `OTHER`
  member and a companion raw-text field (`<field>_raw: str | None`) holding the
  device's own word, so nothing is lost or guessed (shape 3o).
- `str` stays only for open values: interface, object, route, server, zone,
  file, BSS and user names, and similar.
- A grammar held as text (port lists, `(kind, value)` pairs) becomes a typed
  record; the text form stays readable during the deprecation period.
- Records are dataclasses, never a `dict` or a bare `tuple`; a new record is
  `@dataclass(frozen=True)` unless it extends a model that is already mutable.
- An absent value is `X | None`, never an empty-string or zero sentinel.
- No explicit `Any` in a signature or field. `tests/test_typing_ratchet.py`
  caps the explicit-`Any` count per package; a retype may lower the ceiling and
  never raises it. When the count reaches zero the ratchet is replaced by mypy's
  `disallow_any_explicit`.

## Deprecation shapes

Each retype names one of these shapes. The building blocks are reused, never
copied: `testprotocols.deprecation` (`coerce_enum`, `coerce_int`,
`coerce_open_enum`, `warn_renamed`, `renamed_attribute`, `MODEL_FRAMES`),
`testprotocols.models._sync` and, for shape 3o, `testprotocols.models._open_enum`.

- **Shape 1: a released `str` parameter becomes an enum.** The parameter is
  annotated `E | str`. A driver or operation coerces it once, at its boundary
  and before any device I/O, with `coerce_enum(E, value, what=…)`: a member
  passes, a plain string naming a member warns (`DeprecationWarning`) and
  converts, any other string raises `ValueError` listing the legal values.
- **Shape 1i: a released `str` parameter that is really a number becomes
  `int`.** The parameter is annotated `int | str`; `coerce_int` returns the
  int and warns on a numeric string, and a non-numeric string raises
  `ValueError`.
- **Shape 3: a released model field becomes an enum.** The field is annotated
  `E | str` and the model coerces it in `__setattr__` (a mutable model) or
  `__post_init__` (a frozen one), with `skip_file_prefixes=MODEL_FRAMES` so the
  warning points at the caller's construction or assignment site. A reader
  always holds the member.
- **Shape 3o: an extensible enum field.** The field is annotated `E | str` (as
  shape 3, so a caller may still pass a plain string) and always holds a member
  after construction; `E` has a catch-all `OTHER`, and the device's own word is
  held in `<field>_raw: str | None`, only while the field is `OTHER`. A plain
  string naming a member converts with a warning (an exact match). Any other
  string, the empty one included, becomes `OTHER` plus the raw word, kept
  verbatim, with no error and no warning, because the set is open by contract.
  The pair is an `OpenEnumPair` (`models/_open_enum.py`), a `_sync` pair with
  the same hidden provenance field, so it agrees after construction,
  `replace` and assignment, and **the side that changed wins**: a member clears
  the raw word, an unknown string sets it, changing only the raw word keeps the
  field. A raw word beside a named member, or one that disagrees with the unknown
  word the field was given, raises `ValueError` and changes nothing. A frozen
  record calls `settle` from `__post_init__` alone; a mutable one adds `assign`
  in `__setattr__`. `coerce_open_enum` is the function-level form, for a driver
  boundary: it returns `(member, raw)`.
- **Shape 3o, many words: a multi-valued open set.** A record that holds several
  device words of an open set (a station's capability flags) cannot use a per-word
  `OTHER`: the typed field is `tuple[E, ...]` of the words that name a member and a
  companion `<field>_unknown: tuple[str, ...]` holds the others, verbatim and in
  order. The released `list[str]` stays and holds the device's full word list in its
  own order; the three are an `OpenSetPair` (`models/_open_set.py`), a `_sync` pair
  with the same hidden provenance field (the agreed text is the word list), and the
  side that changed wins as in the other shapes. A word names a member exactly,
  letter case included. A refused assignment changes nothing.
- **Shape 4(ii): a released field holding a grammar becomes structured.** A
  new typed field is added beside the text field and the two are kept in
  agreement through `_sync` (below).
- **Shape 4p: a free-string tool parameter becomes typed keyword
  parameters.** The typed keyword-only parameters are added; the old string
  parameter stays, documented as deprecated, and warns when non-empty; passing
  both raises `ValueError`. No parameter changes position.
- **Shape 5: a tuple, dict or `Any` record return becomes a dataclass.** A new
  member name returns the dataclass. The old name is documented "Deprecated
  name of …" and an implementer delegates to the new one after
  `warn_renamed`. `testoperations` callers move to the new name through a
  typed fallback accessor, new name first, then the old; the accessor module
  (`testoperations/_renamed.py`) arrives with the first shape 5 retype.
- **Shape 6: announced only.** A return narrowing to an enum, and a `""`,
  `0` or `"any"` placeholder becoming `None`, get a docstring sentence and a
  *Deprecated* changelog entry. The type changes at the removal step.

A narrowing that takes effect at once (a value that was never meaningful now
raises) is recorded under *Changed* in the changelog.

## Synced fields: the side that changed wins

A shape 4(ii) retype keeps a deprecated text field (or several fields that
together spell one value, such as a `(kind, value)` pair) and its typed
successor in agreement. `testprotocols.models._sync` holds the rule once;
a model declares one `SyncedField` (one text field) or `SyncedFields` (several)
per pair and calls `settle` from `__post_init__` and `assign` from
`__setattr__`.

- **At construction**, a typed value fills the text; the text alone warns and
  fills the typed value; both given and disagreeing raise `ValueError`.
- **Through `dataclasses.replace` and assignment, the side that changed
  wins.** Changing the typed field rewrites the text silently; changing the
  text re-parses it into the typed field and warns. Both changed and
  disagreeing raise `ValueError`.
- **Parse before warn.** Malformed text raises `ValueError` without warning
  and changes nothing.
- **Type errors.** A text field assigned a non-text value, or an enum-typed
  text field assigned a value of another type, raises `TypeError`; a plain
  string for an enum-typed text field converts through `coerce_enum`.
- **Provenance last.** A hidden provenance field (`repr=False`,
  `compare=False`) records the agreed text of every pair; `replace` copies it,
  which is how a changed side is told from an unchanged one. It must be the
  model's last field, because the generated `__init__` assigns in field order;
  `settle` raises `TypeError` otherwise.
- Text is kept in its canonical form, so two records that agree compare equal
  whichever side built them.

## Retypes

Each retype that has landed, with its shape. A capability's own design document,
where one exists, also records its retype.

- **Firewall, NAT and conntrack vocabularies** (shapes 1, 3, 3o and 6). Five
  enums in `testprotocols.models`: `Chain` (`INPUT`, `OUTPUT`, `FORWARD`),
  `FirewallRuleAction` (`allow`, `deny`, `reject`, `log`), `NatMode` (`snat`,
  `dnat`, `1to1`), `PortMappingProtocol` (`tcp`, `udp`, `tcp-udp`) and
  `ConnState`. A rule's, NAT rule's and connection's transport is the existing
  `RuleProtocol`; a chain default policy is `DefaultAction`. The `chain`,
  `policy`, `mode`, `protocol` and `state` parameters of `PacketFilter`, `Nat`
  and `Conntrack` are `E | str` and a driver coerces once at each member
  (shape 1). The four closed vocabularies on `FirewallRule`, `NatRule`,
  `PortMapping` and `Connection` are shape 3: the records are mutable, so the
  coercion is a `__setattr__`, and a plain string warns while an unknown one
  raises `ValueError`. `ConnState` is open (shape 3o): the released contract
  listed nine TCP states, `UNREPLIED` and `ASSURED`, "or driver-specific
  values", so it has those members plus `OTHER`. Its values are exactly the
  released upper-case words (`"ESTABLISHED"`), so `conn.state == "ESTABLISHED"`
  still holds; every enum of this retype equals its released strings. The device's
  own word is in `Connection.state_raw` while the state is `OTHER`. An unknown
  word never raises and never warns; a named plain string warns. Edge words: the
  match is exact, so `"established"` and `"other"` are unknown words (`OTHER` plus
  that raw word), `""` is an unknown word kept as `""`, and `"OTHER"` names the
  member (a warning, no raw word). The pair follows the shape 3o rule above:
  the side that changed wins under `replace` and assignment; a raw word with a
  named state raises `ValueError`. A `state` filter with an unknown word matches flows whose
  `state_raw` equals it. A conntrack `protocol` filter of `any` is refused: a
  flow has one transport, and so is `Connection.protocol`, which raises
  `ValueError` for `RuleProtocol.ANY`. `get_default_policy` keeps returning `str`
  (shape 6, announced only).
- **Firewall and NAT ports and counters** (shapes 4(ii), 5 and 6). `FirewallRule`
  gains `dst_ports` and `NatRule` gains `dst_ports` and `translated_ports`, each a
  `tuple[PortRange, ...]` synced with its deprecated text field through `_sync`.
  A record has one provenance field (`_ports_seen`, last), shared by all its pairs,
  and the same `__setattr__` also applies the enum coercion of the vocabularies
  retype. `FirewallRule.dst_port` now defaults to `"any"` (its released contract
  allowed `"any"`; the default lets a rule be built from `dst_ports` alone). The
  released `NatRule` contract used `""` for no port, so its pairs use `""` as the
  canonical empty text (`"any"` is accepted and reads back `""`), while
  `FirewallRule` keeps `"any"`. The `NatRule` cidr and translated-address `""`
  placeholders are announced only (shape 6). `RuleCounters(packets, bytes)`
  replaces the `(int, int)` tuple: the new members
  `PacketFilter.get_rule_counter_values` and `Nat.get_nat_rule_counter_values`
  are mandatory (breaking for driver authors), the old names deprecated (shape 5).
  `testoperations` does not call either old name.
- **SD-WAN models** (shapes 4(ii) and 6). `L3Rule` gains `src_ports` and
  `dst_ports`, `tuple[PortRange, ...]` synced with the deprecated `src_port` /
  `dst_port` text through `_sync`, one provenance field (`_ports_seen`) for both
  pairs, as on `FirewallRule`. `SecurityEvent` gains `timestamp: datetime | None`
  synced with the deprecated ISO-8601 `ts`. The codec is `datetime.fromisoformat`
  and `datetime.isoformat()`; a timezone-naive value stays naive and no zone is
  assumed. An ISO-8601 instant has several equal spellings (`Z` or `+00:00`, `T` or
  a space), and `isoformat()` writes one, so `isoformat()` does not round-trip a
  producer's text: the pair is a `SyncedField` with `keep_text=True`, which keeps a
  text exactly as given when it differs from the canonical form only in spelling
  (it parses to the agreed value and formats back to the agreed text). A text that
  spells a different value, such as the same instant at another UTC offset, is
  rewritten, so `replace`, assignment and re-assigning the same value agree. A
  typed value alone writes `isoformat()`. Two events with the same instant in two
  spellings compare unequal on `ts`. `ts` gained a default (`""`, no time) so an event can
  be built from `timestamp` alone; the fields after it keep their released
  positions and take a required-argument placeholder that `__post_init__` refuses,
  so omitting one still raises `TypeError` (the placeholder reads `<required>`). The `"any"` cidr placeholders of
  `L3Rule`, the `""` placeholders of `UplinkStatus` and `NetworkAttachment.segment`
  are announced only (shape 6).
- **WAN-edge models** (shapes 3, 3o and the orphan deprecation). `LinkStatus.state`
  and `LinkHealthReport.state` are `UplinkState` (shape 3): the released words `up`,
  `down` and `degraded` are existing members, and `UplinkState` gains `UNKNOWN`
  because the reference implementer reports `"unknown"` for a link with no health
  data (a value the released contract did not forbid, so it must keep working); an
  `UplinkState` is not the appliance's state of record, only the shared vocabulary.
  `AppFlow.category` is `ApplicationCategory` with `category_raw` (shape 3o, an
  `OpenEnumPair`, the rule of `Connection.state`); `ApplicationCategory` gains
  `OTHER`, which `CategoryMatch` refuses, so no L7 or shaping rule can match on it.
  A record holds either `SyncedField` pairs or one `OpenEnumPair` under its single
  provenance field; `AppFlow` has only the latter. `VPNPeerStatus` and
  `TrafficShapingRule` have no capability using them and no successor: both are deprecated by a
  module `__getattr__` (`deprecated_attribute`, the no-successor counterpart of
  `renamed_attribute`) in `wan_edge` and in `testprotocols.models`, removed from
  `models.__all__`, and still defined for type checkers under `TYPE_CHECKING`, so
  a consumer that imports them sees a `DeprecationWarning` and no static error.
  `TrafficShapingRule.match` is `Mapping[str, object]`. `ShapingRule` is not a
  drop-in successor: its `match` is one `TrafficMatch`, so it cannot express the
  dict match (destination prefix, source prefix, protocol, port) a reference
  consumer builds into `TrafficShapingRule`.
- **Switch QoS classifier** (shape 4(ii)). `QosRule.classifier` is
  `QosClassifier | None`, synced with the deprecated `match` text. `QosClassifier`
  is a frozen record of neutral fields: `vlan`, `protocol` (`RuleProtocol`),
  `src_ports` and `dst_ports` (`PortRange` tuples); a field left out places no
  restriction. The released contract described `match` as a vendor-neutral
  expression "by VLAN, protocol, or port" and gave it no grammar, so free text is
  legal and a pinned test used `"vlan 10"`. The reference producers write a comma
  list of `key=value` terms over a VLAN, a protocol, and source and destination
  ports (a port, or an `a-b` range). The parser accepts that list (protocol in any
  letter case, `any` is `RuleProtocol.ANY`); text that is not such a list has no
  classifier, so `classifier` is `None` and `match` keeps the text exactly as given:
  no error, nothing lost. A term given twice raises `ValueError`. Parsed text keeps
  its spelling (`keep_text`); assigning a classifier writes canonical text. A
  `TrafficMatch` was the wrong carrier: it is one match of one kind and has no VLAN
  or protocol. A rule holds one source and one destination range at most, because
  the text spells one range per direction.
- **Telemetry and policy** (shapes 5 and the no-successor deprecation). `Telemetry`
  replaces the `dict[str, Any]` that `Router.get_telemetry` returned (shape 5); the old member now returns
  `Mapping[str, float]`, so an implementer whose declared return is not
  `float`-valued no longer conforms:
  `Router.read_telemetry() -> Telemetry` is a new mandatory member, and the old name
  is documented "Deprecated name of" it; a driver delegates with
  `read_telemetry().as_dict()` after `warn_renamed`. The fields come from evidence,
  not from design. The released docstring said only "a dict of current device
  telemetry data" and named no key. The only implementer in the consumer examples
  (a Linux router) returns `uptime_seconds`, `cpu_load_percent` and
  `mem_used_percent`, all floats, and omits a CPU key when it cannot read one; so
  `Telemetry` has exactly those three fields, the last two optional, and no other
  field (a temperature or load average would be a guess). Each value is a finite,
  non-negative number (`nan` and `inf` raise `ValueError`). `testoperations` does not
  call `get_telemetry`, so there is no accessor in `_renamed.py`.
  `SdwanPolicyManager.apply_policy` is deprecated with no successor (the typed
  steering and SLA members cover it) and keeps its name and place; `Any` becomes
  `object` (`dict[str, object]`). A `Mapping` parameter would be the wider type, but
  a protocol parameter wider than an implementer's `dict` parameter makes the
  implementer fail to conform statically, so the parameter stays a `dict`.
- **Segmentation deny scope** (shape 1, `testoperations`). `build_deny_rule(scope,
  proto)` takes `DenyScope | str` (`DenyScope`: `HOST`, `SUBNET`, defined in
  `testoperations.segmentation`) and `RuleProtocol | str`; both are coerced once at
  the top with `coerce_enum`, so a bad word raises before a rule is built. The
  released text accepted `"host"`, `"subnet"` and a `RuleProtocol` value, all of which
  still work and now warn. The released ``ValueError`` for an unknown scope read
  `unknown rule scope 'vlan' (expected 'host' or 'subnet')`; it now reads
  `scope: 'vlan' is not one of ['host', 'subnet']` (same exception type, still names
  `scope`).
- **Wi-Fi vocabularies** (shapes 1, 1i, 3, 3o many words, 5 and 6). Seven closed
  enums and one open set in `testprotocols.models`, all equal to their released
  strings: `WifiBand` (`2.4GHz`, `5GHz`, `6GHz`), `WifiSecurityMode` (the eight words
  of the `create_bss` docstring, `WPA2-WPA3-PSK-Mixed` included), `MfpMode`,
  `WifiAclMode`, `WifiPhyMode`, `ChannelWidth` (an `IntEnum`) and `MeshRole`, and
  `WifiCapability`. The `band`, `security_mode`, `mfp`, `mode`, `bandwidth_mhz` and
  `set_acl_mode` parameters are `E | str` (`ChannelWidth | int`), coerced by the
  driver once; `coerce_enum` now returns an `IntEnum` member for a plain `int`
  with no warning (the number is the value, not a deprecated spelling), and refuses
  a `bool`, a `float` and text. `WifiClient.set_wlan_scan_channel` takes `int | str`
  (`coerce_int`). The model fields (`WifiBssConfig`, `WifiStation`, `WifiNeighbor`,
  `WifiChannelUtilization`, `WifiRadioStats`, `WifiMeshLink`, `WifiAcl`,
  `WifiMeshStatus`, `WifiMeshNode`) are shape 3, a `__setattr__` coercion. Decisions
  taken on evidence rather than from the survey: `WifiNeighbor.security_mode` stays free text
  (a best-effort identification of a foreign network); `WifiClient.wifi_client_connect`'s
  `security_mode` stays `str | None` because the only implementer passes a client
  key-management word (`NONE`, `WPA-PSK`, `WPA-EAP`), not an access-point
  `WifiSecurityMode`; `WifiClient.iwlist_supported_channels(wifi_band)` keeps its
  `wifi_band: str` because that implementer passes `"2.4"` and `"5"`, not `WifiBand`
  values; `WifiRadio.set_mode` documents that a compound mode (`"n/ac/ax"`, which the
  released contract allowed at a driver's discretion) names no member and is the
  driver's own `str`, and `get_mode` stays `str` for the same reason (announced,
  shape 6, like `list_radios` and `get_bandwidth`). `WifiCapability` is open but has
  no `OTHER`: `WifiStation.capabilities` holds the members and
  `capability_flags_unknown` the other words (the multi-valued variant of shape 3o
  above), synced with the released `capability_flags`. The typed side is named
  `capabilities` because `capability_flags` is the released word list. One record
  carries one provenance field: `WifiStation` has the one `OpenSetPair` (its `band` is a
  plain shape 3 coercion), so no shared provenance was needed.
  `WifiClient.iwlist_supported_channels -> list[str]` is shape 5: the new mandatory
  member `supported_channels(band: WifiBand) -> list[int]` replaces it (breaking for
  driver authors; a driver delegates with `warn_renamed`); `testoperations` does not
  call either. `WifiMeshWhiteBox.get_raw_easymesh_tlvs(message_type)` stays `str |
  None`: no local source lists the EasyMesh message names (the repository mentions
  two examples in a docstring and no vocabulary), and an enum from memory would
  guess; it is revisited when a reference driver and the specification supply them.
- **Voice vocabularies** (shapes 1, 3o parameters, 5 and 6). `PhoneState`, `PresenceStatus`
  and `SipMethod` in `testprotocols.models`, every member equal to a released or used
  string: `PhoneState` has one member per `is_*` predicate of `SipPhone` and the
  `wait_for_state` words the example implementer accepts (note `HOLD == "hold"`, not
  `on_hold`); `SipMethod` is the RFC 3261 methods plus `MESSAGE`, `NOTIFY` and `PUBLISH`,
  which the docstrings name. `PresenceStatus` and `SipMethod` are open. Design of the open
  *parameters*: a parameter is `PresenceStatus | str` (`SipMethod | str`) and the
  driver resolves it once with `coerce_open_enum`, which returns `(member, raw)`: a
  member is silent; a plain string naming a member warns and converts; any other string
  gives `(OTHER, word)` with no error and no warning, and the driver sends the **raw word**
  to the device (so `notify_presence(user, "available")` publishes `available`). The
  parameter stays `str`-typed rather than becoming an `OpenEnumPair` because there is no
  record to carry a companion field. `get_user_presence -> str` is shape 6, announced
  only: the example implementer already returns `"unknown"`, which names no member.
  `wait_for_state` is closed: an unknown word raises `ValueError`, as the released
  implementer did. `verify_sip_message(message_type)` is `SipMethod | str`. The plan also had an `int`
  for a response code; it is deferred: the example implementer declares
  `message_type: str`, so adding `int` to the protocol parameter makes it fail
  static conformance (a parameter widening breaks an implementer declared narrower),
  which is neither a missing member nor a retyped record. A response code stays its
  released text (`"486"`), a raw word. The example's callers also pass a log marker (`"[VOICEMAIL]"`) and a numeric string
  (`"408"`), which are raw words and still work. `since: Any` is `datetime | None`
  (O40): the example's step definitions pass a `datetime`; its unit test passes a text marker
  straight to the implementer, which may keep `Any`. The three dict readers are shape 5:
  new mandatory `read_rtpengine_stats`, `read_mwi_status` and `read_offline_messages`
  return frozen `RtpStats`, `MwiStatus` and `OfflineMessage`; the old names are deprecated
  and a driver delegates, returning `as_dict()`. Fields come from evidence only. `RtpStats`
  (`engaged`, `sessions`): the released docstring says only "a dictionary"; the one
  implementer returns exactly those two keys and the step definitions read `engaged`.
  `MwiStatus` (`waiting`, `new`, `old`) and `OfflineMessage` (`sender`, `body`,
  `stored_at`): the released docstrings list the keys `waiting`/`new`/`old` and
  `from`/`body`/`timestamp`; `timestamp` was ISO-8601 text and becomes a `datetime`;
  `as_dict()` writes it as `isoformat(sep=" ")` (`"2026-04-22 10:00:00"`, the form the implementer's
  database returns; naive stays naive, aware keeps its offset), and the deprecated reader may
  instead keep returning the driver's original text unchanged
  (the implementer returns the database's text unparsed, so it must parse it). No
  `OTHER` or synced field was needed, so the records are plain frozen dataclasses with
  `__post_init__` type checks. `testoperations` calls none of the three readers.
- **Host-tool and service vocabularies** (shapes 1, 3, 3o, 3o many words, 4p, 5 and 6).
  Evidence for every set, from the released docstrings, the `testoperations` callers, the
  example implementers and the released reference implementers of the host templates
  (a Linux host device and the boardfarm LAN device):
  - O17 `start_http_service(ip_version)` is `"4"` / `"6"`: both implementers run the server
    as `-{ip_version}`. It stays `str` (implementers declare `str`) and its narrowing to
    `IpFamily` is announced. The `testoperations` default `"ipv4"` was a pre-existing bug
    (it rendered `-ipv4`); it is corrected to `"4"` and recorded under *Fixed*.
  - O25 `traceroute(version)` is a command suffix, `""` or `"6"` (`traceroute{version}`). It
    stays `str = ""`; narrowing to `IpFamily | None` is announced. `IpVersion` (`ipv4`,
    `ipv6`) is therefore used only for `nmap(ip_type)` (O30), where the reference
    implementer raises `ValueError` for any other word.
  - O15 `curl(protocol)` is the URL scheme, not an IP version: the docstring says "using
    *protocol*", the example implementer folds it into the target as `<protocol>://<url>`
    and its test calls `curl(host, protocol="http")`. `HttpScheme` (`http`, `https`).
  - O16 numbers stay `str` wherever a released implementer declares `str`: `HttpServer`
    `port`, `UpnpClient` `int_port` / `ext_port`, `VlanClient` `vlan_id` (the Linux host
    device and the boardfarm LAN device declare `str`; `curl` and `nmap` already take
    `str | int`). Widening to `int | str` would fail static conformance for them, which is
    outside the accepted classes. Their narrowing to `int` is announced.
  - O19 `ip_version` of the iperf members is `IpFamily | int | None`, with `IpFamily` an
    `IntEnum` (`V4 = 4`, `V6 = 6`): an implementer that declares `int | None` still
    conforms, and a driver that formats it as `-{ip_version}` still emits `4` / `6`. A driver
    may convert with `coerce_enum` (an `int` is silent for an `IntEnum`).
  - O22 `LinkAdminState` (`up`, `down`) is new and is not `PortAdminState` (`enabled` /
    `disabled`): every implementer passes `up` or `down` to `ip link set`. `set_link_state(state)`
    is `LinkAdminState | str`.
  - O23 (shape 4p): `is_link_admin_up(interface) -> bool` is a new mandatory member; the
    `pattern` parameter of `is_link_up` is documented deprecated and a driver warns when it
    differs from the default. A Linux host reads the `UP` flag of `ip link show`.
  - O47 reuses `PortMappingProtocol` (`tcp`, `udp`, `tcp-udp`); `tcp-udp` is not a UPnP
    protocol and a driver refuses it. The plain `str` stays legal.
  - O14 `DnsRecordType` and O33 `QoeScenario` (`page_load`, the only released word) and
    `PageCompletion` (the four Playwright load events) are `E | str` parameters. O34
    `ServiceStatus` is shape 6, announced only (`get_status -> str`).
  - M21 `MeasurementSpec.tool` / `completion` are shape 3 (closed): `QoeTool` is the four
    tools the example implementer dispatches on (`browser`, `http_client`, `webrtc`,
    `tcp_probe`); `completion` is `QoeCompletion`: the four `PageCompletion` events plus
    `DURATION` (the example's streaming and conferencing specs), and `RESPONSE` and `CONNECT`
    (the boardfarm QoE specification's tool by completion matrix: `http_client` completes on
    `response` or `duration`, `tcp_probe` on `connect`). A `PageCompletion` converts
    silently. `QoeTool` and `QoeCompletion` have `__repr__` returning `repr(self.value)`:
    the example browser measurement embeds `repr(spec.completion)` in a generated script,
    and the default enum repr would break it. Every other enum keeps the default repr.
  - M22 `QoEResult.protocol` is shape 3o with `None` allowed (`OpenEnumPair(optional=True)`):
    `HttpVersion.H1 = "http/1.1"`, `H2 = "h2"`, `H3 = "h3"` are the words a browser
    reports as the next-hop protocol, and the example's unit tests pass `"h2"`, `"h3"` and
    `"http/1.1"` (so they warn: the intended warnings; a driver uses `coerce_open_enum`); any
    other word (`http/1.0`, `h2c`) is `OTHER` plus `protocol_raw`.
  - M23 `TransportProtocol` (`tcp`, `udp`): the released docstring of `saturate_link` lists
    exactly those two; `saturate_link` coerces at its boundary.
  - M24 `AcctStatusType` and M25 `AcctTerminateCause` are shape 3o (`OpenEnumPair` with a raw
    companion on `RadiusAccountingRecord`, two pairs sharing one provenance field), because
    the IANA registries have an open assignment policy. They carry every registered value
    cited from RFC 2866 (status 1 to 3, 7, 8 and `Failed` 15; causes 1 to 18), RFC 2867 (status
    9 to 14: the tunnel values), RFC 3580 (causes 19 to 22) and the IANA RADIUS registry
    (status `Subsystem-On` 18 and `Subsystem-Off` 19; cause `Lost-Power` 23), spelled as the attribute
    dictionary spells them; `Start`, `Interim-Update` and `Stop` are the released words, and
    the released docstring spells no cause. `AcctTerminateCause` is a pure `Enum` with an
    explicit code table (`.code`, `None` for `OTHER`, also on `AcctStatusType`) and also
    converts the registry's prose spellings (`User Request`, `Port Reinitialized`, `Port
    Administratively Disabled`, `Lost Power`); the conversion warns quoting the word the
    caller passed. A pure `Enum` does not equal a `str`.
  - M26 `RadiusUser.eap_methods: list[str]` is a multi-valued open set (shape 3o, many
    words, `OpenSetPair`): `eap_methods_known` and `eap_methods_unknown` sync with the
    released list. `EapMethod` has the two words of the released docstring and five more
    (`PEAP-GTC`, `TTLS-MSCHAPv2`, `EAP-TLS`, `EAP-SIM`, `EAP-AKA`) named by analogy to
    them; no local driver uses those five. There is no single-valued EAP field, so no
    `OpenEnumPair` is used for it. `add_user(eap_methods: list[str] | None)` keeps its type
    (an implementer declares `list[str]`; `Sequence` would not conform).
  - M33 `StormControlConfig.unit: StormControlUnit | None = None` is an addition.
  - M20 `HTTPResult` is a frozen dataclass `(status, body, raw)` whose constructor still
    takes the response text (`init=False`, parameter `response`), so the released
    `HTTPResult(response)` works; `parse_http_response` is the same parse. `status` is `0`
    for a response with no numeric code or one outside 100 to 599. The released `code` is a
    property returning the text (`""` when absent, the original word when not numeric)
    that warns; `beautified_text` is `body`, warning. The example implementer builds
    `HTTPResult(response)` and its test reads `result.code == "200"`, which still passes with
    a warning.

## Effective now

Changes that take effect in this release for code written against the released
contract, whether or not it uses the deprecated spelling. Each task appends here;
the matching CHANGELOG entry sits under *Changed*.

- **Conntrack and coercion** (vocabularies task). `Connection.protocol` refuses
  `RuleProtocol.ANY` with `ValueError`, as the released docstring said. An unknown
  string on `FirewallRule`, `NatRule`, `PortMapping` or `Connection` (protocol, mode,
  action) raises `ValueError`; a `Connection.state` unknown word never raises: it
  becomes `ConnState.OTHER` plus `state_raw`. A conntrack `protocol` filter of `any`
  is refused. `NatRule.protocol` defaults to `RuleProtocol.ANY`.
- **Firewall and NAT ports** (ports task). `FirewallRule.dst_port` now defaults to
  `"any"`. `NatRule` port text reads `""` for no port (`"any"` is accepted and reads
  back `""`). Port text accepts only `"any"` (or `""` on `NatRule`), numbers, `a-b`
  ranges and comma lists with no trailing comma; colon or slash forms (`"80:90"`,
  `"tcp/80"`) and a trailing comma raise `ValueError`, so a driver that reads them
  back must convert them. A non-text port text or a non-`PortRange` item raises
  `TypeError`.
- **Static-only: unpacking a loose dict** (ports task; no runtime change). Unpacking
  a loosely typed dict, for example `FirewallRule(**dict[str, str])`, into a retyped
  released record fails type-checking, because the synced typed fields (`dst_ports`)
  and the hidden provenance field are keyword parameters and a type checker matches
  the dict's value type against each. The caller types the dict or passes the fields
  explicitly. The private `_ports_seen` also appears in `__init__` signatures and in
  static error text; it is not API.
- **SD-WAN models** (SD-WAN task). `L3Rule.src_port` / `dst_port` follow the
  `FirewallRule` port rule: only `"any"`, numbers, `a-b` ranges and comma lists are
  text that parses (`""`, `"http"`, `"80:90"` and a trailing comma raise
  `ValueError`; a non-text value raises `TypeError`), and text reads back
  canonical. `SecurityEvent.ts` raises `ValueError` for text `datetime.fromisoformat`
  does not parse (released: any string was accepted) and `TypeError` for a
  non-text value. Static only: unpacking a loosely typed dict into `L3Rule` or
  `SecurityEvent` fails type-checking, as for `FirewallRule` (the keyword
  parameters `src_ports`, `dst_ports`, `timestamp` and the private `_ports_seen`
  and `_ts_seen`). Also static only: `ts` has a default, so `src_ip`, `dst_ip`,
  `protocol`, `action` and `category` carry a `<required>` placeholder default and
  a type checker no longer flags an event built without them (a runtime
  `TypeError` still does).
- **WAN-edge models** (WAN-edge task). A `LinkStatus.state` or
  `LinkHealthReport.state` word that is not an `UplinkState` value raises
  `ValueError` (released: any string). `AppFlow.category` never raises; an unknown
  word becomes `OTHER` plus `category_raw`. `testprotocols.models.TrafficShapingRule`
  and `VPNPeerStatus` are not star-exported any more (they warn on access). Static
  only: unpacking a loosely typed dict into `AppFlow` fails type-checking (the
  keyword parameters `category_raw` and the private `_category_seen`);
  `TrafficShapingRule.match` reads as `Mapping[str, object]` (was `dict[str, Any]`).
- **Switch QoS classifier** (switch QoS task). `QosRule.match` raises `ValueError`
  for a term given twice; free text stays legal (no classifier, text unchanged).
  `match` is now optional (`""`, every frame). A non-text `match` raises
  `TypeError`. Static only: unpacking a
  loosely typed dict into `QosRule` fails type-checking (`classifier` and the private
  `_match_seen`).
- **Telemetry and policy** (router task). Static only, no runtime change:
  `Router.get_telemetry` returns `Mapping[str, float]` (was `dict[str, Any]`), so a
  reader gets `float` values and cannot assume a `dict`, and an implementer whose
  declared return is not `float`-valued no longer conforms; `apply_policy` takes
  `dict[str, object]` (was `dict[str, Any]`), so a caller's `dict[str, str]` variable
  no longer type-checks. A driver must implement `Router.read_telemetry` (breaking for
  driver authors).
- **Wi-Fi vocabularies** (Wi-Fi task). A `band`, `security_mode`, `mfp`, ACL `mode` or
  mesh `role` string on a Wi-Fi model that is not a member raises `ValueError`
  (released: any string); `WifiNeighbor.security_mode` is unchanged. A model reader
  now always holds the enum (`StrEnum` members compare equal to the old strings). A
  `WifiStation` built or assigned from `capability_flags` warns and also fills
  `capabilities` and `capability_flags_unknown`; a word matches a member exactly
  (`"he"` is an unknown word). Mutating the `capability_flags` list in place is not
  seen until the next `replace`; assign a list instead. Static only: unpacking a
  loosely typed dict into `WifiStation` fails type-checking (`capabilities`,
  `capability_flags_unknown` and the private `_caps_seen` are keyword parameters), and
  an implementer must provide `WifiClient.supported_channels` (breaking for driver
  authors).
- **Voice vocabularies** (Voice task). `SipServer.verify_sip_message(since)` is
  `datetime | None` (released `Any`): a caller passing a `datetime` or `None` is
  unaffected; one passing a text marker no longer type-checks (an implementer may keep
  `Any`). An implementer must provide `SipServer.read_rtpengine_stats`, `read_mwi_status`
  and `read_offline_messages` (breaking for driver authors). Every other voice
  annotation only widens (`PhoneState | str`, `PresenceStatus | str`,
  `SipMethod | str`).
- **Host-tool and service vocabularies** (host-tool task). `HTTPResult` is frozen (assigning
  an attribute raises `FrozenInstanceError`), compares by value (released: identity) and
  `code` / `beautified_text` warn when read; `status` is `0` outside 100 to 599.
  `MeasurementSpec.tool` / `completion` and `TrafficSpec.protocol` raise `ValueError` for a
  word that names no member (released: any text was stored; the example implementer treated an
  unknown tool as the browser); a plain string naming a member warns and the field holds the
  member. `QoEResult.protocol`, `RadiusAccountingRecord.record_type` and `terminate_cause` hold
  an enum (or `None`): an unknown word becomes `OTHER` plus the raw companion, no error. The
  browser's `"h2"` / `"h3"` / `"http/1.1"` assigned as plain strings are the intended warnings.
  `repr()`: `QoeTool` and `QoeCompletion` repr as their quoted text, so text built with
  `repr(spec.completion)` is unchanged; every other new enum (`IpVersion`, `PageCompletion`,
  `HttpVersion`, `TransportProtocol`, ...) keeps the default `<Enum.MEMBER: 'x'>` repr, and
  code that builds text with `repr(value)` or `{value!r}` must use `str(value)`.
  `AcctTerminateCause` members do not equal text. `RadiusUser` built or assigned from
  `eap_methods` warns and also fills `eap_methods_known` / `eap_methods_unknown`.
  `StormControlConfig.unit` is ignored by released drivers (they read and write their own
  unit): a writer that sets it gets no error from them. The `testoperations`
  `start_http_server` default `ip_version` is now `"4"` (was `"ipv4"`, which rendered an
  invalid server option). Static only: an implementer must provide
  `IpInterface.is_link_admin_up` (breaking for driver authors).

## Pending narrow steps (announced, not yet taken)

Each lands in a later release with its own breaking changelog entry:

- Enum-only parameters and fields: the firewall, NAT and conntrack parameters
  and fields (`Chain`, `DefaultAction`, `NatMode`, `RuleProtocol`,
  `FirewallRuleAction`, `PortMappingProtocol`, `ConnState`) narrow from
  `E | str` to `E`; `get_default_policy` narrows to `DefaultAction`.
- The `NatRule` cidr and translated-address `""` placeholders become `str | None`;
  the port text fields and the old counter names are removed.
- The `L3Rule` cidr `"any"` placeholders, the `UplinkStatus` address `""`
  placeholders and `NetworkAttachment.segment` `""` become `str | None`; the
  `L3Rule` port text fields and `SecurityEvent.ts` are removed.
- `LinkStatus.state`, `LinkHealthReport.state` narrow from `UplinkState | str` to
  `UplinkState` and `AppFlow.category` from `ApplicationCategory | str` to
  `ApplicationCategory`; `LinkStatus.ip_address` `""` becomes `str | None`;
  `VPNPeerStatus` and `TrafficShapingRule` are removed.
- `QosRule.match` is removed.
- `Router.get_telemetry` and `SdwanPolicyManager.apply_policy` are removed.
- `build_deny_rule(scope, proto)` narrows from `DenyScope | str` and
  `RuleProtocol | str` to the enums.
- Wi-Fi: the model fields and parameters narrow from `E | str` to `E` (`WifiBand`,
  `WifiSecurityMode`, `MfpMode`, `WifiAclMode`, `WifiPhyMode`, `MeshRole`;
  `ChannelWidth | int` stays, an `int` being its value); `list_radios`, `get_bandwidth`
  and (once compound modes are settled) `get_mode` narrow to `list[WifiBand]`,
  `ChannelWidth` and `WifiPhyMode`; `set_wlan_scan_channel` narrows to `int`;
  `WifiStation.capability_flags` and `WifiClient.iwlist_supported_channels` are removed.
- Voice: `wait_for_state` narrows to `PhoneState`; `set_presence` and `notify_presence`
  take `PresenceStatus` with the raw word carried beside it; `verify_sip_message`
  narrows to `SipMethod` (and gains `int` for a response code) likewise; `get_user_presence` returns `PresenceStatus`;
  `get_rtpengine_stats`, `get_mwi_status` and `get_offline_messages` are removed.
- Host tools: the `E | str` parameters narrow to the enums (`DnsRecordType`, `HttpScheme`,
  `IpVersion`, `LinkAdminState`, `QoeScenario`, `PageCompletion`, `PortMappingProtocol`);
  the iperf `ip_version` narrows to `IpFamily | None`; the numeric-text parameters narrow
  (`port`, `int_port`, `ext_port`, `vlan_id` to `int`; `start_http_service(ip_version)` to
  `IpFamily`; `traceroute(version)` to `IpFamily | None`); `is_link_up(pattern)` loses
  `pattern`; `get_status` returns `ServiceStatus`; `MeasurementSpec` and `TrafficSpec` fields
  narrow from `E | str` to `E`, and `RadiusAccountingRecord` fields likewise; `HTTPResult.code`
  / `beautified_text` and `RadiusUser.eap_methods` are removed and `HTTPResult.status` `0`
  becomes `None`.
