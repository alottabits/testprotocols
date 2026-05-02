"""Tests for testoperations.http_server module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from testoperations.http_server import start_http_server

# ---------------------------------------------------------------------------
# start_http_server (context manager)
# ---------------------------------------------------------------------------


class TestStartHttpServer:
    def test_starts_and_stops_service(self):
        srv = MagicMock()
        srv.start_http_service.return_value = "pid123"

        with start_http_server(srv, port="8080") as pid:
            assert pid == "pid123"
            srv.start_http_service.assert_called_once_with("8080", "ipv4")

        srv.stop_http_service.assert_called_once_with("8080")

    def test_stops_on_exception(self):
        srv = MagicMock()
        srv.start_http_service.return_value = "pid456"

        with pytest.raises(ValueError):
            with start_http_server(srv, port="9090", ip_version="ipv6"):
                raise ValueError("test error")

        srv.stop_http_service.assert_called_once_with("9090")

    def test_passes_ip_version(self):
        srv = MagicMock()
        with start_http_server(srv, port="80", ip_version="ipv6"):
            srv.start_http_service.assert_called_once_with("80", "ipv6")
