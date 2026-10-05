"""A released driver builds a released record with released values: no warning, every value
stored as given. A new driver fills only the typed form of a text field: no warning either."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from testprotocols.models import (
    AppFlow,
    Connection,
    FirewallRule,
    L3Rule,
    LinkHealthReport,
    LinkStatus,
    NatRule,
    PortMapping,
    PortRange,
    QosClassifier,
    QosRule,
    RuleAction,
    RuleProtocol,
    SecurityAction,
    SecurityEvent,
    ThreatCategory,
    WifiCaptiveConfig,
)

# The origin/main FirewallRule fields only, with the port as released text.
RELEASED_FIREWALL_RULE_KWARGS: dict[str, object] = {
    "name": "allow-high",
    "action": "allow",
    "protocol": "tcp",
    "src_cidr": "192.0.2.0/24",
    "dst_cidr": "198.51.100.0/24",
    "dst_port": "1000-2000",
    "application": None,
    "application_category": None,
    "log": True,
}

RELEASED_NAT_RULE_KWARGS: dict[str, object] = {
    "name": "fwd",
    "mode": "dnat",
    "interface": "wan0",
    "protocol": "tcp",
    "src_cidr": "",
    "dst_cidr": "",
    "dst_port": "8080",
    "translated_src": "",
    "translated_dst": "192.0.2.10",
    "translated_port": "80",
    "enabled": True,
}

RELEASED_L3_RULE_KWARGS: dict[str, object] = {
    "action": RuleAction.DENY,
    "protocol": RuleProtocol.UDP,
    "src_cidr": "any",
    "src_port": "any",
    "dst_cidr": "198.51.100.0/24",
    "dst_port": "53,123",
    "comment": "c",
    "syslog_enabled": False,
}

RELEASED_SECURITY_EVENT_KWARGS: dict[str, object] = {
    "ts": "2026-01-02T03:04:05Z",
    "src_ip": "192.0.2.1",
    "dst_ip": "198.51.100.1",
    "protocol": RuleProtocol.TCP,
    "action": SecurityAction.BLOCKED,
    "category": ThreatCategory.MALWARE,
    "description": "d",
}

RELEASED_QOS_RULE_KWARGS: dict[str, object] = {
    "name": "voice",
    "match": "vlan 10",
    "dscp": 46,
    "cos": 5,
}

RELEASED_APP_FLOW_KWARGS: dict[str, object] = {
    "application": "app",
    "category": "gaming",
    "src_ip": "192.0.2.1",
    "dst_ip": "198.51.100.1",
    "wan_interface": "wan1",
    "bytes_sent": 1,
    "bytes_received": 2,
}


def _build[T](factory: Callable[..., T], kwargs: dict[str, object]) -> T:
    """*factory* called with *kwargs*, failing on any warning."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return factory(**kwargs)


def _stored_as_given(record: object, kwargs: dict[str, object]) -> None:
    for name, value in kwargs.items():
        held = getattr(record, name)
        assert held == value, name
        assert type(held) is type(value), name


def test_released_records_build_as_released() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rule = FirewallRule(**RELEASED_FIREWALL_RULE_KWARGS)  # type: ignore[arg-type]
    assert rule.dst_port == "1000-2000"
    assert rule.dst_ports is None
    _stored_as_given(rule, RELEASED_FIREWALL_RULE_KWARGS)

    nat = _build(NatRule, RELEASED_NAT_RULE_KWARGS)
    _stored_as_given(nat, RELEASED_NAT_RULE_KWARGS)
    assert nat.dst_ports is None
    assert nat.translated_ports is None

    l3 = _build(L3Rule, RELEASED_L3_RULE_KWARGS)
    _stored_as_given(l3, RELEASED_L3_RULE_KWARGS)
    assert l3.src_ports is None
    assert l3.dst_ports is None

    event = _build(SecurityEvent, RELEASED_SECURITY_EVENT_KWARGS)
    _stored_as_given(event, RELEASED_SECURITY_EVENT_KWARGS)
    assert event.timestamp is None

    qos = _build(QosRule, RELEASED_QOS_RULE_KWARGS)
    _stored_as_given(qos, RELEASED_QOS_RULE_KWARGS)
    assert qos.classifier is None

    flow = _build(AppFlow, RELEASED_APP_FLOW_KWARGS)
    _stored_as_given(flow, RELEASED_APP_FLOW_KWARGS)


def test_released_records_keep_released_positions() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rule = FirewallRule("r", "deny", "udp", "any", "any", "53")
        event = SecurityEvent(
            "", "192.0.2.1", "198.51.100.1", RuleProtocol.ICMP, SecurityAction.DETECTED,
            ThreatCategory.SCAN,
        )  # fmt: skip
        qos = QosRule("q", "")
    assert rule.dst_port == "53"
    assert event.ts == ""
    assert event.category is ThreatCategory.SCAN
    assert qos.match == ""


