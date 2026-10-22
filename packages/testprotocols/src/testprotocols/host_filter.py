"""Host filtering — a per-host block of traffic through the gateway, on a schedule.

A host block denies a host's traffic through the gateway, wired or wireless,
at all times or on a weekly schedule. It is keyed by MAC because that is what
every family keys on. It is not a ``packet_filter`` rule (``FirewallRule``
carries no schedule) and not ``wifi_bss``'s per-network access list (which
admits or refuses a station's association on one network). The block has one
owner: on a family that realises it as a firewall rule, the ``firewall`` driver
refuses ``remove_rule`` on that rule, and ``flush_chain`` and
``set_default_policy`` on the chain that holds it, with ``NotSupportedError``
naming ``host_filter``.

In scope: block, unblock, read one block, list blocks.

Out of scope: the hosts themselves (see ``host_table``), per-network
association control (see ``wifi_bss``), general packet filtering (see
``firewall``, ``packet_filter``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.cpe_gateway import HostBlock


@runtime_checkable
class HostFilter(Protocol):
    """Abstract contract for the gateway's per-host block."""

    def block_host(self, block: HostBlock) -> None:
        """Write the host *block*; paired read ``get_host_block``.

        ``HostBlock.mac`` accepts any case and is normalised to the canonical lowercase
        colon-separated form before the device sees it, so the paired read returns what was
        written. A ``WeeklySchedule`` whose ``end`` is before its ``start`` runs past midnight;
        ``None`` blocks at all times. On a family that realises the block as a firewall rule,
        the rule appears in ``firewall.list_rules`` too, named after the host.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found block list where the family commits atomically, otherwise
        the steps applied before the rejection.
        """
        ...

    def unblock_host(self, mac: str) -> None:
        """Remove the block on *mac* (any case accepted); paired read ``list_host_blocks``.

        Raises ``KeyError`` if no block on that address exists.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found block list where the family commits atomically, otherwise
        the steps applied before the rejection.
        """
        ...

    def get_host_block(self, mac: str) -> HostBlock:
        """Return the block on *mac* (any case accepted), its ``mac`` canonical.

        Raises ``KeyError`` if no block on that address exists.
        """
        ...

    def list_host_blocks(self) -> list[HostBlock]:
        """Return every host block, every ``mac`` canonical."""
        ...
