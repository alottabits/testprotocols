"""Tests for capture / file-transfer / TFTP / PDU / AFTR / streaming-origin Protocol shapes.

Covers: PcapCapture, FileTransfer, TftpServer, PduController, AftrGateway,
StreamingServer.
"""

from __future__ import annotations

import importlib

import pytest

PROTOCOLS = [
    (
        "PcapCapture",
        "testprotocols.pcap_capture",
        {"start_tcpdump", "stop_tcpdump", "tshark_read_pcap"},
    ),
    (
        "FileTransfer",
        "testprotocols.file_transfer",
        {"delete_file", "scp_device_file_to_local"},
    ),
    (
        "TftpServer",
        "testprotocols.tftp_server",
        {"download_image_from_uri", "restart_lighttpd"},
    ),
    (
        "PduController",
        "testprotocols.pdu_controller",
        {"power_on", "power_off", "power_cycle"},
    ),
    (
        "AftrGateway",
        "testprotocols.aftr_gateway",
        {"configure_aftr", "restart_aftr_process"},
    ),
    (
        "StreamingServer",
        "testprotocols.streaming_server",
        {"ensure_content_available"},
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
