"""Firewall / Conntrack template.

Defines the abstract contract for inspecting and administering
connection-tracking state on a stateful device. Read-mostly; the only
write operations are explicit flushes (test-scenario reset), per-flow
drop, and table-size limit configuration.

In scope: aggregate stats, per-flow listing / lookup / drop, full-table
flush, table-size limit configuration.

Out of scope: rule installation (see ``packet_filter`` / ``firewall``
and ``nat``), helper-module loading (driver-internal concern), and
per-flow accounting deltas over time (operations layer can subtract
two snapshots).

Devices that do not track connections (e.g. stateless bridges) should
not compose this template.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.firewall import Connection, ConntrackStats


@runtime_checkable
class Conntrack(Protocol):
    """Abstract contract for connection-tracking observability and admin."""

    # --- Aggregate stats ---

    def get_stats(self) -> ConntrackStats:
        """Return current conntrack table aggregate counters."""
        ...

    # --- Per-flow inspection ---

    def list_connections(
        self,
        *,
        protocol: str | None = None,
        src_ip: str | None = None,
        dst_ip: str | None = None,
        dst_port: int | None = None,
        state: str | None = None,
    ) -> list[Connection]:
        """Return tracked flows, optionally filtered.

        Filters compose with AND. *protocol*, when set, must be one of
        ``"tcp"``, ``"udp"``, ``"icmp"`` — raises ValueError otherwise.
        Empty list when no flow matches.
        """
        ...

    def count_connections(
        self,
        *,
        protocol: str | None = None,
        state: str | None = None,
    ) -> int:
        """Return the number of tracked flows matching the optional filters.

        *protocol*, when set, must be one of ``"tcp"``, ``"udp"``,
        ``"icmp"`` — raises ValueError otherwise. Cheaper than
        ``len(list_connections(...))`` on drivers that can ask the
        kernel directly.
        """
        ...

    def get_connection(
        self,
        protocol: str,
        src_ip: str,
        dst_ip: str,
        src_port: int | None,
        dst_port: int | None,
    ) -> Connection:
        """Return the tracked flow exactly matching the supplied 5-tuple.

        *src_port* / *dst_port* are ``None`` for ICMP.

        Raises KeyError if no flow matches.
        """
        ...

    # --- Per-flow administration ---

    def drop_connection(
        self,
        protocol: str,
        src_ip: str,
        dst_ip: str,
        src_port: int | None,
        dst_port: int | None,
    ) -> None:
        """Drop the tracked flow exactly matching the supplied 5-tuple.

        *src_port* / *dst_port* are ``None`` for ICMP.

        Raises KeyError if no flow matches.
        """
        ...

    def flush_connections(self) -> None:
        """Remove every tracked flow from the conntrack table."""
        ...

    # --- Table size limit ---

    def set_max_connections(self, max_connections: int) -> None:
        """Set the conntrack table size limit.

        Raises ValueError if *max_connections* < 1.
        Drivers that do not expose a configurable limit raise
        NotImplementedError.
        """
        ...

    def get_max_connections(self) -> int:
        """Return the current conntrack table size limit."""
        ...


@runtime_checkable
class ConntrackWhiteBox(Conntrack, Protocol):
    """White-box extension of Conntrack for raw kernel-table introspection.

    Linux drivers that can shell into the box satisfy this extension by
    capturing ``conntrack -L`` (the netfilter conntrack utility) output.
    Vendor-RTOS or locked-down devices typically satisfy only the base
    ``Conntrack`` Protocol; tests requiring raw connection-tuple
    verification should pin against ``ConntrackWhiteBox`` and accept
    the collection-skip on drivers that don't satisfy it (per the
    ``@white_box`` scenario tag rule).
    """

    def get_raw_conntrack_dump(self) -> str:
        """Return the raw ``conntrack -L`` output for the current namespace.

        Format is the standard ``conntrack -L`` serialisation (one line per
        flow, with proto / src / dst / sport / dport / state / mark fields).
        Tests parse this to verify flow tuples landed at the kernel level
        rather than only in the driver's intermediate state — useful for
        debugging NAT-translation discrepancies and stuck-flow diagnostics.
        """
        ...
