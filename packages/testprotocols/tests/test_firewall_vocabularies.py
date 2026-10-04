"""The firewall, NAT and conntrack vocabularies are enums; plain strings are deprecated.

Shape 1 (parameters, through minimal conforming fakes), shape 3 (model fields) and
shape 3o (``Connection.state``, an open enum with a raw-word companion).
"""

from __future__ import annotations

import dataclasses
import warnings

import pytest
from testprotocols.conntrack import Conntrack
from testprotocols.deprecation import coerce_enum, coerce_open_enum
from testprotocols.models import (
    Chain,
    Connection,
    ConnState,
    DefaultAction,
    FirewallRule,
    FirewallRuleAction,
    NatMode,
    NatRule,
    PortMapping,
    PortMappingProtocol,
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


def test_conn_state_values_cover_the_released_docstring() -> None:
    released = (
        "SYN_SENT SYN_RECV ESTABLISHED FIN_WAIT CLOSE_WAIT LAST_ACK TIME_WAIT CLOSE LISTEN "
        "UNREPLIED ASSURED"
    ).split()
    for word in released:
        assert ConnState(word).name == word
        assert word == ConnState[word]  # equals the released upper-case string
    assert ConnState.OTHER.value == "OTHER"
    assert [m.name for m in ConnState] == [*released, "OTHER"]


# --- shape 1: parameters, through minimal conforming fakes ---------------------


class _FakeFilter:
    """Coerces each parameter once, at the boundary, as a driver does."""

    def __init__(self) -> None:
        self.rules: dict[Chain, list[FirewallRule]] = {c: [] for c in Chain}
        self.policy: dict[Chain, DefaultAction] = {}

    def add_rule(self, chain: Chain | str, rule: FirewallRule, position: int | None = None) -> None:
        self.rules[coerce_enum(Chain, chain, what="add_rule chain")].append(rule)

    def remove_rule(self, chain: Chain | str, name: str) -> None:
        coerce_enum(Chain, chain, what="remove_rule chain")

    def list_rules(self, chain: Chain | str) -> list[FirewallRule]:
        return self.rules[coerce_enum(Chain, chain, what="list_rules chain")]

    def get_rule(self, chain: Chain | str, name: str) -> FirewallRule:
        raise KeyError(name)

    def flush_chain(self, chain: Chain | str) -> None:
        self.rules[coerce_enum(Chain, chain, what="flush_chain chain")].clear()

    def set_default_policy(self, chain: Chain | str, policy: DefaultAction | str) -> None:
        self.policy[coerce_enum(Chain, chain, what="set_default_policy chain")] = coerce_enum(
            DefaultAction, policy, what="set_default_policy policy"
        )

    def get_default_policy(self, chain: Chain | str) -> str:
        return self.policy[coerce_enum(Chain, chain, what="get_default_policy chain")]

    def get_rule_counters(self, chain: Chain | str, name: str) -> tuple[int, int]:
        return (0, 0)


def _rule() -> FirewallRule:
    return FirewallRule("r", FirewallRuleAction.ALLOW, RuleProtocol.TCP, "any", "any", "80")


def test_the_fake_conforms_to_packet_filter() -> None:
    assert isinstance(_FakeFilter(), PacketFilter)


def test_a_plain_chain_warns_and_works_at_the_callers_frame() -> None:
    fake = _FakeFilter()
    with pytest.warns(DeprecationWarning, match=r"add_rule chain.*Chain\.FORWARD") as caught:
        fake.add_rule("FORWARD", _rule())
    assert caught[0].filename == __file__
    assert fake.list_rules(Chain.FORWARD) == [_rule()]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fake.add_rule(Chain.INPUT, _rule())


@pytest.mark.parametrize("call", ["add_rule", "remove_rule", "list_rules", "flush_chain"])
def test_an_unknown_chain_raises_value_error(call: str) -> None:
    fake = _FakeFilter()
    args: tuple[object, ...] = {
        "add_rule": ("MANGLE", _rule()),
        "remove_rule": ("MANGLE", "r"),
        "list_rules": ("MANGLE",),
        "flush_chain": ("MANGLE",),
    }[call]
    with pytest.raises(ValueError, match=r"MANGLE.*INPUT"):
        getattr(fake, call)(*args)


def test_a_plain_policy_warns_and_an_unknown_one_raises() -> None:
    fake = _FakeFilter()
    with pytest.warns(DeprecationWarning, match=r"DefaultAction\.DROP"):
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
        wanted = coerce_enum(NatMode, mode, what="list_nat_rules mode")
        return [r for r in self.rules if r.mode is wanted]

    def get_nat_rule(self, name: str) -> NatRule:
        raise KeyError(name)

    def set_nat_rule_enabled(self, name: str, enabled: bool) -> None: ...
    def flush_nat_rules(self) -> None: ...
    def get_nat_rule_counters(self, name: str) -> tuple[int, int]:
        return (0, 0)


def test_list_nat_rules_mode() -> None:
    fake = _FakeNat()
    assert isinstance(fake, Nat)
    assert len(fake.list_nat_rules()) == 2
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert [r.name for r in fake.list_nat_rules(NatMode.DNAT)] == ["b"]
    with pytest.warns(DeprecationWarning, match=r"NatMode\.SNAT") as caught:
        assert [r.name for r in fake.list_nat_rules("snat")] == ["a"]
    assert caught[0].filename == __file__
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
                ConnState.ESTABLISHED,
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
        state: ConnState | str | None = None,
    ) -> list[Connection]:
        found = self.flows
        if protocol is not None:
            wanted = coerce_enum(RuleProtocol, protocol, what="list_connections protocol")
            found = [c for c in found if c.protocol is wanted]
        if state is not None:
            member, raw = coerce_open_enum(
                ConnState, state, what="list_connections state", other=ConnState.OTHER
            )
            found = [c for c in found if c.state is member and c.state_raw == raw]
        return found

    def count_connections(
        self, *, protocol: RuleProtocol | str | None = None, state: ConnState | str | None = None
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
        assert fake.count_connections(protocol=RuleProtocol.TCP, state=ConnState.ESTABLISHED) == 1
        # an unknown word is data, not an error: it filters on the raw word, silently
        assert fake.count_connections(state="gre-weird") == 1
        assert fake.count_connections(state="other-weird") == 0
    with pytest.warns(DeprecationWarning, match=r"RuleProtocol\.UDP"):
        assert fake.count_connections(protocol="udp") == 1
    with pytest.warns(DeprecationWarning, match=r"ConnState\.ESTABLISHED"):
        assert fake.count_connections(state="ESTABLISHED") == 1
    with pytest.raises(ValueError, match="sctp"):
        fake.count_connections(protocol="sctp")


# --- shape 3: model fields (construction, replace, assignment) -----------------


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
        "state": ConnState.ESTABLISHED,
        "timeout_seconds": 1,
        "bytes_orig": 0,
        "bytes_reply": 0,
        "packets_orig": 0,
        "packets_reply": 0,
    }
    args.update(kw)
    return Connection(**args)  # type: ignore[arg-type]


