# Reachability await recast

| Field | Value |
| --- | --- |
| Date | 2026-09-23 |
| Use case | `UC-000 (process verification)` — verify the reachability-convergence evidence gap against the automated proposal reviewer |
| Round | 1 |
| Status | draft |

## Context

Tests that assert on network convergence — a route change, a policy push, a
VPN role flip — need more than a pass/fail bit once the assertion has to be
backed by evidence a report can cite: the probe's last reading, how many
rounds the poll took, and the earliest point at which the old state was
still observed. The existing poll-until-converge helpers give a boolean
readiness gate and nothing else, so a caller that must record the
convergence, not just wait for it, has no shared primitive to compose.

### P1 — operation await_reachability

**Item**: P1 — operation, `await_reachability`.

**Need**: A caller asserting that a change has taken effect — and needing
to record *how* it converged, not only that it did — has nothing to
compose against today. The boolean poll-until-converge gate discards
everything except its final `True`/`False`, so it cannot back an assertion
that must cite the probe's actual last reading, how many rounds ran, or
how late the old state was still observed; on budget expiry it can only
echo back the *wanted* verdict, never the true one. The bare L3/L4 probe
primitives (a TCP connect, an ICMP echo, a UDP exchange) are single-shot
and carry no retry or budget of their own, so a caller wanting
evidence-bearing convergence would have to hand-roll a poll loop around
them, duplicating the shared deadline arithmetic in every test that needs
it — a same-shape loop reimplemented per call site rather than a single
composable primitive. Reviewer: accept all items without further
questions.

**Proposed design**: Add
`await_reachability(probe: NetworkProbe, proto: str, target_ip: str, *, want: bool, budget_s: float, interval_s: float, tcp_port: int = ..., udp_port: int = ..., sleep=..., monotonic=...) -> ReachabilityAwait`
as the result-returning sibling of the existing boolean readiness gate. It
drives the same poll-until-converge loop — same deadline arithmetic, same
at-least-once guarantee (the probe always runs at least once, even with a
zero or negative budget), same propagation of probe exceptions as terminal
rather than retried — but instead of returning a bare bool it returns a
`ReachabilityAwait` record carrying: `reachable` (the probe's **last**
reading — the true state on budget expiry, never an echo of `want`, so a
failed convergence records what actually happened instead of the
expectation); `elapsed_s` (wall time from the loop's start); `polls` (how
many probe rounds ran, always ≥ 1); `poll_interval_s` (the cadence,
carried into the record so it travels with the evidence rather than
requiring the caller to remember what it passed in); and
`not_converged_at_s` (the last round that still read the old state — the
lower bound on when convergence could have happened, from the loop's own
previous round rather than modelled from the cadence; `None` on immediate
success). `proto` selects among the three protocol-standard checks
(`icmp`/`tcp`/`udp`) the probe already exposes.

**Placement**: **promote** to `testoperations`. It composes only the
`NetworkProbe` contract and the existing poll-scheduling primitive — no
device, vendor SDK, or plugin-local state — so it belongs beside the other
poll-and-record helpers already in `testoperations`, not local to one
plugin.

**Affected**: No existing protocol or driver signature changes. The
consumer is any WAN-edge / SD-WAN appliance test that must assert
reachability convergence from a probe device after a change (a firewall
rule push, a VPN role flip, a static-route withdrawal) and needs the
convergence evidence — not just a pass/fail gate — to back the assertion.

**Neutrality evidence**: The reviewed managed-appliance families — Meraki
MX, Catalyst SD-WAN, FortiGate, Prisma SD-WAN, and Arista SD-WAN (the
VeloCloud Edge) — each terminate ordinary IP interfaces that answer a
probe device's ICMP echo, TCP handshake, or UDP exchange the same way any
IP host does; the vendor control-plane API is not on the reachability path
at all, so the operation holds uniformly without a driver-side translation
layer.

- Meraki MX: LAN/WAN interfaces configured through the dashboard's VLAN and
  uplink surfaces present standard IP endpoints — an ICMP echo, a TCP
  three-way handshake, or a UDP exchange against an MX-fronted address
  follows ordinary IP behaviour, independent of the Meraki dashboard API.
- Catalyst SD-WAN: service-VPN parcel-defined WAN/LAN interfaces terminate
  standard IP; the same three probe methods apply against a
  Catalyst-fronted address without involving the Manager API.
- FortiGate: `cmdb/system/interface` objects present ordinary IP
  endpoints; a probe device's reachability check against a
  FortiGate-fronted address is plain ICMP/TCP/UDP, not a FortiOS API call.
- Prisma SD-WAN: element interface / LAN-network objects present standard
  IP endpoints for the same three probe methods, independent of the Prisma
  Orchestrator API.
- Arista SD-WAN (VeloCloud Edge): `deviceSettings`-defined WAN/LAN
  interfaces present ordinary IP endpoints; the family's own review already
  records link state as observable from outside the vendor API, and the
  same holds for basic ICMP/TCP/UDP reachability.
