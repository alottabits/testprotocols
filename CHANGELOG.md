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
  value_type: SnmpValueType, *, timeout_s=10, retries=3, command_timeout=30) -> str`, `snmp_bulk_get(host, oid,
  community, *, non_repeaters=0, max_repetitions=10, timeout_s=100, retries=3,
  command_timeout=30) -> str`, and `testprotocols.ntp_client:NtpClient.set_date_time(value:
  datetime) -> bool` — new mandatory members. Migration: implement them (the first runs
  `snmpget -v 2c -On -c <community> -t <timeout_s> -r <retries> <host> <oid>`, the others the
  matching `snmpwalk`, `snmpset` and `snmpbulkget` command; the NTP member formats `value` for
  the device's `date`); keep `set_date` and `execute_snmp_command` until their removal.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P9;
  design `docs/architecture/precise-types-design.md` (Tool option strings); PR #73.
- **parameters** `testprotocols.http_client:HttpClient.curl(..., *, no_proxy: bool = False,
  insecure: bool = False, follow_redirects: bool = False)`, `HttpClient.http_get(..., *,
  no_proxy: bool = False, insecure: bool = False, follow_redirects: bool = False)` and
  `testprotocols.nmap_scanner:NmapScanner.nmap(..., *, fast: bool = False)` — new keyword-only
  parameters with defaults on released members; they replace the deprecated free option
  strings (`options`, `opts`). Every released call still type-checks. Cost: a released
  implementer's declaration without them no longer conforms statically on upgrade, and a
  caller that passes one of them to such a driver fails with `TypeError`; there is no
  deprecation period for the declaration. Migration: add the keyword-only parameters to the
  implementation's signature (with the protocol's defaults); a declaration without them is
  reported by the checkers. The driver builds the tool's arguments from them; passing both the
  old string and a typed parameter raises `ValueError`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md` (Tool option strings); PR #73.
- **protocol members** `testprotocols.packet_filter:PacketFilter.get_rule_counter_values(chain, name) -> RuleCounters`
  and `testprotocols.nat:Nat.get_nat_rule_counter_values(name) -> RuleCounters`
  (so also `Firewall`, which inherits `PacketFilter`) — new mandatory members,
  taking the parameters of the old counter members. Migration: implement them
  (a driver without per-rule counters adds a one-line stub raising `NotSupportedError`) and
  keep `get_rule_counters` / `get_nat_rule_counters`, with their released
  `NotImplementedError` text, until their removal.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR #73.
- **protocol member** `testprotocols.router:Router.read_telemetry() -> Telemetry` —
  new mandatory member. Migration: implement it, and keep `get_telemetry`, which keeps its
  released `dict[str, Any]` return and returns the reported fields of the new member.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P4;
  design `docs/architecture/precise-types-design.md` (telemetry and policy); PR #73.
- **protocol member** `testprotocols.wifi_client:WifiClient.supported_channels(band: WifiBand) -> list[int]` —
  new mandatory member, replacing `iwlist_supported_channels` (which returned the
  channel numbers as text). Migration: implement it;
  `iwlist_supported_channels` returns the same channels as text until its removal.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR #73.
- **protocol member** `testprotocols.sip_server:SipServer.read_rtp_relay_stats() -> RtpStats` —
  new mandatory member, replacing `get_rtpengine_stats` (which returns a dict). Migration:
  implement it, and keep `get_rtpengine_stats`, returning the record's fields as the released
  dict. Proposal `docs/proposals/2026-10-05-precise-types.md` P7 (Design delta 2026-10-05);
  design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR #73;
  *proposed as* `testprotocols.sip_server:SipServer.read_rtpengine_stats`.
- **protocol members** `testprotocols.sip_server:SipServer.read_mwi_status(user) -> MwiStatus` and
  `read_offline_messages(user) -> list[OfflineMessage]` —
  new mandatory members, replacing `get_mwi_status` and
  `get_offline_messages` (which return dicts). Migration: implement them, and keep each old name,
  returning the record's fields as the released dict (one dict per offline message).
  Proposal `docs/proposals/2026-10-05-precise-types.md` P7;
  design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR #73.
- **protocol member** `testprotocols.wifi_radio:WifiRadio.get_modes(band: WifiBand | str) ->
  frozenset[WifiPhyMode]` — new mandatory member, replacing `get_mode`: a radio operates a set of
  802.11 PHY modes at once (TR-181 `Device.WiFi.Radio.{i}.OperatingStandards` is a list), which
  one `str` cannot report. Migration: implement it; keep `get_mode`, returning the released
  `str`, until its removal.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md` (Wi-Fi
  vocabularies); PR #73.
- **protocol member** `testprotocols.ip_interface:IpInterface.is_link_admin_up(interface) -> bool`
  — new mandatory member: True when the interface is administratively up (the state
  `set_link_state` sets), whether or not a carrier is present. Migration: implement it
  (a Linux host reads the `UP` flag of `ip link show`).
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR #73.
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
  only; with `fast=True` the scan covers fewer ports than the default set (an explicit `ports`
  wins). The new members take no free tool-option string. Migration: implement them; keep the old names until their removal:
  `get_url_rules`, `get_memory_utilization`, `start_traffic_sender` /
  `start_traffic_receiver` return the record's fields in the released shape (one dict per process for `get_running_processes` with the
  default `"-A"` on a procps host), and `inject_transient` applies the event the new member would. `read_event_logs` (whose
  output includes unparsable lines), `dns_lookup`, `ping(json_output=True)`, `nmap`,
  `get_arp_table` and `get_date` keep their released output (which the records cannot
  rebuild).
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8, P9, P10 and P11;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.
- **field** `testprotocols.models:FirewallRule.dst_port` — now `str | None`, still required
  and in its released position; `None` when the producer fills only `dst_ports`. A reader of
  the field sees `str | None`. Read the pair as: `dst_ports` when filled, else `dst_port`
  parsed, else `ValueError` (neither form filled). Write: a caller building a rule for
  `PacketFilter.add_rule` fills both forms until removal, because a driver not yet updated
  reads only `dst_port`; a driver implementing the member reads `dst_ports` when filled,
  else `dst_port`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR #73.
- **fields** `testprotocols.models:NatRule.dst_port` and `translated_port` — now
  `str | None`; the default stays the released `""` (no port), and `None` passed explicitly
  reads as `""`. A reader sees `str | None`. Read a pair as: the typed form when filled, else
  the text, else (text `None`) `""`. Write: a caller building a rule for `Nat.add_nat_rule`
  fills both forms until removal, because a driver not yet updated reads only the text; a
  driver implementing the member reads the typed form when filled, else the text. A caller
  that fills only the typed form leaves the text at `""`, and a driver not yet updated acts
  on that: no port.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR #73.
- **fields** `testprotocols.models:L3Rule.src_port` and `dst_port` — now `str | None`; the
  default stays the released `"any"`, and `None` passed explicitly reads as `"any"`. A reader
  sees `str | None`. Read a pair as: the typed form when filled, else the text, else (text
  `None`) `"any"`. Write: a caller building rules for the `L3Firewall.set_*_rules` members
  fills both forms until removal, because a driver not yet updated reads only the text; a
  driver implementing the members reads the typed form when filled, else the text. A caller
  that fills only the typed form leaves the text at `"any"`, and a driver not yet updated
  acts on that: any port.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P3;
  design `docs/architecture/precise-types-design.md` (SD-WAN models); PR #73.
- **field** `testprotocols.models:SecurityEvent.ts` — now `str | None`, still required and in
  its released position; `None` when the driver fills only `timestamp`. A reader sees
  `str | None`. Read the pair as: `timestamp` when filled, else `ts` parsed (`""`: no time),
  else `None` (no time reported: the typed form holds `None` as a value).
  Proposal `docs/proposals/2026-10-05-precise-types.md` P3;
  design `docs/architecture/precise-types-design.md` (SD-WAN models); PR #73.
- **field** `testprotocols.models:QosRule.match` — now `str | None`, still required and in
  its released position; `None` when the producer fills only `classifier`. A reader sees
  `str | None`. Read the pair as: `classifier` when filled, else `match` parsed, else `None`
  (every frame: the typed form holds `None` as a value). Write: a caller building rules for
  `SwitchQos.set_rules` fills both forms until removal, because a driver not yet updated
  reads only `match`; a driver implementing the member reads `classifier` when filled, else
  `match`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P5;
  design `docs/architecture/precise-types-design.md` (switch QoS classifier); PR #73.
- **fields** `testprotocols.models:FirewallRule.action` / `protocol`, `NatRule.mode` /
  `protocol`, `PortMapping.protocol`, `Connection.protocol`, `LinkStatus.state` and
  `LinkHealthReport.state`, `TrafficSpec.protocol`, `MeasurementSpec.tool` /
  `completion`, the `band` of `WifiBssConfig`, `WifiStation`, `WifiNeighbor`,
  `WifiChannelUtilization`, `WifiRadioStats` and `WifiMeshLink`,
  `WifiBssConfig.security_mode` / `mfp`, `WifiAcl.mode` and the `role` of
  `WifiMeshStatus` and `WifiMeshNode` — now `E | str` (the enum or its released word,
  stored as given), so a reader sees `E | str`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2, P4, P6 and P10;
  design `docs/architecture/precise-types-design.md`; PR #73.
- **fields** `testprotocols.models:WifiRadioStats.tx_retries` and `tx_failed` — now
  `int | None` (released: `int`), still required and in their released positions; `None` when
  the device reports no per-radio count (TR-181 and Wi-Fi Data Elements define none, and not
  every access-point API reports one), never `0` as a stand-in. A reader now sees `int | None`
  and handles `None`. A type change of a released field with no deprecation period, under the
  stated no-period exception (no form of the released field can be kept: an `int` cannot say
  "not reported"). Migration: readers check for `None`; a driver whose device reports no
  per-radio count fills `None`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md` (The
  contract model, "The no-period exception"; Wi-Fi vocabularies); PR #73.
