"""The firewall, NAT and conntrack vocabularies are enums; plain strings are deprecated.

Parameters, through minimal conforming fakes; model fields store a plain string as given.
"""

from __future__ import annotations

import dataclasses
import warnings

import pytest
from testprotocols.conntrack import Conntrack
from testprotocols.models import (
    Chain,
    Connection,
    DefaultAction,
    FirewallRule,
    FirewallRuleAction,
    NatMode,
    NatRule,
    PortMapping,
    PortMappingProtocol,
    RuleCounters,
    RuleProtocol,
)
from testprotocols.nat import Nat
from testprotocols.packet_filter import PacketFilter


def _values(enum_type: type[Chain] | type[FirewallRuleAction] | type[NatMode]) -> list[str]:
    return [m.value for m in enum_type]


def test_chain_values() -> None:
    assert _values(Chain) == ["INPUT", "OUTPUT", "FORWARD"]


def test_firewall_rule_action_values() -> None:
    assert _values(FirewallRuleAction) == ["allow", "deny", "reject", "log"]


def test_nat_mode_values() -> None:
    assert _values(NatMode) == ["snat", "dnat", "1to1"]


def test_port_mapping_protocol_values() -> None:
    assert [m.value for m in PortMappingProtocol] == ["tcp", "udp", "tcp-udp"]


# --- shape 1: parameters, through minimal conforming fakes ---------------------


class _FakeFilter:
    """Converts each parameter once, at the boundary, as a driver does."""

    def __init__(self) -> None:
        self.rules: dict[Chain, list[FirewallRule]] = {c: [] for c in Chain}
        self.policy: dict[Chain, DefaultAction] = {}

    def add_rule(self, chain: Chain | str, rule: FirewallRule, position: int | None = None) -> None:
        self.rules[Chain(chain)].append(rule)

    def remove_rule(self, chain: Chain | str, name: str) -> None:
        Chain(chain)

    def list_rules(self, chain: Chain | str) -> list[FirewallRule]:
        return self.rules[Chain(chain)]

    def get_rule(self, chain: Chain | str, name: str) -> FirewallRule:
        raise KeyError(name)

    def flush_chain(self, chain: Chain | str) -> None:
        self.rules[Chain(chain)].clear()

    def set_default_policy(self, chain: Chain | str, policy: DefaultAction | str) -> None:
        self.policy[Chain(chain)] = DefaultAction(policy)

    def get_default_policy(self, chain: Chain | str) -> str:
        return self.policy[Chain(chain)]

    def get_rule_counter_values(self, chain: Chain | str, name: str) -> RuleCounters:
        return RuleCounters(0, 0)

    def get_rule_counters(self, chain: Chain | str, name: str) -> tuple[int, int]:
        return (0, 0)


def _rule() -> FirewallRule:
    return FirewallRule("r", FirewallRuleAction.ALLOW, RuleProtocol.TCP, "any", "any", "any")


def test_the_fake_conforms_to_packet_filter() -> None:
    assert isinstance(_FakeFilter(), PacketFilter)


def test_a_plain_chain_works() -> None:
    fake = _FakeFilter()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fake.add_rule("FORWARD", _rule())
        fake.add_rule(Chain.INPUT, _rule())
    assert fake.list_rules(Chain.FORWARD) == [_rule()]


@pytest.mark.parametrize("call", ["add_rule", "remove_rule", "list_rules", "flush_chain"])
def test_an_unknown_chain_raises_value_error(call: str) -> None:
    fake = _FakeFilter()
    args: tuple[object, ...] = {
        "add_rule": ("MANGLE", _rule()),
        "remove_rule": ("MANGLE", "r"),
        "list_rules": ("MANGLE",),
        "flush_chain": ("MANGLE",),
    }[call]
    with pytest.raises(ValueError, match="MANGLE"):
        getattr(fake, call)(*args)


def test_a_plain_policy_works_and_an_unknown_one_raises() -> None:
    fake = _FakeFilter()
    fake.set_default_policy(Chain.INPUT, "drop")
    assert fake.get_default_policy(Chain.INPUT) == "drop"
    with pytest.raises(ValueError, match="allow"):
        fake.set_default_policy(Chain.INPUT, "allow")


class _FakeNat:
    def __init__(self) -> None:
        self.rules = [NatRule("a", NatMode.SNAT, "wan"), NatRule("b", NatMode.DNAT, "wan")]

    def add_nat_rule(self, rule: NatRule) -> None: ...
    def remove_nat_rule(self, name: str) -> None: ...

    def list_nat_rules(self, mode: NatMode | str | None = None) -> list[NatRule]:
        if mode is None:
            return list(self.rules)
        wanted = NatMode(mode)
        return [r for r in self.rules if r.mode is wanted]

    def get_nat_rule(self, name: str) -> NatRule:
        raise KeyError(name)

    def set_nat_rule_enabled(self, name: str, enabled: bool) -> None: ...
    def flush_nat_rules(self) -> None: ...
    def get_nat_rule_counter_values(self, name: str) -> RuleCounters:
        return RuleCounters(0, 0)

    def get_nat_rule_counters(self, name: str) -> tuple[int, int]:
        return (0, 0)


