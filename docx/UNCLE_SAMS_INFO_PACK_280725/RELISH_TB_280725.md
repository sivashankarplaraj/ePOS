CONTENTS                                               						Date  28/07/25
________________________________________________________________________________
Relish Table
GoLarge Meal
Products which can only be sold as part of meal
Daily CSV files
Section 1  –  Relish Table
________________________________________________________________________________
“26  Dip Ketchup” and “40  Xtr Ketch” are products. We charge customers when they order them.
We have a relish table. We allow the customer to remove any of the following relishes from their order.
When the customer says they do not want a relish, we check if the selected relish is applicable to this product. If so, we remove the selected relish from the ingredients for the product. But this does not reduce the price of the order.
For example, the customer orders product  “1  Hamburger”  and they say they don’t want ketchup. We check if ketchup (stock A37) is applicable to this product.
Stock items for product  “1  Hamburger”  are
A7 – Bun
A26 – Iceberg
A28 – Red Onions
A37 – Ketchup
A41 – French’s mustard
A53 – Meat
As product  “1  Hamburger”  contains  “A37 – Ketchup”  , we remove A37 from the ingredients for the product  “1  Hamburger”.  Suppose the order is taken at price band 1, then the price of the order is  £4.95   ( Price of  product  “1  Hamburger”  as at 28/07/25).
NOTE
The data of A code stock components of products is stored in  ACODES.CSV.
Section 2  -  GoLarge  Meal
____________________________________________________________________
For example
Meal order :
3 – Cheeseburger
30 – Regular Fries
69 –Vanilla Shake
If we apply Go Large to the above order, then it would make
“31  Large Fries”  		instead of  “30  Regular Fries”  and
“70  Vanilla Sk Large”  	instead of  “69  Vanilla Shake”.
We add  1  to column  TGOLARGENU  in the RV file
TGOLARGENU  is the number of go large recorded by POS on the given date.
For definition for RV file, see definiton for table K_Rev in  CSV_DEFN_240725.docx.
Meals on/off  key
After the user has pressed start key to start the taking order process, meals on/off key can be pressed at any time during the taking order process. Pressing meals on/off key will alternate between the unchecked and checked states of the meals on/off key.
A product can be ordered as a meal or not depending on the value of field meal_code of table PDItem<n> .csv  where n is shop code.
The value of field meal_drink of table PDItem<n>.csv denotes the type of meal (regular meal or kids meal) for which this drink can be ordered. If we wish to order a drink as a meal drink, we have to press meals on/off key first if it is not on.
If the product can be ordered as a meal (regular meal or kids meal), then the corresponding number of regular fries are automatically ordered for the meal product. For example, if 2 Hamburger (regular meal) are ordered, then 2 portions of regular fries are automatically ordered for these 2 Hamburger (regular meal).
Section 3  -  Products which can only be sold as part of meal
________________________________________________________________________________
The following products can only be sold as part of meal. They can’t be sold as a single product.
13 – Kids Hamburger
35 – Kids Cheese-Bgr
118 – Kids 4 Bites
Definition for PDItem<n> .csv  where n is shop code.
Column  MEAL_ONLY
True if this product can only be sold as part of meal.
Column  MEAL_CODE
0 – This product can’t be ordered as part of a meal
1 – This product can be ordered as part of Standard Meal
2 – This product can be ordered as part of Kids Meal
Section 4  -  Daily CSV files
________________________________________________________________________________
We require MP<ddmmyy>.csv, PD<ddmmyy>.csv, RV<ddmmyy>.csv and K_WK_VAT.csv for
each shop and each day of week, where ddmmyy is date dd/mm/yy.
For example, each shop requires the following CSV files for date 20/07/25
K_WK_VAT.csv
MP200725.csv
PD200725.csv
RV200725.csv
Each shop has the following directories
\PK_MAILBOX\IN
\PK_MAILBOX\OUT
Shops require daily csv files in   \PK_MAILBOX\IN   on each day of week after they have closed
the till at night and have done the Z reading.
CSV files with the latest products are sent to   \PK_MAILBOX\OUT   for each shop on Monday
morning before they start the till.
-----  END  -----
|RELISH|A  CODE|
|---|---|
|mdf cheese|9|
|mdf chilli|35|
|mdf dills|44|
|mdf garlic|29|
|mdf ketchup|37|
|mdf lettuce|26|
|mdf mayo|36|
|mdf mustard|41|
|mdf onions|28|
|mdf relish(meat)|53|
|mdf salad|26|
|mdf Special(bun)|7|
|mdf tomato|27|