- **parameter** `testprotocols.multicast_client:MulticastClient.send_mldv2_report(mcast_group_record)`
  — now `Sequence[tuple[list[McastSource], McastGroup, MulticastGroupRecordType]]` (released:
  `MulticastGroupRecord`, an invariant `list` of that tuple), so a caller's `list[GroupRecord]`
  type-checks as well as the released list of tuples. Every released call still type-checks.
  Cost: an implementer declaring the parameter as `list[...]` (or `MulticastGroupRecord`) no
  longer conforms statically, because a protocol parameter wider than the implementer's is a
  conformance error; nothing changes at run time. Migration: widen the declaration to
  `Sequence[...]`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.

#### Added

- **enum** `testprotocols.models.SnmpValueType` (`integer`, `unsigned`, `octet-string`,
  `object-identifier`, `ip-address`, `timeticks`, `bits`) — the SNMP value type of a SET;
  `SnmpClient.snmp_set` takes it as `value_type`, and a driver maps each member to its tool's
  own type code. Counter types are left out (a counter only increments, RFC 2578).
  Proposal `docs/proposals/2026-10-05-precise-types.md` P9;
  design `docs/architecture/precise-types-design.md` (Tool option strings); PR #73.
- **type checking** mypy now runs `disallow_any_explicit` on `testprotocols.*` and
  `testoperations.*` (internal; the contract is unchanged). The only
  exemptions are released signatures, in two classes, all in `testprotocols`
  (`testoperations` has none): 10 deprecation-period exemptions, marked
  `# type: ignore[explicit-any]  # released signature kept until removal` and removed
  with their members or forms (the announced `SipServer.verify_sip_message(since)`
  narrowing among them); and 16 compatibility
  exemptions on live members: `flash_via_bootloader` and `start_tcpdump`, marked
  `# released parameter kept: implementers declare their own types`, the 12
  TR-069 RPCs of `Tr069Server`, marked `# released signature kept: vendors extend the
  parameter model`, and the `HwConsole.get_console` / `get_interactive_consoles` returns,
  marked `# released return kept: implementers return their own types`.
  `tests/test_typing_ratchet.py` counts the non-exempt `Any` (ceiling 0) and pins each class.
  It counts `object` used as a type in a public parameter, return, field or type alias the
  same way (ceiling 0): 4 lines in `testprotocols` and 6 in `testoperations` are a deprecated
  form, marked `# object: deprecated form kept until removal`, and 3 in `testprotocols` are a
  live open value, marked `# object: open value: the contract does not enumerate it`.
  Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P1;
  design `docs/architecture/precise-types-design.md` (Exemption policy); PR #73.
- **model** `testprotocols.models:PortRange` (`first`, `last`, inclusive,
  `1 <= first <= last <= 65535`; frozen; `PortRange.single(port)`) — the typed L4
  port range. A typed port field is a tuple of `PortRange`.
  Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`
  (Text and typed fields: either form); PR #73.
- **enum** `testprotocols.models:DefaultAction` (`ACCEPT`, `DROP`, `REJECT`) —
  what a chain, zone or zone pair does with traffic no rule decides.
  Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`;
  PR #73.
- **enums** `testprotocols.models:Chain` (`INPUT`, `OUTPUT`, `FORWARD`),
  `FirewallRuleAction` (`ALLOW`, `DENY`, `REJECT`, `LOG`, `ALERT`), `NatMode` (`SNAT`,
  `DNAT`, `ONE_TO_ONE`) and `PortMappingProtocol` (`TCP`, `UDP`, `TCP_UDP`).
  Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR #73.
- **member** `testprotocols.models:FirewallRuleAction.ALERT` (`"alert"`) — the action value a
  released implementer reports for `FirewallRule.action` beside the documented four, so the
  value stays valid when `FirewallRuleAction | str` narrows to `FirewallRuleAction`.
  Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR #73.
- **model** `testprotocols.models:RuleCounters` (`packets`, `bytes`: non-negative
  ints; frozen) —
  what a rule has matched since it was added. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR #73.
