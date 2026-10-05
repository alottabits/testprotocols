# pyright: reportUnnecessaryTypeIgnoreComment=true
"""Each use below must be reported as deprecated; an unused ignore fails the type check.

Type-checked only, never imported by pytest. Every line uses one deprecated member or
class and carries ``# type: ignore[deprecated]``. Without the member's ``@deprecated``
marker the ignore is unused: mypy reports it (``warn_unused_ignores``) and pyright
reports it too (the file-level ``reportUnnecessaryTypeIgnoreComment`` above). Pyright
honours ``# type: ignore``, so the one comment serves both checkers.

A class is used through its module, not imported by name: in a multi-line import mypy
reports a deprecated name on the statement's first line and pyright on the name's own
line, so no single comment would serve both.
"""

from testprotocols import models
from testprotocols.arp_client import ArpClient
from testprotocols.content_filtering import ContentFiltering
from testprotocols.device_management import DeviceManagement
from testprotocols.dns_client import DnsClient
from testprotocols.iperf_client import IperfClient
from testprotocols.iperf_server import IperfServer
from testprotocols.nat import Nat
from testprotocols.netem_controller import NetemController
from testprotocols.nmap_scanner import NmapScanner
from testprotocols.ntp_client import NtpClient
from testprotocols.packet_filter import PacketFilter
from testprotocols.router import Router
from testprotocols.sdwan_policy_manager import SdwanPolicyManager
from testprotocols.sip_server import SipServer
from testprotocols.snmp_client import SnmpClient
from testprotocols.wifi_client import WifiClient
from testprotocols.wifi_radio import WifiRadio


def uses(
    arp: ArpClient,
    content: ContentFiltering,
    device: DeviceManagement,
    dns: DnsClient,
    iperf_client: IperfClient,
    iperf_server: IperfServer,
    nat: Nat,
    netem: NetemController,
    nmap: NmapScanner,
    ntp: NtpClient,
    packet_filter: PacketFilter,
    router: Router,
    policy: SdwanPolicyManager,
    sip: SipServer,
    snmp: SnmpClient,
    wifi: WifiClient,
    radio: WifiRadio,
) -> list[object]:
    return [
        models.TrafficShapingRule,  # type: ignore[deprecated]
        models.VPNPeerStatus,  # type: ignore[deprecated]
        arp.get_arp_table,  # type: ignore[deprecated]
        content.get_url_rules,  # type: ignore[deprecated]
        device.get_memory_utilization,  # type: ignore[deprecated]
        device.get_running_processes,  # type: ignore[deprecated]
        device.read_event_logs,  # type: ignore[deprecated]
        dns.dns_lookup,  # type: ignore[deprecated]
        iperf_client.start_traffic_sender,  # type: ignore[deprecated]
        iperf_server.start_traffic_receiver,  # type: ignore[deprecated]
        nat.get_nat_rule_counters,  # type: ignore[deprecated]
        netem.inject_transient,  # type: ignore[deprecated]
        nmap.nmap,  # type: ignore[deprecated]
        ntp.get_date,  # type: ignore[deprecated]
        ntp.set_date,  # type: ignore[deprecated]
        packet_filter.get_rule_counters,  # type: ignore[deprecated]
        router.get_telemetry,  # type: ignore[deprecated]
        policy.apply_policy,  # type: ignore[deprecated]
        sip.get_rtpengine_stats,  # type: ignore[deprecated]
        sip.get_mwi_status,  # type: ignore[deprecated]
        sip.get_offline_messages,  # type: ignore[deprecated]
        snmp.execute_snmp_command,  # type: ignore[deprecated]
        wifi.iwlist_supported_channels,  # type: ignore[deprecated]
        radio.get_mode,  # type: ignore[deprecated]
    ]
