"""USP agent — the gateway's User Services Platform agent (the ``usp`` tier).

The agent connects to a controller over a message transport and exposes the
device's data model to it. This capability is the agent's controller
configuration and its connection state. TR-069 is the other management
protocol and stays on ``tr069_client``.

In scope: the controller endpoint and transport (write, read), the agent's own
state.

Out of scope: the CWMP client (see ``tr069_client``), the controller itself
(a test-bed role), the data model the agent exposes.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.cpe_gateway import UspAgentState, UspController


@runtime_checkable
class UspAgent(Protocol):
    """Abstract contract for the gateway's USP agent."""

    def set_controller(self, controller: UspController) -> None:
        """Write the agent's *controller*; paired read ``get_controller``, and
        ``get_agent_state`` for the effect.

        ``UspController.path`` is the WebSocket resource path and ``None`` on the other
        transports. A family that configures the agent through its own files writes them and
        restarts the agent: the two steps are named.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found controller configuration where the family commits
        atomically, otherwise the steps applied before the rejection.
        """
        ...

    def get_controller(self) -> UspController:
        """Return the agent's controller configuration."""
        ...

    def get_agent_state(self) -> UspAgentState:
        """Return the agent's own endpoint identifier and connection state; ``connected`` is
        ``None`` where the family publishes the configuration but no connection state."""
        ...
