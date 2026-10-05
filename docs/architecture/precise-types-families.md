# Design: reviewed families and substrate surveys for the precise-types retypes

| Field   | Value |
| ------- | ----- |
| Status  | Implemented, unreleased (ratified by the merge of the precise-types change) |
| Author  | rjvisser |
| Date    | 2026-10-05 |
| Related | `docs/architecture/precise-types-design.md` (the retypes and the deprecation rules), `docs/proposals/2026-10-05-precise-types.md` (items P6 to P11, the evidence in full), `docs/architecture/packet-injection-substrate-design.md` §2 (the substrate-tool rule), `docs/architecture/sdwan-appliance-protocol-design.md` and `docs/architecture/l2-switch-protocol-design.md` (the appliance and switch lists, reused), `docs/architecture/capability-only-archetypes.md`, `packages/testprotocols/GAPS.md` |

## 1. What this records

The precise-types change retypes released contracts in domains that had no recorded
reviewed-family list: Wi-Fi, voice and SIP, the host network tools, SNMP and NTP, traffic
generation, impairment and QoE, and device management, content filtering and consoles.
This document records each list, one line of rationale per family, so that the next
change in the domain is checked against the same families. The SD-WAN appliance and L2
switch domains keep the lists their own design documents record.

Two bars apply, as recorded elsewhere:

- **A device-under-test contract** (Wi-Fi, voice, device management, content filtering)
  is checked against representative, independent, documentation-published families,
  standards first where a standard data model exists.
- **A host-substrate instrument** (the host network tools, SNMP and NTP clients, traffic
  generation, impairment, QoE) proves its neutrality by tool universality, not by a
  cross-vendor sweep: `packet-injection-substrate-design.md` §2 records that every
  substrate tool in the class of `NmapScanner`, `PcapCapture`, `NetemController`,
  `IperfGenerator` and `NetworkProbe` landed as a single-substrate host-tool wrapper. The
  same document still records a substrate survey with a vendor-free reference, and so do
  sections 5 and 6 here.

Product and tool names appear in this document as the concept check only, never in a
protocol, model or enum name.

## 2. Wi-Fi

Reference first: Wi-Fi Data Elements (JSON schema v3.0), Wi-Fi EasyMesh v6.1 and TR-181
Device:2.21 (`Device.WiFi.Radio`, `AccessPoint`, `AssociatedDevice`,
`NeighboringWiFiDiagnostic()`, `DataElements`). The vocabularies come from IEEE 802.11
(bands; widths up to 320 MHz from 802.11be; the a to be amendments; MFP from 802.11w) and
the Wi-Fi Alliance security programmes (WPA2, WPA3, Enhanced Open). Each family was then
compared with the reference from its public material.

| Family | Rationale |
| --- | --- |
| hostapd-based access points (OpenWrt; prplOS with prplMesh) | The open reference stack: `hw_mode`, `wpa_key_mgmt`, `ieee80211w` and `macaddr_acl` give every vocabulary directly, and prplMesh is an EasyMesh implementation. |
| A Broadcom- or Qualcomm-based residential gateway stack | The chipset stacks of most residential gateways; their SDKs are not public, so this family is evidenced through TR-181 only. |
| Meraki MR (Dashboard API) | A cloud-managed enterprise family with a published API; it splits the security mode into two fields and has no per-SSID MAC list. |
| Aruba (AOS 8 and AOS 10, Instant, Central) | A controller- and cloud-managed enterprise family; per-SSID HT/VHT/HE switches, `opmode` plus transition mode, MAC authentication and a client deny list. |
| Airties (mesh controller and agent on gateways and extenders, including prplOS-based gateways; cloud management) | An EasyMesh mesh family; it publishes no field-level API of its own, so its evidence is Data Elements (served with `X_AIRTIES_` extensions) and EasyMesh. |
| A Linux station using wpa_supplicant | The client side: key management, `ieee80211w` and the nl80211 channel list. |

