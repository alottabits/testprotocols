"""WAN-edge models typed: link states (shape 3), AppFlow category (shape 3o), orphans deprecated."""

from __future__ import annotations

import dataclasses
import importlib
import warnings

import pytest
from testprotocols.models import (
    AppFlow,
    ApplicationCategory,
    LinkHealthReport,
    LinkStatus,
    UplinkState,
)

# --- M14 / M15: link states ---


def _health(state: UplinkState | str) -> LinkHealthReport:
    return LinkHealthReport(
        state=state,
        route_installed=True,
        avg_rtt_ms=1.0,
        jitter_ms=0.1,
        loss_percent=0.0,
        sla_compliant=True,
    )


@pytest.mark.parametrize("word", ["up", "down", "degraded"])
def test_link_status_released_words_convert_with_a_warning(word: str) -> None:
    with pytest.warns(DeprecationWarning, match=r"LinkStatus.state: plain string"):
        s = LinkStatus(name="wan1", state=word, ip_address="198.51.100.2")
    assert s.state is UplinkState(word)
    assert s.state == word


def test_link_status_member_is_silent() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        s = LinkStatus("wan1", UplinkState.DOWN, "")
    assert s.state is UplinkState.DOWN


def test_link_status_assignment_converts_and_refuses_unknown_words() -> None:
    s = LinkStatus("wan1", UplinkState.UP, "")
    with pytest.warns(DeprecationWarning):
        s.state = "degraded"
    assert s.state is UplinkState.DEGRADED
    with pytest.raises(ValueError, match="not one of"):
        s.state = "flapping"
    assert s.state is UplinkState.DEGRADED
    s2 = dataclasses.replace(s, state=UplinkState.UP)
    assert s2.state is UplinkState.UP


def test_link_status_unknown_word_raises() -> None:
    with pytest.raises(ValueError, match=r"LinkStatus\.state"):
        LinkStatus("wan1", "flapping", "")


@pytest.mark.parametrize("word", ["up", "down", "degraded", "unknown"])
def test_link_health_state_converts(word: str) -> None:
    with pytest.warns(DeprecationWarning, match=r"LinkHealthReport.state: plain string"):
        r = _health(word)
    assert r.state is UplinkState(word)
    assert r.state == word


def test_link_health_member_silent_and_unknown_word_raises() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _health(UplinkState.UNKNOWN).state is UplinkState.UNKNOWN
    with pytest.raises(ValueError, match=r"LinkHealthReport\.state"):
        _health("healthy")


def test_link_health_assignment_converts() -> None:
    r = _health(UplinkState.UP)
    with pytest.warns(DeprecationWarning):
        r.state = "down"
    assert r.state is UplinkState.DOWN


# --- M16: AppFlow category (open) ---


def _flow(category: ApplicationCategory | str, category_raw: str | None = None) -> AppFlow:
    return AppFlow(
        application="x",
        category=category,
        src_ip="10.0.0.1",
        dst_ip="198.51.100.1",
        wan_interface="wan1",
        bytes_sent=1,
        bytes_received=2,
        category_raw=category_raw,
    )


def test_flow_member_is_silent_with_no_raw_word() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        f = _flow(ApplicationCategory.GAMING)
    assert (f.category, f.category_raw) == (ApplicationCategory.GAMING, None)


def test_flow_named_string_converts_with_a_warning() -> None:
    with pytest.warns(DeprecationWarning, match=r"AppFlow.category: plain string"):
        f = _flow("video_streaming")
    assert f.category is ApplicationCategory.VIDEO_STREAMING
    assert f.category_raw is None


def test_flow_unknown_word_is_other_with_the_raw_word_and_no_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        f = _flow("Streaming Video/HD")
    assert f.category is ApplicationCategory.OTHER
    assert f.category_raw == "Streaming Video/HD"
    assert _flow("").category_raw == ""


def test_flow_replace_and_assignment_side_that_changed_wins() -> None:
    f = _flow("odd-word")
    g = dataclasses.replace(f, category=ApplicationCategory.EMAIL)
    assert (g.category, g.category_raw) == (ApplicationCategory.EMAIL, None)
    h = dataclasses.replace(f, category_raw="another")
    assert (h.category, h.category_raw) == (ApplicationCategory.OTHER, "another")
    f.category = "word-two"
    assert (f.category, f.category_raw) == (ApplicationCategory.OTHER, "word-two")
    f.category = ApplicationCategory.NEWS
    assert f.category_raw is None


def test_flow_raw_word_beside_a_named_category_raises() -> None:
    with pytest.raises(ValueError, match="category_raw"):
        _flow(ApplicationCategory.EMAIL, category_raw="x")


def test_flow_wrong_type_raises() -> None:
    with pytest.raises(TypeError):
        _flow(5)  # type: ignore[arg-type]


def test_other_is_not_a_matchable_category() -> None:
    from testprotocols.models import CategoryMatch, L7MatchType, traffic_match

    assert ApplicationCategory.OTHER.value == "other"
    with pytest.raises(ValueError, match="other"):
        CategoryMatch(ApplicationCategory.OTHER)
    with pytest.raises(ValueError):
        traffic_match(L7MatchType.APPLICATION_CATEGORY, "other")


# --- M17 / M18: orphan models deprecated ---


@pytest.mark.parametrize("name", ["VPNPeerStatus", "TrafficShapingRule"])
@pytest.mark.parametrize("module", ["testprotocols.models.wan_edge", "testprotocols.models"])
def test_orphan_models_warn_on_access_and_still_work(module: str, name: str) -> None:
    mod = importlib.import_module(module)
    with pytest.warns(DeprecationWarning, match=rf"{module}.{name} is deprecated; "):
        cls = getattr(mod, name)
    assert cls.__name__ == name
    if name == "VPNPeerStatus":
        v = cls(peer_id="1", peer_name="a", reachability="up", uplink="wan1")
        assert v.peer_name == "a"
    else:
        r = cls(name="n", match={"dst_prefix": "10.0.0.0/8"}, dscp_tag=46)
        assert r.dscp_tag == 46


def test_orphans_are_not_star_exported_and_unknown_names_still_fail() -> None:
    import testprotocols.models as models

    assert "VPNPeerStatus" not in models.__all__
    assert "TrafficShapingRule" not in models.__all__
    with pytest.raises(AttributeError):
        models.NoSuchModel
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        namespace: dict[str, object] = {}
        exec("from testprotocols.models import *", namespace)
