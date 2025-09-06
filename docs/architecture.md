# ePOS Architecture Overview

## Purpose
End-to-end overview of how the menu, configuration, pricing, and ordering flows work across frontend (template + JS) and backend (Django views + models), including data sources and server-side enforcement.

## High-Level Flow
1. User opens Order screen (`app_prod_order.html`).
2. Frontend requests category list for selected price band.
3. User selects a category; items (products + combos) are fetched on demand and cached per category.
4. Selecting/Clicking an item either adds it directly to basket or opens the configuration modal (variants, meal conversion, options, combo structure).
5. Basket accumulates lines using a deterministic signature (merges identical configurations).
6. Checkout modal collects payment method & crew ID; order submission posted to backend.
7. Backend validates payload and recomputes any meal prices authoritatively before persisting.

---
## Frontend (app_prod_order.html)

### Key State Variables
- `currentBand`: Active price band ("1".."6").
- `vatBasis`: 'take' or 'eat' for net price calculations.
- `showNet`: Toggle to display net (ex VAT) prices.
- `categories`: Array of category objects received from backend.
- `catItemsCache`: Map of category id -> list of item objects (products/combos) to avoid refetching.
- `currentItems`: Items currently displayed (selected category).
- `activeCategoryId`: Currently selected category ID.
- `basket`: `{ lines: [], total: 0 }` with each line containing product/combo metadata.
- `cfg`: Modal config state (variant, meal flags, selected fries/drink, options, effective price).

### Category & Item Loading
1. `fetchMenu()` calls `/api/menu/categories?band=<band>`.
2. Renders horizontal strip of category buttons (`renderCategories()`).
3. `selectCategory(id)` fetches items if not in `catItemsCache` via `/api/menu/category/<id>/items?band=<band>`.
4. Items are rendered as Bootstrap cards with deterministic color accent (hash of code/name) and variant/meal/discount badges.

### Pricing Display Logic
- Price fields returned already include: `price_gross`, `price_net_take`, `price_net_eat`, plus discounted (meal) counterparts when applicable.
- UI chooses correct field based on `showNet` and `vatBasis`.

### Configuration Modal
Displayed when item requires extra input (combo, variants, meal_flag, or options present).
Sections:
- Variants (double/triple or trade-up combo) -> set base price.
- Meal Section (for meal_flag products): fries & drinks selection + Go Large logic using `T_DRINK_CD` mapping to large drink code.
- Product Options (from `/api/product/<code>/options` fallback if not in detail payload).
- Combo structure: compulsory vs optional components + free optional heuristic.
- Extras Tab: isolates optional/extra selections from core configuration when present.

### Meal Price Computation (Client View)
Client computes provisional meal price by summing discounted component prices (burger variant, fries, drink) using any `discounted_price_gross` values present, falling back to standard prices if discounted is zero/absent. This is advisory only—server recomputes.

### Basket Logic
- Each line signature: `code|variant|mealFlag|fries|drink|sortedOptionCodes` to merge duplicates.
- `display_choices` human-readable summary (e.g., Fries: Regular, Drink: Coke, Xtra Cheese).

### Order Submission
Payload fields:
```
{
  price_band, vat_basis, show_net,
  payment_method, crew_id,
  lines: [ { code, type, name, variant, meal, qty, price_gross, meta: { fries, drink, options:[...], ... } } ]
}
```
POST to `/api/order/submit` with CSRF token.

---
## Backend (Django)

### Core Models Used
| Concern | Table / Model | Purpose |
|---------|---------------|---------|
| Categories | `GroupTb` | Menu category definitions (GROUP_ID, NAME, SOURCE_TYPE) |
| Menu membership (products) | `AppProd` | Associates product code with GROUP_ID, meal metadata, variant codes (double/triple) |
| Menu membership (combos) | `AppComb` | Associates combo code with GROUP_ID (and reporting order) |
| Product master | `PdItem` | Product pricing per band, VAT classes, meal related flags (MEAL_DRINK, T_DRINK_CD) |
| Combo master | `CombTb` | Combination pricing & trade-up combo reference (T_COMB_NUM) |
| VAT Rates | `PdVatTb` | VAT_CLASS -> rate mapping used for net calculations |
| Product options | `PChoice` | Per-product optional product links |
| Combo components (compulsory) | `CompPro` | Mandatory product codes for a combo |
| Combo components (optional) | `OptPro` | Optional product codes for a combo |

### Price Band Column Mapping
Helper `_price_column_name(band, discounted)` resolves to:
- Standard: `VATPR` (band 1) or `VATPR_<band>`
- Discounted meal: `DC_VATPR` (band 1) or `DC_VATPR_<band>`

### Endpoints
1. `/api/menu/categories` → `api_menu_categories`
   - Aggregates counts from `AppProd` + `AppComb` grouped by `GROUP_ID`.
