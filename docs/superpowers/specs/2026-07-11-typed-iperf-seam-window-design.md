# Typed iperf sender seam + pinned socket buffers (ENG-003 + `window`)

**Date:** 2026-07-11 · **Status:** approved (design) · **Target release:** testprotocols 0.4.1 (additive)

## Problem

Two distinct problems, one seam:

1. **Stringly-typed CLI seam (kpn-sdwan ENG-003).** `testoperations.throughput`
   composes raw iperf3 CLI fragments (`-R -O 3 --json`, see
   `_direction_fragment`) and passes them through
   `IperfClient.start_traffic_sender(direction=...)`, which every impl appends
   verbatim — no validation, quoting/order-sensitive, and every new option
   widens the untyped surface.
2. **TCP receive-autotuning stalls corrupt throughput rounds.** UC-010 live
   forensics (2026-07-11, MX450 sweep): sub-rated dip rounds show the sender's
   cwnd plateauing at 1.5–2.0 MB with zero retransmits and normal RTT — the
   *receiver's* advertised window (Linux dynamic right-sizing) stalls on the
   ~15 ms overlay path. Raising `tcp_wmem`/`tcp_rmem` maxima (2026-07-10 fix)
   did not cure this class: the limiter is the peer's window, not sender
   buffer space. The standard measurement-rig remedy is pinning the socket
   buffer (`iperf3 -w`), which disables autotuning on both ends (the client
   forwards `-w` to the server in the test-parameter exchange).

Adding `-w` through the raw fragment would deepen exactly the debt ENG-003
describes, so both land together.

## Design

### 1. Protocol (`testprotocols.iperf_client.IperfClient`) — additive

`start_traffic_sender` gains four typed keyword parameters, all defaulting to
"absent" (no flag emitted):

| Parameter | Type | iperf flag |
|---|---|---|
| `reverse` | `bool = False` | `-R` |
| `omit_s` | `int \| None = None` | `-O <n>` |
| `json_output` | `bool = False` | `--json` |
| `window` | `str \| None = None` | `-w <size>` (e.g. `"8M"`) |

`direction: str | None` **stays** as a deprecated escape hatch: docstring
marks it deprecated, impls append it verbatim *after* the typed flags.
Additive change → consumers pinning `>=0.4.0,<0.5.0` are unaffected.

### 2. `testoperations.throughput`

- `_direction_fragment()` is deleted.
- `ThroughputFlow` gains `window: str | None = None`.
- `measure_concurrent_throughput` / `measure_one_direction` /
  `measure_path_until` pass typed kwargs
  (`reverse=flow.reverse, omit_s=..., json_output=True, window=flow.window`)
  instead of a composed string. Mechanic stays here, policy (the window
  value) stays with the caller — same layering as `measure_path_until`.

### 3. kpn-sdwan impl (`IperfClientImpl._build_sender_cmd`)

Takes the typed params and composes flags in canonical order
(`-R`, `-O`, `-w`, `--json`), `direction` appended last if a caller ever
passes one. `-w` goes in both the iperf3 and legacy-iperf2 builders (both
support it). This is the **only** `IperfClient` implementation anywhere
(verified 2026-07-11: vitro-bdd examples either use the separate
`IperfGenerator` seam — sdwan-digital-twin — or stub iperf entirely), so the
ENG-003 row's assumed "twin wiring" does not exist; correct the row on close.

### 4. Policy: the window value (kpn-sdwan suite)

The suite's shared throughput steps set `window="8M"` on **saturating**
measurement flows only (UC-009/010 family); the 1 Mbps RTT probes stay
unpinned (non-saturating; autotuning irrelevant). Rationale, recorded at the
constant: BDP ≈ 870 Mbps × ~40 ms queue-inflated RTT ≈ 4.3 MB; 8M ≈ 2×
margin; the kernel doubles the setsockopt value; fleet
`net.core.rmem_max`/`wmem_max` = 16 MB (verified live — `setsockopt` is
capped by `net.core.*mem_max`, **not** `tcp_rmem`/`tcp_wmem`, so this
pre-condition is load-bearing).

### 5. Explicitly out of scope

- **Seam convergence on `IperfGenerator`** (raised 2026-07-11): the
  generator-style contract (typed spec in, structured result out) is the
  better end-state, but today it lacks `reverse`/`omit`/`window`, carries no
  TCP RTT evidence in `TrafficResult`, keeps server lifecycle outside the
  contract, and parses-and-discards the per-side JSON logs our forensics
  depend on. Converging means rewriting the live-proven UC-009/010
  measurement stack. Filed as a new kpn-sdwan engineering-backlog row
  instead.
- ENG-004 and the queued UC-008 refactor (same release window, separate
  changes).

### What this fixes / doesn't

Pinning removes dip **class A** (receiver DRS stall) by construction. Class B
(loss bursts at the path bottleneck) is untouched — cross-traffic
identification stays on the UC-010 queue. KPN methodology note: figures
measured with pinned buffers characterize the *path*, not client OS defaults.

## Testing

TDD throughout:

- testprotocols: unit tests for flag composition order/absence-by-default and
  throughput plumbing (typed kwargs reach the impl; fragment code gone).
- kpn-sdwan: `_build_sender_cmd` unit tests (typed flags, escape hatch,
  iperf2 branch), suite constant applied to saturating flows only.
- Live G4: re-run the 4 failed MX450 cells, then the full clean 13-cell
  sweep.

## Rollout

1. testprotocols branch → PR → v0.4.1 tag → OIDC trusted publish (manual
   approval; mind the uv stale-wheel-cache gotcha).
2. kpn-sdwan (branch `uc/010-spoke-hub-spoke-performance`): impl + policy +
   pin refresh in lockstep; engineering-backlog edits (close ENG-003 with the
   no-twin-wiring correction; add the seam-convergence row).
