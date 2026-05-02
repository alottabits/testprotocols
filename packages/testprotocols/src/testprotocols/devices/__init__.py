"""Device archetype registry — maps inventory device_type strings to Protocols."""

from __future__ import annotations

import importlib
from dataclasses import dataclass

_registry: dict[str, DeviceTypeSpec] = {}


@dataclass(frozen=True)
class DeviceTypeSpec:
    """Registration record: inventory string -> @runtime_checkable Protocol class."""

    name: str
    protocol: type


def device_type(name: str, protocol: type) -> DeviceTypeSpec:
    """Register *protocol* as the contract for inventory devices typed *name*.

    Returns the spec; also stored in the module-level registry so
    ``get_device_type(name)`` can look it up by inventory string.
    """
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
for _mod in ("client", "cpe", "infra", "sdwan", "traffic", "voice", "wan"):
    importlib.import_module(f"testprotocols.devices.{_mod}")
del _mod
