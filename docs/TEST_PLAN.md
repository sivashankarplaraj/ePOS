# ePOS Test Plan (PD/RV/MP + VAT + UI)

Date: 2025-11-11
Owner: QA/Dev

## Scope
Covers end-to-end behavior for daily aggregations and exports:
- MP (KMeal), PD (KPro), RV (KRev) CSVs
- KWkVat VAT weekly snapshot (K_WK_VAT.csv)
- VAT basis (Eat-in/Takeaway) and crew/waste handling
- UI validations: free-choice gating, extras, meal variants, checkout flows

## Assumptions
- Price Band 1 (Walk In) used unless stated
- VAT classes from PdVatTb; basis from order VAT selection
- Crew Food and Waste food orders do not contribute VAT; record net in RV (TSTAFFVAL/TWASTEVAL)
- Free items chosen within combos do not increment OPTION; paid extras/optionals on products do

## Test Matrix

1) Product + Extra (TAKEAWAY)
- Steps: Cheeseburger + Xtr Mayo; pay Cash
- Expect:
  - PD: Cheeseburger TAKEAWAY+1; Xtr Mayo TAKEAWAY+1 and OPTION+1
  - RV: TCASHVAL += gross; VAT includes Mayo + main product split by classes
  - KWkVat: VAT and Net in correct classes; weekday slot updated

2) Combo with free choices (TAKEAWAY)
- Steps: Sharing Platter; select two dips as free choices; pay Cash
- Expect:
  - UI: Add disabled until both free-choice groups selected
  - PD: each compulsory and selected optional component TAKEAWAY+1; OPTION unchanged (0) for free dips
  - RV: TDISCNTVA reflects discount A-B using standard component prices vs combo price
  - VAT: apportioned across component classes by standard price weights

3) Crew Food order
- Steps: Cheeseburger, pay Crew Food, Crew ID set
- Expect:
  - PD: STAFF+1 for product; basis count increments
  - RV: TSTAFFVAL increased by net; VAT unchanged; ACTCASH/CARD mirrored as before
  - KWkVat: no change (crew VAT excluded)

4) Waste food order
- Steps: Cheeseburger, pay Waste food
- Expect:
  - PD: WASTE+1 for product; basis count increments
  - RV: TWASTEVAL increased by net; VAT unchanged
  - KWkVat: no change (waste VAT excluded)

5) Meal discount and Go Large
- Steps: Burger meal with fries+drink; toggle Go Large
- Expect:
  - KMeal (MP): burger code increments BASIS
  - PD: fries/drink components counted on BASIS; TGOLARGENU increments
  - RV: TMEAL_DISCNT increments by (sum singles std - sum meal comps)

6) VAT basis switch
- Steps: Repeat (1) as Eat-in
- Expect: VAT classes chosen via EAT_VAT_CLASS, not TAKE_VAT_CLASS

7) Weekly VAT export presence
- Steps: Run export_daily_csvs for date
- Expect: K_WK_VAT.csv exists with header and updated weekday columns only

## How to Run

- Place orders at http://127.0.0.1:8090/manage_orders/app_prod_order/
- Export CSVs:
  ```powershell
  python manage.py export_daily_csvs --date YYYY-MM-DD --outdir .\exports_tmp
  ```
- Inspect KRev quickly:
  ```powershell
  python manage.py inspect_daily --date YYYY-MM-DD
  ```

## Acceptance Criteria
- All expectations above met; unit tests pass
- RV file contains only one row with correct sums
- K_WK_VAT updated only for current weekday; values reflect non-crew/waste VAT

## Follow-ups
- Add Playwright UI automation (Python): pytest + playwright to exercise flows 1-4 and assert via inspect_daily/CSV parsing.
- CI hook to run Django tests + Playwright smoke on PRs.
