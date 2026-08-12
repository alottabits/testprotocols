"""Flow-marking observation at a capture vantage.

``FlowSelector`` sits close to ``testprotocols.models.FlowMatch`` and is
deliberately NOT it: ``FlowMatch`` is config-side match *intent* (CIDRs,
``"any"``, rule vocabulary) that a driver writes toward a device;
``FlowSelector`` is observed *on-wire facts* (concrete addresses seen at a
capture point) that select frames in a finished capture. One is what a
rule should match; the other is what the wire showed.

These operations capture and count; deciding what a histogram *means*
(marked with the expected value, unmarked, absent) stays with the caller —
operations are assertion-free.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Mapping
from dataclasses import dataclass

from testprotocols.models import RuleProtocol
from testprotocols.pcap_capture import PcapCapture

from testoperations._capture import capture_shared_window, read_fields

#: tshark display-filter protocol names per ``RuleProtocol`` value.
#: ``ICMP6`` is the divergent one (enum ``"icmp6"``, tool ``"icmpv6"``) —
#: the reason this mapping is private to the operation rather than the
#: caller's job. ``ANY`` and ``None`` constrain nothing and have no token.
_PROTOCOL_TOKENS = {
    RuleProtocol.TCP: "tcp",
    RuleProtocol.UDP: "udp",
    RuleProtocol.ICMP: "icmp",
    RuleProtocol.ICMP6: "icmpv6",
}

#: The DSCP field read: both address families' DSCP columns plus the frame's
#: protocol chain (the outermost-wins merge key). ``occurrence=f`` pins each
#: field to its FIRST — outermost — occurrence: a frame carrying several IP
#: headers (an ICMP error quoting the offending header, IP-in-IP) would
#: otherwise emit comma-aggregated values and miscount. The tab separator is
#: pinned rather than assumed.
_DSCP_FIELDS = (
    "-T fields -e ip.dsfield.dscp -e ipv6.tclass.dscp -e frame.protocols"
    " -E occurrence=f -E separator=/t"
)


@dataclass(frozen=True)
class FlowSelector:
    """One observed flow, selected by on-wire address facts.

    ``src_host`` is optional by design: at an egress vantage the source is
    the device's live uplink address (post-NAT), at a receive vantage it
    may be unknown or irrelevant. ``protocol`` is the shared
    ``RuleProtocol`` vocabulary — never a tool token; ``None`` and
    ``RuleProtocol.ANY`` both leave the transport unconstrained.

    Fail-loud at construction, never mid-operation: host fields must be IP
    address literals sharing one address family, and ``dst_port`` requires
    a port-bearing transport (TCP or UDP) — a port filter without a
    transport is ambiguous, and ICMP/ICMP6 carry no ports.
    """

    dst_host: str
    src_host: str | None = None
    protocol: RuleProtocol | None = None
    dst_port: int | None = None

    def __post_init__(self) -> None:
        if self.dst_port is not None and self.protocol not in (
            RuleProtocol.TCP,
            RuleProtocol.UDP,
        ):
            raise ValueError(
                "dst_port requires protocol TCP or UDP — a port filter "
                "without a port-bearing transport is ambiguous"
            )
        try:
            dst = ipaddress.ip_address(self.dst_host)
        except ValueError as exc:
            raise ValueError(
                f"dst_host must be an IP address literal, got {self.dst_host!r}"
            ) from exc
        if self.src_host is not None:
            try:
                src = ipaddress.ip_address(self.src_host)
            except ValueError as exc:
                raise ValueError(
                    f"src_host must be an IP address literal, got {self.src_host!r}"
                ) from exc
            if src.version != dst.version:
                raise ValueError(
                    "src_host and dst_host must share one address family, "
                    f"got IPv{src.version} and IPv{dst.version}"
                )


def _flow_filter(flow: FlowSelector) -> str:
    """The selector's display filter — tool forms built here, never passed in."""
    family = ipaddress.ip_address(flow.dst_host).version
    host_field = "ip" if family == 4 else "ipv6"
    clauses = [f"{host_field}.dst=={flow.dst_host}"]
    if flow.src_host is not None:
        clauses.append(f"{host_field}.src=={flow.src_host}")
    token = _PROTOCOL_TOKENS.get(flow.protocol) if flow.protocol is not None else None
    if token is not None:
        clauses.append(token)
    if flow.dst_port is not None and token is not None:
        # Construction guarantees the transport is TCP or UDP here.
        clauses.append(f"{token}.dstport=={flow.dst_port}")
    return " and ".join(clauses)


def _line_dscp(line: str) -> int | None:
    """One field-read output line -> the frame's OUTERMOST DSCP value.

    Columns: IPv4 DSCP | IPv6 DSCP | protocol chain, each field at its
    first (outermost) occurrence. A plain frame fills exactly one DSCP
    column; an encapsulated frame carrying both families fills both, and
    the protocol chain names which header is outermost. At an encapsulated
    vantage the operation therefore reads OUTER-header DSCP — the wire
    fact at that vantage; what the outer value implies about inner marking
    is the caller's, and possibly vendor-conditioned, interpretation.
    """
    parts = [*line.split("\t"), "", "", ""][:3]
    v4, v6, protocols = (part.strip() for part in parts)
    if v4 and v6:
        for token in protocols.split(":"):
            if token == "ip":
                return int(v4)
            if token == "ipv6":
                return int(v6)
        return int(v4)
    if v4:
        return int(v4)
    if v6:
        return int(v6)
    return None


def observe_flow_dscp(
    pcap: PcapCapture,
    interface: str,
    flows: Mapping[str, FlowSelector],
    window_s: float,
    capture_file: str = "/tmp/marking_observation.pcap",
) -> dict[str, dict[int, int]]:
    """Capture *interface* for ONE window; per flow, count frames by DSCP value.

    One capture, every flow read from the same window. Returns
    ``{flow: {dscp_value: frame_count}}`` — a per-flow histogram; the
    marking judgment (marked with the expected value / unmarked / absent)
    stays with the caller. Total over both address families: each captured
    frame contributes exactly one DSCP value, from the IPv4 DS field or
    the IPv6 traffic class (the same RFC 2474 semantics), the outermost
    header winning on encapsulated frames; an empty histogram therefore
    means the flow was absent, never "wrong family".
    """
    reads = [(_flow_filter(flow), _DSCP_FIELDS) for flow in flows.values()]
    capture_shared_window([(pcap, interface, capture_file)], window_s)
    outputs = read_fields(pcap, capture_file, reads)
    histograms: dict[str, dict[int, int]] = {}
    for name, lines in zip(flows, outputs, strict=True):
        histogram: dict[int, int] = {}
        for line in lines:
            value = _line_dscp(line)
            if value is None:
                continue
            histogram[value] = histogram.get(value, 0) + 1
        histograms[name] = histogram
    return histograms
