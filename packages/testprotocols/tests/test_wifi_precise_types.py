"""Wi-Fi vocabularies typed: enums, shape 1/3."""

from __future__ import annotations

import dataclasses
import typing
import warnings
from enum import IntEnum

import pytest
from _helpers import assert_str_value
from testprotocols.deprecation import coerce_enum
from testprotocols.models.wifi import (
    ChannelWidth,
    MeshRole,
    MfpMode,
    WifiAcl,
    WifiAclMode,
    WifiBand,
    WifiBssConfig,
    WifiCaptiveConfig,
    WifiChannelUtilization,
    WifiMeshLink,
    WifiMeshNode,
    WifiMeshStatus,
    WifiNeighbor,
    WifiPhyMode,
    WifiRadioStats,
    WifiSecurityMode,
    WifiStation,
)
from testprotocols.wifi_bss import WifiBss
from testprotocols.wifi_client import WifiClient
from testprotocols.wifi_mesh import WifiMesh, WifiMeshWhiteBox
from testprotocols.wifi_radio import WifiRadio
from testprotocols.wifi_rf import WifiRf

# --- members equal the released strings ---


@pytest.mark.parametrize(
    ("member", "word"),
    [
        (WifiBand.GHZ_2_4, "2.4GHz"),
        (WifiBand.GHZ_5, "5GHz"),
        (WifiBand.GHZ_6, "6GHz"),
        (WifiSecurityMode.OPEN, "Open"),
        (WifiSecurityMode.OWE, "OWE"),
        (WifiSecurityMode.WPA2_PSK, "WPA2-PSK"),
        (WifiSecurityMode.WPA2_EAP, "WPA2-EAP"),
        (WifiSecurityMode.WPA3_SAE, "WPA3-SAE"),
        (WifiSecurityMode.WPA3_EAP, "WPA3-EAP"),
        (WifiSecurityMode.WPA2_WPA3_PSK_MIXED, "WPA2-WPA3-PSK-Mixed"),
        (WifiSecurityMode.WPA2_WPA3_EAP_MIXED, "WPA2-WPA3-EAP-Mixed"),
        (MfpMode.OFF, "off"),
        (MfpMode.OPTIONAL, "optional"),
        (MfpMode.REQUIRED, "required"),
        (WifiAclMode.DISABLED, "disabled"),
        (WifiAclMode.ALLOW, "allow"),
        (WifiAclMode.DENY, "deny"),
        (WifiPhyMode.A, "a"),
        (WifiPhyMode.B, "b"),
        (WifiPhyMode.G, "g"),
        (WifiPhyMode.N, "n"),
        (WifiPhyMode.AC, "ac"),
        (WifiPhyMode.AX, "ax"),
        (WifiPhyMode.BE, "be"),
        (MeshRole.CONTROLLER, "controller"),
        (MeshRole.AGENT, "agent"),
        (MeshRole.CONTROLLER_AND_AGENT, "controller-and-agent"),
        (MeshRole.UNCOMMISSIONED, "uncommissioned"),
    ],
)
def test_members_equal_their_released_strings(member: object, word: str) -> None:
    assert isinstance(member, str)
    assert str(member) == word
    assert member == word


def test_enum_member_sets_are_the_released_ones() -> None:
    assert {m.value for m in WifiBand} == {"2.4GHz", "5GHz", "6GHz"}
    assert {m.value for m in MfpMode} == {"off", "optional", "required"}
    assert {int(m) for m in ChannelWidth} == {20, 40, 80, 160, 320}
    assert issubclass(ChannelWidth, IntEnum)
    assert_str_value(WifiBand.GHZ_5, "5GHz")


# --- coerce_enum: an IntEnum takes an int without a warning ---


def test_coerce_enum_accepts_an_int_for_an_int_enum_silently() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert coerce_enum(ChannelWidth, 80, what="bandwidth_mhz") is ChannelWidth.MHZ_80
        assert coerce_enum(ChannelWidth, ChannelWidth.MHZ_20, what="w") is ChannelWidth.MHZ_20


def test_coerce_enum_int_enum_refuses_a_number_that_is_no_member() -> None:
    with pytest.raises(ValueError, match="bandwidth_mhz: 30 is not one of"):
        coerce_enum(ChannelWidth, 30, what="bandwidth_mhz")


