# Deprecation register

Every deprecated item of the released contracts, in `testprotocols` and in
`testoperations` — adjacent to `GAPS.md` (capabilities signalled but deferred),
`SPLITS.md` (granularity changes) and `LEVELS.md` (white-box extensions). A
removal, rename or retype is preceded by a deprecation period, which lasts until
the first release 6 months after the release that deprecates it
(`CONTRIBUTING.md`, "Versioning" and "Releases"; `docs/proposals/README.md`,
"The placement ladder", rung 5).

Format: one table row per deprecated item, under its package.

```
| item | replacement | kind | deprecated in | earliest removal |
| <module:Symbol, member, parameter or field> | <successor, or "none" with what to use instead; for a text/typed pair or an `E | str` annotation, the removal step> | member / class / attribute / parameter / field | <version> | <version + 6 months> |
```

- **Adding a row.** The change that deprecates an item adds its row, beside its
  *Deprecated* changelog entry; the CHANGELOG *Deprecated* sections list exactly
  these rows. On an unreleased branch "deprecated in" reads `next release` and
  "earliest removal" `next release + 6 months`; the release that ships a row
  fills in its version and date.
- **Removing a row.** The change that removes the item (or narrows it as its
  replacement says) at or after the earliest removal removes its row, in the
  removal release.
- **Release checklist.** Before tagging a release, every row whose earliest
  removal has passed is removed (the item goes, or narrows as its replacement
  says) or carried forward.

The design records behind the current rows are in
`docs/architecture/precise-types-design.md` ("Deprecations").

---

**testprotocols**

