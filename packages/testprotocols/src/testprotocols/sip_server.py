"""Voice / SipServer template.

Defines the abstract contract for SIP server operations including user
management, call tracking and SIP message verification.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from testprotocols.models.voice import (
    MwiStatus,
    OfflineMessage,
    RtpStats,
)


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

    @property
    def aor_domain(self) -> str:
        """The host part callers should embed in SIP AORs targeting this
        server (``sip:user@<aor_domain>``). May be an FQDN, an IPv4 literal,
        or an IPv6 bracketed literal — the driver decides which form matches
        its testbed's address-resolution context."""
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

    def get_rtpengine_stats(self) -> dict[str, Any]:  # type: ignore[explicit-any]  # released signature kept until removal
        """Deprecated name of :meth:`read_rtpengine_stats`.

        Returns ``read_rtpengine_stats().as_dict()``; the driver warns with
        ``warn_renamed("get_rtpengine_stats", "read_rtpengine_stats")``.
        """
        ...

    def read_rtpengine_stats(self) -> RtpStats:
        """Return the media relay's statistics: whether it is engaged on any call and
        how many sessions it holds."""
        ...

    def verify_sip_message(
        self,
        message_type: str,
        since: datetime | None = None,
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
            The SIP method (``INVITE``, ``MESSAGE``, ``NOTIFY``, an extension method), a
            response code as text such as ``"486"``, or a log marker, matched as the word the
            log carries. An ``int`` response code
            is announced, not yet accepted: it joins the annotation in a later
            release, once implementers have widened their own parameter.
        since:
            Optional timestamp; only messages after this point are considered.
            Released as ``Any``, documented as a timestamp or marker: it is now a
            ``datetime`` (or ``None`` for the whole log).
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

    def get_mwi_status(self, user: str) -> dict[str, Any]:  # type: ignore[explicit-any]  # released signature kept until removal
        """Deprecated name of :meth:`read_mwi_status`.

        Returns ``read_mwi_status(user).as_dict()`` (keys ``waiting``, ``new``,
        ``old``); the driver warns with
        ``warn_renamed("get_mwi_status", "read_mwi_status")``.
        """
        ...

    def read_mwi_status(self, user: str) -> MwiStatus:
        """Return the current MWI status for *user*: the waiting flag and the counts
        of new (unheard) and old (heard but retained) messages."""
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
        """Publish presence *status* for *user* to all current subscribers.

        *status* is the provider's own word (typically ``online``, ``busy``, ``away``,
        ``offline``), published as given.
        """
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

    def get_offline_messages(self, user: str) -> list[dict[str, Any]]:  # type: ignore[explicit-any]  # released signature kept until removal
        """Deprecated name of :meth:`read_offline_messages`.

        Returns the entries as dicts (keys ``from``, ``body``, ``timestamp``): either
        ``[m.as_dict() for m in read_offline_messages(user)]`` (``timestamp`` is then
        ``"YYYY-MM-DD HH:MM:SS"``, space-separated) or, unchanged, the text the driver
        read from its store. The driver warns with
        ``warn_renamed("get_offline_messages", "read_offline_messages")``.
        """
        ...

    def read_offline_messages(self, user: str) -> list[OfflineMessage]:
        """Return the pending offline messages addressed to *user*: each has the
        sender URI, the body and when it was stored."""
        ...

    def clear_offline_messages(self, user: str) -> None:
        """Delete all pending offline messages addressed to *user*."""
        ...