Differences resolve as recorded in `precise-types-design.md` ("Wi-Fi vocabularies"): a
spelling, unit or encoding difference is a driver mapping; a value or source a family
lacks is a known gap, entered in `GAPS.md` (2026-10-05, "Wi-Fi: concepts the reviewed
families have and the contract cannot express"). The per-radio retry and failed counts,
which most of these families do not report, are the one released field widened with no
deprecation period (see `precise-types-design.md`, "The no-period exception").

## 3. Voice and SIP

Reference: RFC 3261 (SIP methods and responses), RFC 3842 (message-summary bodies) and
RFC 3863 (presence basic status). The call states are the contract's own `SipPhone`
predicates, not a vendor vocabulary.

| Family | Rationale |
| --- | --- |
| A SIP proxy / registrar (Kamailio or OpenSIPS) | The server side of registration and routing; its stored-message module (Kamailio `msilo`) stores sender, body and time, the fields of `OfflineMessage`. |
| An RTP relay (rtpengine) | The media relay behind the proxy; the one relay seen, so `RtpStats` holds only the two figures its implementer returns and its callers read. |
| A PBX (Asterisk) | An independent server family that emits RFC 3842 message-waiting bodies (`MwiStatus`). |
| SIP user agents: a softphone (PJSUA) and a residential gateway's FXS port | The two client shapes a voice test drives; they consume message-waiting and produce the call states. |

Presence words and SIP methods are open sets (RFC 3863 plus provider extensions; RFC
3261 plus extensions), so they stay `str`.

## 4. Host network tools

The "families" are the host tools the drivers run; the instrument class is the one
`packet-injection-substrate-design.md` §2 records.

| Family | Rationale |
| --- | --- |
| Linux hosts with iproute2, curl, nmap, bind9 `dig`, iputils `ping` and net-tools `arp` | The tools the released implementers run; the typed parameters and records are their documented options and outputs (`--noproxy`, `-k`, `-L`; nmap `-F` and `-oX`; the `ping` summary lines; the `arp -n` columns; the `UP` flag of `ip link show`). |
| BusyBox equivalents on embedded hosts | An independent implementation of the same tools on gateways and small hosts; its `ping` summary and `arp` output give the same facts. |

Vendor-free references: the IANA DNS resource-record registry (`DnsRecordType`), the UPnP
IGD `AddPortMapping` `NewProtocol` argument (`TCP` or `UDP`), and the nmap reference guide's
six port states.

## 5. SNMP and NTP: substrate survey

`SnmpClient` and `NtpClient` are host-substrate instruments: a test host queries or sets
the device under test with a client tool. Under the substrate-tool rule
(`packet-injection-substrate-design.md` §2) a single-substrate wrapper clears the bar; the
survey below is substrate evidence, not a supported-backends list.

The vendor-free reference is the protocol itself: RFC 3416 (the SNMP operations: get,
get-next as walked, set, get-bulk with `non-repeaters` and `max-repetitions`) and RFC
2578 (the SMI base types, which `SnmpValueType` follows, plus the BITS construct; counters
are left out because no object takes a SET on one). The members carry those operations and
types, not a tool's syntax.

| Substrate | Class | get | walk | set | bulk get | Note |
| --- | --- | :-: | :-: | :-: | :-: | --- |
| Net-SNMP command-line tools (`snmpget`, `snmpwalk`, `snmpset`, `snmpbulkget`) | OSS tool | ✓ | ✓ | ✓ | ✓ | The released implementers' family: `-v 2c -On -c <community> -t <seconds> -r <retries>`, the parameters typed here; the `snmpset` type letters (`i`, `u`, `s`, `o`, `a`, `t`, `b`) map one to one onto `SnmpValueType`. |
| pysnmp (a pure-Python SNMP engine) | OSS library | ✓ | ✓ | ✓ | ✓ | An independent client family with no shared code: its get, next, set and bulk commands take the same community, timeout, retry count and RFC 2578 value types, so a driver maps the members onto it the same way. |

The members return the tool's output text, as the released member did; a typed varbind
record waits for a second implementer's parse (`GAPS.md`, 2026-10-05, "`SnmpClient` typed
varbind return").

NTP: the vendor-free reference is the device's own date (`read_date` returns a
`datetime`, naive in the device's local time unless the device reports its offset;
`None` when the device gives no date to read). The one `set_date` option seen is
`date -s`; `set_date_time` takes a `datetime` and leaves the formatting to the driver, so
any client whose date-setting command takes a date and time maps onto it.

## 6. Traffic generation, impairment and QoE: substrate survey

