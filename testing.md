## **Result of tests done on #codebase ePOS**

I ran the following orders on the #codebase ePOS system.

1) Sharing Platter ( Takeaway, Band 1 )
2) Sharing Platter with an extra dip ( Takeaway, Band 1 )
3) Sharing Platter ( Eatin, Band 1 )
4) Cheeseburger, Xtr Mayo ( Takeaway, Band 1 )
5) Cheeseburger, Xtr Mayo ( Eatin, Band 1 )
6) Cheeseburger ( Crew Food, Band 1 )
7) Hamburger ( Cooked Waste, Band 1 )
8) Must select a choice in the Free Choices section
9) MP, PD files

I have listed the queries as follows.

# 1. **Sharing Platter ( Takeaway, Band 1 )**

Order

- Sharing Platter £10.05 (C)
- Free dips : 27 - Dip Mayo, 39 - Dip BBQ

This combination product offers 2 free dips.

### Compulsory products for "4 Sharing Platter"

- 71 - Six Bites
- 82 - Onion Rings 8
- 95 - Mozarela fingers

### Optional products for "4 Sharing Platter"

- 26 - Dip Ketchup
- 27 - Dip Mayo
- 28 - Dip Chilli
- 29 - Dip Garlic Mayo
- 39 - Dip BBQ
- 101 - Dip 1000 Isle
- 110 - Dip None

Suppose we have ordered combination product "4 Sharing Platter" and have chosen the following dips from the list of optional products for this combination product
- 27 - Dip Mayo
- 39 - Dip BBQ

### Vat calculation
| Product Code | Product Name | Vat Class | Band 1 Price (A+B) | Vat Amount (A) | Value excl Vat (B) | New Vat Amount | New Value excl Vat |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 71  | Six Bites | 1   | 5.60 | 0.93 | 4.67 | 0.74 | 3.69 |
| 82  | Onion Rings 8 | 1   | 2.60 | 0.43 | 2.17 | 0.34 | 1.72 |
| 95  | Mozarela Fingers | 1   | 3.35 | 0.56 | 2.79 | 0.44 | 2.21 |
| 27  | Dip Mayo | 0   | 0.55 | 0.00 | 0.55 | 0.00 | 0.44 |
| 39  | Dip BBQ | 0   | 0.60 | 0.00 | 0.60 | 0.00 | 0.47 |
|     | TOTAL |     | 12.70 (D) |     |     | 1.52 (E) | 8.53 (F) |

| Vat Class | Vat Rate |
| -- | -- |
| 0   | 0.00 |
| 1   | 20.00 |


### How to calculate New Vat Amount and New Value excl Vat

A = Vat Amount

B = Value excl Vat
# Summary of fixes applied (2025-11-12)

- PD counting corrected for combinations and add-ons:
  - Compulsory items and chosen free options for a combo are counted as normal product sales under TAKEAWAY/EATIN (or STAFF/WASTE) — not in OPTION.
  - Priced extras (e.g., Xtr Mayo, Dip Garlic Mayo) are counted as their own product sales under the correct basis; OPTION is not incremented.
- RV values fixed:
  - TDISCNTVA now equals the combination discount: sum of component standard prices (D) minus the combo price (C).
  - VAT for combos is apportioned across components by their standard price weight and each component’s VAT class/rate.
  - Crew Food and Waste orders contribute NET amounts to TSTAFFVAL/TWASTEVAL and add zero VAT.
- MP/PD catalogue completeness: MP lists all products; PD lists all products and all combos (COMBO True/False), even when unsold.
- UI gating: Add to Basket remains disabled until required free choices are selected.

# Verification summary

- Integration (API) test: submits orders (combo cash, crew cheeseburger, waste hamburger) and validates PD counts and RV values — PASS.
- E2E (Playwright) test: places orders via UI, exports, and validates PD/RV — PASS.
- Sharing Platter single-order check: RV delta confirmed TDISCNTVA=265, VAT=152 for Takeaway, Band 1 — PASS.

C = Selling price of combination product = 10.05

D = Total price of individual products = 12.70

- New Vat Amount = A \* C / D
- New Value excl Vat = B \* C / D

**For example, for "Six Bites"**


Result after fixes (Takeaway, Band 1):
- PD: 27 (Dip Mayo) and 39 (Dip BBQ) increment TAKEAWAY (no OPTION increment). Combo line 4 increments TAKEAWAY with COMBO=True.
- RV: TDISCNTVA = 265 (D − C = 1270 − 1005), VAT = 152 (apportioned by component VAT class).
- Verified via single-order delta export.
- New Vat Amount = 0.93 \* 10.05 / 12.70 = 0.74
- New Value excl Vat = 4.67 \* 10.05 / 12.70 = 3.69

Vat amount for combination product "Sharing Platter" = £1.52 (E)

### How to calculate Combination Discount

Let

X = Amount due for all the compulsory products and the chosen optional products for the combination product

Y = Amount due for the combination product

Combination Discount = X - Y

So, the combination discount for this order 

