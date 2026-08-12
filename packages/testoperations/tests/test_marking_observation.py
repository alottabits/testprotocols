"""Tests for testoperations.marking_observation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from testoperations.marking_observation import FlowSelector, observe_flow_dscp
from testprotocols.models import RuleProtocol


def _pcap(tshark_output: str = "") -> MagicMock:
    pcap = MagicMock()
    pcap.start_tcpdump.return_value = "pid-1"
    pcap.tshark_read_pcap.return_value = tshark_output
    return pcap


UDP_FLOW = FlowSelector(
    dst_host="192.0.2.9", src_host="198.51.100.7", protocol=RuleProtocol.UDP, dst_port=5401
)


# ---------------------------------------------------------------------------
# FlowSelector — fail-loud construction
# ---------------------------------------------------------------------------


class TestFlowSelectorValidation:
    def test_port_requires_a_port_bearing_transport(self) -> None:
        with pytest.raises(ValueError, match="port-bearing transport"):
            FlowSelector(dst_host="192.0.2.9", dst_port=5401)

    def test_port_rejects_icmp(self) -> None:
        with pytest.raises(ValueError, match="port-bearing transport"):
            FlowSelector(dst_host="192.0.2.9", protocol=RuleProtocol.ICMP, dst_port=7)

    def test_port_rejects_any(self) -> None:
        with pytest.raises(ValueError, match="port-bearing transport"):
            FlowSelector(dst_host="192.0.2.9", protocol=RuleProtocol.ANY, dst_port=7)

    def test_dst_host_must_be_an_ip_literal(self) -> None:
        with pytest.raises(ValueError, match="dst_host must be an IP address literal"):
            FlowSelector(dst_host="resolver.example.net")

    def test_src_host_must_be_an_ip_literal(self) -> None:
        with pytest.raises(ValueError, match="src_host must be an IP address literal"):
            FlowSelector(dst_host="192.0.2.9", src_host="uplink-1")

    def test_hosts_must_share_one_address_family(self) -> None:
        with pytest.raises(ValueError, match="share one address family"):
            FlowSelector(dst_host="192.0.2.9", src_host="2001:db8::7")

    def test_valid_selectors_construct(self) -> None:
        FlowSelector(dst_host="192.0.2.9")
        FlowSelector(dst_host="2001:db8::9", src_host="2001:db8::7")
        FlowSelector(dst_host="192.0.2.9", protocol=RuleProtocol.TCP, dst_port=443)


# ---------------------------------------------------------------------------
# Display-filter construction (tool forms stay inside)
# ---------------------------------------------------------------------------


def _filter_of(pcap: MagicMock, index: int = 0) -> str:
    args: str = pcap.tshark_read_pcap.call_args_list[index].kwargs["additional_args"]
    return args


class TestFilterConstruction:
    def test_ipv4_clauses_with_transport_and_port(self) -> None:
        pcap = _pcap()
        observe_flow_dscp(pcap, "north0", {"governed": UDP_FLOW}, window_s=0)
        args = _filter_of(pcap)
        assert (
            '-Y "ip.dst==192.0.2.9 and ip.src==198.51.100.7 and udp and udp.dstport==5401"' in args
        )

    def test_ipv6_clauses_use_the_ipv6_fields(self) -> None:
        pcap = _pcap()
        flow = FlowSelector(dst_host="2001:db8::9", src_host="2001:db8::7")
        observe_flow_dscp(pcap, "north0", {"f": flow}, window_s=0)
        assert '-Y "ipv6.dst==2001:db8::9 and ipv6.src==2001:db8::7"' in _filter_of(pcap)

    def test_icmp6_maps_to_the_divergent_tool_token(self) -> None:
        pcap = _pcap()
        flow = FlowSelector(dst_host="2001:db8::9", protocol=RuleProtocol.ICMP6)
        observe_flow_dscp(pcap, "north0", {"f": flow}, window_s=0)
        assert "icmpv6" in _filter_of(pcap)

    def test_any_and_none_constrain_nothing(self) -> None:
        pcap = _pcap()
        flows = {
            "a": FlowSelector(dst_host="192.0.2.9", protocol=RuleProtocol.ANY),
            "b": FlowSelector(dst_host="192.0.2.10"),
        }
        observe_flow_dscp(pcap, "north0", flows, window_s=0)
        assert '-Y "ip.dst==192.0.2.9"' in _filter_of(pcap, 0)
        assert '-Y "ip.dst==192.0.2.10"' in _filter_of(pcap, 1)

    def test_field_read_pins_occurrence_and_separator(self) -> None:
        # Condition 1 of the accepted proposal: first-occurrence extraction
        # (outermost header) and an explicit separator, or multi-header
        # frames emit aggregated values and miscount.
        pcap = _pcap()
        observe_flow_dscp(pcap, "north0", {"governed": UDP_FLOW}, window_s=0)
        args = _filter_of(pcap)
        assert "-e ip.dsfield.dscp" in args
        assert "-e ipv6.tclass.dscp" in args
        assert "-e frame.protocols" in args
        assert "-E occurrence=f" in args
        assert "-E separator=/t" in args


# ---------------------------------------------------------------------------
# Histograms (the judgment stays with the caller)
# ---------------------------------------------------------------------------


class TestObserveFlowDscp:
    def test_unmarked_flow_counts_dscp_zero(self) -> None:
        pcap = _pcap("0\t\teth:ethertype:ip:udp\n0\t\teth:ethertype:ip:udp\n")
        histograms = observe_flow_dscp(pcap, "north0", {"control": UDP_FLOW}, window_s=0)
        assert histograms == {"control": {0: 2}}

    def test_marked_flow_counts_the_declared_value(self) -> None:
        pcap = _pcap("18\t\teth:ethertype:ip:udp\n18\t\teth:ethertype:ip:udp\n")
        histograms = observe_flow_dscp(pcap, "north0", {"governed": UDP_FLOW}, window_s=0)
        assert histograms == {"governed": {18: 2}}

    def test_partially_converged_flow_shows_both_values(self) -> None:
        pcap = _pcap("0\t\teth:ethertype:ip:udp\n18\t\teth:ethertype:ip:udp\n")
        histograms = observe_flow_dscp(pcap, "north0", {"governed": UDP_FLOW}, window_s=0)
        assert histograms == {"governed": {0: 1, 18: 1}}

    def test_absent_flow_is_an_empty_histogram(self) -> None:
        histograms = observe_flow_dscp(pcap := _pcap(""), "n0", {"g": UDP_FLOW}, window_s=0)
        assert histograms == {"g": {}}
        assert pcap.stop_tcpdump.called  # the window still ran

    def test_ipv6_column_counts_when_v4_is_empty(self) -> None:
        pcap = _pcap("\t46\teth:ethertype:ipv6:udp\n")
        flow = FlowSelector(dst_host="2001:db8::9")
        assert observe_flow_dscp(pcap, "n0", {"f": flow}, window_s=0) == {"f": {46: 1}}

    def test_multi_header_frame_takes_the_outermost_value_v4_outer(self) -> None:
        # 6in4: outer IPv4 (dscp 18) around inner IPv6 (tclass dscp 0) —
        # the protocol chain names ip before ipv6, so the outer value wins.
        pcap = _pcap("18\t0\teth:ethertype:ip:ipv6:udp\n")
        assert observe_flow_dscp(pcap, "n0", {"g": UDP_FLOW}, window_s=0) == {"g": {18: 1}}

    def test_multi_header_frame_takes_the_outermost_value_v6_outer(self) -> None:
        # 4in6: outer IPv6 (tclass dscp 46) around inner IPv4 (dscp 0).
        pcap = _pcap("0\t46\teth:ethertype:ipv6:ip:udp\n")
        flow = FlowSelector(dst_host="2001:db8::9")
        assert observe_flow_dscp(pcap, "n0", {"f": flow}, window_s=0) == {"f": {46: 1}}

    def test_every_flow_reads_the_same_single_capture(self) -> None:
        pcap = _pcap("18\t\teth:ethertype:ip:udp\n")
        flows = {
            "governed": UDP_FLOW,
            "control": FlowSelector(
                dst_host="192.0.2.10", protocol=RuleProtocol.UDP, dst_port=5402
            ),
        }
        observe_flow_dscp(pcap, "north0", flows, window_s=0, capture_file="/tmp/m.pcap")
        pcap.start_tcpdump.assert_called_once_with("north0", None, output_file="/tmp/m.pcap")
        pcap.stop_tcpdump.assert_called_once()
        removals = [call.kwargs["rm_pcap"] for call in pcap.tshark_read_pcap.call_args_list]
        assert removals == [False, True]  # two reads, one capture, removed at the end