def test_coerce_enum_int_enum_refuses_a_bool_and_text() -> None:
    with pytest.raises(TypeError):  # a bool is a wrong type
        coerce_enum(ChannelWidth, True, what="w")
    with pytest.raises(ValueError):  # text is never an IntEnum's value
        coerce_enum(ChannelWidth, "80", what="w")


def test_coerce_enum_str_enum_still_warns_on_a_plain_string() -> None:
    with pytest.warns(DeprecationWarning):
        assert coerce_enum(WifiBand, "5GHz", what="band") is WifiBand.GHZ_5


# --- shape 3 models ---


def _bss(
    band: WifiBand | str = WifiBand.GHZ_5,
    security_mode: WifiSecurityMode | str = WifiSecurityMode.WPA2_PSK,
    mfp: MfpMode | str = MfpMode.OPTIONAL,
) -> WifiBssConfig:
    return WifiBssConfig(
        name="guest",
        band=band,
        ssid="s",
        bssid="aa:bb:cc:dd:ee:ff",
        enabled=True,
        broadcast_enabled=True,
        security_mode=security_mode,
        radius_server_name=None,
        mfp=mfp,
        vlan_id=None,
        max_clients=None,
        dtim_period=2,
        captive_portal=WifiCaptiveConfig(enabled=False, redirect_url=None),
    )


def test_bss_config_members_are_silent() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        c = _bss()
    assert c.band is WifiBand.GHZ_5
    assert c.security_mode is WifiSecurityMode.WPA2_PSK
    assert c.mfp is MfpMode.OPTIONAL


def test_bss_config_released_strings_convert_with_a_warning() -> None:
    with pytest.warns(DeprecationWarning) as seen:
        c = _bss("2.4GHz", "WPA3-SAE", "required")
    assert len(seen) == 3
    assert c.band is WifiBand.GHZ_2_4
    assert c.security_mode is WifiSecurityMode.WPA3_SAE
    assert c.mfp is MfpMode.REQUIRED
    assert_str_value(c.band, "2.4GHz")


def test_bss_config_warning_points_at_the_construction_site() -> None:
    with pytest.warns(DeprecationWarning) as seen:
        _bss("5GHz")
    assert seen[0].filename == __file__


def test_bss_config_unknown_word_raises_and_assignment_converts() -> None:
    with pytest.raises(ValueError, match="band: '7GHz' is not one of"):
        _bss("7GHz")
    c = _bss()
    with pytest.warns(DeprecationWarning):
        c.mfp = "off"
    assert c.mfp is MfpMode.OFF
    with pytest.raises(ValueError):
        c.security_mode = "WEP"
    assert c.security_mode is WifiSecurityMode.WPA2_PSK
    c2 = dataclasses.replace(c, band=WifiBand.GHZ_6)
    assert c2.band is WifiBand.GHZ_6


def test_other_models_coerce_their_fields() -> None:
    with pytest.warns(DeprecationWarning):
        n = WifiNeighbor("aa:bb:cc:dd:ee:ff", "x", "5GHz", 36, -60, "WPA2", 1.0)
    assert n.band is WifiBand.GHZ_5
    assert n.security_mode == "WPA2"  # best-effort identification: stays free text
    with pytest.warns(DeprecationWarning):
        u = WifiChannelUtilization("6GHz", 10, None, None, None)
    assert u.band is WifiBand.GHZ_6
    with pytest.warns(DeprecationWarning):
        r = WifiRadioStats("2.4GHz", 1, 1, 1, 1, 0, 0)
    assert r.band is WifiBand.GHZ_2_4
    with pytest.warns(DeprecationWarning):
        link = WifiMeshLink("5GHz", 36, -50, 100.0)
    assert link.band is WifiBand.GHZ_5
    with pytest.raises(ValueError):
        WifiMeshLink("9GHz", 36, -50, 100.0)


def test_acl_and_mesh_roles() -> None:
    with pytest.warns(DeprecationWarning):
        a = WifiAcl("guest", "deny")
    assert a.mode is WifiAclMode.DENY
    assert WifiAcl("guest", WifiAclMode.ALLOW).mode is WifiAclMode.ALLOW
    with pytest.raises(ValueError):
        WifiAcl("guest", "blacklist")
    with pytest.warns(DeprecationWarning):
        s = WifiMeshStatus("controller-and-agent", True, None, 0, None)
    assert s.role is MeshRole.CONTROLLER_AND_AGENT
    with pytest.warns(DeprecationWarning):
        s.role = "uncommissioned"
    assert s.role is MeshRole.UNCOMMISSIONED
    with pytest.warns(DeprecationWarning):
        node = WifiMeshNode("aa:bb:cc:dd:ee:ff", "agent", "11:22:33:44:55:66", 1)
    assert node.role is MeshRole.AGENT
    with pytest.raises(ValueError):
        WifiMeshNode("aa:bb:cc:dd:ee:ff", "relay", None, 1)


