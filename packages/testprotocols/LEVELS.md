# White-box extension log

Per the architecture rule: capability protocols ship a mandatory black-box
"sea-level" surface, plus optional `<Capability>WhiteBox(<Capability>, Protocol)`
extensions for deep introspection. White-box extensions land on tracked evidence
(consumer signal, design review). This file records the evidence.

Format per entry:

```
## YYYY-MM-DD — <Capability>WhiteBox seeded / extended

**Signal:** <consumer-or-reviewer-quote-or-summary>
**Methods:** <list of methods added to the WhiteBox extension>
**Black-box impact:** <which methods stayed on the base, which moved out>
**Rationale:** <why these methods are white-box and not black-box>
**Drivers expected to satisfy:** <which substrate/topology can back it>
**Drivers expected NOT to satisfy:** <which substrate/topology cannot>
```

---

## 2026-05-02 — `WifiRadioWhiteBox` seeded; `inject_radar_event` moved out of base

**Signal:** During Task 9 (manual review and acceptance gate of the ABC →
Protocol migration), the reviewer flagged: *"In wifi_radio.py, you have
inject_radar_event(). The docstring admits: 'Drivers without hardware/simulation
support (i.e. all real APs) raise NotImplementedError'. This breaks the
Liskov Substitution Principle. A black-box test operating against the
WifiRadio protocol should not have to try/except a NotImplementedError for
a standard method."*

**Methods:**
- `inject_radar_event(band, channel)` — moved from `WifiRadio` to `WifiRadioWhiteBox`. Docstring revised: drivers without hardware/simulation support **do not satisfy** the WhiteBox extension at all (rather than raising at call time).
- `get_raw_phy_dump() -> str` — newly seeded in WhiteBox per reviewer's example. Returns raw nl80211 / vendor PHY state for diagnostics.

**Black-box impact:** `WifiRadio` mandatory surface now contains only methods that any conforming WiFi-capable device can satisfy. No more LSP violations on the base Protocol.

**Rationale:** Synthetic radar injection requires kernel-side simulation (`mac80211_hwsim`) or vendor PHY-test harness. Real APs cannot back it without hardware modification. White-box extensions express this honestly: drivers that can't back it don't satisfy the extension; tests requiring it pin against the extension and collection-skip on insufficient drivers.

**Drivers expected to satisfy:** OpenWrt + `mac80211_hwsim`, vendor PHY-test stacks, simulated environments.

**Drivers expected NOT to satisfy:** Production AP firmware (RDK-B, OpenWrt without hwsim, vendor RTOS), all closed-firmware appliances.

---

## 2026-05-02 — `PacketFilterWhiteBox` seeded

**Signal:** During Task 9 review: *"PacketFilterWhiteBox: Add get_kernel_iptables_dump() or get_nftables_ruleset()."* Reviewer rationale: black-box `PacketFilter` operations don't let tests verify rules actually landed at the kernel level — only that the driver believes the rule was added. White-box dumps close the gap.

**Methods:**
- `get_kernel_iptables_dump() -> str` — raw `iptables-save` output for the legacy iptables backend.
- `get_nftables_ruleset() -> str` — raw `nft list ruleset` output for the nftables backend.

**Black-box impact:** None — these are new methods. The base `PacketFilter` Protocol is unchanged.

**Rationale:** The base `PacketFilter` Protocol describes intent (add a rule, list rules in this chain, get counters); driver-side translation can produce the right effect *or* silently lose the rule (e.g. table mismatch, family mismatch, vendor-CLI bug). Kernel-level verification is the deepest possible black-box check; making it a white-box extension keeps the base small while letting tests pin against the extension when they need byte-level verification.

**Drivers expected to satisfy:** Linux-substrate drivers that can `execute_command` into the box (OpenWrt, plain Debian / Ubuntu CPEs, prplOS).

**Drivers expected NOT to satisfy:** Vendor-RTOS drivers that don't expose iptables/nftables (Broadcom CFE-based, Realtek SDK-only firmware), TR-069-only-managed devices (no shell access), docker stubs that mock the underlying packet filter without a real kernel netfilter behind them.

---

## 2026-05-02 — `ConntrackWhiteBox` seeded

**Signal:** During Task 9 review: *"ConntrackWhiteBox: Add raw kernel conntrack -L dumping."* Black-box `Conntrack` operations let you list / count flows; the white-box dump lets you verify NAT-translation correctness, debug stuck flows, and confirm timeout behaviour.

