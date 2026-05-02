# Capability granularity split log

Per the architecture rule: capability protocols bundle by coherent telco domain;
splits and merges land on tracked evidence (consumer signal, design review).
This file records the evidence.

Format per entry:

```
## YYYY-MM-DD — <protocol-or-method-set> moved <from> → <to>

**Signal:** <consumer-or-reviewer-quote-or-summary>
**Decision:** move / keep / defer
**Rationale:** <why>
**Migration impact:** <which consumers / tests / drivers needed updates>
```

---

## 2026-05-02 — MAC ACL methods moved `WifiStations` → `WifiBss`

**Signal:** During Task 9 (manual review and acceptance gate of the ABC →
Protocol migration), the reviewer flagged: *"Currently, set_acl_mode,
add_acl_entry, etc., live in WifiStations. While they do filter stations
(MACs), an ACL is fundamentally a configuration property of the BSS's
authorization scheme. It might conceptually belong in WifiBss alongside
set_security()."*

**Decision:** Move the 5 ACL methods from `WifiStations` to `WifiBss`.
Done as a separate commit on top of the Task 8 verbatim conversion.

**Rationale:**
- All 5 ACL methods were already keyed by BSS (`bss_name: str` was the first
  parameter on every one), not by station MAC. They configure the BSS's
  admission policy, not station state.
- Sit alongside `set_security` (WPA/WPA3/EAP authentication scheme) and
  `set_captive_portal` (post-association authorization) — same logical
  layer of "how does this BSS decide who gets in?".
- `WifiStations` retains only truly station-scoped operations:
  `list_associated_stations`, `get_station`, `disconnect_station`.
- Source ABCs in `palco-templates` had this granularity wrong; preserved
  verbatim by Task 8's mechanical conversion. The migration is the
  natural place to correct it before consumers depend on the bad shape.

**Methods moved (5):**
- `set_acl_mode` — `WifiStations.set_acl_mode(bss_name, mode)` → `WifiBss.set_acl_mode(name, mode)`
- `add_acl_entry` — `WifiStations.add_acl_entry(bss_name, mac)` → `WifiBss.add_acl_entry(name, mac)`
- `remove_acl_entry` — `WifiStations.remove_acl_entry(bss_name, mac)` → `WifiBss.remove_acl_entry(name, mac)`
- `clear_acl` — `WifiStations.clear_acl(bss_name)` → `WifiBss.clear_acl(name)`
- `get_acl` — `WifiStations.get_acl(bss_name) -> WifiAcl` → `WifiBss.get_acl(name) -> WifiAcl`

**Parameter rename:** `bss_name` → `name` for consistency with the rest of
`WifiBss` (every other method uses `name: str` as the BSS identifier).
No semantic change.

**Import migration:** `WifiAcl` (from `testprotocols.models.wifi`) moved
its only consumer from `wifi_stations.py` to `wifi_bss.py`.

**Migration impact at this point in the migration:**
- No drivers or operations consume these methods yet (testprotocols is
  pre-1.0; consumers will be updated in Phase 4-5 when palco-bdd
  examples flip to the new stack).
- Tests for `WifiStations` and `WifiBss` (Task 13's scope) will need to
  be split accordingly.

**Module docstrings updated** in both `wifi_stations.py` and `wifi_bss.py`
to reflect the new boundaries; the wifi_stations docstring includes a
forward reference: *"Per-BSS MAC ACL administration (set_acl_mode,
add_acl_entry, etc.) lives on the WifiBss template — see SPLITS.md
for the rationale."*
