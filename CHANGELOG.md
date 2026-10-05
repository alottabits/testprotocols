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

#### Breaking for driver authors

- **protocol members** `testprotocols.snmp_client:SnmpClient.snmp_get(host, oid, community, *,
  timeout_s=10, retries=3, command_timeout=30) -> str`, `snmp_walk(...)` (same parameters,
  `timeout_s=100`; an empty `oid` walks from the root), `snmp_set(host, oid, community, value,
  value_type, *, timeout_s=10, retries=3, command_timeout=30) -> str`, `snmp_bulk_get(host, oid,
  community, *, non_repeaters=0, max_repetitions=10, timeout_s=100, retries=3,
  command_timeout=30) -> str`, and `testprotocols.ntp_client:NtpClient.set_date_time(value:
  datetime) -> bool` — new mandatory members. Migration: implement them (`snmp_get` runs
  `snmpget -v 2c -On -c <community> -t <timeout_s> -r <retries> <host> <oid>`, the others the
  matching `snmpwalk`, `snmpset` and `snmpbulkget` command; `set_date_time` formats `value` for
  the device's `date`); keep `set_date` and `execute_snmp_command` until their removal. Design
  `docs/architecture/precise-types-design.md` (Tool option strings); PR pending.
- **protocol members** `testprotocols.http_client:HttpClient.curl` and `http_get`
  (`no_proxy`, `insecure`, `follow_redirects`) and `testprotocols.nmap_scanner:NmapScanner.nmap`
  (`fast`) — gain keyword-only parameters with defaults. Callers need no change; an
  implementer's declaration without them is reported by the static type checkers (mypy and
  pyright), and a caller that passes one of them to such a driver fails with `TypeError`.
  Migration: add the keyword-only parameters and build the tool's arguments from them;
  passing both the old string and a typed parameter raises `ValueError`. Design `docs/architecture/precise-types-design.md` (Tool option strings); PR pending.
- **protocol members** `testprotocols.packet_filter:PacketFilter.get_rule_counter_values(chain, name) -> RuleCounters`
  and `testprotocols.nat:Nat.get_nat_rule_counter_values(name) -> RuleCounters`
  (so also `Firewall`, which inherits `PacketFilter`) — new mandatory members,
  taking the parameters of the old counter members. Migration: implement them
  and keep `get_rule_counters` / `get_nat_rule_counters` until their removal. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **protocol member** `testprotocols.router:Router.read_telemetry() -> Telemetry` —
  new mandatory member. Migration: implement it, and keep `get_telemetry`, which
  returns the reported fields of `read_telemetry()` as the released mapping. Design `docs/architecture/precise-types-design.md` (telemetry and policy); PR pending.
- **protocol member** `testprotocols.wifi_client:WifiClient.supported_channels(band: WifiBand) -> list[int]` —
  new mandatory member, replacing `iwlist_supported_channels` (which returned the
  channel numbers as text). Migration: implement it;
  `iwlist_supported_channels` returns the same channels as text until its removal.
  Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **protocol members** `testprotocols.sip_server:SipServer.read_rtpengine_stats() -> RtpStats`,
  `read_mwi_status(user) -> MwiStatus` and `read_offline_messages(user) -> list[OfflineMessage]` —
  new mandatory members, replacing `get_rtpengine_stats`, `get_mwi_status` and
  `get_offline_messages` (which return dicts). Migration: implement them, and keep each old name,
  returning the record's fields as the released dict (one dict per offline message). Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **protocol member** `testprotocols.ip_interface:IpInterface.is_link_admin_up(interface) -> bool`
  — new mandatory member: True when the interface is administratively up (the state
  `set_link_state` sets), whether or not a carrier is present. Migration: implement it
  (a Linux host reads the `UP` flag of `ip link show`). Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **protocol members** `ContentFiltering.read_url_rules() -> UrlRules`,
  `DeviceManagement.read_memory_utilization() -> MemoryUtilization`,
  `read_running_processes() -> list[ProcessInfo]` and
  `read_log_entries() -> list[EventLogEntry]`,
  `DnsClient.resolve(domain_name, record_type: DnsRecordType | str) -> list[DnsRecord]`,
  `IperfClient.start_sender_session(host, traffic_port, *, ..., window_bytes) -> IperfProcess`,
  `IperfServer.start_receiver_session(traffic_port, *, ...) -> IperfProcess`,
  `IpRouting.ping_stats(ping_ip, ping_count, ping_interface, timeout) -> PingResult`,
  `NmapScanner.scan_ports(target, ip_version: IpFamily, *, ports, protocol, max_retries,
  min_rate, timeout, fast) -> NmapResult` (not `scan`, which `WifiRf` has with another
  signature), `ArpClient.read_arp_table() -> list[ArpEntry]`,
  `NtpClient.read_date() -> datetime | None` and `NetemController.inject_event(event:
  TransientEvent, duration_ms)` — new mandatory members. The iperf pair has two names because
  one class implements both protocols; the window is `window_bytes` (bytes) on the new member
  only; `scan_ports(fast=True)` scans fewer ports than the default set (an explicit `ports`
  wins). The new members take no free tool-option string. Migration: implement them; keep the old names until their removal:
  `get_url_rules`, `get_memory_utilization`, `start_traffic_sender` /
  `start_traffic_receiver` return the record's fields in the released shape (one dict per process for `get_running_processes` with the
  default `"-A"` on a procps host), and `inject_transient` applies the event `inject_event` would. `read_event_logs` (whose
  output includes unparsable lines), `dns_lookup`, `ping(json_output=True)`, `nmap`,
  `get_arp_table` and `get_date` keep their released output (which the records cannot
  rebuild). Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **field** `testprotocols.models:FirewallRule.dst_port` — now `str | None`, still required
  and in its released position; `None` when the driver fills only `dst_ports`. A reader of
  the field sees `str | None` (read the ports through testoperations, which accepts either
  form). Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **fields** `testprotocols.models:NatRule.dst_port` and `translated_port` — now
  `str | None`, default `None` (released: `""`, no port); `None` means the same as `""`. A
  reader sees `str | None`. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **fields** `testprotocols.models:L3Rule.src_port` and `dst_port` — now `str | None`,
  default `None` (released: `"any"`); `None` means the same as `"any"`. A reader sees
  `str | None`. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **field** `testprotocols.models:SecurityEvent.ts` — now `str | None`, still required and in
  its released position; `None` when the driver fills only `timestamp`. A reader sees
  `str | None`. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **field** `testprotocols.models:QosRule.match` — now `str | None`, still required and in
  its released position; `None` when the driver fills only `classifier`. A reader sees
  `str | None`. Design `docs/architecture/precise-types-design.md` (switch QoS classifier); PR pending.
