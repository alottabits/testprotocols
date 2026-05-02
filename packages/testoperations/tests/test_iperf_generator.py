"""Tests for testoperations.iperf_generator module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from testoperations.iperf_generator import (
    saturate_link,
    stop_all_generators,
)
from testprotocols.models.traffic import TrafficResult


def _peer(server_ip: str, flow_id: str) -> MagicMock:
    """Build a mock peer generator with the given server_ip and start_traffic return."""
    peer = MagicMock()
    peer.server_ip = server_ip
    peer.start_traffic.return_value = flow_id
    return peer


# ---------------------------------------------------------------------------
# saturate_link
# ---------------------------------------------------------------------------


class TestSaturateLink:
    def test_returns_flow_ids_keyed_by_direction(self):
        peer_a = _peer("PEER_A_ADDR", "flow-a")
        peer_b = _peer("PEER_B_ADDR", "flow-b")

        result = saturate_link(peer_a, peer_b, a_to_b_mbps=100.0)

        peer_a.start_traffic.assert_called_once()
        peer_b.start_traffic.assert_called_once()
        assert result == {"a_to_b": "flow-a", "b_to_a": "flow-b"}

    def test_each_peer_targets_the_other_peers_server_ip(self):
        peer_a = _peer("PEER_A_ADDR", "flow-a")
        peer_b = _peer("PEER_B_ADDR", "flow-b")

        saturate_link(peer_a, peer_b, a_to_b_mbps=50.0)

        a_spec = peer_a.start_traffic.call_args[0][0]
        b_spec = peer_b.start_traffic.call_args[0][0]
        assert a_spec.destination == "PEER_B_ADDR"  # a -> b
        assert b_spec.destination == "PEER_A_ADDR"  # b -> a

    def test_symmetric_load_applies_same_bandwidth_to_both_directions(self):
        peer_a = _peer("PEER_A_ADDR", "flow-a")
        peer_b = _peer("PEER_B_ADDR", "flow-b")

        saturate_link(peer_a, peer_b, a_to_b_mbps=85.0)

        a_spec = peer_a.start_traffic.call_args[0][0]
        b_spec = peer_b.start_traffic.call_args[0][0]
        assert a_spec.bandwidth_mbps == 85.0
        assert b_spec.bandwidth_mbps == 85.0
        assert a_spec.protocol == "udp"
        assert a_spec.dscp == 0
        assert a_spec.duration_s == 120

    def test_asymmetric_load_applies_independent_bandwidths(self):
        peer_a = _peer("PEER_A_ADDR", "flow-a")
        peer_b = _peer("PEER_B_ADDR", "flow-b")

        saturate_link(peer_a, peer_b, a_to_b_mbps=10.0, b_to_a_mbps=100.0)

        a_spec = peer_a.start_traffic.call_args[0][0]
        b_spec = peer_b.start_traffic.call_args[0][0]
        assert a_spec.bandwidth_mbps == 10.0
        assert b_spec.bandwidth_mbps == 100.0

    def test_honours_non_default_kwargs(self):
        peer_a = _peer("PEER_A_ADDR", "flow-a")
        peer_b = _peer("PEER_B_ADDR", "flow-b")

        saturate_link(
            peer_a,
            peer_b,
            a_to_b_mbps=50.0,
            dscp=46,
            duration_s=30,
            protocol="tcp",
        )

        a_spec = peer_a.start_traffic.call_args[0][0]
        assert a_spec.dscp == 46
        assert a_spec.duration_s == 30
        assert a_spec.protocol == "tcp"

    def test_rejects_peers_resolving_to_same_ip(self):
        peer_a = _peer("PEER_A_ADDR", "flow-a")
        peer_b = _peer("PEER_A_ADDR", "flow-b")

        with pytest.raises(ValueError, match="PEER_A_ADDR"):
            saturate_link(peer_a, peer_b, a_to_b_mbps=50.0)

        peer_a.start_traffic.assert_not_called()
        peer_b.start_traffic.assert_not_called()


# ---------------------------------------------------------------------------
# stop_all_generators
# ---------------------------------------------------------------------------


class TestStopAllGenerators:
    def test_stops_all_listed_generators(self):
        gen1 = MagicMock()
        gen2 = MagicMock()
        gen3 = MagicMock()
        gen1.stop_all_traffic.return_value = {"f1": TrafficResult()}
        gen2.stop_all_traffic.return_value = {"f2": TrafficResult()}
        gen3.stop_all_traffic.return_value = {}

        result = stop_all_generators([gen1, gen2, gen3])

        gen1.stop_all_traffic.assert_called_once_with()
        gen2.stop_all_traffic.assert_called_once_with()
        gen3.stop_all_traffic.assert_called_once_with()
        assert len(result) == 3

    def test_returns_per_generator_results(self):
        gen1 = MagicMock()
        r1 = TrafficResult(sent_mbps=100.0)
        gen1.stop_all_traffic.return_value = {"flow-a": r1}

        result = stop_all_generators([gen1])
        assert result[0] == {"flow-a": r1}
