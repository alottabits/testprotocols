"""Data models for the vendor-neutral L2 (access) switch capabilities.

Field value-vocabularies are normalized ``StrEnum`` types owned here; records are
plain ``@dataclass``es composing them. Shared STP/FDB vocab lives in
``models/l2_common.py``; rule action/protocol enums are reused from
``models/sdwan_appliance.py``. Vendor neutrality is part of the contract — no
product name, vendor id, or ``native`` bucket appears in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from testprotocols.models.sdwan_appliance import RuleAction, RuleProtocol


class PortMode(StrEnum):
    ACCESS = "access"
    TRUNK = "trunk"
    ROUTED = "routed"  # used only at L3 (L3Switch); access/trunk are universal


class PortAdminState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class LinkState(StrEnum):
    UP = "up"
    DOWN = "down"
    DISABLED = "disabled"


class Duplex(StrEnum):
    FULL = "full"
    HALF = "half"
    AUTO = "auto"


class AggregationMode(StrEnum):
    LACP = "lacp"
    STATIC = "static"


class PoeStatus(StrEnum):
    DELIVERING = "delivering"
    DISABLED = "disabled"
    FAULT = "fault"
    SEARCHING = "searching"
    OFF = "off"


class PoePriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    LOW = "low"


class AccessPolicyType(StrEnum):
    OPEN = "open"
    MAC_ALLOW_LIST = "mac_allow_list"
    STICKY_MAC = "sticky_mac"
    DOT1X = "dot1x"


class AclDirection(StrEnum):
    INGRESS = "ingress"
    EGRESS = "egress"


class DiscoveryProtocol(StrEnum):
    """Link-layer discovery. Only the open IEEE 802.1AB standard is a member;
    a vendor's proprietary discovery normalizes onto the same LLDP-shaped read."""

    LLDP = "lldp"


class StormControlType(StrEnum):
    BROADCAST = "broadcast"
    MULTICAST = "multicast"
    UNKNOWN_UNICAST = "unknown_unicast"


class QosTrustMode(StrEnum):
    DSCP = "dscp"
    COS = "cos"
    UNTRUSTED = "untrusted"


class FhsTrustState(StrEnum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class FhsScope(StrEnum):
    GLOBAL = "global"
    PER_VLAN = "per_vlan"


class BindingSource(StrEnum):
    DYNAMIC_SNOOPING = "dynamic_snooping"
    STATIC = "static"


__all_enums__ = ()  # records appended in Task 3 (kept for reviewer clarity)
