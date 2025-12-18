# US_EPOS_TEST_20251217 — Bug Summary and Fixes

This document summarizes each issue observed in US_EPOS_TEST_20251217.txt and the corresponding fix applied in the ePOS codebase, with notes on validation and commit references.

## 1) Meal totals omitted paid extras
- Symptom: Ordering a meal (e.g., Chkn BBQ Texan) with a paid extra (e.g., “Xtr Bacon”) persisted the extra on the order line meta but the server-side recomputed meal price excluded the extra, leading to a lower backend total.
- Root cause: Server recomputation for meal price didn’t add `meta.extras_products` values when overriding client-side price.
- Fix: Include paid extras (authoritative pricing from `PdItem` at the active band) when recomputing meal unit price in `api_submit_order`.
- Files: `manage_orders/views.py`
- Validation: Added regression unit test ensuring extras are included in meal recompute; full test suite stayed green.
- Commit: 6f65e2fb71d3f8a237883eb59ea8dc5b8caedf19

## 2) Daily Sales: add Total Sales excluding Crew/Waste
- Symptom: Report endpoint only returned Total Gross; requirement was to also show Total Sales = Total Gross − Crew Food − Cooked Waste.
- Fix: Update `/api/daily-sales` to compute and return `total_sales` alongside `crew_food_gross` and `waste_food_gross`. Update the Reports UI to display the new field.
- Files: `manage_orders/views.py`, `templates/manage_orders/reports.html`
- Validation: Full test suite stayed green; manual check in Reports UI.
- Commit: 721dc31aa556fe20b94a1f1c8ec667790a80e66b

## 3) Voucher mapping and split payments
- Symptom: Voucher amounts should accumulate in RV as token value (`TTOKENVAL`), including split payments (voucher/cash/card).
- Fix: In daily stats aggregation, map `payment_method='voucher'` to `TTOKENVAL`. For split payments, allocate `split_voucher_pence` to `TTOKENVAL` and cash/card parts to their buckets.
- Files: `manage_orders/services/daily_stats.py`
- Validation: Parity tests for revenue fields passed; manual checks confirm mapping behavior.

## 4) Paid Out subtracts cash
- Symptom: Paid Out transactions should record in `TPAYOUTVA` and reduce cash (`TCASHVAL`).
- Fix: Treat order `payment_method='Paid Out'` as leaving the till: add to `TPAYOUTVA` and subtract the same amount from `TCASHVAL`.
- Files: `manage_orders/services/daily_stats.py`
- Validation: Aggregation tests covering revenue fields passed.

## 5) Staff/Waste VAT exclusion in KWkVat (record staff/waste NET in RV)
- Symptom: KWkVat should exclude Crew Food and Cooked Waste from VAT totals; RV still needs total VAT due overall and net totals for staff/waste.
- Fix: VAT pass aggregates per-class VAT for non-staff/waste lines; separately accumulates staff/waste EX‑VAT totals to `KRev.TSTAFFVAL` and `KRev.TWASTEVAL`. RV `VAT` is the sum of all due VAT; KWkVat per-rate excludes staff/waste.
- Files: `manage_orders/services/daily_stats.py`
- Validation: Parity tests for KWkVat/RV passed.

## 6) Combo discount recorded ex‑VAT and component counting
- Symptom: Combination discount (`TDISCNTVA`) must be calculated as components EX‑VAT sum minus combo EX‑VAT; compulsory and selected optional components should count under their product codes.
- Fix: Expand combos to compulsory + selected optional components; compute EX‑VAT totals by component VAT classes; subtract combo EX‑VAT by combo VAT class. Count component products under service basis.
- Files: `manage_orders/services/daily_stats.py`
- Validation: Parity tests expecting specific `TDISCNTVA` values (e.g., 208 pence in crew combo case) passed.

## 7) Meal discount recorded ex‑VAT and component counting
- Symptom: Meal discount (`TMEAL_DISCNT`) must be calculated as singles EX‑VAT minus meal EX‑VAT; fries/drink should count under their own product codes for PD.
- Fix: Compute EX‑VAT for burger + fries + drink at standard prices and meal component prices using current basis classes; record the difference. Increment fries/drink basis counts.
- Files: `manage_orders/services/daily_stats.py`
- Validation: Parity tests expecting specific `TMEAL_DISCNT` values (e.g., 83 pence in crew meal case) passed.

## 8) Sharing Platter (Combo 4) dip classification
- Symptom: Two free dips: first should count under service basis, second under `OPTION`; Dip None (code 110) should remain under basis, not `OPTION`. Additional dips beyond the first two should count under `OPTION`, with the same 110 exception.
- Fix: Special handling for combo code 4:
  - First free dip → basis
  - Second free dip → `OPTION` unless 110 (then basis)
  - Additional dips → `OPTION` unless 110 (then basis)
- Files: `manage_orders/services/daily_stats.py`
- Validation: Parity tests around Sharing Platter passed.

## 9) Product extras VAT apportion and PD counts
- Symptom: Extras attached to product lines must be counted under their own product codes and VAT apportioned by each extra’s VAT class, with the remainder applied to the main product’s class.
- Fix: For product lines, parse `meta.extras_products` and allocate gross per extra at its VAT rate; remaining gross goes to the main product’s VAT class. Count extras in PD under basis.
- Files: `manage_orders/services/daily_stats.py`
- Validation: Aggregation tests for VAT split and PD counts passed.

## 10) Go Large tracking
- Symptom: Go Large occurrences must be counted.
- Fix: Increment `TGOLARGENU` when `line.meta.go_large` is set for meal lines.
- Files: `manage_orders/services/daily_stats.py`
- Validation: Tests around Go Large and meal discount passed.

## 11) Kids’ meal default optional product (P_CHOICE)
- Symptom: When a meal (e.g., kids’ burger) is ordered without explicit free choices, a default optional product (e.g., ketchup) should still be counted in PD `OPTION`.
- Fix: When a meal line has no `free_choices`, look up `PChoice(PRODNUMB=burger_code)` and increment `OPTION` for the mapped product; skip Dip None (110) from `OPTION` (keep under basis).
- Files: `manage_orders/services/daily_stats.py`
- Validation: Full suite remained green; manual verification planned in E2E.
- Commit: Included in latest changes on main (post 2025‑12‑18).

## 12) Payment method normalization
- Symptom: UI payment button labels vary in whitespace/underscore usage; mapping should be robust.
- Fix: Normalize `payment_method` by trimming and collapsing whitespace; accept both spaces and underscores when mapping (e.g., `crew food` and `crew_food`).
- Files: `manage_orders/services/daily_stats.py`
- Validation: Parity tests across payment methods passed.

---

### Test and validation status
- Full Django test suite: PASS (23 tests).
- Regression test added for meal extras inclusion.
- Manual E2E checks:
  - New order persisted with extras recorded; admin shows `extras_products` and updated totals.
  - Reports UI displays Total Sales field.

### References
- App running: http://127.0.0.1:8090/
- Key commits:
  - 6f65e2fb71d3f8a237883eb59ea8dc5b8caedf19 — Include paid extras in meal recomputation (and add test)
  - 721dc31aa556fe20b94a1f1c8ec667790a80e66b — Reports: add Total Sales excluding Crew/Waste

### Notes
- Discounts remain recorded in EX‑VAT terms (`TMEAL_DISCNT`, `TDISCNTVA`) to match parity tests and US info pack expectations.
- If a gross “saved” value is required for reporting, consider a configurable mode flag to compute and expose gross discounts without breaking existing EX‑VAT flows.
