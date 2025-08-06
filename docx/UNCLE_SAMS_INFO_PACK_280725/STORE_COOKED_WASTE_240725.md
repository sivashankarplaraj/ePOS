# COOKED WASTE   								Date  24/07/25
How to store data into the CSV files
CONTENTS
# -------------------------------------------------------------------------------------------------------------
Hamburger,  Regular Fries   ( Cooked Waste,  Standard price )
Cheeseburger,  Strawberry Shake,  Regular Fries   ( Cooked Waste,  Meal,  Standard price )
Six bites  -  Choose an optional product   ( Cooked Waste,  Standard price )
Sharing Platter   ( Cooked Waste,  Standard price )
NOTE
The prices shown on this document are not the latest prices.
Hamburger,  Regular Fries   ( Cooked Waste,  Standard price )
1 – Hamburger
30 – Regular Fries
In MP file
Do not have to store data in MP file.
In PD file, for record with COMBO = False and PRODNUMB
1 – Hamburger  	( add 1 to column  WASTE )
30 – Regular Fries	( add 1 to column  WASTE )
In RV file,
TWASTEVAL = 562
Cheeseburger,  Strawberry Shake,  Regular Fries   ( Cooked Waste,  Meal,  										Standard price )
3 – Cheeseburger
30 – Regular Fries
62 – Strawberry Shk
In MP file
3 – Cheeseburger  	( add 1 to column  WASTE )
30 – Regular Fries	( No need to update column  WASTE )
62 – Strawberry Shk	( No need to update column  WASTE )
In PD file, for record with COMBO = False and PRODNUMB
3 –  Cheeseburger  	( add 1 to column  WASTE )
30 – Regular Fries	( add 1 to column  WASTE )
62 – Strawberry Shk	( add 1 to column  WASTE )
In RV file
TWASTEVAL = 746
Six bites  -  Choose an optional product   (  Cooked Waste,  Standard price )
Optional products for  “71  Six Bites”  are
26 - Dip Ketchup
27 - Dip Mayo
28 - Dip Chilli
29 - Dip Garlic Mayo
39 - Dip BBQ
101 - Dip 1000 Isle
110 - Dip None
Suppose we have chosen product “26  Dip Ketchup” from the list of optional products.
In MP file
Do not have to store data in MP file.
In PD file, for record with COMBO = False and PRODNUMB
26 –  Dip Ketchup  	( add 1 to column  OPTION )
71 – Six Bites   	( add 1 to column  WASTE )
In RV file
TWASTEVAL = 438
Sharing Platter    ( Cooked Waste,  Standard price )
Suppose we have ordered combination product  “4  Sharing Platter” and have chosen product  “27  Dip Mayo” from the list of optional products for this combination product.
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
In MP file
Do not have to store data in MP file.
In PD file
For record with COMBO = False and PRODNUMB
27 – Dip Mayo	( add 1 to column  WASTE )
71 – Six Bites  	( add 1 to column  WASTE )
82 – Onion Rings 8    	( add 1 to column  WASTE )
95 – Mozarela Fingers  ( add 1 to column  WASTE )
For record with COMBO = True and PRODNUMB
4 – Sharing Platter  	( add 1 to column  WASTE )
In RV file
TWASTEVAL = 779
-----  END  -----