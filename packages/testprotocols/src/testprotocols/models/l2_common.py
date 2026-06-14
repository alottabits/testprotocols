"""Shared L2 vocabulary for the switch archetypes and the future CPE L2 bridge.

STP and FDB concepts are common to a hardware switch (``SpanningTree`` /
``MacTable``) and a Linux bridge (the deferred ``L2Bridge``, see GAPS.md). The
normalized vocabularies live here, in a neutral module, so neither
``models/switch.py`` nor a future bridge model depends on the other.

Vendor neutrality is part of the contract: members are plain strings (trivial to
serialize), constructing from a value validates it, and a testbed plugin maps its
product's terms to/from these neutral values. No vendor identifier appears here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class StpMode(StrEnum):
    """IEEE spanning-tree mode (802.1D / 802.1w / 802.1s). Seeded in full."""

    STP = "stp"
    RSTP = "rstp"
    MSTP = "mstp"
    UNKNOWN = "unknown"


class StpGuard(StrEnum):
    """Per-port spanning-tree guard."""

    NONE = "none"
    ROOT = "root"
    BPDU = "bpdu"
    LOOP = "loop"


class StpPortState(StrEnum):
    """Observed per-port spanning-tree state."""

    FORWARDING = "forwarding"
    BLOCKING = "blocking"
    LEARNING = "learning"
    LISTENING = "listening"
    DISABLED = "disabled"


@dataclass
class MacTableEntry:
    """A single forwarding-database (FDB) entry — normalized."""

    mac: str
    port: str
    vlan: int