2. `/api/menu/category/<id>/items` → `api_category_items`
   - For the specific group: loads `AppProd` rows then matching `PdItem` rows, and `AppComb` rows then `CombTb` rows; serializes both.
3. `/api/item/product/<code>/detail` & `/api/item/combo/<code>/detail` → `api_item_detail`
   - Products: merges `_serialize_product` + options via `PChoice` + heuristic meal components (fries codes [30,31], drinks where `MEAL_DRINK>0`).
   - Combos: `_serialize_combo` + compulsory/optional components from `CompPro` / `OptPro` + free optional heuristic (dip detection).
4. `/api/product/<code>/options` → `api_product_options` fallback for options query.
5. `/api/order/submit` → `api_submit_order`
   - Validates lines; recomputes meal price server-side ignoring client total.
6. (Ancillary) summary, pending, completion endpoints for order lifecycle.

### Serialization Helpers
- `_serialize_product`: builds unified dict with gross & net prices (take/eat), discount flag, variants, meal flag, `T_DRINK_CD`.
- `_serialize_combo`: similar for combos (variants for trade-up combo).

### Server Meal Price Enforcement
`_compute_meal_price` inside `api_submit_order`:
- Collects burger, fries, drink, and option product rows (`PdItem`).
- Component price = discounted (DC_) price if non-zero else standard.
- Meal unit price = burger + fries + drink + (sum standard prices of options).
- Overrides any client `price_gross` for meal lines.

### VAT / Net Calculation
- Per line VAT class chosen from TAKE_VAT_CLASS or EAT_VAT_CLASS based on submitted `vat_basis`.
- Net price derived at save time for order totals.

---
## Sequence Diagram (Conceptual)
```
User -> Frontend: Load order page
Frontend -> Backend: GET /api/menu/categories?band=1
Backend --> Frontend: Category list
User -> Frontend: Click category X
Frontend -> Backend: GET /api/menu/category/X/items?band=1
Backend --> Frontend: Items list
User -> Frontend: Click item (needs config)
Frontend -> Backend: GET /api/item/product/123/detail?band=1
Backend --> Frontend: Product detail (options, meal components)
User -> Frontend: Configure + Add to basket
User -> Frontend: Checkout
Frontend -> Backend: POST /api/order/submit (lines, meta)
Backend -> Backend: Recompute meal prices
Backend --> Frontend: { order_id, total_gross }
```

---
## Caching Strategy (Client)
- Category list cached for current band until band changes.
- Item lists cached per category id in `catItemsCache`.
- Changing band resets caches and reloads categories.

## Integrity Measures
- Server authoritative meal pricing (prevents client tampering).
- Line signature prevents accidental duplicate lines with identical config.
- Net price toggle does not alter server computation, it’s a display-only concern.

## Known Heuristics / Technical Debt
- Meal components: hard-coded fries codes [30,31] & drinks where `MEAL_DRINK>0`.
- Free optional detection for combos: simple 'dip' keyword heuristic.
- Options for combos not free-limited beyond heuristic.

## Potential Improvements
1. Replace fries/drink heuristics with explicit relational tables (e.g., `MealComponent` model).
2. Cache layer (Redis) for serialized category + item JSON to reduce DB hits.
3. Precompute and store variant + meal component arrays materialized daily.
4. Add unit tests for `_compute_meal_price` edge cases (missing discounted price, zero values).
5. Implement real rule engine for free optional limits per combo.
6. Extend options retrieval to include Extras model when integrated into UI.
7. Introduce pagination or virtual scrolling for very large categories.

## Glossary
- Band: Price tier selecting which VATPR/DC_VATPR column set to use.
- Meal Flag: Derived from `AppProd.MEAL_ID > 0`; means item can form a meal with fries + drink.
- Variant: Alternative size/quantity (double/triple burger, trade-up combo).
- Optional Product: Add-on linked via `PChoice` or `OptPro`.
- Meal Components: Burger + Fries + Drink combination used to compute discounted meal price.

---
## Quick Reference: Key Tables to UI Fields
| UI Element | Backend Source |
|------------|----------------|
| Category button label | `GroupTb.GROUP_NAME` |
| Item card name | `PdItem.PRODNAME` or `CombTb.DESC` |
| Item card price | `PdItem.VATPR*` / `CombTb.VATPR*` (band mapped) |
| Meal badge | `AppProd.MEAL_ID > 0` |
| Variant badges | `AppProd.DOUBLE_PDNUMB` / `TRIPLE_PDNUMB`, `CombTb.T_COMB_NUM` |
| Options list | `PChoice` → linked `PdItem` rows |
| Combo compulsory list | `CompPro` → linked `PdItem` |
| Combo optional list | `OptPro` → linked `PdItem` |
| Go Large drink mapping | `PdItem.T_DRINK_CD` (on selected drink) |

---
## Changelog (Architecture Doc)
- 2025-09-06: Initial version documenting existing flows and models.

