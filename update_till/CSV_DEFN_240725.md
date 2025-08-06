# CONTENTS								       Date  24/07/25
Definition for Tables
K_MEAL
K_PRO
K_REV
K_WK_VAT
PDVAT_TB
PDITEM<n>     where n is a shop code
COMBTB<n>   where n is a shop code
ACODES
BCODES
COMP_PRO
OPT_PRO
P_CHOICE
ST_ITEMS
APP_COMB
APP_PROD
GROUP_TB
MISC_SEC
COMB_EXT
PROD_EXT
SHOPS_TB
FILES Required by Uncle Sams for each shop and each day of week
MP<ddmmyy>.CSV	for date dd/mm/yy
PD<ddmmyy>.CSV	for date dd/mm/yy
RV<ddmmyy>.CSV  	for date dd/mm/yy
K_WK_VAT.CSV	for the week
FILES provided to the shop at the start of a week
PDITEM<n>.CSV     	where n is a shop code    eg   PDITEM15.CSV  for Crawley Shop
COMBTB<n>.CSV   	where n is a shop code    eg   COMBTB15.CSV  for Crawley Shop
ACODES.CSV	(*)
BCODES.CSV	(*)
COMP_PRO.CSV	(*)
OPT_PRO.CSV	(*)
P_CHOICE.CSV	(*)
PDVAT_TB.CSV	(*)
ST_ITEMS.CSV	(*)
APP_COMB.CSV	(*)
APP_PROD.CSV	(*)
GROUP_TB.CSV	(*)
MISC_SEC.CSV	(*)
COMB_EXT.CSV	(*)
PROD_EXT.CSV	(*)
SHOPS_TB.CSV	(*)
# Definition for Table K_MEAL
### Field Name	Type
PRODNUMB	Integer
Product code.
TAKEAWAY	Integer
Total number of this product sold as part of takeaway meals on the given date.
EATIN	Integer
Total number of this product sold as part of eatin meals on the given date.
# Remarks
Table K_Meal is a template for MP<ddmmyy>, where dd/mm/yy is the given date. We store the number of meals sold on date dd/mm/yy in table MP<dd/mm/yy>.
Sales of meal products are also added to the cumulative sales of the corresponding products in table PD<ddmmyy>, where dd/mm/yy is the given date. Table K_PRO is a template for PD<ddmmyy>.
There is a record for each product at the shop in table K_Meal.
# Definition for Table K_PRO
### Field Name	Type
PRODNUMB	Integer
If COMBO is False then PRODNUMB is a product code.
If COMBO is True then PRODNUMB is a Combination product code.
COMBO	Boolean
See definition for PRODNUMB.
TAKEAWAY	Integer
Total number of this product sold as takeaway on the given date.
EATIN	Integer
Total number of this product sold as eatin on the given date.
WASTE		Integer
Total number of this product entered as Cooked Waste on the given date.
STAFF	Integer
Total number of this product entered as Crew Food on the given date.
OPTION	Integer
Total number of this product chosen as optional product for products (not for combination products) on the given date.
# Remarks
Table K_PRO is a template for PD<ddmmyy>, where dd/mm/yy is the given date.
We store the number of products sold on date dd/mm/yy in table PD<ddmmyy>.
There is a record for each product at the shop in table PD<ddmmyy>.
There is a record for each combination product at the shop in table PD<ddmmyy>.
# Definition for Table K_REV
### Field Name	Type
TCASHVAL	Long
Amount of cash (in pence) in drawer recorded by POS on the given date.
TCHQVAL	Long
Amount of cheques (in pence) in drawer recorded by POS on the given date.
TCARDVAL	Long
Amount of credit/debit card payments in pence recorded by POS on the given date.
TONACCOUNT	Long
Amount of “on account” payments in pence recorded by POS on the given date.
TSTAFFVAL	Long
Value of crew food in pence recorded by POS on the given date.
TWASTEVAL	Long
Value of cooked waste in pence recorded by POS on the given date.
TCOUPVAL	Long
Value of coupons in pence recorded by POS on the given date.
TPAYOUTVA	Long
Amount of paid outs in pence recorded by POS on the given date.
Whenever the cashier has done a paid out, the system will add the amount of that paid out to 	TPAYOUTVA and deduct the amount of that paid out from TCASHVAL
TTOKENVAL	Long
Value of vouchers in pence recorded by POS on the given date.
TDISCNTVA	Long
Amount of combination discount in pence recorded by POS on the given date.
A = Total amount due for all the products in the order in pence
B =  Total amount due for all the combination products in the order in pence
Combination discount for an order = A – B
# Definition for Table K_REV
### Field Name	Type
TTOKENNOVR	Long
Voucher overage in pence recorded by POS on the given date.
TGOLARGENU	Integer
Number of go large recorded by POS on the given date.
TMEAL_DISCNT	Long
Amount of discount for meals in pence recorded by POS on the given date.
Total discount given to the products (Burger, Drink, Fries) ordered as part of a meal.
ACTCASH		Long
Actual amount of cash taken by POS in pence on the given date.
ACTCHQ	Long
Actual amount of cheques taken by POS in pence on the given date.
ACTCARD	Long
Actual amount of credit/debit card payments taken by the card machine in pence on the 	given date.
VAT	Long
Total amount of  VAT due in pence on the given date.
XPV	Long
Extended product value in pence on the given date.
Data in this column is not required.
# Remarks
Table K_REV is a template for RV<ddmmyy>, where dd/mm/yy is the given date.
For example, Table RV210725 is for date 21/07/25.
There is only one record in table RV<ddmmyy>.
# Key
POS – Point of Sales System
# Definition for Table K_WK_VAT
### Field Name	Type
VAT_CLASS	Byte
Vat class.
VAT_RATE	Single
Vat rate for this vat class.
TOT_VAT_1	Single
Total amount of VAT due in pound for all the products which were sold at this VAT rate on Monday. This figure does not include any VAT due for the Deleted orders, Crew food and Cooked waste.
TOT_VAT_2	Single
Total amount of VAT due in pound for all the products which were sold at this VAT rate on Tuesday. This figure does not include any VAT due for the Deleted orders, Crew food and Cooked waste.
Similarily for TOT_VAT_<n>  where n=3,4,5,6,7.
TOT_VAT_3	Single
TOT_VAT_4	Single
TOT_VAT_5	Single
TOT_VAT_6	Single
TOT_VAT_7	Single
T_VAL_EXCLVAT_1	Single
Total value of products excluding VAT in pound sold at this VAT rate on Monday. This figure does not include Deleted orders, Crew food and Cooked waste.
T_VAL_EXCLVAT_2	Single
Total value of products excluding VAT in pound sold at this VAT rate on Tuesday. This figure does not include Deleted orders, Crew food and Cooked waste.
Similarily for T_VAL_EXCLVAT_<n>  where n=3,4,5,6,7.
T_VAL_EXCLVAT_3	Single
T_VAL_EXCLVAT_4	Single
# Definition for Table K_WK_VAT
### Field Name	Type
T_VAL_EXCLVAT_5	Single
T_VAL_EXCLVAT_6	Single
T_VAL_EXCLVAT_7	Single
# Remarks
Table K_Wk_Vat stores values of VAT at different rates on each day of the week. There is one record for each VAT rate.
Table PdVat_Tb stores the details of VAT rates. There is one record for each VAT rate.
We initialize table K_Wk_Vat when we start a new week. For each record in table PDVat_Tb, we add a record to table K_Wk_Vat.
We update table K_Wk_Vat on each day of the week.
# Definition for Table PDVAT_TB
### Field Name	Type
VAT_CLASS	Byte
Vat class.
VAT_RATE	Single
Vat rate for this vat class.
VAT_DESC	Text, 20
Description of this vat class.
# Remarks
There are 2 records in table PdVat_Tb
VAT_CLASS	VAT_RATE	VAT_DESC
0		0	Zero rate
1		20	Standard rate
If there is another vat rate, we just have to add a record to table PdVat_Tb.
# Definition for Table PDITEM<n>
### Field Name	Type
PRODNUMB	Integer
Product code.
PRODNAME	Text, 16
Product name.
EAT_VAT_CLASS		Byte
Vat class for this product in an Eatin order.
We can find out the VAT rate by looking up the VAT class in table PDVat_Tb. Use this VAT rate to calculate the non-Vat price of this product in an Eatin order.
TAKE_VAT_CLASS		Byte
Vat class for this product in a Takeaway order.
We can find out the VAT rate by looking up the VAT class in table PDVat_Tb. Use this VAT rate to calculate the non-Vat price of this product in a Takeaway order.
READBACK_ORD		Byte
Read Back sorting order.
Read Back sorting method:
Set Meal Product to True if the given product is ordered as a standard meal or kids meal.
Items in the order are sorted in ascending order of ReadBack_ord and then Meal Product. After the items in an order have been sorted by Read Back sorting method, they are displayed in the Read Back Box.
There are 3 sections in the Read Back Box.
Items with readback_ord between 1 and 85 inclusive appear in section 1 of the Read Back Box.
Items with readback_ord between 86 and 170 inclusive appear in section 2 of the Read Back Box.
Items with readback_ord between 171 and 255 inclusive appear in section 3 of the Read Back Box.
In each section, meal products are displayed before single products.
Lowest number appears highest on the list of that section.
If the number is 0 then that item will follow the previously rung in item (used for ‘extras’).
# Definition for Table PDITEM<n>
### Field Name	Type
We have set up the Read Back sorting order in the following way
Top section for
Main courses
Nuggets
Middle section for
Fries
Onion Rings
Mushrooms
Desserts
Bottom section for
Hot drinks
Shakes
Fizzy
MEAL_ONLY		Boolean
True if this product can only be sold as part of meal.
MEAL_CODE		Byte
– This product can’t be orderd as part of meal
- This product can be ordered as part of Standard Meal
- This product can be ordered as part of Kids Meal
MEAL_DRINK		Byte
- This product is not a drink or This drink is not available for meals
– This product is a drink for Standard Meal
– This product is a drink for Kids Meal
T_DRINK_CD		Integer
Product code of trade up drink.
It is the product code of the corresponding large drink if this product is a drink and can go large. Otherwise set it to 0.
VATPR		Integer
Current price including VAT in pence.
This is standard price.
DC_VATPR		Integer
Current discounted price for meal product including VAT in pence
This is standard price.
# Definition for Table PDITEM<n>
### Field Name	Type
VATPR_2		Integer
Current price including VAT in pence.
This is price band 2.
Similarly for VATPR_<n>  where n=3,4,5,6.
DC_VATPR_2		Integer
Current discounted price for meal product including VAT in pence
This is price band 2.
Similarly for DC_VATPR_<n>  where n=3,4,5,6.
VATPR_3		Integer
DC_VATPR_3		Integer
VATPR_4		Integer
DC_VATPR_4		Integer
VATPR_5		Integer
DC_VATPR_5		Integer
VATPR_6		Integer
DC_VATPR_6		Integer
# Remarks
Table PdItem<n> is for the shop with shop code <n>.
For example, PDItem15 is for Crawley shop,
PDItem9 is for Broadwater shop.
It contains all the products available at shop <n>. There is one record for each product.
# Definition for Table COMBTB<n>
### Field Name	Type
COMBONUMB	Integer
Combination product code.
DESC	Text, 16
Name of this combination product.
T_COMB_NUM		Integer
The combination product code for the corresponding trade up combination product.  Set it to 0 if there is no corresponding trade up combination product.
EAT_VAT_CLASS		Byte
Vat class for this combination product in an Eatin order.
We can find out the VAT rate by looking up the VAT class in table PDVat_Tb. Use this VAT rate to calculate the non-Vat price of this combination product in an Eatin order.
TAKE_VAT_CLASS		Byte
Vat class for this combination product in a Takeaway order.
We can find out the VAT rate by looking up the VAT class in table PDVat_Tb. Use this VAT rate to calculate the non-Vat price of this combination product in a Takeaway order.
VATPR		Integer
Current price including vat in pence of this combination product. This is standard price.
T_VATPR		Integer
Current price including vat in pence of the corresponding trade up combination product.
Set it to 0 if there is no corresponding trade up combination product.
This is standard price.
VATPR_2		Integer
Current price including vat in pence of this combination product.
This is price band 2.
Similarly for VATPR_<n>  where n=3,4,5,6.
T_VATPR_2		Integer
Current price including vat in pence of the corresponding trade up combination product.
Set it to 0 if there is no corresponding trade up combination product.
This is price band 2.
Similarly for T_VATPR_<n>  where n=3,4,5,6.
# Definition for Table COMBTB<n>
### Field Name	Type
VATPR_3		Integer
T_VATPR_3		Integer
VATPR_4		Integer
T_VATPR_4		Integer
VATPR_5		Integer
T_VATPR_5		Integer
VATPR_6		Integer
T_VATPR_6		Integer
# Remarks
Table CombTb<n> is for the shop with shop code <n>.
For example, CombTb15 is for Crawley shop,
CombTb9 is for Broadwater shop.
It contains all the combination products available at shop <n>. There is one record for a combination product.
# Definition for Table ACODES
### Field Name	Type
PRODNUMB		Integer
Product code.
ST_CODENUM	Integer
Code of a ‘A’ code stock component for the product with Product Code = PRODNUMB
QTY	Single
Quantity of this ‘A’ code stock component for this product.
# Remarks
If a product has <n> ‘A’ code stock components, then add <n> records to table Acodes. Each of these records represents a ‘A’ code stock component for the product.
# Definition for Table BCODES
### Field Name	Type
PRODNUMB		Integer
Product code.
ST_CODENUM	Integer
Code of a ‘B’ code stock component for the product with Product Code = PRODNUMB
QTY	Single
Quantity of this ‘B’ code stock component for this product.
# Remarks
If a product has <n> ‘B’ code stock components, then add <n> records to table BCodes. Each of these records represents a ‘B’ code stock component for the product.
# Definition for Table COMP_PRO
### Field Name	Type
COMBONUMB		Integer
Combination product code.
PRODNUMB		Integer
Product code of a compulsory product for this combination product.
T_PRODNUMB		Integer
Set it to 0 if there is no trade up combination product for this combination product.  Otherwise, it is the product code which will replace the product with the product code PRODNUMB for the corresponding trade up combination product.
# Remarks
There may be more than 1 record for a combination product.
For example, if there are 3 compulsory products for a given combination product, then there are 3 records for the given combination product.
# Definition for Table OPT_PRO
### Field Name	Type
COMBONUMB		Integer
Combination product code.
PRODNUMB		Integer
Product code of an optional product for this combination product.
T_PRODNUMB		Integer
Set it to 0 if there is no trade up combination product for this combination product.  Otherwise, it is the product code which will replace the product with the product code PRODNUMB for the corresponding trade up combination product.
# Remarks
There may be more than 1 record for a combination product.
For example, if there are 3 optional products for a given combination product, then there are 3 records for the given combination product.
# Definition for Table P_CHOICE
### Field Name	Type
PRODNUMB		Integer
Product code.
OPT_PRODNUMB		Integer
Product code of an optional product for the product with product code PRODNUMB.
# Remarks
We add records to table P_Choice for each product that has optional products. If the product has <n> optional products, then we add <n> records to table P_Choice for the product. Each of these records represents an optional product for the product.
# Definition for Table ST_ITEMS
### Field Name	Type
CODEALPH		Text, 1
A stock item code consists of two parts, a letter and then followed by an integer.
CODEALPH is the first part of a stock item code.
ST_CODENUM		Integer
Second part of a stock item code. It is a 4-digit number.
ITEM		Text, 18
Description for this stock item.
# Remarks
Table ST_Items contains records of A and B codes stock items.
# Definition for Table APP_COMB
### Field Name	Type
COMBONUMB	Integer
Combination product code.
DESC	Text, 16
Name of this combination product.
GROUP_ID	Byte
Section number under which this combination product is printed on the report
“App Product Prices – Band <n>”, where n = 1,2, … ,6.
GROUP_ID = 0 means that this combination product is not printed on the report
“App Product Prices – Band <n>”.
GROUP_SUB_ID	Integer
The order in which this combination product is printed in section <GROUP_ID> on the report
“App Product Prices – Band <n>”.
Lowest number appears highest in the list.
# Remarks
Table App_Comb contains all the combination products at Uncle Sams. There is one record for each combination product.
# Definition for Table APP_PROD
### Field Name	Type
PRODNUMB	Integer
Product code.
PRODNAME	Text, 16
Product name.
GROUP_ID	Byte
Section number under which this product is printed on the report
“App Product Prices – Band <n>” where n = 1,2,..,6.
GROUP_SUB_ID	Integer
The order in which this product is printed in section <GROUP_ID> on the report
“App Product Prices – Band <n>”.
Lowest number appears highest in the list.
MEAL_ID	Byte
Section number under which the meal price of this product is printed on the report
“App Product Prices – Band <n>”.
MEAL_ID = 0 means that the meal price of this product is not printed on the report
“App Product Prices – Band <n>”.
MEAL_SUB_ID	Integer
The order in which this product is printed in section <MEAL_ID> on the report
“App Product Prices – Band <n>”.
Lowest number appears highest in the list.
DOUBLE_PDNUMB	Integer
If PRODNUMB is a single product, then DOUBLE_PDNUMB is the corresponding double 	product for this product.
TRIPLE_PDNUMB	Integer
If PRODNUMB is a single product, then TRIPLE_PDNUMB is the corresponding triple	product for this product.
# Remarks
Table App_Prod contains all the products (not combination products)  at Uncle Sams.There is one record for each product.
Meal price of a single product
- = Discounted price for this single product   ( eg  Chesse Burger )  +
- Discounted price for Regular Fries +
- Discounted price for Fizzy Reg  (BASE)
- We have set product “49 Cola” as the Fizzy Reg  (BASE)
Meal price of a double product
- = Discounted price for this double product   ( eg  Double Chesse Burger )  +
- Discounted price for Regular Fries +
- Discounted price for Fizzy Reg  (BASE)
Meal price of a triple product
- = Discounted price for this triple product   ( eg  Triple Chesse Burger )  +
- Discounted price for Regular Fries +
- Discounted price for Fizzy Reg  (BASE)
Meal price of a kid hamburger
- = Discounted price for this kid hamburger   ( eg  kid chesse burger )  +
- Discounted price for Regular Fries +
- Discounted price for Fizzy Kids  (BASE)
- We have set product “89 Cola small” as the Fizzy Kids  (BASE)
# Definition for Table GROUP_TB
### Field Name	Type
GROUP_ID	Byte
Section number on the report “App Product Prices – Band <n>”  where n = 1,2,..,6.
GROUP_NAME	Text, 16
Section name, eg “Chicken”, “Fries and Sides”.
SOURCE_TYPE	Text, 1
If SOURCE_TYPE = ”P”, then this section is for the products (not the combination products),
eg  Cheese burger,  Chicken AllStar.
If SOURCE_TYPE = ”C”, then this section is for the combination products,
eg  “Sharing platter”.
MEAL_GROUP	Byte
Section number for meal products. If MEAL_GROUP is greater than 0, then we list the meal prices of all the products with MEAL_ID (Field of table App_Prod) =  MEAL_GROUP under section number <MEAL_GROUP>.
# Remarks
Table Group_TB does not contain all the sections on the report  “App Product Prices – Band <n>” .
There are 2 more sections:
Section 10 – Miscellaneous
Section 11 – Class Prices of Fries and Drinks
Section 11 is included on the report for us to check the data.
# Definition for Table MISC_SEC
### Field Name	Type
PRODNUMB	Integer
Product Code.  We set PRODNUMB to 0 if this item is not a product in our product file.
PRODNAME	Text, 16
Product name.  We set PRODNAME to blank if this item is not a product in our product file.
ITEM_DESC	Text, 20
If  PRODNUMB > 0 then ITEM_DESC is same as PRODNAME.
ITEM_DESC is the description printed in column “Product Name” in
Section 10 – Miscellaneous. We print the price of this product for the chosen price band in 	column “Price”.
If  PRODNUMB = 0 then ITEM_DESC is not a product name. We need to calculate the figure 	and print it in column “Price”.
Eg,  for  ITEM_DESC = “Shake Instead”, we need to calculate the figure for Shake Instead.
Shake Instead = Shake Reg – Fizzy Reg (BASE)
SEQ_ORDER	Integer
The order in which this item is printed in  Section 10 – Miscellaneous  on the report
“App Product Prices – Band <n>”, where n = 1,2,…,6.
Lowest number appears highest in the list.
# Remarks
Table MISC_SEC contains all the items to be printed in  Section 10 -  Miscellaneous  on the report  “App Product Prices – Band <n>”,  where n = 1,2,…,6.
# Definition for Table COMB_EXT
### Field Name	Type
COMBONUMB	Integer
Combination product code.
DESC	Text, 16
Name of this combination product.
NAME_ON_MENU	Text, 30
Name shown on the menu.
PROD_DESC	Text, 255
Description of this combination product.
# Remarks
Table Comb_Ext contains all the combination products at Uncle Sams. There is one record for each combination product.
# Definition for Table PROD_EXT
### Field Name	Type
PRODNUMB	Integer
Product code.
PRODNAME	Text, 16
Name of this product, eg “DBL CHEESEBURGER”.
NAME_ON_MENU	Text, 30
Name shown on the menu, eg “Double Cheese Burger”.
COOK_ZONE	Byte
Cooking zone.
Code	Cooking zone
Product is not shown on the Cooking Zone
PREP
DRINKS
FRIER
PROD_DESC	Text, 255
Description of this product.
# Remarks
Table Prod_Ext contains all the products at Uncle Sams. There is one record for each product.
# Definition for Table SHOPS_TB
### Field Name	Type
SHOP_CODE	Byte
Shop code.
SHOP_NAME	Text, 10
Shop Name, eg “Crawley”.
SHOP_ABBREV	Text, 2
Abbreviation of the shop name, eg “CW” for Crawley shop.
FRANCHISEE	Text, 25
Name of the franchisee.
FULL_NAME	Text, 32
Name of the company, eg “T/A Uncle Sams Hamburger Express”.
ADDRESS_1	Text, 22
First line of the shop address.
ADDRESS_2	Text, 20
Second line of the shop address.
ADDRESS_3	Text, 17
Third line of the shop address.
POST_CODE	Text, 8
Postcode of the shop address.
# Remarks
Table Shops_Tb contains records of the shops which have your POS System.
-----  END  -----