\= D - C
\= £12.70 - £10.05
\= £2.65

### In PD file,

For record with COMBO = False and PRODNUMB

- 71 - Six Bites ( add 1 to column TAKEAWAY ) <- Correct
- 82 - Onion Rings 8 ( add 1 to column TAKEAWAY ) <- Correct
- 95 - Mozarela Fingers ( add 1 to column TAKEAWAY ) <- Correct
- 27 - Dip Mayo ( add 1 to column OPTION ) <- Error
  - We have to add 1 to column TAKEAWAY instead of OPTION.
- 39 - Dip BBQ ( add 1 to column OPTION ) <- Error
  - We have to add 1 to column TAKEAWAY instead of OPTION.

For record with COMBO = True and PRODNUMB
- 4 - Sharing Platter ( add 1 to column TAKEAWAY ) <- Correct

Please note that for combination products, the sales of each compulsory product and the chosen optional products (Dip Mayo and Dip BBQ in this case) are added to the cumulative sales of the corresponding products in the PD file.

### In RV file,

- TDISCNTVA = 150 <- Error ( Should be 265 )
- VAT = 167 <- Error ( Should be 152 )
- TDISCNTVA is amount of combination discount in pence on the given date.

---

# 2. **Sharing Platter with an extra dip ( Takeaway, Band 1 )**

Order

- Sharing Platter £10.05
- Free dips : 27 - Dip Mayo, 39 - Dip BBQ
- Extra dip : 29 - Dip Garlic Mayo £0.65
Suppose we have ordered combination product "4 Sharing Platter" and have chosen the following dips from the list of optional products for this combination product
- 27 - Dip Mayo
- 39 - Dip BBQ

Also, we have added an extra dip "29 Dip Garlic Mayo".

Please note that product "29 Dip Garlic Mayo" sold for takeaway is zero-rated for VAT (0%).

### In PD file,

For record with COMBO = False and PRODNUMB
- 71 - Six Bites ( add 1 to column TAKEAWAY ) <- Correct
- 82 - Onion Rings 8 ( add 1 to column TAKEAWAY ) <- Correct
- 95 - Mozarela Fingers ( add 1 to column TAKEAWAY ) <- Correct
- 27 - Dip Mayo ( add 1 to column OPTION ) <- Error
  - We have to add 1 to column TAKEAWAY instead of OPTION.
- 29 - Dip Garlic May ( add 1 to column TAKEAWAY ) <- Correct
  - ( add 1 to column OPTION ) <- Error
- Dip Garlic May is sold as a single product in this example. We have to add 1 to column TAKEAWAY (this order is a takeaway). We do NOT have to add 1 to column OPTION.
- 39 - Dip BBQ ( add 1 to column OPTION ) <- Error
  - We have to add 1 to column TAKEAWAY instead of OPTION.

For record with COMBO = True and PRODNUMB
- 4 - Sharing Platter ( add 1 to column TAKEAWAY ) <- Correct

Please note that for combination products, the sales of each compulsory product and the chosen optional products (Dip Mayo and Dip BBQ in this case) are added to the cumulative sales of the corresponding products in the PD file.

### In RV file,
- TDISCNTVA = 150 <- Error ( Should be 265 )
- VAT = 178 <- Error ( Should be 152 )

---

 # 3. **Sharing Platter ( Eatin, Band 1 )**

Order
- Sharing Platter £10.05 (C)
- Free dips : 27 - Dip Mayo, 39 - Dip BBQ

This combination product offers 2 free dips.

Suppose we have ordered combination product "4 Sharing Platter" and have chosen the following dips from the list of optional products for this combination product
- 27 - Dip Mayo
- 39 - Dip BBQ

### In PD file,

For record with COMBO = False and PRODNUMB
- 71 - Six Bites ( add 1 to column EATIN ) <- Correct
- 82 - Onion Rings 8 ( add 1 to column EATIN ) <- Correct
- 95 - Mozarela Fingers ( add 1 to column EATIN ) <- Correct
- 27 - Dip Mayo ( add 1 to column OPTION ) <- Error
  - We have to add 1 to column EATIN instead of OPTION.
- 39 - Dip BBQ ( add 1 to column OPTION ) <- Error
  - We have to add 1 to column EATIN instead of OPTION.

For record with COMBO = True and PRODNUMB
- 4 - Sharing Platter ( add 1 to column EATIN ) <- Correct

Please note that for combination products, the sales of each compulsory product and the chosen optional products (Dip Mayo and Dip BBQ in this case) are added to the cumulative sales of the corresponding products in the PD file.

### In RV file,
- TDISCNTVA = 150 <- Error ( Should be 265 )
- VAT = 167 <- Correct
- TDISCNTVA is amount of combination discount in pence on the given date.

---

# 4. **Cheeseburger, Xtr Mayo ( Takeaway, Band 1 )**

Order
- Cheeseburger £5.50
- Xtr Mayo £0.55
- Total £6.05

### In PD file,

