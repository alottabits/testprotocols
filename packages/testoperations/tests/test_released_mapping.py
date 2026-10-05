"""The shared released-dict read access of the three dict-replacing records."""

from __future__ import annotations

import copy
import warnings
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from testoperations._released import ReleasedMapping
from testoperations.homing import verify_home
from testoperations.iperf_client import start_iperf
from testoperations.iperf_generator import saturate_link
from testprotocols.models import IperfProcess
from testprotocols.models.sdwan_appliance import (
    SiteToSiteVpnConfig,
    VlanConfig,
    VpnPeerState,
    VpnPeerStatus,
    VpnRole,
)


def _iperf() -> ReleasedMapping:
    client = MagicMock(spec=["start_sender_session"])
    server = MagicMock(spec=["start_receiver_session"])
    client.start_sender_session.return_value = IperfProcess(41, "s.log")
    server.start_receiver_session.return_value = IperfProcess(42, "r.log")
    return start_iperf(client, server, port=5001, host="h")


def _pair() -> ReleasedMapping:
    a, b = MagicMock(), MagicMock()
    a.server_ip, b.server_ip = "A", "B"
    a.start_traffic.return_value, b.start_traffic.return_value = "fa", "fb"
    return saturate_link(a, b, a_to_b_mbps=1.0)


def _home() -> ReleasedMapping:
    vlan = VlanConfig(vlan_id=10, name="n", subnet="10.0.0.0/24", appliance_ip="10.0.0.1")
    lan, vpn = MagicMock(), MagicMock()
    lan.get_vlan.return_value = vlan
    vpn.get_vpn_config.return_value = SiteToSiteVpnConfig(role=VpnRole.SPOKE, hubs=[], subnets=[])
    vpn.get_vpn_peers.return_value = [VpnPeerStatus(name="p", state=VpnPeerState.REACHABLE)]
    return verify_home(vlan, lan, vpn)


RECORDS: list[tuple[Callable[[], ReleasedMapping], int]] = [(_iperf, 4), (_pair, 2), (_home, 4)]


@pytest.mark.parametrize(("make", "size"), RECORDS)
class TestFullDictSurface:
    def test_len_keys_items_values_agree_with_the_released_dict(
        self, make: Callable[[], ReleasedMapping], size: int
    ) -> None:
        r = make()
        with pytest.warns(DeprecationWarning, match="as_dict"):
            released = r.as_dict()
        with pytest.warns(DeprecationWarning, match="len"):
            assert len(r) == size
        with pytest.warns(DeprecationWarning, match="keys") as w:
            assert list(r.keys()) == list(released)
        assert len(w) == 1
        with pytest.warns(DeprecationWarning, match="items") as w:
            assert r.items() == list(released.items())
        assert len(w) == 1
        with pytest.warns(DeprecationWarning, match="values") as w:
            assert r.values() == list(released.values())
        assert len(w) == 1

    def test_dict_and_unpacking_warn_for_keys_and_each_key_read(
        self, make: Callable[[], ReleasedMapping], size: int
    ) -> None:
        r = make()
        with pytest.warns(DeprecationWarning) as w:
            converted = dict(r)
        assert len(w) == 1 + size and len(converted) == size
        with pytest.warns(DeprecationWarning) as w:
            unpacked = {**r}
        assert len(w) == 1 + size and unpacked == converted

    def test_a_later_separate_read_always_warns(
        self, make: Callable[[], ReleasedMapping], size: int
    ) -> None:
        r = make()
        with pytest.warns(DeprecationWarning):
            keys = list(r.keys())
        with pytest.warns(DeprecationWarning, match="indexing"):
            r[keys[0]]
        clone = copy.copy(r)
        with pytest.warns(DeprecationWarning, match="indexing"):
            clone[keys[0]]
        with pytest.warns(DeprecationWarning, match="indexing"):
            r[keys[0]]

    def test_fields_never_warn(self, make: Callable[[], ReleasedMapping], size: int) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            r = make()
            assert r == make()


@pytest.mark.parametrize(("make", "size"), RECORDS)
def test_truthiness_is_true_without_a_warning(
    make: Callable[[], ReleasedMapping], size: int
) -> None:
    record = make()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert record  # a released dict with keys was truthy with no call to len()
        assert bool(record) is True
    assert size > 0
