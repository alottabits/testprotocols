"""Per-port access policy — 802.1X / MAB / MAC limit / sticky.

The access policy references RADIUS servers *by name* from the composed
``radius`` (``RadiusClient``) registry; address/port/secret resolution is the
driver's concern.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import AccessPolicy


@runtime_checkable
class PortSecurity(Protocol):
    """Abstract contract for per-port access policy."""

    def set_access_policy(self, policy: AccessPolicy) -> None:
        """Apply the access policy for ``policy.port``."""
        ...

    def get_access_policy(self, port: str) -> AccessPolicy:
        """Return the access policy for *port*."""
        ...
