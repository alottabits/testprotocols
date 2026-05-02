"""Tests for network-tool Protocol shapes.

Covers: HttpClient, HttpServer, DnsClient, NmapScanner, SnmpClient,
NtpClient, UpnpClient, ArpClient, VlanClient.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "HttpClient",
        "testprotocols.http_client",
        {"curl", "http_get"},
    ),
    (
        "HttpServer",
        "testprotocols.http_server",
        {"start_http_service", "stop_http_service"},
    ),
    (
        "DnsClient",
        "testprotocols.dns_client",
        {"dns_lookup"},
    ),
    (
        "NmapScanner",
        "testprotocols.nmap_scanner",
        {"nmap"},
    ),
    (
        "SnmpClient",
        "testprotocols.snmp_client",
        {"execute_snmp_command"},
    ),
    (
        "NtpClient",
        "testprotocols.ntp_client",
        {"get_date", "set_date", "execute_time_sync"},
    ),
    (
        "UpnpClient",
        "testprotocols.upnp_client",
        {"create_upnp_rule", "delete_upnp_rule"},
    ),
    (
        "ArpClient",
        "testprotocols.arp_client",
        {"flush_arp_cache", "get_arp_table", "delete_arp_table_entry"},
    ),
    (
        "VlanClient",
        "testprotocols.vlan_client",
        {"add_vlan_interface", "delete_vlan_interface"},
    ),
]


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_is_runtime_checkable(class_name: str, module: str, expected_methods: set[str]) -> None:
    cls = getattr(importlib.import_module(module), class_name)
    assert getattr(cls, "_is_runtime_protocol", False), (
        f"{class_name} is not a @runtime_checkable Protocol"
    )


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_protocol_shape(class_name: str, module: str, expected_methods: set[str]) -> None:
    cls = getattr(importlib.import_module(module), class_name)
    actual = set(cls.__protocol_attrs__)
    assert expected_methods <= actual, f"{class_name} missing: {expected_methods - actual}"
