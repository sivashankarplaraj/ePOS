Examples of Meal Discount		      				 Date  24/07/25
Note that the prices shown on this document are not the latest prices.
Meal Discount is the total discount given to the products (Burger, Drink, Fries) ordered as part of a meal.
Example 1 – Cheeseburger Meal   (Standard price)
Product	Product	Single item	Part of a
Code	Name	Price	Meal Price
---------	-------------------------	--------------	-------------
3	Cheeseburger	£4.85	£4.85
30	Regular Fries	£2.05	£1.25
69	Vanilla Shake	£2.70	£2.60
---------	-------------------------	--------------	-------------
Total	£9.60  (A)	£8.70  (B)
Meal Discount 	= A – B
= £9.60 - £8.70
= £0.90
Note:
Example 2 – Cheeseburger Meal   (Price band 6)
Product	Product	Single item	Part of a
Code	Name	Price	Meal Price
---------	-------------------------	--------------	-------------
3	Cheeseburger	£6.15	£6.15
30	Regular Fries	£2.60	£1.60
69	Vanilla Shake	£3.40	£3.30
---------	-------------------------	--------------	-------------
Total	£12.15  (A)	£11.05  (B)
Meal Discount 	= A – B
= £12.15 - £11.05
= £1.10
Note:
Example 3 – Cheeseburger Meal Go Large  (Standard price)
Product	Product	Single item	Part of a
Code	Name	Price	Meal Price
---------	-------------------------	--------------	-------------
3	Cheeseburger	£4.85	£4.85
31	Large Fries	£2.50	£1.70
70	Vanilla Sk Large	£3.40	£3.20
---------	-------------------------	--------------	-------------
Total	£10.75  (A)	£9.75  (B)
Meal Discount 	= A – B
= £10.75 - £9.75
= £1.00
Refer to Example 1, if we apply Go Large, then it would make Large Fries instead of 	Regular Fries and Vanilla Sk Large instead of Vanilla Shake.
-----  END  -----
||Corresponding column in
PDITEM<n>.csv    where n is shop code|
|---|---|
|Single Item Price|VATPR

Current price including VAT in pence.
This is standard price.|
|Part of a Meal Price|DC_VATPR

Current discounted price for meal product including VAT in pence.
This is standard price.|
||Corresponding column in
PDITEM<n>.csv    where n is shop code|
|---|---|
|Single Item Price|VATPR_6

Current price including VAT in pence.
This is price band 6.|
|Part of a Meal Price|DC_VATPR_6

Current discounted price for meal product including VAT in pence.
This is price band 6.|