"""Quality of Experience (QoE) result and measurement specification models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast, override

from testprotocols.deprecation import MODEL_FRAMES, coerce_enum
from testprotocols.models._open_enum import OpenEnumPair
from testprotocols.models._sync import assign, settle


class QoeTool(StrEnum):
    """The tool a :class:`MeasurementSpec` measures with: the four the released
    implementers dispatch on."""

    BROWSER = "browser"
    HTTP_CLIENT = "http_client"
    WEBRTC = "webrtc"
    TCP_PROBE = "tcp_probe"


class PageCompletion(StrEnum):
    """The page-load event a browser measurement waits for (``wait_until``)."""

    LOAD = "load"
    DOMCONTENTLOADED = "domcontentloaded"
    NETWORKIDLE = "networkidle"
    COMMIT = "commit"


class QoeCompletion(StrEnum):
    """When a :class:`MeasurementSpec` measurement is complete: a
    :class:`PageCompletion` event, or ``DURATION`` (run for ``duration_s``, as the
    streaming and conferencing measurements do)."""

    LOAD = "load"
    DOMCONTENTLOADED = "domcontentloaded"
    NETWORKIDLE = "networkidle"
    COMMIT = "commit"
    DURATION = "duration"


class QoeScenario(StrEnum):
    """What ``QoeBrowser.measure_productivity`` measures. Grows on evidence."""

    PAGE_LOAD = "page_load"


class HttpVersion(StrEnum):
    """The HTTP version a transfer negotiated, spelled as a browser reports the next-hop
    protocol (``h2``, ``h3``, ``http/1.1``). The set is open: ``OTHER`` stands for any
    other word (``http/1.0``, ``h2c``, ...), which a record keeps verbatim in its raw
    companion field."""

    H1 = "http/1.1"
    H2 = "h2"
    H3 = "h3"
    OTHER = "other"


_PROTOCOL_PAIRS = (OpenEnumPair(HttpVersion, HttpVersion.OTHER, "protocol", "protocol_raw", True),)


@dataclass
class QoEResult:
    """Holds QoE metrics measured during a test (latency, jitter, MOS, etc.).

    *protocol* is the negotiated :class:`HttpVersion`, or ``None`` when not reported.
    The set is open: a word that names no member (``"http/1.0"``) becomes ``OTHER`` and
    the device's word is kept in *protocol_raw*, verbatim and without a warning. A plain
    ``str`` naming a member (``"h3"``) is deprecated: it warns and converts, so a reader
    holds the enum (``result.protocol == "h3"`` still holds, a ``StrEnum`` equals its
    text). *protocol_raw* is ``None`` unless *protocol* is ``OTHER``; the pair agrees
    after construction, ``replace`` and assignment and the side that changed wins, as for
    the other open-enum fields.
    """

    ttfb_ms: float | None = None
    load_time_ms: float | None = None
    startup_time_ms: float | None = None
    rebuffer_ratio: float | None = None
    latency_ms: float | None = None
    jitter_ms: float | None = None
    packet_loss_pct: float | None = None
    mos_score: float | None = None
    protocol: HttpVersion | str | None = None
    success: bool = True
    protocol_raw: str | None = None
    _protocol_seen: tuple[tuple[HttpVersion | None, str | None], ...] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        settle(self, _PROTOCOL_PAIRS, "_protocol_seen")

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name in ("protocol", "protocol_raw", "_protocol_seen"):
            assign(self, name, value, _PROTOCOL_PAIRS, "_protocol_seen")
            return
        object.__setattr__(self, name, value)


@dataclass
class MeasurementSpec:
    """Holds parameters controlling how a QoE measurement is performed.

    *tool* is a :class:`QoeTool` and *completion* a :class:`QoeCompletion` (a
    :class:`PageCompletion` is accepted and converted). A plain ``str`` naming a member
    is deprecated: it warns and converts, also on assignment, so a reader holds the enum
    (the text still compares equal). Any other string raises ``ValueError`` listing the
    legal values: the released field was free text, and an implementer treated an unknown
    tool as the browser.
    """

    tool: QoeTool | str = QoeTool.BROWSER
    completion: QoeCompletion | PageCompletion | str = QoeCompletion.NETWORKIDLE
    timeout_ms: int = 30000
    duration_s: int | None = None
    force_quic: bool = True

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "tool":
            value = coerce_enum(
                QoeTool,
                cast("QoeTool | str", value),
                what="MeasurementSpec.tool",
                skip_file_prefixes=MODEL_FRAMES,
            )
        elif name == "completion":
            if isinstance(value, PageCompletion):
                value = QoeCompletion(value.value)  # a page event, not a deprecated spelling
            value = coerce_enum(
                QoeCompletion,
                cast("QoeCompletion | str", value),
                what="MeasurementSpec.completion",
                skip_file_prefixes=MODEL_FRAMES,
            )
        object.__setattr__(self, name, value)