- **fields** `testprotocols.models:FirewallRule.dst_ports`, `NatRule.dst_ports`
  and `NatRule.translated_ports` — `tuple[PortRange, ...] | None` (keyword-only,
  default `None`), the empty tuple meaning no port restriction: the typed form of
  the deprecated text fields `dst_port` / `translated_port`. A driver fills either
  form, or both, describing the same ports. Migration: pass `PortRange` tuples; a caller
  passing a rule to a write member fills the text form too until removal.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md` (firewall and NAT ports and counters); PR #73.
- **fields** `testprotocols.models:L3Rule.src_ports` and `dst_ports` —
  `tuple[PortRange, ...] | None` (keyword-only, default `None`), the empty tuple
  meaning any port: the typed form of the deprecated text fields `src_port` /
  `dst_port`. A driver fills either form, or both, describing the same ports.
  Migration: pass `PortRange` tuples; a caller passing a rule to a write member fills the
  text form too until removal.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P3;
  design `docs/architecture/precise-types-design.md` (SD-WAN models); PR #73.
- **field** `testprotocols.models:SecurityEvent.timestamp` — `datetime | None`
  (keyword-only, default `None`; `None`: the product reports no time), the typed
  form of the deprecated ISO-8601 text `ts`. A driver fills either form, or both,
  describing the same instant. A timezone-naive value stays naive. Migration: pass
  `timestamp`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P3;
  design `docs/architecture/precise-types-design.md` (SD-WAN models); PR #73.
- **enum member** `testprotocols.models:UplinkState.UNKNOWN` (a state the
  product could not determine, such as a link with no health data). Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P4;
  design `docs/architecture/precise-types-design.md` (WAN-edge models); PR #73.
- **model** `testprotocols.models:QosClassifier` (`vlan`, `protocol`, `src_ports`,
  `dst_ports`; frozen; every field left out places no restriction; `vlan` is 1 to
  4094) — what a QoS rule selects. **field** `testprotocols.models:QosRule.classifier`
  — `QosClassifier | None` (keyword-only, default `None`; `None`: every frame), the
  typed form of the deprecated text `match`. A driver fills either form, or both,
  describing the same traffic. A rule's classifier holds at most one source and one
  destination port range. Migration: pass `classifier`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P5;
  design `docs/architecture/precise-types-design.md` (switch QoS classifier); PR #73.
- **model** `testprotocols.models:Telemetry` (`uptime_seconds`, `cpu_load_percent`,
  `mem_used_percent`; frozen; each is `None` when the device does not report it, and
  `uptime_seconds` is required, so a driver states `None` rather than leaving it out; each
  value given is finite and not negative) — a device's resource telemetry. The absent uptime
  follows the shape recorded in `GAPS.md` 2026-06-11 "appliance health / online capability"
  (`float | None`), because a cloud-managed appliance composes `Router`. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P4;
  design `docs/architecture/precise-types-design.md` (telemetry and policy); PR #73.
- **enums** `testprotocols.models:WifiBand` (`GHZ_2_4`, `GHZ_5`, `GHZ_6`),
  `WifiSecurityMode` (`OPEN`, `OWE`, `WPA2_PSK`, `WPA2_EAP`, `WPA3_SAE`, `WPA3_EAP`,
  `WPA2_WPA3_PSK_MIXED`, `WPA2_WPA3_EAP_MIXED`), `MfpMode` (`OFF`, `OPTIONAL`,
  `REQUIRED`), `WifiAclMode` (`DISABLED`, `ALLOW`, `DENY`), `WifiPhyMode` (`A`, `B`,
  `G`, `N`, `AC`, `AX`, `BE`), `ChannelWidth` (an `IntEnum`: 20, 40, 80, 160, 320 MHz),
  `MeshRole` (`CONTROLLER`, `AGENT`, `CONTROLLER_AND_AGENT`, `UNCOMMISSIONED`) — the Wi-Fi vocabularies;
  every value is the string the released contract used (`WifiBand.GHZ_5 == "5GHz"`).
  Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR #73.
- **enum member** `testprotocols.models:WifiSecurityMode.WPA3_EAP_192` (`"WPA3-EAP-192"`) — the
  WPA3-Enterprise 192-bit security mode (CNSA suite, Suite B). Like the other WPA3-only modes it
  requires management-frame protection. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR #73.
- **enums** `testprotocols.models:PhoneState` (`IDLE`, `DIALING`, `INCALL_DIALING`,
  `RINGING`, `CONNECTED`, `INCALL_CONNECTED`, `HOLD`, `DIALTONE`, `INCALL_DIALTONE`,
  `CALL_ENDED`, `CODE_ENDED`, `CALL_WAITING`, `CONFERENCE`, `BUSY`, `NOT_ANSWERED`;
  one per `is_*` call-state predicate of `SipPhone`; `HOLD == "hold"`) — the voice
  vocabulary; every value is the string the released contract or its implementer used. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P7;
  design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR #73.
- **records** `testprotocols.models:RtpStats` (`engaged`, `sessions`), `MwiStatus`
  (`waiting`, `new`, `old`) and `OfflineMessage` (`sender`, `body`, `stored_at: datetime |
  None`, `None` when the store reports no time) —
  frozen records for what the SIP server's media relay, message-waiting and offline-message
  readers returned as dicts (counts not negative). A driver parses its stored text (ISO 8601,
  as `datetime.fromisoformat` reads it, `T` or space separated) into a
  `datetime` for `read_offline_messages`; its deprecated `get_offline_messages` may keep
  returning that original text unchanged. Migration: read the new records.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P7;
  design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR #73.
- **enums** `testprotocols.models:IpVersion` (`IPV4 = "ipv4"`, `IPV6 = "ipv6"`; the
  `nmap(ip_type)` words), the `IntEnum` `IpFamily` (`V4 = 4`, `V6 = 6`; the iperf
  `ip_version` numbers), `DnsRecordType` (`A`, `AAAA`, `CNAME`, `MX`, `NS`, `PTR`, `SOA`,
  `SRV`, `TXT`), `HttpScheme` (`HTTP`, `HTTPS`), `LinkAdminState` (`UP`, `DOWN`; not
  `PortAdminState`, whose words are `enabled` / `disabled`), `QoeTool` (`BROWSER`,
  `HTTP_CLIENT`, `WEBRTC`, `TCP_PROBE`), `PageCompletion` (`LOAD`, `DOMCONTENTLOADED`,
  `NETWORKIDLE`, `COMMIT`), `QoeCompletion` (those four and `DURATION`, `RESPONSE`,
  `CONNECT`), `QoeScenario` (`PAGE_LOAD`), `TransportProtocol` (`TCP`, `UDP`), `ServiceStatus`
  (`RUNNING`, `STOPPED`, `ERROR`), `StormControlUnit` (`PERCENT`, `PPS`). Where the
  released contract or an implementer used a word, the member equals it. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P5, P8, P10 and P11;
  design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR #73.
- **field** `testprotocols.models:StormControlConfig.unit` (`StormControlUnit | None`,
  default `None`, meaning "as the driver reads it"; released drivers ignore it). Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P5;
  design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR #73.
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
  `{"unparsable": line}` entries, which no record holds). Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8, P10 and P11;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.
- **enums** `testprotocols.models:SyslogSeverity` (`IntEnum`, RFC 5424 severities 0 to 7),
  `NmapPortState` (nmap's six port states: `open`, `closed`, `filtered`, `unfiltered`,
  `open|filtered`, `closed|filtered`). Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8 and P11;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.
- **models** `testprotocols.models:Blackout`, `Brownout(latency_ms, jitter_ms,
  loss_percent)`, `LatencySpike(latency_ms, jitter_ms)`, `PacketStorm(loss_percent, latency_ms,
  jitter_ms, duplicate_percent)` (a burst of loss, as the released implementers apply it;
  `duplicate_percent` is `None`, not requested, unless given), and the union `TransientEvent` — the typed transient impairment events (every field
  optional: `None` is the driver's default; `event_name` gives the released `inject_transient`
  word, whose keyword for a spike's latency is `spike_latency_ms`). Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P10;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.
- **model** `testprotocols.models:GroupRecord(sources, group, record_type)` — a `NamedTuple`,
  so it is the released `(sources, group, record_type)` tuple; a `list[GroupRecord]` is
  accepted by the widened `send_mldv2_report` parameter (see *Breaking for driver
  authors*). Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.
- **marker** `@deprecated` on every deprecated protocol member and model class (the
  standard marker, re-exported by the internal `testprotocols._compat`), with the same
  sentence as the docstring: "Deprecated: use `<new>`. Removal not before the first release 6
  months after the release that deprecates it." It is passed `category=None`: the deprecation
  is stated for the type checkers and in the docstring, and nothing warns at run time. Type
  checkers read `typing_extensions.deprecated` from their bundled stubs; at run time Python
  3.13 and later supply `warnings.deprecated`, and Python 3.12 an identity marker that returns
  the object unchanged, so `testprotocols` keeps no runtime dependency. pyright in strict mode
  reports `reportDeprecated` as an error by default, so a consumer on pyright strict gets an
  error at every use of a deprecated member on upgrade; mypy reports a use only with
  `enable_error_code = deprecated`, as this workspace configures it. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P1;
  design `docs/architecture/precise-types-design.md`; PR #73.

- **protocol** `testprotocols.hw_console:Console` (also `testprotocols.Console`) — the
  interactive text console `HwConsole` hands out: `execute_command(command, /, timeout=-1) ->
  str`, `sendline(text="", /) -> int` (the bytes written, as pexpect's), a read-only `before: str | bytes | None` and
  `start_interactive_session()`: the members callers of the returned consoles were seen to use
  that a `pexpect.spawn` subclass can satisfy (checked against `types-pexpect`, a dev
  dependency only). `runtime_checkable`. `expect` and `expect_exact` are not members: a
  console's own pattern types cannot be matched by one contract type, so a caller that
  matches patterns keeps the concrete console type. `sendline` is positional-only, so a
  `Console` cannot be passed to a helper protocol that takes `string` as a named parameter.
  A returned-object contract, not a capability: `HwConsole` keeps its released `Any` returns,
  and the consoles it returns satisfy `Console`. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P11;
  design `docs/architecture/precise-types-design.md` (HwConsole); PR #73.

- **properties** `testprotocols.models:HTTPResult.status` (`int | None`: the status code, `None`
  when the response has no status line with a code from 100 to 599) and `body` (`str`, the text
  after the headers) — read-only typed reads over the released attributes, so they follow an
  assignment to `code` or `beautified_text`. The class is otherwise the released one: the
  released constructor and parser, plain assignable `raw`, `code` and `beautified_text`, and
  identity equality. Migration: read `status` and `body`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR #73.

#### Changed

- **protocol member** `testprotocols.wifi_bss:WifiBss.create_bss` / `set_security` — the
  management-frame protection read-back changes: the WPA3-only modes (`WPA3_SAE`, `WPA3_EAP`,
  `WPA3_EAP_192`), `OWE` and any BSS on 6 GHz require protection, so a driver applies
  `REQUIRED` whatever `mfp` says and `get_bss_config` reports `mfp` as `REQUIRED` (released: the
  `mfp` passed, by default `"optional"`). Migration: a driver that today reports `optional` for
  such a BSS reports `REQUIRED`; a test that compared the read-back with the `mfp` it passed
  expects `REQUIRED` for these modes.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`
  (Wi-Fi vocabularies); PR #73.