def test_released_defaults_are_unset() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        nat = NatRule(name="n", mode="snat", interface="wan0")
        l3 = L3Rule(action=RuleAction.ALLOW)
    assert (nat.dst_port, nat.translated_port, nat.dst_ports, nat.translated_ports) == (
        None,
        None,
        None,
        None,
    )
    assert (l3.src_port, l3.dst_port, l3.src_ports, l3.dst_ports) == (None, None, None, None)


def test_typed_only_records_build() -> None:
    ports = (PortRange(1000, 2000),)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rule = FirewallRule(
            name="r",
            action="allow",
            protocol="tcp",
            src_cidr="any",
            dst_cidr="any",
            dst_port=None,
            dst_ports=ports,
        )
        nat = NatRule(name="n", mode="dnat", interface="wan0", dst_ports=ports, translated_ports=())
        l3 = L3Rule(action=RuleAction.ALLOW, src_ports=(), dst_ports=ports)
        when = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
        event = SecurityEvent(
            ts=None,
            src_ip="192.0.2.1",
            dst_ip="198.51.100.1",
            protocol=RuleProtocol.TCP,
            action=SecurityAction.BLOCKED,
            category=ThreatCategory.MALWARE,
            timestamp=when,
        )
        classifier = QosClassifier(vlan=10)
        qos = QosRule(name="q", match=None, classifier=classifier)
    assert (rule.dst_port, rule.dst_ports) == (None, ports)
    assert (nat.dst_port, nat.translated_port) == (None, None)
    assert (nat.dst_ports, nat.translated_ports) == (ports, ())
    assert (l3.src_port, l3.dst_port, l3.src_ports, l3.dst_ports) == (None, None, (), ports)
    assert (event.ts, event.timestamp) == (None, when)
    assert (qos.match, qos.classifier) == (None, classifier)


def test_records_do_not_convert_on_assignment() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rule = FirewallRule(**RELEASED_FIREWALL_RULE_KWARGS)  # type: ignore[arg-type]
        rule.dst_port = "443"
        rule.protocol = "udp"
    assert rule.dst_port == "443"
    assert rule.dst_ports is None
    assert type(rule.protocol) is str


_STATION: dict[str, object] = {
    "mac": "02:00:00:00:00:01",
    "bss_name": "main",
    "band": "5GHz",
    "ip_address": None,
    "associated_since": 0.0,
    "rssi_dbm": -50,
    "snr_db": None,
    "tx_rate_mbps": 1.0,
    "rx_rate_mbps": 1.0,
    "tx_bytes": 0,
    "rx_bytes": 0,
    "tx_packets": 0,
    "rx_packets": 0,
    "tx_retries": 0,
}

_BSS: dict[str, object] = {
    "name": "main",
    "band": "2.4GHz",
    "ssid": "s",
    "bssid": "02:00:00:00:00:02",
    "enabled": True,
    "broadcast_enabled": True,
    "security_mode": "WPA2-PSK",
    "radius_server_name": None,
    "mfp": "optional",
    "vlan_id": None,
    "max_clients": None,
    "dtim_period": 1,
    "captive_portal": WifiCaptiveConfig(enabled=False, redirect_url=None),
}

_MESH_LINK: dict[str, object] = {
    "band": "6GHz",
    "channel": 37,
    "rssi_dbm": -60,
    "capacity_mbps": 1.0,
}

# One case per closed-vocabulary field: the record, its released kwargs with the field as
# the released plain string.
_C4_CASES: list[tuple[Callable[..., object], dict[str, object]]] = [
    (FirewallRule, RELEASED_FIREWALL_RULE_KWARGS),  # action, protocol
    (NatRule, RELEASED_NAT_RULE_KWARGS),  # mode, protocol
    (
        PortMapping,
        {
            "name": "m",
            "external_port": 80,
            "protocol": "tcp-udp",
            "internal_host": "192.0.2.10",
            "internal_port": 8080,
        },
    ),
    (
        Connection,
        {
            "protocol": "tcp",
            "src_ip": "192.0.2.1",
            "dst_ip": "198.51.100.1",
            "src_port": 1,
            "dst_port": 2,
            "state": "ESTABLISHED",
            "timeout_seconds": 1,
            "bytes_orig": 0,
            "bytes_reply": 0,
            "packets_orig": 0,
            "packets_reply": 0,
        },
    ),
    (LinkStatus, {"name": "wan1", "state": "degraded", "ip_address": ""}),
    (
        LinkHealthReport,
        {
            "state": "up",
            "route_installed": True,
            "avg_rtt_ms": None,
            "jitter_ms": None,
            "loss_percent": 0.0,
            "sla_compliant": True,
        },
    ),
]


@pytest.mark.parametrize(
    ("factory", "kwargs"), _C4_CASES, ids=[getattr(f, "__name__", "") for f, _ in _C4_CASES]
)
def test_closed_vocabularies_store_the_released_string(
    factory: Callable[..., object], kwargs: dict[str, object]
) -> None:
    record = _build(factory, kwargs)
    _stored_as_given(record, kwargs)
