"""Archetype-purity drift gate.

Device archetypes must compose capability protocols only; the sole sanctioned
exception is the BaseDeviceProtocol identity pair. Enforced twice: here (the
merge gate — parametrized over the registry, so every future archetype is
covered the moment it is registered) and in register_device_type itself (the
import-time gate that also covers plugin-local archetypes downstream). See
docs/architecture/capability-only-archetypes.md.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pytest
from testprotocols.devices import (
    DeviceTypeSpec,
    all_device_types,
    get_device_type,
    non_capability_members,
    register_device_type,
)
from testprotocols.devices.base import BaseDeviceProtocol


@pytest.mark.parametrize(
    ("name", "spec"),
    sorted(all_device_types().items()),
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_archetype_members_are_capability_protocols(name: str, spec: DeviceTypeSpec) -> None:
    offenders = non_capability_members(spec.protocol)
    assert not offenders, (
        f"{name}: non-capability members {sorted(offenders)} — archetypes compose "
        "capability protocols only (docs/architecture/capability-only-archetypes.md)"
    )


def test_checker_detects_scalar_members() -> None:
    """The checker flags annotated scalars AND property-declared scalars."""

    @runtime_checkable
    class _Rogue(BaseDeviceProtocol, Protocol):
        rogue_scalar: str

        @property
        def rogue_property(self) -> int: ...

    assert non_capability_members(_Rogue) == {"rogue_scalar", "rogue_property"}


def test_register_rejects_non_capability_archetype() -> None:
    @runtime_checkable
    class _Rogue(BaseDeviceProtocol, Protocol):
        rogue_scalar: str

    with pytest.raises(TypeError, match="rogue_scalar"):
        register_device_type("_rogue_purity_probe", _Rogue)
    assert get_device_type("_rogue_purity_probe") is None, "must not register on failure"
