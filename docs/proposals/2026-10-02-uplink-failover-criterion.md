# Uplink fail-over criterion on uplink-selection rules

| Field | Value |
| --- | --- |
| Date | 2026-10-02 |
| Use case | `UC-016` — steer selected overlay traffic to a preferred uplink and verify it fails over when that uplink's performance class is breached, or only when the uplink is lost |
| Round | 2 |
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

**Proposed design**: No contract change. A driver whose family carries an explicit per-rule criterion does the following:

- **On write**, it emits the performance-failover criterion when `performance_class` is set, and the uplink-loss criterion otherwise.
- **On read**, it accepts a returned criterion only when it agrees with class presence, and raises on a contradictory combination.
- **On a read with the criterion absent**, it derives the criterion from class presence alone.
- **Scope (C1).** On a family whose criterion and performance-class attributes exist only on the overlay surface, performance-class steering is overlay-only. An `INTERNET`-scope rule carrying `performance_class` raises unsupported-capability rather than being written without its criterion. This is the convention `set_uplink_selection` already states.
- **A class name that resolves to no configured `SLAPolicy` (C2)**, such as a product built-in, raises on read. It is not carried verbatim. The contract defines `performance_class` as the name of an `SLAPolicy` configured through `configure_sla_policy`, and a name outside that set could be read but not written back through `set_uplink_selection`. A faithful restore of such a rule is therefore not possible on the current contract, and a loud read failure keeps the run from reporting a restore it cannot make. Carrying built-in classes is a separate need, for its own proposal if a test requires it.

`UplinkSelectionRule` and the `get_uplink_selection` / `set_uplink_selection` pair are unchanged. The write stays verifiable through the existing read (question 8), and no type changes (question 9).

**Mechanism**: `driver-only`
The need is met inside the driver by the derivation above. A `defaulted field` (rung 3) would add a second encoding of a dimension `performance_class` already carries. It would also admit contradictory states (performance failover with no class, uplink-loss failover with a class), and reopen the recorded decision without new evidence.

**Placement**: **keep local** — the derivation lives in the consumer's driver. Trigger: a reviewed family's device is observed to store and return, as restorable state, an overlay rule whose criterion contradicts class presence (uplink-loss failover with a class attached, or performance failover without one). The driver's consistency check raises on exactly that read, so the trigger is observable in the consumer's runs. The check runs on the as-found capture, before any write (C4), so a contradictory rule is detected while the rule list is still as found, and the trigger fires without the run having modified anything. When it fires, a new proposal cites this one and brings the observed state as the evidence the recorded decision asks for.

**Affected**: no existing symbol, consumer or published driver changes. One consumer driver carries the derivation and its consistency check.

**Neutrality evidence**: The domain's reviewed-family list and its cross-vendor concept check are recorded in `docs/architecture/typed-path-steering-protocol-design.md` ("Cross-vendor concept check"). Per family, how the criterion is expressed:

| Family | How the fail-over criterion is expressed |
| --- | --- |
| Meraki MX | an explicit per-rule `failOverCriterion` on overlay preferences, required on write in practice: a write without it was rejected live with `400 Bad Request` naming the missing attribute, although the published schema marks it optional. The schema also permits a performance class alongside either criterion value, so the one-to-one pairing with class presence is enforced by the driver, not by the API (C3). The contradictory combination is reachable through the published surface, which is what makes the trigger in **Placement** a real one. |
| FortiGate | entangled in the service rule's mode (SLA-driven versus manual or priority), which also encodes member selection; SLA-driven mode is the one that carries SLA targets |
| Catalyst SD-WAN | implied by an SLA class on the app-route sequence versus a plain preferred colour |
| Prisma SD-WAN | implied by attaching performance-policy thresholds |
| VeloCloud | not expressible: per-class SLAs are fixed, and a driver raises unsupported when `performance_class` is set (design document, concept check) |

Three of five families (FortiGate, Catalyst SD-WAN, Prisma SD-WAN) express the criterion only through the presence of a performance class or SLA targets, which is the encoding the model already has. The one family with an explicit attribute (Meraki MX) maps onto it one-to-one under the driver-enforced pairing, and the fifth (VeloCloud) cannot express performance-class failover at all. No family needs a separate field. The family evidence above restates the review of an earlier request for this field, held in the consumer's records. That review declined the field and recommended the driver derivation this proposal records.

---

## Review response (testprotocols review team, 2026-10-02)

| Item | Decision | Reason |
| --- | --- | --- |
| P1 | accept with conditions | Right rung and in line with the recorded decision; the derivation it records is under-specified on three points the restore requirement in its own Need turns on. |

### 0. Neutrality

