"""Tests for testoperations.firewall module."""

from __future__ import annotations

from unittest.mock import MagicMock, call

from testoperations.firewall import reset_to_factory_default
from testprotocols.models.firewall import PortMapping


def _mapping(name: str) -> PortMapping:
    return PortMapping(
        name=name,
        external_port=80,
        protocol="tcp",
        internal_host="10.0.0.2",
        internal_port=80,
    )


class TestResetToFactoryDefault:
    def test_removes_every_listed_port_mapping(self):
        firewall = MagicMock()
        firewall.list_port_mappings.return_value = [
            _mapping("lan_http"),
            _mapping("nas_web"),
        ]

        reset_to_factory_default(firewall)

        firewall.list_port_mappings.assert_called_once_with()
        assert firewall.remove_port_mapping.call_args_list == [
            call("lan_http"),
            call("nas_web"),
        ]

    def test_no_op_when_no_port_mappings(self):
        firewall = MagicMock()
        firewall.list_port_mappings.return_value = []

        reset_to_factory_default(firewall)

        firewall.list_port_mappings.assert_called_once_with()
        firewall.remove_port_mapping.assert_not_called()

    def test_does_not_touch_packet_filter_chains(self):
        firewall = MagicMock()
        firewall.list_port_mappings.return_value = []

        reset_to_factory_default(firewall)

        firewall.flush_chain.assert_not_called()
        firewall.remove_rule.assert_not_called()

    def test_propagates_remove_failures(self):
        firewall = MagicMock()
        firewall.list_port_mappings.return_value = [_mapping("lan_http")]
        firewall.remove_port_mapping.side_effect = RuntimeError("UCI commit failed")

        try:
            reset_to_factory_default(firewall)
        except RuntimeError as exc:
            assert "UCI commit failed" in str(exc)
        else:
            raise AssertionError("RuntimeError was swallowed")
