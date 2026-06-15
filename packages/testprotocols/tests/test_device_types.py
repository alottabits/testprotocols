"""Tests for the device-archetype registry.

The registry maps inventory ``device_type`` strings to ``@runtime_checkable``
Protocol classes. Each archetype Protocol declares the aggregate of capability
attributes a conforming driver must provide. These tests verify both the
inventory-string -> Protocol binding and the per-archetype capability set
(via ``__protocol_attrs__``).
"""

from __future__ import annotations

import pytest

from testprotocols.devices import DeviceTypeSpec, all_device_types, get_device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.devices.client import (
    LanClientDevice,
    QoeClientDevice,
    QoeMeasurementClientDevice,
    WlanClientDevice,
)
from testprotocols.devices.cpe import CpeDevice
from testprotocols.devices.infra import AcsDevice, ProvisionerDevice, TftpDevice
from testprotocols.devices.sdwan import SdwanApplianceDevice, SdwanRouterDevice
from testprotocols.devices.traffic import (
    IperfTrafficGeneratorDevice,
    TrafficControllerDevice,
)
from testprotocols.devices.voice import SipPhoneDevice, SipServerDevice
from testprotocols.devices.switch import L2Switch, L3Switch, L3SwitchRouted
from testprotocols.devices.wan import WanServerDevice

_ALL_ARCHETYPES = (
    AcsDevice,
    CpeDevice,
    IperfTrafficGeneratorDevice,
    L2Switch,
    L3Switch,
    L3SwitchRouted,
    LanClientDevice,
    ProvisionerDevice,
    QoeClientDevice,
    QoeMeasurementClientDevice,
    SdwanApplianceDevice,
    SdwanRouterDevice,
    SipPhoneDevice,
    SipServerDevice,
    TftpDevice,
    TrafficControllerDevice,
    WanServerDevice,
    WlanClientDevice,
)

# ---------------------------------------------------------------------------
# Registry plumbing
# ---------------------------------------------------------------------------


def test_get_unknown_returns_none() -> None:
    assert get_device_type("nonexistent") is None


def test_all_device_types_registered() -> None:
    expected = {
        "linux_lan_client",
        "linux_wlan_client",
        "linux_qoe_client",
        "linux_qoe_measurement_client",
        "linux_cpe",
        "linux_acs",
        "linux_provisioner",
        "linux_tftp",
        "linux_sdwan_router",
        "sdwan_appliance",
        "linux_traffic_controller",
        "iperf_traffic_generator",
        "linux_sip_phone",
        "linux_sip_server",
        "linux_wan_server",
        "managed_switch_l2",
        "managed_switch_l3",
        "managed_switch_l3_routed",
    }
    assert expected == set(all_device_types().keys())


# ---------------------------------------------------------------------------
# Per-archetype: inventory string -> Protocol class binding
# ---------------------------------------------------------------------------


def test_sdwan_router_registered() -> None:
    spec = get_device_type("linux_sdwan_router")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is SdwanRouterDevice


def test_sdwan_appliance_registered() -> None:
    spec = get_device_type("sdwan_appliance")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is SdwanApplianceDevice


def test_cpe_registered() -> None:
    spec = get_device_type("linux_cpe")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is CpeDevice


def test_lan_client_registered() -> None:
    spec = get_device_type("linux_lan_client")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is LanClientDevice


def test_wlan_client_registered() -> None:
    spec = get_device_type("linux_wlan_client")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is WlanClientDevice


def test_qoe_client_registered() -> None:
    spec = get_device_type("linux_qoe_client")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is QoeClientDevice


def test_acs_registered() -> None:
    spec = get_device_type("linux_acs")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is AcsDevice


def test_provisioner_registered() -> None:
    spec = get_device_type("linux_provisioner")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is ProvisionerDevice


def test_tftp_registered() -> None:
    spec = get_device_type("linux_tftp")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is TftpDevice


def test_traffic_controller_registered() -> None:
    spec = get_device_type("linux_traffic_controller")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is TrafficControllerDevice


def test_iperf_traffic_generator_registered() -> None:
    spec = get_device_type("iperf_traffic_generator")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is IperfTrafficGeneratorDevice


def test_sip_phone_device_registered() -> None:
    spec = get_device_type("linux_sip_phone")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is SipPhoneDevice


def test_sip_server_device_registered() -> None:
    spec = get_device_type("linux_sip_server")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is SipServerDevice


def test_wan_server_registered() -> None:
    spec = get_device_type("linux_wan_server")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is WanServerDevice