- **fields** `testprotocols.models:FirewallRule.action` / `protocol`, `NatRule.mode` /
  `protocol`, `PortMapping.protocol`, `Connection.protocol`, `LinkStatus.state` and
  `LinkHealthReport.state`, `TrafficSpec.protocol`, `MeasurementSpec.tool` /
  `completion`, the `band` of `WifiBssConfig`, `WifiStation`, `WifiNeighbor`,
  `WifiChannelUtilization`, `WifiRadioStats` and `WifiMeshLink`,
  `WifiBssConfig.security_mode` / `mfp`, `WifiAcl.mode` and the `role` of
  `WifiMeshStatus` and `WifiMeshNode` — now `E | str` (the enum or its released word,
  stored as given), so a reader sees `E | str`. Design `docs/architecture/precise-types-design.md`; PR pending.

#### Added

- **type checking** mypy now runs `disallow_any_explicit` on `testprotocols.*` and
  `testoperations.*` (internal; the contract is unchanged). The only
  exemptions are released signatures, in two classes: 20 deprecation-period
  exemptions, marked `# type: ignore[explicit-any]  # released signature kept
  until removal` and removed with their members; and 2 compatibility
  exemptions (`flash_via_bootloader`, `start_tcpdump`), marked
  `# released parameter kept: implementers declare their own types`, live
  members whose implementers declare their own types. `tests/test_typing_ratchet.py`
  counts the non-exempt `Any` (ceiling 0) and pins each class. Migration: none. Design `docs/architecture/precise-types-design.md`; no
  proposal (contract infrastructure); PR pending.
- **model** `testprotocols.models:PortRange` (`first`, `last`, inclusive,
  `1 <= first <= last <= 65535`; frozen; `PortRange.single(port)`) — the typed L4
  port range. A typed port field is a tuple of `PortRange`.
  Migration: none. Design `docs/architecture/precise-types-design.md`
  (shape 4(ii)); PR pending.
- **enum** `testprotocols.models:DefaultAction` (`ACCEPT`, `DROP`, `REJECT`) —
  what a chain, zone or zone pair does with traffic no rule decides.
  Migration: none. Design `docs/architecture/precise-types-design.md`;
  PR pending.
- **enums** `testprotocols.models:Chain` (`INPUT`, `OUTPUT`, `FORWARD`),
  `FirewallRuleAction` (`ALLOW`, `DENY`, `REJECT`, `LOG`), `NatMode` (`SNAT`,
  `DNAT`, `ONE_TO_ONE`) and `PortMappingProtocol` (`TCP`, `UDP`, `TCP_UDP`).
  Migration: none. Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.
- **model** `testprotocols.models:RuleCounters` (`packets`, `bytes`: non-negative
  ints; frozen) —
  what a rule has matched since it was added. Migration: none. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **fields** `testprotocols.models:FirewallRule.dst_ports`, `NatRule.dst_ports`
  and `NatRule.translated_ports` — `tuple[PortRange, ...] | None` (keyword-only,
  default `None`), the empty tuple meaning no port restriction: the typed form of
  the deprecated text fields `dst_port` / `translated_port`. A driver fills either
  form, or both, describing the same ports. Migration: pass `PortRange` tuples. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **fields** `testprotocols.models:L3Rule.src_ports` and `dst_ports` —
  `tuple[PortRange, ...] | None` (keyword-only, default `None`), the empty tuple
  meaning any port: the typed form of the deprecated text fields `src_port` /
  `dst_port`. A driver fills either form, or both, describing the same ports.
  Migration: pass `PortRange` tuples. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **field** `testprotocols.models:SecurityEvent.timestamp` — `datetime | None`
  (keyword-only, default `None`; `None`: the product reports no time), the typed
  form of the deprecated ISO-8601 text `ts`. A driver fills either form, or both,
  describing the same instant. A timezone-naive value stays naive. Migration: pass
  `timestamp`. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **enum member** `testprotocols.models:UplinkState.UNKNOWN` (a state the
  product could not determine, such as a link with no health data). Migration: none. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **model** `testprotocols.models:QosClassifier` (`vlan`, `protocol`, `src_ports`,
  `dst_ports`; frozen; every field left out places no restriction; `vlan` is 1 to
  4094) — what a QoS rule selects. **field** `testprotocols.models:QosRule.classifier`
  — `QosClassifier | None` (keyword-only, default `None`; `None`: every frame), the
  typed form of the deprecated text `match`. A driver fills either form, or both,
  describing the same traffic. A rule's classifier holds at most one source and one
  destination port range. Migration: pass `classifier`.
  Design `docs/architecture/precise-types-design.md` (switch QoS classifier); PR pending.
