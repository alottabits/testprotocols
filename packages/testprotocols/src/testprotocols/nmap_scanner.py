"""Nmap / Scanner template.

Defines the abstract contract for network scanning operations using nmap.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class NmapScanner(Protocol):
    """Abstract contract for nmap network scanning operations."""

    def nmap(
        self,
        ipaddr: str,
        ip_type: str,
        port: str | int | None = None,
        protocol: str | None = None,
        max_retries: int | None = None,
        min_rate: int | None = None,
        opts: str | None = None,
        timeout: int = 30,
    ) -> dict:
        """Run an nmap scan against *ipaddr* and return the parsed results."""
        ...