Met. No organisation, customer, site, hostname, address, person or ticket
identifier anywhere in the document. Vendor names (five appliance families)
appear only inside **Neutrality evidence**; the `400 Bad Request` quoted
there is a status line, not an address or an endpoint. The use-case id
`UC-016` is the allowed traceability key. The reference to "an earlier
request for this field, held in the consumer's records" names no consumer
and no ticket — acceptable, though it cites a record this repository cannot
read, so the family table below it has to carry the argument on its own. It
does.

### 1. Recorded decisions

Met. `docs/architecture/typed-path-steering-protocol-design.md` records,
under "Decisions recorded": *"No `FailoverCriterion` enum. Both evidenced
cases are covered by `performance_class` present/absent; grow on
evidence."* P1 does not reopen it — it confirms it and supplies the family
survey the "grow on evidence" clause was waiting for. The model docstring
in `models/sdwan_appliance.py:555` already states the same semantics
(class set → fails over on breach; `None` → static, fails over on uplink
loss), so the driver derivation P1 describes is reading the contract as
written rather than inventing a convention.

A proposal that records a *non*-change is the right instrument here. At
merge the maintainer writes the keep-local pointer into
`packages/testprotocols/GAPS.md` naming this proposal path and these
conditions (`docs/proposals/README.md`, "Merge") — that, not the proposal
file, is what stops the need being raised a third time.

### 2. Vendor and tool neutrality

Met. The domain has a recorded reviewed-family list — the "Cross-vendor
concept check" table in the typed-path-steering design document (Meraki MX,
Catalyst SD-WAN, FortiGate, Prisma SD-WAN, Arista/VeloCloud). P1 uses
exactly that list, not an improvised one, so nothing needs ratifying.

The derivation holds per family on the list:

- the four families that express the criterion implicitly (class presence,
  SLA targets, SLA-class list, performance thresholds) are a direct
  mapping;
- the family that cannot express performance-class failover at all already
  raises unsupported-capability when `performance_class` is set, per
  `sdwan_policy_manager.py:82-91` and the design document's error-handling
  section — the derivation degenerates to its uplink-loss branch, which is
  correct, not a gap;
- the one family with an explicit attribute is the hinge, and is checked
  below.

### 3. Placement ladder walked

Met, on the cheapest rung. **Mechanism `driver-only`** (rung 1) matches the
design: nothing in `testprotocols` or `testoperations` changes, and the
rejection of rung 3 is sound on the evidence. A defaulted
`failover_criterion` field would be a second encoding of the dimension
`performance_class` already carries, and would make two contradictory
states representable in the contract that no family can realise. I searched
`PUBLIC_MAIN` and `INDEX` for a rung P1 missed and found none below rung 1.

### 4. Correct home

Met — plugin-local. The derivation is vendor mapping: it reads a vendor
field name and a vendor enum, neither of which exists above the driver
boundary. It is not an operation under the framing litmus, and could not
become one: an operation over the contracts sees only
`performance_class: str | None` and so has nothing left to derive. If a
second family later needs the same mapping, it is still driver mapping in
two drivers, not a shared operation.

### 5. Overlap with capability protocols

Met. `UplinkSelectionRule` (`models/sdwan_appliance.py:555`) carries the
fact under the name `performance_class`; `SdwanPolicyManager` carries the
read/write pair. `UplinkSelectionSettings` and `set_active_active_vpn`
frame the rule list with network-wide scalars and do not encode a per-rule
criterion. No sibling protocol holds it.

### 6. Overlap with operations

Met, and the document's claim checks out. No `testoperations` module reads
or writes uplink selection. `testoperations.sdwan.measure_failover_convergence`
is the near miss by name only — it composes `NetemController.inject_transient`
with `Router.get_active_wan_interface` and never touches the steering
surface, which `SPLITS.md:351` also records. No consumer reconstructs the
criterion field by field.

### 7. One consumer, and why now

Met, as a keep-local item with a concrete trigger. P1 is not a promote
item, so no second-consumer substitute is required; what it owes instead is
a trigger that is observable, and this one is: *a reviewed family's device
returns, as restorable state, an overlay rule whose criterion contradicts
class presence*. That is a specific device state, not "if this becomes
painful", and the driver's own consistency check is the detector. Accepted
as keep-local.

One correction to how the trigger is argued. P1 says the explicit
attribute's "values pair one-to-one with class presence". I checked the
published schema for that family's uplink-selection update endpoint
(developer.cisco.com/meraki/api-v1, update network appliance traffic
shaping uplink selection). It shows `failOverCriterion` on the VPN
preference objects with the two values the document implies, marked
**optional**, and it permits a `performanceClass` object alongside *either*
value. So the pairing is a driver-enforced invariant, not an API-enforced
one. That strengthens the trigger rather than weakening it — the
contradictory state is reachable through the published surface, which is
exactly why the check has to be there — but the document should say so (C3).