- **protocol members** `testprotocols.packet_filter:PacketFilter` (every `chain`
  parameter; `set_default_policy(policy)`), `testprotocols.nat:Nat.list_nat_rules(mode)`
  and `testprotocols.conntrack:Conntrack` (`protocol` on `list_connections`,
  `count_connections`, `get_connection`, `drop_connection`) — now annotated `Chain | str`, `DefaultAction | str`,
  `NatMode | str | None` and `RuleProtocol | str`. A driver converts each once at its boundary. The `state`
  filters stay `str`, the device's own word. An unknown chain, policy, mode or
  protocol raises `ValueError`; a conntrack `protocol` of `any` is refused,
  because no flow has it. Migration: pass the members; a driver adds the annotations and the conversion.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR #73.
- **models** `testprotocols.models:FirewallRule` (`action`, `protocol`),
  `NatRule` (`mode`, `protocol`), `PortMapping` (`protocol`) and `Connection`
  (`protocol`) — each field is now `Enum | str`: a member or the released word,
  stored as given (a member compares equal to its word); the enums are
  `FirewallRuleAction`, `RuleProtocol`, `NatMode` and `PortMappingProtocol`.
  `NatRule.protocol` keeps its released default `"any"`. `Connection.state` stays a
  `str`, the device's own word. Migration: pass the members.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md` (firewall, NAT and conntrack vocabularies); PR #73.

- **models** `testprotocols.models:LinkStatus.state` and `LinkHealthReport.state` —
  now `UplinkState | str`: a member or the released word, stored as given. The
  vocabulary is the existing `up`, `down`, `degraded` plus `unknown` (a probe with no
  data). Migration: pass the members. Static only:
  `TrafficShapingRule.match` is `Mapping[str, object]` (was `dict[str, Any]`),
  so a reader gets `object` values.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P4;
  design `docs/architecture/precise-types-design.md` (WAN-edge models); PR #73.
- **protocol member** `testprotocols.sdwan_policy_manager:SdwanPolicyManager.apply_policy` —
  static only, no runtime change: it takes `dict[str, object]` (was `dict[str, Any]`), so a
  caller's `dict[str, str]` variable no longer type-checks (an implementer's `dict` parameter
  still conforms).
  Proposal `docs/proposals/2026-10-05-precise-types.md` P3;
  design `docs/architecture/precise-types-design.md` (telemetry and policy); PR #73.
- **models** `testprotocols.models` `WifiBssConfig` (`band`, `security_mode`, `mfp`),
  `WifiStation.band`, `WifiNeighbor.band`, `WifiChannelUtilization.band`,
  `WifiRadioStats.band`, `WifiMeshLink.band`, `WifiAcl.mode`, `WifiMeshStatus.role` and
  `WifiMeshNode.role` — now `E | str` (`WifiBand`, `WifiSecurityMode`, `MfpMode`,
  `WifiAclMode`, `MeshRole`): a member or the released word, stored as given.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR #73.
