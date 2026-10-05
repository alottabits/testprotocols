"""WAN-edge models typed: link states (an enum or its word), the AppFlow category, orphans
deprecated."""

from __future__ import annotations

import dataclasses
import importlib
import warnings
from pathlib import Path

import pytest
from testprotocols.models import (
    AppFlow,
    ApplicationCategory,
    LinkHealthReport,
    LinkStatus,
    UplinkState,
)

# --- link states ---


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
def test_link_status_released_words_are_stored_as_given(word: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        s = LinkStatus(name="wan1", state=word, ip_address="198.51.100.2")
    assert type(s.state) is str
    assert s.state == UplinkState(word)


def test_link_status_member_is_silent() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        s = LinkStatus("wan1", UplinkState.DOWN, "")
    assert s.state is UplinkState.DOWN
    assert dataclasses.replace(s, state=UplinkState.UP).state is UplinkState.UP


@pytest.mark.parametrize("word", ["up", "down", "degraded", "unknown"])
def test_link_health_state_is_stored_as_given(word: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        r = _health(word)
        member = _health(UplinkState(word))
    assert r.state == member.state == UplinkState(word)
    assert type(r.state) is str


# --- AppFlow category (the product's own word) ---


def _flow(category: str) -> AppFlow:
    return AppFlow(
        application="x",
        category=category,
        src_ip="10.0.0.1",
        dst_ip="198.51.100.1",
        wan_interface="wan1",
        bytes_sent=1,
        bytes_received=2,
    )


def test_flow_category_is_stored_as_given() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for word in ("gaming", "Streaming Video/HD", "other", ""):
            f = _flow(word)
            assert f.category == word and type(f.category) is str
    f = _flow("odd-word")
    assert dataclasses.replace(f, category="word-two").category == "word-two"
    f.category = "word-three"
    assert f.category == "word-three"


def test_other_is_not_a_category() -> None:
    assert "other" not in {m.value for m in ApplicationCategory}
    with pytest.raises(ValueError):
        ApplicationCategory("other")


# --- orphan models deprecated ---


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
    name = "NoSuchModel"
    with pytest.raises(AttributeError):
        getattr(models, name)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        namespace: dict[str, object] = {}
        exec("from testprotocols.models import *", namespace)


# --- the deprecation __getattr__ must not make unknown names type-check ---


def test_an_unknown_name_is_a_static_error_but_the_deprecated_ones_are_not(
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    probe = tmp_path / "probe.py"
    probe.write_text(
        "from testprotocols.models import NoSuchModel\n"
        "from testprotocols.models.wan_edge import NoSuchEdgeModel\n"
        "from testprotocols.models import TrafficShapingRule, VPNPeerStatus\n"
        "from testprotocols.models.wan_edge import TrafficShapingRule as T2, VPNPeerStatus as V2\n"
    )
    done = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-incremental", str(probe)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        check=False,
    )
    lines = done.stdout.splitlines()
    assert any("probe.py:1" in line and "NoSuchModel" in line for line in lines), done.stdout
    assert any("probe.py:2" in line and "NoSuchEdgeModel" in line for line in lines), done.stdout
    assert not any("probe.py:3" in line or "probe.py:4" in line for line in lines), done.stdout
