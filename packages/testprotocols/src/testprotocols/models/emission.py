"""Packet-emission result data models.

Normalized outcomes of an emission run — no signature ids, no vendor taxonomy.
``replay`` guarantees only that the packets were emitted, never a bit- or
timing-exact reproduction (substrates differ; see the packet-injection design
record).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmitResult:
    """Outcome of crafting and sending a caller-supplied payload."""

    sent: int
    target: str


@dataclass
class ReplayResult:
    """Outcome of replaying a caller-supplied capture onto the wire."""

    packets: int
    duration_s: float
