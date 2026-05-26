"""Firewall operations — multi-step coordination over the ``Firewall`` protocol.

Receives a resolved ``firewall`` template instance from the caller.
"""

from __future__ import annotations

from testprotocols.firewall import Firewall


def reset_to_factory_default(firewall: Firewall) -> None:
    """Remove every operator-added port mapping currently known to *firewall*.

    Iterates ``list_port_mappings()`` and calls ``remove_port_mapping(name)``
    for each entry. Used as a "Given the firewall is in its factory-default
    state" precondition: scenarios that mutate firewall rules register their
    own per-rule teardown; this operation defensively clears any port-mapping
    leftover from a previous run.

    PacketFilter chain rules are deliberately left alone — wholesale flush
    would also remove the baseline OpenWrt allow rules that ship with the
    factory image.
    """
    for mapping in firewall.list_port_mappings():
        firewall.remove_port_mapping(mapping.name)
