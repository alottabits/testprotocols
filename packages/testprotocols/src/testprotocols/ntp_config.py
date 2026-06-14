"""NTP-server configuration — the time-sync sibling of syslog_config.

Small and generic. Distinct from the operational ``ntp_client`` (get/set/sync
time): this is server-list config. A cloud-managed product that sets time
itself (timezone-only) raises unsupported-capability.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import NtpServer


@runtime_checkable
class NtpConfig(Protocol):
    """Abstract contract for NTP-server configuration."""

    def set_ntp_servers(self, servers: list[NtpServer]) -> None:
        """Replace the NTP-server list."""
        ...

    def get_ntp_servers(self) -> list[NtpServer]:
        """Return the configured NTP servers."""
        ...
