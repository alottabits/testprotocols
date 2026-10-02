# Uplink fail-over criterion on uplink-selection rules

| Field | Value |
| --- | --- |
| Date | 2026-10-02 |
| Use case | `UC-016` — steer selected overlay traffic to a preferred uplink and verify it fails over when that uplink's performance class is breached, or only when the uplink is lost |
| Round | 1 |
| Status | `under review` |

### P1 — model fail-over criterion on `UplinkSelectionRule`

**Item**: `P1`, model.

**Need**: An uplink-selection rule must say which condition releases a flow from its preferred uplink: a breach of a performance class, or only the loss of the uplink. Test code arranges rules of each kind, and must restore the as-found rule list without changing any rule it did not arrange, so a read has to carry the criterion back to the write unchanged.

Checked against the existing contract:

- `testprotocols.models.sdwan_appliance:UplinkSelectionRule` already encodes the criterion. With `performance_class` set, the flow fails over when the class is breached. With `performance_class=None`, the preference is static and fails over only on uplink loss.
- No `testoperations` operation reads or writes uplink selection, so no operation overlaps or needs a change.
- `docs/architecture/typed-path-steering-protocol-design.md` records the decision "No `FailoverCriterion` enum. Both evidenced cases are covered by `performance_class` present/absent; grow on evidence."
- The route with no contract change works. A driver derives the vendor's criterion on write from class presence, maps it back on read by the same rule, and fails the read if the device returns a combination outside that bijection. Round trips are lossless while the bijection holds, and a violation surfaces as an error rather than a silent rewrite.

This proposal records that outcome, so the need is not raised again without the evidence the recorded decision asks for.

**Proposed design**: No contract change. A driver whose family carries an explicit per-rule criterion does three things:

- **On write**, it emits the performance-failover criterion when `performance_class` is set, and the uplink-loss criterion otherwise.
- **On read**, it accepts a returned criterion only when it agrees with class presence, and raises on a contradictory combination.
- **On a read with the criterion absent**, it derives the criterion from class presence alone.

`UplinkSelectionRule` and the `get_uplink_selection` / `set_uplink_selection` pair are unchanged. The write stays verifiable through the existing read (question 8), and no type changes (question 9).

**Mechanism**: `driver-only`
The need is met inside the driver by the derivation above. A `defaulted field` (rung 3) would add a second encoding of a dimension `performance_class` already carries. It would also admit contradictory states (performance failover with no class, uplink-loss failover with a class), and reopen the recorded decision without new evidence.

**Placement**: **keep local** — the derivation lives in the consumer's driver. Trigger: a reviewed family's device is observed to store and return, as restorable state, an overlay rule whose criterion contradicts class presence (uplink-loss failover with a class attached, or performance failover without one). The driver's consistency check raises on exactly that read, so the trigger is observable in the consumer's runs. When it fires, a new proposal cites this one and brings the observed state as the evidence the recorded decision asks for.

**Affected**: no existing symbol, consumer or published driver changes. One consumer driver carries the derivation and its consistency check.

**Neutrality evidence**: The domain's reviewed-family list and its cross-vendor concept check are recorded in `docs/architecture/typed-path-steering-protocol-design.md` ("Cross-vendor concept check"). Per family, how the criterion is expressed:

| Family | How the fail-over criterion is expressed |
| --- | --- |
| Meraki MX | an explicit per-rule `failOverCriterion` on overlay preferences, required on write in practice: a write without it was rejected live with `400 Bad Request` naming the missing attribute, although the published schema marks it optional. Its values pair one-to-one with class presence. |
| FortiGate | entangled in the service rule's mode (SLA-driven versus manual or priority), which also encodes member selection; SLA-driven mode is the one that carries SLA targets |
| Catalyst SD-WAN | implied by an SLA class on the app-route sequence versus a plain preferred colour |
| Prisma SD-WAN | implied by attaching performance-policy thresholds |
| VeloCloud | not expressible: per-class SLAs are fixed, and a driver raises unsupported when `performance_class` is set (design document, concept check) |

Three of five families (FortiGate, Catalyst SD-WAN, Prisma SD-WAN) express the criterion only through the presence of a performance class or SLA targets, which is the encoding the model already has. The one family with an explicit attribute (Meraki MX) maps onto it one-to-one, and the fifth (VeloCloud) cannot express performance-class failover at all. No family needs a separate field. The family evidence above restates the review of an earlier request for this field, held in the consumer's records. That review declined the field and recommended the driver derivation this proposal records.