# --- WifiStation ---

_MAC = "aa:bb:cc:dd:ee:ff"


def _station(
    *, band: WifiBand | str = WifiBand.GHZ_5, flags: list[str] | None = None
) -> WifiStation:
    return WifiStation(
        mac=_MAC,
        bss_name="guest",
        band=band,
        ip_address=None,
        associated_since=1.0,
        rssi_dbm=-50,
        snr_db=None,
        tx_rate_mbps=1.0,
        rx_rate_mbps=1.0,
        tx_bytes=0,
        rx_bytes=0,
        tx_packets=0,
        rx_packets=0,
        tx_retries=0,
        capability_flags=[] if flags is None else flags,
    )


def test_station_band_is_coerced() -> None:
    with pytest.warns(DeprecationWarning):
        s = _station(band="6GHz")
    assert s.band is WifiBand.GHZ_6
    with pytest.raises(ValueError):
        _station(band="60GHz")


def test_station_capability_flags_are_the_device_words_stored_as_given() -> None:
    assert _station().capability_flags == []
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        s = _station(flags=["HT", "he", "TWT"])
    assert s.capability_flags == ["HT", "he", "TWT"]


# --- Protocol signatures (shape 1, shape 1i, shape 5) ---


def _hints(member: object) -> dict[str, object]:
    return typing.get_type_hints(member)


def test_bss_parameters_are_typed() -> None:
    h = _hints(WifiBss.create_bss)
    assert h["band"] == WifiBand | str
    assert h["security_mode"] == WifiSecurityMode | str
    assert h["mfp"] == MfpMode | str
    assert _hints(WifiBss.set_security)["mode"] == WifiSecurityMode | str
    assert _hints(WifiBss.set_acl_mode)["mode"] == WifiAclMode | str


def test_radio_parameters_are_typed() -> None:
    for name in (
        "set_enabled",
        "get_enabled",
        "set_channel",
        "get_channel",
        "list_supported_channels",
        "set_bandwidth",
        "get_bandwidth",
        "set_tx_power",
        "get_tx_power",
        "set_mode",
        "get_mode",
        "get_dfs_state",
    ):
        assert _hints(getattr(WifiRadio, name))["band"] == WifiBand | str, name
    assert _hints(WifiRadio.set_bandwidth)["bandwidth_mhz"] == ChannelWidth | int
    assert _hints(WifiRadio.set_mode)["mode"] == WifiPhyMode | str
    # shape 6: returns are announced, not yet narrowed
    assert _hints(WifiRadio.list_radios)["return"] == list[str]
    assert _hints(WifiRadio.get_mode)["return"] is str
    assert _hints(WifiRadio.get_bandwidth)["return"] is int


def test_rf_and_mesh_bands_are_typed() -> None:
    for name in ("scan", "get_neighbors", "get_channel_utilization", "get_noise_floor"):
        assert _hints(getattr(WifiRf, name))["band"] == WifiBand | str, name
    assert _hints(WifiRf.get_radio_stats)["band"] == WifiBand | str
    assert _hints(WifiMesh.set_backhaul_band)["band"] == WifiBand | str | None


def test_client_channel_is_int_or_str_and_supported_channels_is_new() -> None:
    assert _hints(WifiClient.set_wlan_scan_channel)["channel"] == int | str
    assert _hints(WifiClient.supported_channels)["return"] == list[int]
    assert _hints(WifiClient.supported_channels)["band"] is WifiBand
    # the released member keeps its signature (shape 5: deprecated, not changed)
    assert _hints(WifiClient.iwlist_supported_channels)["return"] == list[str]
    assert _hints(WifiClient.iwlist_supported_channels)["wifi_band"] is str
    assert "supported_channels" in WifiClient.__protocol_attrs__  # type: ignore[attr-defined]


def test_easymesh_message_type_stays_str() -> None:
    assert _hints(WifiMeshWhiteBox.get_raw_easymesh_tlvs)["message_type"] == str | None
