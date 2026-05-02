"""Voice / SipServer template.

Defines the abstract contract for SIP server operations including user
management, call tracking and SIP message verification.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SipServer(Protocol):
    """Abstract contract for SIP server operations."""

    # ------------------------------------------------------------------
    # Abstract properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Human-readable name of this SIP server instance."""
        ...

    @property
    def ipv4_addr(self) -> str | None:
        """IPv4 address of the SIP server, or None if not configured."""
        ...

    @property
    def ipv6_addr(self) -> str | None:
        """IPv6 address of the SIP server, or None if not configured."""
        ...

    # ------------------------------------------------------------------
    # Abstract methods
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the SIP server process."""
        ...

    def stop(self) -> None:
        """Stop the SIP server process."""
        ...

    def restart(self) -> None:
        """Restart the SIP server process."""
        ...

    def get_status(self) -> str:
        """Return a string describing the current SIP server status."""
        ...

    def get_online_users(self) -> str:
        """Return a string listing currently registered/online SIP users."""
        ...

    def add_user(self, user: str, password: str | None = None) -> None:
        """Add a SIP *user* account, optionally with a *password*."""
        ...

    def remove_endpoint(self, endpoint: str) -> None:
        """Remove the SIP *endpoint* (user or device) from the server."""
        ...

    def allocate_number(self, number: str | None = None) -> str:
        """Allocate a DID *number* on the server and return the allocated number."""
        ...

    def get_expire_timer(self) -> int:
        """Return the current SIP registration expire timer value (seconds)."""
        ...

    def set_expire_timer(self, to_timer: int = 60) -> None:
        """Set the SIP registration expire timer to *to_timer* seconds."""
        ...

    def get_active_calls(self) -> int:
        """Return the exact number of currently active dialogs on the server.

        Implementations MUST use a dialog-module backed query (e.g. kamailio
        ``kamcmd dlg.stats_active``). The pre-v0.2.0 "best-effort heuristic"
        based on counting registered contacts is no longer acceptable;
        a driver paired with a v1.3.0+ sipcenter image has access to real
        dialog state and must use it.
        """
        ...

    def get_rtpengine_stats(self) -> dict:
        """Return RTPEngine statistics as a dictionary."""
        ...

    def verify_sip_message(
        self,
        message_type: str,
        since: Any = None,
        timeout: int = 5,
    ) -> bool:
        """Verify that a SIP message of *message_type* was received.

        Implementations MUST consult an authoritative log channel (e.g.
        the sipcenter's ``/var/log/kamailio/kamailio.log`` written by
        rsyslog, or the merged testbed log at ``raikou/logs/sip-testbed.log``).
        The pre-v0.2.0 ``journalctl``-based probe is dead — the image does
        not run systemd — and any driver still relying on it must switch
        to the authoritative file path.

        Parameters
        ----------
        message_type:
            The SIP method (``INVITE``, ``MESSAGE``, ``NOTIFY``, ...) or
            response code (``200``, ``486``, ...) to match.
        since:
            Optional timestamp or marker; only messages after this point
            are considered.
        timeout:
            Seconds to wait for the expected message.
        """
        ...

    # ------------------------------------------------------------------
    # Voicemail (v0.2.0+)
    # ------------------------------------------------------------------

    def get_voicemail_count(self, user: str) -> int:
        """Return the number of unheard voicemail messages waiting for *user*.

        Returns 0 if the user exists but has no messages. Raises when *user*
        has no mailbox provisioned on the server.
        """
        ...

    def clear_voicemail(self, user: str) -> None:
        """Delete all voicemail messages (heard and unheard) for *user*."""
        ...

    # ------------------------------------------------------------------
    # MWI — Message Waiting Indication (v0.2.0+)
    # ------------------------------------------------------------------

    def get_mwi_status(self, user: str) -> dict:
        """Return the current MWI status for *user*.

        Returns a dict with keys:
            - ``waiting`` (bool): True if the waiting flag is set.
            - ``new`` (int): count of new (unheard) messages.
            - ``old`` (int): count of old (heard but retained) messages.
        """
        ...

    def set_mwi_status(self, user: str, waiting: bool) -> None:
        """Set the MWI waiting flag for *user*.

        Implementers should emit a ``message-summary`` NOTIFY to any
        subscribed UA so the phone's indicator updates immediately.
        """
        ...

    # ------------------------------------------------------------------
    # Presence (v0.2.0+)
    # ------------------------------------------------------------------

    def get_user_presence(self, user: str) -> str:
        """Return the current presence status string for *user*.

        Typical values: ``"online"``, ``"busy"``, ``"away"``, ``"offline"``.
        Implementations may return provider-specific extensions.
        """
        ...

    def subscribe_to_user(self, watcher: str, watched: str) -> None:
        """Create a presence subscription from *watcher* to *watched*."""
        ...

    def notify_presence(self, user: str, status: str) -> None:
        """Publish presence *status* for *user* to all current subscribers."""
        ...

    # ------------------------------------------------------------------
    # Offline SIP MESSAGE (v0.2.0+)
    # ------------------------------------------------------------------

    def send_offline_message(self, from_user: str, to_user: str, body: str) -> bool:
        """Store a SIP MESSAGE from *from_user* to the offline *to_user*.

        Returns True if the message was stored for later delivery. The
        message is expected to flush on the next successful REGISTER from
        *to_user*.
        """
        ...

    def get_offline_messages(self, user: str) -> list[dict]:
        """Return the list of pending offline messages addressed to *user*.

        Each entry is a dict with keys:
            - ``from`` (str): sender URI.
            - ``body`` (str): message body.
            - ``timestamp`` (str): ISO-8601 timestamp of when stored.
        """
        ...

    def clear_offline_messages(self, user: str) -> None:
        """Delete all pending offline messages addressed to *user*."""
        ...