# ---------------------------------------------------------------------------
# Per-archetype: aggregate capability checks via __protocol_attrs__
# ---------------------------------------------------------------------------


def test_sdwan_router_aggregates_expected_capabilities() -> None:
    """SdwanRouterDevice declares attributes for every aggregated capability.

    Note: netem is intentionally not on this archetype — traffic impairment
    is the TrafficControllerDevice's job (separate device on the WAN path),
    not the SDWAN router's own. See packages/testprotocols/SPLITS.md.
    """
    expected = {
        "routing",
        "wan_admin",
        "static_routes",
        "bgp",
        "sdwan_policy",
        "ip_interface",
        "pcap",
        "nat",
        "conntrack",
    }
    actual = set(SdwanRouterDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"
    assert "netem" not in actual, "netem should not be on SdwanRouterDevice"


def test_sdwan_appliance_aggregates_expected_capabilities() -> None:
    """The managed-appliance archetype composes the appliance capability set —
    and deliberately excludes the Linux-host substrate capabilities, which stay
    on SdwanRouterDevice (the digital twin). See SPLITS.md."""
    expected = {
        "routing",
        "static_routes",
        "bgp",
        "sdwan_policy",
        "traffic_shaping",
        "l3_firewall",
        "l7_firewall",
        "content_filtering",
        "appliance_nat",
        "security",
        "uplinks",
        "lan",
        "syslog",
        "vpn",
    }
    actual = set(SdwanApplianceDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"
    # device_management is Linux-host-shaped (ps/memory/board-logs/file-content)
    # and intentionally NOT on the managed-appliance archetype — see GAPS.md.
    # wan_admin (forced link-down) is likewise host-substrate-only: an
    # API-managed appliance cannot admin-down its own uplink — see SPLITS.md.
    for twin_ism in (
        "conntrack",
        "pcap",
        "ip_interface",
        "nat",
        "device_management",
        "wan_admin",
    ):
        assert twin_ism not in actual, f"{twin_ism} must not be on the appliance archetype"


def test_cpe_aggregates_expected_capabilities() -> None:
    expected = {
        "tr069_client",
        "device_management",
        "device_lifecycle",
        "hw_console",
        "wifi_radio",
        "wifi_bss",
        "wifi_stations",
        "wifi_rf",
        "wifi_transitions",
        "wifi_onboarding",
        "ip_interface",
        "ip_routing",
        "firewall",
        "nat",
        "conntrack",
        "firewall_zones",
        "ntp_client",
    }
    actual = set(CpeDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_lan_client_aggregates_expected_capabilities() -> None:
    expected = {
        "ip_interface",
        "ip_routing",
        "dhcp_client",
        "http_client",
        "http_server",
        "dns_client",
        "iperf_client",
        "iperf_server",
        "pcap",
        "upnp_client",
        "multicast_client",
        "ntp_client",
        "nmap_scanner",
        "file_transfer",
        "packet_filter",
        "arp_client",
        "vlan_client",
    }
    actual = set(LanClientDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_wlan_client_aggregates_expected_capabilities() -> None:
    expected = {
        "wifi_client",
        "ip_interface",
        "ip_routing",
        "dhcp_client",
        "http_client",
        "iperf_client",
        "iperf_server",
        "pcap",
        "upnp_client",
        "multicast_client",
        "ntp_client",
        "nmap_scanner",
        "file_transfer",
    }
    actual = set(WlanClientDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_qoe_client_aggregates_expected_capabilities() -> None:
    expected = {"qoe_browser", "ip_interface", "dhcp_client"}
    actual = set(QoeClientDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_qoe_measurement_client_aggregates_expected_capabilities() -> None:
    expected = {
        "qoe_browser",
        "ip_interface",
        "dhcp_client",
        "iperf_client",
        "iperf_server",
        "network_probe",
        "pcap",
    }
    actual = set(QoeMeasurementClientDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_qoe_measurement_client_is_a_qoe_client() -> None:
    """Strict-superset invariant: the measurement client subsumes QoeClientDevice."""
    assert set(QoeClientDevice.__protocol_attrs__) <= set(
        QoeMeasurementClientDevice.__protocol_attrs__
    )


def test_acs_aggregates_expected_capabilities() -> None:
    expected = {
        "tr069_server",
        "pcap",
        "file_transfer",
        "packet_filter",
    }
    actual = set(AcsDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_provisioner_aggregates_expected_capabilities() -> None:
    expected = {"dhcp_server", "pcap", "file_transfer", "packet_filter"}
    actual = set(ProvisionerDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_tftp_aggregates_expected_capabilities() -> None:
    expected = {"tftp_server"}
    actual = set(TftpDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_traffic_controller_aggregates_expected_capabilities() -> None:
    expected = {"netem", "ip_interface", "pcap"}
    actual = set(TrafficControllerDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_iperf_traffic_generator_aggregates_expected_capabilities() -> None:
    expected = {"iperf_generator", "ip_interface"}
    actual = set(IperfTrafficGeneratorDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_sip_phone_device_aggregates_expected_capabilities() -> None:
    expected = {"sip_phone", "ip_interface", "dhcp_client", "number"}
    actual = set(SipPhoneDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_sip_server_device_aggregates_expected_capabilities() -> None:
    expected = {"sip_server", "pcap", "file_transfer"}
    actual = set(SipServerDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


def test_wan_server_aggregates_expected_capabilities() -> None:
    expected = {
        "ip_interface",
        "ip_routing",
        "dhcp_client",
        "http_client",
        "http_server",
        "dns_client",
        "iperf_client",
        "iperf_server",
        "pcap",
        "ntp_client",
        "nmap_scanner",
        "file_transfer",
        "snmp_client",
        "packet_filter",
        "nat",
        "conntrack",
    }
    actual = set(WanServerDevice.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"


# ---------------------------------------------------------------------------
# Firewall composition matrix
# ---------------------------------------------------------------------------


def test_acs_firewall_facets() -> None:
    """ACS aggregates packet_filter only — no NAT / port-forwarding / conntrack / zones."""
    attrs = set(AcsDevice.__protocol_attrs__)
    assert "packet_filter" in attrs
    for absent in ("nat", "port_forwarding", "conntrack", "firewall_zones"):
        assert absent not in attrs, f"AcsDevice unexpectedly aggregates {absent}"


def test_provisioner_firewall_facets() -> None:
    """Provisioner aggregates packet_filter."""
    attrs = set(ProvisionerDevice.__protocol_attrs__)
    assert "packet_filter" in attrs


def test_lan_client_firewall_facets() -> None:
    """LanClientDevice aggregates packet_filter only."""
    attrs = set(LanClientDevice.__protocol_attrs__)
    assert "packet_filter" in attrs
    for absent in ("nat", "port_forwarding", "conntrack", "firewall_zones"):
        assert absent not in attrs, f"LanClientDevice unexpectedly aggregates {absent}"


def test_wan_server_firewall_facets() -> None:
    """WanServerDevice aggregates packet_filter, nat, conntrack — no port-forwarding / zones."""
    attrs = set(WanServerDevice.__protocol_attrs__)
    for present in ("packet_filter", "nat", "conntrack"):
        assert present in attrs
    for absent in ("port_forwarding", "firewall_zones"):
        assert absent not in attrs, f"WanServerDevice unexpectedly aggregates {absent}"


def test_cpe_full_firewall_surface() -> None:
    """CpeDevice aggregates the complete firewall surface."""
    attrs = set(CpeDevice.__protocol_attrs__)
    for present in ("firewall", "nat", "conntrack", "firewall_zones"):
        assert present in attrs
    # PortForwarding is no longer a separate attribute — it's bundled into firewall.
    assert "port_forwarding" not in attrs
    # PacketFilter is also not a separate attribute on CPE — the firewall attribute
    # satisfies PacketFilter via Liskov substitution.
    assert "packet_filter" not in attrs


def test_devices_without_firewall() -> None:
    """These archetypes must not pull in any of the firewall capabilities."""
    firewall_attrs = ("packet_filter", "firewall", "nat", "port_forwarding", "conntrack", "firewall_zones")
    for archetype in (
        TftpDevice,
        WlanClientDevice,
        QoeClientDevice,
        SipPhoneDevice,
        SipServerDevice,
        TrafficControllerDevice,
        IperfTrafficGeneratorDevice,
    ):
        attrs = set(archetype.__protocol_attrs__)
        for absent in firewall_attrs:
            assert absent not in attrs, f"{archetype.__name__} unexpectedly aggregates {absent}"


# ---------------------------------------------------------------------------
# Universal base — every archetype inherits identity (device_name + device_type)
# from BaseDeviceProtocol so consumers (operations, step defs) can read identity
# without reaching into framework-specific base classes.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype", _ALL_ARCHETYPES, ids=lambda a: a.__name__)
def test_archetype_inherits_base_device_protocol(archetype: type) -> None:
    """Every archetype declares BaseDeviceProtocol in its MRO.

    ``issubclass`` is unsupported on Protocols with non-method members
    (Python 3.12 raises ``TypeError`` from ``typing.__subclasscheck__``);
    ``__mro__`` membership is the declarative-inheritance contract we
    actually want to enforce: each archetype must list BaseDeviceProtocol
    as a base, not merely satisfy it structurally.
    """
    assert BaseDeviceProtocol in archetype.__mro__, (
        f"{archetype.__name__} must declare BaseDeviceProtocol as a base "
        f"(carries device_name + device_type)"
    )


@pytest.mark.parametrize("archetype", _ALL_ARCHETYPES, ids=lambda a: a.__name__)
def test_archetype_carries_universal_identity(archetype: type) -> None:
    """Every archetype's protocol-attrs include device_name and device_type."""
    attrs = set(archetype.__protocol_attrs__)
    assert {"device_name", "device_type"} <= attrs, (
        f"{archetype.__name__} missing universal-identity attrs: "
        f"{ {'device_name', 'device_type'} - attrs}"
    )


# ---------------------------------------------------------------------------
# L2Switch archetype
# ---------------------------------------------------------------------------


def test_l2_switch_registered() -> None:
    spec = get_device_type("managed_switch_l2")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is L2Switch


def test_l3_switch_registered() -> None:
    spec = get_device_type("managed_switch_l3")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is L3Switch


def test_l3_switch_routed_registered() -> None:
    spec = get_device_type("managed_switch_l3_routed")
    assert isinstance(spec, DeviceTypeSpec)
    assert spec.protocol is L3SwitchRouted


def test_l3_switch_is_strict_superset_of_l2() -> None:
    # Protocol inheritance: every L3 attribute set includes the full L2 set.
    l2_attrs = set(L2Switch.__protocol_attrs__)
    l3_attrs = set(L3Switch.__protocol_attrs__)
    assert l2_attrs <= l3_attrs, f"L3Switch missing L2 attrs: {l2_attrs - l3_attrs}"
    expected_l3 = {
        "routed_interfaces", "static_routes", "routing_read",
        "ospf", "interface_dhcp", "gateway_redundancy",
    }
    assert expected_l3 <= l3_attrs, f"missing: {expected_l3 - l3_attrs}"
    assert "bgp" not in l3_attrs, "bgp belongs only on L3SwitchRouted"


def test_l3_switch_routed_adds_bgp() -> None:
    attrs = set(L3SwitchRouted.__protocol_attrs__)
    assert "bgp" in attrs
    assert set(L3Switch.__protocol_attrs__) <= attrs  # still a superset of L3Switch


def test_l2_switch_aggregates_expected_capabilities() -> None:
    expected = {
        "switch_ports", "switch_vlans", "spanning_tree", "link_aggregation",
        "port_poe", "port_security", "radius", "first_hop_security",
        "storm_control", "switch_acl", "discovery", "mac_table",
        "port_status", "switch_qos", "syslog", "ntp",
    }
    actual = set(L2Switch.__protocol_attrs__)
    assert expected <= actual, f"missing: {expected - actual}"
    # host-substrate levers stay on the Linux twins, never on a managed switch
    for host_lever in (
        "conntrack", "pcap", "ip_interface", "nat",
        "packet_filter", "firewall_zones", "wan_admin",
    ):
        assert host_lever not in actual, f"{host_lever} must not be on L2Switch"


def test_l3_switch_excludes_host_substrate_levers() -> None:
    """L3Switch must not carry any host-substrate levers.

    Routed-interface config is switch-native (``routed_interfaces``), not the
    Linux-host-shaped ``ip_interface``; firewall / NAT / conntrack belong on the
    CPE/router archetypes; wan_admin is a Linux-only forced link-down lever.
    """
    actual = set(L3Switch.__protocol_attrs__)
    for host_lever in (
        "conntrack", "pcap", "ip_interface", "nat",
        "packet_filter", "firewall_zones", "wan_admin",
    ):
        assert host_lever not in actual, f"{host_lever} must not be on L3Switch"


def test_l3_switch_routed_excludes_host_substrate_levers() -> None:
    """L3SwitchRouted (the BGP-capable variant) likewise excludes host-substrate levers."""
    actual = set(L3SwitchRouted.__protocol_attrs__)
    for host_lever in (
        "conntrack", "pcap", "ip_interface", "nat",
        "packet_filter", "firewall_zones", "wan_admin",
    ):
        assert host_lever not in actual, f"{host_lever} must not be on L3SwitchRouted"
