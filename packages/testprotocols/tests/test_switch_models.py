"""Tests for the L2 switch model vocabularies and records."""

from __future__ import annotations

import pytest


def test_l2_common_enums_are_str() -> None:
    from testprotocols.models.l2_common import StpGuard, StpMode, StpPortState

    assert StpMode.RSTP == "rstp"
    assert StpGuard.ROOT == "root"
    assert StpPortState.FORWARDING == "forwarding"
    with pytest.raises(ValueError):
        StpMode("pvst")  # vendor-proprietary value is rejected


def test_mac_table_entry_fields() -> None:
    from testprotocols.models.l2_common import MacTableEntry

    e = MacTableEntry(mac="00:11:22:33:44:55", port="1", vlan=10)
    assert (e.mac, e.port, e.vlan) == ("00:11:22:33:44:55", "1", 10)


def test_switch_enums_values() -> None:
    from testprotocols.models.switch import (
        AccessPolicyType,
        AclDirection,
        AggregationMode,
        BindingSource,
        DiscoveryProtocol,
        Duplex,
        FhsScope,
        FhsTrustState,
        LinkState,
        PoePriority,
        PoeStatus,
        PortAdminState,
        PortMode,
        QosTrustMode,
        StormControlType,
    )

    assert PortMode.TRUNK == "trunk"
    assert PortAdminState.ENABLED == "enabled"
    assert LinkState.UP == "up"
    assert Duplex.FULL == "full"
    assert AggregationMode.LACP == "lacp"
    assert PoeStatus.DELIVERING == "delivering"
    assert PoePriority.CRITICAL == "critical"
    assert AccessPolicyType.DOT1X == "dot1x"
    assert AclDirection.INGRESS == "ingress"
    assert DiscoveryProtocol.LLDP == "lldp"
    assert StormControlType.BROADCAST == "broadcast"
    assert QosTrustMode.DSCP == "dscp"
    assert FhsTrustState.TRUSTED == "trusted"
    assert FhsScope.PER_VLAN == "per_vlan"
    assert BindingSource.STATIC == "static"
    with pytest.raises(ValueError):
        DiscoveryProtocol("cdp")  # CDP normalizes onto LLDP; not a member