`IperfClient`, `IperfServer`, `NetemController` and `QoeBrowser` are host-substrate
instruments of the same class, and the same rule applies.

| Substrate | Concern | Class | Note |
| --- | --- | --- | --- |
| iperf3 | traffic | OSS tool | The released implementers' family; the session parameters (`-c`, `-p`, `-b`, `-B`, `-4` / `-6`, `-u`, `-t`, `--cport`, `-R`, `-O`, `-J`, `-w`, `-P`, `-l`, `-i`) are the keyword parameters of `start_sender_session`. |
| iperf2 | traffic | OSS tool | An independent implementation with most of the same options; it lacks `-J` and `--cport`, so a driver for it raises on those. Its window is a size with binary suffixes too, hence `window_bytes`. |
| Linux `tc` with `netem` | impairment | OSS tool | The released implementers' family: `delay <latency> <jitter>`, `loss`, `duplicate`; a blackout is 100 % loss. The transient-event fields are the keywords the released implementers read. |
| FreeBSD `dummynet` (`ipfw` pipes) | impairment | OSS tool | An independent kernel family: a pipe's `delay` and packet-loss rate (`plr`) carry the latency and loss fields of the events, so `Blackout` and a loss-only `PacketStorm` map onto it directly; jitter and duplication have no plain pipe option, and a driver raises when one is requested (the contract's rule for a field the driver cannot apply). |
| Playwright | QoE | OSS library | The released implementers' family: its `wait_until` load states `load`, `domcontentloaded`, `networkidle`, `commit` are `PageCompletion`. |
| Puppeteer | QoE | OSS library | An independent browser-automation family: its `waitUntil` values `load`, `domcontentloaded` and `networkidle0` give three of the four completions; `commit` has no form there, and a driver raises for it. |

Vendor-free references: RFC 6349 (the TCP throughput testing framework, the measurement
the traffic members serve) and the IP performance metrics for the impairments, RFC 7679
(one-way delay), RFC 7680 (one-way loss) and RFC 3393 (delay variation, the jitter field);
for QoE, the HTML standard's `DOMContentLoaded` and `load` events. The completions
`duration`, `response` and `connect` come from the tool-by-completion matrix of a released
implementer framework's QoE specification.

`inject_event` is a lever: its confirming observation is the impairment seen on the path by
the measurement around it, stated in the member's docstring.

## 7. Device management, content filtering and consoles

| Family | Concern | Rationale |
| --- | --- | --- |
| Linux hosts and gateways (procps `ps`, `free`, BSD syslog) | device management | The released implementers' family: `MemoryUtilization` holds the columns of `free -b`, `ProcessInfo` those of `ps -A`, `EventLogEntry` an RFC 3164 line with its severity derived by the RFC 5424 table. |
| The SD-WAN appliance families of `sdwan-appliance-protocol-design.md` | content filtering | The appliance list already recorded. `UrlRules` (`allowed`, `blocked`) is the shape of Meraki MX (`allowedUrlPatterns`, `blockedUrlPatterns`) and FortiGate (URL filter entries with allow or block actions); Catalyst SD-WAN, Prisma SD-WAN and VeloCloud were not checked for this record and are the first to check when the member next changes. |
| pexpect-based consoles (serial, SSH, telnet) | consoles | The console objects released implementers return; a type-checked test confirms that a `pexpect.spawn` subclass with `execute_command` and `start_interactive_session` satisfies `Console`. |

## 8. `Console` is a returned-object contract, not a capability

`testprotocols.hw_console.Console` describes the objects `HwConsole.get_console` and
`get_interactive_consoles` hand out: `execute_command`, `sendline`, a read-only `before`
and `start_interactive_session`. It is not a capability:

- no device archetype composes it, and no archetype gains a `Console` attribute;
- it is counted in no capability inventory, and its members are counted under no
  capability's new-mandatory-member total;
- a driver never implements it as a capability of a device: the console it returns
  satisfies it structurally, without inheriting from it.

So the capability-only-archetypes rule (`capability-only-archetypes.md`) is untouched: an
archetype still composes capabilities only. `HwConsole` keeps its released `Any` returns
under the compatibility exemption; the docstrings state that the returned objects satisfy
`Console`, and the narrowing of the returns to `Console` is announced in the Deprecations
table of `precise-types-design.md`.