- **protocol members** `WifiBss.create_bss` / `set_security` (`band`, `security_mode`,
  `mfp`; the `mfp` default stays `"optional"`),
  `WifiBss.set_acl_mode`, every `band` of `WifiRadio` and `WifiRf`,
  `WifiRadio.set_bandwidth` (`ChannelWidth | int`), `WifiRadio.set_mode`,
  `WifiMesh.set_backhaul_band` and `WifiClient.set_wlan_scan_channel` (`int | str`) —
  parameter annotations widen to `E | str`, so every released call still type-checks;
  a driver converts once at the boundary. An `int` naming a `ChannelWidth` is that member.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md` (Wi-Fi vocabularies); PR #73.
- **protocol member** `SipPhone.wait_for_state(state)` — the annotation widens to
  `PhoneState | str`, so every released call still type-checks. A `wait_for_state` word
  that names no state raises `ValueError` (released implementer: the same). The presence
  parameters and return (`set_presence`, `notify_presence`, `get_user_presence`) stay
  `str`, the provider's own word.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P7;
  design `docs/architecture/precise-types-design.md` (Voice vocabularies); PR #73.
- **models** `MeasurementSpec.tool` and `completion`, and `TrafficSpec.protocol` — now
  `E | str`: a member or the released word, stored as given (a member compares equal to
  its text). `QoEResult.protocol`, `RadiusUser.eap_methods` and
  `RadiusAccountingRecord.record_type` / `terminate_cause` stay `str`, the device's own
  word. The defaults stay the released words
  (`"browser"`, `"networkidle"`, `"udp"`). A new enum keeps the default `<Enum.MEMBER: 'x'>`
  repr: code that builds text with `repr(value)` or `{value!r}` from a member must use
  `str(value)`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P10;
  design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR #73.
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
  declare `str`; they are documented and their narrowing is announced.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8 and P10;
  design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR #73.
- **protocol members** `NetemController.set_impairment_profile` / `set_interface_profile`
  (`profile: ImpairmentProfile | dict[str, object]`, was `dict[str, Any]`) and
  `DhcpServer.provision_cpe` (`dhcpv4_options` / `dhcpv6_options: dict[str, dict[str, object]]`,
  was `dict[str, Any]`: a service-pool name to an option-name map, as the released implementer
  reads them) — no `Any`; static only: a caller's loosely typed dict variable no longer
  type-checks, and an implementer declaring `dict` or `dict[str, Any]` still conforms.
  `HeldPrefixes.hold(address)` stays `str` (released implementers declare `str`).
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8 and P10;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.
- **models** `DHCPTraceData.dhcp_packet` and `DHCPV6TraceData.dhcpv6_packet` —
  `Mapping[str, object]` (was `dict[str, Any]`): a decoder's nested bag with no fixed typed
  shape; static only, a reader narrows each value it uses.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.

#### Deprecated

- **member** `testprotocols.packet_filter:PacketFilter.get_rule_counters` (so also `Firewall`) —
  deprecated. Replacement: `get_rule_counter_values`. Earliest removal: the first release 6 months
  after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.nat:Nat.get_nat_rule_counters` — deprecated. Replacement:
  `get_nat_rule_counter_values`. Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.router:Router.get_telemetry` — deprecated. Replacement:
  `read_telemetry`. Earliest removal: the first release 6 months after the release that deprecates
  it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P4;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.sdwan_policy_manager:SdwanPolicyManager.apply_policy` — deprecated.
  Replacement: none: the typed steering and SLA members (`configure_sla_policy`,
  `set_uplink_selection`, `set_default_uplink`, `set_active_active_vpn`). Earliest removal: the
  first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P3;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.wifi_client:WifiClient.iwlist_supported_channels` — deprecated.
  Replacement: `supported_channels`. Earliest removal: the first release 6 months after the release
  that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.wifi_radio:WifiRadio.get_mode` — deprecated. Replacement: `get_modes`.
  Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.sip_server:SipServer.get_rtpengine_stats` — deprecated. Replacement:
  `read_rtp_relay_stats`. Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P7;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.sip_server:SipServer.get_mwi_status` — deprecated. Replacement:
  `read_mwi_status`. Earliest removal: the first release 6 months after the release that deprecates
  it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P7;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.sip_server:SipServer.get_offline_messages` — deprecated. Replacement:
  `read_offline_messages`. Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P7;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.content_filtering:ContentFiltering.get_url_rules` — deprecated.
  Replacement: `read_url_rules`. Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P11;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.device_management:DeviceManagement.get_memory_utilization` — deprecated.
  Replacement: `read_memory_utilization`. Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P11;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.device_management:DeviceManagement.get_running_processes` (with
  `ps_options`) — deprecated. Replacement: `read_running_processes`; a `ps_options` other than
  `"-A"` has no successor. Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P11;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.device_management:DeviceManagement.read_event_logs` — deprecated.
  Replacement: `read_log_entries`. Earliest removal: the first release 6 months after the release
  that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P11;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.dns_client:DnsClient.dns_lookup` (with `opts`) — deprecated.
  Replacement: `resolve`; `opts` has no successor. Earliest removal: the first release 6 months
  after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.iperf_client:IperfClient.start_traffic_sender` — deprecated.
  Replacement: `start_sender_session`. Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P10;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.iperf_server:IperfServer.start_traffic_receiver` — deprecated.
  Replacement: `start_receiver_session`. Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P10;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.nmap_scanner:NmapScanner.nmap` (with `opts`) — deprecated. Replacement:
  `scan_ports`; `fast` replaces `opts="-F"`, any other `opts` has no successor. Earliest removal:
  the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.arp_client:ArpClient.get_arp_table` — deprecated. Replacement:
  `read_arp_table`. Earliest removal: the first release 6 months after the release that deprecates
  it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.ntp_client:NtpClient.get_date` — deprecated. Replacement: `read_date`.
  Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P9;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.ntp_client:NtpClient.set_date` — deprecated. Replacement:
  `set_date_time`. Earliest removal: the first release 6 months after the release that deprecates
  it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P9;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.netem_controller:NetemController.inject_transient` — deprecated.
  Replacement: `inject_event`. Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P10;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.snmp_client:SnmpClient.execute_snmp_command` — deprecated. Replacement:
  `snmp_get`, `snmp_walk`, `snmp_set` or `snmp_bulk_get`; any other command has no successor.
  Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P9;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **attribute** `testprotocols.models:HTTPResult.code` — deprecated (docstring and this entry; a
  plain attribute carries no marker). Replacement: `status` (`int | None`). Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **attribute** `testprotocols.models:HTTPResult.beautified_text` — deprecated (docstring and this
  entry; a plain attribute carries no marker). Replacement: `body`. Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **class** `testprotocols.models:VPNPeerStatus` — deprecated. Replacement: none (no successor). Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P4;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **class** `testprotocols.models:TrafficShapingRule` — deprecated. Replacement: none (`ShapingRule`
  where a capability needs one). Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P4;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `testprotocols.ip_routing:IpRouting.ping(json_output=True)` — deprecated.
  Replacement: `ping_stats`; at removal `ping` returns `bool`. Earliest removal: the first release 6
  months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `IpRouting.ping` and `traceroute` `options` — deprecated. Replacement: none.
  Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `testprotocols.http_client:HttpClient.curl` and `http_get` `options` — deprecated.
  Replacement: keyword-only `no_proxy`, `insecure`, `follow_redirects`. Earliest removal: the first
  release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `PacketFilter` `chain` (every member) and `set_default_policy(policy)`: `Chain |
  str`, `DefaultAction | str` — deprecated. Replacement: `Chain`, `DefaultAction` (narrows to the
  enum). Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `Nat.list_nat_rules(mode)`: `NatMode | str | None` — deprecated. Replacement:
  `NatMode | None` (narrows to the enum). Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `Conntrack` `protocol` (`list_connections`, `count_connections`, `get_connection`,
  `drop_connection`): `RuleProtocol | str` — deprecated. Replacement: `RuleProtocol` (narrows to the
  enum). Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** Wi-Fi `band` (`WifiBss.create_bss`, every `WifiRadio` and `WifiRf` member,
  `WifiRadioWhiteBox.inject_radar_event`, `WifiMesh.set_backhaul_band`): `WifiBand | str` —
  deprecated. Replacement: `WifiBand` (narrows to the enum). Earliest removal: the first release 6
  months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `WifiBss.create_bss(security_mode, mfp)` and `set_security(mode, mfp)`:
  `WifiSecurityMode | str`, `MfpMode | str` — deprecated. Replacement: `WifiSecurityMode`, `MfpMode`
  (narrows to the enum). Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `WifiBss.set_acl_mode(mode)`: `WifiAclMode | str` — deprecated. Replacement:
  `WifiAclMode` (narrows to the enum). Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `WifiRadio.set_mode(mode)`: `WifiPhyMode | str` — deprecated. Replacement:
  `WifiPhyMode` (narrows to the enum; a compound mode names no member). Earliest removal: the first
  release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `WifiClient.set_wlan_scan_channel(channel)`: `int | str` — deprecated. Replacement:
  `int`. Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `SipPhone.wait_for_state(state)`: `PhoneState | str` — deprecated. Replacement:
  `PhoneState` (narrows to the enum). Earliest removal: the first release 6 months after the release
  that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P7;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `HttpClient.curl(protocol)`: `HttpScheme | str` — deprecated. Replacement:
  `HttpScheme` (narrows to the enum). Earliest removal: the first release 6 months after the release
  that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `IpInterface.set_link_state(state)`: `LinkAdminState | str` — deprecated.
  Replacement: `LinkAdminState` (narrows to the enum). Earliest removal: the first release 6 months
  after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `UpnpClient.create_upnp_rule(protocol)` and `delete_upnp_rule(protocol)`:
  `PortMappingProtocol | str` — deprecated. Replacement: `PortMappingProtocol` (narrows to the
  enum). Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `QoeBrowser.measure_productivity(scenario, wait_until)`: `QoeScenario | str`,
  `PageCompletion | str` — deprecated. Replacement: `QoeScenario`, `PageCompletion` (narrows to the
  enum). Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P10;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `HttpServer.start_http_service` / `stop_http_service(port)` and
  `start_http_service(ip_version)`: `str` — deprecated. Replacement: `int`, `IpFamily` (announced
  narrowing). Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `UpnpClient` `int_port`, `ext_port` and `VlanClient` `vlan_id`: `str` — deprecated.
  Replacement: `int` (announced narrowing). Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `IpRouting.traceroute(version)`: `str` (`""` or `"6"`) — deprecated. Replacement:
  `IpFamily | None` (announced narrowing). Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `IpInterface.is_link_up(pattern)` — deprecated. Replacement: `is_link_admin_up` for
  the administrative state; at removal `pattern` goes. Earliest removal: the first release 6 months
  after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `NetemController.set_impairment_profile` / `set_interface_profile(profile)` as a
  `dict` — deprecated. Replacement: `ImpairmentProfile` (narrows to it). Earliest removal: the first
  release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P10;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `MulticastClient.send_mldv2_report` records as plain tuples — deprecated.
  Replacement: `GroupRecord` (narrows to `Sequence[GroupRecord]`). Earliest removal: the first
  release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `HeldPrefixes.hold(address)`: `str` — deprecated. Replacement: `IPv4Interface |
  IPv6Interface` (announced narrowing). Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P8;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `PacketFilter.get_default_policy` return `str` — deprecated. Replacement:
  `DefaultAction` (announced narrowing). Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `WifiRadio.list_radios` and `get_bandwidth` returns (`list[str]`, `int`) —
  deprecated. Replacement: `list[WifiBand]`, `ChannelWidth` (announced). Earliest removal: the
  first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`;
  PR #73.
- **member** `RadiusServer.get_status` return `str` — deprecated. Replacement: `ServiceStatus`
  (announced narrowing). Earliest removal: the first release 6 months after the release that
  deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P11;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `FirewallRule.dst_port` (port text, required) — deprecated. Replacement: `dst_ports`; at
  removal the text field goes and `dst_ports` becomes required. Earliest removal: the first release
  6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `NatRule.dst_port` and `translated_port` (port text, released default `""`) —
  deprecated. Replacement: `dst_ports`, `translated_ports`; at removal the text fields go and the
  typed fields default to `()`, the typed form of the released default `""`, so a rule that never
  sets them keeps its meaning. Earliest removal: the first
  release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `L3Rule.src_port` and `dst_port` (port text, released default `"any"`) — deprecated.
  Replacement: `src_ports`, `dst_ports`; at removal the text fields go and the typed fields default to
  `()`, the typed form of the released default `"any"`, so a rule that never sets them keeps its
  meaning. Earliest removal: the first release 6 months
  after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P3;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `SecurityEvent.ts` (ISO-8601 text, required) — deprecated. Replacement: `timestamp`; at
  removal `ts` goes and `timestamp` becomes required (`None`: no time reported). Earliest removal:
  the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P3;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `QosRule.match` (classifier text, required) — deprecated. Replacement: `classifier`; at
  removal `match` goes and `classifier` becomes required (`None`: every frame). Earliest removal:
  the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P5;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `FirewallRule.action` / `protocol`: `FirewallRuleAction | str`, `RuleProtocol | str` —
  deprecated. Replacement: the enums (narrows from `E | str` to `E`). Earliest removal: the first
  release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `NatRule.mode` / `protocol`: `NatMode | str`, `RuleProtocol | str` — deprecated.
  Replacement: the enums (narrows from `E | str` to `E`). Earliest removal: the first release 6
  months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `PortMapping.protocol`, `Connection.protocol`: `PortMappingProtocol | str`,
  `RuleProtocol | str` — deprecated. Replacement: the enums (narrows from `E | str` to `E`).
  Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `LinkStatus.state`, `LinkHealthReport.state`: `UplinkState | str` — deprecated.
  Replacement: `UplinkState` (narrows from `E | str` to `E`). Earliest removal: the first release 6
  months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P4;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** Wi-Fi fields: `band` of `WifiBssConfig`, `WifiStation`, `WifiNeighbor`,
  `WifiChannelUtilization`, `WifiRadioStats`, `WifiMeshLink`; `WifiBssConfig.security_mode` / `mfp`;
  `WifiAcl.mode`; `role` of `WifiMeshStatus`, `WifiMeshNode` — deprecated. Replacement: `WifiBand`,
  `WifiSecurityMode`, `MfpMode`, `WifiAclMode`, `MeshRole` (narrows from `E | str` to `E`). Earliest
  removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P6;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `MeasurementSpec.tool` / `completion`, `TrafficSpec.protocol` — deprecated. Replacement:
  `QoeTool`, `QoeCompletion | PageCompletion`, `TransportProtocol` (narrows from `E | str` to `E`).
  Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P10;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `NatRule.src_cidr`, `dst_cidr`, `translated_src`, `translated_dst` (`""`: absent) —
  deprecated. Replacement: `str | None`, `None` absent (announced). Earliest removal: the first
  release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P2;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `L3Rule.src_cidr`, `dst_cidr` (`"any"`), `UplinkStatus.ip`, `gateway`, `public_ip`,
  `primary_dns` and `NetworkAttachment.segment` (`""`) — deprecated. Replacement: `str | None`,
  `None` unconstrained or not reported (announced). Earliest removal: the first release 6 months
  after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P3;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **field** `LinkStatus.ip_address` (`""`: no address) — deprecated. Replacement: `str | None`
  (announced). Earliest removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P4;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** `testprotocols.hw_console:HwConsole.get_console` and `get_interactive_consoles`
  returns `Any`, `dict[str, Any]` — deprecated. Replacement: `Console`, `Mapping[str, Console]`
  (announced narrowing; a console lacking a `Console` member stops conforming then). Earliest
  removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P11;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `testprotocols.sip_server:SipServer.verify_sip_message(since)` as `Any` —
  deprecated. Replacement: `datetime | None` (announced narrowing; a caller passing a text
  marker, and an implementer whose declared parameter does not accept `datetime | None`, stop
  type-checking then). The released annotation is kept until then,
  and `message_type` stays `str`. Earliest removal: the first release 6 months after the
  release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P7;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.

### testoperations

#### Added

- **module** `testoperations.pairs` — the public readers of a record field that has a
  released text form and a typed form: `firewall_rule_dst_ports(rule)`,
  `nat_rule_dst_ports(rule)`, `nat_rule_translated_ports(rule)`, `l3_rule_src_ports(rule)`,
  `l3_rule_dst_ports(rule)` (each `-> tuple[PortRange, ...]`),
  `security_event_timestamp(event) -> datetime | None` and `qos_rule_classifier(rule) ->
  QosClassifier | None`, and the parsers of the released text forms (`parse_port_ranges`,
  `parse_nat_port_ranges`, `parse_timestamp`, `parse_qos_classifier`). A consumer that reads
  such a pair uses them and gets one answer whichever form the driver filled. The read rule:
  the typed field when filled, else the text parsed, else the released default's meaning
  (`"any"` for `L3Rule` ports, `""`, no port, for `NatRule` ports), or `ValueError` when the
  released field was required and the typed field cannot hold `None` as a value
  (`FirewallRule.dst_port`). `SecurityEvent.ts` and `QosRule.match` are the exception: their
  typed fields hold `None` as a value (no time reported; every frame), so a record with both
  fields `None` reads as `None`. Each reader and parser is removed in the release that
  removes the text fields it reads. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (Text and typed fields: either form); PR #73.
- **behaviour** the operations convert their own released `str` parameters to enums (a plain
  string naming a member warns at the operation's caller). Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md`; PR #73.
