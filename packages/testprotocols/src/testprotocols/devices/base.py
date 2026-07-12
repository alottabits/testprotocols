"""Universal base Protocol shared by every device archetype."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class BaseDeviceProtocol(Protocol):
    """Universal identity surface every test-device archetype carries.

    Substrate- and framework-neutral: any concrete driver that exposes a
    ``device_name`` and a ``device_type`` satisfies this — vitro's
    ``VitroDevice`` (where both are ``@property``), a hypothetical
    boardfarm ``BoardfarmDevice``, a pyATS ``Device`` wrapper, a
    pure-Python simulator. Archetype Protocols in
    ``testprotocols.devices.*`` inherit from this so consumers
    (operations, step defs) can read identity for log / assertion
    messages without reaching into framework-specific base classes.

    Deliberately scoped to the universal pair — name + type. Anything a
    specific framework wants to expose (vitro's ``config`` /
    ``get_interactive_consoles``, boardfarm's lifecycle hooks, etc.) is
    the framework's own concern. Frameworks declare a connector Protocol
    on their side that extends this base; testbed plugins compose
    archetype + framework-connector into a combined Protocol where step
    defs need both.
    """

    # Read-only identity. Declared as properties (not settable variables) so that
    # implementers exposing them as ``@property`` (e.g. vitro's
    # VitroDevice) statically satisfy the Protocol — a settable-variable member
    # would reject a read-only property. A plain ``device_name: str`` attribute
    # also satisfies a read-only-property member, so this is the more permissive,
    # correct declaration for read-only identity.
    @property
    def device_name(self) -> str: ...

    @property
    def device_type(self) -> str: ...