The live-versus-published discrepancy P1 already flags (the write rejected
with `400` naming the attribute the published schema marks optional) is the
right thing to have recorded, and my fetch confirms the published half of
it: optional in the schema. Keep that sentence.

Two gaps in the recorded derivation, both reached from the Need's own
requirement to "restore the as-found rule list without changing any rule it
did not arrange":

- **Scope.** On that same family the explicit criterion and the performance
  class exist only on the overlay preference objects; the internet
  preference objects carry neither (the published field list has
  `trafficFilters` and `preferredUplink` only). `UplinkSelectionRule`
  carries `scope: SteeringScope` with both `INTERNET` and `OVERLAY`, so
  "on write, emit the performance-failover criterion when
  `performance_class` is set" has no realisation for an `INTERNET`-scope
  rule that carries a class. The contract already supplies the answer —
  `set_uplink_selection` says products that cannot express the rule raise
  unsupported-capability rather than approximate — but P1 does not say it
  (C1).
- **Unresolvable class names.** That family's performance class may be a
  product built-in as well as a user-defined one. The contract defines
  `performance_class` as *the name of an `SLAPolicy` configured via
  `configure_sla_policy`*, and `get_sla_policies` will not return a
  built-in. Criterion derivation is unaffected — the class is present
  either way — but the as-found capture is: a rule referencing a built-in
  class round-trips through a name the contract cannot resolve. P1's
  consistency check covers criterion-versus-class contradiction and is
  silent here (C2).

**Corpus impact.** No reference driver exists in the reference corpus at
the reviewed commit (`main`, `fb9343e`); no corpus archetype reaches
`SdwanPolicyManager`, and no matrix lists its members. Nothing to count,
and P1 adds or changes no member in any case.

### 8. Every write verifiable

Met. P1 adds and changes no member, so there is no new write to verify.
Members judged, both pre-existing and both unchanged by this item:

- `set_uplink_selection(rules: list[UplinkSelectionRule]) -> None` — the
  write. Its read is `get_uplink_selection() -> list[UplinkSelectionRule]`,
  returning the same model, so every field the write sets is readable back,
  the criterion dimension included. P1's claim that "the write stays
  verifiable through the existing read" is correct.
- `set_active_active_vpn`, `set_default_uplink` — read back by
  `get_uplink_selection_settings`; not touched here.

Noted, not blocking, because the item does not touch it: `set_uplink_selection`
is a whole-list replace, which at least one reviewed family realises in
more than one device step, and neither the protocol docstring nor the
design document states the failure outcome — whether a replace that fails
partway leaves the as-found list. That is a pre-existing contract gap and
belongs in its own proposal, not this one. What *is* in P1's gift is the
ordering of its own check: capture before arrange, so a contradictory
as-found rule raises while the list is still as found (C4).

### 9. Precise types

Met. P1 adds and changes no member or model, so there is nothing to type.
The fields its derivation reads are already precise:
`performance_class: str | None` is a name reference — an open value, so
`str` is right, not an `Enum` — and the absence meaning is stated in the
model docstring rather than left to a sentinel. `scope: SteeringScope` is
the closed set it should be.

Noted, not blocking, untouched by the item: `FlowMatch` uses the literal
`"any"` as its match-all for `src_cidr` / `src_port` / `dst_cidr` /
`dst_port`. It is a documented match-all mirroring `L3Rule`, not an
absence sentinel, and retyping it would be a rung-5 `deprecate` in a
separate proposal.

### Conditions

- **C1 (P1)** — In **Proposed design**, state the scope restriction: on a
  family whose criterion and performance-class attributes exist only on the
  overlay surface, performance-class steering is overlay-only, and an
  `INTERNET`-scope rule carrying `performance_class` raises
  unsupported-capability rather than being written without its criterion.
  This is the convention `set_uplink_selection` already states; the
  derivation just has to name it.
- **C2 (P1)** — In **Proposed design**, extend the read half to say what
  the driver does with a returned performance-class name that resolves to
  no configured `SLAPolicy` (a product built-in): carry it verbatim so the
  as-found restore is faithful, or raise. Say which, and why. The Need's
  restore requirement turns on it.
- **C3 (P1)** — In **Neutrality evidence**, restate the one-to-one pairing
  as driver-enforced rather than API-enforced: the published schema marks
  the criterion optional and permits a performance class with either
  value. Keep the live-rejection sentence; add that the contradictory
  combination is reachable through the published surface, which is what
  makes the trigger in **Placement** a real one rather than a formality.
- **C4 (P1)** — In **Placement**, state that the consistency check runs on
  the as-found capture before any write, so a contradictory rule is
  detected while the rule list is still as found and the trigger fires
  without the run having modified anything.
