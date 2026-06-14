"""Unified L2 + L3/L4 switch ACL — one ordered rule set per binding + direction.

The reviewed switches use one ACL engine matching MAC/VLAN and IP 5-tuple
fields, so this is one capability (not separate L2/L3 protocols). Rules reuse
``RuleAction`` / ``RuleProtocol``; the record is ``SwitchAclRule``. Bindings are
by port or VLAN, ingress or egress, applied as an ordered whole-list replace.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.switch import AclDirection, SwitchAclRule


@runtime_checkable
class SwitchAcl(Protocol):
    """Abstract contract for the switch ACL."""

    def set_acl(
        self, binding: str, direction: AclDirection, rules: list[SwitchAclRule]
    ) -> None:
        """Replace the ordered ACL bound to *binding* (a port or ``vlan:<id>``)
        in *direction*."""
        ...

    def get_acl(self, binding: str, direction: AclDirection) -> list[SwitchAclRule]:
        """Return the ordered ACL for *binding* / *direction*."""
        ...
