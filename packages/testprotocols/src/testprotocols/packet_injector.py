"""Packet-injector template — put caller-supplied bytes on the wire.

Defines the abstract contract for a testbed instrument that emits traffic to
exercise an inspecting device: crafting and sending a caller-supplied payload, or
replaying a caller-supplied capture, onto a test interface.

A host/substrate instrument, distinct in class from the device-under-test
``threat_prevention.ThreatPrevention`` subsystem. Scanning lives on
``nmap_scanner.NmapScanner`` and attacker-originated HTTP on
``http_client.HttpClient``; packet *capture* is ``pcap_capture.PcapCapture``
(read-only). This capability is only emission, which has no other home.

Scope is exactly "emit caller-supplied bytes / replay a caller-supplied capture."
Selecting named strikes from a vendor catalogue is a different contract shape and
is out of scope (see the packet-injection substrate design record). ``replay``
guarantees the packets were emitted, not a bit- or timing-exact reproduction.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.emission import EmitResult, ReplayResult
from testprotocols.models.sdwan_appliance import RuleProtocol


@runtime_checkable
class PacketInjector(Protocol):
    """Abstract contract for packet emission / replay onto a test interface."""

    def emit_signature(
        self,
        payload: bytes,
        target: str,
        *,
        port: int,
        protocol: RuleProtocol = RuleProtocol.TCP,
    ) -> EmitResult:
        """Craft and send *payload* to *target*:*port* over *protocol*.

        The payload is the caller's data — the contract carries no notion of
        which detection rule it is meant to match.
        """
        ...

    def replay_pcap(self, pcap_path: str, *, iface: str | None = None) -> ReplayResult:
        """Replay the capture at *pcap_path* onto the test interface.

        Guarantees that the packets were emitted, not a bit- or timing-exact
        reproduction of the original capture.
        """
        ...
