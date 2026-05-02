"""Tests for the RADIUS-domain Protocol shapes.

Covers: RadiusClient, RadiusServer.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "RadiusClient",
        "testprotocols.radius_client",
        {
            "add_server",
            "update_server",
            "remove_server",
            "list_servers",
            "get_server",
            "test_server_reachable",
        },
    ),
    (
        "RadiusServer",
        "testprotocols.radius_server",
        {
            # Lifecycle
            "start",
            "stop",
            "get_status",
            # User provisioning
            "add_user",
            "remove_user",
            "list_users",
            "get_user",
            # Active sessions
            "get_active_sessions",
            # Dynamic authorization (RFC 5176)
            "send_coa",
            "send_disconnect",
            # Accounting
            "get_accounting_records",
            "clear_accounting",
        },
    ),
]


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_is_runtime_checkable(class_name: str, module: str, expected_methods: set[str]) -> None:
    cls = getattr(importlib.import_module(module), class_name)
    assert getattr(cls, "_is_runtime_protocol", False), (
        f"{class_name} is not a @runtime_checkable Protocol"
    )


@pytest.mark.parametrize(("class_name", "module", "expected_methods"), PROTOCOLS)
def test_protocol_shape(class_name: str, module: str, expected_methods: set[str]) -> None:
    cls = getattr(importlib.import_module(module), class_name)
    actual = set(cls.__protocol_attrs__)
    assert expected_methods <= actual, f"{class_name} missing: {expected_methods - actual}"