def test_models_built_from_members_do_not_warn_and_defaults_are_members() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        rule, nat, mapping, conn = _rule(), _nat(), _mapping(), _conn()
    assert nat.protocol is RuleProtocol.ANY
    assert rule.action is FirewallRuleAction.ALLOW and rule.protocol is RuleProtocol.TCP
    assert mapping.protocol is PortMappingProtocol.TCP
    assert conn.state_raw is None


def test_firewall_rule_coerces_on_construction_replace_and_assignment() -> None:
    with pytest.warns(DeprecationWarning) as caught:
        rule = FirewallRule("r", "deny", "udp", "any", "any", "53")
    assert [str(w.message).split(":")[0] for w in caught] == [
        "FirewallRule.action",
        "FirewallRule.protocol",
    ]
    assert all(w.filename == __file__ for w in caught)
    assert rule.action is FirewallRuleAction.DENY and rule.protocol is RuleProtocol.UDP
    with pytest.warns(DeprecationWarning) as caught:
        again = dataclasses.replace(rule, action="log")
    assert again.action is FirewallRuleAction.LOG and caught[0].filename == __file__
    with pytest.warns(DeprecationWarning, match=r"FirewallRule\.protocol"):
        again.protocol = "tcp"
    assert again.protocol is RuleProtocol.TCP
    with pytest.raises(ValueError, match="permit"):
        again.action = "permit"
    assert again.action is FirewallRuleAction.LOG
    with pytest.raises(ValueError, match="gre"):
        FirewallRule("r", FirewallRuleAction.ALLOW, "gre", "any", "any", "1")


def test_nat_rule_coerces_on_construction_replace_and_assignment() -> None:
    with pytest.warns(DeprecationWarning) as caught:
        nat = NatRule("n", "dnat", "wan", protocol="tcp")
    assert nat.mode is NatMode.DNAT and nat.protocol is RuleProtocol.TCP
    assert all(w.filename == __file__ for w in caught)
    with pytest.warns(DeprecationWarning, match=r"NatRule\.mode"):
        other = dataclasses.replace(nat, mode="1to1")
    assert other.mode is NatMode.ONE_TO_ONE
    with pytest.warns(DeprecationWarning, match=r"NatMode\.SNAT"):
        other.mode = "snat"
    assert other.mode is NatMode.SNAT
    with pytest.raises(ValueError, match="nat66"):
        other.mode = "nat66"
    with pytest.raises(ValueError):
        NatRule("n", NatMode.SNAT, "wan", protocol="gre")


