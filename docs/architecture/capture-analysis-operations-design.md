# Capture-analysis operations — family design

| Field | Value |
| --- | --- |
| Status | Accepted (proposal review, 2026-08-12) |
| Date | 2026-08-12 |
| Home | `testoperations` (`path_placement`, `marking_observation`, private `_capture`) |

## The family

Operations that read evidence off a wire vantage by composing the
`PcapCapture` capability: a bounded capture, then tshark field reads over
the finished file, returning **facts, never verdicts** (counts,
histograms, traces — the caller judges). Members:

- `path_placement` — stream placement by packet-size signature
  (2026, first member; promoted at first use).
- `marking_observation` — per-flow DSCP histograms (2026-08-12; accepted
  on proposal review with the conditions recorded below).

## Rules the family carries

1. **Home.** Capture analysis is device-, vendor- and testbed-agnostic
   wire analysis over an existing public capability; new members land in
   `testoperations`, not in consumer repos and not as capability
   protocols. `PcapCapture` itself stays a lifecycle-plus-raw-read
   surface — analysis never migrates into the capability.

2. **The private bracket.** The shared mechanic lives once, in the
   private `_capture` module, as composable primitives:
   `capture_shared_window` (every capture started before any stops — the
   multi-vantage shared window is the general case, a single vantage its
   N=1 case) and `read_fields` (per-filter field reads, file removed on
   the last). Public operations compose the primitives; no member carries
   its own copy of the bracket. *Why primitives rather than a monolithic
   helper:* a single-vantage bracket composed per path would serialize
   the windows and break the one-shared-window discipline the multi-path
   operations exist to provide — the ordering is the bracket's contract,
   so the bracket owns it for any N.

3. **No tool tokens in public signatures.** Display filters, tshark field
   names, and occurrence/separator switches are the operations' private
   concern. Public inputs use shared vocabulary (`RuleProtocol`,
   dataclass selectors with plain address literals); the enum→token
   mapping lives inside the operation (`RuleProtocol.ICMP6` → tshark's
   `icmpv6` is the standing example of why). No field-parameterized
   public operation (`observe_flow_field(...)`) is offered — that would
   put tool tokens back in the API.

4. **Field extraction is occurrence-pinned.** Field reads pin
   `-E occurrence=f` (first = outermost occurrence) and an explicit
   separator: frames carrying several IP headers (ICMP errors quoting the
   offender, IP-in-IP) otherwise emit aggregated values and miscount. The
   IPv4/IPv6 merge is **outermost-header-wins**, keyed on the frame's
   protocol chain — at an encapsulated vantage the family reads
   outer-header values, and what an outer value implies about inner
   marking is the caller's (possibly vendor-conditioned) interpretation.

5. **Fail-loud selectors.** Selector dataclasses validate at
   construction (address literals, one address family, ports only on
   port-bearing transports) — a mis-declared selector surfaces where it
   is declared, never as a silent zero-count mid-operation.

6. **Growth on evidence.** New markings (ECN and others) arrive as
   intent-named sibling operations when a test needs them — logged in
   `GAPS.md` until then; family growth is a fresh proposal by convention.
