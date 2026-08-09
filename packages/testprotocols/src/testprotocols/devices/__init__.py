"""Device archetype registry — maps inventory device_type strings to Protocols."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, cast, get_type_hints

_registry: dict[str, DeviceTypeSpec] = {}

#: The sole sanctioned non-capability members — BaseDeviceProtocol's universal
#: identity pair (see devices/base.py).
IDENTITY_MEMBERS = frozenset({"device_name", "device_type"})


def non_capability_members(protocol: type) -> frozenset[str]:
    """Members of *protocol* that are neither capability Protocols nor identity.

    A capability member is annotated with a ``typing.Protocol`` class. Scalar
    annotations (``str``, ``bool``, ``tuple``…) and property-declared members
    (which carry no annotation at all) are both offenders. ``__protocol_attrs__``
    is the CPython 3.12 runtime detail ``typing.get_protocol_members``
    supersedes in 3.13; one cast keeps that knowledge here.
    """
    hints = get_type_hints(protocol)
    members: frozenset[str] = frozenset(cast("Any", protocol).__protocol_attrs__)
    return frozenset(
        member
        for member in members - IDENTITY_MEMBERS
        if not getattr(hints.get(member), "_is_protocol", False)
    )


@dataclass(frozen=True)
class DeviceTypeSpec:
    """Registration record: inventory string -> @runtime_checkable Protocol class."""

    name: str
    protocol: type


def register_device_type(name: str, protocol: type) -> DeviceTypeSpec:
    """Register *protocol* as the contract for inventory devices typed *name*.

    Fails closed on archetype drift: every member must be a capability
    Protocol (the BaseDeviceProtocol identity pair excepted) — see
    docs/architecture/capability-only-archetypes.md. Returns the spec; also
    stored in the module-level registry so ``get_device_type(name)`` can look
    it up by inventory string.
    """
    offenders = non_capability_members(protocol)
    if offenders:
        raise TypeError(
            f"device archetype {protocol.__name__!r} ({name!r}) declares "
            f"non-capability members {sorted(offenders)}; archetypes compose "
            "capability protocols only — move these into a capability protocol "
            "(docs/architecture/capability-only-archetypes.md)"
        )
    spec = DeviceTypeSpec(name=name, protocol=protocol)
    _registry[name] = spec
    return spec


def get_device_type(name: str) -> DeviceTypeSpec | None:
    """Return the spec for inventory *name*, or None if not registered."""
    return _registry.get(name)


def all_device_types() -> dict[str, DeviceTypeSpec]:
    """Return a copy of the full registry."""
    return dict(_registry)


# Auto-import all archetype modules to trigger registration as a side effect.
# ``importlib.import_module`` avoids the unused-import / out-of-order-import
# friction that direct ``from … import …`` statements would create here, and
# keeps the import section at the top of the file as PEP 8 prefers.
for _mod in ("client", "cpe", "infra", "sdwan", "switch", "traffic", "voice", "wan"):
    importlib.import_module(f"testprotocols.devices.{_mod}")
del _mod