- **enum** `testoperations.segmentation:DenyScope` (`HOST`, `SUBNET`) — how wide
  a deny rule built by `build_deny_rule` matches. Migration: pass the member.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (Segmentation deny scope); PR #73.
- **parameter** `testoperations.netem_controller:inject_packet_storm(loss_percent=None)` —
  keyword-only: the share of packets lost during the storm, which the released drivers apply
  for a packet storm. `duplicate_percent` now defaults to `None` (not requested): a
  new-name driver is asked for duplication only when the caller passes it; an old-name driver
  still receives the released `duplicate_percent=100.0`. A packet storm keeps its released
  meaning, a loss burst. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.
- **records** `testoperations.iperf_client:IperfSession` (`sender`, `receiver`: each an
  `IperfProcess`), `testoperations.homing:HomeVerification` (`vlan_defined`,
  `subnet_advertised`, `peers_reachable`, `details`) with `HomeDetails` (`defined_subnet`,
  `defined_gateway`, `peer_states`: peer name to `VpnPeerState`), and
  `testoperations.iperf_generator:FlowPair` (`a_to_b`, `b_to_a`) — frozen records replacing
  the released `dict` returns of `start_iperf`, `verify_home` and `saturate_link`. Each keeps
  the released dict readable for the deprecation period (see *Deprecated*). Migration: read the
  fields.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **enum** `testoperations.netem_controller:NetemPreset` (`CLEAN`, `DSL`, `CABLE`, `LTE`,
  `THREE_G` = `"3g"`, `SATELLITE`, `DEGRADED`, `LOSSY`) — the built-in presets `apply_preset`
  knows. Migration: pass the member.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **enums** `testoperations.throughput:NonCompletionSide` (`ENDPOINT`, `LOCAL_RECEIVER`,
  `UNKNOWN`) and `NonCompletionKind` (`ERROR_DOCUMENT`, `NO_COMPLETED_SESSION`) — replace the
  `Literal` aliases of the same names, with the same text values. Migration: none for a reader
  (`exc.which_side == "endpoint"` still holds); pass the member to `NonCompletion`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **protocol** `testoperations.throughput:MeasureFn` — the call shape of the `measure`
  parameters of `measure_path_rtt`, `measure_one_direction`, `measure_path_until` (and
  the private `_probe_flow`) (the flows and the three keyword-only timings), replacing
  `Callable[..., list[FlowThroughput]]`. Migration: none; a stand-in that takes those keywords
  fits.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **type alias** `testoperations.throughput:JsonValue` (`None | bool | int | float | str |
  list[JsonValue] | dict[str, JsonValue]`) — the recursive type of a parsed JSON value, as
  `json.loads` returns it; the element type of `iter_json_docs`. Migration: none.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.