def test_port_mapping_coerces_on_construction_replace_and_assignment() -> None:
    with pytest.warns(DeprecationWarning, match=r"PortMapping\.protocol") as caught:
        mapping = PortMapping("m", 80, "tcp-udp", "10.0.0.2", 80)
    assert mapping.protocol is PortMappingProtocol.TCP_UDP
    assert caught[0].filename == __file__
    with pytest.warns(DeprecationWarning):
        again = dataclasses.replace(mapping, protocol="udp")
    assert again.protocol is PortMappingProtocol.UDP
    with pytest.warns(DeprecationWarning):
        again.protocol = "tcp"
    assert again.protocol is PortMappingProtocol.TCP
    with pytest.raises(ValueError, match="icmp"):
        again.protocol = "icmp"


def test_connection_protocol_coerces_on_construction_replace_and_assignment() -> None:
    with pytest.warns(DeprecationWarning, match=r"Connection\.protocol") as caught:
        conn = _conn(protocol="icmp")
    assert conn.protocol is RuleProtocol.ICMP and caught[0].filename == __file__
    with pytest.warns(DeprecationWarning):
        again = dataclasses.replace(conn, protocol="udp")
    assert again.protocol is RuleProtocol.UDP
    with pytest.warns(DeprecationWarning):
        again.protocol = "tcp"
    assert again.protocol is RuleProtocol.TCP
    with pytest.raises(ValueError, match="sctp"):
        again.protocol = "sctp"


# --- shape 3o: Connection.state ------------------------------------------------


def _pair(conn: Connection) -> tuple[ConnState | str, str | None]:
    return conn.state, conn.state_raw


def test_conn_state_equals_the_released_strings() -> None:
    assert _conn(state=ConnState.ESTABLISHED).state == "ESTABLISHED"
    assert _conn(state=ConnState.UNREPLIED).state == "UNREPLIED"


def test_conn_state_unknown_word_is_other_and_keeps_raw() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # the set is open: no warning
        conn = _conn(state="NEW-FANCY")
    assert _pair(conn) == (ConnState.OTHER, "NEW-FANCY")


def test_conn_state_plain_member_name_converts_and_warns() -> None:
    with pytest.warns(DeprecationWarning, match=r"Connection\.state.*ConnState\.SYN_SENT") as w:
        conn = _conn(state="SYN_SENT")
    assert _pair(conn) == (ConnState.SYN_SENT, None)
    assert w[0].filename == __file__


def test_conn_state_edge_words_are_pinned() -> None:
    # "OTHER" names the catch-all member: it converts (with the warning), no raw word
    with pytest.warns(DeprecationWarning, match=r"ConnState\.OTHER"):
        assert _pair(_conn(state="OTHER")) == (ConnState.OTHER, None)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        # the match is exact: another letter case, or the empty word, is an unknown word
        assert _pair(_conn(state="other")) == (ConnState.OTHER, "other")
        assert _pair(_conn(state="established")) == (ConnState.OTHER, "established")
        assert _pair(_conn(state="")) == (ConnState.OTHER, "")


def test_conn_state_other_member_with_explicit_raw() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        conn = _conn(state=ConnState.OTHER, state_raw="vendor-state")
    assert _pair(conn) == (ConnState.OTHER, "vendor-state")
    assert _conn(state=ConnState.OTHER).state_raw is None


def test_conn_state_construction_refuses_a_raw_word_that_does_not_belong() -> None:
    with pytest.raises(ValueError, match="state_raw"):
        _conn(state=ConnState.ESTABLISHED, state_raw="x")
    with pytest.raises(ValueError, match="disagree"):
        _conn(state="weird", state_raw="y")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _pair(_conn(state="weird", state_raw="weird")) == (ConnState.OTHER, "weird")


def test_conn_state_assignment_keeps_the_pair_consistent() -> None:
    conn = _conn(state="weird")
    conn.state = ConnState.CLOSE
    assert _pair(conn) == (ConnState.CLOSE, None)
    conn.state = "another"
    assert _pair(conn) == (ConnState.OTHER, "another")
    conn.state = ConnState.OTHER  # a member clears the raw word
    assert _pair(conn) == (ConnState.OTHER, None)
    conn.state_raw = "set-later"
    assert _pair(conn) == (ConnState.OTHER, "set-later")
    conn.state_raw = None
    assert _pair(conn) == (ConnState.OTHER, None)
    with pytest.warns(DeprecationWarning):
        conn.state = "LISTEN"
    assert _pair(conn) == (ConnState.LISTEN, None)