**Methods:**
- `get_raw_conntrack_dump() -> str` — raw `conntrack -L` output (one line per flow with proto / src / dst / sport / dport / state / mark fields).

**Black-box impact:** None — new method. Base `Conntrack` Protocol unchanged.

**Rationale:** Same shape as `PacketFilterWhiteBox` — base describes operations, extension exposes raw kernel state for diagnostic pinning.

**Drivers expected to satisfy:** Linux-substrate drivers with shell access to a netfilter-based kernel.

**Drivers expected NOT to satisfy:** non-netfilter substrates, vendor-RTOS, TR-069-only, docker mocks.

---

## 2026-05-02 — `WifiMeshWhiteBox` seeded

**Signal:** During Task 9 review: *"WifiMeshWhiteBox: Add methods to read raw IEEE 1905.1 AL-entity state, raw EasyMesh TLVs, or raw controller logs."* Black-box `WifiMesh` operations cover the test-author API (set backhaul, add agent, steer client); white-box dumps let tests verify EasyMesh control-plane behaviour at the protocol level.

**Methods:**
- `get_raw_ieee1905_state() -> str` — verbatim 1905.1 AL-entity state dump.
- `get_raw_easymesh_tlvs(message_type=None) -> str` — recent observed TLVs, optionally filtered by message type.
- `get_controller_logs(since_seconds=60.0) -> str` — recent controller-side log lines.

**Black-box impact:** None — all new methods. Base `WifiMesh` Protocol unchanged.

**Rationale:** EasyMesh / 1905.1 control-plane debugging is essential for failure-mode triage but not necessary for steady-state black-box tests (which can poll topology / association events through the base Protocol). Extension lets tests requiring raw-protocol verification pin against the white-box without forcing every conforming controller to expose internal logs.

**Drivers expected to satisfy:** Open-source EasyMesh stacks (prplMesh on prplOS, hostapd-based controllers) with shell access. Possibly vendor controllers with documented diagnostic CLIs.

**Drivers expected NOT to satisfy:** Closed-source vendor controllers without diagnostic-CLI access, mesh-controller-as-a-cloud-service deployments.

---

## 2026-05-11 — `FirewallWhiteBox` seeded

**Signal:** Architecture / code divergence review (see SPLITS.md
2026-05-11 entry for the `PortForwarding` → `Firewall` fold). When
`Firewall` was created as a Protocol extension of `PacketFilter`, the
WhiteBox tier seeded automatically: the same `iptables-save` and
`nft list ruleset` dumps that back `PacketFilterWhiteBox` natively span
both filter rules and DNAT / port-forward entries, so the white-box
methods needed at the `Firewall` tier are identical to those at the
`PacketFilter` tier.

**Methods:**
- `get_kernel_iptables_dump() -> str` — raw `iptables-save` output (legacy backend); spans filter chains, NAT chains, and DNAT / port-forward entries.
- `get_nftables_ruleset() -> str` — raw `nft list ruleset` output (nftables backend); spans the full ruleset.

**Black-box impact:** None — these are new methods on the new
`FirewallWhiteBox` extension. The base `Firewall` Protocol mandates only
rule administration + port-forwarding methods.

**Rationale:** Same shape as `PacketFilterWhiteBox` — base describes
intent, extension exposes raw kernel state for diagnostic pinning. The
two WhiteBox extensions share their method set because Linux kernel
dumps cover the union of both tiers in one stream.

**Drivers expected to satisfy:** Linux-substrate drivers with shell
access (OpenWrt, plain Debian / Ubuntu CPEs, prplOS).

**Drivers expected NOT to satisfy:** Vendor-RTOS drivers without
iptables/nftables, TR-069-only-managed devices (no shell access),
docker stubs that mock the underlying packet filter without a real
kernel netfilter behind them.

---

## Open candidates (signals received, action deferred)

*None yet.*

The architecture doc (palco-bdd `palco-architecture.md` v2.0) initially listed
`FirewallWhiteBox`, `RoutingWhiteBox`, `SipPhoneWhiteBox`, `SipServerWhiteBox`
as seed extensions. `FirewallWhiteBox` is seeded as of 2026-05-11 (see entry
above). The remaining three — `RoutingWhiteBox`, `SipPhoneWhiteBox`,
`SipServerWhiteBox` — remain aspirational; future consumer signals will
determine whether to seed them.