#### Changed

- **operation** `testoperations.throughput:measure_external_path_until` — the
  `measure_flow` annotation narrows from `Callable[..., FlowThroughput]` to a call
  protocol: `(flow: ExternalFlow, /, *, duration_s: int, result_timeout_s: float,
  poll_interval_s: float) -> FlowThroughput`. Migration: a stand-in takes the flow
  (positional) plus the three keyword timings; the default is unchanged.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **operation** `testoperations.segmentation:build_deny_rule` — `scope` is now
  `DenyScope | str` and `proto` `RuleProtocol | str` (shape 1). A plain string
  naming a member warns (`DeprecationWarning`) and converts. The error for an
  unknown scope changes: it is the `coerce_enum` `ValueError` (`scope: 'vlan' is
  not one of ['host', 'subnet']`), still naming `scope`; an unknown `proto` is the
  same kind of `ValueError`, naming `proto`. The rule fills both port forms
  (`"any"` and the empty tuple). Migration: pass `DenyScope` and
  `RuleProtocol` members.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (Segmentation deny scope); PR #73.
- **operation** `testoperations.iperf_generator:saturate_link(protocol)` — takes
  `TransportProtocol | str` (default `"udp"`, as released) and converts it at its boundary with
  `coerce_enum`: a plain `"udp"` / `"tcp"` the caller passes warns at the caller, a call that
  leaves `protocol` out does not; any other word is a `ValueError`. Migration:
  pass `TransportProtocol`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR #73.
