"""Switch QoS — classification rules, DSCP->CoS map, and trust mode."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import QosRule, QosTrustMode


@runtime_checkable
class SwitchQos(Protocol):
    """Abstract contract for switch QoS.

    Explicit queue-scheduler / per-port rate-limit tuning is out of scope
    (deferred); a product with limited scheduler control normalizes to
    rules + trust/map.
    """

    def set_trust_mode(self, port: str, mode: QosTrustMode) -> None:
        """Set the QoS trust mode on *port*."""
        ...

    def set_dscp_cos_map(self, mapping: dict[int, int]) -> None:
        """Replace the DSCP->CoS map.

        A write rejected at any step raises naming the step; the driver puts
        nothing back. The state is then the as-found DSCP->CoS map where the
        family commits atomically, otherwise the steps applied before the
        rejection.
        """
        ...

    def set_rules(self, rules: list[QosRule]) -> None:
        """Replace the ordered QoS classification rule list.

        A write rejected at any step raises naming the step; the driver puts
        nothing back. The state is then the as-found rule list where the family
        commits atomically, otherwise the steps applied before the rejection.
        """
        ...

    def get_rules(self) -> list[QosRule]:
        """Return the QoS classification rules."""
        ...