- **model** `testprotocols.models:Telemetry` (`uptime_seconds`, `cpu_load_percent`,
  `mem_used_percent`; frozen; the last two are `None` when the device does not
  report them; each finite and not negative) — a device's
  resource telemetry. Migration: none. Design `docs/architecture/precise-types-design.md` (telemetry and policy); PR pending.
- **enums** `testprotocols.models:WifiBand` (`GHZ_2_4`, `GHZ_5`, `GHZ_6`),
  `WifiSecurityMode` (`OPEN`, `OWE`, `WPA2_PSK`, `WPA2_EAP`, `WPA3_SAE`, `WPA3_EAP`,
  `WPA2_WPA3_PSK_MIXED`, `WPA2_WPA3_EAP_MIXED`), `MfpMode` (`OFF`, `OPTIONAL`,
  `REQUIRED`), `WifiAclMode` (`DISABLED`, `ALLOW`, `DENY`), `WifiPhyMode` (`A`, `B`,
  `G`, `N`, `AC`, `AX`, `BE`), `ChannelWidth` (an `IntEnum`: 20, 40, 80, 160, 320 MHz),
  `MeshRole` (`CONTROLLER`, `AGENT`, `CONTROLLER_AND_AGENT`, `UNCOMMISSIONED`) — the Wi-Fi vocabularies;
  every value is the string the released contract used (`WifiBand.GHZ_5 == "5GHz"`).
  Migration: none. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **enums** `testprotocols.models:PhoneState` (`IDLE`, `DIALING`, `INCALL_DIALING`,
  `RINGING`, `CONNECTED`, `INCALL_CONNECTED`, `HOLD`, `DIALTONE`, `INCALL_DIALTONE`,
  `CALL_ENDED`, `CODE_ENDED`, `CALL_WAITING`, `CONFERENCE`, `BUSY`, `NOT_ANSWERED`;
  one per `is_*` call-state predicate of `SipPhone`; `HOLD == "hold"`) — the voice
  vocabulary; every value is the string the released contract or its implementer used. Migration: none. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **records** `testprotocols.models:RtpStats` (`engaged`, `sessions`), `MwiStatus`
  (`waiting`, `new`, `old`) and `OfflineMessage` (`sender`, `body`, `stored_at`) —
  frozen records for what the SIP server's media relay, message-waiting and offline-message
  readers returned as dicts (counts not negative). A driver parses its stored text into a
  `datetime` for `read_offline_messages`; its deprecated `get_offline_messages` may keep
  returning that original text unchanged. Migration: read the new records. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **enums** `testprotocols.models:IpVersion` (`IPV4 = "ipv4"`, `IPV6 = "ipv6"`; the
  `nmap(ip_type)` words), the `IntEnum` `IpFamily` (`V4 = 4`, `V6 = 6`; the iperf
  `ip_version` numbers), `DnsRecordType` (`A`, `AAAA`, `CNAME`, `MX`, `NS`, `PTR`, `SOA`,
  `SRV`, `TXT`), `HttpScheme` (`HTTP`, `HTTPS`), `LinkAdminState` (`UP`, `DOWN`; not
  `PortAdminState`, whose words are `enabled` / `disabled`), `QoeTool` (`BROWSER`,
  `HTTP_CLIENT`, `WEBRTC`, `TCP_PROBE`), `PageCompletion` (`LOAD`, `DOMCONTENTLOADED`,
  `NETWORKIDLE`, `COMMIT`), `QoeCompletion` (those four and `DURATION`, `RESPONSE`,
  `CONNECT`), `QoeScenario` (`PAGE_LOAD`), `TransportProtocol` (`TCP`, `UDP`), `ServiceStatus`
  (`RUNNING`, `STOPPED`, `ERROR`), `StormControlUnit` (`PERCENT`, `PPS`). Where the
  released contract or an implementer used a word, the member equals it. Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **field** `testprotocols.models:StormControlConfig.unit` (`StormControlUnit | None`,
  default `None`, meaning "as the driver reads it"; released drivers ignore it). Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **models** `testprotocols.models:UrlRules` (`allowed`, `blocked`),
  `MemoryUtilization` (`total_bytes`, `used_bytes`, `free_bytes`, and `shared_bytes`,
  `cache_bytes`, `available_bytes` all given or all `None`; used and free at most total),
  `ProcessInfo` (`pid`, `tty`, `cpu_time: timedelta`, `command`), `EventLogEntry`
  (`timestamp` text, `hostname`, `tag`, `message`, `priority`; `severity`), `DnsRecord`
  (`name`, `record_type`, `ttl`, `data`; `record_type` is the resolver's own word),
  `IperfProcess` (`pid`, `log_file`), `PingResult`
  (`destination`, `transmitted`, `received`, `packet_loss_percent`, `duplicates`, `rtt_*_ms`;
  received at most transmitted, the loss within one point of what they give),
  `NmapResult` (`up`, `addresses`, `ports`) and `NmapPort` (`port`, `protocol:
  TransportProtocol`, `state`, `service`), `ArpEntry` (`address: IPv4Address`, `hw_type`,
  `hw_address`, `flags`, `interface`) — frozen records for the host-tier readers; each
  holds the figures the deprecated reader returned (the released event-log output also holds
  `{"unparsable": line}` entries, which no record holds). Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **enums** `testprotocols.models:SyslogSeverity` (`IntEnum`, RFC 5424 severities 0 to 7),
  `NmapPortState` (nmap's six port states: `open`, `closed`, `filtered`, `unfiltered`,
  `open|filtered`, `closed|filtered`). Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **models** `testprotocols.models:Blackout`, `Brownout(latency_ms, jitter_ms,
  loss_percent)`, `LatencySpike(latency_ms, jitter_ms)`, `PacketStorm(loss_percent, latency_ms,
  jitter_ms, duplicate_percent)` (a burst of loss, as the released implementers apply it;
  `duplicate_percent` is `None`, not requested, unless given), and the union `TransientEvent` — the typed transient impairment events (every field
  optional: `None` is the driver's default; `event_name` gives the released `inject_transient`
  word, whose keyword for a spike's latency is `spike_latency_ms`). Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **model** `testprotocols.models:GroupRecord(sources, group, record_type)` — a `NamedTuple`,
  so it is the released `(sources, group, record_type)` tuple and fits the released
  `MulticastGroupRecord` parameter type. Migration: none.
  Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **marker** `@deprecated` on every deprecated protocol member, model and property (the
  standard marker: `warnings.deprecated` on Python 3.13 and later, `typing_extensions.deprecated`
  before, re-exported by the internal `testprotocols._compat`), with the same sentence as the
  docstring: "Deprecated: use `<new>`. Removal not before the first release 6 months after the
  release that deprecates it." It is passed `category=None`: the deprecation is stated for the
  type checkers and in the docstring, and nothing warns at run time. mypy (error code
  `deprecated`) and pyright (`reportDeprecated`) report each use, which consumers see when their
  checker enables the check. New dependency on Python 3.12: `typing_extensions>=4.5`.
  Migration: none. Design `docs/architecture/precise-types-design.md`; PR pending.

- **protocol** `testprotocols.hw_console:Console` (also `testprotocols.Console`) — the
  interactive text console `HwConsole` hands out: `execute_command(command, /, timeout=-1) ->
  str`, `sendline(text="", /) -> object`, a read-only `before: str | bytes | None` and
  `start_interactive_session()`: the members callers of the returned consoles were seen to use
  that a `pexpect.spawn` subclass can satisfy (checked against `types-pexpect`, a dev
  dependency only). `runtime_checkable`. `expect` and `expect_exact` are not members: a
  console's own pattern types cannot be matched by one contract type, so a caller that
  matches patterns keeps the concrete console type. `sendline` is positional-only, so a
  `Console` cannot be passed to a helper protocol that takes `string` as a named parameter.
  Migration: none. Design `docs/architecture/precise-types-design.md` (HwConsole); PR pending.

#### Changed

- **protocol members** `testprotocols.packet_filter:PacketFilter` (every `chain`
  parameter; `set_default_policy(policy)`), `testprotocols.nat:Nat.list_nat_rules(mode)`
  and `testprotocols.conntrack:Conntrack` (`protocol` on `list_connections`,
  `count_connections`, `get_connection`, `drop_connection`) — now annotated `Chain | str`, `DefaultAction | str`,
  `NatMode | str | None` and `RuleProtocol | str`. A driver converts each once at its boundary. The `state`
  filters stay `str`, the device's own word. An unknown chain, policy, mode or
  protocol raises `ValueError`; a conntrack `protocol` of `any` is refused,
  because no flow has it. Migration: pass the members; a driver adds the annotations and the conversion. Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.
- **models** `testprotocols.models:FirewallRule` (`action`, `protocol`),
  `NatRule` (`mode`, `protocol`), `PortMapping` (`protocol`) and `Connection`
  (`protocol`) — each field is now `Enum | str`: a member or the released word,
  stored as given (a member compares equal to its word); the enums are
  `FirewallRuleAction`, `RuleProtocol`, `NatMode` and `PortMappingProtocol`.
  `NatRule.protocol` keeps its released default `"any"`. `Connection.state` stays a
  `str`, the device's own word. Migration: pass the members. Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.

- **models** `testprotocols.models:LinkStatus.state` and `LinkHealthReport.state` —
  now `UplinkState | str`: a member or the released word, stored as given. The
  vocabulary is the existing `up`, `down`, `degraded` plus `unknown` (a probe with no
  data). Migration: pass the members. Static only:
  `TrafficShapingRule.match` is `Mapping[str, object]` (was `dict[str, Any]`),
  so a reader gets `object` values. Listed in the design doc's "Effective now".
  Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
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
  `WifiMeshNode.role` — now `E | str` (`WifiBand`, `WifiSecurityMode`, `MfpMode`,
  `WifiAclMode`, `MeshRole`): a member or the released word, stored as given. Listed in
  the design doc's "Effective now". Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **protocol members** `WifiBss.create_bss` / `set_security` (`band`, `security_mode`,
  `mfp`; the `mfp` default stays `"optional"`),
  `WifiBss.set_acl_mode`, every `band` of `WifiRadio` and `WifiRf`,
  `WifiRadio.set_bandwidth` (`ChannelWidth | int`), `WifiRadio.set_mode`,
  `WifiMesh.set_backhaul_band` and `WifiClient.set_wlan_scan_channel` (`int | str`) —
  parameter annotations widen to `E | str`, so every released call still type-checks;
  a driver converts once at the boundary. An `int` naming a `ChannelWidth` is that member. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **protocol member** `testprotocols.sip_server:SipServer.verify_sip_message(message_type, since)` —
  `since` is `datetime | None` (released: `Any`, documented as a timestamp or marker). A
  caller that passed a `datetime` or `None` is unaffected; a caller that passed a text
  marker was outside the typed contract and no longer type-checks (an implementer may
  keep `since: Any`, which still conforms). `message_type` stays `str`. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **protocol member** `SipPhone.wait_for_state(state)` — the annotation widens to
  `PhoneState | str`, so every released call still type-checks. A `wait_for_state` word
  that names no state raises `ValueError` (released implementer: the same). The presence
  parameters and return (`set_presence`, `notify_presence`, `get_user_presence`) stay
  `str`, the provider's own word. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **model** `testprotocols.models:HTTPResult` — now a frozen dataclass with `status: int`,
  `body: str` and `raw: str`. `HTTPResult(response)` takes the response text as before
  (keyword `response` too). *status* is `0` when the response has no numeric status code, or
  one outside 100 to 599 (it will become `None`); the released `code` (text) and `beautified_text` still read (deprecated). Equality is now by value (released: by identity). The
  record is frozen: assigning an attribute raises `FrozenInstanceError` (released: allowed),
  and `dataclasses.replace` does not apply (the constructor takes the text). Migration: read
  `status` and `body`. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **models** `MeasurementSpec.tool` and `completion`, and `TrafficSpec.protocol` — now
  `E | str`: a member or the released word, stored as given (a member compares equal to
  its text). `QoEResult.protocol`, `RadiusUser.eap_methods` and
  `RadiusAccountingRecord.record_type` / `terminate_cause` stay `str`, the device's own
  word. The defaults stay the released words
  (`"browser"`, `"networkidle"`, `"udp"`). A new enum keeps the default `<Enum.MEMBER: 'x'>`
  repr: code that builds text with `repr(value)` or `{value!r}` from a member must use
  `str(value)`. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **protocol members** `DnsClient.dns_lookup(record_type)`, `HttpClient.curl(protocol)`,
  `IperfClient.start_traffic_sender(ip_version)`, `IperfServer.start_traffic_receiver(ip_version)`,
  `IpInterface.set_link_state(state)`, `NmapScanner.nmap(ip_type)`,
  `UpnpClient.create_upnp_rule(protocol)` and `delete_upnp_rule(protocol)` and
  `QoeBrowser.measure_productivity(scenario, wait_until)` — annotations widen to `E | str` (a
  `StrEnum` is a `str`, so every released call and implementer still type-checks) and, for
  `ip_version`, to `IpFamily | int | None` (an `IntEnum` is an `int`, so an implementer that
  declares `int | None` still conforms and still formats `4` / `6`). A plain `str` naming a member is deprecated. The numeric-text parameters
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

- **protocol members** `testprotocols.hw_console:HwConsole.get_console(console_name) ->
  Console` (was `Any`) and `get_interactive_consoles() -> Mapping[str, Console]` (was `dict[str,
  Any]`) — no `Any`. Static only. A reader of a returned console sees only the `Console`
  members (`execute_command`, `sendline`, `before`, `start_interactive_session`): a caller that
  uses `expect`, `expect_exact` or other pexpect members keeps the concrete console type or
  narrows; an implementer whose console lacks one of the four no longer conforms, and one that
  returns a `dict` still does. A caller that mutates the returned mapping (for example
  `popitem`) must take `dict(...)` first. `flash_via_bootloader` keeps its released
  `dict[str, Any]` and `Any` parameters. Design `docs/architecture/precise-types-design.md`
  (HwConsole); PR pending.

#### Deprecated

- **parameters** `HttpClient.curl` and `http_get` `options` and `NmapScanner.nmap` `opts` —
  the free option string is deprecated in favour of the typed keyword-only parameters (see
  *Breaking for driver authors*; on `nmap`, `fast` replaces `-F` and any other `opts` has no
  typed successor); giving both forms raises `ValueError`. `IpRouting.ping` and `traceroute` `options`, `DnsClient.dns_lookup`
  `opts` and a `DeviceManagement.get_running_processes` `ps_options` other than `"-A"` are
  deprecated with no typed replacement (no caller was seen to pass one through these members).
  All keep their released types and positions until a
  later release removes them. Design `docs/architecture/precise-types-design.md` (Tool option strings); PR pending.
- **protocol members** `NtpClient.set_date` (use `set_date_time`) and
  `SnmpClient.execute_snmp_command` (use `snmp_get`, `snmp_walk`, `snmp_set` or
  `snmp_bulk_get`; no successor for any other command) — deprecated; they stay until a later release removes them. Design `docs/architecture/precise-types-design.md` (Tool option strings); PR pending.
- **parameters and fields** `PacketFilter` (`chain`, `set_default_policy(policy)`),
  `Nat.list_nat_rules(mode)`, `Conntrack` (`protocol`), `FirewallRule.action` /
  `protocol`, `NatRule.mode` / `protocol`, `PortMapping.protocol` and
  `Connection.protocol` — a plain `str` naming a member (`"FORWARD"`,
  `"drop"`, `"snat"`, `"tcp"`, `"allow"`, `"tcp-udp"`) is
  deprecated; a field stores it as given.
  The annotations narrow to the enums in
  a later release. Use `Chain`, `DefaultAction`, `NatMode`, `RuleProtocol`,
  `FirewallRuleAction` and `PortMappingProtocol`. Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.
- **return type** `PacketFilter.get_default_policy` — announced only: it returns
  `str` today and narrows to `DefaultAction` in a later release (a
  `DefaultAction` is a `str`, so comparisons with the plain words keep working).
  Design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR pending.
- **fields** `FirewallRule.dst_port`, `NatRule.dst_port` and
  `NatRule.translated_port` — the port text. A driver fills `dst_ports` /
  `translated_ports`, or both forms; at removal the text fields go and the typed
  fields become required. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **protocol members** `PacketFilter.get_rule_counters` and
  `Nat.get_nat_rule_counters` — deprecated names of `get_rule_counter_values` and
  `get_nat_rule_counter_values`; they return `RuleCounters` from the new names.
  Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **placeholders** `NatRule.src_cidr`, `dst_cidr`, `translated_src` and
  `translated_dst` — announced only: `""` means absent today and becomes `None`
  in a later release. Design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR pending.
- **fields** `L3Rule.src_port` and `dst_port`, `SecurityEvent.ts` — the port and
  timestamp text. A driver fills `src_ports` / `dst_ports` and `timestamp`, or both
  forms; at removal the text fields go and the typed fields become required. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **placeholders** `L3Rule.src_cidr` and `dst_cidr` (`"any"`),
  `UplinkStatus.ip`, `gateway`, `public_ip` and `primary_dns` (`""`), and
  `NetworkAttachment.segment` (`""`) — announced only: they mean
  unconstrained or not reported today and become `str | None` (`None`) in a
  later release. Design `docs/architecture/precise-types-design.md` (SD-WAN models); PR pending.
- **parameters and fields** `LinkStatus.state` and `LinkHealthReport.state` — a plain
  `str` naming a member (`"up"`, `"degraded"`) is deprecated; it is stored as given.
  The annotations narrow to `UplinkState` in a later release. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **models** `testprotocols.models.wan_edge:VPNPeerStatus` and
  `TrafficShapingRule` (also reached as `testprotocols.models.VPNPeerStatus` and
  `TrafficShapingRule`) — deprecated with no successor: no capability uses them;
  they carry the `@deprecated` marker and are removed in a later release. Use
  `VpnPeerStatus` for site-to-site peers and `ShapingRule` for shaping where a
  capability needs one. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **placeholder** `LinkStatus.ip_address` — announced only: `""` means no
  address today and becomes `str | None` in a later release. Design `docs/architecture/precise-types-design.md` (WAN-edge models); PR pending.
- **field** `QosRule.match` — the classifier text. A driver fills `classifier`, or
  both forms; at removal the text field goes and `classifier` becomes required. Design `docs/architecture/precise-types-design.md` (switch QoS classifier); PR pending.
- **protocol members** `Router.get_telemetry` — deprecated name of
  `Router.read_telemetry`.
  `SdwanPolicyManager.apply_policy` — deprecated with no successor: the typed
  members (`configure_sla_policy`, `set_uplink_selection`, `set_default_uplink`,
  `set_active_active_vpn`) cover what a policy expresses; the member stays,
  unchanged, until a later release removes it. Design `docs/architecture/precise-types-design.md` (telemetry and policy); PR pending.
- **parameters** `WifiBss` (`band`, `security_mode`, `mfp`, `set_acl_mode(mode)`),
  `WifiRadio` (`band`, `set_mode(mode)`), `WifiRf` (`band`) and
  `WifiMesh.set_backhaul_band` — a plain `str` naming a member (`"5GHz"`,
  `"WPA2-PSK"`, `"required"`, `"deny"`, `"ax"`) is deprecated. The annotations narrow to the enums in a later release. A compound PHY
  mode (`"n/ac/ax"`), which the released `set_mode` allowed at a driver's discretion,
  names no member. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **parameter** `WifiClient.set_wlan_scan_channel(channel)` — a numeric `str` is
  deprecated. Narrows to `int`
  in a later release. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
- **fields** the Wi-Fi model fields listed under *Changed* — a plain `str` naming a member is deprecated; it is stored as given. The
  annotations narrow to the enums in a later release. Design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR pending.
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
  — a plain `str` naming a `PhoneState` member (`"idle"`) is deprecated for `wait_for_state`. The presence
  and message-type words are the provider's own and stay `str`. The `wait_for_state`
  annotation narrows to `PhoneState` in a later release. Design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR pending.
- **properties** `HTTPResult.code` and `HTTPResult.beautified_text` — deprecated names of
  `status` (an `int`, not text) and `body`; they carry the `@deprecated` marker and are removed in a later release. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **parameters** the `E | str` parameters listed under *Changed*: a plain `str` naming a
  member is deprecated; the annotations narrow to the enums
  in a later release. `ip_version` of the iperf members narrows to `IpFamily | None`. The
  `str` parameters that stay `str` narrow later too: `port`, `int_port`, `ext_port` and
  `vlan_id` to `int`, `start_http_service(ip_version)` to `IpFamily` (`"4"` / `"6"`), and
  `traceroute(version)` (the command suffix `""` or `"6"`) to `IpFamily | None`. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **parameter** `IpInterface.is_link_up(pattern)` — the free-text `ip link` flag list is
  deprecated: a driver keeps matching it; use `is_link_admin_up` for the administrative state. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **return type** `RadiusServer.get_status` — announced only: it returns `str` today and
  narrows to `ServiceStatus` (members equal the strings) in a later release. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **fields** `MeasurementSpec` and `TrafficSpec` as above: a plain
  `str` for a typed field is deprecated; the annotations narrow to the enums later. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **protocol members** `ContentFiltering.get_url_rules`, `DeviceManagement.get_memory_utilization`,
  `get_running_processes` and `read_event_logs`, `DnsClient.dns_lookup`,
  `IperfClient.start_traffic_sender`, `IperfServer.start_traffic_receiver`,
  `NmapScanner.nmap`, `ArpClient.get_arp_table`, `NtpClient.get_date` and
  `NetemController.inject_transient` — deprecated names of the new members (see *Breaking for
  driver authors*); they keep their released signatures and returns until a later release
  removes them. `IpRouting.ping(json_output=True)` is deprecated: use `ping_stats`. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **parameters** the netem `profile` as a `dict` (use `ImpairmentProfile`) and a plain tuple in `send_mldv2_report`'s
  records (use `GroupRecord`). The
  `profile` annotation narrows to `ImpairmentProfile` and the records to
  `Sequence[GroupRecord]` in a later release; `HeldPrefixes.hold` / `release` narrow to
  `IPv4Interface | IPv6Interface` (announced only). Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.

### testoperations

#### Added

- **internal module** `testoperations._compat` — reads a record field that has a released
  text form and a typed form (`FirewallRule`, `NatRule` and `L3Rule` ports,
  `SecurityEvent` time, `QosRule` classifier) the same way whichever form the driver
  filled: the typed field, else the text parsed, else the released default's meaning (or
  `ValueError` naming the record and field when the released field was required and the
  typed field cannot hold `None` as a value: `FirewallRule.dst_port`). `SecurityEvent` and
  `QosRule` are the exception: their typed fields hold `None` as a value (no time reported;
  every frame), so a record with neither form filled reads as `None`. It also holds
  the parsers of those text forms (ports, timestamps, the QoS classifier text) and of the
  iperf window size, and `coerce_enum`, which converts an operation's own released `str`
  parameter to its enum (a plain string naming a member warns at the operation's caller). Not public API. Migration: none. Design
  `docs/architecture/precise-types-design.md`; PR pending.
- **enum** `testoperations.segmentation:DenyScope` (`HOST`, `SUBNET`) — how wide
  a deny rule built by `build_deny_rule` matches. Migration: pass the member. Design `docs/architecture/precise-types-design.md` (Segmentation deny scope); PR pending.
- **parameter** `testoperations.netem_controller:inject_packet_storm(loss_percent=None)` —
  keyword-only: the share of packets lost during the storm, which the released drivers apply
  for a packet storm. `duplicate_percent` now defaults to `None` (not requested): a
  new-name driver is asked for duplication only when the caller passes it; an old-name driver
  still receives the released `duplicate_percent=100.0`. A packet storm keeps its released
  meaning, a loss burst. Migration: none. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **records** `testoperations.iperf_client:IperfSession` (`sender`, `receiver`: each an
  `IperfProcess`), `testoperations.homing:HomeVerification` (`vlan_defined`,
  `subnet_advertised`, `peers_reachable`, `details`) with `HomeDetails` (`defined_subnet`,
  `defined_gateway`, `peer_states`: peer name to `VpnPeerState`), and
  `testoperations.iperf_generator:FlowPair` (`a_to_b`, `b_to_a`) — frozen records replacing
  the released `dict` returns of `start_iperf`, `verify_home` and `saturate_link`. Each keeps
  the released dict readable for the deprecation period (see *Deprecated*). Migration: read the
  fields. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **enum** `testoperations.netem_controller:NetemPreset` (`CLEAN`, `DSL`, `CABLE`, `LTE`,
  `THREE_G` = `"3g"`, `SATELLITE`, `DEGRADED`, `LOSSY`) — the built-in presets `apply_preset`
  knows. Migration: pass the member. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **enums** `testoperations.throughput:NonCompletionSide` (`ENDPOINT`, `LOCAL_RECEIVER`,
  `UNKNOWN`) and `NonCompletionKind` (`ERROR_DOCUMENT`, `NO_COMPLETED_SESSION`) — replace the
  `Literal` aliases of the same names, with the same text values. Migration: none for a reader
  (`exc.which_side == "endpoint"` still holds); pass the member to `NonCompletion`. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **protocol** `testoperations.throughput:MeasureFn` — the call shape of the `measure`
  parameters of `measure_path_rtt`, `measure_one_direction`, `measure_path_until` (and
  the private `_probe_flow`) (the flows and the three keyword-only timings), replacing
  `Callable[..., list[FlowThroughput]]`. Migration: none; a stand-in that takes those keywords
  fits. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.

#### Changed

- **operation** `testoperations.throughput:measure_external_path_until` — the
  `measure_flow` annotation narrows from `Callable[..., FlowThroughput]` to a call
  protocol: `(flow: ExternalFlow, /, *, duration_s: int, result_timeout_s: float,
  poll_interval_s: float) -> FlowThroughput`. Migration: a stand-in takes the flow
  (positional) plus the three keyword timings; the default is unchanged. Design
  `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **operation** `testoperations.segmentation:build_deny_rule` — `scope` is now
  `DenyScope | str` and `proto` `RuleProtocol | str` (shape 1). A plain string
  naming a member warns (`DeprecationWarning`) and converts. The error for an
  unknown scope changes: it is the `coerce_enum` `ValueError` (`scope: 'vlan' is
  not one of ['host', 'subnet']`), still naming `scope`; an unknown `proto` is the
  same kind of `ValueError`, naming `proto`. The rule fills both port forms
  (`"any"` and the empty tuple). Migration: pass `DenyScope` and
  `RuleProtocol` members. Design `docs/architecture/precise-types-design.md` (Segmentation deny scope); PR pending.
- **operation** `testoperations.iperf_generator:saturate_link(protocol)` — takes
  `TransportProtocol | str` (default `"udp"`, as released) and converts it at its boundary with
  `coerce_enum`: a plain `"udp"` / `"tcp"` the caller passes warns at the caller, a call that
  leaves `protocol` out does not; any other word is a `ValueError`. Migration:
  pass `TransportProtocol`. Design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR pending.
- **operations** `testoperations.throughput:measure_concurrent_throughput` and
  `measure_external_flow` (and the operations built on them), `testoperations.netem_controller`
  `inject_blackout`, `inject_brownout`, `inject_latency_spike`, `inject_packet_storm` and
  `testoperations.sdwan:measure_failover_convergence` — call the new member names
  (`start_sender_session` with the window in bytes, `start_receiver_session`, `inject_event`)
  through `testoperations._renamed`, falling back to the released names; a driver with only
  the released names receives exactly the released call. With a new-name driver, a flow
  `window` that is not an iperf size raises `ValueError` before anything starts. Design `docs/architecture/precise-types-design.md` (Host-tier records); PR pending.
- **operation** `testoperations.iperf_client:start_iperf` — breaking for callers: gains the
  required keyword-only `host` (the address the sender connects to), returns an `IperfSession`
  (was `dict[str, Any]`), and takes `iperf_client: IperfClient` and `iperf_server: IperfServer`
  (were `Any`). The released operation called `start_sender` / `start_receiver`, which no
  capability protocol declares and no driver in the consumer examples, the corpus or boardfarm
  implements, and it could not name the receiver's address; it now calls `start_receiver_session`
  / `start_sender_session` (or the released `start_traffic_receiver` / `start_traffic_sender` on
  a driver that has only those). `ip_version` is `IpFamily | int` (default `4`, as released): `4` and
  `6` are accepted as numbers, any other value is a `ValueError` (released: passed through).
  Migration: pass `host=`; read the record's fields. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **operation** `testoperations.iperf_client:sender_life_record(iperf_client)` — typed
  `IperfClient` (was `Any`); behaviour unchanged. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **operation** `testoperations.homing:verify_home` — returns a `HomeVerification` (was
  `dict[str, object]`); the released keys still read through it with a `DeprecationWarning`.
  Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **operation** `testoperations.iperf_generator:saturate_link` — returns a `FlowPair` (was
  `dict[str, str]`); the released keys still read through it with a `DeprecationWarning`. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **operation** `testoperations.netem_controller:apply_preset(preset_name)` — takes
  `NetemPreset | str` (shape 1). A plain string naming a preset warns and converts. The error
  for an unknown name is the `coerce_enum` `ValueError` (`apply_preset(preset_name): 'x' is not
  one of [...]`), not `unknown preset 'x'; available: [...]`. Migration: pass `NetemPreset`.
  Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **class** `testoperations.throughput:NonCompletion` — `which_side` and `what` take
  `NonCompletionSide | str` and `NonCompletionKind | str` (shape 1): a plain string naming a
  member warns and converts, any other word is a `ValueError`; the attributes are the enum
  members (equal to the released text). The message text is unchanged. Migration: pass the
  members. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **function** `testoperations.throughput:iter_json_docs` — returns `list[object]` (was
  `list[Any]`); a caller indexing a document narrows it first. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.

#### Deprecated

- **parameters** `build_deny_rule(scope, proto)` — a plain `str` naming a member
  (`"host"`, `"icmp"`) is deprecated: it warns and is converted. The annotations
  narrow to `DenyScope` and `RuleProtocol` in a later release. Design `docs/architecture/precise-types-design.md` (Segmentation deny scope); PR pending.
- **access** reading `IperfSession`, `HomeVerification` or `FlowPair` as the released dict —
  `result["sender_pid"]`, `result["vlan_defined"]`, `result["a_to_b"]`, `.get`, `in`, `len`,
  `keys`, `items`, `values`, iteration, `dict(result)`, `**result` (a conversion warns once for `keys()` and once per key read), `==` against the released dict, and `as_dict()` — warns
  (`DeprecationWarning`) and returns the released values (for `verify_home`, `details` is the
  released nested dict with the peer states as text). Truthiness (`if result:`) does not warn:
  a record is always true, as the released dict with its keys was. Static types narrow: the records are not a
  `Mapping` and `[]` / `get` return `object`, so a typed caller needs the fields or `as_dict()`. The mapping access is removed in a later
  release; read the fields. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.
- **parameters** `apply_preset(preset_name)` and `NonCompletion(which_side, what)` — a plain
  `str` naming a member is deprecated: it warns and is converted; the annotations narrow to the
  enums in a later release. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.

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
- **operation** `testoperations.pcap_capture:tcpdump` — typed `PcapCapture` (was `Any`) and
  calls `start_tcpdump(interface, None, output_file=fname, additional_filters=filters or "")`,
  stopping the capture with the process id the start returned. The released operation called
  `start_tcpdump(fname, interface, ...)` (the file name as the interface) and
  `stop_tcpdump(fname)`, which does not match the protocol's signature. Design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR pending.

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