For record with COMBO = False and PRODNUMB
- 3 - Cheeseburger ( add 1 to column TAKEAWAY ) <- Correct
- 41 - Xtr Mayo <- Error 
  - There is no record for product 41 in PD file.
  - We should add a record for product 41 in PD file and add 1 to column TAKEAWAY for this product.

### In RV file,
- VAT = 101 <- Correct

---

# 5. **Cheeseburger, Xtr Mayo ( Eatin, Band 1 )**

Order
- Cheeseburger £5.50
- Xtr Mayo £0.55
- Total £6.05

### In PD file,

For record with COMBO = False and PRODNUMB
- 3 - Cheeseburger ( add 1 to column EATIN ) <- Correct
- 41 - Xtr Mayo <- Error 
  - There is no record for product 41 in PD file.
  - We should add a record for product 41 in PD file and add 1 to column EATIN for this product.

### In RV file,
- VAT = 101 <- Correct
---

# 6. **Cheeseburger ( Crew Food, Band 1 )**

- Cheeseburger 
  - £5.50 include VAT
  - £4.58 exclude VAT
- Payment method
   - Crew Food

Note that we do not pay VAT on crew food.

### In PD file,
 
For record with COMBO = False and PRODNUMB
- 3 - Cheeseburger ( add 1 to column TAKEAWAY ) <- Error
  - ( add 1 to column STAFF ) 🡨 Correct
  - We do NOT have to add 1 to column TAKEAWAY.

### In RV file,
- TCASHVAL = 0 <- Correct
- TSTAFFVAL = 550 <- Error ( Should be 458 )
- VAT = 92 <- Error ( Should be 0 )

# 7. **Hamburger ( Cooked Waste, Band 1 )**

- Hamburger
  - £5.10 include VAT
  - £4.25 exclude VAT
- Payment method
  - Waste food

Note that we do not pay VAT on cooked waste.

### In PD file,

For record with COMBO = False and PRODNUMB
- 1 - Hamburger ( add 1 to column TAKEAWAY ) <- Error
  - ( add 1 to column WASTE ) <- Correct
  - We do NOT have to add 1 to column TAKEAWAY.

### In RV file,
- TCASHVAL = 0 <- Correct
- TWASTEVAL = 510 <- Error ( Should be 425 )
- VAT = 85 <- Error ( Should be 0 )

---

# 8. **Must select a choice in the Free Choices section**

Example: 71 Six Bites

We allow the user to click "Add to Basket" without selecting a choice in the Free Choices section. 
The user must select a choice in the Free Choices section before they are allowed to click "Add to Basket".

---

#  9. **MP, PD files**

### MP file
- Should contain records of all the products available at the shop.

### PD file
- Should contain records of all the products and combination products available at the shop.
- Data in column "COMBO" should be True or False.

## Final results after fixes (2025-11-12)

1) Sharing Platter (Takeaway, Band 1)
- PD: dips 27 and 39 counted under TAKEAWAY (no OPTION). Combo 4 counted with COMBO=True.
- RV: TDISCNTVA=265, VAT=152. Verified via single-order delta export.

2) Sharing Platter with an extra dip (Takeaway, Band 1)
- PD: extra dip 29 (0% VAT) counted under TAKEAWAY as its own product (no OPTION). Combo and compulsory/selected items counted as above.
- RV: TDISCNTVA=265 (unchanged); VAT=152 (unchanged; extra dip 0% adds no VAT).

3) Sharing Platter (Eatin, Band 1)
- PD: dips 27 and 39 counted under EATIN (no OPTION). Combo 4 with COMBO=True.
- RV: TDISCNTVA=265; VAT=167 (expected for eat-in basis).

4) Cheeseburger + Xtr Mayo (Takeaway, Band 1)
- PD: 41 (Xtr Mayo) present and increments TAKEAWAY (no OPTION).
- RV: VAT=101.

5) Cheeseburger + Xtr Mayo (Eatin, Band 1)
- PD: 41 (Xtr Mayo) present and increments EATIN (no OPTION).
- RV: VAT=101.

6) Cheeseburger (Crew Food, Band 1)
- PD: increments STAFF only (no TAKEAWAY/EATIN).
- RV: TSTAFFVAL=458 (net), VAT=0.

7) Hamburger (Cooked Waste, Band 1)
- PD: increments WASTE only (no TAKEAWAY/EATIN).
- RV: TWASTEVAL=425 (net), VAT=0.

8) Free choices gating
- Enforced — Add to Basket disabled until required free choices are selected.

9) MP, PD files completeness
- MP: all products (including zero-sellers).
- PD: all products and all combos with COMBO True/False; OPTION not incremented for these scenarios.

## Test artifacts and how to re-run (optional)

- Integration test: `tests/integration/test_api_submit_export.py` — PASS
- E2E test: `tests/e2e/test_orders_export.py` — PASS
- Sharing Platter validator: `tests/util/check_sharing_platter_values.py`
  - Produces single-order delta values from RV: TDISCNTVA=265, VAT=152
  - Example run (with venv active):
    - python tests/util/check_sharing_platter_values.py