| item | replacement | kind | deprecated in | earliest removal |
| --- | --- | --- | --- | --- |
| `testprotocols.packet_filter:PacketFilter.get_rule_counters` (so also `Firewall`) | `get_rule_counter_values` | member | next release | next release + 6 months |
| `testprotocols.nat:Nat.get_nat_rule_counters` | `get_nat_rule_counter_values` | member | next release | next release + 6 months |
| `testprotocols.router:Router.get_telemetry` | `read_telemetry` | member | next release | next release + 6 months |
| `testprotocols.sdwan_policy_manager:SdwanPolicyManager.apply_policy` | none: the typed steering and SLA members (`configure_sla_policy`, `set_uplink_selection`, `set_default_uplink`, `set_active_active_vpn`) | member | next release | next release + 6 months |
| `testprotocols.wifi_client:WifiClient.iwlist_supported_channels` | `supported_channels` | member | next release | next release + 6 months |
| `testprotocols.wifi_radio:WifiRadio.get_mode` | `get_modes` | member | next release | next release + 6 months |
| `testprotocols.sip_server:SipServer.get_rtpengine_stats` | `read_rtp_relay_stats` | member | next release | next release + 6 months |
| `testprotocols.sip_server:SipServer.get_mwi_status` | `read_mwi_status` | member | next release | next release + 6 months |
| `testprotocols.sip_server:SipServer.get_offline_messages` | `read_offline_messages` | member | next release | next release + 6 months |
| `testprotocols.content_filtering:ContentFiltering.get_url_rules` | `read_url_rules` | member | next release | next release + 6 months |
| `testprotocols.device_management:DeviceManagement.get_memory_utilization` | `read_memory_utilization` | member | next release | next release + 6 months |
| `testprotocols.device_management:DeviceManagement.get_running_processes` (with `ps_options`) | `read_running_processes`; a `ps_options` other than `"-A"` has no successor | member | next release | next release + 6 months |
| `testprotocols.device_management:DeviceManagement.read_event_logs` | `read_log_entries` | member | next release | next release + 6 months |
| `testprotocols.dns_client:DnsClient.dns_lookup` (with `opts`) | `resolve`; `opts` has no successor | member | next release | next release + 6 months |
| `testprotocols.iperf_client:IperfClient.start_traffic_sender` | `start_sender_session` | member | next release | next release + 6 months |
| `testprotocols.iperf_server:IperfServer.start_traffic_receiver` | `start_receiver_session` | member | next release | next release + 6 months |
| `testprotocols.nmap_scanner:NmapScanner.nmap` (with `opts`) | `scan_ports`; `fast` replaces `opts="-F"`, any other `opts` has no successor | member | next release | next release + 6 months |
| `testprotocols.arp_client:ArpClient.get_arp_table` | `read_arp_table` | member | next release | next release + 6 months |
| `testprotocols.ntp_client:NtpClient.get_date` | `read_date` | member | next release | next release + 6 months |
| `testprotocols.ntp_client:NtpClient.set_date` | `set_date_time` | member | next release | next release + 6 months |
| `testprotocols.netem_controller:NetemController.inject_transient` | `inject_event` | member | next release | next release + 6 months |
| `testprotocols.snmp_client:SnmpClient.execute_snmp_command` | `snmp_get`, `snmp_walk`, `snmp_set` or `snmp_bulk_get`; any other command has no successor | member | next release | next release + 6 months |
| `testprotocols.models:HTTPResult.code` (a plain attribute: docstring only, no marker) | `status` (`int \| None`) | attribute | next release | next release + 6 months |
| `testprotocols.models:HTTPResult.beautified_text` (a plain attribute: docstring only, no marker) | `body` | attribute | next release | next release + 6 months |
| `testprotocols.models:VPNPeerStatus` | none (no successor) | class | next release | next release + 6 months |
| `testprotocols.models:TrafficShapingRule` | none (`ShapingRule` where a capability needs one) | class | next release | next release + 6 months |
| `testprotocols.ip_routing:IpRouting.ping(json_output=True)` | `ping_stats`; at removal `ping` returns `bool` | parameter | next release | next release + 6 months |
| `IpRouting.ping` and `traceroute` `options` | none | parameter | next release | next release + 6 months |
| `testprotocols.http_client:HttpClient.curl` and `http_get` `options` | keyword-only `no_proxy`, `insecure`, `follow_redirects` | parameter | next release | next release + 6 months |
| `PacketFilter` `chain` (every member; `get_rule_counter_values` is excepted, it takes the bare `Chain`) and `set_default_policy(policy)`: `Chain \| str`, `DefaultAction \| str` | `Chain`, `DefaultAction` (narrows to the enum) | parameter | next release | next release + 6 months |
| `Nat.list_nat_rules(mode)`: `NatMode \| str \| None` | `NatMode \| None` (narrows to the enum) | parameter | next release | next release + 6 months |
| `Conntrack` `protocol` (`list_connections`, `count_connections`, `get_connection`, `drop_connection`): `RuleProtocol \| str` | `RuleProtocol` (narrows to the enum) | parameter | next release | next release + 6 months |
| Wi-Fi `band` (`WifiBss.create_bss`, every `WifiRadio` and `WifiRf` member, `WifiRadioWhiteBox.inject_radar_event`, `WifiMesh.set_backhaul_band`, annotated `WifiBand \| str \| None`; `WifiRadio.get_modes` is excepted, it takes the bare `WifiBand`): `WifiBand \| str` | `WifiBand` (narrows to the enum; `WifiMesh.set_backhaul_band` narrows to `WifiBand \| None`, the `None` releasing the band constraint stays) | parameter | next release | next release + 6 months |
| `WifiBss.create_bss(security_mode, mfp)` and `set_security(mode, mfp)`: `WifiSecurityMode \| str`, `MfpMode \| str` | `WifiSecurityMode`, `MfpMode` (narrows to the enum) | parameter | next release | next release + 6 months |
| `WifiBss.set_acl_mode(mode)`: `WifiAclMode \| str` | `WifiAclMode` (narrows to the enum) | parameter | next release | next release + 6 months |
| `WifiRadio.set_mode(mode)`: `WifiPhyMode \| str` | `WifiPhyMode` (narrows to the enum; a compound mode names no member) | parameter | next release | next release + 6 months |
| `WifiClient.set_wlan_scan_channel(channel)`: `int \| str` | `int` | parameter | next release | next release + 6 months |
| `SipPhone.wait_for_state(state)`: `PhoneState \| str` | `PhoneState` (narrows to the enum) | parameter | next release | next release + 6 months |
| `HttpClient.curl(protocol)`: `HttpScheme \| str` | `HttpScheme` (narrows to the enum) | parameter | next release | next release + 6 months |
| `IpInterface.set_link_state(state)`: `LinkAdminState \| str` | `LinkAdminState` (narrows to the enum) | parameter | next release | next release + 6 months |
| `UpnpClient.create_upnp_rule(protocol)` and `delete_upnp_rule(protocol)`: `PortMappingProtocol \| str` | `PortMappingProtocol` (narrows to the enum) | parameter | next release | next release + 6 months |
| `QoeBrowser.measure_productivity(scenario, wait_until)`: `QoeScenario \| str`, `PageCompletion \| str` | `QoeScenario`, `PageCompletion` (narrows to the enum) | parameter | next release | next release + 6 months |
| `HttpServer.start_http_service` / `stop_http_service(port)` and `start_http_service(ip_version)`: `str` | `int`, `IpFamily` (announced narrowing) | parameter | next release | next release + 6 months |
| `UpnpClient` `int_port`, `ext_port` and `VlanClient` `vlan_id`: `str` | `int` (announced narrowing) | parameter | next release | next release + 6 months |
| `IpRouting.traceroute(version)`: `str` (`""` or `"6"`) | `IpFamily \| None` (announced narrowing) | parameter | next release | next release + 6 months |
| `IpInterface.is_link_up(pattern)` | `is_link_admin_up` for the administrative state; at removal `pattern` goes | parameter | next release | next release + 6 months |
| `NetemController.set_impairment_profile` / `set_interface_profile(profile)` as a `dict` | `ImpairmentProfile` (narrows to it) | parameter | next release | next release + 6 months |
| `MulticastClient.send_mldv2_report` records as plain tuples | `GroupRecord` (narrows to `Sequence[GroupRecord]`) | parameter | next release | next release + 6 months |
| `HeldPrefixes.hold(address)`: `str` | `IPv4Interface \| IPv6Interface` (announced narrowing) | parameter | next release | next release + 6 months |
| `PacketFilter.get_default_policy` return `str` | `DefaultAction` (announced narrowing) | member | next release | next release + 6 months |
| `WifiRadio.list_radios` and `get_bandwidth` returns (`list[str]`, `int`) | `list[WifiBand]`, `ChannelWidth` (announced) | member | next release | next release + 6 months |
| `RadiusServer.get_status` return `str` | `ServiceStatus` (announced narrowing) | member | next release | next release + 6 months |
| `SipServer.verify_sip_message(since)`: `Any` | `datetime \| None` (announced narrowing) | parameter | next release | next release + 6 months |
| `HwConsole.get_console` and `get_interactive_consoles` returns `Any`, `dict[str, Any]` | `Console`, `Mapping[str, Console]` (announced narrowing; a console lacking a `Console` member stops conforming then) | member | next release | next release + 6 months |
| `FirewallRule.dst_port` (port text, required) | `dst_ports`; at removal the text field goes and `dst_ports` becomes required | field | next release | next release + 6 months |
| `NatRule.dst_port` and `translated_port` (port text, released default `""`) | `dst_ports`, `translated_ports`; at removal the text fields go and the typed fields default to `()` (the typed form of the released default `""`) | field | next release | next release + 6 months |
| `L3Rule.src_port` and `dst_port` (port text, released default `"any"`) | `src_ports`, `dst_ports`; at removal the text fields go and the typed fields default to `()` (the typed form of the released default `"any"`) | field | next release | next release + 6 months |
| `SecurityEvent.ts` (ISO-8601 text, required) | `timestamp`; at removal `ts` goes and `timestamp` becomes required (`None`: no time reported) | field | next release | next release + 6 months |
| `QosRule.match` (classifier text, required) | `classifier`; at removal `match` goes and `classifier` becomes required (`None`: every frame) | field | next release | next release + 6 months |
| `FirewallRule.action` / `protocol`: `FirewallRuleAction \| str`, `RuleProtocol \| str` | the enums (narrows from `E \| str` to `E`) | field | next release | next release + 6 months |
| `NatRule.mode` / `protocol`: `NatMode \| str`, `RuleProtocol \| str` | the enums (narrows from `E \| str` to `E`) | field | next release | next release + 6 months |
| `PortMapping.protocol`, `Connection.protocol`: `PortMappingProtocol \| str`, `RuleProtocol \| str` | the enums (narrows from `E \| str` to `E`) | field | next release | next release + 6 months |
| `LinkStatus.state`, `LinkHealthReport.state`: `UplinkState \| str` | `UplinkState` (narrows from `E \| str` to `E`) | field | next release | next release + 6 months |
| Wi-Fi fields: `band` of `WifiBssConfig`, `WifiStation`, `WifiNeighbor`, `WifiChannelUtilization`, `WifiRadioStats`, `WifiMeshLink`; `WifiBssConfig.security_mode` / `mfp`; `WifiAcl.mode`; `role` of `WifiMeshStatus`, `WifiMeshNode` | `WifiBand`, `WifiSecurityMode`, `MfpMode`, `WifiAclMode`, `MeshRole` (narrows from `E \| str` to `E`) | field | next release | next release + 6 months |
| `MeasurementSpec.tool` / `completion`, `TrafficSpec.protocol` | `QoeTool`, `QoeCompletion \| PageCompletion`, `TransportProtocol` (narrows from `E \| str` to `E`) | field | next release | next release + 6 months |
| `NatRule.src_cidr`, `dst_cidr`, `translated_src`, `translated_dst` (`""`: absent) | `str \| None`, `None` absent (announced) | field | next release | next release + 6 months |
| `L3Rule.src_cidr`, `dst_cidr` (`"any"`), `UplinkStatus.ip`, `gateway`, `public_ip`, `primary_dns` and `NetworkAttachment.segment` (`""`) | `str \| None`, `None` unconstrained or not reported (announced) | field | next release | next release + 6 months |
| `LinkStatus.ip_address` (`""`: no address) | `str \| None` (announced) | field | next release | next release + 6 months |

**testoperations**

| item | replacement | kind | deprecated in | earliest removal |
| --- | --- | --- | --- | --- |
| `testoperations.segmentation:build_deny_rule(scope, proto)` as a plain `str` | `DenyScope`, `RuleProtocol` (narrows to the enum) | parameter | next release | next release + 6 months |
| `testoperations.netem_controller:apply_preset(preset_name)` as a plain `str` | `NetemPreset` (narrows to the enum) | parameter | next release | next release + 6 months |
| `testoperations.throughput:NonCompletion(which_side, what)` as a plain `str` | `NonCompletionSide`, `NonCompletionKind` (narrows to the enum) | parameter | next release | next release + 6 months |
| `testoperations.iperf_generator:saturate_link(protocol)` as a plain `str` | `TransportProtocol` (narrows to the enum) | parameter | next release | next release + 6 months |
| reading `IperfSession`, `HomeVerification` or `FlowPair` as the released dict (indexing, `get`, `in`, `len`, `keys`, `items`, `values`, iteration, `==` a dict, `as_dict()`) | the record's fields; the mapping access is removed | member | next release | next release + 6 months |
