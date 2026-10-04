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
  that differs from the canonical form only in spelling (it parses to the agreed
  value and formats back to the agreed text, as an ISO-8601 `Z` for `+00:00`) stays
  exactly as given; a text that spells a different value (another UTC offset for
  the same instant) is rewritten, so `replace` and assignment agree. Used by
  `SecurityEvent.ts` and `QosRule.match`. Not public API. Migration: none. Design
  `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **function** `testprotocols.deprecation:deprecated_attribute` — for a module
  `__getattr__` that resolves a deprecated name with no successor, with a
  `DeprecationWarning` that gives the reason; the counterpart of
  `renamed_attribute`. Migration: none. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **enum members** `testprotocols.models:UplinkState.UNKNOWN` (a state the
  product could not determine, such as a link with no health data) and
  `ApplicationCategory.OTHER` (the catch-all of an observed flow; `CategoryMatch`
  refuses it, so no rule can match on it). Migration: none. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **field** `testprotocols.models:AppFlow.category_raw` — the product's own
  category word, held only while `category` is `ApplicationCategory.OTHER`; the
  pair agrees after construction, `replace` and assignment (the rule of
  `Connection.state`). Migration: none. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **model** `testprotocols.models:QosClassifier` (`vlan`, `protocol`, `src_ports`,
  `dst_ports`; frozen; every field left out places no restriction; `vlan` is 1 to
  4094) — what a QoS rule selects. **field** `testprotocols.models:QosRule.classifier`
  — `QosClassifier | None`, kept in agreement with the deprecated text `match`
  (typed fills text; text alone warns and fills typed; disagreeing raises
  `ValueError`; the side that changed wins under `replace` and assignment). Text
  that is not a key=value list of VLAN, protocol and port terms has no classifier:
  `None`, and the text stays as given. A rule holds at most one source and one
  destination port range (`ValueError` otherwise). Migration: pass `classifier`.
  Design `docs/architecture/precise-types-design.md` (switch QoS classifier); PR pending.
- **model** `testprotocols.models:Telemetry` (`uptime_seconds`, `cpu_load_percent`,
  `mem_used_percent`; frozen; the last two are `None` when the device does not
  report them; a bool or non-number raises `TypeError`, a negative number
  `ValueError`; `as_dict()` is the released `get_telemetry` mapping) — a device's
  resource telemetry. Migration: none. Design `docs/architecture/precise-types-design.md` (telemetry and policy); PR pending.
- **enums** `testprotocols.models:WifiBand` (`GHZ_2_4`, `GHZ_5`, `GHZ_6`),
  `WifiSecurityMode` (`OPEN`, `OWE`, `WPA2_PSK`, `WPA2_EAP`, `WPA3_SAE`, `WPA3_EAP`,
  `WPA2_WPA3_PSK_MIXED`, `WPA2_WPA3_EAP_MIXED`), `MfpMode` (`OFF`, `OPTIONAL`,
  `REQUIRED`), `WifiAclMode` (`DISABLED`, `ALLOW`, `DENY`), `WifiPhyMode` (`A`, `B`,
  `G`, `N`, `AC`, `AX`, `BE`), `ChannelWidth` (an `IntEnum`: 20, 40, 80, 160, 320 MHz),
  `MeshRole` (`CONTROLLER`, `AGENT`, `CONTROLLER_AND_AGENT`, `UNCOMMISSIONED`) and the
  open `WifiCapability` (`HT`, `VHT`, `HE`, `EHT`, `MLO`) — the Wi-Fi vocabularies;
  every value is the string the released contract used (`WifiBand.GHZ_5 == "5GHz"`).
  Migration: none. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **fields** `testprotocols.models:WifiStation.capabilities` (`tuple[WifiCapability, ...]`)
  and `capability_flags_unknown` (`tuple[str, ...]`) — the device's capability words
  split into the members and the words no member names, synced with the released
  `capability_flags`: the side that changed wins. Migration: read `capabilities` and
  `capability_flags_unknown`. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **internal module** `testprotocols.models._open_set` (`OpenSetPair`) — the
  multi-valued counterpart of `_open_enum`: a `_sync` pair that splits a released
  word list into known members and unknown words. Not public API. Migration: none. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **behaviour** `testprotocols.deprecation:coerce_enum` — for an `IntEnum`, a plain
  `int` naming a member returns it with no warning (a `bool`, a `float` or a number
  that is no member raises `ValueError`). Migration: none. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **enums** `testprotocols.models:PhoneState` (`IDLE`, `DIALING`, `INCALL_DIALING`,
  `RINGING`, `CONNECTED`, `INCALL_CONNECTED`, `HOLD`, `DIALTONE`, `INCALL_DIALTONE`,
  `CALL_ENDED`, `CODE_ENDED`, `CALL_WAITING`, `CONFERENCE`, `BUSY`, `NOT_ANSWERED`;
  one per `is_*` call-state predicate of `SipPhone`; `HOLD == "hold"`),
  `PresenceStatus` (`ONLINE`, `BUSY`, `AWAY`, `OFFLINE`, `OTHER`; open) and `SipMethod`
  (`INVITE`, `ACK`, `BYE`, `CANCEL`, `OPTIONS`, `REGISTER`, `MESSAGE`, `NOTIFY`,
  `PUBLISH`, `OTHER`; open) — the voice vocabularies; every value is the string the
  released contract or its implementer used. Migration: none. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **records** `testprotocols.models:RtpStats` (`engaged`, `sessions`), `MwiStatus`
  (`waiting`, `new`, `old`) and `OfflineMessage` (`sender`, `body`, `stored_at`) —
  frozen records for what the SIP server's media relay, message-waiting and offline-message
  readers returned as dicts; each has `as_dict()`, the released dict shape (for
  `OfflineMessage`: keys `from`, `body`, `timestamp`, the latter `stored_at.isoformat(sep=" ")`,
  i.e. `"2026-04-22 10:00:00"`, naive stays naive, aware keeps its offset). A driver parses its
  stored text into a `datetime` for `read_offline_messages`; its deprecated
  `get_offline_messages` may keep returning that original text unchanged. A
  wrong type raises `TypeError`, a negative count `ValueError`. Migration: read the new
  records. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **enums** `testprotocols.models:IpVersion` (`IPV4 = "ipv4"`, `IPV6 = "ipv6"`; the
  `nmap(ip_type)` words), the `IntEnum` `IpFamily` (`V4 = 4`, `V6 = 6`; the iperf
  `ip_version` numbers), `DnsRecordType` (`A`, `AAAA`, `CNAME`, `MX`, `NS`, `PTR`, `SOA`,
  `SRV`, `TXT`), `HttpScheme` (`HTTP`, `HTTPS`), `LinkAdminState` (`UP`, `DOWN`; not
  `PortAdminState`, whose words are `enabled` / `disabled`), `QoeTool` (`BROWSER`,
  `HTTP_CLIENT`, `WEBRTC`, `TCP_PROBE`), `PageCompletion` (`LOAD`, `DOMCONTENTLOADED`,
  `NETWORKIDLE`, `COMMIT`), `QoeCompletion` (those four and `DURATION`, `RESPONSE`,
  `CONNECT`), `QoeScenario` (`PAGE_LOAD`), the open `HttpVersion` (`H1 = "http/1.1"`,
  `H2 = "h2"`, `H3 = "h3"`, `OTHER`), `TransportProtocol` (`TCP`, `UDP`), `ServiceStatus`
  (`RUNNING`, `STOPPED`, `ERROR`), `StormControlUnit` (`PERCENT`, `PPS`), the open
  `AcctStatusType` (RFC 2866 `Start`, `Stop`, `Interim-Update`, `Accounting-On`,
  `Accounting-Off`, `Failed`; RFC 2867 `Tunnel-Start` ... `Tunnel-Link-Reject`; IANA
  `Subsystem-On`, `Subsystem-Off`; `OTHER`; `.code` is the registered number),
  the open pure `Enum` `AcctTerminateCause` (RFC 2866 causes 1 to 18, RFC 3580 causes 19 to 22,
  IANA `Lost-Power` 23, `OTHER`; `.code` is the registered number; the registry's prose
  spellings, such as `User Request` and `Port Reinitialized`, convert too) and `EapMethod` (`PEAP-MSCHAPv2` and `TTLS-PAP`,
  the two words of the released docstring, plus `PEAP-GTC`, `TTLS-MSCHAPv2`, `EAP-TLS`,
  `EAP-SIM`, `EAP-AKA`, named by analogy to them and not used by any local driver). Where the
  released contract or an implementer used a word, the member equals it; the registry values
  are spelled as the RADIUS attribute dictionary spells them. `QoeTool` and `QoeCompletion`
  have `__repr__` returning the quoted text (`'load'`), because a released implementer embeds
  `repr(spec.completion)` in generated text. Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **function** `testprotocols.models:parse_http_response(response) -> HTTPResult`.
  Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **fields** `testprotocols.models:QoEResult.protocol_raw`, `RadiusAccountingRecord.record_type_raw`
  and `terminate_cause_raw` (the device's own word, held only while the field is `OTHER`;
  each pair agrees after construction, `replace` and assignment), `RadiusUser.eap_methods_known`
  (`tuple[EapMethod, ...]`) and `eap_methods_unknown` (`tuple[str, ...]`; the methods that
  name a member and the words that name none, synced with the released `eap_methods`;
  the side that changed wins) and `StormControlConfig.unit` (`StormControlUnit | None`,
  default `None`, meaning "as the driver reads it"; released drivers ignore it). Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **option** `testprotocols.models._open_enum:OpenEnumPair(optional=True)` — the field may
  also be `None` (no value reported), which carries no raw word; used by
  `QoEResult.protocol`. Not public API. Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.

- **models** `testprotocols.models:UrlRules` (`allowed`, `blocked`; `as_tuple()`),
  `MemoryUtilization` (`total_bytes`, `used_bytes`, `free_bytes`, and `shared_bytes`,
  `cache_bytes`, `available_bytes` all given or all `None`; used and free at most total;
  `as_dict()`), `ProcessInfo` (`pid`, `tty`, `cpu_time:
  timedelta`, `command`; `as_dict()`), `EventLogEntry` (`timestamp` text, `hostname`, `tag`,
  `message`, `priority`; `severity`; `as_dict()`), `DnsRecord` (`name`, `record_type`, `ttl`,
  `data`, `record_type_raw`), `IperfProcess` (`pid`, `log_file`; `as_tuple()`), `PingResult`
  (`destination`, `transmitted`, `received`, `packet_loss_percent`, `duplicates`, `rtt_*_ms`;
  received at most transmitted, the loss within one point of what they give),
  `NmapResult` (`up`, `addresses`, `ports`) and `NmapPort` (`port`, `protocol:
  TransportProtocol`, `state`, `service`), `ArpEntry` (`address: IPv4Address`, `hw_type`,
  `hw_address`, `flags`, `interface`) — frozen records for the host-tier readers; a wrong type
  raises `TypeError`, an out-of-range or inconsistent value `ValueError`. `as_dict()` /
  `as_tuple()` give exactly what the deprecated reader returned for `UrlRules`,
  `MemoryUtilization` (in bytes), `ProcessInfo` (a procps `ps -A` entry, time
  `[DD-]hh:mm:ss`) and `IperfProcess`. `EventLogEntry.as_dict()` is the released entry of a
  parsed line (`priority`, `date`, `hostname`, `tag`, `content`) only: the released output
  also holds `{"unparsable": line}` entries, which no record holds. Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **enums** `testprotocols.models:SyslogSeverity` (`IntEnum`, RFC 5424 severities 0 to 7),
  `NmapPortState` (nmap's six port states: `open`, `closed`, `filtered`, `unfiltered`,
  `open|filtered`, `closed|filtered`) and the member `DnsRecordType.OTHER` (a read-back value
  for an answer record of a type the enum does not name; its name is in
  `DnsRecord.record_type_raw`). Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **models and functions** `testprotocols.models:Blackout`, `Brownout(latency_ms, jitter_ms,
  loss_percent)`, `LatencySpike(latency_ms, jitter_ms)`, `PacketStorm(loss_percent, latency_ms,
  jitter_ms, duplicate_percent)` (a burst of loss, as the released implementers apply it;
  `duplicate_percent` is `None`, not requested, unless given), the union `TransientEvent`, and
  `transient_event(event, **kwargs)` — the typed transient impairment events (every field
  optional: `None` is the driver's default; `event_name` and `as_kwargs()` give the released `inject_transient` word
  and keywords, a spike's latency being `spike_latency_ms` there) and the converter from a
  released call (an unknown event or keyword raises `ValueError`). Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **functions** `testprotocols.models:coerce_impairment_profile(profile, *, what)`,
  `group_records(records, *, what)` and `parse_window_size(text)` — a driver's converters:
  a netem `dict` profile to `ImpairmentProfile` (warns; a missing figure is `0`, as the
  released example implementer converts; a wrong value type raises `TypeError`), plain group-record tuples to
  `GroupRecord` (warns), and an iperf size (`"8M"`, binary units) to bytes (`ValueError` for
  text that is not a size). Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **internal module** `testprotocols.models._checks` — the field checks the frozen records
  share (`TypeError` for a wrong type, `ValueError` out of range; a `bool` is never a number);
  the voice records use it too. Not public API. Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **model** `testprotocols.models:GroupRecord(sources, group, record_type)` — a `NamedTuple`,
  so it is the released `(sources, group, record_type)` tuple and fits the released
  `MulticastGroupRecord` parameter type; a wrong type raises `TypeError`, also through
  `_make` and `_replace`. Migration: none.
  Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.

#### Breaking for driver authors

- **protocol members** `testprotocols.packet_filter:PacketFilter.get_rule_counter_values(chain, name) -> RuleCounters`
  and `testprotocols.nat:Nat.get_nat_rule_counter_values(name) -> RuleCounters`
  (so also `Firewall`, which inherits `PacketFilter`) — new mandatory members,
  taking the parameters of the old counter members. Migration: implement them
  and make `get_rule_counters` / `get_nat_rule_counters` warn with
  `warn_renamed` and delegate. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **protocol member** `testprotocols.router:Router.read_telemetry() -> Telemetry` —
  new mandatory member. Migration: implement it, and make `get_telemetry` warn
  with `warn_renamed("get_telemetry", "read_telemetry")` and return
  `self.read_telemetry().as_dict()`. Design `docs/architecture/precise-types-design.md` (telemetry and policy); PR pending.
- **protocol member** `testprotocols.wifi_client:WifiClient.supported_channels(band: WifiBand) -> list[int]` —
  new mandatory member, replacing `iwlist_supported_channels` (which returned the
  channel numbers as text). Migration: implement it and make
  `iwlist_supported_channels` warn with `warn_renamed("iwlist_supported_channels",
  "supported_channels")` and return `[str(c) for c in self.supported_channels(band)]`.
  Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **protocol members** `testprotocols.sip_server:SipServer.read_rtpengine_stats() -> RtpStats`,
  `read_mwi_status(user) -> MwiStatus` and `read_offline_messages(user) -> list[OfflineMessage]` —
  new mandatory members, replacing `get_rtpengine_stats`, `get_mwi_status` and
  `get_offline_messages` (which return dicts). Migration: implement them, and make each
  old name warn with `warn_renamed(old, new)` and return the record's `as_dict()` (a list
  comprehension of `as_dict()` for the offline messages). Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **protocol member** `testprotocols.ip_interface:IpInterface.is_link_admin_up(interface) -> bool`
  — new mandatory member: True when the interface is administratively up (the state
  `set_link_state` sets), whether or not a carrier is present. Migration: implement it
  (a Linux host reads the `UP` flag of `ip link show`). Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.

- **protocol members** `ContentFiltering.read_url_rules() -> UrlRules`,
  `DeviceManagement.read_memory_utilization() -> MemoryUtilization`,
  `read_running_processes() -> list[ProcessInfo]` and
  `read_log_entries() -> list[EventLogEntry]`,
  `DnsClient.resolve(domain_name, record_type: DnsRecordType) -> list[DnsRecord]`,
  `IperfClient.start_sender_session(host, traffic_port, *, ..., window_bytes) -> IperfProcess`,
  `IperfServer.start_receiver_session(traffic_port, *, ...) -> IperfProcess`,
  `IpRouting.ping_stats(ping_ip, ping_count, ping_interface, timeout) -> PingResult`,
  `NmapScanner.scan_ports(target, ip_version: IpFamily, *, ports, protocol, max_retries,
  min_rate, timeout) -> NmapResult` (not `scan`, which `WifiRf` has with another signature), `ArpClient.read_arp_table() -> list[ArpEntry]`,
  `NtpClient.read_date() -> datetime | None` and `NetemController.inject_event(event:
  TransientEvent, duration_ms)` — new mandatory members. The iperf pair has two names because
  one class implements both protocols; the window is `window_bytes` (bytes) on the new member
  only. The new members take no free tool-option string. Migration: implement them; make
  `get_url_rules`, `get_memory_utilization`, `start_traffic_sender` /
  `start_traffic_receiver` warn with `warn_renamed(old, new)` and return the record's
  `as_tuple()` / `as_dict()` (a list of `as_dict()` for `get_running_processes` with the
  default `"-A"` on a procps host); make `inject_transient` warn and call
  `inject_event(transient_event(event, **kwargs), duration_ms)`. `read_event_logs` (whose
  output includes unparsable lines), `dns_lookup`, `ping(json_output=True)`, `nmap`,
  `get_arp_table` and `get_date` keep their released output (which the records cannot
  rebuild) and warn. `resolve` and `dns_lookup` refuse `DnsRecordType.OTHER`. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.

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
  value, at construction too (`FirewallRule` and `NatRule` follow); text normalises to its canonical form (`"22, 80"` reads `"22,80"`).
  `SecurityEvent.ts` now raises `ValueError` for text that
  `datetime.fromisoformat` does not parse (released: any string) and `TypeError`
  naming the field for a non-text value; it defaults to `""` (no time), so the fields after it
  take a required-argument placeholder and omitting one still raises
  `TypeError`; a type checker no longer flags a missing `src_ip`, `dst_ip`,
  `protocol`, `action` or `category`. The placeholder reads `<required>`. Static only, no runtime change: unpacking a loosely typed dict
  (for example `L3Rule(**dict[str, str])`) into `L3Rule` or `SecurityEvent` now
  fails type-checking, because `src_ports`, `dst_ports`, `timestamp` and the
  private provenance fields (`_ports_seen`, `_ts_seen`; not API) are keyword
  parameters; type the dict or pass the fields explicitly. Listed in the design
  doc's "Effective now". Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **models** `testprotocols.models:LinkStatus.state`, `LinkHealthReport.state` and
  `AppFlow.category` — now `UplinkState | str` (both link states) and
  `ApplicationCategory | str`, and always hold the enum after construction,
  `replace` and assignment. A link state word that is not an `UplinkState` value
  (released: any string) now raises `ValueError`; the vocabulary is the existing
  `up`, `down`, `degraded` plus `unknown` (a probe with no data), so the words a
  reference implementer returns still work. `AppFlow.category` never raises: an
  unknown word becomes `ApplicationCategory.OTHER` plus `category_raw`, without a
  warning. A plain string naming a member warns and converts. Migration: pass the
  members. Static only: unpacking a loosely typed dict into `AppFlow` fails
  type-checking (`category_raw` and the private `_category_seen` are parameters),
  and `TrafficShapingRule.match` is `Mapping[str, object]` (was `dict[str, Any]`),
  so a reader gets `object` values. Listed in the design doc's "Effective now".
  Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **module attributes** `testprotocols.models:TrafficShapingRule` and
  `VPNPeerStatus` — no longer in `__all__`, so `from testprotocols.models import *`
  does not bind them; reaching them by name still works and warns (see
  *Deprecated*). Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **model** `testprotocols.models:QosRule.match` — now optional (`""`, every
  frame), and text with a repeated term (a VLAN, protocol or port term twice, or
  both the port and the range key of one direction) raises `ValueError`; a non-text
  value raises `TypeError`. Free text stays legal and keeps its spelling; it has no
  classifier. Static only: unpacking a loosely typed dict into `QosRule` fails
  type-checking (`classifier` and the private `_match_seen`). Listed in the design
  doc's "Effective now". Design `docs/architecture/precise-types-design.md` (switch QoS classifier); PR pending.
- **protocol members** `testprotocols.router:Router.get_telemetry` and
  `testprotocols.sdwan_policy_manager:SdwanPolicyManager.apply_policy` — static
  only, no runtime change: `get_telemetry` returns `Mapping[str, float]` (was
  `dict[str, Any]`), so a reader gets `float` values and no longer a `dict`; and
  `apply_policy` takes `dict[str, object]` (was `dict[str, Any]`), so a caller's
  `dict[str, str]` variable no longer type-checks (an implementer's `dict`
  parameter still conforms). An implementer whose declared `get_telemetry` return
  is not `float`-valued (for example `dict[str, object]`) no longer conforms and
  must narrow it. Listed in the design doc's "Effective now". Design `docs/architecture/precise-types-design.md` (telemetry and policy); PR pending.
- **models** `testprotocols.models` `WifiBssConfig` (`band`, `security_mode`, `mfp`),
  `WifiStation.band`, `WifiNeighbor.band`, `WifiChannelUtilization.band`,
  `WifiRadioStats.band`, `WifiMeshLink.band`, `WifiAcl.mode`, `WifiMeshStatus.role` and
  `WifiMeshNode.role` — now enums (`WifiBand`, `WifiSecurityMode`, `MfpMode`,
  `WifiAclMode`, `MeshRole`); a plain string naming a member warns and converts
  (also on assignment and `replace`), and a string that is no member raises
  `ValueError` (released: any string). `WifiStation` gains `capabilities`,
  `capability_flags_unknown` and the private `_caps_seen`, so unpacking a loosely typed
  dict into `WifiStation` fails type-checking (static only). Listed in the design
  doc's "Effective now". Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **protocol members** `WifiBss.create_bss` / `set_security` (`band`, `security_mode`,
  `mfp`; the `mfp` default is `MfpMode.OPTIONAL`, equal to `"optional"`),
  `WifiBss.set_acl_mode`, every `band` of `WifiRadio` and `WifiRf`,
  `WifiRadio.set_bandwidth` (`ChannelWidth | int`), `WifiRadio.set_mode`,
  `WifiMesh.set_backhaul_band` and `WifiClient.set_wlan_scan_channel` (`int | str`) —
  parameter annotations widen to `E | str`, so every released call still type-checks;
  a driver coerces once at the boundary. An `int` for a `ChannelWidth` parameter
  needs no coercion warning. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **protocol member** `testprotocols.sip_server:SipServer.verify_sip_message(message_type, since)` —
  `since` is `datetime | None` (released: `Any`, documented as a timestamp or marker). A
  caller that passed a `datetime` or `None` is unaffected; a caller that passed a text
  marker was outside the typed contract and no longer type-checks (an implementer may
  keep `since: Any`, which still conforms). `message_type` widens to
  `SipMethod | str`: every released call, and every released implementer, still type-checks. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **protocol members** `SipPhone.wait_for_state(state)`, `SipPhone.set_presence(status)` and
  `SipServer.notify_presence(user, status)` — annotations widen to `PhoneState | str` and
  `PresenceStatus | str`, so every released call still type-checks. A presence word that
  names no member is the provider's own word and passes to the device unchanged, with no
  error and no warning; a `wait_for_state` word that names no state raises `ValueError`
  (released implementer: the same). Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **model** `testprotocols.models:HTTPResult` — now a frozen dataclass with `status: int`,
  `body: str` and `raw: str`. `HTTPResult(response)` takes the response text as before
  (keyword `response` too). *status* is `0` when the response has no numeric status code, or
  one outside 100 to 599 (it will become `None`); the released `code` (text) and
  `beautified_text` still read but warn. Equality is now by value (released: by identity). The
  record is frozen: assigning an attribute raises `FrozenInstanceError` (released: allowed),
  and `dataclasses.replace` does not apply (the constructor takes the text). Migration: read
  `status` and `body`. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **models** `MeasurementSpec.tool` and `completion`, `TrafficSpec.protocol`,
  `RadiusAccountingRecord.record_type` and `terminate_cause`, and `QoEResult.protocol` — now
  enums. A plain `str` naming a member warns and converts, also on assignment, so a reader
  holds the member (it compares equal to its text, except `AcctTerminateCause`, a pure
  `Enum`). The intended warnings include the browser's own words in `QoEResult.protocol`
  (`"h2"`, `"h3"`, `"http/1.1"`): a driver builds the member with `coerce_open_enum` instead.
  A word that names no member raises `ValueError` for `MeasurementSpec.tool` / `completion`
  and `TrafficSpec.protocol` (released: free text; the example implementer treated an unknown
  tool as the browser); for `QoEResult.protocol`, `record_type` and `terminate_cause` it
  becomes `OTHER` plus the raw companion, with no error and no warning. `repr()` of a
  `QoeTool` or `QoeCompletion` is the quoted text, so generated text is unchanged; every
  other new enum keeps the default `<Enum.MEMBER: 'x'>` repr (code that builds text with
  `repr(value)` or `{value!r}` must use `str(value)`). Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **protocol members** `DnsClient.dns_lookup(record_type)`, `HttpClient.curl(protocol)`,
  `IperfClient.start_traffic_sender(ip_version)`, `IperfServer.start_traffic_receiver(ip_version)`,
  `IpInterface.set_link_state(state)`, `NmapScanner.nmap(ip_type)`,
  `UpnpClient.create_upnp_rule(protocol)` and `delete_upnp_rule(protocol)` and
  `QoeBrowser.measure_productivity(scenario, wait_until)` — annotations widen to `E | str` (a
  `StrEnum` is a `str`, so every released call and implementer still type-checks) and, for
  `ip_version`, to `IpFamily | int | None` (an `IntEnum` is an `int`, so an implementer that
  declares `int | None` still conforms and still formats `4` / `6`). A plain `str` naming a
  member is deprecated (the driver converts and warns). The numeric-text parameters
  (`HttpServer` `port`, `ip_version`, `UpnpClient` `int_port` / `ext_port`, `VlanClient`
  `vlan_id`) and `IpRouting.traceroute(version)` stay `str`, because released implementers
  declare `str`; they are documented and their narrowing is announced. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **protocol members** `NetemController.set_impairment_profile` / `set_interface_profile`
  (`profile: ImpairmentProfile | dict[str, object]`, was `dict[str, Any]`) and
  `DhcpServer.provision_cpe` (`dhcpv4_options` / `dhcpv6_options: dict[str, dict[str, object]]`,
  was `dict[str, Any]`: a service-pool name to an option-name map, as the released implementer
  reads them) — no `Any`; static only: a caller's loosely typed dict variable no longer
  type-checks, and an implementer declaring `dict` or `dict[str, Any]` still conforms.
  `HeldPrefixes.hold(address)` stays `str` (released implementers declare `str`). Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **models** `DHCPTraceData.dhcp_packet` and `DHCPV6TraceData.dhcpv6_packet` —
  `Mapping[str, object]` (was `dict[str, Any]`): a decoder's nested bag with no fixed typed
  shape; static only, a reader narrows each value it uses. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.

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
- **parameters and fields** `LinkStatus.state`, `LinkHealthReport.state` and
  `AppFlow.category` — a plain `str` naming a member (`"up"`, `"degraded"`,
  `"video_streaming"`) is deprecated: it warns and is converted. The annotations
  narrow to `UplinkState` and `ApplicationCategory` in a later release. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **models** `testprotocols.models.wan_edge:VPNPeerStatus` and
  `TrafficShapingRule` (also reached as `testprotocols.models.VPNPeerStatus` and
  `TrafficShapingRule`) — deprecated with no successor: no capability uses them;
  every access warns, and they are removed in a later release. Use
  `VpnPeerStatus` for site-to-site peers and `ShapingRule` for shaping where a
  capability needs one. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **placeholder** `LinkStatus.ip_address` — announced only: `""` means no
  address today and becomes `str | None` in a later release. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **field** `QosRule.match` — the classifier text; assigning or constructing from
  it warns (free text has no classifier and stays as given). Use `classifier`. Design `docs/architecture/precise-types-design.md` (switch QoS classifier); PR pending.
- **protocol members** `Router.get_telemetry` — deprecated name of
  `Router.read_telemetry` (a driver warns with `warn_renamed` and delegates).
  `SdwanPolicyManager.apply_policy` — deprecated with no successor: the typed
  members (`configure_sla_policy`, `set_uplink_selection`, `set_default_uplink`,
  `set_active_active_vpn`) cover what a policy expresses; the member stays,
  unchanged, until a later release removes it. Design `docs/architecture/precise-types-design.md` (telemetry and policy); PR pending.
- **parameters** `WifiBss` (`band`, `security_mode`, `mfp`, `set_acl_mode(mode)`),
  `WifiRadio` (`band`, `set_mode(mode)`), `WifiRf` (`band`) and
  `WifiMesh.set_backhaul_band` — a plain `str` naming a member (`"5GHz"`,
  `"WPA2-PSK"`, `"required"`, `"deny"`, `"ax"`) is deprecated: it warns and is
  converted. The annotations narrow to the enums in a later release. A compound PHY
  mode (`"n/ac/ax"`), which the released `set_mode` allowed at a driver's discretion,
  names no member and is not coerced by the contract. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **parameter** `WifiClient.set_wlan_scan_channel(channel)` — a numeric `str` is
  deprecated: the driver converts it with `coerce_int` (it warns). Narrows to `int`
  in a later release. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **fields** the Wi-Fi model fields listed under *Changed* — a plain `str` naming a member is deprecated (warns, converts). The
  annotations narrow to the enums in a later release. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **field** `WifiStation.capability_flags` — the released word list; giving or assigning
  it warns. Use `capabilities` and `capability_flags_unknown`. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **protocol member** `WifiClient.iwlist_supported_channels` — deprecated name of
  `supported_channels` (see *Breaking for driver authors*); it keeps its released
  signature (`wifi_band: str`, `list[str]`). Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **return types** `WifiRadio.list_radios`, `get_mode` and `get_bandwidth` — announced
  only: they return `list[str]`, `str` and `int` today and narrow to
  `list[WifiBand]`, `WifiPhyMode` and `ChannelWidth` in a later release (members equal
  their strings and numbers, so comparisons keep working; `get_mode` stays `str`
  until the compound-mode question is settled). Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **protocol members** `SipServer.get_rtpengine_stats`, `get_mwi_status` and
  `get_offline_messages` — deprecated names of `read_rtpengine_stats`, `read_mwi_status`
  and `read_offline_messages` (see *Breaking for driver authors*); they keep their dict
  returns until a later release removes them. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **parameters** `SipPhone.wait_for_state(state)`, `SipPhone.set_presence(status)`,
  `SipServer.notify_presence(user, status)` and `SipServer.verify_sip_message(message_type)`
  — a plain `str` naming a member (`"idle"`, `"away"`, `"INVITE"`) is deprecated: the
  driver converts it with `coerce_enum` or `coerce_open_enum` and warns. A presence or
  method word that names no member is not deprecated (the sets are open). The annotations
  narrow to `PhoneState`, and to `PresenceStatus` / `SipMethod` (and `int`, for a response code) with the raw word
  carried separately, in a later release. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **return type** `SipServer.get_user_presence` — announced only: it returns `str`
  today and narrows to `PresenceStatus` (with the device's own word beside it) in a later
  release; members equal their strings. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **properties** `HTTPResult.code` and `HTTPResult.beautified_text` — deprecated names of
  `status` (an `int`, not text) and `body`; they warn when read and are removed in a
  later release. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **parameters** the `E | str` parameters listed under *Changed*: a plain `str` naming a
  member is deprecated (the driver converts and warns); the annotations narrow to the enums
  in a later release. `ip_version` of the iperf members narrows to `IpFamily | None`. The
  `str` parameters that stay `str` narrow later too: `port`, `int_port`, `ext_port` and
  `vlan_id` to `int`, `start_http_service(ip_version)` to `IpFamily` (`"4"` / `"6"`), and
  `traceroute(version)` (the command suffix `""` or `"6"`) to `IpFamily | None`. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **parameter** `IpInterface.is_link_up(pattern)` — the free-text `ip link` flag list is
  deprecated: a driver warns when it differs from the default `"BROADCAST,MULTICAST,UP"`
  and keeps matching it; use `is_link_admin_up` for the administrative state. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **return type** `RadiusServer.get_status` — announced only: it returns `str` today and
  narrows to `ServiceStatus` (members equal the strings) in a later release. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **field** `RadiusUser.eap_methods` — deprecated word list: giving it warns; use
  `eap_methods_known` and `eap_methods_unknown`. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **fields** `MeasurementSpec`, `TrafficSpec`, `RadiusAccountingRecord` as above: a plain
  `str` for a typed field is deprecated; the annotations narrow to the enums later. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **protocol members** `ContentFiltering.get_url_rules`, `DeviceManagement.get_memory_utilization`,
  `get_running_processes` and `read_event_logs`, `DnsClient.dns_lookup`,
  `IperfClient.start_traffic_sender`, `IperfServer.start_traffic_receiver`,
  `NmapScanner.nmap`, `ArpClient.get_arp_table`, `NtpClient.get_date` and
  `NetemController.inject_transient` — deprecated names of the new members (see *Breaking for
  driver authors*); they keep their released signatures and returns until a later release
  removes them. `IpRouting.ping(json_output=True)` is deprecated: use `ping_stats`. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **parameters** the netem `profile` as a `dict` (use `ImpairmentProfile`; the driver converts
  with `coerce_impairment_profile`, which warns) and a plain tuple in `send_mldv2_report`'s
  records (use `GroupRecord`; the driver converts with `group_records`, which warns). The
  `profile` annotation narrows to `ImpairmentProfile` and the records to
  `Sequence[GroupRecord]` in a later release; `HeldPrefixes.hold` / `release` narrow to
  `IPv4Interface | IPv6Interface` (announced only). Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.

### testoperations

#### Added

- **enum** `testoperations.segmentation:DenyScope` (`HOST`, `SUBNET`) — how wide
  a deny rule built by `build_deny_rule` matches. Migration: pass the member. Design `docs/architecture/precise-types-design.md` (testoperations: segmentation); PR pending.
- **parameter** `testoperations.netem_controller:inject_packet_storm(loss_percent=None)` —
  keyword-only: the share of packets lost during the storm, which the released drivers apply
  for a packet storm. `duplicate_percent` now defaults to `None` (not requested): a
  new-name driver is asked for duplication only when the caller passes it; an old-name driver
  still receives the released `duplicate_percent=100.0`. A packet storm keeps its released
  meaning, a loss burst. Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.

#### Changed

- **operation** `testoperations.segmentation:build_deny_rule` — `scope` is now
  `DenyScope | str` and `proto` `RuleProtocol | str` (shape 1). A plain string
  naming a member warns (`DeprecationWarning`) and converts. The error for an
  unknown scope changes: it is the `coerce_enum` `ValueError` (`scope: 'vlan' is
  not one of ['host', 'subnet']`), still naming `scope`; an unknown `proto` is the
  same kind of `ValueError`, naming `proto`. Migration: pass `DenyScope` and
  `RuleProtocol` members. Design `docs/architecture/precise-types-design.md` (testoperations: segmentation); PR pending.
- **operation** `testoperations.iperf_generator:saturate_link(protocol)` — takes
  `TransportProtocol | str` (default `UDP`) and converts it at its boundary with `coerce_enum`:
  a plain `"udp"` / `"tcp"` warns at the caller; any other word is a `ValueError`. Migration:
  pass `TransportProtocol`. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **operations** `testoperations.throughput:measure_concurrent_throughput` and
  `measure_external_flow` (and the operations built on them), `testoperations.netem_controller`
  `inject_blackout`, `inject_brownout`, `inject_latency_spike`, `inject_packet_storm` and
  `testoperations.sdwan:measure_failover_convergence` — call the new member names
  (`start_sender_session` with the window in bytes, `start_receiver_session`, `inject_event`)
  through `testoperations._renamed`, falling back to the released names; a driver with only
  the released names receives exactly the released call. With a new-name driver, a flow
  `window` that is not an iperf size raises `ValueError` before anything starts. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.

#### Deprecated

- **parameters** `build_deny_rule(scope, proto)` — a plain `str` naming a member
  (`"host"`, `"icmp"`) is deprecated: it warns and is converted. The annotations
  narrow to `DenyScope` and `RuleProtocol` in a later release. Design `docs/architecture/precise-types-design.md` (testoperations: segmentation); PR pending.

#### Fixed

- **operation** `testoperations.http_server:start_http_server` — the default `ip_version`
  was `"ipv4"`, which the released implementers rendered as `webfsd -ipv4`; the server
  command takes `-4` / `-6`. The default is now `"4"` and `ip_version` is documented as `"4"`
  or `"6"`. A caller that passed `"ipv4"` / `"ipv6"` explicitly reaches the same bug and
  should pass `"4"` / `"6"`. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **operation** `testoperations.netem_controller:inject_latency_spike(latency_ms)` — the
  released drivers read a spike's latency as `spike_latency_ms`, so the value was ignored (they
  applied their 500 ms default). With a driver that implements `inject_event` it takes effect;
  an old-name driver still receives the released call (and still ignores it). Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.

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