def test_list_nat_rules_mode() -> None:
    fake = _FakeNat()
    assert isinstance(fake, Nat)
    assert len(fake.list_nat_rules()) == 2
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert [r.name for r in fake.list_nat_rules(NatMode.DNAT)] == ["b"]
    assert [r.name for r in fake.list_nat_rules("snat")] == ["a"]
    with pytest.raises(ValueError, match="nat44"):
        fake.list_nat_rules("nat44")


class _FakeConntrack:
    def __init__(self) -> None:
        self.flows = [
            Connection(
                RuleProtocol.TCP,
                "192.0.2.1",
                "198.51.100.1",
                1,
                80,
                "ESTABLISHED",
                5,
                0,
                0,
                0,
                0,
            ),
            Connection(
                RuleProtocol.UDP, "192.0.2.1", "198.51.100.1", 1, 53, "gre-weird", 5, 0, 0, 0, 0
            ),
        ]

    def get_stats(self) -> object:
        raise NotImplementedError

    def list_connections(
        self,
        *,
        protocol: RuleProtocol | str | None = None,
        src_ip: str | None = None,
        dst_ip: str | None = None,
        dst_port: int | None = None,
        state: str | None = None,
    ) -> list[Connection]:
        found = self.flows
        if protocol is not None:
            wanted = RuleProtocol(protocol)
            found = [c for c in found if c.protocol is wanted]
        if state is not None:
            found = [c for c in found if c.state == state]
        return found

    def count_connections(
        self, *, protocol: RuleProtocol | str | None = None, state: str | None = None
    ) -> int:
        return len(self.list_connections(protocol=protocol, state=state))

    def get_connection(
        self,
        protocol: RuleProtocol | str,
        src_ip: str,
        dst_ip: str,
        src_port: int | None,
        dst_port: int | None,
    ) -> Connection:
        raise KeyError

    def drop_connection(
        self,
        protocol: RuleProtocol | str,
        src_ip: str,
        dst_ip: str,
        src_port: int | None,
        dst_port: int | None,
    ) -> None: ...
    def flush_connections(self) -> None: ...
    def set_max_connections(self, max_connections: int) -> None: ...
    def get_max_connections(self) -> int:
        return 0


def test_conntrack_filters() -> None:
    fake = _FakeConntrack()
    assert isinstance(fake, Conntrack)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert fake.count_connections(protocol=RuleProtocol.TCP, state="ESTABLISHED") == 1
        # the state is the device's own word: it filters on that word, silently
        assert fake.count_connections(state="gre-weird") == 1
        assert fake.count_connections(state="other-weird") == 0
    assert fake.count_connections(protocol="udp") == 1
    with pytest.raises(ValueError, match="sctp"):
        fake.count_connections(protocol="sctp")


# --- model fields: a member or a plain string, stored as given ------------------


def _nat() -> NatRule:
    return NatRule("n", NatMode.SNAT, "wan")


def _mapping() -> PortMapping:
    return PortMapping("m", 80, PortMappingProtocol.TCP, "10.0.0.2", 80)


def _conn(**kw: object) -> Connection:
    args: dict[str, object] = {
        "protocol": RuleProtocol.TCP,
        "src_ip": "192.0.2.1",
        "dst_ip": "198.51.100.1",
        "src_port": 1,
        "dst_port": 2,
        "state": "ESTABLISHED",
        "timeout_seconds": 1,
        "bytes_orig": 0,
        "bytes_reply": 0,
        "packets_orig": 0,
        "packets_reply": 0,
    }
    args.update(kw)
    return Connection(**args)  # type: ignore[arg-type]


def test_models_built_from_members_do_not_warn_and_defaults_are_released() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rule, nat, mapping, conn = _rule(), _nat(), _mapping(), _conn()
    assert nat.protocol == "any" and type(nat.protocol) is str  # the released default
    assert nat.protocol == RuleProtocol.ANY
    assert rule.action is FirewallRuleAction.ALLOW and rule.protocol is RuleProtocol.TCP
    assert mapping.protocol is PortMappingProtocol.TCP
    assert conn.state == "ESTABLISHED"


def test_plain_strings_are_stored_as_given_and_equal_the_members() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rule = FirewallRule("r", "deny", "udp", "any", "any", "any")
        nat = dataclasses.replace(_nat(), mode="dnat")
        mapping = _mapping()
        mapping.protocol = "tcp-udp"
        conn = _conn(protocol="icmp")
    assert (type(rule.action), type(nat.mode), type(mapping.protocol)) == (str, str, str)
    assert rule.action == FirewallRuleAction.DENY and rule.protocol == RuleProtocol.UDP
    assert nat.mode == NatMode.DNAT
    assert mapping.protocol == PortMappingProtocol.TCP_UDP
    assert conn.protocol == RuleProtocol.ICMP