- **operations** `testoperations.throughput:measure_concurrent_throughput` and
  `measure_external_flow` (and the operations built on them), `testoperations.netem_controller`
  `inject_blackout`, `inject_brownout`, `inject_latency_spike`, `inject_packet_storm` and
  `testoperations.sdwan:measure_failover_convergence` — call the new member names
  (`start_sender_session` with the window in bytes, `start_receiver_session`, `inject_event`)
  through `testoperations._renamed`, falling back to the released names; a driver with only
  the released names receives exactly the released call. With a new-name driver, a flow
  `window` that is not an iperf size raises `ValueError` before anything starts.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.
- **operation** `testoperations.iperf_client:start_iperf` — breaking for callers: gains the
  required keyword-only `host` (the address the sender connects to), returns an `IperfSession`
  (was `dict[str, Any]`), and takes `iperf_client: IperfClient` and `iperf_server: IperfServer`
  (were `Any`). The released operation called `start_sender` / `start_receiver`, which no
  capability protocol declares and no released implementer implements, and it could not name
  the receiver's address; it now calls `start_receiver_session`
  / `start_sender_session` (or the released `start_traffic_receiver` / `start_traffic_sender` on
  a driver that has only those). `ip_version` is `IpFamily | int` (default `4`, as released): `4` and
  `6` are accepted as numbers, any other value is a `ValueError` (released: passed through).
  Migration: pass `host=`; read the record's fields.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **operation** `testoperations.iperf_client:sender_life_record(iperf_client)` — typed
  `IperfClient` (was `Any`); behaviour unchanged.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **operation** `testoperations.homing:verify_home` — returns a `HomeVerification` (was
  `dict[str, object]`); the released keys still read through it with a `DeprecationWarning`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **operation** `testoperations.iperf_generator:saturate_link` — returns a `FlowPair` (was
  `dict[str, str]`); the released keys still read through it with a `DeprecationWarning`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **operation** `testoperations.netem_controller:apply_preset(preset_name)` — takes
  `NetemPreset | str` (shape 1). A plain string naming a preset warns and converts. The error
  for an unknown name is the `coerce_enum` `ValueError` (`apply_preset(preset_name): 'x' is not
  one of [...]`), not `unknown preset 'x'; available: [...]`. Migration: pass `NetemPreset`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **class** `testoperations.throughput:NonCompletion` — `which_side` and `what` take
  `NonCompletionSide | str` and `NonCompletionKind | str` (shape 1): a plain string naming a
  member warns and converts, any other word is a `ValueError`; the attributes are the enum
  members (equal to the released text). The message text is unchanged. Migration: pass the
  members.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **function** `testoperations.throughput:iter_json_docs` — returns
  `list[dict[str, JsonValue]]` (was `list[Any]`): each document is a JSON object, and
  `JsonValue` (new, in the same module) is the recursive type of a parsed JSON value. A caller
  indexing into a document narrows each nested value first.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.
- **type alias** `testoperations.throughput:JsonObj` — `Mapping[str, JsonValue]` (was
  `Mapping[str, object]`): a parsed JSON object, typed over the recursive JSON value. A value
  of the alias still passes where `Mapping[str, object]` is expected; a caller that passes a
  `Mapping[str, object]` where `JsonObj` is expected narrows its values first.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.

#### Deprecated

- **parameter** `testoperations.segmentation:build_deny_rule(scope, proto)` as a plain `str` —
  deprecated. Replacement: `DenyScope`, `RuleProtocol` (narrows to the enum). Earliest removal: the
  first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `testoperations.netem_controller:apply_preset(preset_name)` as a plain `str` —
  deprecated. Replacement: `NetemPreset` (narrows to the enum). Earliest removal: the first release
  6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md`;
  register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `testoperations.throughput:NonCompletion(which_side, what)` as a plain `str` —
  deprecated. Replacement: `NonCompletionSide`, `NonCompletionKind` (narrows to the enum). Earliest
  removal: the first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **parameter** `testoperations.iperf_generator:saturate_link(protocol)` as a plain `str` —
  deprecated. Replacement: `TransportProtocol` (narrows to the enum). Earliest removal: the first
  release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.
- **member** reading `IperfSession`, `HomeVerification` or `FlowPair` as the released dict
  (indexing, `get`, `in`, `len`, `keys`, `items`, `values`, iteration, `==` a dict, `as_dict()`) —
  deprecated. Replacement: the record's fields; the mapping access is removed. Earliest removal: the
  first release 6 months after the release that deprecates it.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md`; register `packages/testprotocols/DEPRECATIONS.md`; PR #73.

#### Fixed

- **operation** `testoperations.http_server:start_http_server` — the default `ip_version`
  was `"ipv4"`, which the released implementers rendered as `webfsd -ipv4`; the server
  command takes `-4` / `-6`. The default is now `"4"` and `ip_version` is documented as `"4"`
  or `"6"`. A caller that passed `"ipv4"` / `"ipv6"` explicitly reaches the same bug and
  should pass `"4"` / `"6"`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (Host-tool and service vocabularies); PR #73.
- **operation** `testoperations.netem_controller:inject_latency_spike(latency_ms)` — the
  released drivers read a spike's latency as `spike_latency_ms`, so the value was ignored (they
  applied their 500 ms default). With a driver that implements `inject_event` it takes effect;
  an old-name driver still receives the released call (and still ignores it).
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (Host-tier records); PR #73.
- **operation** `testoperations.pcap_capture:tcpdump` — typed `PcapCapture` (was `Any`) and
  calls `start_tcpdump(interface, None, output_file=fname, additional_filters=filters or "")`,
  stopping the capture with the process id the start returned. The released operation called
  `start_tcpdump(fname, interface, ...)` (the file name as the interface) and
  `stop_tcpdump(fname)`, which does not match the protocol's signature.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.

#### Consumer action

- **operation** `testoperations.iperf_client:start_iperf` — every caller passes the new required
  keyword-only `host=` (the address the sender connects to: the receiver's address); a call
  without it raises `TypeError`. Read the returned `IperfSession`'s fields rather than the
  released dict keys. Migration: `start_iperf(client, server, port, host="<receiver address>")`.
  Proposal `docs/proposals/2026-10-05-precise-types.md` P12;
  design `docs/architecture/precise-types-design.md` (testoperations: typed records); PR #73.

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
