"""Switchport configuration — the first-class object of a managed switch.

Per-port access/trunk mode, native (PVID) + allowed VLANs, enable state, voice
VLAN, and isolation. Read via a port listing; configured per whole-port object.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import SwitchPort


@runtime_checkable
class SwitchPorts(Protocol):
    """Abstract contract for per-port switchport configuration."""

    def list_ports(self) -> list[SwitchPort]:
        """Return every switchport."""
        ...

    def get_port(self, name: str) -> SwitchPort:
        """Return the port *name*. Raises KeyError if absent."""
        ...

    def set_port(self, port: SwitchPort) -> None:
        """Create or replace the port identified by ``port.name``."""
        ...