def test_conn_state_assignment_refusals_change_nothing() -> None:
    conn = _conn()
    with pytest.raises(ValueError, match="state_raw"):
        conn.state_raw = "x"
    with pytest.raises(TypeError):
        conn.state = 5  # type: ignore[assignment]
    assert _pair(conn) == (ConnState.ESTABLISHED, None)
    other = _conn(state=ConnState.OTHER)
    with pytest.raises(TypeError):
        other.state_raw = 5  # type: ignore[assignment]
    assert _pair(other) == (ConnState.OTHER, None)


def test_conn_state_replace_the_side_that_changed_wins() -> None:
    conn = _conn(state="weird")
    same = dataclasses.replace(conn, bytes_orig=9)
    assert _pair(same) == (ConnState.OTHER, "weird")
    named = dataclasses.replace(conn, state=ConnState.ESTABLISHED)
    assert _pair(named) == (ConnState.ESTABLISHED, None)
    reworded = dataclasses.replace(conn, state="stranger")
    assert _pair(reworded) == (ConnState.OTHER, "stranger")
    with pytest.warns(DeprecationWarning):
        converted = dataclasses.replace(conn, state="CLOSE")
    assert _pair(converted) == (ConnState.CLOSE, None)
    assert dataclasses.replace(conn, state_raw="renamed").state_raw == "renamed"
    assert dataclasses.replace(conn, state_raw=None).state_raw is None
    assert _pair(conn) == (ConnState.OTHER, "weird")


def test_conn_state_replace_with_both_sides_changed() -> None:
    conn = _conn()
    with pytest.raises(ValueError, match="state_raw"):  # a named state takes no raw word
        dataclasses.replace(conn, state=ConnState.ASSURED, state_raw="q")
    with pytest.raises(ValueError, match="state_raw"):
        dataclasses.replace(conn, state_raw="zzz")  # changing only the raw word of a named state
    both = dataclasses.replace(conn, state=ConnState.OTHER, state_raw="q")
    assert _pair(both) == (ConnState.OTHER, "q")
    with pytest.raises(ValueError, match="disagree"):
        dataclasses.replace(both, state="w", state_raw="v")
    assert _pair(dataclasses.replace(both, state="w", state_raw="w")) == (ConnState.OTHER, "w")


def test_conn_state_equality_and_repr_see_the_raw_word_not_the_provenance() -> None:
    assert _conn(state="a") == _conn(state="a")
    assert _conn(state="a") != _conn(state="b")
    assert "_state_seen" not in repr(_conn(state="a"))
    assert "state_raw='a'" in repr(_conn(state="a"))


def test_connection_refuses_the_any_protocol() -> None:
    with pytest.raises(ValueError, match="one transport"):
        _conn(protocol=RuleProtocol.ANY)
    with pytest.raises(ValueError, match="one transport"):
        with pytest.warns(DeprecationWarning):
            _conn(protocol="any")
    conn = _conn()
    with pytest.raises(ValueError, match="one transport"):
        conn.protocol = RuleProtocol.ANY
    with pytest.raises(ValueError, match="one transport"):
        dataclasses.replace(conn, protocol=RuleProtocol.ANY)
    assert conn.protocol is RuleProtocol.TCP


# --- coerce_open_enum ----------------------------------------------------------


def test_coerce_open_enum_member_is_returned_as_is() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert coerce_open_enum(ConnState, ConnState.CLOSE, what="x", other=ConnState.OTHER) == (
            ConnState.CLOSE,
            None,
        )


def test_coerce_open_enum_named_str_converts_and_warns() -> None:
    def boundary(state: str) -> tuple[ConnState, str | None]:
        return coerce_open_enum(ConnState, state, what="x", other=ConnState.OTHER)

    with pytest.warns(DeprecationWarning, match=r"x: plain string 'CLOSE'.*ConnState\.CLOSE") as w:
        result = boundary("CLOSE")
    assert result == (ConnState.CLOSE, None)
    assert w[0].filename == __file__  # the caller of the function that coerces


def test_coerce_open_enum_unknown_str_is_other_without_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert coerce_open_enum(ConnState, "nope", what="x", other=ConnState.OTHER) == (
            ConnState.OTHER,
            "nope",
        )


def test_coerce_open_enum_match_is_exact() -> None:
    assert coerce_open_enum(ConnState, "close", what="x", other=ConnState.OTHER) == (
        ConnState.OTHER,
        "close",
    )


def test_coerce_open_enum_rejects_other_types() -> None:
    for bad in (None, 3, b"CLOSE", 1.5):
        with pytest.raises(TypeError, match="x"):
            coerce_open_enum(ConnState, bad, what="x", other=ConnState.OTHER)  # type: ignore[arg-type]
