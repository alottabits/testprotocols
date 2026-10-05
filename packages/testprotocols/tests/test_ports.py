"""PortRange: the typed form of the released port text."""

from __future__ import annotations

from testprotocols.models import PortRange


def test_port_range_shape() -> None:
    assert PortRange.single(80) == PortRange(80, 80)
    assert str(PortRange.single(80)) == "80" and str(PortRange(80, 90)) == "80-90"
