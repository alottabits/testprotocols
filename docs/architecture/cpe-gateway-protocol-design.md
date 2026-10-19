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
  configuration backup and restore, no USP, no voice, no mesh (health —
  uptime, load, memory, logs — it has, through `device_management`). A tier of it cannot close the
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
  extending the other; software lifecycle, configuration transfer, identity
  and health are demands both charters carry and whose placement each design
  decides, so the two designs record the dependency on each other's rows
  rather than assume a shared protocol. The router publishes what the gateway does
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
- **OpenWrt 24.10 stable, with icwmp from the public iopsys feed as its
  TR-069 client.** The substrate under prplOS and under many retail routers;
  UCI and ubus; no TR-181 data model, no mesh controller
  (https://openwrt.org/releases/24.10/start — 24.10.0 released February
  2025, 24.10.8 on 26 July 2026). The family is named with its TR-069 client
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
| OpenWrt 24.10 stable with icwmp (iopsys feed) | trigger | triggering consumer; the substrate under prplOS and many retail routers; UCI/ubus with a packaged TR-069 client, no data model, no mesh |
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

Not reviewed: **ADTRAN SmartOS, Zyxel, TP-Link, Calix**. This charter makes
no claim about their published operations; any of them can join the list by
a dated revision.

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
  26 July 2026). The official feeds at the 24.10 branch:
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
  lever; lifecycle, identity and health are demands both charters carry, not
  shared protocols; sources for every version line added; the evidence-bar
  paraphrase aligned with the README; one line wrapped. One finding
  rejected: `tr069_client` is a member of `CpeDevice` (`devices/cpe.py`).
