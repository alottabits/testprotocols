"""RADIUS / RadiusServer template.

Defines the abstract contract for a controllable RADIUS server used as
the AAA backend in a testbed (e.g. FreeRADIUS in a container, exercised
by WPA-Enterprise / 802.1X / VPN scenarios).

Tests use this template to provision EAP-capable users, inspect active
sessions, drive RFC 5176 dynamic-authorization (CoA / Disconnect) flows,
and read accounting records produced by NAS devices (APs, switches).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.radius import (
    RadiusAccountingRecord,
    RadiusSession,
    RadiusUser,
)


@runtime_checkable
class RadiusServer(Protocol):
    """Abstract contract for a controllable RADIUS server."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the RADIUS daemon."""
        ...

    def stop(self) -> None:
        """Stop the RADIUS daemon."""
        ...

    def get_status(self) -> str:
        """Return the daemon status. Typical values: ``"running"``, ``"stopped"``, ``"error"``."""
        ...

    # ------------------------------------------------------------------
    # User provisioning
    # ------------------------------------------------------------------

    def add_user(
        self,
        username: str,
        password: str,
        eap_methods: list[str] | None = None,
        attributes: dict[str, str] | None = None,
    ) -> None:
        """Provision a user authorised to authenticate.

        *eap_methods* lists the EAP methods this user may use (e.g.
        ``["PEAP-MSCHAPv2", "TTLS-PAP"]``); None means the server's default
        method set. *attributes* is a dict of RADIUS attributes returned in
        the Access-Accept reply (e.g. ``{"Tunnel-Private-Group-Id": "42"}``
        for VLAN assignment, ``{"Session-Timeout": "3600"}``).

        Raises ValueError if *username* is already provisioned.
        """
        ...

    def remove_user(self, username: str) -> None:
        """Remove the provisioned user. Raises KeyError if absent."""
        ...

    def list_users(self) -> list[RadiusUser]:
        """Return all provisioned users (without passwords)."""
        ...

    def get_user(self, username: str) -> RadiusUser:
        """Return the provisioned user (without password). Raises KeyError if absent."""
        ...

    # ------------------------------------------------------------------
    # Active sessions
    # ------------------------------------------------------------------

    def get_active_sessions(self) -> list[RadiusSession]:
        """Return currently authenticated NAS sessions tracked by the server."""
        ...

    # ------------------------------------------------------------------
    # Dynamic authorization (RFC 5176)
    # ------------------------------------------------------------------

    def send_coa(self, session_id: str, attributes: dict[str, str]) -> bool:
        """Send a Change-of-Authorization request to the NAS for *session_id*.

        *attributes* are the RADIUS attributes to apply (e.g. a new VLAN
        assignment, a new Filter-Id). Returns True on CoA-ACK, False on
        CoA-NAK or no response within the driver's timeout.
        """
        ...

    def send_disconnect(self, session_id: str) -> bool:
        """Send a Disconnect-Message to the NAS for *session_id*.

        Returns True on Disconnect-ACK, False on Disconnect-NAK or no
        response within the driver's timeout.
        """
        ...

    # ------------------------------------------------------------------
    # Accounting
    # ------------------------------------------------------------------

    def get_accounting_records(
        self,
        username: str | None = None,
        nas_address: str | None = None,
        since: float | None = None,
    ) -> list[RadiusAccountingRecord]:
        """Return accounting records, optionally filtered.

        *since* is a Unix timestamp; only records at or after that time are
        returned. Filters compose (AND).
        """
        ...

    def clear_accounting(self) -> None:
        """Discard all stored accounting records.

        Tests typically call this at scenario start so subsequent
        ``get_accounting_records()`` returns only what the scenario produced.
        """
        ...
