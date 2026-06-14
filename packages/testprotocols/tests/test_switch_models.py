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


def test_switch_records() -> None:
    from testprotocols.models.sdwan_appliance import RuleAction
    from testprotocols.models.switch import (
        AccessPolicy,
        AccessPolicyType,
        FhsBinding,
        LinkState,
        LldpNeighbor,
        NtpServer,
        PoePortStatus,
        PoeStatus,
        PortStatusEntry,
        QosRule,
        StormControlConfig,
        StormControlType,
        StpPortConfig,
        SwitchAclRule,
        SwitchPort,
        VlanDef,
        LinkAggregationGroup,
    )

    p = SwitchPort(name="1", mode="access")  # type: ignore[arg-type]
    assert p.enabled is True and p.allowed_vlans == [] and p.isolated is False
    assert VlanDef(vlan_id=10).name == ""
    assert StpPortConfig(port="1").guard == "none"
    assert LinkAggregationGroup(name="po1", member_ports=["1", "2"]).mode == "lacp"
    assert PoePortStatus(port="1", status=PoeStatus.DELIVERING).draw_watts is None
    assert AccessPolicy(port="1", policy_type=AccessPolicyType.DOT1X).max_macs is None
    assert StormControlConfig(port="1").thresholds == {}
    r = SwitchAclRule(action=RuleAction.DENY, vlan=10)
    assert r.src_mac is None and r.dst_cidr == "any"
    assert LldpNeighbor(local_port="1", remote_system="sw2", remote_port="5").protocol == "lldp"
    assert PortStatusEntry(name="1", link_state=LinkState.UP).duplex == "auto"
    assert QosRule(name="voip", match="vlan 10").dscp is None
    assert FhsBinding(mac="aa", ip="10.0.0.1", vlan=10, port="1").source == "dynamic_snooping"
    assert NtpServer(host="10.0.0.1").prefer is False
