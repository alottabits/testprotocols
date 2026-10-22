# Design: vendor-neutral **CPE gateway** archetype

| Field | Value |
| --- | --- |
| Status | verified |
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
  https://fritz.com/en/apps/knowledge-base/FRITZ-Box-7490/1635_Access-to-the-FRITZ-Box-via-Telnet-is-not-supported/
  (Telnet unsupported since FRITZ!OS 6.25; re-pointed 2026-10-19 from the
  `en.fritz.com/service/knowledge-base/dok/...` path, which now redirects to
  a page that does not exist; the live page renders its text client-side,
  so the version statement is also cited from the archived copy
  http://web.archive.org/web/20221204193844/https://en.avm.de/service/knowledge-base/dok/FRITZ-Box-7490/1635_Access-to-the-FRITZ-Box-via-Telnet-is-not-supported/).
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
◐ and ✗ cell is a stage-4 verification item (§9); the cells stage 4 re-graded
(review record, stage 4b) carry the limit the reference driver found. The `Id` column is a
working id for the exploration and the review; the design decides whether
it stays.

| Id | Operation | prplOS 4.0 line | OpenWrt 24.10 line + icwmp | RDK-B 2025q4+ | FRITZ!OS 8.20+ | RouterOS v7 |
| --- | --- | :--: | :--: | :--: | :--: | :--: |
| | **WAN connection** |  |  |  |  |  |
| R1 | Set the WAN connection mode (DHCP, static, PPPoE, IPoE) | ✓ [1] | ✓ [1] | ✓ [1] | ◐ SetConnectionType only routed/bridged; no static/DHCP/IPoE selector [1] | ◐ no WAN-mode selector; add dhcp-client, pppoe-client or address object [1] |
| R2 | Read WAN connection state, address and lease | ✓ [2] | ✓ [2] | ✓ [2] | ◐ status, address, uptime, DNS; no lease-time field [2] | ✓ [2] |
| R3 | Set PPPoE credentials and service name | ✓ [3] | ✓ [3] | ◐ ppp-manager not in the reference build; the CcspPandM `PPP.Interface` parameters are written, their backend without ppp-manager unverified [3] | ◐ credentials only; PPPoEServiceName "Not supported, returns ''" [3] | ✓ [3] |
| R4 | Reset the PPPoE session | ✓ [4] | ✓ [4] | ◐ ppp-manager not in the reference build; without a PPPoE client the reset's status cycle cannot be observed [4] | ✓ [4] | ◐ no reset command; disable then enable the pppoe-client interface [4] |
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
| R15 | Configure DNS forwarder upstreams | ✓ [15] | ✓ [15] | ◐ the static name-server parameters are declared only under the data model's `BCI` or `_ONESTACK_PRODUCT_REQ_` build flag; whether the reference build sets either is unverified [15] | ✗ X_SetDNSServers "The action is not supported"; LAN GetDNSServer read-only [15] | ✓ [15] |
| R16 | Configure local host overrides | ✓ [16] | ✓ [16] | ◐ shell only: marked `/etc/hosts` lines and dnsmasq's SIGHUP, rewritten when the host file is regenerated; no data-model parameter [16] | ◐ only X_AVM-DE_SetHostNameByMACAddress; no arbitrary name/record override [16] | ✓ [16] |
| R17 | Configure DNS rebind protection | ✓ [17] | ✓ [17] | ◐ always on: hard-coded dnsmasq `--stop-dns-rebind`, not configurable [17] | ✗ no rebind-protection action in any listed TR-064 service [17] | ✗ no rebind or private-address answer filter on the DNS page [17] |
| R18 | Configure bridge membership (ports, wireless networks) | ✓ [18] | ✓ [18] | ✓ [18] | ✗ no bridge/port-membership action; LAN services configure IP and DHCP only [18] | ✓ [18] |
| R19 | Read bridge and port membership | ✓ [19] | ◐ UCI `ports` gives config; live membership via `bridge` shell [19] | ✓ [19] | ◐ per-host port/guest flag only; no bridge object [19] | ✓ [19] |
| R20 | Configure a guest segment | ✓ [20] | ✓ [20] | ◐ no guest object; composed from LanManagementEntry table + a dedicated SSID [20] | ◐ Wi-Fi guest AP via its own WLANConfiguration instance; no LAN guest-port action [20] | ◐ no guest object; composed from bridge VLAN, address, DHCP and firewall [20] |
| R21 | Read LAN port status (link, speed, duplex) | ✓ [21] | ◐ `link` documented; speed and duplex are the device status's `speed` field (`"1000F"`), source-only; no ethtool [21] | ✓ [21] | ◐ single LANEthernetInterfaceConfig instance; per-port only via host entries [21] | ✓ [21] |
| | **Wi-Fi access points** |  |  |  |  |  |
| R22 | Configure radio (band, channel, width, power, enable) | ✓ [22] | ✓ [22] | ◐ band fixed per radio: OperatingFrequencyBand is read-only; TransmitPower is a percentage with no dBm maximum [22] | ◐ channel and enable only (SetEnable/SetChannel); no channel-width, TX-power, country or DFS action [22] | ✓ [22] |
| R23 | Read radio state | ✓ [23] | ✓ [23] | ✓ [23] | ◐ enable, status, channel and band read; no transmit power, regulatory domain or DFS state [23] | ◐ wifi package: monitor fields undocumented; state via running/inactive flags [23] |
| R24 | Configure a BSS (SSID, security mode, passphrase, hidden) | ✓ [24] | ✓ [24] | ✓ [24] | ✓ [24] | ✓ [24] |
| R25 | Read BSS state | ✓ [25] | ✓ [25] | ✓ [25] | ✓ [25] | ◐ wifi package: print flags/detail only; no BSS monitor field table [25] |
| R26 | Read connected stations (signal, rate) | ✓ [26] | ✓ [26] | ✓ [26] | ✓ [26] | ✓ [26] |
| R27 | Disconnect a station | ✓ [27] | ◐ `del_client` only in hostapd ubus source, no wiki page [27] | ✓ [27] | ✗ no deauthenticate/disconnect-station action in WLANConfiguration [27] | ✓ [27] |
| R28 | Start / cancel push-button or PIN onboarding; read its state | ✓ [28] | ◐ PBC via `wps_pushbutton`/hostapd_cli; `wps_start`/`wps_status` source-only [28] | ✓ [28] | ◐ push-button only: start, stop and status; the PIN variables are obsolete [28] | ◐ wifi package: push-button start only; no cancel, state read or PIN [28] |
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
| R54 | Configure a SIP account; read registration state | ✗ the plugin's default branch publishes no parameter: LICENSE and a one-sentence README, no ODL [54] | ✗ Asterisk PBX config files + CLI; no operation a gateway voice member calls [54] | ◐ telco-voice-manager installed; the TR-104 v2 switch is misspelt in the platform layer, so the v2 model may not be the one built; MTA model is DOCSIS-eMTA only [54] | ✓ [54] | ✗ no SIP user agent; SIP appears only as a NAT helper [54] |
| R55 | Read FXS line state | ✗ no `POTS.FXS` object on the plugin's default branch [55] | ✗ asterisk-chan-lantiq Lantiq SoC FXS only; state via Asterisk CLI, no operation a gateway voice member calls [55] | ◐ same component caveat: voice manager installed, v2 model unverified; X_CISCO_COM_MTA.LineTable only on DOCSIS eMTA builds [55] | ◐ X_AVM-DE_GetPhonePort returns port name only; no hook/line state [55] | ✗ no FXS or telephony port in the feature list [55] |
| | **Mesh controller** |  |  |  |  |  |
| R56 | Read mesh topology (agents, backhaul links) | ✓ [56] | ✗ no EasyMesh controller; 802.11s is a peer mesh [56] | ◐ controller on the EasyMesh build variant (`FEATURE_TYPE=EasyMesh`); data-element paths in controller source only [56] | ✓ [56] | ◐ CAPsMAN, not EasyMesh; CAP list without backhaul links [56] |
| R57 | Read backhaul link health | ◐ Backhaul object gives link type/MACs; signal/rate only via parent BSS STA entry [57] | ✗ 802.11s peer links via `iw station dump`, not EasyMesh backhaul [57] | ◐ EasyMesh build variant; `MultiAPDevice.Backhaul.Stats` in controller source only [57] | ◐ link metrics present; no explicit backhaul flag (is_upstream is LAN-only) [57] | ✗ no backhaul-link metrics; remote-cap shows connected-time only [57] |
| R58 | Steer a client to another agent | ✓ [58] | ◐ usteer roams clients between plain APs; no EasyMesh agents [58] | ◐ EasyMesh build variant; `ClientSteer()` rbus method in controller source only [58] | ✗ no steering action; schema steering_enabled is a read-only flag [58] | ✗ no per-client steer command: Steering is properties only (802.11v requests to a neighbor group) [58] |

## 3. Decision

Add a vendor-neutral **`CpeGatewayDevice`** archetype (registered
`cpe_gateway`), **superseding** `CpeDevice` (`linux_cpe`). The new class
composes what a CPE gateway publishes on its management planes (§1): the WAN
connection as a managed object, the LAN services, the Wi-Fi access points, the
security posture, the host table, device operations and remote management by
an auto-configuration server. `CpeDevice` stays registered under `linux_cpe`,
intact and deprecated, for one MINOR release and six months (§6; the
maintainer's decision of 2026-10-19, review record): its one consumer keeps
passing the runtime `isinstance` gate while it moves (the extensions below
change its static conformance, as every `extend` does), and
the old shape is removed, not evolved, when the period ends.

The **core** is every operation of §2 that both trigger columns and a
majority of the five columns support, a caveated cell (◐) counting as
support with its limit becoming the member's documented per-column behaviour
or a per-method unsupported case (the maintainer's decision of 2026-10-19,
review record): 52 of the 58 operations, R1–R52; the six operations of the
tiers below meet the count on four of them as stage 4 graded them (R53 and
R56–R58; the two voice rows fell to two of five). It composes existing
capabilities wherever their shape holds (§5), and designs ten capabilities
no protocol on `main` owns, each argued on the placement ladder in §5 and
§6: `WanConnection`, `DnsForwarder`, `L2Bridge` (the `GAPS.md`
entry of 2026-05-02 whose trigger is this class), `HostTable`, `HostFilter`,
`AutoPortMapping`, `AdminCredential`, `DeviceHealth` (a read-only base split
off the host-shaped `DeviceManagement`, which inherits it) and, on the tiers,
`VoiceGateway` and `UspAgent`; nine land, and `VoiceGateway` is staged with
its tier (below). Six existing protocols are extended (rung 5):
`DeviceInfo` with the identity facts, `DeviceLifecycle` with the firmware
upgrade and configuration transfer, `Tr069Client` with the ACS configuration,
`NtpConfig` with the synchronisation state, `WifiOnboarding` with the cancel
and state read, and `DeviceManagement` with the one load read it gains
through the inherited health base. The identity, health, lifecycle and
configuration members are worded for any closed network product, not for
this class alone, so the chartered router sibling can compose them when its
design lands (the maintainer's decision of 2026-10-19, review record).

Three **optional tiers** are designed; two are built in this pass and the
third is `tier-staged`. Voice and the mesh controller are facets the charter
places "on many models", not on the class: a bridged modem or an operator
gateway without telephony publishes neither, so both are tiers whatever the
count says. The mesh count (three or four of five columns support each mesh
operation) meets the amended evidence bar, so the mesh tier is implemented and
tested like the core. The voice count was four of five at the exploration;
stage 4 found the nominal cells of columns 1 and 2 unsupported in substance,
so voice holds on two of five (columns 3 and 4) and is `tier-staged` (§6, the
nominal cells), its shape kept in this design for the trigger that reopens it.
USP is a tier because one trigger column publishes no agent (R53, column 2)
while three columns do. Each tier is a Protocol a driver satisfies in addition to
the core; §9 names the columns expected to implement each tier member and
the ones expected to raise. The cells that support a tier only nominally (a
stub plugin, a PBX from a package feed, controller source whose porting is
marked ongoing) are the design's stated risk, listed by id in §9: if stage 4
finds one of them unsupported in substance, the member becomes a per-column
unsupported case or the tier drops to `tier-staged`, and its manifest rows
are re-outcomed without reopening the design. Stage 4 settled them: voice
dropped to `tier-staged` (M3, M32), the mesh cells of column 3 held on the
controller's build variant (§9 Stated risks).

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
lacks, or maps with a stated loss (§8); of the three facets that fail the core
threshold or the class definition, the two built ones (mesh, USP) are
independent optional tier Protocols, so a driver satisfies any combination of
them, and the third (voice) is `tier-staged` (§6).

```python
@runtime_checkable
class CpeGatewayDevice(BaseDeviceProtocol, Protocol):
    """CPE gateway — universal core. Vendor-neutral; satisfiable by any
    gateway whose driver publishes the members below. The reviewed
    families and their evidence are in
    docs/architecture/cpe-gateway-protocol-design.md (§2, §10); the
    management transport and who manages the device are driver concerns."""

    wan_connection: WanConnection        # NEW — the WAN connection as a managed object: mode, credentials, tag, IPv6, state (§6)
    wan_admin: WanLinkAdmin              # reuse as-is — administrative down/up of the WAN by label (the twin's attribute name); module docstring generalised (§6)
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
    device_lifecycle: DeviceLifecycle    # EXTENDED — boot wait, factory reset, reboot as today; firmware upgrade, configuration export and import added; one member renamed (§6)
    admin_credential: AdminCredential    # NEW — the local administrator credential (§6)
    tr069_client: Tr069Client            # EXTENDED — connection state, identifier and inform as today, the inform's meaning stated; ACS configuration added (§6)
    wan_endpoint: NetworkEndpoint        # reuse — test-bed role object: the gateway's WAN-side address
    lan_endpoint: NetworkEndpoint        # reuse — test-bed role object: the gateway's LAN-side address

register_device_type("cpe_gateway", CpeGatewayDevice)
```

**Ten new capabilities designed, each argued in §5 and §6:** seven on the
core (`WanConnection`, `DnsForwarder`, `L2Bridge`, `HostTable`, `HostFilter`,
`AutoPortMapping`, `AdminCredential`), one split (`DeviceHealth`) and two on
tiers (`VoiceGateway`, `UspAgent`); nine land at seed, `VoiceGateway` staging
with its tier (M32). Every other member exists today; each
change to an existing one is placed on the ladder in §5 and listed in §12.
Where a disposition has a fallback, §6 states the condition that would move
to it.

Optional tier Protocols, each a strict `(CpeGatewayDevice, Protocol)`
superset adding one facet, built in this pass on the matrix evidence under
the amended evidence bar:

```python
@runtime_checkable
class CpeGatewayMeshTier(CpeGatewayDevice, Protocol):
    """Adds the mesh-controller facet: the agents and their backhaul links,
    client steering between agents. The extender is not a device of this
    archetype; it is an agent in the controller's topology (§1). Evidence:
    three or four of five columns per operation (R56–R58); the second
    trigger column publishes no controller and raises."""
    wifi_mesh: WifiMesh                  # reuse (+ one defaulted field on the topology node) — topology, backhaul, steering (§6)

@runtime_checkable
class CpeGatewayUspTier(CpeGatewayDevice, Protocol):
    """Adds the USP agent: the controller endpoint and its transport, the
    agent's own endpoint identifier. Evidence: three of five columns (R53,
    all caveated); the second trigger column packages no agent and raises."""
    usp_agent: UspAgent                  # NEW (tier) — controller endpoint and transport, the agent's endpoint identifier (§6)
```

The voice tier is `tier-staged` (M3, M32): stage 4 found R54–R55 supported
on columns 3 and 4 only, two of five. Its shape stays recorded for the
trigger that reopens it (a third column supporting the SIP account (R54) beside columns 3 and 4, the majority of five, or a
consumer): `CpeGatewayVoiceTier(CpeGatewayDevice, Protocol)` adding `voice:
VoiceGateway` (§6), unregistered like the two built tiers.

The tiers are not registered: one registry key, `cpe_gateway`, names the
class, and a test that needs a facet pins against the tier Protocol with
`isinstance`, exactly as the white-box tests pin against an extension (§7).
Three of the five columns satisfy both built tiers, so a key per facet would
name the minority case and a combined key the power set; the structural
check already answers "does this driver publish a mesh controller" without
either.

**Concerns, dispositions and evidence.** One row per concern of §1; the
X-vendor column gives the count of the concern's weakest matrix row as
`✓ + ◐ + ✗` over the five columns, the ◐ cells counting as support;
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
| Onboarding: start, cancel, state | `WifiOnboarding` | **extend** | 2 + 3 ◐ | R28; cancel and state read added; columns 4 and 5 push-button only |
| Band steering, 11k/v/r | `WifiTransitions` | reuse | 2 + 2 ◐ + 1 ✗ | R29; band steering by composition of the 11v members (§6) |
| Zone defaults and membership | `FirewallZones` | reuse | 1 + 3 ◐ + 1 ✗ | R30; four columns have no zone object: mapped or per-method unsupported (§6) |
| Port forwards, DMZ host | `Firewall` | reuse | 4 + 1 ◐ | R31–R32; column 4 forwards to the calling host only |
| Egress filter rules | `Firewall` (the inherited rule members) | reuse | 3 + 1 ◐ + 1 ✗ | R33–R34; column 4 publishes profiles, not rules |
| Host block with schedule | `HostFilter` | **new** | 5 | R35 |
| Automatic port mapping | `AutoPortMapping` | **new** | 1 + 4 ◐ | R36–R37; PCP absent on three columns, per-protocol unsupported |
| Host table | `HostTable` | **new** | 3 + 2 ◐ | R38; two columns join leases, neighbours and station lists |
| Identity | `DeviceInfo` | **extend** | 4 + 1 ◐ | R39; manufacturer, serial number, OUI, hardware and software version added (generic introduction); column 2 publishes neither manufacturer nor serial (§9 Stated risks) |
| Health: uptime, load, memory, processes, logs | `DeviceHealth` | **new (split)** | 3 + 1 ◐ + 1 ✗ | R40–R42; weakest R41 (column 4 has no process list); the base `DeviceManagement` inherits (generic introduction, §6) |
| Log export | `SyslogConfig` | reuse | 4 + 1 ✗ | R43; column 4 raises |
| Time: servers, synchronisation state | `NtpConfig` | **extend** | 3 + 2 ◐ | R44; sync-state read added; raises on columns 2 and 4 (§9 Stated risks) |
| Firmware upgrade | `DeviceLifecycle` | **extend** | 5 | R45; one upgrade member added (generic introduction); a staged pair is `tier-staged` (§6) |
| Factory reset; reboot and readiness | `DeviceLifecycle` | reuse | 1 + 4 ◐ | R46–R47; readiness is the boot wait on uptime or reachability on four columns |
| Configuration export and import | `DeviceLifecycle` | **extend** | 4 + 1 ◐ | R48–R49 (generic introduction); column 3 through the shell store |
| Local administrator credential | `AdminCredential` | **new** | 5 | R50 |
| ACS configuration, inform, connection-request state | `Tr069Client` | **extend** | 0 + 5 ◐ | R51 (5 ✓) and R52 (5 ◐): ACS configuration added; the inform's meaning stated, the connection-request state read nowhere (§6) |
| USP controller endpoint, transport, agent state | `UspAgent` | **new (tier)** | 0 + 3 ◐ + 2 ✗ | R53; column 2 packages no agent: tier `usp` |
| Voice: SIP accounts, registration, FXS lines | `VoiceGateway` | **new (tier)**, `tier-staged` | 0 + 2 ◐ + 3 ✗ | R54–R55; the class definition makes it a tier; columns 1, 2 and 5 ✗ at stage 4, two of five: staged (§6) |
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
placement-ladder argument per operation is stage 3 (the ladder table
below supersedes the Fit column). "generic" marks the operations this pass
introduces as generic capabilities worded for any closed network product.

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
| R11 | Configure the DHCP server pool and lease time | `interface_dhcp` (InterfaceDhcp) or `dhcp_server` (provisioner) | as-is + field | set_interface_dhcp is per interface with pool and lease time; the provisioner's `provision_cpe` is test-bed shaped |
| R12 | Configure DHCP options | `interface_dhcp` | as-is | `InterfaceDhcpConfig.options` (a list of `DhcpOption`) already exists; the survey first read it as missing |
| R13 | Configure static leases | `interface_dhcp` | as-is | `InterfaceDhcpConfig.reservations` (a list of `DhcpReservation`) already exists |
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
| R39 | Read identity (manufacturer, model, serial, OUI, software version) | `device_info` (DeviceInfo) | extend | only `model` today; manufacturer, serial, OUI, software version are new fields (generic: introduce here) |
| R40 | Read uptime, load, memory | `device_management` | as-is | get_seconds_uptime, get_load_avg, read_memory_utilization (generic: health split decided by the design) |
| R41 | Read process state | `device_management.read_running_processes` | as-is |  |
| R42 | Read device logs | `device_management.read_log_entries` | as-is |  |
| R43 | Configure log export | `syslog_config` | as-is | set_syslog_servers/get_syslog_servers (generic) |
| R44 | Configure NTP servers; read sync state | `ntp_config` + `ntp_client` | extend | set/get_ntp_servers exist; neither carries a sync-state read |
| R45 | Upgrade firmware from an image | `device_lifecycle` | extend | no upgrade member today (generic: introduce here) |
| R46 | Factory reset | `device_lifecycle.factory_reset` | as-is |  |
| R47 | Reboot; read readiness | `device_lifecycle.reset` + `wait_for_boot` | as-is | readiness = wait_for_boot; `verify_cpe_is_booting` carries a class name in a method (rename candidate) |
| R48 | Export configuration | new or `device_lifecycle` extend (configuration transfer) | extend | generic: introduce here; export |
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

### Placement on the ladder

Every operation group of §2, on the lowest rung of the placement ladder
(`docs/proposals/README.md`, "The placement ladder") that fits, with the
reason no cheaper rung does for every item above rung 2. The Mechanism value
is the one its §12 rows carry. A `new capability` row carries the "rung 5
before rung 6" argument: no existing protocol owns the concern, or extending
one would leave an archetype that composes it permanently unsupported.

| Operations | Capability | Rung | Mechanism | Why no cheaper rung |
| --- | --- | :--: | --- | --- |
| R1–R7, R9 (as a member's label) | `WanConnection` | 6 | new capability | no protocol carries a WAN connection with a mode: `wan_link_admin` is the down/up lever only, `ip_interface` is a host's netdev, `appliance_uplinks` is the appliance's read-only uplink status (an `extend` of it with a mode and credentials would leave every appliance driver permanently unsupported on the writes), `dhcp_client` is the lease lever; the connection object is a concern of its own |
| R8, R21 | `PortStatus` | 2 | reuse | link, speed and duplex per port, unchanged |
| R9 | `WanLinkAdmin` | 2 | reuse | `bring_wan_down` / `bring_wan_up` by label match, `get_wan_state` the paired read on this class; the module docstring, which calls the lever twin-only, is generalised at stage 4 (a `record` row in SPLITS) because four of five columns publish it |
| R10 | `DhcpClient` | 2 | reuse | release and renew, v4 and v6 |
| R11–R14 | `InterfaceDhcp` | 3 | defaulted field | `InterfaceDhcpConfig` already carries the mode, lease time, options, reservations and reserved ranges, and `get_dhcp_leases` reads the leases; the pool's first and last address are two defaulted fields (§6), `None` meaning the whole subnet minus the reserved ranges, which is the appliance's shape today |
| R15–R17 | `DnsForwarder` | 6 | new capability | no protocol owns a forwarder: `dns_client` is a host's resolver (`extend` would put server-side settings on every LAN client); the three operations are one concern |
| R18–R19 | `L2Bridge` | 6 | new capability | the `GAPS.md` 2026-05-02 entry, whose trigger is this class; `switch_ports` / `switch_vlans` are the switchport shape the switch designs kept apart from the bridge-native one; imports the shared STP vocabulary from `models/l2_common.py` |
| R20 | composition | 1 | driver-only | a guest segment is the four capabilities with their own membership (§6) |
| R22–R23 | `WifiRadio` | 2 | reuse | radios addressed by band; no setter added (§6) |
| R24–R25 | `WifiBss` | 2 | reuse | unchanged |
| R26–R27 | `WifiStations` | 2 | reuse | `disconnect_station` is the disconnect |
| R28 | `WifiOnboarding` | 5 | extend | the protocol owns onboarding and has the triggers; cancel and the state read are two members on the same concern, so rung 3 (a field) cannot carry them and rung 6 would split one concern over two protocols |
| R29 | `WifiTransitions` | 2 | reuse | 11k/v/r setters; band steering composed from the 11v members (§6) |
| R30 | `FirewallZones` | 2 | reuse | zone defaults and membership; per-method unsupported on four columns |
| R31–R34 | `Firewall` | 2 | reuse | port mappings and DMZ, plus the inherited `PacketFilter` rule members for the egress rules |
| R35 | `HostFilter` | 6 | new capability | a schedule field on `FirewallRule` (rung 3) would be unusable by every host-side `PacketFilter` driver and `None` for every existing rule; `content_filtering` is URL-based; the per-host block with a schedule is a concern of its own |
| R36–R37 | `AutoPortMapping` | 6 | new capability | `upnp_client` is the LAN client's lever to request a mapping, not the gateway's enable and table; `firewall`'s mappings are the administrator's, not the automatic ones (origin and lease differ); the enable and the table are one concern |
| R38 | `HostTable` | 6 | new capability | no archetype reads a host table; `arp_client` is a host lever; `wifi_stations` covers wireless only and `interface_dhcp` leases only — the joined table is the concern |
| R39 | `DeviceInfo` | 5 | extend | the protocol owns identity and nominates the extension point in its docstring; a Protocol property cannot default (rung 3); the appliance and the switches publish the facts, so no archetype is left permanently unsupported |
| R40–R42 | `DeviceHealth` | 6 | new capability (split) | the `GAPS.md` 2026-06-11 record forbids composing the host-shaped `DeviceManagement` on a closed product; a split base that `DeviceManagement` inherits (the `Router` → `RoutingRead` precedent) leaves its implementers satisfying both; `read_cpu_load` is an `extend` of the base's inheritor |
| R43 | `SyslogConfig` | 2 | reuse | unchanged |
| R44 | `NtpConfig` | 5 | extend | the protocol owns the server list; the synchronisation state is the read beside it; a family that publishes no state raises the documented per-method case, so no archetype is left permanently unsupported |
| R45, R48–R49 | `DeviceLifecycle` | 5 | extend | the protocol owns the device's lifecycle (boot, reset, factory reset); image upgrade and configuration transfer are its concern; composed by the superseded class only, so no other archetype is affected; the docstring generalised from CPE to any device |
| R46–R47 | `DeviceLifecycle` | 2 | reuse | `factory_reset`, `reset`, `wait_for_boot` unchanged; `verify_cpe_is_booting` renamed (`deprecate`, lands with the extend) |
| R50 | `AdminCredential` | 6 | new capability | no protocol owns a local credential; `radius_client` is a server registry and an `extend` of it would put a local-account write on every AAA-client implementer |
| R51–R52 | `Tr069Client` | 5 | extend | the protocol owns the ACS relationship and has the connection state, identifier and inform; the ACS configuration is two members on the same concern; composed by the superseded class only |
| R53 | `UspAgent` | 6 | new capability (tier) | USP is a second management protocol with its own endpoint and transport, not a TR-069 field: an `extend` of `Tr069Client` would mix two protocols' lifecycles on one member set and leave the two columns without an agent permanently unsupported on the core |
| R54–R55 | `VoiceGateway` | 6 | new capability (tier) | `sip_phone` and `sip_server` are the test-bed far ends; no protocol owns the gateway's own accounts and lines; `tier-staged` at stage 4 (two of five, §6) |
| R56–R58 | `WifiMesh` | 3 | defaulted field | `get_topology`, `get_mesh_status`, `steer_client` unchanged; `WifiMeshNode.backhaul_link: WifiMeshLink | None = None` carries each agent's backhaul health |
| class | `CpeGatewayDevice`, three tier Protocols | — | archetype | the archetype and its tiers (§4); two built, the voice tier staged |
| class | `CpeDevice` | 5 | deprecate | superseded, intact under `linux_cpe` for the period (§6) |

### Shared with the appliance

Read against `SdwanApplianceDevice`'s members, the gateway shares by reuse of
the same capability protocols, never by one archetype extending the other
(§1). The appliance's shapes that the gateway does not take are recorded
with the reason, so the two designs do not drift into near-duplicates.

| Concern | Appliance member | Gateway member | How |
| --- | --- | --- | --- |
| Identity | `info: DeviceInfo` | `info: DeviceInfo` | the same protocol; the gateway's five identity properties are an `extend` the appliance's drivers implement too (§6) |
| Log export | `syslog: SyslogConfig` | `syslog: SyslogConfig` | reuse as-is |
| NAT | `appliance_nat: ApplianceNat` (list-replacing `NatRule` tables) | `firewall: Firewall` (per-mapping `PortMapping`) | two shapes for two device classes; a gateway publishes one mapping at a time and no column needs a table replace; recorded in SPLITS (§12) |
| WAN uplink status | `uplinks: ApplianceUplinks` (read-only `UplinkStatus`) | `wan_connection: WanConnection` (configured object with state) | the appliance's uplink is a controller fact read back; the gateway's connection is written on the box with credentials and a tag; the read records overlap on address and state only |
| WAN admin | — (the appliance cannot) | `wan_admin: WanLinkAdmin` | the twin's lever, published by four gateway columns (§6) |
| LAN | `lan: ApplianceVlans` | `l2_bridge` + `interface_dhcp` | the appliance's VLAN object is the switchport shape; the gateway's LAN is a bridge of ports and networks with a DHCP pool |
| Edge firewall, zones | `l3_firewall: L3Firewall` | `firewall_zones`, `firewall` | the appliance's triad is a controller-side rule set; the gateway's is a zone model plus per-rule administration, already modelled for the superseded class |
| Health | (`GAPS.md` 2026-06-11, deferred) | `health: DeviceHealth` | the read-only base this design seeds takes that entry's concern with two differences its update records (M17): `get_seconds_uptime` returns `float`, not the sketch's `float \| None`, so an appliance that reports no uptime raises the documented unsupported case, and the base carries the process-list read the sketch lacks; the appliance composes it when its trigger lands |

### Shared with the switches

| Concern | Switch member | Gateway member | How |
| --- | --- | --- | --- |
| Per-interface DHCP | `interface_dhcp: InterfaceDhcp` | `interface_dhcp: InterfaceDhcp` | reuse as-is, over the same sub-models |
| Port state | `port_status: PortStatus` | `port_status: PortStatus` | reuse as-is |
| Time | `ntp: NtpConfig` | `ntp: NtpConfig` | the same protocol; the sync-state read is an `extend` the switch drivers implement too (§6) |
| Identity, log export | `info`, `syslog` | `info`, `syslog` | as with the appliance |
| LAN ports | `switch_ports`, `switch_vlans`, `spanning_tree`, `mac_table` | `l2_bridge: L2Bridge` | the switchport shape versus the bridge-native shape, kept apart by the 2026-06-14 switch designs; the shared STP and FDB vocabulary (`StpMode`, `StpPortState`, `MacTableEntry`) is imported from `models/l2_common.py`, not re-invented |

### Shared with the chartered router sibling

The sibling is chartered, not designed on `main`; this table records
operations as demand, not symbols, so that the two designs can record the
dependency on each other's rows when the sibling's design lands.

| Demand (both charters) | This design's home | The sibling's design |
| --- | --- | --- |
| Software image lifecycle | `DeviceLifecycle.upgrade_firmware` (one action; §6) | composes the extended protocol, or adds staging by a further `extend` on dual-image evidence |
| Configuration transfer | `DeviceLifecycle.export_configuration` / `import_configuration` | composes the same members |
| Identity | `DeviceInfo` (+ five properties) | composes the extended protocol |
| Health reads | `DeviceHealth` | composes the base, which its charter lists as demand under a different grouping |
| Log export, time | `SyslogConfig`, `NtpConfig` (+ sync state) | reuse |
| On-box reachability | not on this core (no matrix row; §3) | its charter's demand; its own evidence |
| Operator authentication, routing, first-hop redundancy, QoS, capture | not published by a gateway (§1) | its own |
| WAN connection with credentials, Wi-Fi, host table, ACS management, voice lines, mesh controller | this design | not published by a router core (§1) |

### Boundary with the superseded shape

Each row names a member `CpeDevice` has and what `CpeGatewayDevice` offers
instead; the old class keeps every member for the period (§6).

| `CpeDevice` member | `CpeGatewayDevice` | Why |
| --- | --- | --- |
| `tr069_client`, `device_lifecycle`, `wifi_radio`, `wifi_bss`, `wifi_stations`, `wifi_transitions`, `wifi_onboarding`, `firewall`, `firewall_zones`, `wan_endpoint`, `lan_endpoint` | the same members (three of the protocols extended) | the matrix operations hold on all five columns; the members of these protocols without a matrix row are verification items (§9) |
| `device_management: DeviceManagement` | `health: DeviceHealth` | the host-shaped members (file content, board and boot-time logs) are not published by a closed product; the read-only base is (§6) |
| `ntp_client: NtpClient` | `ntp: NtpConfig` (+ sync state) | a host's clock lever versus the device's server list |
| `hw_console: HwConsole` | — | a test-bed attachment, not a published operation; several columns have no console |
| `ip_interface`, `ip_routing`, `conntrack`, `nat` | — (`firewall` carries the port-forward table) | host-substrate levers of the Linux twin; no column publishes them as operations |
| `wifi_rf: WifiRf` | — | no matrix row; a dated row brings it back |
| `network_probe: NetworkProbe` | — | no matrix row; reachability is observed from the test-bed hosts (`await_reachability`) |
| — | `wan_connection`, `wan_admin`, `dhcp_client`, `port_status`, `interface_dhcp`, `dns_forwarder`, `l2_bridge`, `host_filter`, `auto_port_mapping`, `hosts`, `info`, `syslog`, `admin_credential` | the under-specification the charter names (§1), closed from the matrix |

## 6. Modelling decisions

Each decision is stated with the condition that would overturn it. Columns
are named by their position in §2. New symbols live in the module named in
§12; new records live in `models/cpe_gateway.py` unless a row says
otherwise. Every write below promises the family's **acknowledgement** of
the write, never the resulting state: the call returns when the family
accepted the write and raises the rejection error when it refused; the
paired read is how a test confirms the state (track README, "Write outcome").

### The WAN connection — one object, a mode, mode-specific fields

**Decision.** One capability, `WanConnection` (`wan_connection`), models the
connection the charter describes (§1): a `WanConnectionConfig` record with a
`name` (the handle `wan_admin` also takes as its label), `mode: WanMode`
(`DHCP`, `STATIC`, `PPPOE`; IPoE is `DHCP` or `STATIC` with the `vlan` part
set, so it is not a fourth value), and the mode-specific parts as optional
records — `pppoe: PppoeCredentials | None` (`username`, `password: str | None`
— required on a write, `None` on every read because no column returns a stored
secret — `service_name: str | None`), `static: StaticAddressing | None`
(`address: str`, `prefix_length: int`, `gateway: str`, all required, and
`dns_servers: tuple[str, ...]`, the resolvers the connection supplies in place
of a lease's — empty when the forwarder's own upstreams are to serve; the DNS
forwarder decision states the boundary), `vlan: WanVlan | None` (`vlan_id`,
`priority: int | None`) and `ipv6: WanIpv6 | None` (`mode: WanIpv6Mode` —
`DISABLED`, `DHCPV6_PD`, `SLAAC`, `STATIC` — `requested_prefix_length: int |
None`, `static_address: str | None`). A part that does not apply to the mode is
`None` and the driver rejects a configuration whose parts contradict its mode
before touching the device. The state is a separate read record,
`WanConnectionState`: `status: WanStatus` (the TR-181 connection-status set:
`UNCONFIGURED`, `CONNECTING`, `AUTHENTICATING`, `CONNECTED`, `DISCONNECTING`,
`DISCONNECTED`; CLI families map their words onto it), `ipv4_address: str |
None`, `ipv4_gateway: str | None`, `dns_servers: tuple[str, ...]` (the
resolvers the connection supplies), `lease_remaining_s: int | None` (None where
the family publishes no lease time, column 4), `ipv6_address: str | None`,
`delegated_prefix: str | None` — each address `None`, and the tuple empty,
while its address family is not provisioned or the status is anything but
`CONNECTED` —, `provisioning_mode: ProvisioningMode | None` (`IPV4`, `IPV6`,
`DUAL_STACK`; derived from the v4 and v6 states on columns 2, 4 and 5, which
publish no mode field, and `None` only while neither family of addresses is up)
and `uptime_s: int | None`. Members: `set_wan_connection(config) -> None`,
`get_wan_connection(name) -> WanConnectionConfig`, `list_wan_connections() ->
list[WanConnectionConfig]`, `get_wan_state(name) -> WanConnectionState`,
`reset_session(name) -> None`. The reset is the PPPoE session reset R4
evidences: on a `PPPOE` connection the session is terminated and redialled, and
its confirming observation is `get_wan_state` showing the status leave
`CONNECTED` and return, through `await_reachability` from a LAN client. On a
`DHCP` or `STATIC` connection it raises the documented unsupported case, and
its docstring points at the released levers that already do that work:
`dhcp_client`'s release and renew (R10) for the lease and `wan_admin`'s down
and up (R9) for the administrative state, with `get_wan_state` as their paired
read on this class; the connection record carries no `enabled` field, so one
lever encodes the administrative state once. The link beneath the connection
stays on `port_status` (R8): link state is a port fact, published that way by
all five columns. The written PPPoE password is confirmed by the session:
`WanStatus.CONNECTED` after `AUTHENTICATING`.

**Per-column limits, as docstring normalisations.** Column 4 publishes no
mode selector beyond routed/bridged, no service name and no tag: a
`WanConnectionConfig` with `mode` other than the connection's existing one,
a `service_name`, or a `vlan` is rejected by the driver with the
unsupported case before any write. Column 5 has no mode selector either:
the driver realises the mode as the family's client or address object and
the read reports the mode from which object exists. Column 1 and column 3
realise the whole record; column 2 realises the priority only through a
mapping the family does not document (R5 ◐), so a `priority` is the
unsupported case there until stage 4 sources it.

**Multi-step write.** `set_wan_connection` is several device steps on every
column but the fourth: one set per parameter on columns 1 and 3 (column 3 with
an apply step for some objects), interface, protocol, credential and tag
objects on columns 2 and 5. A rejection at any step raises naming the step and
the driver writes nothing more; the family's own mechanism decides whether the
as-found state returns (column 2 stages every step under a change-file path
unique to the driver's session and fresh per write, and commits only when every
step is accepted, so a rejected
write's steps are never committed; columns 1, 3 and 5 apply each step, so the
steps before the rejection stand) — stated per column in §8 and in the drivers'
`lossy:` lines.

**Not modelled.** An IPv4-over-IPv6 transition (DS-Lite), which columns 1
and 4 publish as a status, has no matrix row and no field; a dated row adds
it as a `WanIpv6` part.

**Overturn.** A trigger column that cannot represent the `WanMode` set
(none in §2), or a second connection shape (a bridged WAN) that a consumer
needs, which would add a mode rather than a second object.

### DHCP server — `interface_dhcp` as-is

**Decision.** The gateway's DHCP server is `InterfaceDhcp`: its
`InterfaceDhcpConfig` already carries the mode and lease time, `options`,
`reservations` (static leases) and `reserved_ranges`, and `get_dhcp_leases`
reads the active leases. The pool's bounds are two defaulted fields (rung
3), `pool_start: str | None = None` and `pool_end: str | None = None`:
`None` means the whole interface subnet minus the reserved ranges, which is
what the appliance's and the switches' drivers serve today, so no consumer
changes; every gateway column publishes the pool as a first and last address
(R11) and its driver fills both. Every reserved range must lie inside the
bounds: a range inside them is subtracted from the pool, and a configuration
whose reserved range lies wholly or partly outside its bounds is rejected by
the driver before any write (with `None` bounds nothing is outside, so no
consumer's configuration changes meaning). The gateway composes it per LAN
interface (the
bridge, the guest bridge) exactly as the switches do per SVI. The
provisioner's `dhcp_server` is a test-bed server for the device under test,
not the device's own, and stays where it is. Column 4 publishes the pool but
no lease-time or reservation write (R11 ◐, R13 ✗): its driver rejects a
`lease_seconds` other than the device's and any `reservations` with the
unsupported case before writing. Column 2's active-lease read joins a lease
file with a bus method (R14 ◐): a mapping with a `source:` line, not a
limit. `set_interface_dhcp` is a whole-interface replace on every column; a
rejection raises naming the step and the family's own mechanism decides the
as-found question (§8).

**Overturn.** A field the gateway needs that the appliance and the switches
cannot default, which would make the gateway's DHCP server a new capability
rather than two more defaulted fields.

### Port forwards — the per-mapping `firewall` shape

**Decision.** Port forwards are `Firewall.add_port_mapping` /
`remove_port_mapping` / `list_port_mappings` / `get_port_mapping` /
`set_port_mapping_enabled` over `PortMapping`, and the DMZ host is
`set_dmz_host` / `get_dmz_host`: the gateway-tier, per-mapping shape the
superseded class already composed. `appliance_nat` (list-replacing
`NatRule` tables) stays the appliance's shape; the two coexist for different
device classes and the shared-with table (§5) records both. Column 4 adds a
mapping for the calling host only (R31 ◐): `internal_host` other than the
driver's own address is the unsupported case there. Because `Firewall`
inherits `PacketFilter`, the same member also carries the egress rules
(R33–R34): `add_rule` on the forward chain with `src_cidr` the LAN host and
`dst_cidr` / `dst_ports` the destination. Column 3 matches no destination
address (R33 ◐: a rule with `dst_cidr` other than any is the unsupported
case); column 4 publishes profiles, not rules (R33 ✗: the rule writes raise;
R34 ◐: `list_rules` and `get_rule` read the filter profiles as forward-chain
rules named after the profile, allow for the standard and unrestricted
profiles, deny otherwise). Stage 4 found the chain models per column: column
1's firewall is level- and policy-based with forward chains only — the
forward chain maps to the outbound custom chain, the input and output chains
are per-value refusals on every chain member, the default policy is the
custom level's one policy, and rules take effect while the custom level is
active; column 3 is forward-only too (the internet-access policy table, no
default policy, a hit log rather than counters). Per inherited chain member
as built: `flush_chain` maps on columns 1, 2 and 3, `set_default_policy` /
`get_default_policy` on columns 1 and 2, the counter pair on column 2 only;
each raises elsewhere. Column 5 keeps per-rule counters, but their fields are
undocumented, so its counter members raise too (§8).

**Overturn.** A column that cannot add one mapping without rewriting the
table (none in §2), which would make the list-replacing shape the honest
one.

### Host filtering — a new capability with a schedule

**Decision.** `HostFilter` (`host_filter`) owns the per-host block: a
`HostBlock` record (`mac: str`, `schedule: WeeklySchedule | None`, `enabled:
bool = True`) with `WeeklySchedule(days: frozenset[Weekday], start: time, end:
time)` and `Weekday` an `IntEnum` Monday to Sunday; members `block_host(block)
-> None`, `unblock_host(mac) -> None`, `get_host_block(mac) -> HostBlock`,
`list_host_blocks() -> list[HostBlock]`. It is not a `packet_filter` rule
because `FirewallRule` carries no schedule and the five columns publish the
block in five shapes (a per-host access flag with a time profile, a schedule
object bound to a rule, a parental control entry, a time-budget profile, a
scheduler script): a schedule field on `FirewallRule` would be `None` for every
rule consumer today and would make every host-side `PacketFilter` driver carry
a field it cannot honour. The block is by MAC because that is what every column
keys on; an address-keyed block is not offered. It is not `WifiBss`'s
per-network MAC access list either: that list admits or refuses a station's
association on one network, while a host block denies a host's traffic through
the gateway, wired or wireless, on a schedule. On column 4 a block is one
action and an unblock two (the host back on the standard profile, then its
disallow cleared); on column 5 a new block is two requests (the profile, then
the device entry) and an unblock two deletes; on both, the steps before a
rejection stand, as the drivers' `lossy:` lines say. On column 1 it is the host
access-control entry (the hosts plugin's access-control object, not a firewall
rule), one set per parameter and
one add per schedule window; on column 2 a rule plus a schedule section; on
column 3 an internet-access policy, one set per parameter; a rejection raises
naming the step. The device resource is shared with `firewall` on columns 2
and 3: on column 2 the realised block is a firewall rule, so
`firewall.list_rules` shows it too, named after the host so a reader can tell
the two apart; on column 3 the block is a policy in the same internet-access
table that `firewall` writes its rules to, and the `firewall` driver keeps the
host-block policies out of `list_rules` and `flush_chain` by their name. The
block has one owner, `host_filter`: on column 2 the `firewall` driver refuses
`remove_rule` on a rule that realises a host block, and `flush_chain` and
`set_default_policy` on the chain that holds one, with `NotSupportedError`
naming the owner; on column 3 it never sees one. So no `firewall` write
disturbs a block. Column 1's access-control object is `firewall`'s concern on
no column. The `mac` of
`HostBlock`, and the argument of `unblock_host` and `get_host_block`, is the
canonical lowercase colon-separated form `WifiMeshNode.mac` already uses: the
driver canonicalises every MAC it reads (columns 3 and 5 upper-case theirs) and
accepts any case on a write, normalising before the device sees it, so what a
test reads back equals what it wrote.

**Overturn.** A schedule field acceptable on `packet_filter` rules for all
its consumers (the hosts, the twin, the superseded class), which would move
this to a `defaulted field` row.

### Remote management — the ACS configuration, the inform's meaning, USP

**Decision.** `Tr069Client` is extended with `set_acs(config: AcsConfig) ->
None` and `get_acs() -> AcsConfig`, where `AcsConfig` carries `enabled: bool`, `url`,
`username: str | None`, `password: str | None`, `periodic_inform_enabled:
bool`, `periodic_inform_interval_s: int`, `connection_request_username: str
| None` and `connection_request_password: str | None` — the parameter set
the five columns publish (R51, five ✓). The two passwords are required on a
write when the ACS authenticates and `None` on every read: no column returns a
stored secret (the data-model columns return an empty string, the CLI column
marks the field sensitive), and the written value is confirmed by the session —
`is_tr069_connected` after the next inform — not by a read. On column 4
`set_acs` is several SOAP actions (one per parameter group); a rejection raises
naming the action. `force_inform` keeps its name and gains the stated meaning:
*provoke an inform session where the family publishes a trigger (columns 1 and
2, through the client's own interface); raise the unsupported case where it
publishes none (columns 3, 4 and 5)*, with `is_tr069_connected` as its
confirming observation and the test-bed ACS as the far-end witness. The
rewritten docstring names no vendor command or daemon; the released text's
example moves to the column-1 driver's `source:` line. The member stays on the
core because the operation it belongs to (R52) is supported on every column in
part; the trigger half is a per-method unsupported case on three of five,
stated here and in §9. The connection-request state is read by no column (R52,
five ◐): no member is added for it, and the row's second half is a verification
item that may become a `feat:` change when a column publishes it. The `get_id`
identifier and `get_tr069_log` stay as they are.

USP is the `usp` tier: `UspAgent` (`usp_agent`) with `set_controller(
controller: UspController) -> None`, `get_controller() -> UspController` and
`get_agent_state() -> UspAgentState`. `UspController` carries `endpoint_id:
str` (the controller's endpoint identifier), `transport: UspTransport`
(`WEBSOCKET`, `MQTT`, `STOMP`; the CoAP transport is omitted because no
column's agent documentation lists it, and joins by a dated note), `host: str`,
`port: int`, `path: str | None` (the WebSocket resource path; `None` on the
other transports, which have none) and `tls: bool`; `UspAgentState` carries the
agent's `endpoint_id`. The design offered a `connected: bool | None` beside it,
to be dropped if no family published a connection state by stage 4: none does
(columns 1, 3 and 4 read the configuration only, R53 ◐), so the field was
dropped before landing and a column that publishes the state adds it by a
`feat:` change. Columns 1 and 3 configure
the agent through its own files rather than a data-model object: a mapping with
a `source:` line, not a limit. Column 2 packages no agent and column 5 has
none: both raise, and both drivers satisfy the core without the tier.

**Overturn.** A trigger column that publishes no TR-069 configuration (none
in §2) would move TR-069 to a tier; a column publishing the connection-request
state would add the read as a `feat:` change, not reopen the design.

### Mesh and voice — tiers, with the nominal cells named

**Decision.** The mesh controller is the `mesh` tier and reuses `WifiMesh`
unchanged in its members: `get_topology` (R56), `get_mesh_status` and
`get_topology` for the backhaul health (R57), `steer_client` (R58). The
three rows travel together as one capability even though R58's count alone
would allow the core: a controller that lists agents but cannot steer is not
a published shape, and splitting the protocol by row would be the single-verb
smell. One defaulted field is added (rung 3): `WifiMeshNode.backhaul_link:
WifiMeshLink | None = None`, so the topology read carries each agent's
wireless backhaul link (band, channel, signal, capacity) where the family
publishes it (columns 1, 3 and 4, each in part; R57 ◐) and `None` where it does not
or where the backhaul is wired (a wired link has none of the four facts);
the existing `WifiMeshStatus.backhaul_link` keeps describing the queried
node.
The extender is never a device of this archetype (§1).

Voice is designed as the `voice` tier and is `tier-staged` (the nominal
cells, below); the shape it takes when its trigger lands is: `VoiceGateway`
(`voice`) with `set_sip_account(
account: SipAccount) -> None`, `remove_sip_account(name) -> None`,
`list_sip_accounts() -> list[SipAccount]`, `get_sip_registration(name) ->
SipRegistration` and `list_fxs_lines() -> list[FxsLine]`. `SipAccount`
carries `name`, `username`, `password: str | None` (required on a write,
`None` on every read; the written value is confirmed by
`SipRegistrationState.REGISTERED`), `registrar`, `domain: str | None`,
`display_name: str | None`, `enabled: bool = True`; `SipRegistration`
carries `account`, `state: SipRegistrationState` (`REGISTERED`,
`REGISTERING`, `UNREGISTERED`, `FAILED`), `registrar: str | None`,
`expires_s: int | None`; `FxsLine` carries `name`, `enabled`, `hook_state:
FxsHookState | None` (`ON_HOOK`, `OFF_HOOK`, `RINGING`; `None` where the
family publishes the port but not its state, column 4) and `account: str |
None`. The test-bed `sip_phone` and `sip_server` are the far ends; this
capability is the gateway's own account and lines. None of these symbols lands
with this PR (M3, M32); the stage-4 evidence of columns 3 and 4, kept in the
private corpus, is what the `GAPS.md` pointer rests on.

**The nominal cells.** Three groups of ◐ cells support a tier only in name:
voice on column 1 (the family lists a voice plugin that publishes nothing,
R54–R55), voice on column 2 (a PBX from a package feed, reached through its
own configuration files and CLI, R54–R55) and mesh on column 3 (controller
source whose porting to the reference platform is marked ongoing, R56–R58).
§9 lists them as the stated risk with the arithmetic of each flip. If stage
4 finds a cell unsupported in substance, the cell flips to ✗ with its
source. The tier stays built while a majority of the five supports its
defining operation (the SIP account, R54; the topology, R56; the controller
configuration, R53); a member whose own row falls below the majority
becomes a documented per-column unsupported case inside the tier, as a core
member with a ◐ cell does; a tier whose defining operation falls below the
majority drops to `tier-staged` with its rows re-outcomed in the review
record.

Stage 4 outcome (review record, stage 4b). *Voice, column 1:* flipped — the
plugin's default branch publishes no parameter (R54–R55 ✗). *Voice, column 2:*
flipped — the PBX publishes no operation a voice member calls (R54–R55 ✗).
With column 5 ✗ already, voice holds on columns 3 and 4, two of five, below
the majority: the tier drops to `tier-staged` and M3 and M32 are re-outcomed;
its trigger is a third column supporting the SIP account (R54) beside columns 3 and 4, the majority of five (column 1's plugin releasing its voice data model would be
one), or a consumer. *Mesh, column 3:*
confirmed — the controller is carried on the family's mesh build variant, so
the cells stay ◐ and the tier stays built (the topology on four of five); the
six controller-side configuration members raise there.

**Overturn.** The flip above taking a tier below the majority; or a consumer
driving an extender directly, which is a separate request.

### Supersession of `CpeDevice` — new class, new key, old shape intact

**Decision.** `CpeGatewayDevice` is a new class under the new registry key
`cpe_gateway`; `CpeDevice` stays registered under `linux_cpe`, with every
member it has today, marked with the repository's deprecation marker
(`testprotocols._compat.deprecated`) and recorded as a `class` row in
`DEPRECATIONS.md`:

> | `testprotocols.devices.cpe:CpeDevice` (registry key `linux_cpe`) | `testprotocols.devices.cpe_gateway:CpeGatewayDevice`, registry key `cpe_gateway` | class | next release | next release + 6 months |

The period is one MINOR release and six months: the deprecating release is
the next MINOR, and removal is not before the first release six months
after it. Rung 5 in place — evolving `CpeDevice` member by member — does not
fit because the class name and key carry the Linux-twin pattern (`linux_`)
that two of the five columns are not, because the host-substrate levers it
mandates would each need a `remove` row with its own period while the one
consumer's driver still satisfies them, and because one deprecation of a
whole shape is cheaper for that consumer to reason about than a series. The
members the new class does not compose are listed in §4 ("Dropped
members"). The extensions this design makes to protocols the old class
composes — `DeviceLifecycle`, `Tr069Client`, `WifiOnboarding` and, through
the inherited health base, `DeviceManagement` (`DeviceInfo` is not among
them) — are breaking for the old class's implementer as any `extend` is:
the runtime `isinstance` gate keeps passing until the implementer's class
is checked against the extended protocols, the static conformance check
fails until the members are added, the changelog names each one, and the
stage-4 PR's deprecation tests cover both classes. `CpeDevice` is the only
archetype on `main` that composes `DeviceLifecycle`, `Tr069Client`,
`WifiOnboarding` and `DeviceManagement`, so its implementer is the one
these four extensions reach.

**Overturn.** A consumer that must keep `linux_cpe` beyond the period (none
known), which would extend the period by a dated note, not change the
mechanism.

### Health — a read-only base split off `DeviceManagement`

**Decision.** `DeviceHealth` (`health`) is a new protocol carrying the reads a
closed product publishes about itself: `is_online() -> bool`,
`get_seconds_uptime() -> float`, `read_cpu_load() -> CpuLoad`,
`read_memory_utilization() -> MemoryUtilization`, `read_running_processes() ->
list[ProcessInfo]` and `read_log_entries() -> list[EventLogEntry]`.
`DeviceManagement` inherits it, so every implementer of the host-shaped
protocol satisfies the base; the host-shaped members (`get_file_content`,
`get_board_logs`, `get_boottime_log`, the deprecated pairs) stay on
`DeviceManagement` and off the gateway. `CpuLoad` answers R40's load question
precisely instead of renaming `get_load_avg`: `percent: float | None` (the
family's processor-usage figure, columns 1, 3 and 5) and `load_average_1m:
float | None` (the kernel's figure, column 2), each `None` where the family
publishes no such figure (column 4 publishes neither; R40 ◐). `get_load_avg`
keeps its name and its meaning on `DeviceManagement` and is not part of the
split. The one member the base adds that `DeviceManagement` lacks,
`read_cpu_load`, is therefore an `extend` of `DeviceManagement` (breaking,
§12), whose one implementer on `main`'s archetypes is the superseded class's
driver. The inheritance is kept because it is what lets the existing
`testoperations` lifecycle wait `wait_for_reboot_completion`, typed against
`DeviceManagement` today, be widened to the health base without a second code
path — a stage-4 `testoperations` change recorded in §12 (`is_cpe_online`
probes through the test-bed ACS and takes a `Tr069Server`; it is unaffected).
This follows the recorded decision of `GAPS.md` 2026-06-11 (the host-shaped
protocol is not reused on a closed product) and the `RoutingRead` precedent (a
read-only protocol split off `Router`, `SPLITS.md`). Column 4 publishes uptime
only (R40 ◐, R41 ✗): memory, processes and the load record raise there; column
5 publishes per-class usage without process ids (R41 ◐): `read_running_processes`
raises there (`ProcessInfo.pid` is a required `int`, so no record can be
built).

**Overturn.** A test that needs the kernel's three load averages as a
record, which would widen `CpuLoad` by defaulted fields.

### The generic introductions — identity, lifecycle, configuration transfer

**Decision.** Worded for any closed network product, so the chartered router
sibling composes the same members when its design lands:

- `DeviceInfo` gains the read-only properties `manufacturer: str`,
  `serial_number: str`, `software_version: str`, `oui: str | None` and
  `hardware_version: str | None` beside `model` (R39); the two optional
  facts are `None` where the family publishes no field. Column 2 publishes
  neither manufacturer nor serial (R39 ◐): both properties raise the
  unsupported case there until stage 4 sources a board-level read. This is
  an `extend` (rung 5; a Protocol property cannot default) of a protocol the
  appliance and the switches compose.
- `DeviceLifecycle` gains `upgrade_firmware(image: ImageSource) -> None` (R45;
  `ImageSource(url: str, checksum_sha256: str | None = None)` in
  `models/device_management.py`, beside the management models, because the
  members it serves are generic), a lever whose acknowledgement is the family
  accepting the transfer and the apply and whose confirming observation is
  `wait_for_boot` followed by `info.software_version`. On column 5 it is two
  steps (upload, then reboot) and a rejection raises naming the step. It is one
  member rather than a staged pair (`stage_image` / `activate_image`) because
  three of five columns upgrade in one action and no column publishes a
  staged-image read: the pair is the staged half of this operation and sits
  below the majority, so it is a `tier-staged` row with its trigger (the first
  dual-image product), the method-grain rule applied (the unsplit member on the
  core, the finer pair staged). It gains `export_configuration() -> bytes` and
  `import_configuration(archive: bytes) -> None` (R48–R49): the archive is the
  family's own, opaque to the contract; the import is a lever confirmed by
  `wait_for_boot` where the family reboots and by the test reading back a
  setting it changed after the export (`wifi_bss.get_bss_config` is the
  natural one; the orchestration is a `testoperations` candidate). Column 3
  realises both through the shell store (◐, a `source:` line).
  `DeviceLifecycle` is composed by the superseded class only, so the extension
  reaches one implementer. `verify_cpe_is_booting` is renamed `verify_booting`
  with the old name delegating for the period (`deprecate`, §12), so the
  generalised docstring stops naming a class.
- Log export is `SyslogConfig` as it stands (R43; column 4 raises).

**Overturn.** A column whose firmware upgrade needs an explicit staged
state that a test must read (none in §2), which would add `stage_image` /
`activate_image` as a further `extend`.

### The administrator credential

**Decision.** `AdminCredential` (`admin_credential`) with
`set_password(account: str, password: str) -> None` and `list_accounts() ->
list[str]`. No protocol on `main` owns a local credential (`radius_client`
is a server registry; the chartered sibling's operator-login demand is a
policy over such servers, a different concern), and all five columns publish
the write (R50, five ✓). The write is a lever: its confirming observation is
a new management session authenticating with the credential, which the
**test** performs (a `testoperations` candidate: connect a second driver
instance with the new credential), never the driver after its own write.
When the account is the driver's own login, the driver's open session
continues and every later connection needs the new credential, which the
test supplies; the driver does not update its own configuration. The
account list is the read that finds the account.

**Overturn.** A sibling design landing a credential member on a shared
protocol first, which would make this a `reuse` row.

### Time — servers on `ntp_config`, the synchronisation state added

**Decision.** The gateway composes `NtpConfig` (`ntp`), the device's server
list the switches already compose, and `NtpConfig` gains `get_sync_state()
-> NtpSyncState` (R44): `status: NtpSyncStatus` (`SYNCHRONISED`,
`UNSYNCHRONISED`, `DISABLED`), `server: str | None`, `offset_ms: float |
None`, `last_sync: datetime | None`; the two types live in `models/switch.py`
beside `NtpServer`, where the protocol's server model already is. Columns 2
and 4 publish no sync state
(R44 ◐): the read raises there, a documented per-method unsupported case on
a trigger column (§9 Stated risks). `NtpClient` (set the date, run a
one-shot sync) is a host's clock lever and is not composed. A switch driver
whose family publishes no synchronisation state raises the same documented
case; which switch families do is not this design's evidence to cite.

**Overturn.** A trigger column that publishes neither the server list nor
the state (none in §2), which would move time to a tier.

### Onboarding, radios and stations

**Decision.** `WifiOnboarding` gains `cancel_wps(bss_name: str) -> None` and
`get_wps_state(bss_name: str) -> WpsState` (R28), with `WpsState(session:
WpsSessionState, method: WpsMethod | None, remaining_s: int | None)`,
`WpsSessionState` (`IDLE`, `ACTIVE`, `SUCCESS`, `FAILED`, `TIMEOUT`) and
`WpsMethod` (`PUSH_BUTTON`, `PIN`); the triggers keep their names and the
state read is their paired read. Column 5 publishes the push-button start
only (R28 ◐): cancel, the state read and the PIN trigger raise there. Column
4 publishes push-button only (R28 ◐: start, stop, status): the PIN trigger and
`get_wps_device_pin` raise there.
`WifiRadio` is unchanged: "configure band" (R22) is satisfied by addressing
every radio by its band, which is how the contract already works and how
three columns publish it (the band is fixed per radio on column 3, R22 ◐;
there the transmit power is a percentage with no dBm maximum, so
`set_tx_power` / `get_tx_power` raise); column 4 publishes the channel and the
enable only (R22 ◐, R23 ◐): the width, power and country setters raise, and so
do `get_tx_power`, `get_country` and `get_dfs_state`. `get_dfs_state` raises
on column 3 and column 5 as well (no channel-availability state published). `WifiStations.disconnect_station` is the disconnect (R27); column 4
raises. Band steering (R29) is composed from `WifiTransitions`'s 11v
members (`set_btm_enabled`, `send_btm_request`) and `wifi_bss` placement,
not a member of its own; column 4 raises on the 11k/v/r setters.

**Overturn.** A trigger column whose radios are not addressable by band
(none), which would need a radio handle on `WifiRadio`.

### DNS forwarder — a new capability

**Decision.** `DnsForwarder` (`dns_forwarder`) owns the gateway's forwarder:
`set_upstreams(upstreams: tuple[DnsUpstream, ...]) -> None` and
`get_upstreams() -> tuple[DnsUpstream, ...]` (R15; `DnsUpstream(address: str,
port: int = 53, domain: str | None = None)`, `domain` naming the suffix the
upstream serves — `None` is the default upstream for every name);
`add_host_override(override: DnsHostOverride) -> None`,
`remove_host_override(name: str) -> None`, `list_host_overrides() ->
list[DnsHostOverride]` (R16; `DnsHostOverride(name: str, address: str)`);
`set_rebind_protection(enabled: bool) -> None` and `get_rebind_protection() ->
bool` (R17). `set_upstreams` is a list replace of the forwarder's configured
upstreams. On columns 1 and 3 the driver rewrites the existing forwarding
instances in place and adds or deletes only the difference, so no step leaves
the forwarder without an upstream (one set per parameter; a rejection raises
naming the step); on column 2 it is one staged write and one commit, on column
5 one property set, so there is no window and no partial state. The configured
upstreams are distinct from the resolvers the WAN connection supplies (a
lease's, or `StaticAddressing.dns_servers`): those are read on
`get_wan_state().dns_servers`, `get_upstreams` returns the configured set only,
and the rewrite never touches a connection-derived entry on the data-model
columns, where both live in one forwarding table; an empty tuple written means
the connection's resolvers serve. `get_upstreams` returns the upstreams in the
device's own order, which columns 2 and 5 may not keep as written: the contract
promises the same set, not the order, and a test compares as a set (the
docstring says so). On column 4 a `DnsHostOverride.name` outside the family's
allowed character set would be rewritten by the device; the driver rejects such
a name before the write with the reason, so a read-back equals the write.
Per-column limits: column 3 publishes host overrides only through the shell
(R16 ◐: a `source:` line) and its rebind protection is always on (R17 ◐:
`set_rebind_protection(False)` is the unsupported case, `get_rebind_protection`
returns `True`); column 4 publishes no upstream write (R15 ✗: `set_upstreams`
raises), overrides only as a host name per MAC (R16 ◐: an override whose name
is not a LAN host's raises) and no rebind setting (R17 ✗: both members raise);
column 5 has no rebind filter (R17 ✗). `dns_client` is a host's resolver and is
not composed.

**Overturn.** A column whose forwarder cannot be reached except through a
per-host record (none in §2), which would make the overrides a `HostTable`
write instead.

### Bridge — `L2Bridge` from the GAPS entry, membership only

**Decision.** `L2Bridge` (`l2_bridge`) realises the membership half of the
`GAPS.md` 2026-05-02 entry: `create_bridge(config: BridgeConfig) -> None`,
`delete_bridge(name: str) -> None`, `list_bridges() -> list[BridgeConfig]`,
`get_bridge(name: str) -> BridgeConfig`, `add_member(bridge: str, member:
BridgeMember) -> None`, `remove_member(bridge: str, member_name: str) ->
None`, `get_members(bridge: str) -> list[BridgeMemberState]`.
`BridgeConfig(name: str, stp_mode: StpMode | None)` carries no membership:
`create_bridge` creates the bridge only, `add_member` / `remove_member` are the
only writes of membership and `get_members` its read (one owner per concern, no
coarser member defined by the two); `stp_mode` is `None` when spanning tree is off
(the shared `StpMode` has no off value) and otherwise a value of
`models/l2_common.py`'s enum. `BridgeMember(name: str, kind:
BridgeMemberKind)` with `BridgeMemberKind` `PORT` or `WIRELESS_NETWORK`;
`BridgeMemberState(member: BridgeMember, stp_state: StpPortState | None,
link_up: bool | None)`, each `None` where the family publishes no such
state. The bridge carries no address: the gateway's LAN address and DHCP
pool are `interface_dhcp`'s concern on the bridge interface. Membership of a
`WIRELESS_NETWORK` decides which bridge the network joins and is `l2_bridge`'s
alone; the VLAN tag the network's traffic carries on a VLAN-aware bridge is
`wifi_bss`'s alone (`set_vlan`, `create_bss(vlan_id=…)`). Where a family
realises both on one bridge-port entry, the driver backs the two with that one
entry, each member owning its parameter and neither writing the other's;
`set_vlan` with a tag on a network whose bridge is not VLAN-aware is the
documented unsupported case. The STP timers
and the forwarding-table read of the GAPS entry stay open under a dated
note; the table read is the `L2BridgeWhiteBox` candidate (§7). Per-column:
column 2 reads live membership through the shell (R19 ◐: a `source:`
line); column 4 publishes no bridge object (R18 ✗: every write raises;
R19 ◐: `get_members` is derived from the per-host port and guest flags).
`create_bridge` is two steps on columns 1 and 3 (the object add, then the STP
parameter) and a rejection raises naming the step; it is one staged write on
column 2 and one command on column 5. `get_members` returns the members in the
device's own order; the contract promises the set.

**Overturn.** A trigger column whose bridge cannot carry a wireless network
as a member (none in §2), which would split the two member kinds.

### Host table — a joined read

**Decision.** `HostTable` (`hosts`) with `list_hosts() -> list[LanHost]` and
`get_host(mac: str) -> LanHost` (R38). `LanHost(mac: str, ipv4_address: str
| None, ipv6_addresses: tuple[str, ...], hostname: str | None, attachment:
HostAttachment | None, interface: str | None, active: bool)`; `attachment`
is `ETHERNET` or `WIFI` and `None` where the family does not publish how the
host attaches. The set is closed by the contract: a host attached over a medium
the set lacks (coax, powerline) reads `None` too, and a column that publishes
such a medium adds a value by a dated note. `LanHost.mac` and the argument of
`get_host` are the canonical lowercase colon-separated form, canonicalised by
the driver on read and normalised on the argument (the host-filtering decision
states the rule once). Columns 1, 3 and 4 publish the table as one object; columns
2 and 5 publish no single table (R38 ◐) and their drivers **join** the DHCP
leases, the neighbour table and the station list inside `list_hosts`. That
join is a mapping, not an orchestration: it is one read of three sources
with no device state changed and no wait, and the `lossy:` line states
which fields each source lacks (no `hostname` for a static host without a
lease, no `attachment` for a host seen only in the neighbour table).

**Overturn.** A column whose sources disagree in a way the join cannot
reconcile (none found), which would make `list_hosts` a per-column
unsupported case there and the three sources the test's own reads.

### Automatic port mapping — enable per protocol, one table

**Decision.** `AutoPortMapping` (`auto_port_mapping`) with `set_enabled(
protocol: AutoMappingProtocol, enabled: bool) -> None`, `get_enabled(
protocol: AutoMappingProtocol) -> bool` (R36) and `list_mappings() ->
list[AutoPortMappingEntry]` (R37). `AutoMappingProtocol` is `UPNP_IGD`,
`PCP` or `NAT_PMP`; `AutoPortMappingEntry(external_port: int, protocol:
PortMappingProtocol, internal_host: str, internal_port: int, origin:
AutoMappingProtocol | None, remaining_lease_s: int | None, description: str
| None)`, `origin` `None` where the family does not say which protocol
created the mapping (column 4, R37 ◐). Per-column: PCP is absent on columns
3, 4 and 5 (R36 ◐: `set_enabled(PCP, …)` raises there) and NAT-PMP on columns
3, 4 and 5. Column 2 publishes NAT-PMP jointly with PCP (one switch for both):
`set_enabled` on either is a per-value refusal and `get_enabled` reads the
joint switch. Column 1's NAT-PMP is the IGD daemon's own switch, shared with
that daemon's PCP server, while the PCP the column-1 R36–R37 cells cite is a
client whose entries are mappings requested upstream; the IGD's mappings may
be readable in the port-mapping table with their origin (stage 4,
unverified; §8). Column 4's toggle enables or disables UPnP as a whole (R36 ◐:
stated in the docstring, the driver maps `UPNP_IGD` onto it); column 1
reads PCP mappings only (R37 ◐: the UPnP lease table is the unsupported
case); columns 2 and 3 read the table from the lease file or the IGD service
(R37 ◐: a `source:` line). The administrator's own mappings stay on
`firewall` (R31–R32): origin and lease distinguish the two tables.

**Overturn.** A column that publishes the automatic mappings only inside the
administrator's table (none in §2), which would make `list_mappings` a
filter over `firewall.list_port_mappings`.

### Composed operations — the guest segment

**Decision.** A guest segment (R20) is a bridge (`l2_bridge`), a zone
(`firewall_zones`), a pool (`interface_dhcp`) and a network (`wifi_bss`)
with its own membership: no member is added. The orchestration that creates
one belongs to `testoperations`, where the per-column shapes (a guest flag
per network on column 4, a composed VLAN on column 5) are expressed as
composition over the four capabilities. Column 3 and column 5 publish no
guest object (R20 ◐): their drivers satisfy the four capabilities and the
operation composes them.

**Overturn.** A column that publishes a guest segment as one object that
the four capabilities cannot reach (none in §2).

### Method grain and paired reads

Every write this design adds or extends, its paired read or confirming
observation, and whether a column realises it in more than one device step
(design questions 8 and 11). A multi-step write raises naming the step and
writes nothing more; whether the as-found state returns is a per-column fact
recorded in §8 and in the drivers' `lossy:` lines.

| Write | Paired read / observation | Multi-step? failure outcome |
| --- | --- | --- |
| `WanConnection.set_wan_connection` | `get_wan_connection`, `get_wan_state` (`CONNECTED` after `AUTHENTICATING` confirms the password) | yes on columns 1, 2, 3 and 5: raises naming the step; column 2's steps are staged under a change-file path unique to the session and fresh per write and never committed, columns 1, 3 and 5 leave the steps before |
| `WanConnection.reset_session` (PPPoE lever; raises on the other modes) | `get_wan_state` status cycling; `await_reachability` from a LAN client | yes on columns 2, 4 and 5 (the session is torn down, then re-established: two device steps); a refusal at the second step names it and leaves the session down; one parameter write on columns 1 and 3 |
| `DnsForwarder.set_upstreams` (list replace) | `get_upstreams` (set equality) | yes on columns 1 and 3 (existing instances rewritten in place, the difference added or deleted, so no step leaves the forwarder without an upstream; one set per parameter): raises naming the step; one commit on column 2, one property set on column 5 |
| `DnsForwarder.add_host_override` / `remove_host_override` | `list_host_overrides` | no |
| `DnsForwarder.set_rebind_protection` | `get_rebind_protection` | no |
| `L2Bridge.create_bridge` / `delete_bridge` | `list_bridges`, `get_bridge` | yes on columns 1 and 3 (the object add, then the STP parameter): raises naming the step; one staged write on column 2, one command on column 5 |
| `L2Bridge.add_member` / `remove_member` | `get_members` | no |
| `HostFilter.block_host` / `unblock_host` | `get_host_block`, `list_host_blocks` | yes on columns 1, 2 and 3 (column 1: the host access-control entry, then one set per parameter and one add per schedule window; column 2: a rule plus a schedule section; column 3: the internet-access policy, then one set per parameter): raises naming the step; column 4: one action for a block, two for an unblock (standard profile, then the disallow cleared); column 5: two requests for a new block (profile, then device entry), two deletes for an unblock; on both the steps before a rejection stand |
| `AutoPortMapping.set_enabled` | `get_enabled` | no |
| `AdminCredential.set_password` (lever) | a new management session authenticating with the credential, opened by the test; `list_accounts` finds the account | no |
| `NtpConfig.set_ntp_servers` (existing) | `get_ntp_servers`; `get_sync_state` for the effect | as today |
| `DeviceLifecycle.upgrade_firmware` (lever) | `wait_for_boot`, then `info.software_version` | yes on column 5 (upload, then reboot): raises naming the step |
| `DeviceLifecycle.import_configuration` (lever) | `wait_for_boot` where the family reboots; the test re-reads a setting it changed after the export (`wifi_bss.get_bss_config`) | no (one archive) |
| `Tr069Client.set_acs` | `get_acs` (passwords `None`); `is_tr069_connected` after the next inform confirms the credentials | yes on columns 1, 3 and 4 (one set or one action per parameter group): raises naming the step |
| `Tr069Client.force_inform` (lever) | `is_tr069_connected`; the test-bed ACS's inform record | no |
| `UspAgent.set_controller` | `get_controller` | yes on columns 1, 3 and 4 (write the agent's file and restart the agent; one set per parameter on column 4): raises naming the step |
| `VoiceGateway.set_sip_account` / `remove_sip_account` (`tier-staged`, M32: the grain it takes when it lands) | `list_sip_accounts` (password `None`); `get_sip_registration` `REGISTERED` confirms the credentials | yes on columns 1, 2, 3 and 4 (one set per parameter; account section then reload on column 2; one action per parameter group on column 4): raises naming the step |
| `WifiOnboarding.cancel_wps` (lever) | `get_wps_state` | no |
| `WifiMesh.steer_client` (existing lever) | `get_topology` showing the station on the target agent | as today |
| `DeviceLifecycle.upgrade_firmware` (lever) on column 5 | as above | yes on column 5 (upload, then reboot): raises naming the step; every other lever above is one device step |

**A write the as-found state already satisfies** (stage 4, all columns). An
idempotent write whose requested state already holds, as the member's own
lookup shows — a removal of what is absent, a clear of what is empty, a
replace with the set already held — may return without sending anything; its
docstring in the driver carries the `acknowledged:` line "a request the
as-found state already satisfies sends nothing". A write with nothing to act
on (a country with no radio to set it on, a WAN write with nothing to write)
is not such a case and raises. The reference drivers apply the rule on
clearing the DMZ host, clearing a network's access list and writing an empty
log-server list (§8).

Each member is one transition between stable states; nothing here orchestrates
(a guest segment, a WAN failover, a reboot-and-verify is a `testoperations`
operation over these members). The cross-capability candidates this design
leaves to `testoperations`: `wait_for_reboot_completion` already exists for the
lifecycle levers and is widened from `DeviceManagement` to the health base
(§12; `is_cpe_online` takes the test-bed ACS and is unchanged); a guest-segment
composition, a WAN-reconnect wait, the second-session credential check and the
export-change-import-compare sequence are candidates recorded at stage 4.

### Precise types and proportionality

The enums this design adds (`WanMode` has three values; IPoE is a mode plus
the `vlan` part): `WanMode`, `WanIpv6Mode`, `WanStatus`,
`ProvisioningMode`, `BridgeMemberKind`, `HostAttachment`, `Weekday`,
`AutoMappingProtocol`, `NtpSyncStatus`, `WpsSessionState`, `WpsMethod`,
`UspTransport`, `SipRegistrationState`, `FxsHookState`. The records:
`WanConnectionConfig`, `PppoeCredentials`, `StaticAddressing`, `WanVlan`,
`WanIpv6`, `WanConnectionState`, `DnsUpstream` (`address`, `port: int = 53`,
`domain: str | None`), `DnsHostOverride` (`name`, `address`), `BridgeConfig`
(`name`, `stp_mode: StpMode | None` from `models/l2_common.py`, `None` = off;
membership is read by `get_members`), `BridgeMember` (`name`, `kind`), `BridgeMemberState`
(`member`, `stp_state: StpPortState | None`, `link_up: bool | None`),
`LanHost` (`mac`, `ipv4_address: str | None`, `ipv6_addresses: tuple[str,
...]`, `hostname: str | None`, `attachment: HostAttachment | None` —
`ETHERNET`, `WIFI`, `None` where the family does not publish it —
`interface: str | None`, `active: bool`), `HostBlock`, `WeeklySchedule`
(`start` and `end` are times of day on each listed weekday; an `end` before
`start` runs past midnight into the next day, as every column's scheduler
reads it),
`AutoPortMappingEntry` (`external_port`, `protocol: PortMappingProtocol`,
`internal_host`, `internal_port`, `origin: AutoMappingProtocol | None`,
`remaining_lease_s: int | None`, `description: str | None`), `CpuLoad`,
`ImageSource` (`url`, `checksum_sha256: str | None`), `AcsConfig`,
`NtpSyncState`, `WpsState`, `UspController`,
`UspAgentState` (the endpoint identifier only), and, staged with the voice
tier (M32), `SipAccount`, `SipRegistration`, `FxsLine` and the two voice enums
above. Reused:
`PortMapping`, `PortMappingProtocol`, `FirewallRule`, `Zone`,
`InterfaceDhcpConfig` and its sub-models, `DhcpLease`, `NtpServer`,
`SyslogServer`, `PortStatusEntry`, `MemoryUtilization`, `ProcessInfo`,
`EventLogEntry`, `WifiMeshTopology`, `WifiMeshNode`, `WifiMeshLink`,
`StpMode`, `StpPortState`.

Values that stay `str`, with the reason: names and handles (connection, bridge,
account, interface names: the family's own identifiers), credentials and
passphrases (typed `str | None` on the records that are also read back, `None`
meaning "not readable", never an empty string), URLs, hostnames and addresses
(an address is a `str` in every model on `main`, and a MAC is the canonical
lowercase colon-separated form on every record and argument of this design, as
`WifiMeshNode.mac` is; retyping is the open `GAPS.md` 2026-06-11 question, not
this design's), the device's own version strings and the archive bytes. No
`Any`, `object` or `dict` appears in a signature or field; absent values are `X
| None` with the meaning stated above; every closed set is an enum. Each type
pays for itself in the structural check: a driver that returns the wrong enum,
omits a field or widens a type fails `mypy --strict` and the conformance check,
which is the verification stage 4 runs.

### Decided as verification items

- **Source maintenance** (§11 Q10): §10 re-points the charter's knowledge-base
  citation and notes the frozen documentation site of column 5 with its
  successor; the client-rendered wiki and the mis-titled service documents
  are recorded as they are, with the retrieval method. Stage 4 re-checks
  every cited URL when the drivers cite them (`source:` lines).
- **Reference-image inclusion** (§11 Q11): the column-3 driver cites the
  reference build's component list for every manager its `source:` lines
  rest on (§10 column 3 entries 1, 3, 5–8); a manager absent from the build
  flips its cells to ◐ with the component named. Stage 4: the PPP manager is
  absent, so R3–R4 on column 3 are ◐ (whether the platform's own PPP
  parameters are served without it is unverified); the voice manager is
  installed with its data-model version unverified; the mesh controller is
  carried on the family's mesh build variant; the USP agent is in the build
  (§10 column 3).
- **Two CWMP clients on column 1** (§11 Q12): decided at stage 4. The
  column-1 driver takes the data-model route for `set_acs` / `get_acs` (the
  management-server object, one set per parameter: enable, URL, username,
  password, periodic-inform enable and interval) and the CWMP client's own bus
  object for `force_inform` and `is_tr069_connected`, because the
  management-server object publishes no inform method. The two halves rest
  on two clients' documentation (§10 column 1 entries 51 and 52): whether an
  image with the data-model client registers the same bus object is
  unverified, and stays a verification item until a source settles it.
  Recorded in the review record (stage 4b).

## 7. Levels

### Intent (sea-level) and mechanism (white-box)

The five columns reach the same operations through four kinds of
management plane (§1, §8): two expose a **data model** whose every path is
readable and, where the model allows, writable (columns 1 and 3); one
exposes a **configuration store and a bus** whose every section and object
is reachable from a shell (column 2); one exposes a **proprietary CLI** over
every menu of the device (column 5); one exposes **SOAP actions** on the LAN
side and nothing beneath them (column 4). The first four publish mechanism
as well as intent — any path, any section, any menu — and the fifth
publishes intent only. The portable surface is the **intersection**, and
the intersection is the intent level: the operations of §2, as the capability
members of §4. That is why the core is written as intents (set the
connection, block the host, read the hosts) and never as paths, sections or
actions.

The finer granularity of the four mechanism-publishing columns is real, and
the repo already has the axis for it: `LEVELS.md` gives every capability a
mandatory black-box sea-level surface plus optional `<Capability>WhiteBox(
<Capability>, Protocol)` extensions that land on tracked evidence. Applied
here, mechanism access takes the three forms the sibling designs
distinguish, of which two have merit:

- **Raw-state reads that prove a write landed** — white-box, per the
  `PacketFilterWhiteBox` and `FirewallWhiteBox` precedents already on `main`
  (the kernel rule dumps behind a gateway's port forwards and filters). For
  this class the valuable ones are the realised state behind the composed
  intents: the connection object's full state (every parameter the data
  model or the store holds for it), the bridge's forwarding table and port
  states, the realised rules behind a host block and its schedule, the
  forwarder's effective configuration. The verb and the return type stay
  vendor-neutral; the payload is substrate state, opaque `str` where no
  neutral record exists and a typed record where the vocabulary is shared
  (`MacTableEntry` from `models/l2_common.py` for the bridge table, the
  read the `GAPS.md` 2026-05-02 entry sketches). Column 4 cannot back any
  of them: it publishes no mechanism, so its driver satisfies no white-box
  extension, which the convention handles (a test pinned to the extension
  collection-skips there).
- **Levers with no intent-level equivalent** — white-box, per the
  `WifiRadioWhiteBox.inject_radar_event` precedent. Restarting the ACS
  client or the USP agent without touching its configuration, forcing a
  lease expiry on the server side, dropping the WAN link at the port driver
  rather than the connection object: each makes a convergence test
  reproducible and is published by the mechanism columns only. None is
  seeded here (no consumer signal in the request); each is a candidate.
- **Mechanism-level passthroughs as protocol surface** — a read of an
  arbitrary data-model path, of an arbitrary configuration section, or a
  call of an arbitrary SOAP action — **no merit as protocols.** Each is
  shaped by one management plane by construction and fails the neutrality
  check; each would open a second write path for behaviour the intent level
  already encodes. The reference drivers use them as **driver-internal
  helpers** (the dialogue and transport sessions of the corpus), never as
  members.

**Selecting the level needs no mechanism of its own.** A driver either
satisfies a `WhiteBox` extension or does not; a test declares the level it
needs by pinning against the extension (`isinstance`), as the existing
white-box tests do. For this class the enabling fact is **mechanism
publication**: the four shell, data-model and CLI columns offer both levels;
the SOAP column offers sea level only. Who manages the device never enters
(§1, §8).

### White-box candidates

Nothing is seeded with this archetype; every candidate below is recorded in
`LEVELS.md` as a candidate (§12) and lands when a consumer or reviewer
signal names it, with the drivers expected to satisfy it (the shell,
data-model and CLI columns, 1, 2, 3 and 5) and not (the SOAP column, 4).

- *Raw-state reads* (prove a composed write landed; pin diagnostics):
  `WanConnectionWhiteBox.get_raw_connection_state(name) -> str` — the
  connection's full realised state; `L2BridgeWhiteBox.get_bridge_table(
  name) -> list[MacTableEntry]` — the forwarding table, typed with the
  shared vocabulary, and `get_raw_bridge_state(name) -> str`;
  `HostFilterWhiteBox.get_raw_filter_rules() -> str` — the realised rules
  and schedule behind the blocks; `DnsForwarderWhiteBox.get_raw_forwarder_
  config() -> str`; `DeviceHealthWhiteBox.get_raw_process_table() -> str`
  (the host-shaped read `DeviceManagement` keeps at sea level on the
  hosts). The existing `FirewallWhiteBox`, `PacketFilterWhiteBox`,
  `WifiRadioWhiteBox` and `WifiMeshWhiteBox` apply unchanged: columns 1, 2
  and 3 back the kernel dumps and the PHY dump; column 5 backs none of the
  kernel dumps (a different kernel firewall) and column 4 none at all.
- *Levers with no intent-level equivalent* (reproducible convergence tests):
  `Tr069ClientWhiteBox.restart_client() -> None` and
  `UspAgentWhiteBox.restart_agent() -> None` — restart the management
  client without changing its configuration (the sea-level `force_inform`
  provokes a session, not a restart); `WanConnectionWhiteBox.
  expire_lease(name) -> None` — force the WAN lease to expire so the renew
  path runs; `InterfaceDhcpWhiteBox.expire_lease(mac) -> None` — the
  server-side counterpart for a LAN host.

Each candidate is recorded with its signal when it lands; until then the
sea-level members and the test-bed hosts carry every test the request names
(§1 Demand).

## 8. Driver-facing neutrality notes

Vendor names appear in this section by design: it tells a driver author how
each reviewed family's management plane acknowledges a write, what it
normalises, how it refuses, and what the reference driver cites. Nothing
here enters a method, model or enum. The management mode (operator through
an ACS, household through a local interface) is not a driver fact either:
the reference drivers reach every family as an administrator on the box.

**Column 1 — prplOS (prplWare 4.0 line).** Transport: SSH to the box; the
TR-181 data model through the Ambiorix CLI (`ba-cli`, `ubus-cli`), the
configuration store beneath it where the data model stops (the firewall
zones of R30, the CWMP client's own bus object of R52). A write is a
parameter set or an object add on a data-model path; the acknowledgement is
the CLI's reply (an error line and a non-zero status on refusal: an
unknown path, an invalid value, a bus ACL denial), applied by the owning
plugin at once with no commit step; a write that the model marks read-only
is refused, not ignored. The driver requires the set's echo of the parameter
and the exit status of every shell step beside the data model (the agent's
service and file steps, the bus call, the access-point daemon's `OK`); a
data-model method call's silent success is undocumented and stays an
unverified acknowledgement, the lever's paired observation being the check.
Normalisations: MAC addresses lower-cased, Wi-Fi
and connection object instances re-numbered on add (the driver keys on the
alias parameter it sets, never on the instance number), enumerations returned in the
model's spelling. The driver's `source:` lines cite the plugin's data-model
documentation page for the path and the observed output of the public
example image where the exploration lifted a cell to ✓ (R56–R58, R52).
Multi-step writes: one set per parameter, so a rejection leaves the sets
before it applied; the `lossy:` line says so for the WAN connection and the
guest segment. A DHCP reservation keeps the instance named after it (the
alias is write-once), so a renamed reservation is added before the old entry
is deleted: the host briefly has two entries and never none (`lossy:`).
Stage 4 recorded the family facts the driver states. The
firewall is level- and policy-based (tr181-firewall 0cfb99f) with forward
chains only: `FORWARD` maps to `FORWARD_L_Custom_Out`, `INPUT` and `OUTPUT`
are per-value refusals on every chain member, the default policy is the
custom level's one DefaultPolicy, rules take effect while the custom level
is active, and no per-rule counter is published (both counter members raise).
The TR-069 route: `set_acs` / `get_acs` through `Device.ManagementServer.`
(tr069-manager v1.31.3, §10 [51]: EnableCWMP, URL, Username,
Password, PeriodicInformEnable, PeriodicInformInterval), one set per
parameter; `force_inform` and `is_tr069_connected` through the CWMP client's
bus object (`ubus call tr069 inform '{"event":"6 CONNECTION REQUEST"}'`,
`ubus call tr069 status`; §10 [52], observed on prplOS 4.0.3), because
`ManagementServer.` publishes no inform method. The two halves cite two
clients' documents: [51] is tr069-manager's page (the `mgmt` build profile
packages `tr069-manager`), [52]'s `tr069` bus object is icwmp's; whether a
tr069-manager image registers the same object is unverified. NAT-PMP is
miniupnpd's `X_PRPL-COM_IGDConfig.NATPMPPCPSupport` (one `%protected` switch
with the daemon's own PCP server), the PCP of §10 [36]/[37] is tr181-pcp, a
client, and IGD mappings may appear in `NAT.PortMapping` with `Origin=UPnP`
(unverified). DPP has no data-model object: enrolment goes through the
hostapd control interface beneath pwhm (README-DPP), source-only. The USP
agent's only documented write path, the CI scripts, stops obuspa, installs
the reset file and removes `/etc/obuspa.db`, resetting every run-time value
(unverified). Radio and network limits (pwhm d98e872): TransmitPower is a
percentage of full power (-1 auto), mapped to the dBm contract through pwhm's
`getMaxTransmitPowerdBm(channel)` / `getCurrentTransmitPowerdBm()`
(unverified); PossibleChannels is marked "NOT SUPPORTED YET", so
`list_supported_channels` reads nothing on an image that leaves it empty;
MultiAPVlanId is the backhaul's, so a per-network VLAN tag is a per-value
refusal. The controller ODL (prplMesh eda905b) carries no agent removal and
no backhaul constraint, and `MultiAPDevice.Backhaul.Stats` exists though the
driver reads the parent's station entry for the backhaul link (`partial:`).

**Column 2 — OpenWrt 24.10 line with icwmp.** Transport: SSH to the box; the
configuration store through `uci` (set, add, delete, then `commit` on the
configuration, then the service reload or `reload_config`), the runtime through
`ubus` (JSON replies) and the service CLIs (`hostapd_cli`, `iwinfo`, `wifi
reload`). A write is acknowledged by `uci`'s exit status and `commit`
(refusals: "Entry not found", "Invalid argument", "Parse error"), the driver
requiring the status of every shell step, and by the
bus's reply ("Command failed: Not found / Invalid argument"); the PPPoE
session reset is two steps, the interface brought down and then up, and a
refusal at the second leaves it down; the TR-069 client
answers on its `tr069` bus object and in the `cwmp` section. The store is
staged until `commit`, and staged changes outlive the call that made them: `uci
changes` lists them and the next `commit` of that configuration applies them,
so the leftovers of a rejected write would ride the driver's next commit. The
driver therefore stages every write under a change-file path of its own (`uci
-t <path>` on each `set`, `add`, `delete` and on the `commit`), unique to the
session and fresh per write (`/tmp/.uci-<nonce>-write_<n>`; a `-t` commit under
a reused name would commit a rejected write's leftover delta): a rejected
write's staged steps are never committed, nothing is written on the failure
path, and the leftovers are a file in the temporary file system that the
reboot clears. The flag is `-t`, not `-P`: at the 24.10 pin (uci
16ff0badbde7e17ec3bd1f827ffe45922956cf86, cli.c:330-333) `-P` also sets
`CLI_FLAG_NOCOMMIT`, under which `commit` returns 0 having applied nothing
(cli.c:737-746), so a `-P` write would "succeed" with nothing applied; `-t`
sets the save directory only. The `lossy:` line states the family fact that a
`-t` commit also applies whatever another session staged for the same
configuration in the default path and leaves that delta staged there, applied
again on the other session's own commit, and that a plain `uci show` shows it
before either commit (source-only: libuci.c:63-64, delta.c:108-123,
delta.c:329-345; no page documents it).
Normalisations: list options re-ordered on commit (the contract promises the
set, §6), anonymous sections renamed (`cfg0a3b...`; the driver names every
section it creates), booleans written as `1`/`0`. Refusal shapes are text lines
on stderr; the driver matches them, never the success path. `source:` lines
cite the wiki page for the section or the bus object and, for the three hostapd
methods the wiki does not document (R27, R28), the project source at the 24.10
tag with "source-only" stated; hostapd also registers `wps_cancel` at the tag
(`cancel_wps` maps, source-only). Netifd at the pin prints field names the
ubus page does not show (`ipv4-address`, `ipv6-address`, `ipv6-prefix`,
`dns-server`, `carrier`, `speed`; §10 [2], [8], [21]), cited source-only.
The access point sends no Neighbor Report Request: the member sends
`rrm_beacon_req` (`lossy:`), and `bss_transition_request` takes
neighbour-report elements, so a BTM candidate list is a per-value refusal; no
static tag is documented for an AP network (`wifi-vlan` serves 802.1X dynamic
VLANs), so `set_vlan` with a tag is a per-value refusal; miniupnpd's
`enable_natpmp` switches NAT-PMP and PCP together, so `set_enabled` on either
is a per-value refusal; one remote log destination (`log_ip`), so more
than one server is a per-value refusal; netifd publishes the granted lease
time (`data.leasetime`), not its remaining part, so the driver derives an
upper bound. Voice (R54–R55) is ✗ here at stage 4 (the PBX publishes
no operation a voice member calls) and the mesh (R56–R58) has no controller:
the driver composes neither tier.

**Column 3 — RDK-B (rdkb-2025q4-kirkstone and later).** Transport: SSH or
serial to the box; the TR-181 data model through `dmcli eRT` (`getv`,
`setv`, `addtable`, `deltable`). A write is acknowledged by the tool's
result line ("Execution succeed." / "Execution fail(error code:<name>(<code>))." — the
tool prints no space after the colon, data-model-cli develop 83e0a58
ccsp_message_bus_client_tool.c; the driver's pattern accepts both); a
destination component that is not running yields its own error. Some write
groups take effect only after the family's apply parameter is set (Wi-Fi:
the radio and access-point apply flags), which the driver names as the step
in a multi-step write; a rejection leaves the sets before it applied, and
the `lossy:` line says so. Normalisations: MAC addresses upper-cased in
some tables and lower-cased in others (the driver canonicalises on read),
instance numbers re-assigned on `addtable`. Cells marked "shell only" (R16,
R48, R49) are realised through the store or the file system with the
command cited as a `source:` line and a `lossy:` line for the format. The
reference-image question (§6, verification items) binds every `source:`
that rests on an optional manager: the driver cites the build's component
list beside the manager's documentation. Stage 4 found, against the BPI layer
(meta-cmf-bananapi `rdkb-2025q4-kirkstone` 76849e6): ppp-manager is not built
(`rdk-ppp-manager` only with `rdkb_xdsl_ppp_manager`, unset), so R3–R4 are ◐
and the driver writes CcspPandM's `PPP.Interface` parameters; the
telco-voice-manager is installed, but the TR-104 v2 switch is written as
`DISTRO_FEATURE_append` (singular, not read by bitbake) and the shared
packagegroup keys `rdktelcovoicemanager` on that same feature, so which voice
model is built is unverified; unified-wifi-mesh is carried on the EasyMesh
build variant (`FEATURE_TYPE=EasyMesh`), whose data elements publish no
network enable, agent onboarding or removal, backhaul band or channel or
enrolment credential (the six controller-side members raise; topology,
`Backhaul.Stats` and `ClientSteer()` map); the USP agent is built (`usppa`),
with no agent state. The firewall is the internet-access policy table:
forward-only (`INPUT` and `OUTPUT` refused per value), no default policy for
forwarded traffic (FirewallLevel is a preset), and `InternetAccess.LogEntry`
is a hit log, not a counter, so the policy pair and both counter members
raise. OneWifi's SSID and access-point tables are static: `create_bss` claims
the band's first unnamed disabled slot and `delete_bss` disables it
(`lossy:`). Host overrides are marked `/etc/hosts` lines plus dnsmasq's
SIGHUP (§10 [16]). No DHCPv6 release trigger is published (`release_ipv6`
raises), no 802.11r parameter and no BTM or measurement request (those
members raise).

**Column 4 — FRITZ!OS 8.20 and later.** Transport: HTTP(S) on the LAN side
only — TR-064 SOAP actions on the device's service port with digest
authentication, the mesh topology as JSON behind the HTTP session-ID login,
UPnP IGD for the mapping table. There is no CLI (the knowledge base states
Telnet is unsupported since 6.25) and TR-064 is not reachable from the WAN;
the reference driver runs from a LAN host. A write is acknowledged by an
HTTP 200 with the action's response envelope (the PPPoE session reset is two
actions, the termination and then the connection request, and a fault at the
second leaves the session down); a refusal is a SOAP fault
whose `errorCode` the driver maps (invalid action, invalid arguments, action
failed, internal error, and the per-action codes the service documents
list); a silent 200 on an action the service document marks as having no
effect is treated as a refusal by the driver when the document says so — the
one action so marked is `LANEthernetInterfaceConfig` SetEnable ("Writeable
but internally ignored.", TR-064_LAN_Ethernet_Interface_Config.pdf Table 1),
which backs no member, so the rule is the session's and no write relies on
it. The driver relies on three reads at login (TR-064_First_Steps.pdf §3.1,
§5.1, §6.1.3): the device description (`/tr64desc.xml`), Layer3Forwarding
GetDefaultConnectionService (the R1 mode refusal rests on it: an IP
connection reads `DHCP`, its addressing method unpublished, so `STATIC` never
matches, and every accepted write sends SetConnectionType `IP_Routed`) and
the session's own LAN address (the R31 host refusal).
Normalisations: hostnames re-written to the family's allowed character set,
SSIDs applied at once with a Wi-Fi restart, per-host settings keyed by the
host's MAC. The write-narrow side of the matrix is here: thirteen ✗ cells
and twenty-six ◐ cells (§9), each raised as `NotSupportedError` with the
service document as the source, or mapped with the limit stated. `source:`
lines cite the service document (title and the action's section), retrieved
as PDF; several documents carry wrong metadata titles, so the driver cites
the document's file name and the action, not the metadata. Beyond titles the
documents carry argument-direction and table errors the driver works around
(SetPassword's NewPassword listed "out"; UPnP SetConfig's arguments "out";
the Hosts service's swapped host-name length limits; the USP_Controller and
Host_Filter action lists titled "the service Hosts"). Stage 4 also recorded:
WPS is push-button only (`X_AVM-DE_SetWPSConfig` takes pbc and stop; the PIN
variables obsolete since history v45), so the PIN members raise (R28 ◐); the
radio service publishes no transmit power, regulatory domain or DFS state
(R23 ◐); the Hosts service's only mesh action is the topology path, so every
controller-side mesh write and steering raise; the filter profiles read as
forward-chain rules (R34); the pool's lease time has neither a Set action nor
a state variable (the driver reports ten days, unverified); ManagementServer
GetInfo publishes no TR-069 enable or session state; the agent's own USP
EndpointID is in no action (the driver reports the TR-369 `os::` form built
from DeviceInfo).

**Column 5 — MikroTik RouterOS v7.** Transport: SSH to the CLI, or the REST
API (the operations are the same menus; the reference driver takes REST). On
the CLI a write is a menu command (`add`, `set`, `remove`, `enable`,
`disable`); a success is **silent** (no output) and cited as such from the
manual; a refusal is a text line ("failure: ...", "input does not match any
value of ...", "no such item", "invalid value for argument"), which the
driver matches. On REST (REST API page 47579162, "HTTP Methods", "Errors")
the acknowledgement is the 2xx (a PUT returns the created object with its
`.id`; without one the driver raises its no-acknowledgement error; the PPPoE
session reset is two requests, the client disabled and then enabled, and a
refusal at the second leaves it disabled), a refusal is a
status of 400 or above with `{"error","message","detail"}`, and there is no
silent success; record-less menus (`/ip dns`, `/ip upnp`, `/system ntp
client`, `/tr069-client`, `/interface/wifi/capsman`) are changed with POST
`/rest/<menu>/set`, not PATCH (PATCH on a record-less menu unverified). Reads use `print` with the terse or as-value forms. There
is no commit: each command applies at once, so a rejection in a multi-step
write leaves the commands before it applied, and the `lossy:` line says
so. Normalisations: item ordering by the menu's own order, `disabled=no`
filled in, MAC addresses upper-cased, the `wifi` package versus the legacy
`wireless` package (the driver cites the package per model; the ✓ Wi-Fi
cells rest on the `wifi` package, named in their §10 entries). On the CLI the
reboot asks for confirmation (the driver answers it); on REST the POST runs
the reboot and no prompt arises (unverified); the lever's observation is
`wait_for_boot`. Mesh is CAPsMAN, not EasyMesh (R56 ◐): the driver maps the
controller's access-point list onto the topology with no backhaul links, maps
the CAPsMAN switch (`set_enabled`) and raises for backhaul health (R57 ✗),
for steering (R58 ✗: the Steering section has properties only, no command
addressing one client) and for the other controller-side writes (a CAP joins
from its own side), with the source. 802.11r is published (`security.ft`,
`security.ft-over-ds`), so `set_ft_enabled` maps; the band-steering switch and
the three frame senders raise. Per-rule firewall counters exist (a
`passthrough` rule increments them) but their fields are undocumented on the
Filter page, so both counter members raise; the three predefined chains have
no default policy (the policy pair and the flush raise). The profiler reports
CPU usage per process class without process ids, so `read_running_processes`
raises. The `wifi` package documents no CAC or non-occupancy read
(`get_dfs_state` raises), and the country is a country name mapped through a
table of ISO codes (`lossy:`). Kid Control holds one allowed range per
weekday: a block that is not one range per day is a per-value refusal. The documentation
site the exploration cited carries a "frozen" banner pointing at its
successor (§10); the driver cites the successor page where one exists.

**All columns — a write the as-found state already satisfies** (§6, method
grain). The reference drivers return without sending when the member's own
lookup shows the requested state already holds, and say so in an
`acknowledged:` line ("a request the as-found state already satisfies sends
nothing"): `set_dmz_host(None)` with no DMZ entry (columns 1, 2 and 5),
`clear_acl` with no entries (columns 1, 2, 3 and 5), `set_syslog_servers([])`
with none of the driver's log actions present (columns 1, 2 and 5). A write
with nothing to act on raises instead (column 5's `set_country` with no radio
to set it on).

### Lossy mappings as built

Every `lossy:` line of the five reference drivers (verification question 4:
every lossy mapping recorded in the document), per column, named by the
protocol it maps and the member where the line sits on one; a line on the
protocol covers its whole mapping, a line on the session the family's
transport. The texts are the drivers' own, as folded at the verification
review (corpus commit `1448bb8`); a later driver change re-records them here.


**Column 1** (37 lines)

- the session: an instance found by alias is written through the numbered path the same call read
- `AdminCredential`: the account is found by its `Username`; the password is never read back (the model returns no stored secret).
- `AutoPortMapping`: NAT-PMP is miniupnpd's `NATPMPPCPSupport`, one switch for NAT-PMP and the daemon's PCP server (a `%protected` parameter); PCP is the tr181-pcp service's `Enable`; a mapping's lease is its granted `Lifetime`, its host the third-party address (empty: the gateway itself).
- `DeviceHealth`: the load is `ProcessStatus.CPUUsage` (a percentage; no load average is published); memory is in KiB in the model (x 1024); a process has no terminal (``None``) and its `CPUTime` is milliseconds; a log line names no host (empty).
- `DeviceInfo`: an empty inventory `model` falls back to `ModelName`; an empty OUI or hardware version is ``None``.
- `DeviceLifecycle`: *method* names the reset channel; this family resets through its own session. The upgrade downloads into the image that is not active, activating it (the device reboots into it); the archive is the vendor configuration file, opaque to the contract, moved through a `file://` URL on the box.
- `DhcpClient`: *stateless* is not passed (the client's `RequestAddresses`/`RequestPrefixes` decide what it asks for); the observation pair is the host lever and raises (§9).
- `DnsForwarder`: the upstreams are rewritten in place (the static entries in table order take the upstreams in order; one added per upstream beyond them, alias `up<k>`, or the first free `up<j>` with j > k; the surplus deleted from the last), one step each, applied at once: a rejection leaves the steps before it; an override is a host entry whose alias is the name, with one address.
- `Firewall`: FORWARD rules land in the outbound custom chain (`Custom_Out`, LAN -> WAN forwarded traffic); the default policy is the custom level's one `DefaultPolicy`; a rule's position is its `Order`; a mapping's source is a host (`RemoteHost`), not a prefix. The rules take effect while the custom level is the active one (`Firewall.Config`/`PolicyLevel`; the driver does not switch it). One step per add, delete or set, applied at once: a rejection leaves the steps before it.
- `Firewall.set_dmz_host`: the driver keys its DMZ entry on the alias `dmz`
- `FirewallZones`: a target reads lower-cased (`ACCEPT` → `accept`); the store's zones are the image's, which the data-model plugin renders from its own levels.
- `HostFilter`: an entry blocked always is `AccessPolicy=Deny`; a scheduled block is `AccessPolicy=Allow` with the schedule's complement as access windows (the model schedules access, not blocks), one window per day and run, grouped by start and duration; read back, the blocked windows that share a start and end are the schedule (a block made of runs with different times reads as the first). The driver names an entry it adds `block-<mac digits>`. The entry's windows are rewritten in place in table order (one added per window beyond them, alias `s<k>`, or the first free `s<j>` with j > k), the policy set after them and the surplus deleted from the last after it, so a Deny entry turning Allow has its windows before the policy changes. One step per add, delete or set, applied at once: a rejection leaves the steps before it.
- `HostTable`: the attachment is the kind of `Layer1Interface` (a Wi-Fi SSID object or an Ethernet interface; anything else ``None``); the interface is the alias of the `Layer3Interface` IP interface; an empty host name is ``None``.
- `InterfaceDhcp`: options are written as the model's hexBinary `Value` (an INTEGER as four octets) and read back as ``HEX``. The options are rewritten in place: an option keeps the instance carrying its `Tag`, the others take the other instances in table order (their `Alias`, write-once, keeps the old `opt<tag>` label), one added per option beyond them (alias `opt<tag>`, or `opt<tag>-<j>` when taken), the surplus deleted from the last. A reservation's name is its static address's `Alias`, which the model makes write-once (tr181-dhcpv4 87c7f357 dhcpv4-manager-server-pool.odl `StaticAddress[]` `%unique %key %write-once string Alias`): a reservation keeps the instance named after it (`Chaddr`, `Yiaddr` rewritten in place), a new or renamed one is added (alias the name, or `res-<mac digits>`) and the instances no reservation names are deleted from the last after the adds — a renamed reservation is briefly two entries for one host, never none. Both tables read back in table order; one step each, applied at once: a rejection leaves the steps before it.
- `InterfaceDhcp.get_dhcp_leases`: `hostname` is empty (the client table names none) and `vlan_id` 0
- `L2Bridge`: the driver names each port it adds after the member; a port another manager added is listed under its alias. The management port is not a member. A new bridge has no management port until its interface is configured elsewhere. One step per add or set, applied at once: a rejection leaves the steps before it.
- `L2Bridge.get_members`: no STP state is published (``None``)
- `NetworkEndpoint`: the first IPv4 address of the interface
- `NetworkEndpoint`: the first IPv4 address of the interface
- `NtpConfig`: the list holds host names only (`prefer` is not stored: ``False``); the state's server, offset and last synchronisation are not published (``None``); every status but `Synchronized` and `Disabled` reads UNSYNCHRONISED.
- `PortStatus`: `Status` values other than `Up` read DOWN (DISABLED when `Enable` is false); `CurrentBitRate` 0 or -1 (no link, unknown) is ``None``.
- `SyslogConfig`: the driver owns the actions it names `remote<k>`; a write deletes them (from the last) and adds one per server, one step each; the roles are not stored (a server reads back with the event log role); the transport is UDP.
- `Tr069Client`: the passwords are never returned (``None``); one set per parameter, applied at once: a rejection leaves the sets before it.
- `UspAgent`: a write replaces the controller-1 lines of the factory-reset file (the other lines kept), then removes the agent's database so the file is read again: every value the agent stored at run time is reset; the controller's MQTT broker is `Device.MQTT.Client.1`. One step per shell command, applied at once: a step refused or unacknowledged leaves the steps before it (after the stop, the agent stays stopped).
- `UspAgent.get_controller`: an absent WebSocket path reads ``None``; a reply without the controller's endpoint, host, port, encryption setting, MQTT client reference or broker parameters is ``NoAcknowledgement`` naming the parameter (a value the agent prints, an empty one included, is returned as printed)
- `WanConnection`: one set per parameter, applied at once (§8 column 1): a rejection leaves the sets before it applied. The name keys every object of the stack: an image whose stack objects carry other aliases is not found (``KeyError``). The PPPoE credentials go to wan-manager's interface (`UserName`, `Password`, which override the PPP object's, §10 [3]), the service name to the PPP object. ``ipv6=None`` and ``WanIpv6Mode.DISABLED`` both write `IPv6Mode` `none` and read back as ``None``; ``SLAAC`` is wan-manager's `ppp6` (PPPoE only). The driver renders the static resolvers as `DNS.Client.Server` instances `<name>-dns<k>` (or the first free `<name>-dns<j>` with j > k; the connection's entries rewritten in place in table order, one added per resolver beyond them, the surplus deleted from the last) and the gateway as the router's `IPv4Forwarding` instance named after the connection; a write in another mode deletes those objects after its own sets (the resolvers from the last, then the route), so they do not stay enabled beside the lease's — a rejection partway leaves the new mode set and the objects before it deleted, the rest still enabled. The IP interface's first `IPv4Address` instance the static mode wrote is the interface's own, left to the new mode.
- `WanConnection.get_wan_state`: the uptime is the IP interface's `LastChange` while it is `Up` (the time in its current state); a DSL/DS-Lite `IPv4Mode` reports the IP interface's state; the provisioning mode is the configured families (`IPv4Mode`/`IPv6Mode` not `none`) while the IP interface is `Up` with an address or a delegated prefix, ``None`` otherwise (the `WanConnectionState` contract)
- `WanLinkAdmin`: the IP layer goes down, the layers beneath it (Ethernet, PPP) keep their own `Enable`; the setting is persistent (`%persistent`), so it survives a reboot
- `WifiBss`: the DTIM period is the radio's (`WiFi.Radio.{i}.DTIMPeriod`): a write changes it for every network on the radio; a mode outside the map keeps the model's spelling; a `MaxAssociatedDevices` of 0 reads as no limit (unverified: 0 lifts the limit). One step per add, delete or set, applied at once: a rejection leaves the steps before it.
- `WifiMesh`: the signal is the station's RCPI (`SignalStrength`, dBm = RCPI ÷ 2 - 110), the capacity its estimated downlink MAC rate; the band follows the parent radio's channel and operating class; the hop count walks `BackhaulDeviceID` up to the controller; a steer names the target agent's first BSS (`ClientSteering` has no disassociation- imminent argument).
- `WifiOnboarding`: *window_seconds* is not passed (the WPS walk time is the plugin's); the state is `WPS.PairingInProgress` (ACTIVE) or IDLE — no method, no time left and no outcome are published.
- `WifiRadio`: the transmit power is a percentage of the radio's maximum in the model (`TransmitPower`, -1 = auto): a dBm figure is written as the percentage of the maximum `getMaxTransmitPowerdBm(channel)` returns, rounded; a mode is written as the band's backward-compatible standards list up to it (`a,n,ac` for AC on 5 GHz); the country is the first two octets of `RegulatoryDomain` (written with the all-environments space). One set per parameter, applied at once.
- `WifiRadio.list_supported_channels`: a range `n-m` is expanded in steps of one channel on 2.4 GHz and of four (20 MHz) on 5 and 6 GHz
- `WifiRadio.set_bandwidth`: 320 MHz is written as `320MHz-1`
- `WifiRadio.get_dfs_state`: the time left in the check is not published (``None``)
- `WifiStations`: `associated_since` is now minus `ConnectionDuration`; the rates are the last data rates (kbit/s → Mbit/s); `ip_address` is ``None`` (the table names none; the host table joins it); a station is listed while `Active`.
- `WifiTransitions`: BSS-transition management is `MBOEnable` (pwhm publishes no separate 802.11v switch; MBO requires BTM); a "neighbour report request" from the AP is a remote (beacon) measurement request, `sendRemoteMeasumentRequest` — an AP does not send a Neighbor Report Request; a BTM request names one target with its operating class and channel, taken from the access point's `Neighbour` table.

**Column 2** (50 lines)

- the configuration store: a commit also applies whatever another session staged for the same configuration
- `AdminCredential`: an account is a `/etc/passwd` entry with uid 0
- `AutoPortMapping`: the lease file does not say which protocol created a mapping (`origin` ``None``); a lease's expiry is an epoch time, so the remaining time is that time less the device's clock (`date +%s`), ``None`` for a lease without expiry (0); the toggles leave miniupnpd's own `enabled` (the service) as it is.
- `AutoPortMapping`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `DeviceHealth`: the load is the kernel's one-minute average (`load[0]` ÷ 65536, no processor percentage); the processes are procd's service instances (a process procd does not manage is left out, no CPU time: zero, no terminal: ``None``); a log line carries no host name, so each entry takes the board's `hostname`.
- `DeviceLifecycle`: *method* names the reset channel; this family resets through its own session and does not read it. The upgrade keeps the configuration (no `-n`); the archive is `sysupgrade -b`'s tar.gz, opaque to the contract.
- `DeviceLifecycle.upgrade_firmware`: the driver renders the image path `/tmp/sysupgrade.bin`
- `DhcpClient`: *stateless* is not read — netifd's DHCPv6 client (`proto dhcpv6`) asks for what the interface's `reqaddress` / `reqprefix` options say
- `DnsForwarder`: an upstream is written `[/domain/]address[#port]` (the port only when it is not 53); `get_upstreams` returns the device's order, which the commit may change (design §8: a list re-ordered on commit), so the contract promises the set; a `server` entry with no address (`/lan/`, a local-only domain) is not an upstream and is left out.
- `DnsForwarder`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `DnsForwarder.list_host_overrides`: an entry naming several names (`/a/b/ip`) reads as one override per name
- `Firewall`: a rule's chain is its zones — `src '*'` (input), `src '*'` and `dest '*'` (forward), `dest '*'` (output); its action is `target` (ALLOW `ACCEPT`, DENY `DROP`, REJECT `REJECT`; LOG and ALERT are the unsupported case), its protocol `proto` (ICMP6 is `icmp`, ANY `all`), its ports `dest_port` (space-separated); an application match is the unsupported case. The driver names the sections it creates `rule_<name>`, `redirect_<name>` and `dmz`; a port forward is a `DNAT` redirect from the external zone (default `wan`) to `lan`, and its description is not stored (reads empty). A position is a `reorder` of the new section before the chain's rule at that position. A rule or chain that realises a host block (`host_block_<mac>`) is `host_filter`'s: removing it, flushing its chain or setting that chain's default policy is the unsupported case.
- `Firewall`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `FirewallZones`: the driver names the zone sections it creates `zone_<name>` and the forwarding sections `fwd_<src>_<dst>`; a zone's networks are its `list subnet`; the actions are written upper case (`ACCEPT`); a forwarding section allows only, so a zone pair's `drop` or `reject` is the absence of the forwarding (the source zone's `forward` default then decides) and every listed policy reads `accept`.
- `FirewallZones`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `HostFilter`: the block is a rule section named `host_block_<mac without colons>` (its `name` too), `src 'lan'`, `dest 'wan'`, `src_mac` canonical, `target 'REJECT'`; a schedule is the rule's `weekdays` (`Mon` … `Sun`), `start_time` and `stop_time` (`hh:mm:ss`, the device's local time); the rule shows in `firewall.list_rules` (FORWARD) and the firewall driver refuses the writes that would disturb it. A schedule of every day is written with all seven days. An `end` before `start` is written as given (unverified: the page does not say how fw4 reads a window past midnight).
- `HostFilter`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `HostTable`: a host without a lease has no `hostname`; a host seen only in the neighbour table or the leases has no `attachment` (``None``: wired is not published as such); a host is `active` when it is a station or a neighbour entry not FAILED/INCOMPLETE; the station lists are left out when the wireless status is unreadable
- `InterfaceDhcp`: the pool is written as `start` (the first address's offset in the subnet) and `limit` (its size); ``None`` bounds are the whole subnet (offset 1, every host address but the broadcast); the lease time is written in seconds and read in any of the units dnsmasq accepts; the DNS servers are DHCP option 6 (`list dhcp_option '6,…'`) and every other option is `code,value` with its type inferred on read (an address is IP, anything else TEXT); a static lease belongs to the interface whose subnet holds its address, and the driver names the host sections it creates `host_<interface>_<mac>`.
- `InterfaceDhcp`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `InterfaceDhcp.get_dhcp_leases`: `vlan_id` is 0 (neither source names a tag); a hostname dnsmasq prints as `*` reads empty; the bus reply's field names (`device` → `leases` → `mac`, `address`, `hostname`) are unverified (the page names the method, not its reply)
- `L2Bridge`: a wireless network joins a bridge through its `network` option, which names the netifd interface on the bridge (the first such interface); the driver names the bridge sections it creates `br_<name>`; spanning tree is the Linux bridge's (`stp '1'`), so the only mode is STP and RSTP / MSTP are the unsupported case.
- `L2Bridge`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `L2Bridge.get_members`: a member the kernel does not list (down, or not yet attached) has no state (``None``); `link_up` is the `LOWER_UP` flag
- `NetworkEndpoint.get_ipv4_addr`: the bridge's device name comes from the inventory (`lan_interface`)
- `NtpConfig`: the list holds host names only; `prefer` is not stored (``False`` on read).
- `NtpConfig`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `PortStatus`: a port is a device of type "Network device" (bridges, VLAN devices and wireless interfaces are left out); a port without a carrier reports no `speed`, so its speed is ``None`` and its duplex AUTO; `up` false (administratively down) is DISABLED
- `SyslogConfig`: the system section holds one remote destination, so a list of more than one is the unsupported case (per value); the transport is written `udp`; every destination receives every message (role EVENT_LOG on read).
- `SyslogConfig`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `Tr069Client`: the passwords are never returned (``None``); `enabled` is the `cpe` section's `enable` (unverified: the option table names it for the client, not the ACS); a write ends with the client's own `reload` command, not `reload_config`.
- `Tr069Client`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `WanConnection`: the driver renders the tag as a device section `<name>_vlan` named `<base>.<vid>`, and the IPv6 part as the companion interface `<name>6`; an IPv6 part of ``None`` deletes that companion. Booleans are written `1`/`0`.
- `WanConnection`: a rejected write's steps stay staged in its own change-file path and are never committed (the as-found connection stands); a commit also applies whatever another session staged in the default change path and leaves it staged there (source-only, `_uci` module docstring).
- `WanConnection.get_wan_connection`: the stored `password` is never returned (``None``)
- `WanConnection.list_wan_connections`: a WAN connection is an interface the `wan` zone lists; the IPv6 companion (`proto dhcpv6`) is reported as its connection's IPv6 part, not as a connection
- `WanConnection.get_wan_state`: netifd publishes the granted lease time (`data.leasetime`), not its remaining part; the remaining time is the lease time less the time since the interface came up modulo the lease time — a renewal before expiry restarts the lease earlier, so the figure is an upper bound. The status maps `up` → CONNECTED, `pending` → CONNECTING, otherwise DISCONNECTED (netifd publishes no authentication phase)
- `WanLinkAdmin`: the running state changes, the stored configuration does not (`ifdown` leaves the interface's `auto` option as it is), so a reboot brings the interface up again
- `WifiBss`: the security mode is `encryption` (`none`, `owe`, `psk2`, `sae`, `sae-mixed`) and the EAP modes are the unsupported case (no RADIUS client composed); MFP is `ieee80211w` (`0`/`1`/`2`); hidden is `hidden`; the access list is `macfilter` (`disable`/`allow`/`deny`) with `list maclist` (canonical MACs); the BSSID is hostapd's `get_status` reply for a running network and empty for one that is not.
- `WifiBss`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `WifiOnboarding`: hostapd opens a fixed two-minute push-button window, so *window_seconds* is not sent for a push-button start; the state carries no remaining time (``None``)
- `WifiOnboarding.get_wps_state`: hostapd's status is the push-button session's; a PIN session reads through `last_wps_result` only (method ``None``); an overlap is FAILED
- `WifiRadio`: the width and the PHY mode share one option, `htmode` (`HE80` = 802.11ax at 80 MHz): a mode write keeps the width, a width write keeps the family (HE when none); `NOHT` is the legacy rates of the band; the modes a radio operates are its family and every older one its band carries (a 5 GHz HE radio: a, n, ac, ax). The transmit power is the configured `txpower` (dBm; absent: the live figure). The non-occupancy list is not published (always empty).
- `WifiRadio`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `WifiRadio.get_dfs_state`: the non-occupancy list is not published (empty)
- `WifiStations`: hostapd publishes no client address, connection time, SNR or retry count (``None`` / 0); a station whose driver read failed has no signal or counters (0)
- `WifiTransitions`: 11r is `ieee80211r` with `ft_over_ds` (`0` = over the air); a write of `ieee80211r` alone leaves `mobility_domain` to the default (from the SSID); band steering is usteer's, not a member (design §6).
- `WifiTransitions`: a rejected write's steps stay staged in its own change-file path and are never committed; a commit also applies whatever another session staged in the default path and leaves it staged there (source-only, `_uci` module docstring).
- `WifiTransitions.get_transition_config`: `ft_over_ds` absent reads as over the air (``False``)
- `WifiTransitions.send_neighbor_report_request`: an access point sends a radio-measurement (beacon) request; the station's report of the networks it sees is the answer hostapd keeps

**Column 3** (35 lines)

- the session: one set per step, applied by the owning component at once: a rejection leaves the
- `AdminCredential`: the account is found by its `Username`; the password is never read back (the model returns no stored secret).
- `AutoPortMapping`: every IGD mapping's origin is UPnP IGD; the remaining lease is the lease less the time since the entry's last update (a lease of 0 is none); the internal host is the entry's address.
- `DeviceHealth`: the load is `ProcessStatus.CPUUsage` (a percentage; no load average); memory is in KiB in the model (x 1024); a process has no terminal (``None``) and its `CPUTime` is milliseconds; a log entry names no host (empty) and no facility (``priority`` ``None``: its `Level` is a severity alone).
- `DeviceInfo`: an empty inventory `model` falls back to `ModelName`; an empty OUI or hardware version is ``None``.
- `DeviceLifecycle`: *method* names the reset channel; this family resets through its own session. The upgrade fetches `<URL directory>/<image name>` and reboots into it; a checksum is the unsupported value (no checksum parameter).
- `DeviceLifecycle.export_configuration`: the archive is the syscfg store's `name=value` lines, opaque to the contract
- `DhcpClient`: the release is the device-control `ReleaseWan` trigger, the box's one WAN lease whatever client *interface* names (the driver checks the client exists); *stateless* is not passed (the client's `RequestAddresses`/`RequestPrefixes` decide). The observation pair is the host lever and raises (§9).
- `DnsForwarder`: Utopia's `prepare_hostname` rewrites the host file on every DNS (re)start, so an override lasts until then; the upstreams are written as one set per parameter, applied at once.
- `Firewall`: a rule is a policy named after it (`Alias`) with one `BlockedApplication`; every policy blocks always (`Schedule.AllDay`); blocked attempts are logged in `InternetAccess.LogEntry` (a rule reads `log` true, `False` is the unsupported value); the host filter's policies (`host-block-…`) are not rules (a rule may not take that prefix). A mapping's source is one host (`RemoteHost`). One step per add, delete or set, applied at once: a rejection leaves the steps before it.
- `FirewallZones`: `lan` accepts in all three directions; `wan` drops input and forwarding at every preset but `None` (accept), accepts output and masquerades; the interfaces are named `lan` and `wan`, no networks.
- `HostFilter`: an always block is `Schedule.AllDay`; a scheduled block is the schedule's days (`Include<Day>`) and window (`StartTime`/`EndTime`, `hh:mm`) with `AllowAccess` false; the policy names one host. One set per parameter, applied at once.
- `HostTable`: the MAC reads canonical (the table prints it upper-cased); the attachment is the kind of `Layer1Interface` (a Wi-Fi SSID object or an Ethernet interface; anything else ``None``); the interface is the alias of the `Layer3Interface` IP interface; an empty host name is ``None``.
- `InterfaceDhcp`: options are written as the model's hexBinary `Value` (an INTEGER as four octets) and read back as ``HEX``. The options and static addresses are rewritten in place: an item keeps the instance that carries its key (`Tag`, `Chaddr`), the other items take the other instances in table order with their `Alias` set (writable in CcspPandM TR181-USGv2.XML), one added per item beyond them, the surplus deleted from the last; both read back in table order. One step each, applied at once: a rejection leaves the steps before it. A name moved to another host in one write sets an `Alias` another instance still carries until that one's own set (unverified: whether CcspPandM refuses a duplicate `Alias`; TR-181 makes it a unique key). A reservation without a name gets the alias `res-<mac digits>`; the pool's MACs read canonical (the model prints them upper-cased).
- `InterfaceDhcp.get_dhcp_leases`: `vlan_id` is 0; the MAC reads canonical
- `L2Bridge`: the driver names each port it adds after the member; a port another component added is listed under its alias. The management port is not a member. One step per add or set, applied at once: a rejection leaves the steps before it.
- `L2Bridge.get_members`: no STP state is published (``None``)
- `NetworkEndpoint`: the first IPv4 address of the interface
- `NetworkEndpoint`: the first IPv4 address of the interface
- `NtpConfig`: the slots hold host names only (`prefer` is not stored: ``False``); a write sets every slot (the unused ones empty), one set each, applied at once; the state's server, offset and last synchronisation are not published (``None``); every status but `Synchronized` and `Disabled` reads UNSYNCHRONISED.
- `PortStatus`: `Status` values other than `Up` read DOWN (DISABLED when `Enable` is false); a `CurrentBitRate` of 0 (no link) is ``None``; the duplex is the configured `DuplexMode` (`Auto` reads AUTO — the negotiated duplex is not published).
- `SyslogConfig`: the roles are not stored (a server reads back with the event-log role); the transport is UDP; one set per parameter, applied at once.
- `Tr069Client`: the passwords are never returned (``None``); one set per parameter, applied at once: a rejection leaves the sets before it.
- `UspAgent`: a write replaces the controller-1 lines of the reset file (the other lines kept), then removes the agent's database so the file is read again: every value the agent stored at run time is reset; the controller's MQTT broker is `Device.MQTT.Client.1`. One step per shell command, applied at once.
- `WanConnection`: one set per parameter, applied at once (§8 column 3): a rejection leaves the sets before it applied. The static address, mask and gateway are the device-control object's (`WanStaticIPAddress`, `WanStaticSubnetMask`, `WanStaticGatewayIP`, one set per box, §10 [1]); the static resolvers are `DNS.Client.Server` entries the driver names `<name>-dns<k>` (or the first free `<name>-dns<j>` with j > k; the connection's entries rewritten in place in table order, one added per resolver beyond them, the surplus deleted from the last). The 802.1p priority is the interface's first `Marking` (`-1`: no mark, unverified). ``ipv6=None`` and ``WanIpv6Mode.DISABLED`` both write `IP.Mode` `IPv4 Only` and read back as ``None``.
- `WanConnection.get_wan_state`: the uptime is the IP interface's `LastChange` while it is `Up`
- `WanLinkAdmin`: the IP layer goes down, the WAN manager keeps the interface selected (its `Selection.Enable` is not changed)
- `WifiBss`: `create_bss` claims the band's first unnamed, disabled slot and names it (the SSID object and its access point get the network's alias); `delete_bss` disables the slot and clears both aliases. The DTIM period is the radio's (`X_CISCO_COM_DTIMInterval`, a write applies it to every network on the radio). A write sets its parameters, then `WiFi.ApplyAccessPointSettings` (the access-point apply flag, its own step; a radio parameter adds `WiFi.ApplyRadioSettings`): a rejection leaves the sets before it pending until the next apply. A `MaxAssociatedDevices` of 0 reads as no limit; MACs read canonical (the tables print them upper-cased).
- `WifiMesh`: the signal is the RCPI (`SignalStrength`, dBm = RCPI ÷ 2 - 110), the capacity the last downlink data rate (kbit/s → Mbit/s); the parent is `BackhaulALID`, the hop count walks it up to the controller; the controller's state reads enabled while it publishes a `ControllerID`; a steer is a mandate (`RequestMode=Steering_Mandate`) to the target agent's first BSS, on that BSS's radio class and channel.
- `WifiOnboarding`: *window_seconds* is not passed (the WPS walk time is the component's); the state is ACTIVE (push-button) while `X_CISCO_COM_ActivatePushButton` reads true, else IDLE — no PIN session, time left or outcome is published.
- `WifiRadio`: a write sets its parameters, then `WiFi.ApplyRadioSettings` (the radio apply flag, its own step): a rejection leaves the sets before it pending until the next apply. A mode is written as the band's backward-compatible standards up to it; the country is `RegulatoryDomain`'s first two octets on every radio.
- `WifiRadio.get_bandwidth`: `Auto` has no width (20 is read); `80_80MHz` reads 80
- `WifiStations`: no association time is published: `associated_since` is the time of the read; the rates are the last data rates (kbit/s → Mbit/s); `ip_address` is ``None`` (the host table joins it); a station is listed while `Active`; MACs read canonical (the table prints them upper-cased).
- `WifiStations.disconnect_station`: *reason_code* is not passed (the parameter takes the MAC only)
- `WifiTransitions`: 802.11k is `X_RDKCENTRAL-COM_NeighborReportActivated` (neighbour reports), 802.11v `X_RDKCENTRAL-COM_BSSTransitionActivated`; a deauthentication is the forced disassociation (`ClientForceDisassociation`), its reason code not passed.

**Column 4** (28 lines)

- the session: one action per step, applied at once: a rejection leaves the steps before it
- `AutoPortMapping`: `SetConfig` carries the media-server switch too, which the driver writes as it read it; the table is the IGD's whole mapping table (the administrator's forwards included, without an origin); a `LeaseDuration` of 0 (no lease) reads ``None``; an empty description reads ``None``.
- `DeviceHealth`: a log line is `<date> <time> <message>`: the timestamp is the first two words as the device prints them, no host (empty), no tag and no priority (``None``).
- `DeviceInfo`: an empty inventory `model` falls back to `ModelName`; an empty OUI or hardware version is ``None``.
- `DeviceLifecycle`: *method* names the reset channel; this family resets through its own session. The upgrade is the manual update from the image's URL (the device fetches it); a checksum is the unsupported value (no checksum argument). The archive is the device's encrypted export, encrypted with the driver's own password; an archive from another tool needs that tool's password (not part of the contract).
- `DhcpClient`: *interface* names the one connection.
- `DnsForwarder`: the box answers each LAN host's name itself, so every named host lists as an override; removing one sets the host's name to the empty string (the family's own name for the host returns).
- `DnsForwarder.get_upstreams`: the connection's resolvers stand for the forwarder's upstreams (port 53, no domain)
- `Firewall`: a TCP-and-UDP forward is two entries (`AddPortMapping` once per protocol) and reads back as one when both carry the same name and ports; the forward's name is its `PortMappingDescription`; a source restriction and an external interface are refused (the entry has `RemoteHost` only); `set_port_mapping_enabled` re-adds the forward with the new `Enabled` (the IGD semantics of an add on an existing triple); a profile reads as a FORWARD rule named after the profile, `allow` for the standard and the unrestricted profile and `deny` otherwise, any protocol, address and port.
- `HostFilter`: the host is reached by the address the host table holds for its MAC; a profile of type `Standard` or `Unrestricted`, or one without a timetable, is no block; one action per step, applied at once: a rejection leaves the steps before it.
- `HostFilter.block_host`: a scheduled block over a block at all times is two actions, the profile first: a rejected disallow clear leaves the host in the profile and still disallowed at all times (blocked throughout, never unblocked between the steps)
- `HostTable`: no IPv6 addresses per host (empty); a HomePlug host's attachment is ``None`` (outside the set); no interface name is published per entry (``None``; the port is in the per-host entry by address, which `l2_bridge.get_members` reads); MACs read canonical.
- `InterfaceDhcp`: the reservations the pool reports in aggregate (`ReservedAddresses`, addresses without MACs) read as none; the options read back as ``IP``; one action per step, applied at once: a rejection leaves the steps before it.
- `InterfaceDhcp.get_dhcp_leases`: `vlan_id` is 0; the guest network's leases are listed beside the LAN's
- `L2Bridge`: `link_up` is ``True`` for a member an active host sits on; no spanning tree (`stp_state` ``None``); a host on another medium is not a member.
- `NetworkEndpoint`: the address is the router the DHCP server hands out (`IPRouters`), the box's own LAN address
- `NtpConfig`: the `prefer` flag is not stored (the first slot is the first server); an empty slot is no server.
- `PortStatus`: no error or discard counters are published (all 0); `MaxBitRate` is the rate (`Auto` or a non-number reads ``None``); the WAN's rate is not read (``None``); `PhysicalLinkStatus` other than `Up` reads DOWN.
- `Tr069Client`: `enabled` reads ``True`` while an ACS URL is configured (GetInfo publishes no enable); an empty user name reads ``None``; one action per step, applied at once: a rejection leaves the steps before it.
- `UspAgent`: a write adds the controller (`AddUSPController`, every access right granted, no MQTT topics, no credentials), then deletes the other entries from the last to the first: a rejection of the add leaves the table as found, a rejection of a delete leaves two controllers; the agent's endpoint identifier is the TR-369 `os::` form built from DeviceInfo (`os::<OUI>-<ProductClass>-<SerialNumber>`).
- `WanConnection`: an IP connection reads ``WanMode.DHCP`` (its addressing method is not published); a write makes the connection routed (`IP_Routed`: the gateway's connection, never a bridge); one action per step (`SetConnectionType`, then `SetUserName` and `SetPassword`), applied at once: a rejection leaves the steps before it.
- `WanConnection.get_wan_connection`: a connection with an IPv6 address reads ``WanIpv6Mode.DHCPV6_PD`` (the IPv6 addressing method is not published)
- `WanConnection.get_wan_state`: the provisioning mode is derived — IPv4 when the status is Connected with an address, IPv6 when the IGD names an IPv6 address
- `WifiBss`: `vlan_id` and `max_clients` read ``None``, the DTIM period reads 1 and the captive portal off (none is published); the MFP mode reads REQUIRED for WPA3 and OWE, OPTIONAL for the mixed mode, OFF otherwise (not published); `OWETrans` reads OWE and `WPAand11i` WPA2-PSK; an SSID is applied at once with a Wi-Fi restart (§8 column 4); one action per step, applied at once: a rejection leaves the steps before it.
- `WifiMesh`: this device is the master node; an agent is a node with `is_meshed` true and the `slave` role; its parent is the other end of its backhaul link; the signal is the link's RCPI (dBm) at the agent's end, the capacity its current rate towards the agent (kbit/s / 1000); a wired backhaul has no link record (``None``).
- `WifiOnboarding`: WPS reads enabled unless its status is `off`; the `err_*` statuses other than the timeout read FAILED; no remaining time is published (``None``); the window length is the device's own (*window_seconds* is not passed).
- `WifiRadio`: the radio's enable is its normal access point's `Enable`; the channel `0` (auto) reads as given; `get_mode` is `Standard`, "Only the highest of the active modes"; a width of 80+80 MHz reads 160.
- `WifiStations`: `X_AVM-DE_SignalStrength` is a 0-100 figure with no published unit, reported as -100 + strength/2 dBm; `X_AVM-DE_Speed` (Mbit/s) is both rates; the association time, the byte, packet and retry counters are not published (0); no SNR (``None``); no capability flags.

**Column 5** (32 lines)

- the session: there is no commit: each request applies at once, so a rejection in a multi-step
- `AdminCredential`: an administrator is a user of group `full`
- `AutoPortMapping`: a mapping is a dynamic `dstnat` rule whose comment the service writes `upnp <host>: <description>`; its origin is UPnP IGD; no lease time is published (``None``).
- `DeviceHealth`: the CPU figure is `cpu-load` (all cores, percent; no load average, ``None``); used memory is the total less the free; a log entry's tag is its `topics`, its host the router's identity, its priority ``None``.
- `DeviceInfo`: the manufacturer is `/system resource` `platform` (`MikroTik`); the software version is `version` without its channel (`7.16 (stable)` → `7.16`); the OUI is the first three octets of the first Ethernet port's MAC (no named field); no hardware revision is published (``None``).
- `DeviceLifecycle`: *method* names the reset channel; this family resets through its own session and does not read it. The console's reboot confirmation ("Reboot, yes? [y/N]") does not arise on the REST route: the POST runs the command (unverified). The reset keeps the defaults (`no-defaults=no`) and skips the backup; the package is fetched into the root directory under its own file name and installed at the reboot; the configuration is the `.rsc` export script (`/export file=tp-export`) pulled over SFTP, opaque to the contract; a checksum is the unsupported value (the fetch tool checks no digest).
- `DhcpClient`: *stateless* is not read — the DHCPv6 client asks for what its `request` property says (`address`, `prefix`)
- `DnsForwarder`: the upstreams are one comma list written in one `set`; an upstream on a port other than 53, or serving one domain only, is the unsupported value (`servers` lists addresses only); `get_upstreams` returns the configured `servers` in the device's order (the contract promises the set), not the `dynamic-servers` a client added. A host override is a static record of type A (an IPv4 address) or AAAA; the dynamic records (`D` flag) and the records of other types are not overrides.
- `Firewall`: a rule is named by its `comment`; ALLOW / DENY / REJECT / LOG are `accept` / `drop` / `reject` / `log`, another action reads as its own word; ANY is no `protocol`; a source or destination of `0.0.0.0/0` is no address match. The dynamic rules (Kid Control's, a host block's) are not listed. A port forward is a `dstnat` `dst-nat` rule named by its `comment`, from the `WAN` interface list unless an external interface is named; its description is not stored (reads empty); TCP+UDP is the unsupported value (a rule matches one protocol). The DMZ host is a `dstnat` `dst-nat` rule from the `WAN` list without a port, named `dmz`, kept after the port forwards (a forward added later is placed before it). A position is `place-before` the chain's rule at that position.
- `FirewallZones`: a zone's default input and forward actions are those of the first catch-all drop or reject rule that matches the list (`in-interface-list=<zone>` or `!<other>`), else `accept` (a chain accepts what no rule drops); the output default is `accept`; masquerade is a `srcnat` masquerade rule with `out-interface-list=<zone>`; networks and MSS clamping are not read (empty, False).
- `HostFilter`: a block is a profile named `block-<mac without colons>` holding the allowed times — every weekday empty for a block at all times; for a schedule, the block's days allow the complement of its window and the other days the whole day — and a device entry for the MAC with `user=<profile>`; a disabled block is a disabled profile. A window inside a day, or one past midnight on some days only, is the unsupported value (a weekday holds one allowed range). On read, any device entry's profile is a block; one whose allowed times are not one weekly block is ``NoAcknowledgement``. The router applies a profile as dynamic filter rules (not listed by ``firewall``).
- `HostTable`: the address is the lease's, else the ARP entry's; the name is the lease's `host-name`, else the neighbour's `identity`; the interface is the registration entry's (the network), else the ARP entry's; a registered host is WIFI, any other's attachment ``None`` (the menus do not say a host is wired); a host is active while it is registered, its ARP entry is complete or its lease is bound; no IPv6 address is read (empty).
- `InterfaceDhcp`: the driver names the server `dhcp-<interface>`, its pool `dhcp-<interface>`, its options `<interface>-option<code>` and the relay `relay-<interface>` when it creates them; the pool is the bounds less the reserved ranges as one comma list of ranges, read back as the first and last address and the gaps between them (their comments empty); the lease time is written as an interval; the DNS servers are the network's `dns-server`. An option's value is written in the console's form (a string quoted, hex `0x…`) and its type inferred on read (quoted: TEXT, `0x`: HEX, digits: INTEGER, otherwise IP). A static lease is a lease of the server whose `comment` is the reservation's name. One request per item, no commit: a rejection leaves the requests before it applied.
- `InterfaceDhcp.get_dhcp_leases`: `vlan_id` is 0 (a lease names its server, not a tag); a lease not `bound` is left out
- `L2Bridge`: a member's kind is read from the interface menus (a `/interface wifi` item is a WIRELESS_NETWORK, anything else a PORT); `protocol-mode=none` reads ``None``; a port's STP state is its `forwarding` / `learning` flags (an inactive port DISABLED, else BLOCKING), ``None`` on a bridge without spanning tree.
- `L2Bridge.delete_bridge`: the bridge's ports go with it (the router removes them)
- `NetworkEndpoint.get_ipv4_addr`: the bridge's name comes from the inventory (`lan_interface`), the defconf `bridge` when it names none; an interface the device does not have is ``KeyError``
- `NtpConfig`: the servers are `/system ntp client servers` items (the old ones removed from the last to the first, then the new added, then the client enabled — disabled for an empty list); *prefer* is not stored (False on read); the state's offset and time of the last synchronisation are not read (``None``).
- `NtpConfig.get_sync_state`: `stopped` or a disabled client is DISABLED, `synchronized` SYNCHRONISED, anything else UNSYNCHRONISED
- `PortStatus`: a port is an `/interface ethernet` item (bridges, VLANs and wireless interfaces are left out); a disabled port is DISABLED without a monitor read; a port without link reports no `rate` (speed ``None``, duplex AUTO); the error and discard counters are not read (0)
- `SyslogConfig`: the driver names its actions `syslog<n>` (1-based) and routes the `info` topic to each; a destination is a `target=remote` action some rule uses (an action with the unset address `0.0.0.0` is none); every destination receives every routed message (role EVENT_LOG on read); the transport is the action's default (UDP). A write updates the driver's actions in place, adds the missing ones with their rules, then removes the surplus (their rules first), one request each.
- `Tr069Client`: "connected" is `status=running` with an empty `last-session-error`; the passwords are sensitive properties the print leaves out (``None``); the device identifier is `OUI-ProductClass-SerialNumber` from the first Ethernet MAC's OUI, the RouterBOARD `model` and `serial-number` (unverified: the page does not state the identifier the client sends); the client's log lines are the memory log's entries whose topics name `tr069` (unverified: the topic).
- `WanConnection`: the driver names the tag interface `<name>-vlan` and labels its DHCP client, address and default route with `comment=<name>`; a mode change removes the other modes' objects first, then adds the new one, one request each (no commit: a rejection leaves the requests before it applied, the connection possibly without an object). An IPv6 part of ``None`` removes the IPv6 companion; on read, no companion is ``None`` (`DISABLED` is never read). The PPPoE password is never returned.
- `WanConnection.get_wan_connection`: the stored `password` is never returned (``None``)
- `WanConnection.list_wan_connections`: a WAN connection is a PPPoE client, or a DHCP client or address labelled with a `comment`, on a member of the `WAN` interface list or a VLAN over one
- `WanConnection.get_wan_state`: a DHCP lease publishes no connection uptime (``None``); a PPPoE session publishes no lease (``None``) and its resolvers are `/ip dns` `dynamic-servers`, which every client adding peer DNS shares; a static connection is CONNECTED while its address is enabled and valid. The words map: `bound` / `connected` → CONNECTED, `searching` / `requesting` / `renewing` / `rebinding` / `dialing` / `connecting` → CONNECTING, `authenticating` → AUTHENTICATING, anything else → DISCONNECTED
- `WanLinkAdmin`: the interface the connection sits on is disabled (the PPPoE client itself, else the WAN port or its VLAN), so every other object on that interface goes down with it; the disabled flag is stored in the configuration and survives a reboot
- `WifiBss`: the security modes map onto `security.authentication-types` (WPA3-SAE is `wpa3-psk`; a mixed mode is both types); the EAP modes use the router's `/radius` entries, so `radius_server_name` reads ``None`` (a named server is the unsupported value); MFP maps onto `security.management-protection` (OFF `disabled`, OPTIONAL `allowed`, REQUIRED `required`); no client limit is written as the default 1000 and 1000 reads ``None``; no captive portal is published (always off). The passphrase is a sensitive property the print leaves out. The access list holds one catch-all entry per network (no `mac-address`) whose action carries the mode — `reject` ALLOW, `accept` DENY, disabled or absent DISABLED — and an entry per MAC with the mode's action (`accept` / `reject`), placed before the catch-all.
- `WifiMesh`: the controller's MAC is the first Ethernet port's; a CAP is its `base-mac`.
- `WifiOnboarding`: the window is the package's fixed two minutes; *window_seconds* is not sent.
- `WifiRadio`: the PHY mode and the band share `channel.band` (`5ghz-ax`): the modes a radio operates are the band's own and every older one it lists (`5ghz-ax`: a, n, ac, ax); a mode write keeps the band; 802.11b alone is no band value. The width is the widest of `channel.width`'s set (`20/40/80mhz` → 80; `80+80` → 160). The channel is written as its centre frequency (`channel.frequency`). The transmit power is the configured limit (`configuration.tx-power`, dBm). The country is the package's country name, written on every radio (one request each) from the driver's table of ISO 3166-1 codes; a code outside the table is the unsupported value.
- `WifiStations`: `associated_since` is now less the entry's `uptime`; the rates are the leading figure of `tx-rate` / `rx-rate` (`866.6Mbps-80MHz/2S/SGI` → 866.6); `bytes` and `packets` are read as the pair `tx,rx`; the table publishes no SNR (``None``), no retry count (0), no station address (``None``) and no capability flags. A disconnect removes the entry (the client re-associates unless kept out); *reason_code* is not sent (the command takes none).

## 9. Verification

Stage 4 verifies this design statically and shape-only, as the sibling
designs were: one reference driver per column in the private reference
corpus, each a driver of the corpus's plugin shape with a `source:`
line per method, pinned to the design PR's head, under the corpus's
`conformance` check and strict type checking. No live device is driven.
Columns are named by their position in §2.

### What each reference driver must show

- **Column 1 (trigger family 1):** every core member realised through the
  data model, with the configuration store beneath it for the zone reads
  (R30) and the inform trigger (R52); two tiers implemented (mesh through
  the controller's data model, the controller side in part: `remove_agent`
  and the backhaul band and channel raise, backhaul health in part; USP
  through the agent's own files), voice absent (R54–R55 ✗ at stage 4). The
  TR-069 route is decided (§6, verification items): the data-model object for
  `set_acs` / `get_acs`, the client's bus object for `force_inform` and
  `is_tr069_connected`, recorded in the review record.
- **Column 2 (trigger family 2):** every core member realised through the
  configuration store and the bus, with the staged-commit failure outcome
  stated, except the three documented per-method unsupported cases on this
  trigger column: `info.manufacturer` and `info.serial_number` (R39 ◐, the
  board read publishes neither) and `ntp.get_sync_state` (R44 ◐), listed
  under Stated risks; the three access-point bus methods the wiki leaves undocumented
  cited as source-only (R27, R28); no tier
  satisfied: voice is ✗ (R54–R55, the PBX publishes no operation a member
  calls), the mesh has no controller (R56–R57 ✗; R58's plain-AP roaming has
  no member to carry it) and the USP tier is absent (R53 ✗).
- **Column 3:** every core member realised through the data-model tool,
  with the apply-parameter step named for the Wi-Fi writes and the shell
  store cited for the three "shell only" cells (R16, R48, R49);
  `tr069_client.force_inform` raises (R52 ◐, no trigger published); the
  `source:` lines beside the reference build's component list (§6,
  verification items): R3–R4 ◐ (no PPP manager in the build); the mesh tier
  implemented on the family's mesh build variant (topology, backhaul health
  and steering map, the six controller-side configuration members raise);
  USP implemented through the agent's file; voice, installed with its
  data-model version unverified, holds the tier on two columns only and is
  staged with it.
- **Column 4:** the read-rich, write-narrow column: every core member
  present, with the thirteen ✗ cells raising `NotSupportedError` and the
  twenty-six ◐ cells mapped with their limit or raising for the part the
  column lacks (R1 mode changes, R5, R9, R13, R15, R17, R18, R27, R29, R30,
  R33, R41, R43, R58 raise; R2, R3, R6, R7, R10, R11, R12, R16, R19, R20,
  R21, R22, R23, R28, R31, R34, R36, R37, R40, R44, R47, R52, R53, R55, R57
  map or raise in part; `force_inform` and `get_sync_state` raise, and so do
  the PIN members, `get_tx_power`, `get_country` and `get_dfs_state`); the
  mesh tier implemented from the topology JSON behind the session-ID login
  (backhaul health in part; every controller-side write and steering raise);
  the USP tier implemented from the service document; voice (SIP accounts at
  ✓, FXS hook state unpublished) staged with its tier. No white-box extension
  satisfied.
- **Column 5:** every core member realised through the management API
  (CLI or REST; §8 names the acknowledgement of each); the six ✗ cells raising
  (R17, R53, R54, R55, R57, R58) and `force_inform` raising (R52 ◐); the
  mesh tier implemented in part from the controller's access-point list
  (topology without backhaul links and the controller switch; backhaul
  health and steering raising); the voice and USP tiers absent; the `wifi`
  package cited per model for the Wi-Fi cells.

### Reference-driver expectations per tier

| Tier | Column 1 | Column 2 | Column 3 | Column 4 | Column 5 |
| --- | --- | --- | --- | --- | --- |
| `voice` (`VoiceGateway`; `tier-staged`) | absent (R54–R55 ✗) | absent (R54–R55 ✗) | evidenced (installed; data-model version unverified) | evidenced (`hook_state` unpublished) | absent (R54–R55 ✗) |
| `mesh` (`WifiMesh`) | implemented; controller side in part (`remove_agent`, backhaul band and channel raise); backhaul health in part (R57 ◐) | absent (R56–R57 ✗; R58 is plain-AP roaming, no member) | implemented on the mesh build variant; the six controller-side configuration members raise | implemented; every controller-side write and steering raise (R58 ✗) | implemented in part: topology without backhaul links and `set_enabled`; backhaul health (R57 ✗) and steering (R58 ✗) raise |
| `usp` (`UspAgent`) | implemented | absent (R53 ✗) | implemented | implemented | absent (R53 ✗) |

As built at stage 4: the voice tier is staged (two columns evidence it, so
it is in no driver); the mesh tier is on columns 1, 3, 4 and 5 and the USP
tier on columns 1, 3 and 4. A column whose driver does not satisfy a tier
registers under `cpe_gateway` only; a column that satisfies a tier in part implements the tier with the
documented per-method unsupported cases, as a core member with a ◐ cell
does.

### Stated risks — the nominal ◐ cells and the trigger-column gaps

These cells support an operation in name only (the family lists or packages
something, but publishes no operation a driver can call), or leave a core
member unsupported on a trigger column. Each is a stage-4 verification item
with its consequence named; a flip reshapes nothing in this design, only the
cell, the driver and the manifest row's Outcome. The arithmetic counts a
flipped cell as ✗ and applies §6's rule: a tier stays built while a majority
supports its defining operation, a member below the majority becomes a
per-column unsupported case inside the tier.

| Cells | What the cell rests on | If stage 4 finds no operation |
| --- | --- | --- |
| R54–R55, column 1 | a voice plugin repository that publishes no parameters | cells flip to ✗; voice keeps columns 2, 3 and 4 (three of five) and stays built; the column-1 driver raises. **Stage 4: flipped** (the default branch publishes no parameter) |
| R54–R55, column 2 | a PBX from a package feed, reached through its own configuration files and CLI | cells flip to ✗; voice keeps columns 1, 3 and 4 and stays built; if columns 1 **and** 2 both flip, voice keeps columns 3 and 4 only and drops to `tier-staged` with its rows re-outcomed. **Stage 4: flipped**, with column 1: voice keeps columns 3 and 4, two of five, and is `tier-staged` (M3, M32) |
| R56–R58, column 3 | controller source whose porting to the reference platform is marked ongoing, no documentation of the paths | cells flip to ✗; the topology (R56) keeps columns 1, 4 and 5 and the tier stays built; steering (R58) keeps columns 1, 2 and 5 by count but is implemented on columns 1 and 5 only, column 2's cell being plain-AP roaming whose driver raises (above); backhaul health (R57) keeps columns 1 and 4 only and becomes a per-column unsupported case on columns 2, 3 and 5. **Stage 4: no flip** — the controller is carried on the family's mesh build variant, the cells stay ◐. With R58 ✗ on column 5: the topology keeps columns 1, 3, 4 and 5 and the tier stays built; steering keeps columns 1, 2 and 3 by count and is implemented on columns 1 and 3; backhaul health keeps columns 1, 3 and 4 and is a per-column unsupported case on columns 2 and 5 |
| R53, column 1 | build-profile and CI scripts, no agent-state documentation | the cell flips to ✗; USP keeps columns 3 and 4 only and drops to `tier-staged` with its rows re-outcomed. **Stage 4: no flip** — the driver configures the agent through the build profile's reset file and its CLI; USP keeps columns 1, 3 and 4 and stays built |
| R30, columns 1, 3, 4 and 5 | zone defaults readable in part or not at all; the zone writes of `FirewallZones` are published by column 2 only | no flip: the zone writes are a per-method unsupported case on four columns, including trigger column 1, so a test of zone writes runs on one family |
| R39, column 2 | the board read publishes model and software version but neither manufacturer nor serial number | no flip: two of five identity properties raise on a trigger column, a documented per-method unsupported case; if a board-level read is sourced at stage 4 the case closes |
| R44, column 2 | the server list is published; the synchronisation state needs a package the family does not document | no flip: `get_sync_state` raises on a trigger column (and on column 4), a documented per-method unsupported case |
| R52, columns 1–5 | an inform trigger on columns 1 and 2, session state only on all five | no flip possible for the operation (◐ everywhere); the member's trigger half is supported on two of five columns and raises on columns 3, 4 and 5 — kept on the core as a per-method unsupported case because the operation it belongs to meets the threshold; a reviewer who reads the bar per member rather than per operation moves `force_inform` to a `tier-staged` row, which this design flags as the one open reading |

### Members without a matrix row

Reuse composes whole protocols, and the reused protocols carry members for
which §2 has no operation row. Each such member is a stage-4 verification
item settled as the core members with ◐ cells are: a sourced mapping where
the column publishes the operation, `NotSupportedError` with a source where
it does not. Expected per column, from the family notes of §8: column 4
raises every write below and most reads; column 5 raises the kernel- and
PHY-specific reads; columns 1, 2 and 3 map most of them.

| Protocol | Members without a row | Expected |
| --- | --- | --- |
| `FirewallZones` | `create_zone`, `delete_zone`, `add_zone_interface`, `remove_zone_interface`, `add_zone_network`, `remove_zone_network`, `set_zone_defaults`, `set_forwarding`, `list_forwarding` (R30 is the read) | mapped on column 2 (a zone model); raise on columns 1, 3, 4 and 5 (no zone object, R30 ◐/✗) |
| `Firewall` | `set_dmz_host`, `get_dmz_host`, `set_port_mapping_enabled`; the inherited `flush_chain`, `set_default_policy`, `get_default_policy`, `get_rule_counter_values` | DMZ mapped on columns 1, 2, 3 and 5, raises on column 4; as built at stage 4, `flush_chain` maps on columns 1, 2 and 3, the default-policy pair on columns 1 and 2, the counter pair on column 2 only, each raising elsewhere (columns 1 and 3 have forward chains only; column 5's counters exist with undocumented fields, §6 Port forwards) |
| `WifiRadio` | `set_mode`, `get_mode`, `get_modes`, `set_country`, `get_country`, `get_dfs_state`, `list_supported_channels` | mapped on columns 1, 2, 3 and 5, except `get_dfs_state`, which raises on columns 3, 4 and 5 (no channel-availability state); column 4 raises the setters and `get_country` (and, of the row-bearing reads, `get_tx_power`); column 3 raises the dBm power pair (a percentage only, R22) |
| `WifiBss` | `set_acl_mode`, `add_acl_entry`, `remove_acl_entry`, `clear_acl`, `get_acl`, `set_vlan`, `set_max_clients`, `set_dtim_period`, `set_captive_portal`, `create_bss`, `delete_bss` | mapped on columns 1, 2, 3 and 5 except the captive portal (raises everywhere but column 2); `set_vlan` with a tag is a per-value refusal on columns 1, 2 and 3 (no static per-network tag) and maps on column 5; column 3's `create_bss` / `delete_bss` claim and release a static slot; column 4 raises the access list, VLAN, DTIM and portal members and `set_max_clients` and `get_acl`, reads DTIM 1, and maps `create_bss` / `delete_bss` onto the guest network |
| `WifiStations` | `get_station` | mapped on all five |
| `WifiTransitions` | `get_transition_config`, `send_btm_request`, `send_neighbor_report_request`, `send_deauth` | column 4 raises all four; columns 1 and 2 map them, the "neighbour report request" sent as a radio-measurement (beacon) request (`lossy:`), column 2 refusing a BTM candidate list per value; column 3 maps the config read and the deauth (the forced disassociation) and raises both request senders and `set_ft_enabled` (no 802.11r); column 5 maps the config read and 802.11r (`set_ft_enabled`) and raises the three frame senders |
| `WifiOnboarding` | `set_wps_enabled`, `get_wps_enabled`, `get_wps_device_pin`, `enroll_client_via_dpp` | enable mapped on columns 1, 2, 3 and 4; the PIN on columns 1, 2 and 3 (columns 4 and 5 raise it: obsolete on column 4); DPP mapped on column 1 (through the access-point daemon's control interface, source-only), raises elsewhere; column 2 also maps `cancel_wps` (source-only) |
| `DhcpClient` | `release_ipv6`, `renew_ipv6`, `observe_lease`, `release_observed_lease` | the IPv6 pair mapped on columns 1, 2 and 5, raises on column 4; column 3 maps `renew_ipv6` and raises `release_ipv6` (no release trigger); the observation pair is a host lever and raises on every column |
| `DeviceLifecycle` | `finalize_boot` | mapped on all five (a no-op completion where the family has nothing to finalise, stated in the docstring) |
| `Tr069Client` | `get_id`, `get_tr069_log` | mapped on all five; the log read raises on column 4 |
| `DeviceHealth` | `is_online` | mapped on all five (the session answers) |
| `WifiMesh` (tier) | `set_enabled`, `set_backhaul_band`, `set_backhaul_channel`, `add_agent`, `remove_agent`, `set_mesh_psk_for_enrollment` (controller side); `get_dpp_uri`, `start_dpp_enrollee`, `trigger_wps_enrollee` (agent side) | controller-side members as built at stage 4: column 1 in part (`set_enabled`, `add_agent` with push-button, PIN and passphrase, `set_mesh_psk_for_enrollment` map; `remove_agent` and the backhaul band and channel raise); column 3 none (all six raise on the mesh build variant); column 4 none (the mesh surface is a read-only topology, §10 column 4 [58]); column 5 `set_enabled` only; the agent-side members raise on every column whose device acts as controller only — they exist for a device that is also an agent (the protocol's `CONTROLLER_AND_AGENT` role), which this archetype does not drive (§1) |

The protocols without such members are `PortStatus`, `DhcpClient`'s v4 pair,
`InterfaceDhcp`, `SyslogConfig`, `NtpConfig`, `WanLinkAdmin` and
`NetworkEndpoint`.

### Verification items (exploration)

Every ◐ and ✗ cell of §2 as it stands after stage 4, by column and row id
(the cell text and its source stand in §2 and §10); stage 4 settled each as
an explicit `NotSupportedError` with a source or as a sourced mapping. 109
items: the exploration's 105, with four ✓ cells re-graded to ◐ (R3 and R4 on
column 3, R23 and R28 on column 4) and five ◐ cells flipped to ✗ (R54 and R55
on columns 1 and 2, R58 on column 5), which moves no count.

- **Column 1 (trigger family 1)** (8): ◐ R30, R37, R47, R52, R53, R57; ✗ R54, R55
- **Column 2 (trigger family 2)** (20): ◐ R5, R7, R10, R14, R19, R21, R27, R28, R37, R38, R39, R44, R47, R52, R58; ✗ R53, R54, R55, R56, R57
- **Column 3** (20): ◐ R3, R4, R16, R17, R20, R22, R29, R30, R33, R36, R37, R48, R49, R52, R53, R54, R55, R56, R57, R58; ✗ none
- **Column 4** (39): ◐ R1, R2, R3, R6, R7, R10, R11, R12, R16, R19, R20, R21, R22, R23, R28, R31, R34, R36, R37, R40, R44, R47, R52, R53, R55, R57; ✗ R5, R9, R13, R15, R17, R18, R27, R29, R30, R33, R41, R43, R58
- **Column 5** (22): ◐ R1, R4, R5, R7, R20, R23, R25, R28, R29, R30, R36, R38, R41, R47, R52, R56; ✗ R17, R53, R54, R55, R57, R58

Three further items from §6, settled at stage 4: the TR-069 route on column
1 (decided; the two-clients question stays unverified), the reference build's
component list on column 3 (checked; R3–R4 re-graded), and the re-check of
every cited URL when the drivers cite it (done through their `source:`
lines).

### Precise types in the corpus

Every driver fills the records of §6 with the enum values named there and
nothing looser; a family value outside an enum is a `lossy:` line with the
mapping, never a widened field. The corpus's fakes emit each column's
refusal shape (§8) so the negative path of every write is tested, and the
`source:` line of every unsupported case names the document that
establishes the absence.

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
52. iCWMP ubus API (tr069) — <https://dev.iopsys.eu/bbf/icwmp/-/blob/devel/docs/api/ubus/tr069.md> — methods `inform` ("Ubus method to handle RPC"), `status` ("last_session", "next_session") — UCI/ubus substrate: `ubus call tr069 inform` triggers a session, `ubus call tr069 status` reports session state — both observed, prplOS 4.0.3, impls/cpe_tr069.py; DM side (tr069-manager) reads `ManagementServer.State.SessionStatus` (Initializing/idle/busy/failure), `LastSession`, `ConnRequest.ConnRequestPort/Path` and offers `updateConnectionRequestURL()` but no inform-trigger method. Stage 4 route: `set_acs` / `get_acs` through `Device.ManagementServer.` ([51], tr069-manager v1.31.3), `force_inform` and `is_tr069_connected` through this `tr069` bus object (icwmp's); whether a tr069-manager image registers the same bus object is unverified
53. prplos (build profiles + CI DUT scripts) — <https://gitlab.com/prpl-foundation/prplos/prplos> — profiles/mgmt.yml (`obuspa`, `mod-amxb-usp`, `CONFIG_OBUSPA_WEBSOCKET_MTP_SUPPORT`); .gitlab/scripts/dut-init/obuspa_param_reset-mqtt.txt (`Device.LocalAgent.Controller.1.EndpointID/Enable/MTP.1.Protocol/MQTT.Reference/MQTT.Topic`); cdrouter-dut-configure-usp-common.sh (`obuspa -c get Device.LocalAgent.MTP.1.Protocol`) — USP agent (obuspa) in the prplOS `mgmt` profile: controller endpoint and MTP (MQTT/WebSocket) are written through obuspa's factory-reset file `/etc/config/obuspa_param_reset.txt` and read back with `obuspa -c get Device.LocalAgent.…` — obuspa CLI, not ba-cli
54. tr104-voip plugin repository — <https://gitlab.com/prpl-foundation/components/core/plugins/tr104-voip> — README: "tr181-voip is a service providing VoiceService:2 data model" (repo contains only LICENSE + README) — prplOS lists a voice plugin but publishes no ODL/README naming SIP account (`VoiceService.{i}.SIP.Client`) or registration state; not in any prplos build profile. Stage 4: the default branch `main` at 65f9575 (the only tag v0.0.0) holds LICENSE and the one-sentence README, no ODL — R54 ✗
55. tr104-voip plugin repository — <https://gitlab.com/prpl-foundation/components/core/plugins/tr104-voip> — README (single sentence) — No prplOS source names FXS/POTS line state (`VoiceService.{i}.POTS.FXS`); only the TR-104 stub exists. Stage 4: no `POTS.FXS` object on the default branch at 65f9575 — R55 ✗
56. prplOS TR-181 Data Model documentation — <https://prpl-foundation.gitlab.io/prplos/feeds/feed-prpl/> — pages `Device.WiFi.DataElements.Network.Device.{i}..html` (`ID`, `Manufacturer`, `SerialNumber`, `SoftwareVersion`, `InterfaceNumberOfEntries`) and `…Device.{i}.MultiAPDevice.Backhaul..html` (`LinkType`, `BackhaulMACAddress`, `BackhaulDeviceID`, `MACAddress`) — prplMesh 4.2.3 controller.odl/device.odl — DM (prplMesh controller): `Device.WiFi.DataElements.Network.Device.{i}` lists agents, `Radio.{i}`/`Interface.{i}.Neighbor.{i}` the links and `MultiAPDevice.Backhaul` the upstream link type/MACs, read-only via ba-cli
57. prplOS TR-181 Data Model documentation — <https://prpl-foundation.gitlab.io/prplos/feeds/feed-prpl/> — pages `…MultiAPDevice.Backhaul..html` (`LinkType`, `BackhaulMACAddress`), `…Radio.{i}.BackhaulSta..html` (`MACAddress`), `…Radio.{i}.BSS.{i}.STA.{i}..html` (`SignalStrength`, `EstMACDataRateDownlink/Uplink`, `LastDataDownlinkRate`, `UtilizationReceive`) — DM: the backhaul link itself exposes only type and MACs; health metrics must be read from the backhaul STA's entry under the parent agent's `BSS.{i}.STA.{i}` (prplMesh 4.2.3)
58. prplOS TR-181 Data Model documentation — <https://prpl-foundation.gitlab.io/prplos/feeds/feed-prpl/> — page `Device.WiFi.DataElements.Network..html`: `void ClientSteering(in <mandatory> string station_mac, in <mandatory> string target_bssid)` (prplMesh 4.2.3 controller.odl) — DM (prplMesh controller): `Device.WiFi.DataElements.Network.ClientSteering(station_mac=…, target_bssid=…)` steers a client to another agent's BSS; `BTMSteeringDisallowedSTAList`/`SteerEvent.{i}` are the related read objects

### OpenWrt 24.10 line with icwmp

1. IPv4 configuration — <https://openwrt.org/docs/guide-user/network/ipv4/configuration> — Protocol "static" / Protocol "dhcp" (`proto`, `ipaddr`, `netmask`, `gateway`) — option tables for `proto static` and `proto dhcp` on the WAN interface; PPPoE is `proto pppoe` on the WAN protocols page; IPoE = dhcp/static
2. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `ubus call network.interface.wan status` (`up`, `pending`, `uptime`, `address`, `route`, `data`) — status call returns interface up/pending state, uptime and address list (lease data in `data`; `ifstatus wan6` shows prefix lifetimes on the IPv6 page). Stage 4: netifd at the 24.10 pin (7901e66, ubus.c) prints `ipv4-address`, `ipv6-address`, `ipv6-prefix` and `dns-server`, not the page's `address`; the field names are cited source-only, the operation stands on the page
3. WAN interface protocols — <https://openwrt.org/docs/guide-user/network/wan/wan_interface_protocols> — `pppoe`: `username`, `password`, `service`, `ac` — the PPPoE option table names username, password and service (plus ac, keepalive, padi_*)
4. Network configuration /etc/config/network — <https://openwrt.org/docs/guide-user/network/network_configuration> — `ifdown <name>` / `ifup <name>` (`ubus list network.interface.*`) — interfaces are brought down and up individually with ifdown/ifup, which restarts the PPPoE session
5. ISP configurations — <https://openwrt.org/docs/guide-user/network/wan/isp-configurations> — `config device` / `option type '8021q'` / `option ifname 'wan'` / `option vid '…'`; `option device 'wan.<vid>'` — many ISP examples define a tagged WAN device by `type 8021q` + `vid` (or legacy `eth0.7`); no `ingress/egress_qos_mapping` on any wiki page
6. IPv6 configuration — <https://openwrt.org/docs/guide-user/network/ipv6/configuration> — Protocol "dhcpv6": `reqaddress`, `reqprefix`; LAN `ip6assign`; `ifstatus wan6` → `ipv6-prefix` — wan6 is `proto dhcpv6` with `reqprefix` (auto/no/1-64), and `ifstatus wan6` lists the delegated `ipv6-prefix` with lifetimes and `assigned` sub-prefixes
7. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `network.interface.<name> status` (`up`, `address`) — there is no provisioning-mode object; v4/v6/dual is inferred from which of wan/wan6 is up with addresses
8. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `ubus call network.device status '{"name":"eth0"}'` → `up`, `link`, `mtu`, `macaddr`, `statistics` — device status reports the carrier `link` flag and counters for the WAN device. Stage 4: netifd at the 24.10 pin (7901e66, device.c) prints `carrier`; the field name is cited source-only
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
21. ubus (techref) — <https://openwrt.org/docs/techref/ubus> — `network.device status` → `link`, `up` — only link state is exposed uniformly; speed/duplex appear as device write options (`speed`, `duplex`, `autoneg`) and swconfig's `link` attribute, not a uniform read API. Stage 4: the same reply carries `speed` (`"1000F"`: speed and duplex) at the 24.10 pin — netifd 7901e66 system-linux.c `system_if_dump_info`, device.c `device_dump_status`, source-only; no `ethtool`
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
3. RdkPppManager.xml (ppp-manager) — <https://github.com/rdkcentral/ppp-manager/blob/main/config/RdkPppManager.xml> — Device.PPP.Interface.{i}.Username (RW), Password (RW), PPPoE.ServiceName (RW), PPPoE.ACName (RW); same params in CcspPandM XML — PPPoE credentials and service name are writable. Stage 4: ppp-manager is not in the reference build (meta-cmf-bananapi `rdkb-2025q4-kirkstone` 76849e6 rdk-bpi.inc and rdk-generic-broadband-image.bbappend: `rdk-ppp-manager` only with `rdkb_xdsl_ppp_manager`, unset; `ppp-enabled` commented out; meta-cmf develop 2f49787 packagegroup-rdk-ccsp-broadband.bbappend; `rp-pppoe` removed; PPPoE under the 2025Q4 release page's "Future"); CcspPandM declares `Device.PPP.Interface`, whether it serves it without ppp-manager is unverified — R3 ◐
4. RdkPppManager.xml (ppp-manager) — <https://github.com/rdkcentral/ppp-manager/blob/main/config/RdkPppManager.xml> — Device.PPP.Interface.{i}.Reset (RW boolean); ConnectionStatus (RO) — writable Reset re-establishes the PPP session; status readable. Stage 4: as [3], ppp-manager is not in the reference build; with no PPPoE client the reset's observation cannot be made — R4 ◐
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
15. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.EnableStaticNameServer, NameServer1, NameServer2 (RW; declared inside `<?ifdef BCI | _ONESTACK_PRODUCT_REQ_?>`, so present only on a build that sets that flag); Device.DNS.Client.Server.{i}.DNSServer (RW, writable table add/del); Device.DHCPv4.Server.Pool.{i}.DNSServers (RW) — upstream resolver addresses for the gateway's DNS proxy are writable
16. Utopia dhcp_server_functions.sh — <https://github.com/rdkcentral/utopia/blob/develop/source/scripts/init/service.d/service_dhcp_server/dhcp_server_functions.sh> — `echo "address=/$LOCDOMAIN_NAME/$locaddr" >> $LOCAL_DHCP_CONF` — local name overrides are generated by the dnsmasq start script; no TR-181 parameter exposes them. Stage 4 (Utopia 383ae69 service_dhcp_server.sh: the launch line without `--no-hosts`, `dns_start`, `prepare_hostname`; dnsmasq(8) SIGHUP): the `address=/` line serves the secure web UI's FQDN only and the file is regenerated on every DNS restart; an override is a marked `/etc/hosts` line plus dnsmasq's SIGHUP, lasting until `prepare_hostname` rewrites the host file (that `/etc/hosts` is writable on the reference image is unverified)
17. Utopia service_dhcp_server.sh — <https://github.com/rdkcentral/utopia/blob/develop/source/scripts/init/service.d/service_dhcp_server.sh> — dnsmasq launch line `... --proxy-dnssec --cache-size=0 --stop-dns-rebind ...` — rebind protection exists but only as a fixed command-line flag, no parameter
18. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.Bridging.Bridge.{i} and Bridge.{i}.Port.{i} (writable tables, add/del): Port.{i}.LowerLayers (RW), Enable (RW), PVID (RW); Device.Ethernet.X_RDK_Interface.{i}.AddToLanBridge (RW) — bridge membership is configured by writable ports with LowerLayers references
19. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.Bridging.Bridge.{i}.Status, Port.{i}.Name, Port.{i}.Status, Port.{i}.PortState (RO), Port.{i}.LowerLayers — bridge and port membership/state are readable
20. CcspPandM TR181-USGv2.XML + OneWifi XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.X_CISCO_COM_DeviceControl.LanManagementEntry.{i} (writable table add/del): LanMode, LanIPAddress, LanSubnetMask, LanDhcpServer, LanNaptEnable (RW); Device.WiFi.SSID.{i}/AccessPoint.{i} — an extra LAN segment with its own DHCP/NAPT can be created, but a guest segment is not a named operation
21. CcspPandM TR181-USGv2.XML — <https://github.com/rdkcentral/provisioning-and-management/blob/develop/config-arm/TR181-USGv2.XML> — Device.Ethernet.Interface.{i}.Status (Up/Down/...), CurrentBitRate, MaxBitRate (RO), DuplexMode (Half/Full/Auto) — LAN port link, speed and duplex are readable
22. OneWifi TR181-WiFi-USGv2.XML — <https://github.com/rdkcentral/OneWifi/blob/develop/config/TR181-WiFi-USGv2.XML> — Device.WiFi.Radio.{i}.Enable (RW), Channel (RW), AutoChannelEnable (RW), OperatingChannelBandwidth (RW: 20/40/80/160/320MHz), TransmitPower (RW), OperatingStandards (RW); OperatingFrequencyBand (RO) — channel, width, power and enable are writable; band cannot be set. Stage 4 (OneWifi develop 7b3a6cc): `TransmitPower` is int[-1:100], a percentage with no dBm maximum (`TransmitPowerSupported`), so the dBm power members raise
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
53. RDK Reference USP controller documentation (RDK wiki) — <https://wiki.rdkcentral.com/x/pAbyHQ> — `obuspa -p -v 4 -r factory_reset_example.txt`; Device.LocalAgent.Controller.1.EndpointID, Controller.1.MTP.1.Protocol "MQTT", Controller.1.MTP.1.MQTT.Topic, Device.LocalAgent.MTP.1.MQTT.Reference, Device.MQTT.Client.1.BrokerAddress/BrokerPort — controller endpoint and MQTT transport are set in the agent's boot file; no agent-state parameter documented. Stage 4: USP is in the reference build (meta-cmf-bananapi 76849e6 rdk-bpi.inc `DISTRO_FEATURES_append = " usppa"`, recipes-rdkb/usp-pa/usp-pa.bbappend); the cell stays ◐ (no agent state)
54. RdkTelcoVoiceManager_v2.xml (telco-voice-manager) — <https://github.com/rdkcentral/telco-voice-manager/blob/main/config/RdkTelcoVoiceManager_v2.xml> — Device.Services.VoiceService.{i}.SIP.Client.{i}.AuthUserName, AuthPassword, RegisterURI, Enable (RW), Status (RO: Registering/Up/Error_Registration); SIP.Network.{i}.ProxyServer, RegistrarServer (RW); SIP.Registrar.{i}.Account.{i}.RegistrationStatus (RO) — TR-104v2 SIP account and registration state exist in the voice manager; absent from CcspPandM; CcspMtaAgent has no SIP account objects. Stage 4: the manager is installed in the reference image (meta-cmf-bananapi 76849e6 rdk-bpi.inc, rdk-generic-broadband-image.bbappend: `IMAGE_INSTALL_append … rdktelcovoicemanager asterisk hal-voice-asterisk`), but the platform writes the TR-104 v2 switch as `DISTRO_FEATURE_append` (singular, not read by bitbake) and the shared packagegroup (meta-cmf develop 2f49787 packagegroup-rdk-ccsp-broadband.bbappend line 20) keys `rdktelcovoicemanager` on that same feature, so the v2 model may not be the one built (README default v1, `VoiceProfile.{i}.Line.{i}.SIP.*`); the 2025Q4 page lists TelcoVoice under "No Release due to GitHub migration"
55. RdkTelcoVoiceManager_v2.xml + CcspMtaAgent.xml — <https://github.com/rdkcentral/telco-voice-manager/blob/main/config/RdkTelcoVoiceManager_v2.xml> — Device.Services.VoiceService.{i}.POTS.FXS.{i}.Status (RO: Up/Error/Testing/Disabled), Active (RO), DiagTests.*; Device.X_CISCO_COM_MTA.LineTable.{i}.Status (RO On-Hook/Off-Hook), CALLP.LCState — FXS line state readable in both voice models, neither confirmed in the BPI R4 reference build. Stage 4: as [54], the manager is installed and the v2 model unverified
56. unified-wifi-mesh inc/tr_181.h — <https://github.com/rdkcentral/unified-wifi-mesh/blob/develop/inc/tr_181.h> — Device.WiFi.DataElements.Network.Topology, Network.Device.{i}.ID, BackhaulMACAddress, BackhaulALID, BackhaulMediaType, BackhaulPHYRate, Network.Device.{i}.Radio.{i}.BackhaulSta.MACAddress — EasyMesh topology elements are defined by the RDK-B controller code. Stage 4: the controller is installed on the EasyMesh build variant of the same release (meta-cmf-bananapi 76849e6 rdk-generic-broadband-image.bbappend, rdk-bpi.inc; setup-environment-refboard-rdkb lines 86–87: `FEATURE_TYPE=EasyMesh` uncomments `DISTRO_FEATURES_append = " EasyMesh"` and the image adds `unified-wifi-mesh`; 2025Q4 release page "SD Build for Gateway with EasyMesh"); the shared packagegroup names an alternative controller (`rdk-easymesh-controller`, `easymesh-controller`) the BPI layer does not set; unified-wifi-mesh develop 1ba9529
57. unified-wifi-mesh inc/tr_181.h — <https://github.com/rdkcentral/unified-wifi-mesh/blob/develop/inc/tr_181.h> — Device.WiFi.DataElements.Network.Device.{i}.MultiAPDevice.Backhaul.Stats.SignalStrength, LinkUtilization, LastDataDownlinkRate, LastDataUplinkRate, BytesSent/Received, ErrorsSent/Received; Network.Device.{i}.BackhaulDown.{i} — backhaul link health elements are defined in code only; on the EasyMesh build variant (as [56]) `Backhaul.Stats` fills the agent's backhaul link, source only
58. unified-wifi-mesh inc/tr_181.h + docs — <https://github.com/rdkcentral/unified-wifi-mesh/blob/develop/inc/tr_181.h> — Device.WiFi.DataElements.Network.Device.{i}.Radio.{i}.BSS.{i}.STA.{i}.ClientSteer() (DE_STA_CLIENTSTEER, clientsteer_handler); MultiAPDevice.Backhaul.SteerWiFiBackhaul(); method-invocation format shown for ChannelSelectionRequest() in the unified-wifi-mesh docs — client steering is an EasyMesh controller method, not documented in RDK-B release material; on the EasyMesh build variant (as [56]) `ClientSteer()` carries `steer_client`, source only

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
17. FRITZ! interfaces index (TR-064 service list) — <https://fritz.com/en/pages/interfaces> — TR-064 service table (no DNS/rebind service) — the published service list contains no DNS forwarder service and no rebind-protection parameter; the row rests on this index (41 documents, none for DNS, firewall, zones, syslog or processes), not on a service document
18. TR-064 Support – LANHostConfigManagement1 (v9, 2025-08-07) — <https://fritz.support/resources/TR-064_LAN_Host_Config_Management.pdf> — Action List (SetIPInterface, SetAddressRange, …) — the LAN-side services carry no bridge or VLAN membership write
19. TR-064 Support – Hosts (v32, 2026-01-29) — <https://fritz.support/resources/TR-064_Hosts.pdf> — §2.10 X_AVM-DE_GetSpecificHostEntryByIP (InterfaceType, X_AVM-DE_Port, X_AVM-DE_Speed, X_AVM-DE_Guest) — which LAN port or guest segment a host sits on is readable per host, not as a bridge table
20. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §1 introduction (logical guest AP as service #2/#3/#4), §2.1 SetEnable, §2.12 SetSSID, §2.4 SetSecurityKeys, §2.33 X_AVM-DE_GetWLANExtInfo (APType normal/guest, UserIsolation) — the guest Wi-Fi is a separate service instance with the full Set* action set; wired guest access is not covered
21. TR-064 Support – LAN Ethernet Interface Config (v3, 2025-08-07) — <https://fritz.support/resources/TR-064_LAN_Ethernet_Interface_Config.pdf> — GetInfo (Status, MaxBitRate, DuplexMode, MACAddress), GetStatistics; Hosts X_AVM-DE_Port/X_AVM-DE_Speed — link status, rate and duplex are read for one LAN interface; per-port speed is only visible on connected hosts
22. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.1 SetEnable, §2.16 SetChannel (0 = auto), §2.3 SetConfig, §2.34 X_AVM-DE_SetWLANGlobalEnable; band = service instance — radio enable and channel are writable per band instance; width, power, country and DFS have no action
23. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.2 GetInfo (Enable, Status Up/Disabled, Channel, Standard, X_AVM-DE_FrequencyBand), §2.15 GetChannelInfo (PossibleChannels, X_AVM-DE_AutoChannelEnabled) — radio enable, status, channel, band and auto-channel state are returned; no transmit power, regulatory domain or DFS state is published (R23 ◐, stage 4)
24. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.12 SetSSID, §2.14 SetBeaconType (None, WPA, 11i, WPAand11i, WPA3, 11iandWPA3, OWE, OWETrans), §2.4 SetSecurityKeys (KeyPassphrase/PreSharedKey), §2.18 SetBeaconAdvertisement (hidden) — SSID, security mode, passphrase and SSID broadcast are each set by a documented action
25. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.2 GetInfo (SSID, BSSID, BeaconType, Enable, Status), §2.17 GetBeaconAdvertisement, §2.19 GetTotalAssociations — BSS identity, security mode, enable/status and association count are readable
26. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.20 GetGenericAssociatedDeviceInfo (MAC, IP, AuthState, X_AVM-DE_Speed, X_AVM-DE_SignalStrength, X_AVM-DE_ChannelWidth), §2.23 X_AVM-DE_GetWLANDeviceListPath — per-station signal strength, rate and channel width are listed
27. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2 Action List (38 actions, none acting on a single station) — the service's full action list has no kick/deauth action
28. TR-064 Support – WLANConfiguration (v49, 2026-03-10) — <https://fritz.support/resources/TR-064_WLAN_Configuration.pdf> — §2.36 X_AVM-DE_SetWPSConfig (WPSMode pbc / stop), §2.35 X_AVM-DE_GetWPSInfo (WPSStatus off, inactive, active, success, err_*), §2.37 X_AVM-DE_SetWPSEnable — push-button WPS can be started and stopped and its status read; Service States Table: X_AVM-DE_WPSAPPIN and X_AVM-DE_WPSClientPIN obsolete (history v45), and SetWPSConfig takes pbc and stop only ("WPS is supported with Push Button Configuration") — R28 ◐, push-button only
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
41. FRITZ! interfaces index (TR-064 service list) — <https://fritz.com/en/pages/interfaces> — TR-064 service table — the published services (DeviceInfo, DeviceConfig, …) contain nothing about processes; the row rests on this index, not on a service document
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
58. WiFi — <https://help.mikrotik.com/docs/spaces/ROS/pages/224559120/WiFi> — wifi package Steering `wnm`, `neighbor-group`, `transition-threshold`, `transition-request-count`, `transition-time` — Clients can be nudged to neighbor-group APs by (unsolicited, 7.21+) 802.11v BSS-transition requests and optionally de-authenticated; there is no per-client "steer to agent X" command: the Steering section has properties only, none addressing one client or naming a target — R58 ✗ (stage 4)

### Citation maintenance (stage 3)

- The charter's no-CLI citation for FRITZ!OS (the knowledge-base article
  "Access to the FRITZ!Box via Telnet is not supported") moved from the
  `en.fritz.com/service/knowledge-base/dok/...` path, which now redirects to
  a missing page, to `fritz.com/en/apps/knowledge-base/...`; §1 cites the
  live path and, because that page renders its text client-side, the
  archived copy for the "since FRITZ!OS 6.25" statement. The interfaces index (https://fritz.com/en/pages/interfaces)
  corroborates the point from the other side: it lists TR-064, UPnP IGD,
  the HTTP session-ID login and the Smart Home REST API, and no shell or
  command-line interface.
- RouterOS: the legacy documentation wiki (`wiki.mikrotik.com`) carries a
  "frozen" notice pointing at its successor, the help site
  (https://help.mikrotik.com/docs); every entry in the column's list above
  already cites the successor, and a driver's `source:` line cites it too.
- RDK-B: the project wiki renders client-side; the entries above were read
  through its export views, and a driver's `source:` line names the page
  title beside the URL so a reader can find it when the rendering changes.
- FRITZ!OS: several TR-064 service documents carry wrong metadata titles;
  the entries above and the drivers cite the document's file name and the
  action, not the metadata title.

## 11. Open questions

No open questions at the design stage; the verification items are §9. The
twelve questions the exploration raised are answered in §6, each with the
condition that would overturn the answer:

1. Does ◐ count as support? — Yes (the maintainer's decision of 2026-10-19,
   review record): §3 and §4 apply it; every ◐ cell stays a verification
   item (§9).
2. The WAN connection object's shape — §6, "The WAN connection": one object,
   a mode, mode-specific optional parts; link state stays on `port_status`.
3. DHCP server placement — §6, "DHCP server": `interface_dhcp` with two
   defaulted pool fields.
4. Port forwards — §6, "Port forwards": the per-mapping `firewall` shape;
   the appliance keeps its list-replacing one.
5. Host filtering — §6, "Host filtering": a new capability with a weekly
   schedule.
6. Remote management — §6, "Remote management": the ACS configuration as an
   extend, the inform's meaning stated, no connection-request read, USP as
   a tier.
7. Mesh and voice tiers — §6, "Mesh and voice": both designed, the nominal
   cells named (§9 Stated risks); at stage 4 the mesh tier is built and the
   voice tier `tier-staged`.
8. `CpeDevice` supersession — §6, "Supersession": new class and key, the old
   shape intact and deprecated as a `class` row.
9. Health reads — §6, "Health": `DeviceHealth` split with `read_cpu_load`.
   The four core capabilities the exploration left without a question
   (DNS forwarder, bridge, host table, automatic port mapping) have their
   own §6 subsections.
10. Source maintenance — §6, "Decided as verification items"; §10 re-points
    what it can.
11. Reference-image inclusion — §6, "Decided as verification items".
12. Two CWMP clients on column 1 — §6, "Decided as verification items";
    decided at stage 4 (review record).

## 12. Landing manifest

Every symbol change the body proposes. `core` and `tier` rows land on this
design's `archetype:` PR at stage 4 with changelog entries citing this document
and the row id; the `tier-staged` rows become `GAPS.md` pointers at merge.
Outcomes record the design review rounds (round 1, 2026-10-20: approve with
conditions C1–C8; a row carries the conditions folded into it) and the
stage-4 re-outcomes (stage 4b, review record). A new record
that serves an extension travels in the extension's row; a new record that
serves a new capability travels in that capability's row.

| Id | Kind | Symbol | Mechanism | Placement | Breaking | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | new archetype | `testprotocols.devices.cpe_gateway:CpeGatewayDevice` (registered `cpe_gateway`) | archetype | core | no | accepted, 2026-10-20 |
| M2 | deprecation | `testprotocols.devices.cpe:CpeDevice` (registry key `linux_cpe`): kept intact, marked deprecated, `class` row; replacement `CpeGatewayDevice` / `cpe_gateway`; period one MINOR and six months (§6) | deprecate | core | no | accepted, 2026-10-20 |
| M3 | new tier | `testprotocols.devices.cpe_gateway:CpeGatewayVoiceTier` (`voice: VoiceGateway`; not registered, pinned by `isinstance`) | archetype | tier-staged — a third column supporting the SIP account (R54) beside columns 3 and 4, the majority of five, or a consumer | no | tier-staged (stage 4: voice R54–R55 ✗ on columns 1, 2 and 5 — 2 of 5 — 2026-10-20) |
| M4 | new tier | `testprotocols.devices.cpe_gateway:CpeGatewayMeshTier` (`wifi_mesh: WifiMesh`; not registered) | archetype | tier — mesh | no | accepted, 2026-10-20 |
| M5 | new tier | `testprotocols.devices.cpe_gateway:CpeGatewayUspTier` (`usp_agent: UspAgent`; not registered) | archetype | tier — usp | no | accepted, 2026-10-20 |
| M6 | new protocol | `testprotocols.wan_connection:WanConnection` (`set_wan_connection`, `get_wan_connection`, `list_wan_connections`, `get_wan_state`, `reset_session`) with `testprotocols.models.cpe_gateway:WanMode`, `WanIpv6Mode`, `WanStatus`, `ProvisioningMode`, `PppoeCredentials`, `StaticAddressing`, `WanVlan`, `WanIpv6`, `WanConnectionConfig`, `WanConnectionState` | new capability | core | no | accepted with conditions (C4, C6; stage 4: R3–R4 ◐ on column 3, no PPP manager in the reference build), 2026-10-20 |
| M7 | new protocol | `testprotocols.dns_forwarder:DnsForwarder` (`set_upstreams`, `get_upstreams`, `add_host_override`, `remove_host_override`, `list_host_overrides`, `set_rebind_protection`, `get_rebind_protection`) with `testprotocols.models.cpe_gateway:DnsUpstream`, `DnsHostOverride` | new capability | core | no | accepted with conditions (C3, C8), 2026-10-20 |
| M8 | new protocol | `testprotocols.l2_bridge:L2Bridge` (`create_bridge`, `delete_bridge`, `list_bridges`, `get_bridge`, `add_member`, `remove_member`, `get_members`) with `testprotocols.models.cpe_gateway:BridgeMemberKind`, `BridgeMember`, `BridgeConfig`, `BridgeMemberState` (importing `StpMode`, `StpPortState` from `models/l2_common.py`); realises the `GAPS.md` 2026-05-02 entry's membership half | new capability | core | no | accepted with conditions (C3, C5), 2026-10-20 |
| M9 | GAPS entry | `GAPS.md` 2026-05-02 `L2Bridge`: closed for membership by M8; the STP tuning and the forwarding-table read stay open under a dated note, the table read as the `L2BridgeWhiteBox` candidate (M27) | record | core | no | accepted, 2026-10-20 |
| M10 | new protocol | `testprotocols.host_table:HostTable` (`list_hosts`, `get_host`) with `testprotocols.models.cpe_gateway:HostAttachment`, `LanHost` | new capability | core | no | accepted with conditions (C3), 2026-10-20 |
| M11 | new protocol | `testprotocols.host_filter:HostFilter` (`block_host`, `unblock_host`, `get_host_block`, `list_host_blocks`) with `testprotocols.models.cpe_gateway:Weekday`, `WeeklySchedule`, `HostBlock` | new capability | core | no | accepted with conditions (C3, C7), 2026-10-20 |
| M12 | new protocol | `testprotocols.auto_port_mapping:AutoPortMapping` (`set_enabled`, `get_enabled`, `list_mappings`) with `testprotocols.models.cpe_gateway:AutoMappingProtocol`, `AutoPortMappingEntry` | new capability | core | no | accepted, 2026-10-20 |
| M13 | new protocol | `testprotocols.admin_credential:AdminCredential` (`set_password`, `list_accounts`) | new capability | core | no | accepted, 2026-10-20 |
| M14 | new protocol (split) | `testprotocols.device_health:DeviceHealth` (`is_online`, `get_seconds_uptime`, `read_cpu_load`, `read_memory_utilization`, `read_running_processes`, `read_log_entries`), inherited by `DeviceManagement`; with `testprotocols.models.device_management:CpuLoad` (`percent: float \| None`, `load_average_1m: float \| None`) | new capability | core | no | accepted, 2026-10-20 |
| M15 | protocol extension | `testprotocols.device_management:DeviceManagement.read_cpu_load` (through the inherited base, M14); `get_load_avg` unchanged | extend | core | yes | accepted, 2026-10-20 |
| M16 | SPLITS entry | `DeviceHealth` split off `DeviceManagement` so a closed product composes the health reads without the host-shaped members; follows `GAPS.md` 2026-06-11 and the `RoutingRead` read-only split precedent | record | core | no | accepted, 2026-10-20 |
| M17 | GAPS entry | update to `GAPS.md` 2026-06-11 (appliance health): the read-only base landed as M14; the appliance composes it when its trigger lands | record | core | no | accepted, 2026-10-20 |
| M18 | protocol extension | `testprotocols.device_info:DeviceInfo`: properties `manufacturer`, `serial_number`, `software_version`, `oui`, `hardware_version`; module docstring's extension point taken | extend | core | yes | accepted, 2026-10-20 |
| M19 | protocol extension | `testprotocols.device_lifecycle:DeviceLifecycle`: `upgrade_firmware`, `export_configuration`, `import_configuration`; module docstring generalised from CPE to any device; with `testprotocols.models.device_management:ImageSource` (`url`, `checksum_sha256: str \| None`) | extend | core | yes | accepted, 2026-10-20 |
| M20 | rename | `testprotocols.device_lifecycle:DeviceLifecycle.verify_cpe_is_booting` → `verify_booting`, both declared for the period, the old delegating; lands with M19 | deprecate | core | no | accepted, 2026-10-20 |
| M21 | GAPS entry | the staged firmware pair (`stage_image` / `activate_image`) as the finer grain of M19's `upgrade_firmware`: no reviewed column publishes a staged-image read (§6) | record | tier-staged — the first dual-image product that needs the staged state read | no | accepted, 2026-10-20 |
| M22 | protocol extension | `testprotocols.tr069_client:Tr069Client`: `set_acs`, `get_acs`; `force_inform` docstring states the per-column meaning (§6) and names no vendor command or daemon; with `testprotocols.models.tr069:AcsConfig` | extend | core | yes | accepted, 2026-10-20 |
| M23 | protocol extension | `testprotocols.ntp_config:NtpConfig.get_sync_state`; with `testprotocols.models.switch:NtpSyncStatus`, `NtpSyncState` beside `NtpServer` | extend | core | yes | accepted, 2026-10-20 |
| M24 | protocol extension | `testprotocols.wifi_onboarding:WifiOnboarding`: `cancel_wps`, `get_wps_state`; module docstring's `NotImplementedError` wording replaced by the documented unsupported case; with `testprotocols.models.wifi:WpsSessionState`, `WpsMethod`, `WpsState` | extend | core | yes | accepted with conditions (stage 4: R28 ◐ on column 4, push-button only, the PIN members raise), 2026-10-20 |
| M25 | new field | `testprotocols.models.switch_routing:InterfaceDhcpConfig.pool_start`, `pool_end` (`str \| None = None`; `None` = the whole subnet minus the reserved ranges, the shape served today) | defaulted field | core | no | accepted, 2026-10-20 |
| M26 | SPLITS entry | `InterfaceDhcpConfig` gains the pool bounds with the appliance meaning preserved as the default (M25); the port-forward shapes (`Firewall` per-mapping for gateways, `ApplianceNat` list-replacing for appliances) recorded as two shapes for two device classes | record | core | no | accepted, 2026-10-20 |
| M27 | LEVELS entry | the white-box candidates of §7 recorded as candidates, not seeded (`WanConnectionWhiteBox`, `L2BridgeWhiteBox`, `HostFilterWhiteBox`, `DnsForwarderWhiteBox`, `DeviceHealthWhiteBox`, `Tr069ClientWhiteBox`, `UspAgentWhiteBox`, `InterfaceDhcpWhiteBox`), with the columns expected to satisfy (1, 2, 3, 5) and not (4) | record | core | no | accepted, 2026-10-20 |
| M28 | composition | `testprotocols.wan_link_admin:WanLinkAdmin` on `CpeGatewayDevice` as `wan_admin`, `get_wan_state` its paired read on this class; module docstring generalised at stage 4 (the lever is published by four of five gateway columns) | reuse | core | no | accepted, 2026-10-20 |
| M29 | SPLITS entry | `WanLinkAdmin` composed by a closed product: the 2026-06-12 rationale ("implemented only by the Linux twin") narrowed to "not by API-managed appliances", on the matrix evidence of R9 | record | core | no | accepted, 2026-10-20 |
| M30 | composition | `testprotocols.port_status:PortStatus`, `testprotocols.dhcp_client:DhcpClient`, `testprotocols.interface_dhcp:InterfaceDhcp`, `testprotocols.syslog_config:SyslogConfig`, `testprotocols.network_endpoint:NetworkEndpoint` on `CpeGatewayDevice` | reuse | core | no | accepted, 2026-10-20 |
| M31 | composition | `testprotocols.wifi_radio:WifiRadio`, `testprotocols.wifi_bss:WifiBss`, `testprotocols.wifi_stations:WifiStations`, `testprotocols.wifi_transitions:WifiTransitions`, `testprotocols.firewall:Firewall`, `testprotocols.firewall_zones:FirewallZones` on `CpeGatewayDevice`; their members without a matrix row are verification items (§9); the `firewall` driver refuses rule writes on a host block (§6) | reuse | core | no | accepted with conditions (C7; stage 4: R23 ◐ on column 4 and R22's power limit on column 3, the radio reads and setters named in §6 raise there), 2026-10-20 |
| M32 | new protocol (tier) | `testprotocols.voice_gateway:VoiceGateway` (`set_sip_account`, `remove_sip_account`, `list_sip_accounts`, `get_sip_registration`, `list_fxs_lines`) with `testprotocols.models.voice:SipRegistrationState`, `FxsHookState`, `SipAccount`, `SipRegistration`, `FxsLine` | new capability | tier-staged — a third column supporting the SIP account (R54) beside columns 3 and 4, the majority of five, or a consumer | no | tier-staged (stage 4: voice R54–R55 ✗ on columns 1, 2 and 5 — 2 of 5 — 2026-10-20) |
| M33 | composition (tier) | `testprotocols.wifi_mesh:WifiMesh` on `CpeGatewayMeshTier`; its agent-side members are verification items (§9); module docstring's `NotImplementedError` wording replaced by the documented unsupported case | reuse | tier — mesh | no | accepted with conditions (stage 4: R58 ✗ on column 5, `steer_client` raises there; column 3 confirmed on the mesh build variant), 2026-10-20 |
| M34 | new field (tier) | `testprotocols.models.wifi:WifiMeshNode.backhaul_link` (`WifiMeshLink \| None = None`; `None` also for a wired backhaul) | defaulted field | tier — mesh | no | accepted, 2026-10-20 |
| M35 | new protocol (tier) | `testprotocols.usp_agent:UspAgent` (`set_controller`, `get_controller`, `get_agent_state`) with `testprotocols.models.cpe_gateway:UspTransport`, `UspController`, `UspAgentState` (`endpoint_id` only) | new capability | tier — usp | no | accepted with conditions (stage 4: `UspAgentState.connected` dropped, no column publishes a connection state), 2026-10-20 |
| M36 | DEPRECATIONS entry | the `class` row of M2 in `packages/testprotocols/DEPRECATIONS.md` (`next release` / `next release + 6 months`), beside the *Deprecated* changelog entry; the M20 `member` row | record | core | no | accepted, 2026-10-20 |
| M37 | GAPS entry | `CpeGatewayDevice` design record and matrix (this document); the dropped members `wifi_rf` and `network_probe` with their trigger (a sourced matrix row); DS-Lite as a `WanIpv6` part with its trigger (a matrix row) | record | core | no | accepted, 2026-10-20 |
| M38 | testoperations change | `testoperations.device_management:wait_for_reboot_completion` widened from `DeviceManagement` to the health base of M14, so it accepts both classes (`is_cpe_online` takes `Tr069Server` and is unaffected); the candidates of §6 (guest segment, WAN reconnect, second-session credential check, export-change-import-compare) recorded for the stage-4 collector | record | core | no | accepted with conditions (C1), 2026-10-20 |

M9's note keeps the unrealised half of the `L2Bridge` entry (STP tuning,
forwarding-table read) visible; M17, M26 and M29 update records this design
relies on rather than contradicts; M3, M21 and M32 are the `tier-staged` rows
(M3 and M32 since stage 4).

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
- **2026-10-19 — maintainer decisions recorded for the design (stage 3).**
  Taken before the design was written and binding on it: (1) a caveated
  matrix cell (◐) counts as support for the evidence bar, its limit becoming
  the member's documented per-column behaviour or a per-method unsupported
  case; (2) the existing archetype is superseded by a new class under a new
  registry key, the old class kept intact and deprecated as a `class` row
  for one MINOR release and six months, because an alias of the new class
  under the old key would fail the existing consumer's driver at load;
  (3) tiers whose matrix evidence is a majority of the ratified list are
  built in the pass (the evidence bar as amended on 2026-10-19, #97);
  (4) the identity, health, lifecycle and configuration-transfer members
  are introduced here as generic capabilities worded for any closed network
  product, so the chartered router sibling composes them when its design
  lands, rather than each design introducing its own.
- **2026-10-19 — design opened (stage 3).** §3–§8, §11 and §12 written on
  the exploration's matrix with ◐ counting as support: 52 of 58 operations
  on the core (R1–R52), three tiers built in this pass (`voice`, `mesh`,
  `usp`), one `tier-staged` row (the staged firmware pair). Ten new
  capabilities (seven core, one split, two tier), six protocol extensions,
  two defaulted-field rows, two deprecations (the superseded class, one
  method rename), four reuse rows covering fourteen protocols, and eight
  tracking-file records; 38 manifest rows, every Outcome `pending review`.
  §9 names the nominal ◐ cells and the trigger-column gaps as the design's
  stated risk and lists the reused protocols' members without a matrix row
  as verification items. One departure from the brainstorm's wording is
  flagged for the maintainer: firmware upgrade is one member, the staged
  pair `tier-staged`, because no reviewed column publishes a staged-image
  read. The charter's knowledge-base citation re-pointed (§10). A fresh
  final review of the branch before this PR opened returned two critical
  and twelve important findings, all folded back here (un-evidenced members
  of reused protocols, trigger-column gaps, four missing §6 decisions, the
  tier flip arithmetic, a duplicated admin-state encoding, secrets read
  back, the multi-step table, private decision labels, the DHCP pool
  bounds, tier registration, the core count).
- **2026-10-20 — design review, round 1 (on 382011b): approve with
  conditions (C1–C8, N1–N10). Status moved to `accepted for verification`;
  every manifest row carries its outcome.** Applied:
  - C1 the `testoperations` widening names `wait_for_reboot_completion` only;
    `is_cpe_online` takes the test-bed ACS and is unaffected (§6 Health, §6
    method grain, M38).
  - C2 every row outcomed with the conditions it carries; Status set.
  - C3 the §8 normalisations carried into the members: `get_upstreams` and
    `get_members` promise the set, not the order; a column-4
    `DnsHostOverride.name` the device would rewrite is rejected before the
    write; MACs on `HostBlock`, `LanHost` and the `get_host`,
    `get_host_block` and `unblock_host` arguments are the canonical lowercase
    colon-separated form, canonicalised on read and normalised on write (§6,
    precise types).
  - C4 column 2's failure outcome corrected: staged changes outlive the
    call, so the driver stages each write under its own change-file path and
    a rejected write's steps are never committed, with no write on the
    failure path (§8, §6 WAN connection, method-grain table).
  - C5 `create_bridge` creates the bridge only; `BridgeConfig` carries no
    membership and `add_member` / `remove_member` are its only writes (§6
    Bridge, precise types, method-grain table).
  - C6 `reset_session` narrowed to the PPPoE session reset R4 evidences; on
    the other modes it raises and points at `dhcp_client` and `wan_admin`.
  - C7 on columns 1 and 2 the `firewall` driver refuses `remove_rule`,
    `flush_chain` and `set_default_policy` on a rule or chain that realises a
    host block, naming `host_filter` as the owner (§6, M31).
  - C8 `set_upstreams` rewrites the existing forwarding instances in place on
    columns 1 and 3, is one commit on column 2 and one property set on
    column 5 (§6, method-grain table).
  Notes: N1 the appliance-health claim restated with the two differences from
  the sketch (uptime not optional, process list present), recorded by M17;
  N2 the mesh risk row says steering is implemented on columns 1 and 5 after
  a column-3 flip; N3 Kind values aligned where the README has a word
  (`rename`, `new field`), and M38 keeps `record` because the Mechanism
  vocabulary has no value for a `testoperations` widening and `hygiene`
  accepts it; N4 the §5 switch claim dropped, `ImageSource` placed in
  `models/device_management.py` and the NTP types beside `NtpServer`; N5 a
  stated-risk row for the zone writes (column 2 only); N6 the `force_inform`
  docstring rewrite names no vendor command or daemon (M22); N7 the state,
  static-addressing and controller fields typed with their absence meaning;
  N8 `HostAttachment` closed with `None` for other media, reserved ranges
  must lie inside the pool bounds; N9 the bridge-membership versus
  `wifi_bss` VLAN boundary stated; N10 the connection's resolvers kept apart
  from the configured upstreams, `set_upstreams` never touching them.
- **2026-10-20 — stage 4a: core code landed on this PR.** Every `core` and
  `tier` row of §12 is implemented (commits `d2abb3c..d7e819c`, plus the
  records commit carrying this entry): ten capability
  protocols, six extensions, the archetype and three unregistered tier
  Protocols, the superseded class and one method deprecated with their
  register rows, the two defaulted fields, the tracking-file records M9, M16,
  M17, M21, M26, M27, M29, M36, M37 and the `testoperations` widening M38.
  The §4 listing's lifecycle comment corrected to the one-member decision of
  §6. Stage 4b (the reference drivers) follows in the private corpus.
- **2026-10-20 — stage 4b: reference drivers written in the private corpus.**
  Five drivers (one per column) at corpus commit `9c2812b`, run against this
  PR's head `47954b1` through the corpus's `.testprotocols` checkout (its
  `TESTPROTOCOLS_REF` then still `main`); after this fold-back the corpus
  followed the voice withdrawal and the `connected` drop at `f5a5075`, run
  against this PR's `3a13607` (`9c2812b` imports the withdrawn tier and does not
  run against it); the pin to this PR's head `56b3cdc` is corpus commit
  `026d684`, the commit the verification review ran against. MATRIX (core, 154 members, ✓/✗): column 1 140/14,
  column 2 148/6, column 3 129/25, column 4 86/68, column 5 124/30; tiers as
  built: voice on none (`tier-staged`), mesh on columns 1, 3, 4 and 5, USP on
  columns 1, 3 and 4. Findings folded:
  - cell corrections (13): R54–R55 ✗ on columns 1 and 2; R3–R4 ◐ on column 3;
    R58 ✗ on column 5; R23 and R28 ◐ on column 4; the limit text of R21
    (column 2), R16 and R22 (column 3), R22 (column 4) and R54–R58 (column 3)
    corrected (§2, §10);
  - cells that stand with a per-method case (44): recorded in §6, §8 and the
    §9 member table, except five low-value items (unverified or not graded)
    that stay in the corpus's FINDINGS and EVIDENCE only: column 1's R1–R7
    secondary paths and its R57 "could be ✓", column 3's R30 zone-preset
    reading, column 4's upstream-link selection for R57, and column 5's
    further per-value refusals;
  - design-text corrections (32): §6, §8 and §9 as listed in this entry's
    rulings and the sections themselves (the column-2 change-file flag and its
    per-session path, the column-1 and column-3 chain models, the
    satisfied-state write, the column-4 login reads, the column-5 REST route,
    the column-3 build facts);
  - `lossy:`, `partial:` and `unverified:` lines: recorded in the corpus, not
    in this design (since 2026-10-21 the `lossy:` lines are also in §8 "Lossy
    mappings as built");
  - six corpus-only records: settled in the corpus, not folded.
  The TR-069 route on column 1 decided: `set_acs` / `get_acs` through the
  data model's management-server object, `force_inform` and
  `is_tr069_connected` through the CWMP client's own bus object (§6 Decided
  as verification items); the two halves cite two clients' documents, and
  whether the data-model client's image registers the same bus object is
  unverified. 180 `lossy:` and 89 `partial:` lines recorded in the corpus
  (48 `unverified:`), as recounted after the final-review fix wave at corpus
  commit `0123313`, pinned at `026d684`. Nominal cells: voice flipped (columns 1 and 2), mesh on
  column 3 confirmed on the family's mesh build variant, USP on column 1
  confirmed. Maintainer rulings applied:
  - (1) the voice tier drops to `tier-staged`: §6's rule (a tier stays built
    while a majority of the five supports its defining operation) with R54
    on columns 3 and 4 only, two of five. The tier Protocol, `VoiceGateway`
    and its five records are withdrawn from this PR (the pre-existing voice
    models stay); M3 and M32 re-outcomed `tier-staged` with their trigger (a
    third column supporting the SIP account beside columns 3 and 4, the
    majority of five, or a consumer); the `GAPS.md`
    CPE gateway entry points at them. **Finding for the owner:** this
    design's denominator ("a majority of the five") is stricter than the
    public README's evidence bar ("a majority of the ratified list"), under
    one reading of which voice at two of three would have stayed built; the
    owner decides later whether to align them, and this PR follows the
    design.
  - (2) `UspAgentState.connected` dropped (§6's own condition: no column
    publishes a connection state; columns 1, 3 and 4 read `None`); M35
    re-outcomed.
  - (3) R22/R23 and R28 on column 4 graded ◐ with the limit named (channel
    and enable published, power, width, country and DFS not; WPS push-button
    start, stop and status published, the PIN obsolete); the family evidence
    had them ✓; M24 and M31 re-outcomed.
  - (4) R58 on column 5 is ✗ (no per-client steering), not the stage-3 ◐;
    M33 re-outcomed.
  - (5) three stage-4a text minors: the `import_configuration` observation
    worded the same way in §6, the method-grain table and the protocol
    docstring (the test re-reads a setting it changed after the export); the
    stage-4a commit range written `d2abb3c..d7e819c` (a git range excludes its
    left commit); the changelog's archetype entry recounted after the voice
    withdrawal (eight of the twenty-six capability members are new
    protocols, the split health base among them).
  - (6) every other cell and text correction of the corpus findings applied
    as listed above; M6 re-outcomed for R3–R4.
- **2026-10-21 — stage 4b: verification review folded; Status `verified`.**
  The verification review ran on this PR's head `56b3cdc` against corpus
  commit `026d684`, the pin to that head (`conformance`: 5 of 5 families).
  Code leg: approve with conditions (C1, negative-path shape tests) and notes
  N1–N8. Archetype leg: approve with conditions C1–C6 (its review text was
  withheld by the review runner's corpus-content guard on two false
  positives, since fixed in the runner; the verdict and conditions are taken
  from the kept transcript, and the re-review posts them). Folded: code C1 and
  notes N2, N3, N5–N7 (`5f599f2`); design C4, C5 and C6 (`4b73fd6`) and this
  entry with §8 "Lossy mappings as built"; corpus C1 (WAN mode contradictions
  refused before any send and the PPPoE reset raising off PPPoE on columns 1,
  3 and 4), C2 (the delete-then-add windows closed by in-place rewrites:
  upstreams, static resolvers, host-block schedules, and the DHCP options and
  reservations under the same rule), C3 (every OpenWrt write step
  acknowledged by its exit status) and C5 (the build condition in the
  column-3 source line), at corpus commits `0c311ae..c58db69`; the pin to
  this PR's head `174c69a` is corpus commit `be0f1c6`, the commit the second
  verification review (2026-10-22) ran against. Counts after
  the fold: 180 `lossy:`, 89 `partial:` and 48 `unverified:` lines in the
  drivers (one new: a column-3 write that moves a reservation's name between
  hosts may meet a duplicate-alias refusal partway, naming the step). Family
  facts stated: the column-1 reservation rename (§8). Owner items unchanged:
  the tier denominator and the satisfied-state write (above).
- **2026-10-22 — stage 4b: second verification review folded.**
  The second verification review ran on this PR's head `174c69a` against
  corpus commit `be0f1c6`, the pin to that head (`conformance`: 5 of 5
  families). Code leg: approve with conditions (C1, `DeviceHealth` in the
  negative-path shape tests) and notes N1–N5. Archetype leg: approve with
  conditions C1 (every column-1 write step acknowledged; the controller read
  raising on a reply without the controller's host or port) and C2 (the
  column-4 and column-5 host-filter step counts in §6 and the method-grain
  table) and notes N1–N8. Neither review text was posted by the review runner
  (a refused write on one leg, a withheld text on the other, both since fixed
  in the runner); the verdicts and conditions are taken from the kept
  transcripts. Folded: code C1 and N1, N2, N3, N5 and archetype C2, N7
  (`16a21e3`); archetype N6, the column-1 acknowledgement rule in §8, §8
  "Lossy mappings as built" re-recorded, and this entry (the commit after it);
  corpus C1 and notes N1 (the ubus command-line client's source cited for the
  `Command failed:` refusal), N3 (a scheduled block on column 4 clears a block
  at all times), N4 (a column-1 mode change off `STATIC` removes the static
  route and resolvers the driver wrote) and N5 (column 1 reports no
  provisioning mode while no address is up), at corpus commits
  `103a53e..1448bb8`; the pin to this PR's new head follows `1448bb8` on the
  companion branch. Counts after the fold: 182 `lossy:`, 89 `partial:` and 50
  `unverified:` lines in the drivers (new `lossy:`: the column-1 controller
  read that raises on a reply without the controller's parameters, and the
  column-4 two-action scheduled block over a block at all times; new
  `unverified:` on column 1: a data-model method call's silent success, and
  the set echo documented in an interactive session while the driver runs
  one-shot commands). Deferred: N8 (the column-5 mode-change order; its
  `lossy:` line states the order). Owner items: the tier denominator and the
  satisfied-state write (above); code N4, the contract-surface script not
  following an inherited base (a tooling follow-up).
