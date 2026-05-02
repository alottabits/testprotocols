"""Streaming origin (HLS/DASH) server template.

Defines the abstract contract for content-origin servers used by
streaming/QoE test scenarios. Implementations are responsible for
ensuring named assets are present and serveable; richer surface
(bitrate enumeration, log inspection, etc.) is intentionally deferred
until a concrete testbed needs it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StreamingServer(Protocol):
    """Abstract contract for HLS/DASH content origins used in test scenarios."""

    def ensure_content_available(self, video_id: str = "default") -> None:
        """Ensure the named asset is present in the origin.

        Idempotent: returns immediately if the asset is already seeded;
        otherwise generates and uploads it. Raises if the operation fails.

        Parameters
        ----------
        video_id:
            Identifier of the asset to seed. Implementation decides how
            this maps to actual content (bucket key, file path, stream
            name, etc.).
        """
        ...
