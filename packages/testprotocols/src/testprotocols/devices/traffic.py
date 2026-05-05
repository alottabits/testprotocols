"""Traffic device archetypes — impairment injection and load generation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.devices import register_device_type
from testprotocols.devices.base import BaseDeviceProtocol
from testprotocols.ip_interface import IpInterface
from testprotocols.iperf_generator import IperfGenerator
from testprotocols.netem_controller import NetemController


@runtime_checkable
class TrafficControllerDevice(BaseDeviceProtocol, Protocol):
    """Traffic controller archetype — inline impairment injector.

    Sits in the data path to apply latency, loss, jitter, and rate-limit
    impairments via netem. Also exposes IP interface management for placement
    on the test topology.
    """

    netem: NetemController
    ip_interface: IpInterface


@runtime_checkable
class IperfTrafficGeneratorDevice(BaseDeviceProtocol, Protocol):
    """Iperf traffic generator archetype — multi-flow load source.

    Drives concurrent iperf flows (UDP / TCP, configurable rate / count) to
    saturate or stress a path under test. IP interface management for
    placement on the test topology.
    """

    iperf_generator: IperfGenerator
    ip_interface: IpInterface


register_device_type("linux_traffic_controller", TrafficControllerDevice)
register_device_type("iperf_traffic_generator", IperfTrafficGeneratorDevice)
