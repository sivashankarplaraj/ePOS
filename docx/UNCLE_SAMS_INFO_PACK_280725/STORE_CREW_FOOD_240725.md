# CREW FOOD   								Date  24/07/25
How to store data into the daily CSV files
CONTENTS
# -------------------------------------------------------------------------------------------------------------
Hamburger,  Regular Fries   ( Crew Food,  Standard price )
Vanilla Shake   (Crew Food,  Standard price )
Cheeseburger,  Strawberry Shake,  Regular Fries   (Crew Food,  Meal,  Standard price )
Six bites  -  Choose an optional product   (Crew Food,  Standard price )
Chosen dip : Dip Ketchup
Sharing Platter   (Crew Food,  Standard price )
Chosen dip : Dip Mayo
NOTE
The prices shown on this document are not the latest prices.
Hamburger,  Regular Fries   ( Crew Food,  Standard price )
Product			Standard Price
Code	Name			Excl Vat
------	-------------------------	------------------
1	Hamburger		£3.88
30	Regular Fries		£1.83
------	-------------------------	------------------
Total			£5.71
In MP file
There is no need to store any data in the MP file for this order.
In PD file, for record with COMBO = False and PRODNUMB
1 – Hamburger  	( add 1 to column  STAFF )
30 – Regular Fries	( add 1 to column  STAFF )
In RV file
We add  571  to TSTAFFVAL.
TSTAFFVAL  is the value of crew food in pence on the given date.
Vanilla Shake   ( Crew Food,  Standard price )
Product			Standard Price
Code	Name			Excl Vat
------	-------------------------	------------------
69	Vanilla Shake		£2.38
------	-------------------------	------------------
Total			£2.38
In MP file
There is no need to store any data in the MP file for this order.
In PD file, for record with COMBO = False and PRODNUMB
69 – Vanilla Shake  	( add 1 to column  STAFF )
In RV file
We add  238  to TSTAFFVAL.
TSTAFFVAL  is the value of crew food in pence on the given date.
Cheeseburger,  Strawberry Shake,  Regular Fries   (Crew Food,  Meal,  										Standard price )
Product			Part of a
Code	Name			Meal Price Excl Vat
------	-------------------------	------------------
3	Cheeseburger		£4.21
30	Regular Fries		£1.08
62	Strawberry Shk	£2.33
------	-------------------------	------------------
Total			£7.62
In MP file
3 – Cheeseburger  	( add 1 to column  STAFF )
30 – Regular Fries	( No need to update column  STAFF )
62 – Strawberry Shk	( No need to update column  STAFF )
In PD file, for record with COMBO = False and PRODNUMB
3 –  Cheeseburger  	( add 1 to column  STAFF )
30 – Regular Fries	( add 1 to column  STAFF )
62 – Strawberry Shk	( add 1 to column  STAFF )
In RV file
We add  762  to TSTAFFVAL.
TSTAFFVAL  is the value of crew food in pence on the given date.
Six bites  -  Choose an optional product   (  Crew Food,  Standard price )
Optional products for  “71  Six Bites”  are
26 - Dip Ketchup
27 - Dip Mayo
28 - Dip Chilli
29 - Dip Garlic Mayo
39 - Dip BBQ
101 - Dip 1000 Isle
110 - Dip None
Suppose we have chosen product “26  Dip Ketchup” from the list of optional products.
Product			Standard Price
Code	Name			Excl Vat
------	-------------------------	------------------
71	Six Bites		£4.42
------	-------------------------	------------------
Total			£4.42
In MP file
There is no need to store any data in the MP file for this order.
In PD file, for record with COMBO = False and PRODNUMB
26 –  Dip Ketchup  	( add 1 to column  OPTION )
71 – Six Bites   	( add 1 to column  STAFF )
In RV file
We add  442  to TSTAFFVAL.
TSTAFFVAL  is the value of crew food in pence on the given date.
Sharing Platter    ( Crew Food,  Standard price )
Suppose we have chosen product  “27  Dip Mayo” from the list of optional products for the combination product  “4  Sharing Platter”.
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
Combination
Product			Standard Price
Code	Name			Excl Vat
------	-------------------------	------------------
4	Sharing Platter		£7.92
------	-------------------------	------------------
Total			£7.92
In MP file
There is no need to store any data in the MP file for this order.
In PD file
For record with COMBO = False and PRODNUMB
27 – Dip Mayo	( add 1 to column  STAFF )
71 – Six Bites  	( add 1 to column  STAFF )
82 – Onion Rings 8    	( add 1 to column  STAFF )
95 – Mozarela Fingers  ( add 1 to column  STAFF )
For record with COMBO = True and PRODNUMB
4 – Sharing Platter  	( add 1 to column  STAFF )
In RV file
We add  792  to TSTAFFVAL.
TSTAFFVAL  is the value of crew food in pence on the given date.
-----  END  -----