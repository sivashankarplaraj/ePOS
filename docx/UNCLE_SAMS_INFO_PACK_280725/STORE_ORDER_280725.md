# ORDERS	   								Date  28/07/25
How to store data in the daily CSV files
CONTENTS
# -------------------------------------------------------------------------------------------------------------
Hamburger
Regular Fries
Strawberry Shake
Dip Ketchup
Cheeseburger,  Xtr Mayo
Hamburger,  No Ketchup
Six bites  -  Choose an optional product
Cheeseburger,  Vanilla Shake   ( Meal )
Sharing Platter   ( Combination Product )
NOTE
The prices shown on this document are not the latest prices.
# Hamburger
______________________________________________________________________________________________
Standard price for product  “1  Hamburger”  is  £4.65.
In MP file
There is no need to store any data in the MP file for this order.
In PD file
- For Takeaway	order
For record with COMBO = False and PRODNUMB
1 – Hamburger 		( add 1 to column  TAKEAWAY )
For Eatin order
For record with COMBO = False and PRODNUMB
1 –  Hamburger		( add 1 to column  EATIN )
In RV file
We have to add the corresponding data to the fields.
For example,
suppose this order is a standard price order and the customer pays for this order by cash.
Thus we add  465  to TCASHVAL.
TCASHVAL  is the amount of cash (in pence) in drawer recorded by POS on the given date.
# Regular Fries
______________________________________________________________________________________________
Standard price for product  “30  Regular Fries”  is  £2.20.
In MP file
There is no need to store any data in the MP file for this order.
In PD file
- For Takeaway	order
For record with COMBO = False and PRODNUMB
30 – Regular Fries 		( add 1 to column  TAKEAWAY )
For Eatin order
For record with COMBO = False and PRODNUMB
30 –  Regular Fries		( add 1 to column  EATIN )
In RV file
We have to add the corresponding data to the fields.
For example,
suppose this order is a standard price order and the customer pays for this order by card.
Thus we add  220  to TCARDVAL.
TCARDVAL  is the amount of credit/debit card payments in pence recorded by POS on the given date.
# Strawberry Shake
______________________________________________________________________________________________
Standard price for product  “62  Strawberry Shk”  is  £2.85.
In MP file
There is no need to store any data in the MP file for this order.
In PD file
- For Takeaway	order
For record with COMBO = False and PRODNUMB
62 – Strawberry Shk 		( add 1 to column  TAKEAWAY )
For Eatin order
For record with COMBO = False and PRODNUMB
62 – Strawberry Shk 		( add 1 to column  EATIN )
In RV file
We have to add the corresponding data to the fields.
For example,
suppose this order is a standard price order and the customer pays for this order by card.
Thus we add  285  to TCARDVAL.
TCARDVAL  is the amount of credit/debit card payments in pence recorded by POS on the given date.
# Dip Ketchup
______________________________________________________________________________________________
Standard price for product  “26  Dip Ketchup”  is  £0.35.
In MP file
There is no need to store any data in the MP file for this order.
In PD file
- For Takeaway	order
For record with COMBO = False and PRODNUMB
26 – Dip Ketchup 		( add 1 to column  TAKEAWAY )
For Eatin order
For record with COMBO = False and PRODNUMB
26 – Dip Ketchup 		( add 1 to column  EATIN )
In RV file
We have to add the corresponding data to the fields.
For example,
suppose this order is a standard price order and the customer pays for this order by card.
Thus we add  35  to TCARDVAL.
TCARDVAL  is the amount of credit/debit card payments in pence recorded by POS on the given date.
# Cheeseburger,  Xtr Mayo
______________________________________________________________________________________________
Order   ( Standard Price )
1  Cheeseburger	£5.05
1  Xtr Mayo		£0.55
-------
Total		£5.60
In MP file
There is no need to store any data in the MP file for this order.
In PD file
- For Takeaway	order
For record with COMBO = False and PRODNUMB
3 – Cheeseburger 		( add 1 to column  TAKEAWAY )
41 – Xtr Mayo 		( add 1 to column  TAKEAWAY )
For Eatin order
For record with COMBO = False and PRODNUMB
3 – Cheeseburger 		( add 1 to column  EATIN )
41 – Xtr Mayo 		( add 1 to column  EATIN )
In RV file
We have to add the corresponding data to the fields.
For example,
suppose this order is a standard price order and the customer pays for this order by card.
Thus we add  560  to TCARDVAL.
TCARDVAL  is the amount of credit/debit card payments in pence recorded by POS on the given date.
# Hamburger,  No Ketchup
______________________________________________________________________________________________
Order   ( Standard Price )
The standard price for product  “1  Hamburger”  is  £4.65.
Suppose the customer orders product  “1  Hamburger”  and they say they don’t want ketchup. We check if ketchup (stock A37) is applicable to this product.
As product  “1  Hamburger”  contains “A37 – Ketchup”, we remove A37 from the ingredients for 	the product  “1  Hamburger”. But we still charge £4.65 for this order.
In MP file
There is no need to store any data in the MP file for this order.
In PD file
- For Takeaway	order
For record with COMBO = False and PRODNUMB
1 – Hamburger 		( add 1 to column  TAKEAWAY )
For Eatin order
For record with COMBO = False and PRODNUMB
1 – Hamburger 		( add 1 to column  EATIN )
In RV file
We have to add the corresponding data to the fields.
For example,
suppose the customer pays for this order by card.
Thus we add  465  to TCARDVAL.
TCARDVAL  is the amount of credit/debit card payments in pence recorded by POS on the given date.
# Six bites  -  Choose an optional product
______________________________________________________________________________________________
Optional products for  product  “71  Six Bites”  are
26 - Dip Ketchup
27 - Dip Mayo
28 - Dip Chilli
29 - Dip Garlic Mayo
39 - Dip BBQ
101 - Dip 1000 Isle
110 - Dip None
Suppose we have chosen product “27  Dip Mayo” from the list of optional products.
_______________________________________________________________________________
In MP file
There is no need to store any data in the MP file for this order.
In PD file
- For Takeaway	order
For record with COMBO = False and PRODNUMB
27 – Dip Mayo 		( add 1 to column  OPTION )
71 – Six Bites  		( add 1 to column  TAKEAWAY )
For Eatin order
For record with COMBO = False and PRODNUMB
27 – Dip Mayo 		( add 1 to column  OPTION )
71 – Six Bites  		( add 1 to column  EATIN )
- Definition of OPTION is the total number of this product chosen as the optional product for 	products on the given date.
In RV file
We have to add the corresponding data to the fields.
# Cheeseburger, Vanilla Shake   ( Meal )
______________________________________________________________________________________________
Order - Cheeseburger Meal   (Standard price)
Product	Product	Single item	Part of a
Code	Name	Price	Meal Price
---------	-------------------------	--------------	-------------
3	Cheeseburger	£5.05	£5.05
30	Regular Fries	£2.20	£1.30
69	Vanilla Shake	£2.85	£2.80
---------	-------------------------	--------------	-------------
Total	£10.10  (A)	£9.15  (B)
Meal Discount 	= A – B
= £10.10 - £9.15
= £0.95
_______________________________________________________________________________
In MP file
- For Takeaway	order
For record with PRODNUMB
3 – Cheeseburger  		( add 1 to column  TAKEAWAY )
Please note that we do not have to add 1 to column  TAKEAWAY  for fries and drink for 	meal order in MP file.
- For Eatin order
For record with PRODNUMB
3 – Cheeseburger  		( add 1 to column  EATIN )
Please note that we do not have to add 1 to column  EATIN  for fries and drink for meal 	order in MP file.
In PD file
- For Takeaway	order
For record with COMBO = False and PRODNUMB
3 – Cheeseburger  		( add 1 to column  TAKEAWAY )
30 – Regular Fries  		( add 1 to column  TAKEAWAY )
69 – Vanilla Shake  		( add 1 to column  TAKEAWAY )
- For Eatin order
For record with COMBO = False and PRODNUMB
3 – Cheeseburger  		( add 1 to column  EATIN )
30 – Regular Fries  		( add 1 to column  EATIN )
69 – Vanilla Shake  		( add 1 to column  EATIN )
In RV file
TMEAL_DISCNT  is the amount of meal discount in pence on the given date.
Thus add  95  to column  TMEAL_DISCNT  for the above example.
We also have to add the corresponding data to the other fields.
# Sharing Platter   ( Combination Product )
______________________________________________________________________________________________
Suppose we have ordered combination product  “4  Sharing Platter” and have chosen
product  “27  Dip Mayo”  from the list of optional products for this combination product.
Compulsory products for  “4  Sharing Platter”
71 – Six Bites
82 – Onion Rings 8
95 – Mozarela fingers
Optional products for  “4  Sharing Platter”
26 – Dip Ketchup
27 – Dip Mayo
28 – Dip Chilli
29 – Dip Garlic Mayo
39 – Dip BBQ
101 – Dip 1000 Isle
110 – Dip None
_______________________________________________________________________________
Suppose the example is a standard price order.
Combination discount is calculated as follows.
Product			Single item
Code	Name			Standard Price
------	-------------------------	------------------
71	Six bites		£5.30
82	Onion rings 8		£2.45
95	Mozarela Fingers	£3.15
27	Dip Mayo		£0.55
------	-------------------------	------------------
Total			£11.45  (A)
Standard price of combination product  “4  Sharing Platter”  is  £9.50  (B)
Definition of Combination Discount
A = Amount due for all the compulsory products and the chosen optional product 			for the combination product
B = Amount due for the combination product
Combination Discount   = A - B
= £11.45 – £9.50
= £1.95
In MP file
There is no need to store any data in the MP file for this order.
In PD file
_________________________________________________________________________
- For Takeaway	order
For record with COMBO = False and PRODNUMB
71 – Six Bites  		( add 1 to column  TAKEAWAY )
82 – Onion Rings 8  		( add 1 to column  TAKEAWAY )
95 – Mozarela Fingers  	( add 1 to column  TAKEAWAY )
27 – Dip Mayo 		( add 1 to column  TAKEAWAY )
For record with COMBO = True and PRODNUMB
4 – Sharing Platter  		( add 1 to column  TAKEAWAY )
_________________________________________________________________________
- For Eatin order
For record with COMBO = False and PRODNUMB
71 – Six Bites  		( add 1 to column  EATIN )
82 – Onion Rings 8  		( add 1 to column  EATIN )
95 – Mozarela Fingers  	( add 1 to column  EATIN )
27 – Dip Mayo 		( add 1 to column  EATIN )
For record with COMBO = True and PRODNUMB
4 – Sharing Platter  		( add 1 to column  EATIN )
- _________________________________________________________________________
Please note that for combination products, the sales of each compulsory product and the chosen optional product are added to the cumulative sales of the corresponding products in the PD file.
In RV file
TDISCNTVA  is amount of combination discount in pence on the given date.
Thus add  195  to column TDISCNTVA for the above example.
We also have to add the corresponding data to the other fields.
-----  END  -----