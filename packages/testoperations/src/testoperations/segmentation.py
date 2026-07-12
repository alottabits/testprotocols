"""Spoke-to-spoke segmentation operations — role selection + VPN-firewall deny.

Pure, assertion-free helpers for a spoke-to-spoke segmentation test:

* :func:`select_roles` resolves the three roles the test needs — a *source*
  spoke of a requested MX model, and a *destination* and *control* drawn
  **deterministically** from the remaining spokes in the same AutoVPN domain
  (so all three share a hub and can peer). Nothing is tied to a specific spoke;
  the caller builds the candidate list from discovery and acts on the result.
* :func:`build_deny_rule` constructs the directional VPN-firewall ``L3Rule`` for
  a given rule *shape* (host ``/32`` vs subnet scope, and protocol).
* :func:`find_matching_deny` locates that deny in an effective policy read-back.

The module imports only testprotocols models — no devices, no vendor SDKs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from testprotocols.models import L3Rule, RuleAction, RuleProtocol


@dataclass(frozen=True)
class SpokeCandidate:
    """A spoke eligible to play a role in the test.

    *name* is the spoke's network identity, *mx_model* the MX behind it (joined
    from inventory), *hub* the AutoVPN hub it homes to (the **domain key** — two
    spokes can peer only if they share a hub), and *subnet* its advertised VPN
    subnet.
    """

    name: str
    mx_model: str
    hub: str
    subnet: str


@dataclass(frozen=True)
class RoleAssignment:
    """The resolved source / destination / control spokes for one scenario."""

    source: SpokeCandidate
    destination: SpokeCandidate
    control: SpokeCandidate


class NoEligibleSelectionError(Exception):
    """The discovered topology cannot satisfy the requested role selection."""


def select_roles(candidates: Sequence[SpokeCandidate], source_mx_model: str) -> RoleAssignment:
    """Resolve (source, destination, control) over *candidates*.

    The source is the first spoke (ordered by name, for determinism) whose
    ``mx_model`` equals *source_mx_model*; the destination and control are the
    next two spokes (by name) sharing the source's hub. Raises
    :class:`NoEligibleSelectionError` when no spoke of the model exists, or when
    fewer than two further same-domain spokes are available.
    """
    ordered = sorted(candidates, key=lambda c: c.name)

    source = next((c for c in ordered if c.mx_model == source_mx_model), None)
    if source is None:
        available = sorted({c.mx_model for c in ordered})
        raise NoEligibleSelectionError(
            f"no spoke with MX model {source_mx_model!r}; available models: {available}"
        )

    peers = [c for c in ordered if c is not source and c.hub == source.hub]
    if len(peers) < 2:
        raise NoEligibleSelectionError(
            f"need 2 further reachable spokes sharing hub {source.hub!r} for the "
            f"destination and control roles, found {len(peers)}: "
            f"{[p.name for p in peers]}"
        )

    return RoleAssignment(source=source, destination=peers[0], control=peers[1])


def build_deny_rule(
    *,
    scope: str,
    proto: str,
    source_subnet: str,
    source_host: str,
    dest_subnet: str,
    dest_host: str,
    comment: str = "",
    syslog_enabled: bool = True,
) -> L3Rule:
    """Build the directional source->destination deny rule for a rule shape.

    *scope* selects the match width: ``"host"`` denies a single ``/32`` host
    pair (built from *source_host* / *dest_host*); ``"subnet"`` denies the whole
    *source_subnet* -> *dest_subnet*. *proto* is a ``RuleProtocol`` value
    (``"icmp"`` / ``"tcp"`` / ``"udp"`` / ``"any"``). ``syslog_enabled`` defaults
    on so the denial is auditable (Success Guarantee 2).
    """
    if scope == "host":
        src_cidr, dst_cidr = f"{source_host}/32", f"{dest_host}/32"
    elif scope == "subnet":
        src_cidr, dst_cidr = source_subnet, dest_subnet
    else:
        raise ValueError(f"unknown rule scope {scope!r} (expected 'host' or 'subnet')")

    return L3Rule(
        action=RuleAction.DENY,
        protocol=RuleProtocol(proto),
        src_cidr=src_cidr,
        dst_cidr=dst_cidr,
        comment=comment,
        syslog_enabled=syslog_enabled,
    )


def find_matching_deny(
    rules: Sequence[L3Rule], *, protocol: RuleProtocol, src_cidr: str, dst_cidr: str
) -> L3Rule | None:
    """Return the active DENY rule matching protocol + src/dst CIDR, or ``None``.

    Used to confirm an applied deny is present in an effective-policy read-back.
    """
    for rule in rules:
        if (
            rule.action is RuleAction.DENY
            and rule.protocol == protocol
            and rule.src_cidr == src_cidr
            and rule.dst_cidr == dst_cidr
        ):
            return rule
    return None
