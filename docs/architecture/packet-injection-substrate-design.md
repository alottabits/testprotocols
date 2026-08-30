# Packet-Injection Substrate Capability (`PacketInjector`)

**Status:** accepted (2026-08-17) · **Kind:** substrate/tool capability (host
instrument, **not** a device-under-test contract) · **Enforced by:**
`tests/test_network_tool_templates.py` (method-set shape) + the vendor-isolation
grep guarantee (§6)

## 1. What this is

`PacketInjector` is the contract for a testbed instrument that **puts
caller-supplied bytes on the wire**: it crafts and sends a chosen payload, or
replays a chosen capture, onto a test interface. It is the emission primitive that
lets a suite *exercise* an inspecting device (IDS/IPS, anti-malware) without
reinventing a private emitter per testbed.

Two members, one coherent domain (offensive emission for detection testing):

- `emit_signature(payload, target, *, port=None, protocol=RuleProtocol.TCP) -> EmitResult`
  — craft and send caller-supplied bytes to a target (the content-match class).
  `port` is required for port-bearing transports (TCP/UDP) and must be `None` for
  portless ones (ICMP/ICMP6 — e.g. ICMP-tunnel / oversized-ICMP signatures); the
  impl validates the pairing loudly (rule #5, "ports only on port-bearing
  transports"), and `ANY` is not a valid emit transport.
- `replay_pcap(pcap_path, *, iface=None) -> ReplayResult` — put a caller-supplied
  capture on the wire (the flow/session class).

Scanning stays on `NmapScanner`, attacker-originated HTTP on `HttpClient`, and
packet *capture* on `PcapCapture` (read-only). This capability is only emission,
which had no home.

## 2. Class: substrate/tool, not a DUT contract

`PacketInjector` is a **host-substrate instrument** — the same class as
`NmapScanner`, `PcapCapture`, `NetemController`, `IperfGenerator`, `NetworkProbe`,
`ReachabilityResponder`. Its neutrality is proven by **tool universality**, not by
the cross-vendor *K/N* sweep that gates management-plane **device-under-test**
contracts (RADIUS 6/7, the appliance families, `WanLinkAdmin`). Every substrate
tool in this class landed as a single-substrate host-tool wrapper with no
cross-vendor sweep; `PacketInjector` clears that same bar.

It is the *active* counterpart to the passive `ThreatPrevention` (the DUT-side
IDS/IPS + anti-malware subsystem), but the two are **different classes** — an
instrument that emits vs. a management-plane contract that inspects. The pairing is
a convenience, not a class equivalence: do not use the "symmetry" to pull this
substrate tool into the DUT cross-vendor frame.

## 3. Substrate-family survey (proposed, not a conformance matrix)

For a substrate capability the "families" are the independent instruments that can
**back** the contract — not devices under test. Commercial traffic/attack
generators therefore enter as *substrate families*, which **strengthens**
neutrality (the two verbs survive on independent instruments, not one host) without
converting the contract into a DUT check. The survey below is recorded as
**substrate evidence**; `scapy` is the vendor-free reference implementation. OSS
rows are reference-verifiable here; the commercial-appliance rows are recorded from
the maintainers' published-vendor-doc review and are **illustrative of substrate
universality, not a supported-backends list**.

| Substrate | Class | Licence | emit | replay | Note |
|---|---|---|:--:|:--:|---|
| scapy (reference impl) | OSS lib | BSD | ✓ | ✓ | `sendp(rdpcap())` |
| tcpreplay | OSS tool | BSD | — | ✓ | |
| hping3 | OSS tool | GPL | ✓ | — | |
| nping | OSS tool | Nmap | ✓ | — | |
| mausezahn | OSS tool | GPL | ✓ | ✓ | |
| Cisco TRex | commercial-origin OSS | Apache | ✓ | ✓ | field engine emit; 1-packet pcap-template caveat |
| Keysight/Ixia IxNetwork | commercial appliance | proprietary | ✓ | ✓ | raw traffic item |
| Spirent TestCenter | commercial appliance | proprietary | ✓ | ✓ | replay may shrink the packet |
| Xena Valkyrie | commercial appliance | proprietary | ✓ | ✓ | timing not preserved; L2/L3 rewritten by default |
| Keysight BreakingPoint / Spirent CyberFlood | commercial security appliance | proprietary | ◐ | ✓ | emit only via custom-pcap import |

Both verbs are backed by ≥4 independent substrates spanning OSS and commercial
hardware, and no substrate vocabulary appears in either method signature.

## 4. Scope boundary — no strike catalog

The commercial security appliances split into two modes: (a) raw-packet / custom-pcap
replay, which backs these two verbs; and (b) **curated strike-catalog selection** —
a library of named CVE/malware/DDoS strikes chosen by *vendor id*. Mode (b) is a
**different contract shape** whose inclusion would leak a vendor's strike taxonomy
into the neutral surface — the exact anti-pattern `ThreatPrevention` and the
appliance design forbid (assert behaviour, never *"signature N fired"*).
`PacketInjector` is **"put caller-supplied bytes / pcaps on the wire," full stop.**
A catalog mode, if ever needed, is a separate `StrikeLibrary`-shaped capability,
deferred in `GAPS.md` on evidence.

## 5. Replay is not fidelity-guaranteed

Independent substrates replay non-identically: one may emit a smaller packet than
the original, another does not preserve inter-packet timing and rewrites L2/L3
headers, another loads only the first packet of a multi-packet template.
Consequently `replay_pcap` guarantees **"these packets were emitted"**, not a
bit-exact or timing-exact reproduction. `ReplayResult` is deliberately minimal
(`packets`, `duration_s`) so it cannot imply a fidelity the substrate does not
promise.

## 6. Neutrality (vendor-isolation) guarantee

No tool or product name appears in the package source — not in `packet_injector.py`,
not in `models/emission.py`, not in the method or field names. Substrates are cited
**only in this design doc**. Enforced by convention and re-checkable:

```
grep -RiE 'scapy|tcpreplay|hping|nping|mausezahn|trex|ixia|spirent|xena|breakingpoint|cyberflood' \
  src/testprotocols/packet_injector.py src/testprotocols/models/emission.py
# expected: no matches
```

The `protocol` field reuses the normalized `RuleProtocol` StrEnum rather than a
bare `str`, per the under-typed-field rule (`GAPS.md` 2026-06-11, capture-analysis
rule #3).

## 7. Overlap analysis — none

- `PcapCapture` — lifecycle + read only (no inject).
- `NmapScanner` — returns scan results.
- `NetworkProbe` — explicitly read-only ("no data is sent").
- `ReachabilityResponder` — answers probes.
- `IperfGenerator` — iperf load, not crafted signatures.

The craft-and-emit / pcap-replay surface has no other home. Keeping scan on
`NmapScanner` and fetch on `HttpClient` (not folded in) is the SPLITS.md-consistent
call (recorded there).

## 8. Emit→detect orchestration is downstream, not here

Composing the injector with a detection read (emit a signature, then read
`ThreatPrevention.get_security_events` or capture-analyse the result) is a natural
**future `testoperations` operation**, where cross-capability glue belongs. It is
deliberately **not** part of this capability — the capability only emits.

## 9. Archetype deferral

A placed *threat-source* device archetype composing `PacketInjector` with existing
host capabilities is a real shape, but it is **derivable plugin-local today**
(register `MaliciousHostDevice(Protocol)` downstream via `register_device_type`; the
purity gate runs downstream) — the `StreamingServerDevice` playbook. It is therefore
deferred to commons under the three-tier scope rule, logged in `GAPS.md` with a
second-consumer trigger, and lifts to `devices/security.py` (Option A: lean) on
aligned evidence.
