"""Quality of Experience (QoE) result and measurement specification models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import override


class QoeTool(StrEnum):
    """The tool a :class:`MeasurementSpec` measures with: the four the released
    implementers dispatch on. ``repr()`` of a member is the quoted text (``'browser'``)."""

    BROWSER = "browser"
    HTTP_CLIENT = "http_client"
    WEBRTC = "webrtc"
    TCP_PROBE = "tcp_probe"

    @override
    def __repr__(self) -> str:
        """The text, quoted: released implementers build generated text with ``repr(spec.tool)``."""
        return repr(self.value)


class PageCompletion(StrEnum):
    """The page-load event a browser measurement waits for (``wait_until``)."""

    LOAD = "load"
    DOMCONTENTLOADED = "domcontentloaded"
    NETWORKIDLE = "networkidle"
    COMMIT = "commit"


class QoeCompletion(StrEnum):
    """When a :class:`MeasurementSpec` measurement is complete: a
    :class:`PageCompletion` event; ``DURATION`` (run for ``duration_s``, as the streaming and
    conferencing measurements do); ``RESPONSE`` (the HTTP response arrived, for the
    ``http_client`` tool) or ``CONNECT`` (the connection opened, for ``tcp_probe``).

    ``repr()`` of a member is the quoted text (``'load'``), not the enum default, like
    :class:`QoeTool`: a released implementer embeds ``repr(spec.completion)`` in generated
    text and must keep getting a quoted literal."""

    LOAD = "load"
    DOMCONTENTLOADED = "domcontentloaded"
    NETWORKIDLE = "networkidle"
    COMMIT = "commit"
    DURATION = "duration"
    RESPONSE = "response"
    CONNECT = "connect"

    @override
    def __repr__(self) -> str:
        """The text, quoted: released implementers build generated text with
        ``repr(spec.completion)``, as for :class:`QoeTool`."""
        return repr(self.value)


class QoeScenario(StrEnum):
    """What ``QoeBrowser.measure_productivity`` measures. Grows on evidence."""

    PAGE_LOAD = "page_load"


@dataclass
class QoEResult:
    """Holds QoE metrics measured during a test (latency, jitter, MOS, etc.).

    *protocol* is the negotiated HTTP version as the device reports it (for example
    ``h2``, ``h3``, ``http/1.1``), stored as given, or ``None`` when not reported.
    """

    ttfb_ms: float | None = None
    load_time_ms: float | None = None
    startup_time_ms: float | None = None
    rebuffer_ratio: float | None = None
    latency_ms: float | None = None
    jitter_ms: float | None = None
    packet_loss_pct: float | None = None
    mos_score: float | None = None
    protocol: str | None = None
    success: bool = True


@dataclass
class MeasurementSpec:
    """Holds parameters controlling how a QoE measurement is performed.

    *tool* is a :class:`QoeTool` and *completion* a :class:`QoeCompletion` (a
    :class:`PageCompletion` has the same words). A plain ``str`` naming a member is
    deprecated and stored as given (a member compares equal to its text); each field
    narrows to its enum when the plain ``str`` form is removed.
    """

    tool: QoeTool | str = QoeTool.BROWSER
    completion: QoeCompletion | PageCompletion | str = QoeCompletion.NETWORKIDLE
    timeout_ms: int = 30000
    duration_s: int | None = None
    force_quic: bool = True
