"""Client-placement templates — both halves of the placement mechanism.

A *placement pipe* is a client's dedicated access port on a managed switch:
re-VLANing that port is the client's placement knob. The mechanism has two
sides owned by two devices: the **client** declares which switch/port carries
its pipe (``PlacementPipe`` — topology fact), and the **switch** declares
which ports a testbed may re-VLAN at all (``PlacementPorts`` — write
authorization, owned by the resource's owner). Pipe ownership and write
authorization are deliberately independent declarations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PlacementPipe(Protocol):
    """Abstract contract for a client's declared placement pipe."""

    @property
    def switch(self) -> str:
        """Name of the switch carrying this client's dedicated access port,
        empty when the client has no declared pipe."""
        ...

    @property
    def port(self) -> str:
        """The dedicated access port whose VLAN is this client's placement
        knob, empty when the client has no declared pipe."""
        ...


@runtime_checkable
class PlacementPorts(Protocol):
    """Abstract contract for a switch's placement-write authorization."""

    @property
    def ports(self) -> tuple[str, ...]:
        """Designated ports a testbed may re-VLAN to place a client; empty
        means no placement write is permitted on this switch. Independent of
        which device's pipe enters a port: pipe ownership is topology, this is
        write authorization — declared by the switch, the resource's owner."""
        ...
