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

- no entries yet

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
- **operation** `testoperations.segmentation:derive_decoy_target` — derive
  an inert deny target from a documentation range, with a fail-closed
  non-collision check against the caller's in-use CIDRs; returns a
  `DecoyDerivation`, assertion-free. No proposal; PR #25.

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
- **operation** `testoperations.path_placement:locate_streams_by_size` —
  locate each stream's path by its size signature, one shared window across
  paths. No proposal; PR #19.
- **operation** `testoperations.path_placement:await_stream_on_path` — a
  caller-anchored bounded await returning a `ConvergenceRecord`; the budget
  verdict stays with the caller. No proposal; PR #19.
- **operation** `testoperations.iperf_client:sender_life_record` — parse a
  stopped sender's interval reports into a `SenderLifeRecord` (intervals,
  gaps, total bytes). No proposal; PR #19.
