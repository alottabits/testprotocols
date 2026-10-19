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

Also excluded, with reasons: **ADTRAN SmartOS** (SmartOS 11 and later is
built on prplWrt, the predecessor of prplOS, so its published operations are
covered by the prplOS family; a dated revision brings it in if its data model
diverges); **Zyxel** (operator and retail gateways on vendor firmware managed
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
| R1 | Set the WAN connection mode (DHCP, static, PPPoE, IPoE) | ? | ✓ [1] | ? | ? | ? |
| R2 | Read WAN connection state, address and lease | ? | ✓ [2] | ? | ? | ? |
| R3 | Set PPPoE credentials and service name | ? | ✓ [3] | ? | ? | ? |
| R4 | Reset the PPPoE session | ? | ✓ [4] | ? | ? | ? |
| R5 | Set the WAN VLAN id and priority | ? | ◐ VLAN id via `8021q` `vid`; 802.1p priority mapping undocumented [5] | ? | ? | ? |
| R6 | Set the IPv6 WAN mode; read the delegated prefix | ? | ✓ [6] | ? | ? | ? |
| R7 | Read the provisioning mode (v4, v6, dual) | ? | ◐ no mode field; derive from wan/wan6 interface status [7] | ? | ? | ? |
| R8 | Read WAN link state | ? | ✓ [8] | ? | ? | ? |
| R9 | Administratively disable / enable the WAN | ? | ✓ [9] | ? | ? | ? |
| R10 | Renew / release the WAN DHCP lease | ? | ◐ wiki shows `ifdown`/`ifup` only; `renew` method only in netifd source [10] | ? | ? | ? |
| | **LAN services** |  |  |  |  |  |
| R11 | Configure the DHCP server pool and lease time | ? | ✓ [11] | ? | ? | ? |
| R12 | Configure DHCP options | ? | ✓ [12] | ? | ? | ? |
| R13 | Configure static leases | ? | ✓ [13] | ? | ? | ? |
| R14 | Read active leases | ? | ◐ dnsmasq leases are a file; ubus `dhcp ipv4leases` is odhcpd-only [14] | ? | ? | ? |
| R15 | Configure DNS forwarder upstreams | ? | ✓ [15] | ? | ? | ? |
| R16 | Configure local host overrides | ? | ✓ [16] | ? | ? | ? |
| R17 | Configure DNS rebind protection | ? | ✓ [17] | ? | ? | ? |
| R18 | Configure bridge membership (ports, wireless networks) | ? | ✓ [18] | ? | ? | ? |
| R19 | Read bridge and port membership | ? | ◐ UCI `ports` gives config; live membership via `bridge` shell [19] | ? | ? | ? |
| R20 | Configure a guest segment | ? | ✓ [20] | ? | ? | ? |
| R21 | Read LAN port status (link, speed, duplex) | ? | ◐ `link` via network.device status; speed/duplex need ethtool/swconfig [21] | ? | ? | ? |
| | **Wi-Fi access points** |  |  |  |  |  |
| R22 | Configure radio (band, channel, width, power, enable) | ? | ✓ [22] | ? | ? | ? |
| R23 | Read radio state | ? | ✓ [23] | ? | ? | ? |
| R24 | Configure a BSS (SSID, security mode, passphrase, hidden) | ? | ✓ [24] | ? | ? | ? |
| R25 | Read BSS state | ? | ✓ [25] | ? | ? | ? |
| R26 | Read connected stations (signal, rate) | ? | ✓ [26] | ? | ? | ? |
| R27 | Disconnect a station | ? | ◐ `del_client` only in hostapd ubus source, no wiki page [27] | ? | ? | ? |
| R28 | Start / cancel push-button or PIN onboarding; read its state | ? | ◐ PBC via `wps_pushbutton`/hostapd_cli; `wps_start`/`wps_status` source-only [28] | ? | ? | ? |
| R29 | Configure band steering and 11k/v/r | ? | ✓ [29] | ? | ? | ? |
| | **Security posture** |  |  |  |  |  |
| R30 | Read zone defaults and zone membership | ? | ✓ [30] | ? | ? | ? |
| R31 | Add / remove a port forward | ? | ✓ [31] | ? | ? | ? |
| R32 | Read the port-forward table | ? | ✓ [32] | ? | ? | ? |
| R33 | Add / remove an egress filter rule | ? | ✓ [33] | ? | ? | ? |
| R34 | Read filter rules | ? | ✓ [34] | ? | ? | ? |
| R35 | Block a host, on demand or on a schedule | ? | ✓ [35] | ? | ? | ? |
| R36 | Enable / disable automatic port mapping (UPnP IGD, PCP) | ? | ✓ [36] | ? | ? | ? |
| R37 | Read automatic port mappings | ? | ◐ lease file only; no documented read command [37] | ? | ? | ? |
| | **Host table** |  |  |  |  |  |
| R38 | Read the host table (address, name, attachment) | ? | ◐ no unified host table; DHCP leases + `ip neigh`/LuCI hints [38] | ? | ? | ? |
| | **Device operations** |  |  |  |  |  |
| R39 | Read identity (manufacturer, model, serial, OUI, software version) | ? | ◐ `system board` lacks serial, manufacturer, OUI [39] | ? | ? | ? |
| R40 | Read uptime, load, memory | ? | ✓ [40] | ? | ? | ? |
| R41 | Read process state | ? | ✓ [41] | ? | ? | ? |
| R42 | Read device logs | ? | ✓ [42] | ? | ? | ? |
| R43 | Configure log export | ? | ✓ [43] | ? | ? | ? |
| R44 | Configure NTP servers; read sync state | ? | ◐ servers via `system.ntp.server`; sync state needs ntp-utils `ntpq` [44] | ? | ? | ? |
| R45 | Upgrade firmware from an image | ? | ✓ [45] | ? | ? | ? |
| R46 | Factory reset | ? | ✓ [46] | ? | ? | ? |
| R47 | Reboot; read readiness | ? | ◐ `reboot` documented; readiness inferred from `system info` uptime, no flag [47] | ? | ? | ? |
| R48 | Export configuration | ? | ✓ [48] | ? | ? | ? |
| R49 | Import configuration | ? | ✓ [49] | ? | ? | ? |
| R50 | Set the local administrator credential | ? | ✓ [50] | ? | ? | ? |
| | **Remote management** |  |  |  |  |  |
| R51 | Configure ACS URL, credentials and periodic inform | ? | ✓ [51] | ? | ? | ? |
| R52 | Trigger an inform; read connection-request state | ? | ◐ `status` reports session state, not connection-request state [52] | ? | ? | ? |
| R53 | Configure the USP controller endpoint and transport; read agent state | ? | ✗ no USP agent (obuspa) in 24.10 packages/luci/routing/telephony feeds [53] | ? | ? | ? |
| | **Voice** |  |  |  |  |  |
| R54 | Configure a SIP account; read registration state | ? | ◐ Asterisk PBX config files + CLI; no UCI/ubus voice model [54] | ? | ? | ? |
| R55 | Read FXS line state | ? | ◐ asterisk-chan-lantiq Lantiq SoC FXS only; state via Asterisk CLI [55] | ? | ? | ? |
| | **Mesh controller** |  |  |  |  |  |
| R56 | Read mesh topology (agents, backhaul links) | ? | ✗ no EasyMesh controller; 802.11s is a peer mesh [56] | ? | ? | ? |
| R57 | Read backhaul link health | ? | ✗ 802.11s peer links via `iw station dump`, not EasyMesh backhaul [57] | ? | ? | ? |
| R58 | Steer a client to another agent | ? | ◐ usteer roams clients between plain APs; no EasyMesh agents [58] | ? | ? | ? |

## 10. Sources

The charter (§1) carries the sources for the version lines. The matrix
sources follow, one numbered list per family; a cell's `[n]` resolves to
entry `n` of its column's list. Each entry: title — URL — section or anchor —
what it establishes. The vendor-isolation rule forbids vendor names and URLs
in the package source, not in this design record.

### prplOS 4.0 line

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
12. DHCP and DNS configuration — <https://openwrt.org/docs/guide-user/base-system/dhcp> — `list dhcp_option '3,192.168.1.1'`, `dhcp_option_force` — per-pool DHCP options in `code,value` or `option:name,value` form
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

### FRITZ!OS 8.20 and later

### RouterOS v7

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
  lever; software lifecycle and configuration transfer are demands both
  charters carry, not shared protocols; sources for every version line added; the evidence-bar
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
