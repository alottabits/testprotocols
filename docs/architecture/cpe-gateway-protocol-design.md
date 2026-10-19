# Design: vendor-neutral **CPE gateway** archetype

| Field | Value |
| --- | --- |
| Status | chartered |
| Author | rjvisser |
| Date | 2026-10-19 |
| Related | `docs/archetypes/README.md` (the track), `docs/architecture/managed-router-protocol-design.md` (the chartered sibling), `packages/testprotocols/src/testprotocols/devices/cpe.py` (the archetype this charter rebuilds), `packages/testprotocols/GAPS.md` (`L2Bridge`, 2026-05-02), `docs/architecture/l2-switch-protocol-design.md` (the shared STP/FDB vocabulary), `packages/testprotocols/SPLITS.md`, `packages/testprotocols/LEVELS.md` |

This charter describes the class that the registered `linux_cpe` archetype
(`CpeDevice`) already names. That archetype predates the archetype track and
never had a design document, a cross-family matrix or reference drivers; this
is the track pass that gives the class all three. The boundary section says
how the existing archetype relates to the result.

## 1. Charter

### The class, by the operations it publishes

A **CPE gateway** is the residential or small-business gateway at the edge of
an access network — a closed product, not a general-purpose host — that
terminates one WAN access (Ethernet, xDSL, fibre, cable or cellular) and
publishes on its management planes the operations that define the class:

- **the WAN connection as a managed object** — its mode (an address by DHCP, a
  PPPoE session, a static address, IPoE with a VLAN tag and priority), its
  credentials, its addressing (IPv4, IPv6 with a delegated prefix, the
  provisioning mode), its state, and the state of the link beneath it;
- **LAN services** — a DHCP server with pools, options and reservations; a DNS
  forwarder with upstream servers and local overrides; the bridge that joins
  the LAN ports and the wireless networks, with a guest segment kept apart;
  the state of the LAN ports;
- **Wi-Fi access points** — radios and their settings, the networks they
  carry, the stations attached, onboarding, and client steering between bands;
- **a security posture between WAN and LAN** — the zone defaults, inbound port
  forwards, egress filters, per-host blocking and schedules, and automatic
  port mapping requested by LAN hosts;
- **the table of hosts behind it**, wired and wireless, with address, name and
  attachment;
- **device operations** — identity, health (uptime, load, memory), logs and
  their export, time synchronisation, firmware upgrade, factory reset,
  configuration backup and restore, the local administrator credential;
- **remote management by an auto-configuration server** — TR-069 (the ACS
  endpoint and credentials, periodic inform, connection requests) and USP
  (the controller endpoint and its transport);
- on many models, **voice** (SIP accounts and their registration, FXS lines
  and their state) and a **mesh controller** (the agents, their backhaul
  links, steering of a client between agents).

How that management plane is reached — a shell with a configuration
utility, a TR-181 data-model CLI, a SOAP/UPnP API on the LAN side, a
proprietary CLI — is a driver concern and plays no part in the definition.
Who manages the device, the operator through an ACS or the household through
a local interface, is not a shape fact either: both publish the same
operations. An instance belongs to the archetype when its driver publishes
the members; the `isinstance` gate decides.

The class spans three device classes that recur across vendors: the
**operator-managed access gateway** (cable, fibre, xDSL, with cellular where
offered; managed through an ACS, often with voice); the **retail router**
(bought by the household, managed locally or through an app, often the
controller of a mesh); and the **small-business gateway** (the retail set with
VLANs and a site-to-site VPN). Capability presence is platform-scoped inside
every family — a retail router may publish no ACS client, an operator gateway
no local administrator credential, a bridged modem no Wi-Fi — so the contract
needs per-method unsupported signalling even inside one family, and the design
(not this charter) decides the core and the tiers under the evidence bar as
amended on 2026-10-19 (a tier supported on a majority of the ratified list is
built with the archetype).

Standalone Wi-Fi extenders and mesh agents are out of scope as devices: the
class sees them as agents in the controller's topology. Driving an agent
directly is a separate request.

### Boundary with the registered archetypes

- **`linux_cpe` (`CpeDevice`) — the archetype this charter rebuilds.** It
  names this class and predates the track. *Over*-specified: it mandates the
  full Wi-Fi stack (`wifi_radio`, `wifi_bss`, `wifi_stations`, `wifi_rf`,
  `wifi_transitions`, `wifi_onboarding`), a hardware console (`hw_console`)
  and host-substrate levers (`ip_interface`, `ip_routing`, `conntrack`, host
  `nat`); a gateway reached through a SOAP API or a data-model CLI publishes
  none of the four host levers, several families publish no console, and a
  bridged modem publishes no Wi-Fi. *Under*-specified: no WAN connection object, no
  DHCP server, DNS forwarder or bridge (`GAPS.md`, `L2Bridge`, 2026-05-02,
  whose trigger is this class), no host table, no identity read, no
  configuration backup and restore, no USP, no voice, no mesh. Health and
  logs it has: `DeviceManagement` publishes uptime, load, memory, process
  state and log reads, and is the reuse candidate for both. A tier of it cannot close the
  over-specification, because its mandatory members stay mandatory; extending
  it member by member would keep its one consumer on a shape no matrix has
  tested. The design decides the mechanism on the placement ladder — evolve
  in place through `extend` and `deprecate`, or supersede under a new registry
  name with the old one deprecated — and the recorded deprecation period
  applies either way. This charter commits to the class, not to the mechanism.
- **`managed_router` (chartered,
  `docs/architecture/managed-router-protocol-design.md`; not yet registered).**
  The sibling closed network product. Shared services — NAT, zone firewall,
  DHCP server, on-box probes, time synchronisation, log export — are shared
  by **reuse of the same capability protocols**, not by one archetype
  extending the other; software image lifecycle and configuration transfer
  are demands both charters carry and whose placement each design decides,
  so the two designs record the dependency on each other's rows rather than
  assume a shared protocol. Identity and health are demands of this class
  only (I25, I26); the router charter does not list them. The router publishes what the gateway does
  not: routing tables and peers, first-hop redundancy, own-traffic capture,
  QoS by class, operator authentication against a central server. The gateway
  publishes what the router does not: the WAN connection as an access object
  with credentials, Wi-Fi access points, a host table, remote management by
  an ACS, voice lines, a mesh controller. Neither is a tier of the other.
- **`sdwan_appliance` (`SdwanApplianceDevice`)** — *over*-specified: its
  mandatory members include a WAN-uplink object model, SD-WAN policy and
  security bundles and controller ownership that a gateway does not publish.
  *Under*-specified: no Wi-Fi access point, no DHCP server, no host table, no
  ACS management, no PPPoE or IPoE connection object. Its `DeviceInfo`,
  `SyslogConfig` and `ApplianceNat` (`appliance_nat`, the port-forward table
  rather than the host primitives) members are reuse candidates for the
  design.
- **`linux_sdwan_router` (`SdwanRouterDevice`, the Linux twin)** —
  *over*-specified: host-substrate levers (`ip_interface`, `conntrack`,
  `pcap`, host `nat`, `wan_admin`) that a closed gateway does not expose;
  *under*-specified as the appliance is.
- **`managed_switch_l2`, `managed_switch_l3`, `managed_switch_l3_routed`** —
  *under*-specified: no WAN access, NAT, Wi-Fi, stateful firewall or ACS
  management. *Over*-specified: every one mandates the switch port layer
  (`switch_ports`, `switch_vlans`, `spanning_tree`, `link_aggregation`,
  `port_poe`, `port_security`, `storm_control`, `mac_table`, `port_status`,
  `placement`),
  which a gateway with four LAN ports behind one bridge cannot satisfy. The
  L2 switch design (2026-06-14) deliberately left the bridge-native shape to
  this class and placed the shared STP and FDB vocabulary in
  `models/l2_common.py` for it; this charter takes that up. A gateway's LAN
  port state (link, speed, duplex) has `port_status` (`PortStatus`, the
  read-only per-port state) as its reuse candidate; `switch_ports` is the
  configuration object and is not.
- **The test-bed hosts** — `linux_lan_client`, `linux_wlan_client`,
  `linux_qoe_client`, `linux_qoe_measurement_client`, `linux_sip_phone`,
  `linux_sip_server`, `linux_wan_server`, `linux_traffic_controller`,
  `iperf_traffic_generator`, `linux_acs`, `linux_provisioner`, `linux_tftp` —
  are not network elements under test; none overlaps. `linux_acs` is the far
  end of the gateway's TR-069 client, and `linux_provisioner` carries the
  test-bed's `DhcpServer`, whose shape the design examines for reuse by the
  gateway's own DHCP server.

The conclusion is an archetype that composes what a CPE gateway publishes,
reusing existing capability protocols wherever their shape holds, and that
resolves the existing `linux_cpe` archetype into it on the placement ladder.

### Trigger families

The triggering consumer runs two families, reviewed at these public version
lines:

- **prplOS, the prplWare 4.0 line and later.** The prpl Foundation's
  open-source carrier gateway stack: OpenWrt-based, with an Ambiorix TR-181
  data model, the iCWMP TR-069 client and prplMesh. Public release tags on
  the prpl Foundation GitLab project (`prpl-foundation/prplos/prplos`, tags)
  show the 4.0 line maintained (prplware-v4.0.4, October 2026) beside the 5.x
  line (prplware-v5.2.0, October 2026). The 4.0 line is the floor because it
  is the line the consumer runs; a 5.x revision joins by a dated note where
  its evidence differs.
- **OpenWrt, the 24.10 line, with icwmp from the public iopsys feed as its
  TR-069 client.** The substrate under prplOS and under many retail routers;
  UCI and ubus; no TR-181 data model, no mesh controller. The 24.10 line is
  the old-stable series since 25.12 (25.12.6 released 18 October 2026;
  24.10.8 on 26 July 2026) and is the floor because it is the line the
  consumer runs and the base prplOS builds on; a 25.12 revision joins by a
  dated note where its evidence differs. The family is named with its TR-069 client
  because the four official OpenWrt feeds (`packages`, `luci`, `routing`,
  `telephony`) at `openwrt-24.10` carry no CWMP or USP client: icwmp (iopsys,
  BSD 3-Clause, https://dev.iopsys.eu/bbf/icwmp) is packaged in the public
  iopsys feed and in prplOS. With it, remote management over TR-069 is
  reached on OpenWrt through the `cwmp` UCI section and the `tr069` ubus
  object, and on prplOS through the TR-181 `Device.ManagementServer.` object:
  two mechanisms for the same operations, which is what two trigger families
  are for. USP is not named: the Broadband Forum's OB-USP-Agent has no
  OpenWrt packaging outside the prpl and iopsys feeds, so the design places
  USP on the other families' evidence.

Both families run on commodity single-board hardware and in containers, so
every cell of their matrix columns is reproducible from public material.

### Reviewed-family list (proposed for ratification)

Five families: the two trigger families plus three competitors.

| Family | Role | Reason in |
| --- | --- | --- |
| prplOS, prplWare 4.0 line and later | trigger | triggering consumer; operator-managed access gateway class; TR-181 data model, TR-069, USP, mesh controller |
| OpenWrt, 24.10 line, with icwmp (iopsys feed) | trigger | triggering consumer; the substrate under prplOS and many retail routers; UCI/ubus with a packaged TR-069 client, no data model, no mesh |
| RDK-B, quarterly releases `rdkb-2025q4-kirkstone` and later | competitor | the other open operator gateway stack (cable and fibre); `dmcli` over TR-181 with `X_RDK_` extensions; the 2026q1 release moves the lead reference platform from Raspberry Pi 4 to Banana Pi R4 |
| FRITZ!OS 8.20 and later (AVM FRITZ!Box) | competitor | the retail and small-business gateway with a fully published SOAP/UPnP management API (TR-064, about fifty services) and **no CLI** (AVM states Telnet is unsupported since FRITZ!OS 6.25); the family that tests whether the shape survives a read-rich, write-narrow API |
| MikroTik RouterOS v7 | competitor | the same family line the managed-router charter reviews, here on its low-end routers used as CPE; the first "one OS, two archetypes" data point for the composition question; v6 is out |

Excluded, with reasons: **operator ONTs on vendor firmware** (Huawei
EchoLife, Nokia ONT lines — public documentation is partial and
vendor-controlled, so a reference driver would be mostly unsupported cells
with weak citations); **Technicolor and Sagemcom gateways** (their current
lines run RDK-B or prplOS and are covered by those families); **Ubiquiti**
(UniFi gateways are controller-managed and EdgeOS is effectively end of
development, as the managed-router charter found); **consumer mesh systems**
managed only through a vendor app (no published management plane).

Also excluded, with reasons: **ADTRAN SmartOS** (SmartOS 11 and later
realizes the principles and best practices of the prplWrt project, the
predecessor of prplOS, so its published operations are covered by the prplOS
family; a dated revision brings it in if its data model diverges); **Zyxel**
(operator and retail gateways on vendor firmware managed
through a web interface and TR-069, with no published management-plane
documentation beyond the TR-069 data model that the RDK-B, prplOS and
FRITZ!OS columns already exercise); **TP-Link** (retail routers managed
through a web interface and a vendor app, no published management API);
**Calix** (operator gateways on vendor firmware managed through the vendor's
cloud, no published device-side API). Each can join the list by a dated
revision that cites a published management plane.

Five families give denominators with meaning under the evidence bar as
amended on 2026-10-19: a core member is supported on both trigger families
and on a majority of the five; a tier is built with the archetype when its
members are supported on a majority of the five; anything else is
`tier-staged` or a documented per-method unsupported case. FRITZ!OS's narrow
write side is where the majority rule is expected to bite, and that is the
point of including it.

### Sources for the version lines

- prplOS release tags: https://gitlab.com/prpl-foundation/prplos/prplos/-/tags
  (prplware-v4.0.4, 2 October 2026; prplware-v5.2.0, 7 October 2026).
- OpenWrt 24.10: https://openwrt.org/releases/24.10/start (24.10.8 released
  26 July 2026; https://openwrt.org/ names 25.12.6 of 18 October 2026 as the
  current stable and 24.10 as old-stable). The official feeds at the 24.10
  branch:
  https://github.com/openwrt/packages/tree/openwrt-24.10,
  https://github.com/openwrt/luci/tree/openwrt-24.10,
  https://github.com/openwrt/routing/tree/openwrt-24.10,
  https://github.com/openwrt/telephony/tree/openwrt-24.10 — none carries a
  CWMP or USP client.
- icwmp: https://dev.iopsys.eu/bbf/icwmp (BSD 3-Clause); the iopsys feed:
  https://dev.iopsys.eu/feed/iopsys.
- RDK-B quarterly releases: https://wiki.rdkcentral.com/x/tXtkH
  (RDKB_2026q1_kirkstone: the Banana Pi is the lead reference gateway
  platform and the Raspberry Pi 4 is no longer supported; its changelog is
  against rdkb-2025q4-kirkstone). `dmcli`:
  https://developer.rdkcentral.com/documentation/?p=9589.
- FRITZ!OS: https://fritz.com/en/pages/interfaces (the TR-064 service list,
  documents for FRITZ!OS 8.20 and 8.25);
  https://en.fritz.com/service/knowledge-base/dok/FRITZ-Box-7490/1635_Access-to-the-FRITZ-Box-via-Telnet-is-not-supported
  (Telnet unsupported since FRITZ!OS 6.25).
- RouterOS v7: https://mikrotik.com/download/changelogs (the v7 stable
  channel), as the managed-router charter cites.
- ADTRAN SmartOS on prplWrt: the SmartRG (ADTRAN) release of SmartOS 11,
  "which realizes the principles and best practices established by the
  prplWrt project":
  https://www.nasdaq.com/press-release/smartrg-first-to-deliver-open-cpe-solutions-2019-10-23

### Demand

The demand evidence is public: the archetype request
https://github.com/alottabits/testprotocols/issues/98, intents I1–I35. They
map onto the operations above as follows: I1–I5 the WAN connection object
and its link; I6–I9 the LAN services and the LAN port state; I10–I14 the
Wi-Fi access points; I15–I19 the security posture and host filtering; I20–I21
remote management; I22–I28 lifecycle, identity, health, logs and time; I29 the
host table; I30 the administrator credential; I31–I32 voice; I33–I35 the mesh
controller.

The design, not this charter, places the following on the matrix evidence —
in the core, in a tier built with the archetype, or `tier-staged`: USP
(I21), onboarding and client steering (I13, I14), host filtering and
schedules (I18), automatic port mapping (I19), configuration backup and
restore (I24), the administrator credential (I30), voice (I31–I32) and the
mesh controller (I33–I35). Remote management over TR-069 (I20) is a core
candidate on the trigger-family definitions above.

## 2. Cross-family matrix

✓ = fully present · ◐ = partial or caveated, the limit named in the cell ·
✗ = absent, the absence named in the cell. Every cell carries `[n]`, a
numbered source in the family's list under §10. A cell is ✓ only where the
family's own documentation names the operation (a command reference, a
service document, a data-model plugin's README that lists the object, a
project wiki page); a cell that rests on the TR-181 data-model definition
alone is ◐ and a verification item. A public observation of the operation on
prplOS 4.0.3 (the triggering consumer's public example) may lift a prplOS
cell to ✓ when cited as an observation with its path. The columns are the
five ratified families at the charter's version lines; the OpenWrt column is
the 24.10 line with icwmp from the iopsys feed as its TR-069 client. Every
◐ and ✗ cell is a stage-4 verification item (§9). The `Id` column is a
working id for the exploration and the review; the design decides whether
it stays.

| Id | Operation | prplOS 4.0 line | OpenWrt 24.10 line + icwmp | RDK-B 2025q4+ | FRITZ!OS 8.20+ | RouterOS v7 |
| --- | --- | :--: | :--: | :--: | :--: | :--: |
| | **WAN connection** |  |  |  |  |  |
| R1 | Set the WAN connection mode (DHCP, static, PPPoE, IPoE) | ✓ [1] | ✓ [1] | ✓ [1] | ◐ SetConnectionType only routed/bridged; no static/DHCP/IPoE selector [1] | ◐ no WAN-mode selector; add dhcp-client, pppoe-client or address object [1] |
| R2 | Read WAN connection state, address and lease | ✓ [2] | ✓ [2] | ✓ [2] | ◐ status, address, uptime, DNS; no lease-time field [2] | ✓ [2] |
| R3 | Set PPPoE credentials and service name | ✓ [3] | ✓ [3] | ✓ [3] | ◐ credentials only; PPPoEServiceName "Not supported, returns ''" [3] | ✓ [3] |
| R4 | Reset the PPPoE session | ✓ [4] | ✓ [4] | ✓ [4] | ✓ [4] | ◐ no reset command; disable then enable the pppoe-client interface [4] |
| R5 | Set the WAN VLAN id and priority | ✓ [5] | ◐ VLAN id via `8021q` `vid`; 802.1p priority mapping undocumented [5] | ✓ [5] | ✗ no WAN VLAN action; WANEthernetLinkConfig has only GetEthernetLinkStatus [5] | ◐ 802.1p only via mangle/bridge-filter set-priority, not a VLAN property [5] |
| R6 | Set the IPv6 WAN mode; read the delegated prefix | ✓ [6] | ✓ [6] | ✓ [6] | ◐ read only via UPnP IGD; no IPv6 WAN-mode Set action [6] | ✓ [6] |
| R7 | Read the provisioning mode (v4, v6, dual) | ✓ [7] | ◐ no mode field; derive from wan/wan6 interface status [7] | ✓ [7] | ◐ derivable from v4/v6 ConnectionStatus and DsliteStatus; no mode field [7] | ◐ no provisioning-mode object; derive from v4 and v6 client status [7] |
| R8 | Read WAN link state | ✓ [8] | ✓ [8] | ✓ [8] | ✓ [8] | ✓ [8] |
| R9 | Administratively disable / enable the WAN | ✓ [9] | ✓ [9] | ✓ [9] | ✗ no SetEnable on WANIP/PPPConnection; DSL default link cannot be disabled [9] | ✓ [9] |
| R10 | Renew / release the WAN DHCP lease | ✓ [10] | ◐ wiki shows `ifdown`/`ifup` only; `renew` method only in netifd source [10] | ✓ [10] | ◐ ForceTermination/RequestConnection re-establish the connection; no explicit lease renew [10] | ✓ [10] |
| | **LAN services** |  |  |  |  |  |
| R11 | Configure the DHCP server pool and lease time | ✓ [11] | ✓ [11] | ✓ [11] | ◐ pool via SetAddressRange; no lease-time action [11] | ✓ [11] |
| R12 | Configure DHCP options | ✓ [12] | ✓ [12] | ✓ [12] | ◐ only router and subnet options (SetIPRouter, SetSubnetMask); DNS/domain read-only [12] | ✓ [12] |
| R13 | Configure static leases | ✓ [13] | ✓ [13] | ✓ [13] | ✗ ReservedAddresses is out-only in GetInfo; no Set action [13] | ✓ [13] |
| R14 | Read active leases | ✓ [14] | ◐ dnsmasq leases are a file; ubus `dhcp ipv4leases` is odhcpd-only [14] | ✓ [14] | ✓ [14] | ✓ [14] |
| R15 | Configure DNS forwarder upstreams | ✓ [15] | ✓ [15] | ✓ [15] | ✗ X_SetDNSServers "The action is not supported"; LAN GetDNSServer read-only [15] | ✓ [15] |
| R16 | Configure local host overrides | ✓ [16] | ✓ [16] | ◐ shell only: Utopia dnsmasq `address=/` lines, no data-model parameter [16] | ◐ only X_AVM-DE_SetHostNameByMACAddress; no arbitrary name/record override [16] | ✓ [16] |
| R17 | Configure DNS rebind protection | ✓ [17] | ✓ [17] | ◐ always on: hard-coded dnsmasq `--stop-dns-rebind`, not configurable [17] | ✗ no rebind-protection action in any listed TR-064 service [17] | ✗ no rebind or private-address answer filter on the DNS page [17] |
| R18 | Configure bridge membership (ports, wireless networks) | ✓ [18] | ✓ [18] | ✓ [18] | ✗ no bridge/port-membership action; LAN services configure IP and DHCP only [18] | ✓ [18] |
| R19 | Read bridge and port membership | ✓ [19] | ◐ UCI `ports` gives config; live membership via `bridge` shell [19] | ✓ [19] | ◐ per-host port/guest flag only; no bridge object [19] | ✓ [19] |
| R20 | Configure a guest segment | ✓ [20] | ✓ [20] | ◐ no guest object; composed from LanManagementEntry table + a dedicated SSID [20] | ◐ Wi-Fi guest AP via its own WLANConfiguration instance; no LAN guest-port action [20] | ◐ no guest object; composed from bridge VLAN, address, DHCP and firewall [20] |
| R21 | Read LAN port status (link, speed, duplex) | ✓ [21] | ◐ `link` via network.device status; speed/duplex need ethtool/swconfig [21] | ✓ [21] | ◐ single LANEthernetInterfaceConfig instance; per-port only via host entries [21] | ✓ [21] |
| | **Wi-Fi access points** |  |  |  |  |  |
| R22 | Configure radio (band, channel, width, power, enable) | ✓ [22] | ✓ [22] | ◐ band fixed per radio: OperatingFrequencyBand is read-only [22] | ◐ SetEnable/SetChannel; no channel-width or TX-power action [22] | ✓ [22] |
| R23 | Read radio state | ✓ [23] | ✓ [23] | ✓ [23] | ✓ [23] | ◐ wifi package: monitor fields undocumented; state via running/inactive flags [23] |
| R24 | Configure a BSS (SSID, security mode, passphrase, hidden) | ✓ [24] | ✓ [24] | ✓ [24] | ✓ [24] | ✓ [24] |
| R25 | Read BSS state | ✓ [25] | ✓ [25] | ✓ [25] | ✓ [25] | ◐ wifi package: print flags/detail only; no BSS monitor field table [25] |
| R26 | Read connected stations (signal, rate) | ✓ [26] | ✓ [26] | ✓ [26] | ✓ [26] | ✓ [26] |
| R27 | Disconnect a station | ✓ [27] | ◐ `del_client` only in hostapd ubus source, no wiki page [27] | ✓ [27] | ✗ no deauthenticate/disconnect-station action in WLANConfiguration [27] | ✓ [27] |
| R28 | Start / cancel push-button or PIN onboarding; read its state | ✓ [28] | ◐ PBC via `wps_pushbutton`/hostapd_cli; `wps_start`/`wps_status` source-only [28] | ✓ [28] | ✓ [28] | ◐ wifi package: push-button start only; no cancel, state read or PIN [28] |
| R29 | Configure band steering and 11k/v/r | ✓ [29] | ✓ [29] | ◐ band steering and 11k/11v writable; no 802.11r parameter found [29] | ✗ no steering/11k/v/r action; mesh JSON exposes read-only flags [29] | ◐ wifi package: 11k/v/r properties; no explicit band-steering switch [29] |
| | **Security posture** |  |  |  |  |  |
| R30 | Read zone defaults and zone membership | ◐ TR-181 Firewall uses Level/Chain, no zone objects; UCI zones shell-only [30] | ✓ [30] | ◐ no zone model; firewall level presets only [30] | ✗ no zone/firewall object; only per-host WANAccess granted/denied [30] | ◐ no zone object; WAN/LAN interface lists and defconf filter rules [30] |
| R31 | Add / remove a port forward | ✓ [31] | ✓ [31] | ✓ [31] | ◐ AddPortMapping only for the calling host itself, not other LAN hosts [31] | ✓ [31] |
| R32 | Read the port-forward table | ✓ [32] | ✓ [32] | ✓ [32] | ✓ [32] | ✓ [32] |
| R33 | Add / remove an egress filter rule | ✓ [33] | ✓ [33] | ◐ LAN-host/port/protocol access policy; no destination-address match [33] | ✗ no L3/L4 rule action; only per-host WAN disallow and filter profiles [33] | ✓ [33] |
| R34 | Read filter rules | ✓ [34] | ✓ [34] | ✓ [34] | ◐ only filter profiles (time budgets/timetables), not address/port rules [34] | ✓ [34] |
| R35 | Block a host, on demand or on a schedule | ✓ [35] | ✓ [35] | ✓ [35] | ✓ [35] | ✓ [35] |
| R36 | Enable / disable automatic port mapping (UPnP IGD, PCP) | ✓ [36] | ✓ [36] | ◐ UPnP IGD only; PCP absent [36] | ◐ X_UPnP SetConfig Enable toggles UPnP generally; PCP not covered [36] | ◐ UPnP IGD only; no PCP or NAT-PMP [36] |
| R37 | Read automatic port mappings | ◐ PCP mappings readable; UPnP IGD lease table not in data model [37] | ◐ lease file only; no documented read command [37] | ◐ no TR-181 table; UPnP IGD service action only (shell/UPnP side) [37] | ◐ mappings listed; origin (UPnP vs manual) not flagged [37] | ✓ [37] |
| | **Host table** |  |  |  |  |  |
| R38 | Read the host table (address, name, attachment) | ✓ [38] | ◐ no unified host table; DHCP leases + `ip neigh`/LuCI hints [38] | ✓ [38] | ✓ [38] | ◐ no single host table; join DHCP leases, ARP and neighbor list [38] |
| | **Device operations** |  |  |  |  |  |
| R39 | Read identity (manufacturer, model, serial, OUI, software version) | ✓ [39] | ◐ `system board` lacks serial, manufacturer, OUI [39] | ✓ [39] | ✓ [39] | ✓ [39] |
| R40 | Read uptime, load, memory | ✓ [40] | ✓ [40] | ✓ [40] | ◐ UpTime only; no load or memory figures [40] | ✓ [40] |
| R41 | Read process state | ✓ [41] | ✓ [41] | ✓ [41] | ✗ no process-list action in any listed TR-064 service [41] | ◐ per-class CPU usage only; no process list or PIDs [41] |
| R42 | Read device logs | ✓ [42] | ✓ [42] | ✓ [42] | ✓ [42] | ✓ [42] |
| R43 | Configure log export | ✓ [43] | ✓ [43] | ✓ [43] | ✗ no syslog/export action; SendSupportData targets vendor support only [43] | ✓ [43] |
| R44 | Configure NTP servers; read sync state | ✓ [44] | ◐ servers via `system.ntp.server`; sync state needs ntp-utils `ntpq` [44] | ✓ [44] | ◐ SetNTPServers; no sync-state field, timezone fields "not supported" [44] | ✓ [44] |
| R45 | Upgrade firmware from an image | ✓ [45] | ✓ [45] | ✓ [45] | ✓ [45] | ✓ [45] |
| R46 | Factory reset | ✓ [46] | ✓ [46] | ✓ [46] | ✓ [46] | ✓ [46] |
| R47 | Reboot; read readiness | ◐ Reboot() exists; no boot-readiness parameter, infer from DeviceInfo.UpTime [47] | ◐ `reboot` documented; readiness inferred from `system info` uptime, no flag [47] | ✓ [47] | ◐ Reboot action; readiness only inferable via DeviceInfo GetInfo UpTime [47] | ◐ no readiness state; infer from reachability and resource uptime [47] |
| R48 | Export configuration | ✓ [48] | ✓ [48] | ◐ shell only (syscfg/PSM store); no data-model export parameter [48] | ✓ [48] | ✓ [48] |
| R49 | Import configuration | ✓ [49] | ✓ [49] | ◐ shell only (syscfg/PSM store); no data-model import parameter [49] | ✓ [49] | ✓ [49] |
| R50 | Set the local administrator credential | ✓ [50] | ✓ [50] | ✓ [50] | ✓ [50] | ✓ [50] |
| | **Remote management** |  |  |  |  |  |
| R51 | Configure ACS URL, credentials and periodic inform | ✓ [51] | ✓ [51] | ✓ [51] | ✓ [51] | ✓ [51] |
| R52 | Trigger an inform; read connection-request state | ◐ inform only through the substrate bus object; session state, no connection-request state [52] | ◐ `status` reports session state, not connection-request state [52] | ◐ ConnectionRequestURL readable; no inform-trigger parameter [52] | ◐ no inform-trigger action; only ConnectionRequestURL/Username readable [52] | ◐ no inform-trigger command; connection-request settings undocumented; status read-only [52] |
| R53 | Configure the USP controller endpoint and transport; read agent state | ◐ source-only: build profile and CI scripts; agent state not documented [53] | ✗ no USP agent (obuspa) in 24.10 packages/luci/routing/telephony feeds [53] | ◐ obuspa config via factory-reset file; Device.LocalAgent not on dmcli/rbus [53] | ◐ endpoint, MTP (websocket/mqtt), host, path, TLS writable; no agent connection state [53] | ✗ no USP/TR-369 agent; only the CWMP tr069-client exists [53] |
| | **Voice** |  |  |  |  |  |
| R54 | Configure a SIP account; read registration state | ◐ tr104-voip repo is a 3-line stub; no VoiceService parameters published [54] | ◐ Asterisk PBX config files + CLI; no UCI/ubus voice model [54] | ◐ telco-voice-manager is an optional component, not in the reference-build list; MTA model is DOCSIS-eMTA only [54] | ✓ [54] | ✗ no SIP user agent; SIP appears only as a NAT helper [54] |
| R55 | Read FXS line state | ◐ VoiceService:2 stub only; FXS line objects unpublished [55] | ◐ asterisk-chan-lantiq Lantiq SoC FXS only; state via Asterisk CLI [55] | ◐ same component caveat: voice manager optional; X_CISCO_COM_MTA.LineTable only on DOCSIS eMTA builds [55] | ◐ X_AVM-DE_GetPhonePort returns port name only; no hook/line state [55] | ✗ no FXS or telephony port in the feature list [55] |
| | **Mesh controller** |  |  |  |  |  |
| R56 | Read mesh topology (agents, backhaul links) | ✓ [56] | ✗ no EasyMesh controller; 802.11s is a peer mesh [56] | ◐ controller source only; BPI R4 porting marked ongoing/TBD, no RDK doc of the paths [56] | ✓ [56] | ◐ CAPsMAN, not EasyMesh; CAP list without backhaul links [56] |
| R57 | Read backhaul link health | ◐ Backhaul object gives link type/MACs; signal/rate only via parent BSS STA entry [57] | ✗ 802.11s peer links via `iw station dump`, not EasyMesh backhaul [57] | ◐ controller source only; BPI R4 porting marked ongoing/TBD [57] | ◐ link metrics present; no explicit backhaul flag (is_upstream is LAN-only) [57] | ✗ no backhaul-link metrics; remote-cap shows connected-time only [57] |
| R58 | Steer a client to another agent | ✓ [58] | ◐ usteer roams clients between plain APs; no EasyMesh agents [58] | ◐ controller rbus method in source only; BPI R4 porting marked ongoing/TBD [58] | ✗ no steering action; schema steering_enabled is a read-only flag [58] | ◐ no EasyMesh steer; 802.11v BSS-transition suggestion via steering only [58] |

## 3. Decision

Add a vendor-neutral **`CpeGatewayDevice`** archetype (registered
`cpe_gateway`), **superseding** `CpeDevice` (`linux_cpe`). The new class
composes what a CPE gateway publishes on its management planes (§1): the WAN
connection as a managed object, the LAN services, the Wi-Fi access points, the
security posture, the host table, device operations and remote management by
an auto-configuration server. `CpeDevice` stays registered under `linux_cpe`,
intact and deprecated, for one MINOR release and six months (§6, D6): its one
consumer keeps passing the `isinstance` gate unchanged while it moves, and
the old shape is removed, not evolved, when the period ends.

The **core** is every operation of §2 that both trigger columns and a
majority of the five columns support, a caveated cell (◐) counting as
support with its limit becoming the member's documented per-column behaviour
or a per-method unsupported case (D9): 55 of the 58 operations. It composes
existing capabilities wherever their shape holds (§5), and introduces nine
capabilities no protocol on `main` owns, each argued on the placement ladder
in §5 and §6: `WanConnection`, `DnsForwarder`, `L2Bridge` (the `GAPS.md`
entry of 2026-05-02 whose trigger is this class), `HostTable`, `HostFilter`,
`AutoPortMapping`, `AdminCredential`, `DeviceHealth` (a read-only base split
off the host-shaped `DeviceManagement`, which inherits it) and, on the tiers,
`VoiceGateway` and `UspAgent`. Four existing protocols are extended (rung 5):
`DeviceInfo` with the identity facts, `DeviceLifecycle` with image staging and
configuration transfer, `Tr069Client` with the ACS configuration,
`NtpConfig` with the synchronisation state and `WifiOnboarding` with the
cancel and state read. The identity, health, lifecycle and configuration
members are worded for any closed network product, not for this class
alone, so the chartered router sibling can compose them when its design
lands (D8).

Three **optional tiers** are built in this pass. Voice and the mesh
controller are facets the charter places "on many models", not on the class:
a bridged modem or an operator gateway without telephony publishes neither,
so both are tiers whatever the count says, and the count (four of five
columns support voice, three support each mesh operation) meets the amended
evidence bar, so both are implemented and tested like the core (D7). USP is
a tier because one trigger column publishes no agent (R53, column 2) while
three columns do. Each tier is a Protocol a driver satisfies in addition to
the core; §9 names the columns expected to implement each tier member and
the ones expected to raise. The cells that support a tier only nominally (a
stub plugin, a PBX from a package feed, controller source whose porting is
marked ongoing) are the design's stated risk, listed by id in §9: if stage 4
finds one of them unsupported in substance, the member becomes a per-column
unsupported case or the tier drops to `tier-staged`, and its manifest rows
are re-outcomed without reopening the design.

The superseded shape drops what no closed gateway publishes: the hardware
console and the four host-substrate levers (`hw_console`, `ip_interface`,
`ip_routing`, `conntrack`, host `nat`), which stay on the Linux twin, and the
host-shaped `device_management` and `ntp_client`, whose device-side concerns
move to `DeviceHealth` and `NtpConfig`. It also drops two members for which
§2 carries no row (`wifi_rf`, `network_probe`); a dated matrix row brings
either back as a `feat:` change. The test-bed role objects (`wan_endpoint`,
`lan_endpoint`) stay (§4).

## 4. The archetype

The mandatory **core** is the universal surface of §1: satisfiable by an
operator gateway reached through a data-model CLI, a retail router reached
through a SOAP API on the LAN side, and a low-end router reached through a
proprietary CLI, with no Wi-Fi assumption beyond the radios the matrix shows
every column publishes and no voice or mesh member. Where a column supports
an operation only in part (◐ in §2), the member keeps its neutral shape and
the driver raises the documented unsupported case for the part the column
lacks, or maps with a stated loss (§8); the three facets that fail the core
threshold or the class definition are independent optional tier Protocols,
so a driver satisfies any combination of them.

```python
@runtime_checkable
class CpeGatewayDevice(BaseDeviceProtocol, Protocol):
    """CPE gateway — universal core. Vendor-neutral; satisfiable by any
    gateway whose driver publishes the members below. The reviewed
    families and their evidence are in
    docs/architecture/cpe-gateway-protocol-design.md (§2, §10); the
    management transport and who manages the device are driver concerns."""

    wan_connection: WanConnection        # NEW — the WAN connection as a managed object: mode, credentials, tag, IPv6, state (§6)
    wan_link_admin: WanLinkAdmin         # reuse as-is — administrative down/up of the WAN by label; module docstring generalised (§6)
    dhcp_client: DhcpClient              # reuse — release and renew of the WAN lease, v4 and v6
    port_status: PortStatus              # reuse — link, speed, duplex of the WAN and LAN ports
    interface_dhcp: InterfaceDhcp        # reuse as-is — pools, lease time, options, reservations, active leases (§6)
    dns_forwarder: DnsForwarder          # NEW — upstreams, local host overrides, rebind protection (§6)
    l2_bridge: L2Bridge                  # NEW (GAPS 2026-05-02) — bridge membership of ports and wireless networks (§6)
    wifi_radio: WifiRadio                # reuse — radios addressed by band; no band setter (§6)
    wifi_bss: WifiBss                    # reuse — networks, security, visibility
    wifi_stations: WifiStations          # reuse — attached stations, disconnect
    wifi_onboarding: WifiOnboarding      # EXTENDED — push-button and PIN as today; cancel and state read added (§6)
    wifi_transitions: WifiTransitions    # reuse — 11k/v/r; band steering by composition (§6)
    firewall_zones: FirewallZones        # reuse — zone defaults and membership; per-method unsupported on four columns (§6)
    firewall: Firewall                   # reuse — port forwards and the DMZ host, plus the rule members it inherits (egress filters) (§6)
    host_filter: HostFilter              # NEW — per-host block, on demand or on a weekly schedule (§6)
    auto_port_mapping: AutoPortMapping   # NEW — automatic port mapping enable per protocol; the mapping table (§6)
    hosts: HostTable                     # NEW — the hosts behind the gateway: address, name, attachment (§6)
    info: DeviceInfo                     # EXTENDED — model as today; manufacturer, serial number, OUI, hardware and software version added (§6)
    health: DeviceHealth                 # NEW (split off DeviceManagement) — uptime, online state, load figure, memory, processes, log entries (§6)
    syslog: SyslogConfig                 # reuse — log export
    ntp: NtpConfig                       # EXTENDED — servers as today; synchronisation state added (§6)
    device_lifecycle: DeviceLifecycle    # EXTENDED — boot wait, factory reset, reboot as today; image staging and activation, configuration export and import added; one member renamed (§6)
    admin_credential: AdminCredential    # NEW — the local administrator credential (§6)
    tr069_client: Tr069Client            # EXTENDED — connection state, identifier and inform as today, the inform's meaning stated; ACS configuration added (§6)
    wan_endpoint: NetworkEndpoint        # reuse — test-bed role object: the gateway's WAN-side address
    lan_endpoint: NetworkEndpoint        # reuse — test-bed role object: the gateway's LAN-side address

register_device_type("cpe_gateway", CpeGatewayDevice)
```

**Nine new capabilities at seed, each argued in §5 and §6:** seven on the
core (`WanConnection`, `DnsForwarder`, `L2Bridge`, `HostTable`, `HostFilter`,
`AutoPortMapping`, `AdminCredential`), one split (`DeviceHealth`) and two on
tiers (`VoiceGateway`, `UspAgent`). Every other member exists today; each
change to an existing one is placed on the ladder in §5 and listed in §12.
Where a disposition has a fallback, §6 states the condition that would move
to it.

Optional tier Protocols, each a strict `(CpeGatewayDevice, Protocol)`
superset adding one facet, built in this pass on the matrix evidence (D7):

```python
@runtime_checkable
class CpeGatewayVoiceTier(CpeGatewayDevice, Protocol):
    """Adds the voice facet: SIP accounts and their registration, FXS lines
    and their state. Present on operator gateways and on retail gateways
    with telephony; absent on bridged modems and on the fifth reviewed
    column. Evidence: four of five columns (R54–R55, one at ✓, three
    caveated; §9 names the nominal cells)."""
    voice: VoiceGateway                  # NEW (tier) — SIP accounts, registration state, FXS line state (§6)

@runtime_checkable
class CpeGatewayMeshTier(CpeGatewayDevice, Protocol):
    """Adds the mesh-controller facet: the agents and their backhaul links,
    client steering between agents. The extender is not a device of this
    archetype; it is an agent in the controller's topology (§1). Evidence:
    three of five columns per operation (R56–R58); the second trigger
    column publishes no controller and raises."""
    wifi_mesh: WifiMesh                  # reuse (+ one defaulted field on the topology node) — topology, backhaul, steering (§6)

@runtime_checkable
class CpeGatewayUspTier(CpeGatewayDevice, Protocol):
    """Adds the USP agent: the controller endpoint and its transport, the
    agent's state. Evidence: three of five columns (R53, all caveated); the
    second trigger column packages no agent and raises."""
    usp_agent: UspAgent                  # NEW (tier) — controller endpoint and transport, agent state (§6)
```

The tiers are registered with the archetype (`cpe_gateway_voice`,
`cpe_gateway_mesh`, `cpe_gateway_usp`) because their reference drivers exist
at stage 4; a driver that satisfies two facets registers plugin-local under
the combined shape until a second consumer lifts it (the composition rule
the sibling designs follow).

**Concerns, dispositions and evidence.** One row per concern of §1; the
X-vendor column gives the count of the concern's weakest matrix row as
`✓ + ◐ + ✗` over the five columns, the ◐ cells counting as support (D9);
Notes cite the rows. Core membership needs both trigger columns (1 and 2)
supporting and at least three of five.

| Concern | Capability | Disposition | X-vendor (of 5) | Notes |
| --- | --- | --- | :--: | --- |
| WAN connection: mode, credentials, tag, IPv6, provisioning mode, state | `WanConnection` | **new** | 2 + 2 ◐ + 1 ✗ | R1–R7; weakest R5 (the tag's priority, column 4 publishes no tag action); R7 derived on three columns |
| WAN link state | `PortStatus` | reuse | 5 | R8 |
| WAN administrative down/up | `WanLinkAdmin` | reuse, docstring generalised | 4 + 1 ✗ | R9; column 4 raises |
| WAN lease release and renew | `DhcpClient` | reuse | 3 + 2 ◐ | R10 |
| DHCP server: pool, lease time, options, reservations, leases | `InterfaceDhcp` | reuse as-is | 4 + 1 ✗ | R11–R14; weakest R13 (column 4 has no reservation write); `InterfaceDhcpConfig` already carries options and reservations |
| DNS forwarder: upstreams, overrides, rebind protection | `DnsForwarder` | **new** | 2 + 1 ◐ + 2 ✗ | R15–R17; weakest R17 (rebind protection, two columns raise, one is always on) |
| Bridge membership | `L2Bridge` | **new** (GAPS 2026-05-02) | 4 + 1 ✗ | R18–R19; column 4 publishes no bridge object |
| Guest segment | `L2Bridge` + `FirewallZones` + `InterfaceDhcp` + `WifiBss` | composition | 2 + 3 ◐ | R20; no named member (§6) |
| LAN port status | `PortStatus` | reuse | 3 + 2 ◐ | R21 |
| Radios | `WifiRadio` | reuse | 3 + 2 ◐ | R22–R23; the band is the radio's address, not a setting (§6) |
| Networks (BSS) | `WifiBss` | reuse | 4 + 1 ◐ | R24–R25 |
| Stations, disconnect | `WifiStations` | reuse | 3 + 1 ◐ + 1 ✗ | R26–R27; column 4 cannot disconnect |
| Onboarding: start, cancel, state | `WifiOnboarding` | **extend** | 3 + 2 ◐ | R28; cancel and state read added |
| Band steering, 11k/v/r | `WifiTransitions` | reuse | 2 + 2 ◐ + 1 ✗ | R29; band steering by composition of the 11v members (§6) |
| Zone defaults and membership | `FirewallZones` | reuse | 1 + 3 ◐ + 1 ✗ | R30; four columns have no zone object: mapped or per-method unsupported (§6) |
| Port forwards, DMZ host | `Firewall` | reuse | 4 + 1 ◐ | R31–R32; column 4 forwards to the calling host only |
| Egress filter rules | `Firewall` (the inherited rule members) | reuse | 3 + 1 ◐ + 1 ✗ | R33–R34; column 4 publishes profiles, not rules |
| Host block with schedule | `HostFilter` | **new** | 5 | R35 |
| Automatic port mapping | `AutoPortMapping` | **new** | 1 + 4 ◐ | R36–R37; PCP absent on three columns, per-protocol unsupported |
| Host table | `HostTable` | **new** | 3 + 2 ◐ | R38; two columns join leases, neighbours and station lists |
| Identity | `DeviceInfo` | **extend** | 4 + 1 ◐ | R39; manufacturer, serial number, OUI, hardware and software version added (D8) |
| Health: uptime, load, memory, processes, logs | `DeviceHealth` | **new (split)** | 3 + 1 ◐ + 1 ✗ | R40–R42; weakest R41 (column 4 has no process list); the base `DeviceManagement` inherits (D8, §6) |
| Log export | `SyslogConfig` | reuse | 4 + 1 ✗ | R43; column 4 raises (D8) |
| Time: servers, synchronisation state | `NtpConfig` | **extend** | 3 + 2 ◐ | R44; sync-state read added |
| Firmware upgrade | `DeviceLifecycle` | **extend** | 5 | R45; image staging and activation added (D8) |
| Factory reset; reboot and readiness | `DeviceLifecycle` | reuse | 1 + 4 ◐ | R46–R47; readiness is the boot wait on uptime or reachability on four columns |
| Configuration export and import | `DeviceLifecycle` | **extend** | 4 + 1 ◐ | R48–R49 (D8); column 3 through the shell store |
| Local administrator credential | `AdminCredential` | **new** | 5 | R50 |
| ACS configuration, inform, connection-request state | `Tr069Client` | **extend** | 0 + 5 ◐ | R51 (5 ✓) and R52 (5 ◐): ACS configuration added; the inform's meaning stated, the connection-request state read nowhere (§6) |
| USP controller endpoint, transport, agent state | `UspAgent` | **new (tier)** | 0 + 3 ◐ + 2 ✗ | R53; column 2 packages no agent: tier `usp` |
| Voice: SIP accounts, registration, FXS lines | `VoiceGateway` | **new (tier)** | 0 + 4 ◐ + 1 ✗ | R54–R55; the class definition makes it a tier; column 5 raises |
| Mesh controller: topology, backhaul health, steering | `WifiMesh` | reuse (tier) | 0 + 3 ◐ + 2 ✗ | R56–R58; weakest R57; column 2 publishes no controller: tier `mesh`; one defaulted field for backhaul health per agent (§6) |

**Test-bed role objects.** `wan_endpoint` and `lan_endpoint` are not
operations the gateway publishes; they are how a scenario binds the two
sides of the device under test (which address a LAN client reaches it on,
which address the WAN server sees), the same role the superseded shape gave
them. They stay on the core as `NetworkEndpoint` members; no matrix row
applies, and no driver "supports" or "lacks" them.

**Dropped members.** Against `CpeDevice`, the new class drops `hw_console`
(a hardware console is a test-bed attachment, not a published operation),
`ip_interface`, `ip_routing`, `conntrack` and host `nat` (host-substrate
levers of the Linux twin; the gateway's NAT concern is the port-forward table
on `firewall`), `device_management` (replaced by the read-only `health`
split; the host-shaped file and board-log members stay on the hosts),
`ntp_client` (a host's clock lever; the gateway publishes its server list and
synchronisation state on `ntp`), `wifi_rf` and `network_probe` (no matrix
row; §3). A consumer that needs one of the dropped members on a gateway
composes it plugin-local, or brings the matrix row.

## 5. Reuse vs. net-new

### Reuse survey (exploration)

A first reading of the capabilities on `main` for every matrix row; the
placement-ladder argument per operation is stage 3. "D8" marks the
operations the spec has this pass introduce as generic capabilities.

| Id | Operation | Candidate on main | Fit | Note |
| --- | --- | --- | --- | --- |
| R1 | Set the WAN connection mode (DHCP, static, PPPoE, IPoE) | new (WAN connection object) | new | no capability carries a WAN connection with a mode; `wan_link_admin` (twin) has only bring_wan_down/up |
| R2 | Read WAN connection state, address and lease | new (WAN connection object) | new | state, address and lease belong to the same object as R1 |
| R3 | Set PPPoE credentials and service name | new (WAN connection object) | new | PPPoE credentials and service name are fields of the connection |
| R4 | Reset the PPPoE session | new (WAN connection object) | new | session reset is a lever on the connection |
| R5 | Set the WAN VLAN id and priority | new (WAN connection object) | new | tag and priority are fields of the connection; `vlan_client` is a host lever |
| R6 | Set the IPv6 WAN mode; read the delegated prefix | new (WAN connection object) | new | IPv6 mode and delegated prefix on the connection; `held_prefixes` is the provisioner's view |
| R7 | Read the provisioning mode (v4, v6, dual) | new (WAN connection object) | new | provisioning mode is a read on the connection |
| R8 | Read WAN link state | `port_status` (PortStatus) | as-is | link state of the WAN port; the WAN connection object carries the upper-layer state |
| R9 | Administratively disable / enable the WAN | `wan_link_admin` (WanLinkAdmin) | as-is or extend | bring_wan_down/up match; written for the twin, check its docstring for host assumptions |
| R10 | Renew / release the WAN DHCP lease | `dhcp_client` (DhcpClient) | as-is | release_dhcp/renew_dhcp and the IPv6 pair |
| R11 | Configure the DHCP server pool and lease time | `interface_dhcp` (InterfaceDhcp) or `dhcp_server` (provisioner) | extend | set_interface_dhcp is per interface with pool and lease time; the provisioner's `provision_cpe` is test-bed shaped |
| R12 | Configure DHCP options | `interface_dhcp` | extend | options need a field or a member; `DhcpOption` lives in `models/sdwan_appliance.py` |
| R13 | Configure static leases | `interface_dhcp` | extend | static leases are a new member |
| R14 | Read active leases | `interface_dhcp` | as-is | get_dhcp_leases |
| R15 | Configure DNS forwarder upstreams | new (DNS forwarder) | new | `dns_client` is a resolver on a host; no forwarder configuration exists |
| R16 | Configure local host overrides | new (DNS forwarder) | new | local overrides are forwarder entries |
| R17 | Configure DNS rebind protection | new (DNS forwarder) | new | rebind protection is a forwarder setting |
| R18 | Configure bridge membership (ports, wireless networks) | new `L2Bridge` (GAPS 2026-05-02) | new | imports `models/l2_common.py`; `switch_ports`/`switch_vlans` are the switchport shape, rejected for this class |
| R19 | Read bridge and port membership | new `L2Bridge` | new | membership read on the same capability |
| R20 | Configure a guest segment | `L2Bridge` + `firewall_zones` + `interface_dhcp` | reuse (composition) | a guest segment is a bridge, a zone and a pool; the design decides whether a named operation is needed |
| R21 | Read LAN port status (link, speed, duplex) | `port_status` | as-is | link, speed, duplex |
| R22 | Configure radio (band, channel, width, power, enable) | `wifi_radio` | as-is or extend | existing member; no band setter today |
| R23 | Read radio state | `wifi_radio` | as-is |  |
| R24 | Configure a BSS (SSID, security mode, passphrase, hidden) | `wifi_bss` | as-is |  |
| R25 | Read BSS state | `wifi_bss` | as-is |  |
| R26 | Read connected stations (signal, rate) | `wifi_stations` | as-is |  |
| R27 | Disconnect a station | `wifi_stations` or `wifi_transitions.send_deauth` | as-is | check which carries the kick today |
| R28 | Start / cancel push-button or PIN onboarding; read its state | `wifi_onboarding` | as-is | trigger_wps_pbc/pin, get_wps_enabled; cancel and state read may need `extend` |
| R29 | Configure band steering and 11k/v/r | `wifi_transitions` | as-is | set_rrm_enabled/set_btm_enabled/set_ft_enabled; band steering may need a field |
| R30 | Read zone defaults and zone membership | `firewall_zones` | as-is | list_zones/get_zone/set_zone_defaults; four columns have no zone object (◐) |
| R31 | Add / remove a port forward | `firewall` (port mappings) or `appliance_nat` | as-is | `firewall.add_port_mapping` is the gateway-tier shape; `appliance_nat.set_port_forwarding_rules` is list-replacing; the design picks one |
| R32 | Read the port-forward table | `firewall.list_port_mappings` | as-is |  |
| R33 | Add / remove an egress filter rule | `packet_filter` rules | as-is or extend | egress rule by host and destination; `firewall` carries port mappings and DMZ only, the rule members are `packet_filter`'s |
| R34 | Read filter rules | `packet_filter` | as-is |  |
| R35 | Block a host, on demand or on a schedule | new (host filter) | new | per-host block and schedule; `content_filtering` is URL-based, `firewall` rules are address-based without schedule |
| R36 | Enable / disable automatic port mapping (UPnP IGD, PCP) | new (automatic port mapping control) | new | `upnp_client` is the LAN client's lever, not the gateway's enable |
| R37 | Read automatic port mappings | new (automatic port mapping control) | new | mapping table read |
| R38 | Read the host table (address, name, attachment) | new (host table) | new | no archetype reads a host table; `arp_client` is a host lever |
| R39 | Read identity (manufacturer, model, serial, OUI, software version) | `device_info` (DeviceInfo) | extend | only `model` today; manufacturer, serial, OUI, software version are new fields (D8: introduce here) |
| R40 | Read uptime, load, memory | `device_management` | as-is | get_seconds_uptime, get_load_avg, read_memory_utilization (D8: health split decided by the design) |
| R41 | Read process state | `device_management.read_running_processes` | as-is |  |
| R42 | Read device logs | `device_management.read_log_entries` | as-is |  |
| R43 | Configure log export | `syslog_config` | as-is | set_syslog_servers/get_syslog_servers (D8) |
| R44 | Configure NTP servers; read sync state | `ntp_config` + `ntp_client` | extend | set/get_ntp_servers exist; neither carries a sync-state read |
| R45 | Upgrade firmware from an image | `device_lifecycle` | extend | no image stage/activate member today (D8: introduce here) |
| R46 | Factory reset | `device_lifecycle.factory_reset` | as-is |  |
| R47 | Reboot; read readiness | `device_lifecycle.reset` + `wait_for_boot` | as-is | readiness = wait_for_boot; `verify_cpe_is_booting` carries a class name in a method (rename candidate) |
| R48 | Export configuration | new or `device_lifecycle` extend (configuration transfer) | extend | D8: introduce here; export |
| R49 | Import configuration | same as R48 | extend | import |
| R50 | Set the local administrator credential | new (management access / admin credential) | new | no admin-credential capability on `main`; `radius_client` is a server-side AAA client, a single credential set is a smaller shape |
| R51 | Configure ACS URL, credentials and periodic inform | `tr069_client` | extend | is_tr069_connected/get_id/force_inform exist; ACS URL, credentials and periodic inform are new members |
| R52 | Trigger an inform; read connection-request state | `tr069_client.force_inform` + `is_tr069_connected` | as-is | connection-request state read may need `extend` |
| R53 | Configure the USP controller endpoint and transport; read agent state | new (USP agent) | new | no USP capability exists |
| R54 | Configure a SIP account; read registration state | new (voice: SIP account) | new | `sip_phone` is the test-bed phone, not the gateway's account |
| R55 | Read FXS line state | new (voice: FXS line) | new |  |
| R56 | Read mesh topology (agents, backhaul links) | `wifi_mesh.get_topology` | as-is | `wifi_mesh` exists on main (controller side: topology, agents, steering) |
| R57 | Read backhaul link health | `wifi_mesh.get_mesh_status` / `get_topology` | as-is or extend | backhaul health fields to check |
| R58 | Steer a client to another agent | `wifi_mesh.steer_client` | as-is |  |

## 9. Verification

### Verification items (exploration)

Every ◐ and ✗ cell of §2 as it stands, by column and row id (the cell text
and its source stand in §2 and §10); stage 4 settles each as an explicit
`NotSupportedError` with a source or as a sourced mapping. 105 items.

- **Column 1 (trigger family 1)** (8): ◐ R30, R37, R47, R52, R53, R54, R55, R57; ✗ none
- **Column 2 (trigger family 2)** (20): ◐ R5, R7, R10, R14, R19, R21, R27, R28, R37, R38, R39, R44, R47, R52, R54, R55, R58; ✗ R53, R56, R57
- **Column 3** (18): ◐ R16, R17, R20, R22, R29, R30, R33, R36, R37, R48, R49, R52, R53, R54, R55, R56, R57, R58; ✗ none
- **Column 4** (37): ◐ R1, R2, R3, R6, R7, R10, R11, R12, R16, R19, R20, R21, R22, R31, R34, R36, R37, R40, R44, R47, R52, R53, R55, R57; ✗ R5, R9, R13, R15, R17, R18, R27, R29, R30, R33, R41, R43, R58
- **Column 5** (22): ◐ R1, R4, R5, R7, R20, R23, R25, R28, R29, R30, R36, R38, R41, R47, R52, R56, R58; ✗ R17, R53, R54, R55, R57

## 10. Sources

The charter (§1) carries the sources for the version lines. The matrix
sources follow, one numbered list per family; a cell's `[n]` resolves to
entry `n` of its column's list. Each entry: title — URL — section or anchor —
what it establishes. The vendor-isolation rule forbids vendor names and URLs
in the package source, not in this design record.

### prplOS 4.0 line

1. wan-manager (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/wan-manager> — odl/wan-manager_WAN_Intf_definition.odl `IPv4Mode` / `IPv6Mode`; README "OperationMode", `setWANMode()` — DM: `WANManager.WAN.{i}.Intf.{i}.IPv4Mode` enum dhcp4/ppp4/static/dslite/none, `IPv6Mode` dhcp6/ppp6/static/none are persistent (writable); `WANManager.setWANMode()` / `WANMode` switch the mode and reconfigure DHCP/PPP/IP plugins
2. tr181-dhcpv4client ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-dhcpv4client/-/tree/main/odl> — dhcpv4c_definition.odl `Status`, `DHCPStatus`, `IPAddress`, `SubnetMask`, `IPRouters`, `DNSServers`, `LeaseTimeRemaining` — DM: `DHCPv4.Client.{i}` exposes read-only Status, DHCPStatus (Init…Bound/Renewing), IPAddress, SubnetMask, IPRouters, DNSServers, LeaseTimeRemaining, DHCPServer; readable with `ba-cli DHCPv4.Client.1.?`
3. tr181-ppp ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-ppp/-/tree/main/odl> — tr181-ppp-interface.odl `Username`, `Password`; tr181-ppp-interface-pppoe.odl `ServiceName`, `ACName` — DM: `PPP.Interface.{i}.Username`/`Password` and `PPP.Interface.{i}.PPPoE.ServiceName`/`ACName` are %persistent (writable); wan-manager `WAN.{i}.Intf.{i}.UserName/Password` override them
4. tr181-ppp ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-ppp/-/tree/main/odl> — tr181-ppp-interface.odl `uint32 Reset();` — DM: `PPP.Interface.{i}.Reset()` tears down the current PPP session and re-establishes it (no-op on a disabled interface)
5. wan-manager (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/wan-manager> — odl/wan-manager_WAN_Intf_definition.odl `Type="vlan"`, `VlanID`, `VlanPriority`; README "Ethernet: new vlan termination" — DM: `WANManager.WAN.{i}.Intf.{i}.Type=vlan`, `VlanID` (0–4096), `VlanPriority` (-1..7) are writable and wan-manager creates the matching `Ethernet.VLANTermination.{i}` (`VLANID`, `VLANPriority`, `TPID` writable in tr181-ethernet)
6. tr181-ip ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-ip/-/tree/main/odl> — ip-manager-ipv6prefix.odl `Prefix`, `Origin`="PrefixDelegation", `PrefixStatus`; ip-manager-interface.odl `IPv6Enable` — DM: IPv6 WAN mode is set with wan-manager `IPv6Mode` (dhcp6/ppp6/static) plus `DHCPv6.Client.{i}.RequestPrefixes`; the delegated prefix is read from `IP.Interface.{i}.IPv6Prefix.{i}.Prefix` with read-only `Origin=PrefixDelegation` and `PrefixStatus`
7. wan-manager (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/wan-manager> — odl/wan-manager_WAN_Intf_definition.odl `IPv4Mode`/`IPv6Mode`; README `getWANMode()` — DM: `WANManager.getWANMode()` and the `Intf.{i}.IPv4Mode`/`IPv6Mode` values ("none" on one side = single-stack) read the provisioning mode; `IP.Interface.{i}.IPv4Enable`/`IPv6Enable` confirm it
8. tr181-ethernet ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-ethernet/-/tree/main/odl> — ethernet-manager_interface.odl `%read-only string Status` — DM: `Ethernet.Interface.{i}.Status` (Up/Down/NotPresent…) is read-only; `WANManager.WAN.{i}.Status` and `PPP.Interface.{i}.ConnectionStatus` give the upper layers; substrate `ip link show` observed (prplOS 4.0.3, impls/linux_net.py)
9. tr181-ip ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-ip/-/tree/main/odl> — ip-manager-interface.odl `%persistent bool Enable` — DM: `IP.Interface.{i}.Enable` (and `Ethernet.Interface.{i}.Enable`) is writable; wan-manager also offers `WANManager.WANModeDisable()/WANModeEnable()`
10. tr181-dhcpv4client ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-dhcpv4client/-/tree/main/odl> — dhcpv4c_definition.odl `void Renew();`, `"${global_vendor_prefix_}Release"()` — DM: `DHCPv4.Client.{i}.Renew()` and vendor-prefixed `X_PRPL-COM_Release()` methods (DHCPv6 client likewise has `Renew()`/`Release`)
11. prplOS wiki: TR-181 components configuration — <https://gitlab.com/prpl-foundation/prplos/prplos/-/wikis/TR-181-components-configuration> — "Disabling the DHCP server on the LAN network" `ubus call DHCPv4.Server.Pool _del` — DM via ubus: pools are `DHCPv4.Server.Pool.{i}` instances (wiki shows `_del` by Alias); tr181-dhcpv4 odl/server/dhcpv4-manager-server-pool.odl has writable `MinAddress`, `MaxAddress`, `LeaseTime`, `Interface`
12. tr181-dhcpv4 (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-dhcpv4> — README "Force option" `Device.DHCPv4.Server.Pool.{i}.Option.{i}.Force`; odl `Option[]` `Tag`, `Value` — DM: `DHCPv4.Server.Pool.{i}.Option.{i}.Tag`/`Value`/`Enable` are persistent (writable), plus prpl `Force`
13. tr181-dhcpv4 (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-dhcpv4> — README events on `DHCPv4.Server.Pool.*.StaticAddress` (`Yiaddr`, `Chaddr`, `Enable`); odl `StaticAddress[]` — DM: `DHCPv4.Server.Pool.{i}.StaticAddress.{i}.Chaddr`/`Yiaddr` writable; adds/changes are pushed to UCI/dnsmasq
14. tr181-dhcpv4 (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-dhcpv4> — README "Calls ubus dnsmasq leases … Pool.instance.Client.Client-<MAC>.IPv4Address"; odl `Client[]` — DM: read-only `DHCPv4.Server.Pool.{i}.Client.{i}.Chaddr`, `.IPv4Address.{i}.IPAddress`, `LeaseTimeRemaining`, `Active`, populated from dnsmasq lease events
15. tr181-dns ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-dns/-/tree/main/odl> — tr181-dns_relay.odl `Forwarding[]` `DNSServer`, `Interface`, `Enable`; `Config[]` `Forwarders` — DM: `DNS.Relay.Forwarding.{i}.DNSServer`/`Interface`/`Enable` writable (Type=Static); `DNS.Relay.Config.{i}.Forwarders` orders upstreams (README feature note)
16. tr181-dns ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-dns/-/tree/main/odl> — tr181-dns_host.odl `'${global_vendor_prefix_}Host'[]` `Name`, `Interface`, `IPAddress[].IPAddress` — DM (vendor extension): `DNS.X_PRPL-COM_Host.{i}.Name` + `.IPAddress.{i}.IPAddress` writable, serves local hostname overrides from unbound
17. tr181-dns ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-dns/-/tree/main/odl> — tr181-dns_rebindprotection.odl `RebindProtection` `Enable`, `IPExceptions[]`, `DomainExceptions[]` — DM (vendor extension): `DNS.X_PRPL-COM_RebindProtection.Enable` (default true) with IP/domain exception tables, writable
18. tr181-bridging ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-bridging/-/tree/main/odl> — tr181-bridging_port.odl `%persistent csv_string LowerLayers`, `Enable`; tr181-bridging_defaults/00_bridging_defaults.odl `LowerLayers = "Device.WiFi.SSID.4"` — DM: `Bridging.Bridge.{i}.Port.{i}.LowerLayers` writable (Ethernet.Interface or WiFi.SSID references), `Port.{i}.Enable`; defaults show wireless SSIDs as bridge ports
19. tr181-bridging ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-bridging/-/tree/main/odl> — tr181-bridging_definition.odl `Bridge[]` `Status`; tr181-bridging_port.odl `Status`, `Name`, `ManagementPort`, `PortNumberOfEntries` — DM: `Bridging.Bridge.{i}.Status`, `Port.{i}.Status/Name/ManagementPort/LowerLayers` readable (`ba-cli Bridging.?`)
20. prplOS wiki: TR-181 components configuration — <https://gitlab.com/prpl-foundation/prplos/prplos/-/wikis/TR-181-components-configuration> — "Remove the guest network" `ubus call Bridging.Bridge _del '{"rel_path": ".[Alias == \"guest\"]."}'`; `DHCPv4.Server.Pool` Alias guest — DM via ubus: a guest segment is a `Bridging.Bridge` instance (default `guest` = br-guest + guest_wl0/wl1 in tr181-bridging defaults) with its own `DHCPv4.Server.Pool` and firewall defaults (tr181-firewall odl/defaults.gw.d/30_guest_defaults.odl.uc); the wiki shows the TR-181 write (delete) for it
21. tr181-ethernet ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-ethernet/-/tree/main/odl> — ethernet-manager_interface.odl `Status`, `CurrentBitRate`, `CurrentDuplexMode` — DM: read-only `Ethernet.Interface.{i}.Status`, `CurrentBitRate`, `CurrentDuplexMode` (plus writable `MaxBitRate`, `DuplexMode`)
22. pwhm (Wi-Fi) ODL — <https://gitlab.com/prpl-foundation/prplmesh/pwhm/plugins/pwhm/-/tree/main/odl> — wld_radio.odl `Enable`, `OperatingFrequencyBand`, `Channel`, `AutoChannelEnable`, `OperatingChannelBandwidth`, `TransmitPower` — DM (pwhm = tr181-wifi): `WiFi.Radio.{i}.Enable/OperatingFrequencyBand/Channel/AutoChannelEnable/OperatingChannelBandwidth/TransmitPower` are %persistent (writable), e.g. `ba-cli Device.WiFi.Radio.1.Channel=36`
23. pwhm (Wi-Fi) ODL — <https://gitlab.com/prpl-foundation/prplmesh/pwhm/plugins/pwhm/-/tree/main/odl> — wld_radio.odl `%read-only string Status`, `ChannelsInUse`, `CurrentOperatingChannelBandwidth`, `RadioStatus` — DM: read-only radio state parameters on `WiFi.Radio.{i}`
24. pwhm (Wi-Fi) ODL — <https://gitlab.com/prpl-foundation/prplmesh/pwhm/plugins/pwhm/-/tree/main/odl> — wld_ssid.odl `SSID`, `Enable`; wld_accesspoint.odl `Security.ModeEnabled`, `KeyPassphrase`, `SAEPassphrase`, `SSIDAdvertisementEnabled` — DM: `WiFi.SSID.{i}.SSID`, `WiFi.AccessPoint.{i}.Security.ModeEnabled` (ModesSupported read-only), `KeyPassphrase`/`SAEPassphrase`, `SSIDAdvertisementEnabled` all writable
25. pwhm (Wi-Fi) ODL — <https://gitlab.com/prpl-foundation/prplmesh/pwhm/plugins/pwhm/-/tree/main/odl> — wld_ssid.odl `Status`, `BSSID`, `Name`; wld_accesspoint.odl `Status` — DM: read-only `WiFi.SSID.{i}.Status/BSSID/Name` and `WiFi.AccessPoint.{i}.Status`
26. pwhm (Wi-Fi) ODL — <https://gitlab.com/prpl-foundation/prplmesh/pwhm/plugins/pwhm/-/tree/main/odl> — wld_accesspoint.odl `%read-only object AssociatedDevice[]` `MACAddress`, `SignalStrength`, `LastDataDownlinkRate`, `LastDataUplinkRate`, `Active` — DM: `WiFi.AccessPoint.{i}.AssociatedDevice.{i}` read-only table with signal strength and last data rates
27. pwhm (Wi-Fi) ODL — <https://gitlab.com/prpl-foundation/prplmesh/pwhm/plugins/pwhm/-/tree/main/odl> — wld_accesspoint.odl `bool kickStation(%in string macaddress);`, `kickStationReason()`, `cleanStation()` — DM: `WiFi.AccessPoint.{i}.kickStation(macaddress)` disconnects a station (reason-code variant available)
28. pwhm (Wi-Fi) ODL — <https://gitlab.com/prpl-foundation/prplmesh/pwhm/plugins/pwhm/-/tree/main/odl> — wld_accesspoint.odl `WPS` `InitiateWPSPBC()`, `InitiateWPSPIN(clientPIN)`, `cancelWPSPairing()`, `Status`, `Enable`, `ConfigMethodsEnabled` — DM: `WiFi.AccessPoint.{i}.WPS.InitiateWPSPBC()` / `InitiateWPSPIN()` start, `cancelWPSPairing()` cancels, read-only `WPS.Status`
29. pwhm (Wi-Fi) ODL — <https://gitlab.com/prpl-foundation/prplmesh/pwhm/plugins/pwhm/-/tree/main/odl> — wld_accesspoint.odl `IEEE80211kEnabled`, `object IEEE80211r` (`Enable`), `MBOEnable`, `sendBssTransferRequest()` — DM: 11k/11r/MBO toggles and 11v BTM request on `WiFi.AccessPoint.{i}`; band steering is a prplMesh controller DM parameter `X_PRPLWARE-COM_Controller.Configuration.BandSteeringEnabled` (prplMesh-configuration.md)
30. tr181-firewall ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-firewall/-/tree/main/odl> — firewall/firewall_definition.odl `Level[]` `DefaultPolicy`, `Chain[]`, `InterfaceSetting`; `getPolicy()` — DM: zone-like defaults are `Firewall.Level.{i}.DefaultPolicy` + `Firewall.Chain.{i}` and `Firewall.getPolicy()`; the observed plugin reads UCI defaults with `uci get firewall.@defaults[0].<chain>` but leaves zone membership unimplemented (observed, prplOS 4.0.3, impls/uci.py)
31. tr181-firewall ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-firewall/-/tree/main/odl> — nat/feature/nat_portmap_definition.odl `PortMapping[]` `ExternalPort`, `InternalPort`, `InternalClient`, `Protocol`, `Interface`, `Enable` — DM: `NAT.PortMapping.{i}` writable instances (add with `NAT.PortMapping.+`, remove with `.-`); also observed via UCI `uci add firewall redirect` … `uci commit firewall; fw4 reload` (observed, prplOS 4.0.3, impls/uci.py)
32. vitro-bdd cpe-gateway example — <https://github.com/alottabits/vitro-bdd/tree/main/examples/cpe-gateway/vitro_plugins/cpe/cpe_plugin/devices/impls> — uci.py `list_port_mappings` parses `uci show firewall` redirect sections — UCI substrate: observed, prplOS 4.0.3, `uci show firewall` → `=redirect` sections; DM equivalent is read of `NAT.PortMapping.{i}` incl. read-only `Status`
33. tr181-firewall ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-firewall/-/tree/main/odl> — firewall/firewall_definition.odl `Chain[].Rule[]` `Target`, `SourceInterface`, `DestInterface`, `SourceIP`, `DestIP`, `Protocol`, `DestPort`, `Enable`; `setService()` — DM: `Firewall.Chain.{i}.Rule.{i}` writable (Target Drop/Accept/Reject), `Firewall.setService()/deleteService()`; also observed `uci add firewall rule` + `fw4 reload` (observed, prplOS 4.0.3, impls/uci.py)
34. vitro-bdd cpe-gateway example — <https://github.com/alottabits/vitro-bdd/tree/main/examples/cpe-gateway/vitro_plugins/cpe/cpe_plugin/devices/impls> — uci.py `list_rules` parses `uci show firewall` `=rule` sections — UCI substrate: observed, prplOS 4.0.3; DM equivalent `Firewall.Chain.{i}.Rule.{i}` read (read-only `Status`) and `Firewall.getService()`/`getPolicy()`
35. tr181-hosts (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-hosts> — README "AccessControl Object" (`AccessPolicy` Allow/Deny, `Schedule`); odl/hosts-accesscontrol-definitions.odl `PhysAddress`, `Enable`, `AccessPolicy`, `Schedule[]` `Day`, `StartTime`, `Duration` — DM: `Hosts.AccessControl.{i}` with `PhysAddress`, `AccessPolicy=Deny` (always blocked) or `Allow` + `Schedule.{i}.Day/StartTime/Duration` for timed access, all writable
36. tr181-upnp ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-upnp/-/tree/main/odl> — tr181-upnp_definition.odl `UPnP.Device.Enable`, `UPnPIGD`; tr181-pcp README "toggle PCP.Client.1.Enable" — DM: `UPnP.Device.Enable` and `UPnP.Device.UPnPIGD` writable (miniupnpd backend); PCP via `PCP.Enable`/`PCP.Client.{i}.Enable` (tr181-pcp)
37. tr181-pcp README — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-pcp> — README "send MAP request … InboundMapping.1"; odl/tr181-pcp_inboundmapping.odl `AssignedExternalPort`, `AssignedExternalIPAddress`, `Status`, `ErrorCode` — DM: `PCP.Client.{i}.Server.{i}.InboundMapping.{i}` has read-only assigned port/address/status; tr181-upnp exposes only `X_PRPL-COM_IGDConfig` (MaxLifetime, CleanupInterval), no mapping table
38. tr181-hosts (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-hosts> — odl/hosts-definitions.odl `Host[]` `PhysAddress`, `IPAddress`, `HostName`, `Layer1Interface`, `Layer3Interface`, `InterfaceType`, `Active`, `DHCPClient`, `AssociatedDevice` — DM: read-only `Hosts.Host.{i}` table with address, name and attachment references (also on the prplOS data-model site, tr181-hosts v0.3.3)
39. tr181-deviceinfo (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-deviceinfo> — odl/deviceinfo-manager_definition.odl `Manufacturer`, `ManufacturerOUI`, `ModelName`, `ProductClass`, `SerialNumber`, `HardwareVersion`, `SoftwareVersion` — DM: read-only identity parameters on `DeviceInfo.`; substrate alternative `uci get cwmp.cpe.userid` (OUI-ProductClass-Serial) observed, prplOS 4.0.3, impls/cpe_tr069.py
40. tr181-deviceinfo (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-deviceinfo> — README "MemoryStatus exposes Total/Free … ProcessStatus exposes aggregate CPUUsage and per-CPU CPU[]"; odl `UpTime` — DM: `DeviceInfo.UpTime`, `MemoryStatus.Total/Free`, `ProcessStatus.CPUUsage` (+ `CPU.{i}` utilisation); load is CPU utilisation, no loadavg parameter
41. tr181-deviceinfo (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-deviceinfo> — odl/deviceinfo-manager_definition.odl `%read-only object Process[]` (`Command`, `Size`, …) — DM: `DeviceInfo.ProcessStatus.Process.{i}` read-only process table
42. vitro-bdd cpe-gateway example — <https://github.com/alottabits/vitro-bdd/tree/main/examples/cpe-gateway/vitro_plugins/cpe/cpe_plugin/devices/impls> — cpe_tr069.py `get_tr069_log`: `logread … grep -iE 'cwmp — icwmpd'`
43. tr181-syslog ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-syslog/-/tree/main/odl> — tr181-syslog_definition_action.odl `Action[]` `LogRemote` `Enable`, `Address`, `Protocol`, `Certificate`, `PeerVerify`; `LogFile.FilePath` — DM: `Syslog.Action.{i}.LogRemote.*` configures remote syslog export (syslog-ng); `DeviceInfo.VendorLogFile.{i}.Upload(URL,Username,Password)` pushes a log file (tr181-deviceinfo odl)
44. tr181-time ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-time/-/tree/main/odl> — time-manager_client_definition.odl `Client[]` `Servers` (csv_string), `Enable`, `Interface`; time-manager_definition.odl `%read-only string Status`, `CurrentLocalTime` — DM: `Time.Client.{i}.Servers` writable NTP server list (chrony backend); `Time.Status` Disabled/Unsynchronized/Synchronized read-only (also on the data-model site, tr181-time v2.4.3)
45. tr181-deviceinfo (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-deviceinfo> — README "TR-181 FirmwareImage — Download and Activate RPC Lifecycle"; odl `%async void Download(URL, AutoActivate, …)`, `Activate(Start, End, Mode, …)`, `BootFirmwareImage` — DM: `DeviceInfo.FirmwareImage.{i}.Download(URL=…, AutoActivate=…)` flashes the inactive bank, `Activate()` switches/reboots (async, usable from TR-069/USP/ubus/CLI)
46. tr181-device ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-device/-/tree/main/odl> — tr181-device_definition.odl `void FactoryReset(%in string Cause, %in string Reason);` — DM: `Device.FactoryReset()` command
47. tr181-device ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-device/-/tree/main/odl> — tr181-device_definition.odl `void Reboot(%in string Cause, %in string Reason);` — DM: `Device.Reboot()` (reboot-service adds cause/reason and `DeviceInfo.Reboots` history); readiness only inferable by re-reading `DeviceInfo.UpTime`/bus objects — the `tr181-bootstatus` repo is an empty README template
48. tr181-deviceinfo (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-deviceinfo> — odl/deviceinfo-manager_definition.odl `VendorConfigFile[]` `%async void Backup(URL, Username, Password)` — DM: `DeviceInfo.VendorConfigFile.{i}.Backup(URL=…)` uploads the configuration file to a URL
49. tr181-deviceinfo (README + odl) — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-deviceinfo> — odl/deviceinfo-manager_definition.odl `%async void Restore(URL, Username, Password, FileSize, TargetFileName, CheckSumAlgorithm, CheckSum)` — DM: `DeviceInfo.VendorConfigFile.{i}.Restore(URL=…)` downloads and applies a configuration file
50. tr181-usermanagement ODL — <https://gitlab.com/prpl-foundation/components/core/plugins/tr181-usermanagement/-/tree/main/odl> — tr181-usermanagement_user.odl `User[]` `Username`, `Password`, `'${global_vendor_prefix_}HashedPassword'`, `Enable`, `RoleParticipation` — DM: `Users.User.{i}.Password` (or `X_PRPL-COM_HashedPassword`) writable; change events are applied to the system account
51. prplOS TR-181 Data Model documentation — <https://prpl-foundation.gitlab.io/prplos/feeds/feed-prpl/> — page `ManagementServer..html` (tr069-manager v1.31.3): `EnableCWMP`, `URL`, `Username`, `Password`, `PeriodicInformEnable`, `PeriodicInformInterval`, `PeriodicInformTime` (persistent) — DM: tr069-manager's `ManagementServer.URL/Username/Password/PeriodicInformEnable/PeriodicInformInterval` are writable; substrate alternative UCI `cwmp.acs.url/username/password/periodic_inform_enable/periodic_inform_interval` (prplOS wiki "ucwmpd"; icwmp docs/api/uci/cwmp.md)
52. iCWMP ubus API (tr069) — <https://dev.iopsys.eu/bbf/icwmp/-/blob/devel/docs/api/ubus/tr069.md> — methods `inform` ("Ubus method to handle RPC"), `status` ("last_session", "next_session") — UCI/ubus substrate: `ubus call tr069 inform` triggers a session, `ubus call tr069 status` reports session state — both observed, prplOS 4.0.3, impls/cpe_tr069.py; DM side (tr069-manager) reads `ManagementServer.State.SessionStatus` (Initializing/idle/busy/failure), `LastSession`, `ConnRequest.ConnRequestPort/Path` and offers `updateConnectionRequestURL()` but no inform-trigger method
53. prplos (build profiles + CI DUT scripts) — <https://gitlab.com/prpl-foundation/prplos/prplos> — profiles/mgmt.yml (`obuspa`, `mod-amxb-usp`, `CONFIG_OBUSPA_WEBSOCKET_MTP_SUPPORT`); .gitlab/scripts/dut-init/obuspa_param_reset-mqtt.txt (`Device.LocalAgent.Controller.1.EndpointID/Enable/MTP.1.Protocol/MQTT.Reference/MQTT.Topic`); cdrouter-dut-configure-usp-common.sh (`obuspa -c get Device.LocalAgent.MTP.1.Protocol`) — USP agent (obuspa) in the prplOS `mgmt` profile: controller endpoint and MTP (MQTT/WebSocket) are written through obuspa's factory-reset file `/etc/config/obuspa_param_reset.txt` and read back with `obuspa -c get Device.LocalAgent.…` — obuspa CLI, not ba-cli
54. tr104-voip plugin repository — <https://gitlab.com/prpl-foundation/components/core/plugins/tr104-voip> — README: "tr181-voip is a service providing VoiceService:2 data model" (repo contains only LICENSE + README) — prplOS lists a voice plugin but publishes no ODL/README naming SIP account (`VoiceService.{i}.SIP.Client`) or registration state; not in any prplos build profile
55. tr104-voip plugin repository — <https://gitlab.com/prpl-foundation/components/core/plugins/tr104-voip> — README (single sentence) — No prplOS source names FXS/POTS line state (`VoiceService.{i}.POTS.FXS`); only the TR-104 stub exists
56. prplOS TR-181 Data Model documentation — <https://prpl-foundation.gitlab.io/prplos/feeds/feed-prpl/> — pages `Device.WiFi.DataElements.Network.Device.{i}..html` (`ID`, `Manufacturer`, `SerialNumber`, `SoftwareVersion`, `InterfaceNumberOfEntries`) and `…Device.{i}.MultiAPDevice.Backhaul..html` (`LinkType`, `BackhaulMACAddress`, `BackhaulDeviceID`, `MACAddress`) — prplMesh 4.2.3 controller.odl/device.odl — DM (prplMesh controller): `Device.WiFi.DataElements.Network.Device.{i}` lists agents, `Radio.{i}`/`Interface.{i}.Neighbor.{i}` the links and `MultiAPDevice.Backhaul` the upstream link type/MACs, read-only via ba-cli
57. prplOS TR-181 Data Model documentation — <https://prpl-foundation.gitlab.io/prplos/feeds/feed-prpl/> — pages `…MultiAPDevice.Backhaul..html` (`LinkType`, `BackhaulMACAddress`), `…Radio.{i}.BackhaulSta..html` (`MACAddress`), `…Radio.{i}.BSS.{i}.STA.{i}..html` (`SignalStrength`, `EstMACDataRateDownlink/Uplink`, `LastDataDownlinkRate`, `UtilizationReceive`) — DM: the backhaul link itself exposes only type and MACs; health metrics must be read from the backhaul STA's entry under the parent agent's `BSS.{i}.STA.{i}` (prplMesh 4.2.3)
58. prplOS TR-181 Data Model documentation — <https://prpl-foundation.gitlab.io/prplos/feeds/feed-prpl/> — page `Device.WiFi.DataElements.Network..html`: `void ClientSteering(in <mandatory> string station_mac, in <mandatory> string target_bssid)` (prplMesh 4.2.3 controller.odl) — DM (prplMesh controller): `Device.WiFi.DataElements.Network.ClientSteering(station_mac=…, target_bssid=…)` steers a client to another agent's BSS; `BTMSteeringDisallowedSTAList`/`SteerEvent.{i}` are the related read objects

### OpenWrt 24.10 line with icwmp

1. IPv4 configuration — <https://openwrt.org/docs/guide-user/network/ipv4/configuration> — Protocol "static" / Protocol "dhcp" (`proto`, `ipaddr`, `netmask`, `gateway`) — option tables for `proto static` and `proto dhcp` on the WAN interface; PPPoE is `proto pppoe` on the WAN protocols page; IPoE = dhcp/static
2. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `ubus call network.interface.wan status` (`up`, `pending`, `uptime`, `address`, `route`, `data`) — status call returns interface up/pending state, uptime and address list (lease data in `data`; `ifstatus wan6` shows prefix lifetimes on the IPv6 page)
3. WAN interface protocols — <https://openwrt.org/docs/guide-user/network/wan/wan_interface_protocols> — `pppoe`: `username`, `password`, `service`, `ac` — the PPPoE option table names username, password and service (plus ac, keepalive, padi_*)
4. Network configuration /etc/config/network — <https://openwrt.org/docs/guide-user/network/network_configuration> — `ifdown <name>` / `ifup <name>` (`ubus list network.interface.*`) — interfaces are brought down and up individually with ifdown/ifup, which restarts the PPPoE session
5. ISP configurations — <https://openwrt.org/docs/guide-user/network/wan/isp-configurations> — `config device` / `option type '8021q'` / `option ifname 'wan'` / `option vid '…'`; `option device 'wan.<vid>'` — many ISP examples define a tagged WAN device by `type 8021q` + `vid` (or legacy `eth0.7`); no `ingress/egress_qos_mapping` on any wiki page
6. IPv6 configuration — <https://openwrt.org/docs/guide-user/network/ipv6/configuration> — Protocol "dhcpv6": `reqaddress`, `reqprefix`; LAN `ip6assign`; `ifstatus wan6` → `ipv6-prefix` — wan6 is `proto dhcpv6` with `reqprefix` (auto/no/1-64), and `ifstatus wan6` lists the delegated `ipv6-prefix` with lifetimes and `assigned` sub-prefixes
7. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `network.interface.<name> status` (`up`, `address`) — there is no provisioning-mode object; v4/v6/dual is inferred from which of wan/wan6 is up with addresses
8. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `ubus call network.device status '{"name":"eth0"}'` → `up`, `link`, `mtu`, `macaddr`, `statistics` — device status reports the carrier `link` flag and counters for the WAN device
9. Network configuration /etc/config/network — <https://openwrt.org/docs/guide-user/network/network_configuration> — interface options `disabled`, `auto`; `ifup`/`ifdown` — interface section has `disabled` and `auto` options; ifup/ifdown change the running state
10. Network configuration /etc/config/network — <https://openwrt.org/docs/guide-user/network/network_configuration> — `ifdown wan` ; `ifup wan` — lease release/re-acquire is documented only as ifdown then ifup (netifd's `network.interface.<name> renew` exists in ubus.c but no wiki page shows it)
11. DHCP and DNS configuration — <https://openwrt.org/docs/guide-user/base-system/dhcp> — `config dhcp`: `start`, `limit`, `leasetime`, `interface`, `ignore` — pool section defines offset, size and lease time per interface
12. DHCP and DNS configuration — <https://openwrt.org/docs/guide-user/base-system/dhcp> — `list dhcp_option '3,<router address>'`, `dhcp_option_force` — per-pool DHCP options in `code,value` or `option:name,value` form
13. DHCP and DNS configuration — <https://openwrt.org/docs/guide-user/base-system/dhcp> — `config host`: `mac`, `ip`, `name`, `leasetime` — static lease section binding MAC to address and hostname
14. odhcpd (techref) — <https://openwrt.org/docs/techref/odhcpd> — `ubus call dhcp ipv4leases`, `ubus call dhcp ipv6leases`; dnsmasq `leasefile` default `/tmp/dhcp.leases` (dhcp page) — lease reads exist as a ubus method for odhcpd and as the lease file for the default dnsmasq
15. DHCP and DNS configuration — <https://openwrt.org/docs/guide-user/base-system/dhcp> — `config dnsmasq`: `list server` — dnsmasq `server` list names upstream DNS forwarders
16. DHCP and DNS configuration — <https://openwrt.org/docs/guide-user/base-system/dhcp> — `config dnsmasq`: `list address '/host/ip'` (`dhcp.@dnsmasq[0].address`) — `address` entries answer local names with fixed addresses
17. DHCP and DNS configuration — <https://openwrt.org/docs/guide-user/base-system/dhcp> — `rebind_protection` (default 1), `list rebind_domain '/example.com/'` — rebind protection toggle and whitelist are dnsmasq UCI options
18. Network configuration /etc/config/network — <https://openwrt.org/docs/guide-user/network/network_configuration> — `config device` `type bridge`, `list ports`; wifi-iface `network` (wireless page) — bridge membership is the device `ports` list; wireless networks join via the wifi-iface `network` option
19. Network configuration /etc/config/network — <https://openwrt.org/docs/guide-user/network/network_configuration> — `config device` `ports` (read with `uci show network`) — configured membership is readable from UCI; the DSA page reads live VLAN/port tables with `bridge v`, no ubus field is documented
20. Guest Wi-Fi basics — <https://openwrt.org/docs/guide-user/network/wifi/guestwifi/guest-wlan> — `uci set network.guest=interface` … `firewall.guest=zone` `input=REJECT` `forward=REJECT`, `forwarding guest→wan` — full UCI recipe for an isolated guest bridge, SSID, DHCP pool and zone
21. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `network.device status` → `link`, `up` — only link state is exposed uniformly; speed/duplex appear as device write options (`speed`, `duplex`, `autoneg`) and swconfig's `link` attribute, not a uniform read API
22. Wi-Fi /etc/config/wireless — <https://openwrt.org/docs/guide-user/network/wifi/basic> — `wifi-device`: `band`, `channel`, `htmode`, `txpower`, `disabled`, `country` — radio section sets band, channel, width (htmode), power and enable
23. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `network.wireless status`; rpcd `iwinfo` `devices`/`info`/`freqlist`/`txpowerlist` — radio/running wireless state is exposed by netifd `network.wireless status` and the rpcd iwinfo object (method names listed, fields not expanded)
24. Wi-Fi /etc/config/wireless — <https://openwrt.org/docs/guide-user/network/wifi/basic> — `wifi-iface`: `ssid`, `encryption`, `key`, `hidden`, `mode ap`, `network`, `disabled` — BSS section with SSID, security mode, passphrase and hidden flag
25. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `network.wireless status`; `iwinfo info` — BSS/running state readable via network.wireless status and iwinfo info (names listed; output fields not expanded on the page)
26. Wireless utilities — <https://openwrt.org/docs/guide-user/network/wifi/wireless-tool/wireless.utilities> — `iwinfo wlan0 assoclist`; `iw dev wlan0 station dump` — both commands list connected clients in AP mode (iw adds retry/fail counts); rpcd `iwinfo assoclist` is also listed on the ubus page
27. hostapd ubus.c (openwrt-24.10) — <https://raw.githubusercontent.com/openwrt/openwrt/openwrt-24.10/package/network/services/hostapd/src/src/ap/ubus.c> — `UBUS_METHOD("del_client", …, del_policy)`, `list_bans` — the 24.10 hostapd build registers `hostapd.<ifname> del_client` (addr, reason, deauth, ban_time); not documented on openwrt.org
28. Wi-Fi /etc/config/wireless — <https://openwrt.org/docs/guide-user/network/wifi/basic> — `wps_pushbutton`, `wps_pin`, `hostapd_cli wps_pin any $PIN` (needs wpad + hostapd-utils) — WPS enable and PIN trigger documented; start/cancel/status via `hostapd.<ifname> wps_start
29. usteer band steering — <https://openwrt.org/docs/guide-user/network/wifi/usteer> — `/etc/config/usteer` `band_steering_interval`, `band_steering_min_snr`, `signal_diff_threshold`; wireless `ieee80211k '1'`, `bss_transition '1'` (+ `ieee80211r`, `mobility_domain`, `ft_over_ds` on the wireless page) — usteer (in the 24.10 packages feed) configures band/AP steering; 11k/v/r are wifi-iface options requiring full wpad
30. Firewall configuration — <https://openwrt.org/docs/guide-user/firewall/firewall_configuration> — `config defaults` (`input`,`output`,`forward`); `config zone` (`name`,`network`,`input`,`output`,`forward`,`masq`) — zone defaults and interface membership live in UCI and are read with `uci show firewall`
31. Firewall configuration — <https://openwrt.org/docs/guide-user/firewall/firewall_configuration> — `config redirect`: `src`, `src_dport`, `dest_ip`, `dest_port`, `proto`, `target DNAT`; `uci add firewall …`/`uci commit firewall` + `/etc/init.d/firewall reload` — port forwards are redirect sections added/removed via uci
32. Firewall configuration — <https://openwrt.org/docs/guide-user/firewall/firewall_configuration> — `config redirect` sections (`uci show firewall`) — the redirect table is the set of redirect sections
33. Firewall configuration — <https://openwrt.org/docs/guide-user/firewall/firewall_configuration> — `config rule`: `src lan`, `dest wan`, `src_ip`, `dest_ip`, `dest_port`, `proto`, `target REJECT — DROP
34. Firewall configuration — <https://openwrt.org/docs/guide-user/firewall/firewall_configuration> — `config rule` sections (`uci show firewall`) — filter rules are readable UCI sections
35. Firewall configuration — <https://openwrt.org/docs/guide-user/firewall/firewall_configuration> — `rule`: `src_mac`, `src_ip`, `target REJECT`, `start_time`, `stop_time`, `weekdays`, `utc_time`, `enabled` — a rule can match a host by MAC/IP, be scheduled by time window and weekdays, and be toggled with `enabled`
36. miniupnpd — <https://openwrt.org/docs/guide-user/firewall/upnp/miniupnpd> — `/etc/config/upnpd`: `enable_upnp`, `enable_natpmp` ("NAT-PMP and PCP"), `enabled` — UPnP IGD and NAT-PMP/PCP are separately enabled via uci (`uci set upnpd.config.enable_natpmp=1`)
37. miniupnpd — <https://openwrt.org/docs/guide-user/firewall/upnp/miniupnpd> — `upnp_lease_file` (`/var/run/miniupnpd.leases`) — active redirects are stored "like DHCP leases" in the lease file; no ubus/CLI read is documented (luci-app-upnp shows them)
38. DHCP and DNS configuration — <https://openwrt.org/docs/guide-user/base-system/dhcp> — dnsmasq `leasefile` `/tmp/dhcp.leases` (MAC, IP, hostname) — host/name/address comes from the lease file; attachment (port/SSID) requires combining `iwinfo assoclist`/`bridge` output, `luci-rpc getHostHints` is LuCI-only
39. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `ubus call system board` → `kernel`, `hostname`, `system`, `model`, `board_name`, `release{distribution,version,revision,target}` — identity read gives model/board and software release but no serial or OUI (icwmp lets `cwmp.cpe.serial_number`/`manufacturer_oui` be set manually)
40. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `ubus call system info` (load averages ÷ 65536) — procd system info returns uptime/load/memory (page expands only the load field)
41. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `ubus call service list` — procd returns all services and their instances, filterable by name
42. Log essentials — <https://openwrt.org/docs/guide-user/base-system/log.essentials> — `logread`, `logread -f`, `logread -e <regexp>`, `ubus subscribe log` — logread reads the ring buffer and can follow/filter
43. System configuration — <https://openwrt.org/docs/guide-user/base-system/system_configuration> — `/etc/config/system`: `log_ip`, `log_port` (514), `log_proto` (udp/tcp), `log_remote`, `log_file`, `log_size` — remote syslog export and local file logging are system-section options
44. NTP configuration — <https://openwrt.org/docs/guide-user/advanced/ntp_configuration> — `uci add_list system.ntp.server=…`, `enable_server`, `use_dhcp`, `interface`; `/etc/init.d/sysntpd restart`; `ntpq` → `peer` — NTP server list is UCI; the only documented sync check installs ntp-utils and reads ntpq peers (busybox sysntpd has no status API)
45. sysupgrade (CLI) — <https://openwrt.org/docs/guide-user/installation/sysupgrade.cli> — `sysupgrade -v /tmp/firmware_image.bin` (`-n` drops config); `ubus call system board` → `release` — image must be in /tmp; upgrade and post-check of the release are documented
46. Failsafe mode, factory reset — <https://openwrt.org/docs/guide-user/troubleshooting/failsafe_and_factory_reset> — `firstboot && reboot` (`firstboot -y`), `jffs2reset`, `umount /overlay && jffs2reset && reboot` — soft and hard overlay reset commands; squashfs/overlayfs only (ext4 x86 excluded)
47. Failsafe mode, factory reset — <https://openwrt.org/docs/guide-user/troubleshooting/failsafe_and_factory_reset> — `reboot`; ubus `system reboot` listed (techref) — reboot is documented; no readiness object exists, so recovery is judged from ubus/ssh reachability and `system info` uptime
48. Backup and restore — <https://openwrt.org/docs/guide-user/troubleshooting/backup_restore> — `sysupgrade -b /tmp/backup-….tar.gz`; `sysupgrade -l`; `/etc/sysupgrade.conf` — configuration archive export with the file list under control
49. Backup and restore — <https://openwrt.org/docs/guide-user/troubleshooting/backup_restore> — `sysupgrade -r /tmp/backup-*.tar.gz` then reboot — restore of a configuration archive
50. SSH access for newcomers — <https://openwrt.org/docs/guide-quick-start/sshadministration> — `passwd` ("Use the “passwd” command to set up a new password"); account `root` — root is the only administrator account; password set with passwd (LuCI "Set up root password" on the login walkthrough)
51. icwmp UCI configuration — cwmp — <https://dev.iopsys.eu/bbf/icwmp/-/blob/devel/docs/api/uci/cwmp.md> — `config acs`: `url` (required), `userid`, `passwd`, `periodic_inform_enable` (default 1), `periodic_inform_interval` (86400), `periodic_inform_time`, `dhcp_discovery`; `config cpe`: `userid`, `passwd`, `port` 7547, `allowed_cr_ip` — ACS URL, credentials and periodic inform are UCI options of /etc/config/cwmp; connection-request credentials/port are in the cpe section
52. icwmp UBUS schema — tr069 — <https://dev.iopsys.eu/bbf/icwmp/-/blob/devel/docs/api/ubus/tr069.md> — `ubus call tr069 inform {"event":"6 CONNECTION REQUEST"…}`; `ubus call tr069 status {}` → `cwmp{acs_url,start_time,status}`, `last_session`, `next_session`, `statistics`; `tr069 command {"command":"reload"}` — inform can be triggered with an event code; status exposes ACS URL, last/next session status; no field for pending connection-request state
53. openwrt/packages net/ (openwrt-24.10) — <https://github.com/openwrt/packages/tree/openwrt-24.10/net> — 382 package directories; none named obuspa/usp/bbf (only `uspot`, a captive portal) — the official 24.10 feeds carry no USP agent; icwmp docs cover TR-069 only
54. Asterisk (VoIP) — <https://openwrt.org/docs/guide-user/services/voip/asterisk> — `/etc/asterisk/pjsip.conf` `[reg_…]`/`[auth_…]`/`[aor_…]`; `asterisk -rx "pjsip show endpoints"`, `pjsip show registration <name>` — a SIP account is a pjsip.conf registration and its state is read via the Asterisk CLI; packages come from the telephony feed, not the base system
55. Asterisk (VoIP) — <https://openwrt.org/docs/guide-user/services/voip/asterisk> — `asterisk-chan-lantiq`, `/etc/asterisk/lantiq.conf` (`channels`, `per_channel_context`) — FXS exists only on Lantiq SoCs through the chan-lantiq package (telephony feed: asterisk, asterisk-chan-lantiq, dahdi-*, freeswitch, kamailio, yate, baresip); no gateway FXS state API
56. IEEE 802.11s Wireless Mesh Networking — <https://openwrt.org/docs/guide-user/network/wifi/mesh/802-11s> — `option mode 'mesh'`, `mesh_id`, `encryption sae`; `iw dev $MESH_IFACE mpath dump` — OpenWrt mesh = 802.11s peers (+ batman-adv/OLSR); no controller/agent topology object; packages feed has no prplmesh/easymesh
57. IEEE 802.11s Wireless Mesh Networking — <https://openwrt.org/docs/guide-user/network/wifi/mesh/802-11s> — `iw dev $MESH_IFACE station dump` — per-peer station stats are the only link-health read; no backhaul concept
58. usteer band steering — <https://openwrt.org/docs/guide-user/network/wifi/usteer> — `roam_scan_snr`, `roam_trigger_snr`, `signal_diff_threshold`; `ubus call usteer get_clients — get_client_info`

### RDK-B quarterly releases, rdkb-2025q4-kirkstone and later

1. CcspPandM TR181-USGv2.XML (provisioning-and-management) — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.WanAddressMode (RW: DHCP/Static/DHALIP), WanStaticIPAddress/SubnetMask/GatewayIP (RW); Device.X_RDK_WanManager.Interface.{i}.VirtualInterface.{i}.IP.IPv4Source (RW: Static/DHCP/PPP) in RdkWanManager_v2.xml — writable mode selectors cover DHCP/IPoE, static and PPP(oE) WAN addressing
2. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.DHCPv4.Client.{i}.DHCPStatus, IPAddress, SubnetMask, IPRouters, DNSServers, LeaseTimeRemaining, DHCPServer (all RO); Device.IP.Interface.{i}.Status — WAN DHCP client state, address and remaining lease are readable
3. RdkPppManager.xml (ppp-manager) — <https://github.com/rdkcentral/ppp-manager/blob/main/config/RdkPppManager.xml> — Device.PPP.Interface.{i}.Username (RW), Password (RW), PPPoE.ServiceName (RW), PPPoE.ACName (RW); same params in CcspPandM XML — PPPoE credentials and service name are writable
4. RdkPppManager.xml (ppp-manager) — <https://github.com/rdkcentral/ppp-manager/blob/main/config/RdkPppManager.xml> — Device.PPP.Interface.{i}.Reset (RW boolean); ConnectionStatus (RO) — writable Reset re-establishes the PPP session; status readable
5. RdkVlanManager.xml (vlan-manager) + RdkWanManager_v2.xml — <https://github.com/rdkcentral/vlan-manager/blob/main/config/RdkVlanManager.xml> — Device.X_RDK_Ethernet.VLANTermination.{i}.VLANID (RW), TPID (RW); Device.X_RDK_WanManager.Interface.{i}.Marking.{i}.EthernetPriorityMark (RW, writable table) — WAN VLAN id and 802.1p priority are writable (VLAN manager + WAN manager, not CcspPandM)
6. RdkWanManager_v2.xml (wan-manager) + CcspPandM XML — <https://github.com/rdkcentral/wan-manager/blob/main/config/RdkWanManager_v2.xml> — Device.X_RDK_WanManager.Interface.{i}.VirtualInterface.{i}.IP.Mode (RW: IPv4 Only/IPv6 Only/Dual Stack/No IP), IP.IPv6Source (RW); Device.DHCPv6.Client.{i}.RequestPrefixes (RW); Device.IP.Interface.{i}.IPv6Prefix.{i}.Prefix/Origin=PrefixDelegation and Device.DHCPv6.Server.Pool.{i}.IAPDPrefixes (RO) — IPv6 WAN mode writable; delegated prefix readable
7. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.DeviceMode (Bridge/Ipv4/Ipv6/Dualstack); Device.X_RDK_WanManager...IP.Mode — provisioning mode (v4/v6/dual/bridge) is readable
8. TR181-EthAgent.xml (ethernet-agent) — <https://github.com/rdkcentral/ethernet-agent/blob/develop/config/TR181-EthAgent.xml> — Device.Ethernet.X_RDK_Interface.{i}.Status (RO Up/Down), WanStatus; Device.Ethernet.X_RDKCENTRAL-COM_WAN.Enabled/Port; Device.Ethernet.Interface.{i}.Status (RO) — WAN physical link state is readable
9. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.ErouterEnable (RW boolean); Device.IP.Interface.{i}.Enable (RW); Device.X_RDK_WanManager.Interface.{i}.Selection.Enable (RW) — WAN (erouter) can be administratively disabled/enabled by a writable parameter
10. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.ReleaseWan (RW), RenewWan (RW); Device.DHCPv4.Client.{i}.Renew (RW); Device.DHCPv6.Client.{i}.Renew (RW) — explicit release and renew triggers exist as writable booleans
11. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.DHCPv4.Server.Pool.{i}.MinAddress, MaxAddress, SubnetMask, LeaseTime, IPRouters, DomainName (RW); Device.DHCPv4.Server.Enable (RW) — DHCPv4 pool range and lease time are writable
12. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.DHCPv4.Server.Pool.{i}.Option.{i} (writable table with AddEntry/DelEntry): Tag, Value, Enable (RW); Device.DHCPv6.Server.Pool.{i}.Option.{i} likewise — DHCP options are add/delete-able with writable tag and hex value
13. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.DHCPv4.Server.Pool.{i}.StaticAddress.{i} (writable table, add/del): Chaddr, Yiaddr, Enable, X_CISCO_COM_DeviceName (RW) — static leases are add/delete-able with writable MAC and address
14. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.DHCPv4.Server.Pool.{i}.Client.{i}.Chaddr, Active, X_CISCO_COM_HostName (RO); Client.{i}.IPv4Address.{i}.IPAddress, LeaseTimeRemaining (RO) — active leases with remaining time are readable
15. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.EnableStaticNameServer, NameServer1, NameServer2 (RW); Device.DNS.Client.Server.{i}.DNSServer (RW, writable table add/del); Device.DHCPv4.Server.Pool.{i}.DNSServers (RW) — upstream resolver addresses for the gateway's DNS proxy are writable
16. Utopia dhcp_server_functions.sh — <https://github.com/rdkcentral/utopia/blob/develop/source/scripts/init/service.d/service_dhcp_server/dhcp_server_functions.sh> — `echo "address=/$LOCDOMAIN_NAME/$locaddr" >> $LOCAL_DHCP_CONF` — local name overrides are generated by the dnsmasq start script; no TR-181 parameter exposes them
17. Utopia service_dhcp_server.sh — <https://github.com/rdkcentral/utopia/blob/develop/source/scripts/init/service.d/service_dhcp_server.sh> — dnsmasq launch line `... --proxy-dnssec --cache-size=0 --stop-dns-rebind ...` — rebind protection exists but only as a fixed command-line flag, no parameter
18. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.Bridging.Bridge.{i} and Bridge.{i}.Port.{i} (writable tables, add/del): Port.{i}.LowerLayers (RW), Enable (RW), PVID (RW); Device.Ethernet.X_RDK_Interface.{i}.AddToLanBridge (RW) — bridge membership is configured by writable ports with LowerLayers references
19. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.Bridging.Bridge.{i}.Status, Port.{i}.Name, Port.{i}.Status, Port.{i}.PortState (RO), Port.{i}.LowerLayers — bridge and port membership/state are readable
20. CcspPandM TR181-USGv2.XML + OneWifi XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.LanManagementEntry.{i} (writable table add/del): LanMode, LanIPAddress, LanSubnetMask, LanDhcpServer, LanNaptEnable (RW); Device.WiFi.SSID.{i}/AccessPoint.{i} — an extra LAN segment with its own DHCP/NAPT can be created, but a guest segment is not a named operation
21. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.Ethernet.Interface.{i}.Status (Up/Down/...), CurrentBitRate, MaxBitRate (RO), DuplexMode (Half/Full/Auto) — LAN port link, speed and duplex are readable
22. OneWifi TR181-WiFi-USGv2.XML — <https://github.com/rdkcentral/OneWifi/blob/develop/config/TR181-WiFi-USGv2.XML> — Device.WiFi.Radio.{i}.Enable (RW), Channel (RW), AutoChannelEnable (RW), OperatingChannelBandwidth (RW: 20/40/80/160/320MHz), TransmitPower (RW), OperatingStandards (RW); OperatingFrequencyBand (RO) — channel, width, power and enable are writable; band cannot be set
23. OneWifi TR181-WiFi-USGv2.XML — <https://github.com/rdkcentral/OneWifi/blob/develop/config/TR181-WiFi-USGv2.XML> — Device.WiFi.Radio.{i}.Status (RO Up/Down/...), ChannelsInUse (RO), Channel, OperatingFrequencyBand (RO), TransmitPowerSupported (RO) — radio operational state is readable
24. OneWifi TR181-WiFi-USGv2.XML — <https://github.com/rdkcentral/OneWifi/blob/develop/config/TR181-WiFi-USGv2.XML> — Device.WiFi.SSID.{i}.SSID (RW), Enable (RW); Device.WiFi.AccessPoint.{i}.Security.ModeEnabled (RW), KeyPassphrase (RW), PreSharedKey (RW), MFPConfig (RW); AccessPoint.{i}.SSIDAdvertisementEnabled (RW) — SSID, security mode, passphrase and hidden flag are writable
25. OneWifi TR181-WiFi-USGv2.XML — <https://github.com/rdkcentral/OneWifi/blob/develop/config/TR181-WiFi-USGv2.XML> — Device.WiFi.SSID.{i}.Status (RO), BSSID (RO), MACAddress (RO); Device.WiFi.AccessPoint.{i}.Status (RO), AssociatedDeviceNumberOfEntries (RO) — BSS state is readable
26. OneWifi TR181-WiFi-USGv2.XML — <https://github.com/rdkcentral/OneWifi/blob/develop/config/TR181-WiFi-USGv2.XML> — Device.WiFi.AccessPoint.{i}.AssociatedDevice.{i}.MACAddress, SignalStrength, LastDataDownlinkRate, LastDataUplinkRate, Active, X_RDKCENTRAL-COM_SNR (all RO) — connected stations with signal and rates are readable
27. OneWifi TR181-WiFi-USGv2.XML — <https://github.com/rdkcentral/OneWifi/blob/develop/config/TR181-WiFi-USGv2.XML> — Device.WiFi.AccessPoint.{i}.ConnectionControl.ClientForceDisassociation (RW string); AccessPoint.{i}.X_CISCO_COM_KickAssocDevices (RW boolean) — a station can be force-disassociated by a writable parameter
28. OneWifi TR181-WiFi-USGv2.XML — <https://github.com/rdkcentral/OneWifi/blob/develop/config/TR181-WiFi-USGv2.XML> — Device.WiFi.AccessPoint.{i}.WPS.Enable (RW), X_CISCO_COM_ActivatePushButton (RW), X_CISCO_COM_ClientPin (RW), X_CISCO_COM_CancelSession (RW), X_CISCO_COM_Pin (RO), ConfigMethodsEnabled (RW) — PBC and PIN onboarding can be started and cancelled; PIN state readable
29. OneWifi TR181-WiFi-USGv2.XML — <https://github.com/rdkcentral/OneWifi/blob/develop/config/TR181-WiFi-USGv2.XML> — Device.WiFi.X_RDKCENTRAL-COM_BandSteering.Enable (RW), BandSetting.{i}.RSSIThreshold/UtilizationThreshold/PhyRateThreshold (RW); Device.WiFi.AccessPoint.{i}.X_RDKCENTRAL-COM_NeighborReportActivated (RW, 11k), X_RDKCENTRAL-COM_BSSTransitionActivated (RW, 11v) — steering and k/v are writable; fast transition (11r) is absent from both WiFi XMLs
30. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.Firewall.Config (High/Low/Off); Device.X_CISCO_COM_Security.Firewall.FirewallLevel (High/Medium/Low/Custom/None), FirewallLevelV6, WanPingEnable — firewall posture is a level preset; no zone defaults or zone membership objects exist
31. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.NAT.PortMapping.{i} (writable table add/del): Enable, ExternalPort, ExternalPortEndRange, InternalPort, Protocol (TCP/UDP/BOTH), InternalClient, RemoteHost, Description (RW) — port forwards are add/delete-able with writable fields
32. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.NAT.PortMapping.{i}.Status (RO) plus all mapping fields; NAT.PortMappingNumberOfEntries — the port-forward table is readable
33. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_Security.InternetAccess.AccessPolicy.{i} (writable table add/del): LanHostMACAddresses/LanHostIPRange (RW); AccessPolicy.{i}.BlockedApplication.{i} (add/del): StartPortNumber, EndPortNumber, Protocol (RW) — egress blocking rules keyed on LAN host + port/protocol can be added and removed
34. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_Security.InternetAccess.AccessPolicy.{i}.* and BlockedApplication.{i}.*; InternetAccess.NumberOfPolicies (RO); InternetAccess.LogEntry.{i} (RO) — configured filter policies (and hit log) are readable
35. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_Security.InternetAccess.AccessPolicy.{i}.Enable, LanHostMACAddresses (RW); AccessPolicy.{i}.Schedule.StartTime, EndTime, AllDay, IncludeMonday..IncludeSunday, AllowAccess (RW) — a host can be blocked immediately or on a weekly schedule
36. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.UPnP.Device.Enable (RW), UPnPIGD (RW); Device.IP.Interface.{i}.X_CISCO_COM_UPnPIGDEnabled (RW) — UPnP IGD can be toggled; no PCP object or parameter exists
37. Utopia WANIPConnectionServiceSCPD.xml — <https://github.com/rdkcentral/utopia/blob/develop/source/igd/src/inc/WANIPConnectionServiceSCPD.xml> — GetGenericPortMappingEntry / AddPortMapping / DeletePortMapping actions; Device.NAT.X_RDK_PortMapping.Data is an opaque RW string — automatic mappings are only enumerable via the IGD's own UPnP action, not via the data model
38. LMLite.XML (lan-manager-lite) — <https://github.com/rdkcentral/lan-manager-lite/blob/develop/config/LMLite.XML> — Device.Hosts.Host.{i}.PhysAddress, IPAddress, HostName, Active, Layer1Interface, Layer3Interface, AssociatedDevice, X_RDKCENTRAL-COM_Parent (RO); Host.{i}.IPv4Address.{i}/IPv6Address.{i}.IPAddress — host table with address, name and attachment interface is readable
39. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.DeviceInfo.Manufacturer, ManufacturerOUI, ModelName, SerialNumber, HardwareVersion, SoftwareVersion, X_CISCO_COM_BaseMacAddress (RO); dmcli example `Device.DeviceInfo.SoftwareVersion` — identity parameters are readable
40. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.DeviceInfo.UpTime (RO); DeviceInfo.ProcessStatus.CPUUsage (RO, %); DeviceInfo.MemoryStatus.Total, Used, Free (RO) — uptime, CPU usage and memory are readable (CPU% rather than load average)
41. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.DeviceInfo.ProcessStatus.Process.{i}.PID, Command, Size, Priority, CPUTime, State (Running/Sleeping/Stopped/Idle/Uninterruptible/Zombie) (RO) — per-process state table is readable
42. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_Diagnostics.Syslog.Entry.{i}.Time, Tag, Level, Message (RO); X_CISCO_COM_Diagnostics.Eventlog.Entry.{i}.* (RO) — syslog and event-log entries are readable through the data model
43. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_Diagnostics.Syslog.RemoteLog.Enable, Host, Port, Protocol (TCP/UDP), Patterns (RW); also DeviceInfo.X_RDKCENTRAL-COM_xOpsDeviceMgmt.Logging.xOpsDMUploadLogsNow (RW) and xOpsDMLogsUploadStatus (RO) — remote syslog target is writable; cloud log upload trigger also exists
44. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.Time.Enable (RW), NTPServer1..NTPServer5 (RW), Status (RO: Disabled/Unsynchronized/Synchronized/Error_FailedToSynchronize/Error), CurrentLocalTime (RO) — NTP servers writable; sync state readable
45. FwUpgradeManager Support in RDKB RPI (RDK wiki) — <https://wiki.rdkcentral.com/x/t4IZCg> — `dmcli eRT setv Device.DeviceInfo.X_RDKCENTRAL-COM_FirmwareDownloadURL string ...`, `...X_RDKCENTRAL-COM_FirmwareToDownload string ...`, `...X_RDKCENTRAL-COM_FirmwareDownloadNow bool true`; X_RDKCENTRAL-COM_FirmwareDownloadStatus (read); params also listed in the tr069 mapper — URL + image name + download-now trigger upgrades from an HTTP-hosted image and reboots
46. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.FactoryReset (RW string); DeviceInfo.FactoryResetCount (RO); DeviceInfo.X_RDKCENTRAL-COM_FirmwareDownloadAndFactoryReset (RW) — factory reset is a writable parameter
47. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.RebootDevice (RW string); DeviceInfo.X_RDKCENTRAL-COM_xOpsDeviceMgmt.RPC.RebootDevice (RW); readiness via DeviceInfo.UpTime, X_RDKCENTRAL-COM_BootTime, X_RDKCENTRAL-COM_LastRebootReason, X_RDKCENTRAL-COM_OnBoarding_State (RO) — reboot is writable; post-reboot readiness readable via uptime/boot-time/onboarding state
48. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.DeviceInfo.VendorConfigFile.{i}.Name/Version/Date (RO static table) is the only config-file object; no Upload/Backup parameter — configuration export is not exposed through the data model
49. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — DeviceInfo.VendorConfigFile.{i} read-only; tr069-protocol-agent sources contain no vendor-configuration-file Download handling — configuration import is not exposed through the data model
50. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.Users.User.{i}.Username (RW), Password (RW), Enable (RW), X_CISCO_COM_AccessPermission (RW: Admin/HomeUser/...), X_RDKCENTRAL-COM_PasswordReset (RW) — local admin credential is writable
51. tr069-protocol-agent ccsp_management_server.c (parameter table) — <https://github.com/rdkcentral/tr069-protocol-agent/blob/develop/source-embedded/DslhManagementServer/ccsp_management_server.c> — Device.ManagementServer.EnableCWMP, URL, Username, Password, PeriodicInformEnable, PeriodicInformInterval, PeriodicInformTime all CCSP_RW; ConnectionRequestUsername/Password CCSP_RW — ACS URL, credentials and periodic inform are writable in the TR-069 PA's own data model
52. tr069-protocol-agent ccsp_management_server.c — <https://github.com/rdkcentral/tr069-protocol-agent/blob/develop/source-embedded/DslhManagementServer/ccsp_management_server.c> — ConnectionRequestURL CCSP_RO, UDPConnectionRequestAddress CCSP_RO, KickURL CCSP_RO; no ForceInform/X_RDKCENTRAL-COM inform parameter in table or mapper — connection-request state is readable but an inform can only be provoked indirectly (e.g. toggling EnableCWMP)
53. RDK Reference USP controller documentation (RDK wiki) — <https://wiki.rdkcentral.com/x/pAbyHQ> — `obuspa -p -v 4 -r factory_reset_example.txt`; Device.LocalAgent.Controller.1.EndpointID, Controller.1.MTP.1.Protocol "MQTT", Controller.1.MTP.1.MQTT.Topic, Device.LocalAgent.MTP.1.MQTT.Reference, Device.MQTT.Client.1.BrokerAddress/BrokerPort — controller endpoint and MQTT transport are set in the agent's boot file; no agent-state parameter documented, release page does not list USP in the reference build
54. RdkTelcoVoiceManager_v2.xml (telco-voice-manager) — <https://github.com/rdkcentral/telco-voice-manager/blob/main/config/RdkTelcoVoiceManager_v2.xml> — Device.Services.VoiceService.{i}.SIP.Client.{i}.AuthUserName, AuthPassword, RegisterURI, Enable (RW), Status (RO: Registering/Up/Error_Registration); SIP.Network.{i}.ProxyServer, RegistrarServer (RW); SIP.Registrar.{i}.Account.{i}.RegistrationStatus (RO) — TR-104v2 SIP account and registration state exist in the voice manager; absent from CcspPandM; CcspMtaAgent has no SIP account objects
55. RdkTelcoVoiceManager_v2.xml + CcspMtaAgent.xml — <https://github.com/rdkcentral/telco-voice-manager/blob/main/config/RdkTelcoVoiceManager_v2.xml> — Device.Services.VoiceService.{i}.POTS.FXS.{i}.Status (RO: Up/Error/Testing/Disabled), Active (RO), DiagTests.*; Device.X_CISCO_COM_MTA.LineTable.{i}.Status (RO On-Hook/Off-Hook), CALLP.LCState — FXS line state readable in both voice models, neither confirmed in the BPI R4 reference build
56. unified-wifi-mesh inc/tr_181.h — <https://github.com/rdkcentral/unified-wifi-mesh/blob/develop/inc/tr_181.h> — Device.WiFi.DataElements.Network.Topology, Network.Device.{i}.ID, BackhaulMACAddress, BackhaulALID, BackhaulMediaType, BackhaulPHYRate, Network.Device.{i}.Radio.{i}.BackhaulSta.MACAddress; porting status per the EasyMesh porting wiki — EasyMesh topology elements are defined by the RDK-B controller code but not yet documented as part of the reference build
57. unified-wifi-mesh inc/tr_181.h — <https://github.com/rdkcentral/unified-wifi-mesh/blob/develop/inc/tr_181.h> — Device.WiFi.DataElements.Network.Device.{i}.MultiAPDevice.Backhaul.Stats.SignalStrength, LinkUtilization, LastDataDownlinkRate, LastDataUplinkRate, BytesSent/Received, ErrorsSent/Received; Network.Device.{i}.BackhaulDown.{i} — backhaul link health elements are defined in code only
58. unified-wifi-mesh inc/tr_181.h + docs — <https://github.com/rdkcentral/unified-wifi-mesh/blob/develop/inc/tr_181.h> — Device.WiFi.DataElements.Network.Device.{i}.Radio.{i}.BSS.{i}.STA.{i}.ClientSteer() (DE_STA_CLIENTSTEER, clientsteer_handler); MultiAPDevice.Backhaul.SteerWiFiBackhaul(); method-invocation format shown for ChannelSelectionRequest() in the unified-wifi-mesh docs — client steering is an EasyMesh controller method, not documented in RDK-B release material

### FRITZ!OS 8.20 and later

1. TR-064 Support – WAN IP Connection (v7, 2025-12-18) — <https://fritz.support/resources/TR-064_WAN_IP_Connection.pdf> — §1.3 SetConnectionType (ConnectionType: Unconfigured, IP_Routed, IP_Bridged); Layer3Forwarding SetDefaultConnectionService picks WANIP vs WANPPP — the only mode writes are routed/bridged per service and default-service selection; addressing method is not settable
2. TR-064 Support – WAN IP Connection (v7, 2025-12-18) — <https://fritz.support/resources/TR-064_WAN_IP_Connection.pdf> — §1.1 GetInfo (ConnectionStatus, ExternalIPAddress, Uptime, DNSServers, X_AVM-DE_IPv6ConnectionStatus), §1.16 GetExternalIPAddress — GetInfo returns connection state, external address and uptime; no DHCP lease expiry is exposed
3. TR-064 Support – WAN PPP Connection (v16, 2025-12-18) — <https://fritz.support/resources/TR-064_WAN_PPP_Connection.pdf> — §1.7 SetUserName, §1.8 SetPassword; §1.1 GetInfo remark on NewPPPoEServiceName — username and password are settable actions; the PPPoE service name is explicitly unsupported
4. TR-064 Support – WAN PPP Connection (v16, 2025-12-18) — <https://fritz.support/resources/TR-064_WAN_PPP_Connection.pdf> — §1.11 ForceTermination, §1.12 RequestConnection — the PPP connection can be torn down and re-requested by two argument-less actions
5. TR-064 Support – WAN Ethernet Link Config (v3, 2025-08-07) — <https://fritz.support/resources/TR-064_WAN_Ethernet_Link_Config.pdf> — Action List (GetEthernetLinkStatus only) — the WAN Ethernet link service exposes a single read action and no VLAN id/priority parameter in any WAN service
6. Internet Gateway Device Support v2 (FRITZ!OS 6.93 baseline, 2023-01-20) — <https://fritz.support/resources/IGD_v2.pdf> — WANIPConnection:2 additional actions X_AVM_DE_GetIPv6Prefix (IPv6Prefix, PrefixLength, ValidLifetime), X_AVM_DE_GetExternalIPv6Address — the delegated prefix and external IPv6 address are readable over IGD; nothing sets the IPv6 WAN mode
7. TR-064 Support – WAN IP Connection (v7, 2025-12-18) — <https://fritz.support/resources/TR-064_WAN_IP_Connection.pdf> — §1.1 GetInfo NewConnectionStatus + NewX_AVM-DE_IPv6ConnectionStatus (both Unconfigured…Connected); IGD X_AVM_DE_GetDsliteStatus — separate IPv4 and IPv6 connection states (and a DS-Lite flag over IGD) let v4/v6/dual be inferred, but no provisioning-mode value exists
8. TR-064 Support – WANCommonInterfaceConfig (v22, 2026-02-25) — <https://fritz.support/resources/TR-064_WAN_Common_Interface_Config.pdf> — §4 GetCommonLinkProperties NewPhysicalLinkStatus (Unavailable, Down, Initializing, Up), NewWANAccessType — the physical WAN link status and access type are returned by a documented read action
9. TR-064 Support – WANDSLLinkConfig (v14, 2025-08-07) — <https://fritz.support/resources/TR-064_WAN_DSL_Link_Config.pdf> — SetEnable remark "Default connection cannot be disabled"; WANIPConnection Enable is out-only in GetInfo — the only Enable write is on the DSL link and is documented as unable to disable the default connection
10. TR-064 Support – WAN IP Connection (v7, 2025-12-18) — <https://fritz.support/resources/TR-064_WAN_IP_Connection.pdf> — §1.7 ForceTermination, §1.8 RequestConnection — an IP connection can be dropped and re-requested, which re-acquires the address, but no renew/release verb exists
11. TR-064 Support – LANHostConfigManagement1 (v9, 2025-08-07) — <https://fritz.support/resources/TR-064_LAN_Host_Config_Management.pdf> — SetAddressRange (MinAddress, MaxAddress), SetDHCPServerEnable, SetIPInterface — the DHCP range and server enable are writable; the state table has no lease-time variable
12. TR-064 Support – LANHostConfigManagement1 (v9, 2025-08-07) — <https://fritz.support/resources/TR-064_LAN_Host_Config_Management.pdf> — SetIPRouter, SetSubnetMask; GetDNSServer (no Set); DomainName out-only in GetInfo — gateway and mask handed out by DHCP are writable, DNS and domain are read-only, no generic option action
13. TR-064 Support – LANHostConfigManagement1 (v9, 2025-08-07) — <https://fritz.support/resources/TR-064_LAN_Host_Config_Management.pdf> — GetInfo NewReservedAddresses (out); Action List has no reservation write — static reservations can be read in aggregate but no action creates or deletes one
14. TR-064 Support – Hosts (v32, 2026-01-29) — <https://fritz.support/resources/TR-064_Hosts.pdf> — §2.3 GetGenericHostEntry (IPAddress, AddressSource, LeaseTimeRemaining, Active, HostName), §2.1 GetHostNumberOfEntries — each host entry carries address source and remaining lease time
15. TR-064 Support – WAN IP Connection (v7, 2025-12-18) — <https://fritz.support/resources/TR-064_WAN_IP_Connection.pdf> — §1.10 X_SetDNSServers (not supported); §1.9 X_GetDNSServers; history v3 "Mark X_SetDNSServer as unsupported" — the only DNS-server write action in the WAN services is explicitly marked unsupported
16. TR-064 Support – Hosts (v32, 2026-01-29) — <https://fritz.support/resources/TR-064_Hosts.pdf> — §2.8 X_AVM-DE_SetHostNameByMACAddress, §2.17–2.19 X_AVM-DE_SetFriendlyName* — a host's name can be set per MAC, but no action defines a local DNS record or override
17. FRITZ! interfaces index (TR-064 service list) — <https://fritz.com/en/pages/interfaces> — TR-064 service table (no DNS/rebind service) — the published service list contains no DNS forwarder service and no rebind-protection parameter
18. TR-064 Support – LANHostConfigManagement1 (v9, 2025-08-07) — <https://fritz.support/resources/TR-064_LAN_Host_Config_Management.pdf> — Action List (SetIPInterface, SetAddressRange, …) — the LAN-side services carry no bridge or VLAN membership write
19. TR-064 Support – Hosts (v32, 2026-01-29) — <https://fritz.support/resources/TR-064_Hosts.pdf> — §2.10 X_AVM-DE_GetSpecificHostEntryByIP (InterfaceType, X_AVM-DE_Port, X_AVM-DE_Speed, X_AVM-DE_Guest) — which LAN port or guest segment a host sits on is readable per host, not as a bridge table
20. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §1 introduction (logical guest AP as service #2/#3/#4), §2.1 SetEnable, §2.12 SetSSID, §2.4 SetSecurityKeys, §2.33 X_AVM-DE_GetWLANExtInfo (APType normal/guest, UserIsolation) — the guest Wi-Fi is a separate service instance with the full Set* action set; wired guest access is not covered
21. TR-064 Support – LAN Ethernet Interface Config (v3, 2025-08-07) — <https://fritz.support/resources/TR-064_LAN_Ethernet_Interface_Config.pdf> — GetInfo (Status, MaxBitRate, DuplexMode, MACAddress), GetStatistics; Hosts X_AVM-DE_Port/X_AVM-DE_Speed — link status, rate and duplex are read for one LAN interface; per-port speed is only visible on connected hosts
22. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.1 SetEnable, §2.16 SetChannel (0 = auto), §2.3 SetConfig, §2.34 X_AVM-DE_SetWLANGlobalEnable; band = service instance — radio enable and channel are writable per band instance; width and power have no action
23. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.2 GetInfo (Enable, Status Up/Disabled, Channel, Standard, X_AVM-DE_FrequencyBand), §2.15 GetChannelInfo (PossibleChannels, X_AVM-DE_AutoChannelEnabled) — radio enable, status, channel, band and auto-channel state are returned
24. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.12 SetSSID, §2.14 SetBeaconType (None, WPA, 11i, WPAand11i, WPA3, 11iandWPA3, OWE, OWETrans), §2.4 SetSecurityKeys (KeyPassphrase/PreSharedKey), §2.18 SetBeaconAdvertisement (hidden) — SSID, security mode, passphrase and SSID broadcast are each set by a documented action
25. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.2 GetInfo (SSID, BSSID, BeaconType, Enable, Status), §2.17 GetBeaconAdvertisement, §2.19 GetTotalAssociations — BSS identity, security mode, enable/status and association count are readable
26. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.20 GetGenericAssociatedDeviceInfo (MAC, IP, AuthState, X_AVM-DE_Speed, X_AVM-DE_SignalStrength, X_AVM-DE_ChannelWidth), §2.23 X_AVM-DE_GetWLANDeviceListPath — per-station signal strength, rate and channel width are listed
27. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2 Action List (38 actions, none acting on a single station) — the service's full action list has no kick/deauth action
28. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.36 X_AVM-DE_SetWPSConfig (WPSMode pbc / stop), §2.35 X_AVM-DE_GetWPSInfo (WPSStatus off, inactive, active, success, err_*), §2.37 X_AVM-DE_SetWPSEnable — push-button WPS can be started and stopped and its status read (PIN variables marked obsolete)
29. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2 Action List; Mesh schema node_interfaces.steering_enabled, 11k_friendly, 11v_friendly (read-only) — neither the Wi-Fi service nor the mesh JSON offers a write for steering or 802.11k/v/r
30. TR-064 Support – X_AVM-DE_HostFilter (v8, 2025-09-11) — <https://fritz.support/resources/TR-064_Host_Filter.pdf> — §2.4 GetWANAccessByIP (WANAccess granted/denied/error); no zone action anywhere — the security surface is per-host WAN access, with no zone defaults or membership
31. TR-064 Support – WAN IP Connection (v7, 2025-12-18) — <https://fritz.support/resources/TR-064_WAN_IP_Connection.pdf> — §1.14 AddPortMapping (restriction text), §1.15 DeletePortMapping; same in WAN PPP Connection §1.18/§1.19 — add/delete actions exist but the document limits adds to the requesting host and excludes guest hosts
32. TR-064 Support – WAN IP Connection (v7, 2025-12-18) — <https://fritz.support/resources/TR-064_WAN_IP_Connection.pdf> — §1.11 GetPortMappingNumberOfEntries, §1.12 GetGenericPortMappingEntry (RemoteHost, ExternalPort, Protocol, InternalPort, InternalClient, Enabled, Description, LeaseDuration) — the full mapping table is enumerable by index
33. TR-064 Support – X_AVM-DE_HostFilter (v8, 2025-09-11) — <https://fritz.support/resources/TR-064_Host_Filter.pdf> — §2 Action List (DisallowWANAccessByIP, AddHostEntryToFilterProfile, tickets) — the host-filter service blocks hosts and assigns time profiles; no address/port/protocol rule can be written
34. TR-064 Support – X_AVM-DE_HostFilter (v8, 2025-09-11) — <https://fritz.support/resources/TR-064_Host_Filter.pdf> — §2.10 GetFilterProfiles, §2.7 GetFilterProfileByID, §4.1 FilterProfile XML (TimeTable Time/Action) — readable rules are per-profile allow/disallow timetables, not packet-filter rules
35. TR-064 Support – X_AVM-DE_HostFilter (v8, 2025-09-11) — <https://fritz.support/resources/TR-064_Host_Filter.pdf> — §2.1 DisallowWANAccessByIP (Disallow 1/0), §2.9 AddHostEntryToFilterProfile (profile with timetable), §2.8 AddTicketTimeToHostEntryByIP — a host can be blocked immediately or bound to a scheduled filter profile
36. TR-064 Support – X_UPnP (v3, 2025-08-08) — <https://fritz.support/resources/TR-064_UPnP.pdf> — SetConfig (Enable "UPnP functionality enabled", UPnPMediaServer); IGD GetAddonInfos UpnpControlEnabled "True, if portmappings allowed" (read) — UPnP can be switched on/off by action; the port-mapping permission is only readable and PCP is absent
37. Internet Gateway Device Support v2 (FRITZ!OS 6.93 baseline, 2023-01-20) — <https://fritz.support/resources/IGD_v2.pdf> — WANIPConnection:2 GetListOfPortMappings, GetGenericPortMappingEntry; TR-064 GetGenericPortMappingEntry — the mapping table is readable over IGD and TR-064 but entries carry no automatic/static origin marker
38. TR-064 Support – Hosts (v32, 2026-01-29) — <https://fritz.support/resources/TR-064_Hosts.pdf> — §2.3 GetGenericHostEntry (MAC, IP, HostName, InterfaceType Ethernet/802.11, Active), §2.10 X_AVM-DE_GetSpecificHostEntryByIP (X_AVM-DE_Port, X_AVM-DE_Guest), §2.14 X_AVM-DE_GetHostListPath (XML list) — the host table with address, name and attachment (interface type, port, guest) is enumerable
39. TR-064: Supported Actions of Device Info (v11, 2025-08-07) — <https://fritz.support/resources/TR-064_Device_Info.pdf> — GetInfo (ManufacturerName, ManufacturerOUI, ModelName, SerialNumber, SoftwareVersion, HardwareVersion, ProductClass) — all five identity fields are returned by one action
40. TR-064: Supported Actions of Device Info (v11, 2025-08-07) — <https://fritz.support/resources/TR-064_Device_Info.pdf> — GetInfo NewUpTime (ui4) — uptime is readable; no service exposes CPU load or memory
41. FRITZ! interfaces index (TR-064 service list) — <https://fritz.com/en/pages/interfaces> — TR-064 service table — the published services (DeviceInfo, DeviceConfig, …) contain nothing about processes
42. TR-064: Supported Actions of Device Info (v11, 2025-08-07) — <https://fritz.support/resources/TR-064_Device_Info.pdf> — GetDeviceLog (NewDeviceLog), X_AVM-DE_GetDeviceLogPath (XML events; filter all/sys/net/fon/wlan/usb) — the device log is readable as text and as filtered XML
43. TR-064 Support – DeviceConfig (v12, 2025-12-01) — <https://fritz.support/resources/TR-064_Device_Config.pdf> — §2.12 X_AVM-DE_SendSupportData (mode normal/mesh), §2.14 X_AVM-DE_SetSupportDataEnable — the only log-shipping action sends support data to the vendor; no syslog destination is configurable
44. TR-064 Support – Time (v5, 2025-08-07) — <https://fritz.support/resources/TR-064_Time.pdf> — SetNTPServers (NTPServer1, NTPServer2), GetInfo (CurrentLocalTime; LocalTimeZone etc. not supported) — two NTP servers are settable and current time readable, but no synchronisation status exists
45. TR-064 Support – Special Actions (v5, 2025-08-07) — <https://fritz.support/resources/TR-064_Special_Actions.pdf> — §3.2 Firmware Upgrade (HTTP POST multipart to /cgi-bin/firmwarecfg: sid + UploadFile image), sid from UserInterface X_AVM-DE_DoPrepareCGI; alternative UserInterface X_AVM-DE_DoManualUpdate (DownloadURL) — a firmware image can be uploaded by POST or pulled from a URL; downgrade is "Not supported"
46. TR-064 Support – DeviceConfig (v12, 2025-12-01) — <https://fritz.support/resources/TR-064_Device_Config.pdf> — §2.5 FactoryReset (no arguments) — factory reset is a documented argument-less action
47. TR-064 Support – DeviceConfig (v12, 2025-12-01) — <https://fritz.support/resources/TR-064_Device_Config.pdf> — §2.6 Reboot (no arguments); DeviceInfo GetInfo NewUpTime — reboot exists; no readiness/boot-complete indicator is documented
48. TR-064 Support – DeviceConfig (v12, 2025-12-01) — <https://fritz.support/resources/TR-064_Device_Config.pdf> — §2.8 X_AVM-DE_GetConfigFile (Password in, ConfigFileUrl out; URL valid <30 s, digest-protected, LAN-only per Remote Access §5.1) — an encrypted configuration export is produced on demand and fetched from a short-lived URL
49. TR-064 Support – DeviceConfig (v12, 2025-12-01) — <https://fritz.support/resources/TR-064_Device_Config.pdf> — §2.9 X_AVM-DE_SetConfigFile (Password, ConfigFileUrl http/https); Special Actions §3.1 POST ConfigImportFile — a configuration file is imported from a client-hosted URL or by multipart POST
50. TR-064 Support – LANConfigSecurity (v12, 2025-08-07) — <https://fritz.support/resources/TR-064_LAN_Config_Security.pdf> — §2.4 SetConfigPassword (NewPassword; "needs up to 20 seconds"), §2.5 X_AVM-DE_GetUserList, §2.1 GetInfo X_AVM-DE_IsDefaultPasswordActive — the administrator password is settable by action; user creation is not (password only)
51. TR-064 Support – ManagementServer (v10, 2025-08-07) — <https://fritz.support/resources/TR-064_Management_Server.pdf> — §1.2 SetManagementServerURL, §1.3 SetManagementServerUsername, §1.4 SetManagementServerPassword, §1.5 SetPeriodicInform (Enable, Interval, Time), §1.8 X_SetTR069Enable — ACS URL, credentials and periodic inform are each writable (URL change may demand second-factor auth, codes 866–868)
52. TR-064 Support – ManagementServer (v10, 2025-08-07) — <https://fritz.support/resources/TR-064_Management_Server.pdf> — §1.1 GetInfo (ConnectionRequestURL, ConnectionRequestUsername, ParameterKey), §1.6 SetConnectionRequestAuthentication — connection-request URL and credentials are exposed but nothing triggers an Inform or reports its state
53. TR-064 Support – X_AVM-DE_USPController (v6, 2025-08-08) — <https://fritz.support/resources/TR-064_USP_Controller.pdf> — §2.4 AddUSPController (EndpointID, MTP, Hostname, Path, Port, UseTLS, MQTT topics, Username/Password, AccessRight*), §2.6 SetUSPControllerEnableByIndex, §2.2 GetUSPControllerByIndex — a USP controller endpoint and transport are fully configurable; the service table has no agent/connection status variable
54. TR-064 Support – X_VoIP (v71, 2025-08-08) — <https://fritz.support/resources/TR-064_VoIP.pdf> — §2.14 X_AVM-DE_AddVoIPAccount (Registrar, Number, Username, Password, OutboundProxy, STUNServer), §2.32 X_AVM-DE_GetVoIPStatus (disabled, not registered, registered, connected, unknown) — SIP accounts are added by action and their registration state is readable per account
55. TR-064 Support – X_VoIP (v71, 2025-08-08) — <https://fritz.support/resources/TR-064_VoIP.pdf> — §2.29 X_AVM-DE_GetPhonePort (Index in, X_AVM-DE_PhoneName out; analog, ISDN, DECT ports) — analog ports are enumerable by name, but no off-hook/ringing/line status is exposed
56. TR-064 Support – Hosts (v32, 2026-01-29) — <https://fritz.support/resources/TR-064_Hosts.pdf> — §2.15 X_AVM-DE_GetMeshListPath → JSON per Mesh-Topology_Schema_v8.7 (nodes.mesh_role master/slave, is_meshed; node_interfaces; node_links node_1_uid/node_2_uid, state) — the mesh topology (nodes, interfaces, links) is fetched as JSON via a documented action and schema
57. Mesh Topology JSON Schema v8.7 (FRITZ!OS 08.19–08.25) — <https://fritz.support/resources/Mesh-Topology_Schema_v8.7.json> — node_links: state, cur_data_rate_rx/tx, max_data_rate_rx/tx, cur_availability_rx/tx, rx_rsni/tx_rsni, rx_rcpi/tx_rcpi; node_interfaces.is_upstream, blocking_state — per-link rate, availability and signal metrics exist, but backhaul links must be inferred from mesh_role/is_upstream
58. Mesh Topology JSON Schema v8.7 (FRITZ!OS 08.19–08.25) — <https://fritz.support/resources/Mesh-Topology_Schema_v8.7.json> — node_interfaces.steering_enabled ("Steering of this interface is enabled.", boolean); Hosts service has only Get*MeshListPath — the mesh surface is read-only JSON; no TR-064 action steers a client

### RouterOS v7

1. DHCP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP> — `/ip dhcp-client add interface=` (DHCP Client > Properties) — The WAN mode is the object added on the WAN port: `/ip dhcp-client` for DHCP, `/interface pppoe-client` (PPPoE page) for PPPoE, `/ip address` for static; no single mode property exists
2. DHCP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP> — `/ip dhcp-client` read-only `status`, `address`, `gateway`, `dhcp-server`, `expires-after` — The DHCP client's read-only properties give the state (bound/searching/…), the assigned address and the lease expiry; `/interface pppoe-client monitor` gives `status`, `uptime`, `local-address` for PPPoE
3. PPPoE — <https://help.mikrotik.com/docs/spaces/ROS/pages/2031625/PPPoE> — `/interface pppoe-client` `user`, `password`, `service-name` (PPPoE Client > Properties) — The PPPoE client property table lists settable `user`, `password` and `service-name` (plus `ac-name`, `add-default-route`, `use-peer-dns`)
4. Console — <https://help.mikrotik.com/docs/spaces/ROS/pages/8978498/Console> — general commands `disable` / `enable` — The Console page lists `enable`/`disable` among commands common to nearly all menus; the PPPoE page documents no session-reset or redial command
5. VLAN — <https://help.mikrotik.com/docs/spaces/ROS/pages/88014957/VLAN> — `/interface vlan` `vlan-id` (1..4094), `interface` — The VLAN interface property table has `vlan-id` and `interface` but no priority property; the "WMM and VLAN priority" page shows PCP set with `/ip firewall mangle add action=set-priority new-priority=…` (default priority 0)
6. DHCP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP> — `/ipv6 dhcp-client add request=prefix pool-name=` ; read-only `prefix`, `status`, `expires-after` — The DHCPv6 Client section documents `request` (address, prefix), `pool-name`, `pool-prefix-length`, and `print detail` showing `prefix=…/62 status=bound`; `/ipv6 address add address=::1/64 from-pool=` uses the delegated prefix
7. DHCP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP> — `/ip dhcp-client` `status` and `/ipv6 dhcp-client` `status` — Both client menus expose a `status` read-only property (bound/searching/…); the v4/v6/dual mode is inferred from which clients are bound, no single field names it
8. Ethernet — <https://help.mikrotik.com/docs/spaces/ROS/pages/8323191/Ethernet> — `/interface ethernet monitor` `status` (link-ok / no-link / unknown), `rate` — The Monitor section documents the current link status and rate of an Ethernet interface; PPPoE session state is `monitor` `status` on the PPPoE page
9. Console — <https://help.mikrotik.com/docs/spaces/ROS/pages/8978498/Console> — `disable` / `enable` ; `interface print` flags `X - disabled, D - dynamic, R - running` — Console documents `enable`/`disable` (and `set … disabled=`) for any interface item and the `interface print` flag legend for reading the administrative and running state
10. DHCP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP> — `/ip dhcp-client` commands `release (numbers)`, `renew (numbers)` — The DHCP Client menu documents `release` ("Release current binding and restart the DHCP client") and `renew` ("Renew current leases …"); DHCPv6 client has the same two commands
11. DHCP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP> — `/ip dhcp-server` `address-pool`, `lease-time` (default 30m), `interface`; `/ip dhcp-server network add address= gateway=` — DHCP Server Properties list the pool and lease-time; the Network submenu sets `address`, `gateway`, `netmask`, `dns-server`
12. DHCP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP> — `/ip dhcp-server option` `code` (1..254), `value`; `/ip dhcp-server option sets`; network `dhcp-option`, `dns-server`, `ntp-server`, `domain` — The DHCP Options section documents custom options by code/value (and option sets), attached per network or per lease via `dhcp-option`/`dhcp-option-set`
13. DHCP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP> — `/ip dhcp-server lease` `address`, `mac-address`, `client-id`, `block-access`; command `make-static (id)` — The Leases section documents adding static leases (address + mac-address/client-id) and converting a dynamic lease with `make-static`
14. DHCP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805500/DHCP> — `/ip dhcp-server lease print` (ADDRESS, MAC-ADDRESS, HOST-NAME, SERVER, STATUS); `status` waiting/testing/…/bound — The Leases section says issued leases are shown as dynamic entries and documents the `status` values and print output columns
15. DNS — <https://help.mikrotik.com/docs/spaces/ROS/pages/37748767/DNS> — `/ip dns set servers=` (list of IPv4/IPv6 addresses@vrf), `allow-remote-requests` — DNS configuration documents the upstream `servers` list (and `use-doh-server`) plus `allow-remote-requests` to serve LAN clients
16. DNS — <https://help.mikrotik.com/docs/spaces/ROS/pages/37748767/DNS> — `/ip dns static` `name`, `address`, `type` (A, AAAA, CNAME, …) — The DNS Static section documents local name records with name, address and record type
17. DNS — <https://help.mikrotik.com/docs/spaces/ROS/pages/37748767/DNS> — `/ip dns` property table (configuration, cache, static, DoH, adlist) — The DNS page documents servers, cache, static records, DoH and adlists; no rebinding-protection property exists
18. Bridging and Switching — <https://help.mikrotik.com/docs/spaces/ROS/pages/328068/Bridging+and+Switching> — `/interface bridge add`; `/interface bridge port add bridge=bridge1 interface=ether1` — Bridge port membership is configured by adding ports; the page states non-Ethernet interfaces such as WiFi are bridged the same way (wifi/wireless interfaces listed as bridge members)
19. Bridging and Switching — <https://help.mikrotik.com/docs/spaces/ROS/pages/328068/Bridging+and+Switching> — `/interface bridge port print` (INTERFACE, BRIDGE, HW, PVID, PRIORITY, PATH-COST, HORIZON); `/interface bridge host` — Bridge and port membership is read with `bridge port print`; the host table shows `mac-address`, `on-interface`, `bridge`
20. Bridging and Switching — <https://help.mikrotik.com/docs/spaces/ROS/pages/328068/Bridging+and+Switching> — "VLAN Example - InterVLAN Routing by Bridge"; `/interface bridge vlan` `vlan-ids`, `tagged`, `untagged` — A guest segment is built as a bridge VLAN with its own `/interface vlan`, address, DHCP server and filter rules; no single guest-network object exists
21. Ethernet — <https://help.mikrotik.com/docs/spaces/ROS/pages/8323191/Ethernet> — `/interface ethernet monitor` `status`, `rate` (10Mbps…400Gbps), `full-duplex` (yes/no), `auto-negotiation` — The Monitor section documents link status, negotiated rate, duplex and auto-negotiation state per port
22. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — wifi package: `channel.band`, `channel.frequency`, `channel.width`, `configuration.tx-power` (0..40), `disabled` — The wifi package (wifi-qcom / wifi-qcom-ac) Property Reference documents band, frequency, width, tx-power limit and `disabled` on `/interface wifi`; legacy wireless package uses `band`, `frequency`, `channel-width`, `tx-power`
23. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — read-only `running`, `inactive`, `bound`; `/interface/wifi/radio print detail`; `/interface/wifi/monitor` — The wifi package page documents the interface flags and radio capabilities (bands, current-channels, current-max-reg-power) but references `/interface/wifi/monitor` output only for puncturing state, without a field table
24. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — wifi package: `configuration.ssid`, `configuration.hide-ssid`, `security.authentication-types`, `security.passphrase` — The wifi package Property Reference documents SSID, hidden SSID, authentication types (WPA2/WPA3/OWE…) and passphrase; legacy wireless uses `ssid`, `hide-ssid`, `security-profile`
25. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — `/interface/wifi/print detail`; flags `X - disabled, I - inactive, R - running` — wifi package: BSS state is read from the interface flags and effective configuration shown by `print detail`; no dedicated BSS status table is documented
26. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — wifi package: `/interface/wifi/registration-table` `mac-address`, `signal` (dBm), `rx-rate`, `tx-rate`, `tx-bits-per-second`, `uptime` — The wifi package Registration table section lists per-station signal, rates, bytes/packets and uptime (legacy: `/interface wireless registration-table`)
27. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — wifi package, "De-authentication": `/interface/wifi/registration-table remove [find where mac-address=…]` — The wifi package documents de-authenticating a client by removing its registration-table entry (legacy wireless registration table is read-only on its page)
28. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — `/interface/wifi wps-push-button wifi1`; `security.wps` (disabled / push-button); `/interface/wifi/wps-client` — wifi package: WPS server accepts WPS for 2 minutes after `wps-push-button`; no cancel command, PIN mode or WPS state field is documented (legacy wireless: `wps-mode`, `wps-client`)
29. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — Steering properties `neighbor-group`, `rrm` (802.11k), `wnm` (802.11v), `transition-threshold`; Security `ft` (802.11r) — wifi package Steering documents 802.11k neighbor reports, 802.11v BSS-transition and 802.11r FT; band preference is only the note that 5 GHz APs are marked preferable within a neighbor group
30. Default configurations — <https://help.mikrotik.com/docs/spaces/ROS/pages/167706788/Default+configurations> — "AP Router": WAN port protected by firewall, other ports in LAN bridge; `/interface list` WAN/LAN — Defaults are described per configuration type (WAN port firewalled, LAN bridge); membership is read from interface lists and filter rules, there is no zone abstraction
31. NAT — <https://help.mikrotik.com/docs/spaces/ROS/pages/3211299/NAT> — `/ip firewall nat add chain=dstnat action=dst-nat dst-port= protocol= to-addresses=` ("Destination NAT") — The NAT page documents adding a dstnat rule with `to-addresses`/`to-ports`; `remove` is a Console common command
32. NAT — <https://help.mikrotik.com/docs/spaces/ROS/pages/3211299/NAT> — `ip firewall nat print` (Flags: X - disabled, I - invalid, D - dynamic) — The NAT page shows the nat table print output including dynamic rules
33. Filter — <https://help.mikrotik.com/docs/spaces/ROS/pages/48660574/Filter> — `/ip firewall filter add chain=forward action=drop` with `src-address`, `dst-address`, `out-interface`, `protocol`, `dst-port` — The Filter page documents forward-chain rules with drop/reject/accept actions; matchers incl. `out-interface-list`, `src-mac-address`, `time` are on the Common Firewall Matchers page
34. Filter — <https://help.mikrotik.com/docs/spaces/ROS/pages/48660574/Filter> — `/ip firewall filter` chains input/forward/output; `print` (Console common command) — The Filter page defines the chains and rules; reading them is the generic `print` documented on the Console page
35. Kid Control — <https://help.mikrotik.com/docs/spaces/ROS/pages/129531911/Kid+Control> — `/ip kid-control` `mon`…`sun`, `tur-*`, `rate-limit`, `pause`/resume; `/ip kid-control device` `mac-address`, `user` — Kid Control schedules per-weekday Internet access per device (by MAC) and pauses on demand; `/ip dhcp-server lease block-access=yes` (DHCP page) blocks a host immediately; firewall `time` and `src-mac-address` matchers also exist
36. UPnP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805490/UPnP> — `/ip upnp set enabled=yes`; `/ip upnp interfaces add interface= type=external/internal` — UPnP page documents enabling the service and declaring internal/external interfaces; PCP/NAT-PMP are not mentioned anywhere
37. UPnP — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805490/UPnP> — "dynamic NAT rules" in `ip firewall nat print` flag `D`, comment "upnp <ip>: <app>" — The Configuration Example shows UPnP mappings appearing as dynamic dstnat rules (`dst-port`, `to-addresses`, `to-ports`, `protocol`)
38. Neighbor discovery — <https://help.mikrotik.com/docs/spaces/ROS/pages/24805517/Neighbor+discovery> — `/ip neighbor` `interface`, `address`, `mac-address`, `identity`; DHCP lease `host-name`, `address`, `mac-address` — Hosts are read from `/ip dhcp-server lease` (name/address/MAC), `/ip arp` (address/MAC/interface) and `/ip neighbor` (discovery-protocol hosts); no unified host table exists
39. RouterBOARD — <https://help.mikrotik.com/docs/spaces/ROS/pages/40992878/RouterBOARD> — `/system routerboard` `model`, `serial-number`, `current-firmware`; `/system resource` `version`, `board-name`, `platform` — Model and serial come from `/system routerboard print`; RouterOS version, board name and platform from `/system resource print`; OUI is read from interface MAC, not a named field
40. Resource — <https://help.mikrotik.com/docs/spaces/ROS/pages/40992875/Resource> — `/system resource` `uptime`, `cpu-load`, `free-memory`, `total-memory`, `free-hdd-space`; `/system resource cpu` `load` — All `/system resource` properties are read-only and include uptime, combined CPU load, free/total memory; per-core load is in the CPU submenu
41. Profiler — <https://help.mikrotik.com/docs/spaces/ROS/pages/8323153/Profiler> — `/tool profile` (NAME, CPU, USAGE); "Classifiers" — Profiler shows CPU usage per RouterOS process class (firewall, dhcp, winbox, idle…), not individual processes
42. Log — <https://help.mikrotik.com/docs/spaces/ROS/pages/328094/Log> — `/log print`, `/log print follow where topics~…`, `where buffer=` — The Log page documents reading the in-memory log with filtering and follow mode
43. Log — <https://help.mikrotik.com/docs/spaces/ROS/pages/328094/Log> — `/system logging action` `target=remote`, `remote-port`, `remote-protocol`, `remote-log-format` (syslog/cef), `syslog-facility`; `/system logging add topics= action=` — Remote syslog export is configured as a logging action with target `remote` and routed per topic
44. NTP — <https://help.mikrotik.com/docs/spaces/ROS/pages/40992869/NTP> — `/system ntp client` `enabled`, `servers` (FQDN/IP), `mode`; Status synchronized/stopped/waiting/using-local-clock; `/system/ntp/monitor-peers` — NTP Client properties set the servers; the Status field and `monitor-peers` (stratum, offset, jitter) give sync state
45. Upgrading and installation — <https://help.mikrotik.com/docs/spaces/ROS/pages/328142/Upgrading+and+installation> — "Manual upgrade": upload .npk to Files, `/system reboot`, verify `/system package print`; `/system package update check-for-updates`/`install`; `/system routerboard upgrade` — Firmware is upgraded by uploading the package image and rebooting (or via package update), followed by a RouterBOOT upgrade
46. Configuration Management — <https://help.mikrotik.com/docs/spaces/ROS/pages/328155/Configuration+Management> — `/system reset-configuration` `no-defaults`, `keep-users`, `skip-backup`, `run-after-reset` — The Configuration Reset section documents the factory-reset command and its options; the router reboots into default configuration
47. Upgrading and installation — <https://help.mikrotik.com/docs/spaces/ROS/pages/328142/Upgrading+and+installation> — `/system reboot` ("Reboot, yes? [y/N]") — Reboot is documented; readiness after reboot is not a field — read `/system resource` `uptime` (Resource page) once management is reachable
48. Configuration Management — <https://help.mikrotik.com/docs/spaces/ROS/pages/328155/Configuration+Management> — `/export file=` (`compact`, `terse`, `verbose`, `show-sensitive`) ; `/system backup save` — Export writes the configuration as an .rsc script; the Backup page adds the binary `/system backup save name= password=`
49. Backup — <https://help.mikrotik.com/docs/spaces/ROS/pages/40992852/Backup> — `/system backup load name= password=` ; `/import file-name=` (`dry-run`, Configuration Management) — Binary backups are restored with `backup load`; .rsc scripts are applied with `/import`
50. User — <https://help.mikrotik.com/docs/spaces/ROS/pages/8978504/User> — `/user` property `password` (sensitive); Actions `password` ("Option to change user password"), `expire-password` — The Router Users section documents the settable password property and the password action; default user `admin` with group `full`
51. TR-069 — <https://help.mikrotik.com/docs/spaces/ROS/pages/9863195/TR-069> — `/tr069-client` `enabled`, `acs-url`, `username`, `password`, `periodic-inform-enabled`, `periodic-inform-interval` (tr069-client package) — Writable Settings document ACS URL, HTTP credentials and periodic inform (mapped to Device.ManagementServer.*); requires the tr069-client package
52. TR-069 — <https://help.mikrotik.com/docs/spaces/ROS/pages/9863195/TR-069> — Read-only `status` (disabled / waiting-URL / running), `last-session-error`, `retry-count`; command `reset-tr069-config` — Session state is readable; the page has no manual inform command and no connection-request username/password/port properties
53. TR-069 — <https://help.mikrotik.com/docs/spaces/ROS/pages/9863195/TR-069> — page scope: CWMP `/tr069-client` only — The TR-069 page and the Packages list contain no USP/TR-369 agent or controller settings
54. Software Specifications — <https://help.mikrotik.com/docs/spaces/ROS/pages/19136707/Software+Specifications> — Firewall: "NAT helpers (h323, pptp, quake3, sip, ftp, irc, tftp)" — The feature list has no VoIP/SIP account or registration feature; SIP is only a connection-tracking helper
55. Software Specifications — <https://help.mikrotik.com/docs/spaces/ROS/pages/19136707/Software+Specifications> — feature areas (Firewall, Routing, Wireless, DHCP, Hotspot, QoS, Tools, Other) — No analog-line (FXS) feature is listed anywhere
56. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — wifi package: `/interface/wifi/capsman/remote-cap print detail` `address`, `identity`, `board-name`, `serial`, `version`, `connected-time`, `uptime` — WiFi CAPsMAN lists managed CAPs with identity/model/version/uptime; it is a central AP controller, not an EasyMesh controller, and shows no backhaul topology
57. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — wifi package: Remote CAP property table — The remote-cap table has no link quality, rate or backhaul-type fields; CAPs attach over any IP/L2 path
58. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — wifi package Steering `wnm`, `neighbor-group`, `transition-threshold`, `transition-request-count`, `transition-time` — Clients can be nudged to neighbor-group APs by (unsolicited, 7.21+) 802.11v BSS-transition requests and optionally de-authenticated; there is no per-client "steer to agent X" command

## 11. Open questions

Carried from the charter and raised by the matrix; the design (stage 3)
answers each. Columns are named by their position in §2.

1. **Does ◐ count as support?** The evidence bar says "supported"; the matrix
   grades a caveated cell ◐. Counting ✓ only: 33 core candidates (R1, R2, R3,
   R4, R6, R8, R9, R11, R12, R13, R15, R16, R18, R22, R23, R24, R25, R26, R31,
   R32, R33, R34, R35, R40, R41, R42, R43, R45, R46, R48, R49, R50, R51); 9
   tier candidates on a majority without both triggers (R10, R14, R19, R21,
   R27, R28, R38, R39, R44); 16 below the majority (R5, R7, R17, R20, R29, R30,
   R36, R37, R47, R52, R53, R54, R55, R56, R57, R58). Counting ✓ and ◐ as
   support: 55 core candidates, 3 tier candidates (R53, R56, R57), 0 below
   (none); the rows that change category are R5, R7, R10, R14, R17, R19, R20,
   R21, R27, R28, R29, R30, R36, R37, R38, R39, R44, R47, R52, R54, R55, R58.
   Mesh (R56–R58), USP (R53), voice (R54–R55), zone defaults (R30), automatic
   port mapping (R36–R37) and provisioning mode (R7) all hinge on this reading.
2. **The WAN connection object's shape** (R1–R7, R9–R10): one object with a
   mode and mode-specific fields, or one object per mode; and whether link
   state (R8) stays on `port_status`.
3. **DHCP server placement** (R11–R14): extend `interface_dhcp`, extend the
   provisioner's `dhcp_server`, or a new gateway-side capability.
4. **Port forwards** (R31–R32): `firewall` (per-mapping, gateway tier) or
   `appliance_nat` (list-replacing); one shape for both archetypes.
5. **Host filtering** (R35): a new capability, or `packet_filter` rules with a
   schedule; all five columns publish both a per-host block and a schedule, in
   five different shapes (§2 R35).
6. **Remote management**: TR-069 configuration (R51) is ✓ on all five columns;
   the inform trigger (R52) is ◐ on every column (a session can be provoked,
   its connection-request state read nowhere), so `tr069_client.force_inform`
   needs a stated meaning or becomes a per-family unsupported case. USP (R53)
   is ◐ on columns 1, 3 and 4 (configured through the agent's own files, agent
   state undocumented) and ✗ on columns 2 and 5.
7. **Mesh and voice tiers** (D7): topology (R56) is ✓ on columns 1 and 4 and ◐
   on column 3; backhaul health (R57) is ◐ on columns 1, 3 and 4; steering
   (R58) is ✓ on column 1 and ◐ on columns 2, 3 and 5. Voice (R54–R55) has no
   column pair at ✓. Both tiers depend on question 1. `wifi_mesh` exists on
   `main` as the reuse candidate for R56–R58.
8. **`CpeDevice` supersession mechanics** (D6): the new class name, the
   `linux_cpe` deprecation row (kind `class`), the members the new class drops
   (`hw_console`, `ip_interface`, `ip_routing`, `conntrack`, host `nat`).
9. **Health reads** (R40): no column publishes a load average under that name;
   columns 1 and 3 publish a CPU-usage figure, column 2 the kernel load
   averages, column 5 a CPU-load figure, column 4 uptime only.
   `device_management.get_load_avg` needs a stated meaning.
10. **Source maintenance**: one column's documentation site carries a "frozen"
    banner pointing at a successor site; another's wiki renders client-side;
    one vendor's service documents carry wrong metadata titles; the charter's
    no-CLI knowledge-base citation now redirects. Stage 3 re-points what it can
    and records the rest (§10).
11. **Reference-image inclusion** (column 3): several ✓ cells rest on optional
    manager components whose presence on the reference build is not stated by
    the release page; stage 4 cites the build's component list or downgrades
    (§10, column 3 entries 1, 3, 5–8).
12. **Two CWMP clients on column 1**: the observed image ships one client (the
    substrate bus object of R52), the data-model site documents another; the
    driver's TR-069 route (substrate configuration or data model) is chosen at
    stage 4.

## Review record

- **2026-10-19 — chartered under the archetype track.** Request: issue #98
  (public). The reviewed-family list above is proposed for ratification by
  this charter's review. The OpenWrt trigger family is defined with its
  TR-069 client after the official feeds were found to carry none; USP and
  the other placements listed under Demand are left to the design.
- **2026-10-19 — maintainer's pre-review (local code review), before
  `/review`.** Eight findings applied: health is not an under-specification
  of `linux_cpe` (`device_management` carries uptime, load and memory; the
  request's I26 row corrected the same way); the LAN port-state reuse
  candidate is `port_status`, not `switch_ports` (I9 row corrected); the
  appliance's NAT member is `appliance_nat`; `ip_routing` is a fourth host
  lever; software lifecycle, configuration transfer, identity and health
  stated as demands both charters carry, not shared protocols (corrected in
  round 2); sources for every version line added; the evidence-bar
  paraphrase aligned with the README; one line wrapped. One finding
  rejected: `tr069_client` is a member of `CpeDevice` (`devices/cpe.py`).
- **2026-10-19 — charter review, round 1 (on 378007f): approve with
  conditions (C1–C2, N1–N3).** Applied: C1 the health claim corrected and
  `DeviceManagement` named as the reuse candidate for health and logs; C2 the
  four "not reviewed" families given a reason out each (ADTRAN SmartOS covered
  by the prplOS family; Zyxel, TP-Link and Calix without a published
  management plane); N1 the request's I26 and I27 cells corrected in #98 and
  in the PR body; N2 sources added for every version line; N3 OpenWrt stated
  as the 24.10 line, old-stable since 25.12, with a 25.12 revision allowed by
  dated note.
- **2026-10-19 — charter review, round 2 (on a97cde5): approve with
  conditions (C1, N1).** Applied: C1 the shared-demand sentence with the
  managed-router charter restricted to software image lifecycle and
  configuration transfer, identity and health stated as demands of this
  class only; N1 a public source for ADTRAN SmartOS on prplWrt added to the
  sources.
- **2026-10-19 — exploration (stage 2).** Matrix of 58 operations × 5 families
  sourced (§2, §10; 290 cells); 105 ◐ and ✗ cells listed as verification items
  (§9); reuse survey drafted (§5); twelve open questions (§11). Tally per
  column (✓/◐/✗): column 1 50/8/0; column 2 38/17/3; column 3 40/18/0; column 4
  21/24/13; column 5 36/17/5. Charter notes carried: the fourth excluded
  family's reason out now follows its source's wording; the pre-review entry
  above is restored to what the pre-review applied. The final review of the
  exploration (a fresh reviewer) re-graded R52 and R53 on column 1 to ◐,
  removed a symbol absent from `main` from §5, and neutralised §9, §11 and this
  entry.
