
from django.db import models

# Table 1: K_MEAL
# Stores the number of meals sold per product per date.
# Table K_Meal is a template for MP<dd/mm/yy>, where dd/mm/yy is the given date. 
# We store the number of meals sold on date dd/mm/yy in table MP<dd/mm/yy>. 
# Sales of meal products are also added to the cumulative sales of the 
# corresponding products in table PD, where dd/mm/yy is the given date. 
# Table K_PRO is a template for PD. There is a record for each product at 
# the shop in table K_Meal.
class KMeal(models.Model):
    PRODNUMB = models.IntegerField(help_text="Product code.")
    TAKEAWAY = models.IntegerField(help_text="Total number sold as takeaway meals on the given date.")
    EATIN = models.IntegerField(help_text="Total number sold as eatin meals on the given date.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 2: K_PRO
# Tracks product and combination product sales and related stats per date.
# Table K_PRO is a template for PD<dd/mm/yy>, where dd/mm/yy is the given date. 
# We store the number of products sold on date dd/mm/yy in table PD<dd/mm/yy>. 
# There is a record for each product at the shop in table PD<dd/mm/yy>. 
# There is a record for each combination product at the shop in table PD<dd/mm/yy>.
class KPro(models.Model):
    PRODNUMB = models.IntegerField(help_text="Product or combination product code.")
    COMBO = models.BooleanField(help_text="True if combination product, else False.")
    TAKEAWAY = models.IntegerField(help_text="Total number sold as takeaway on the given date.")
    EATIN = models.IntegerField(help_text="Total number sold as eatin on the given date.")
    WASTE = models.IntegerField(help_text="Total entered as Cooked Waste on the given date.")
    STAFF = models.IntegerField(help_text="Total entered as Crew Food on the given date.")
    OPTION = models.IntegerField(help_text="Total chosen as optional product for products on the given date.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 3: K_REV
# Tracks POS financials for a given date.
# Table K_REV is a template for RV<dd/mm/yy>, where dd/mm/yy is the given date. 
# For example, Table RV210725 is for date 21/07/25. 
# There is only one record in table RV<dd/mm/yy>.
class KRev(models.Model):
    TCASHVAL = models.BigIntegerField(help_text="Cash in drawer (pence) recorded by POS.")
    TCHQVAL = models.BigIntegerField(help_text="Cheques in drawer (pence) recorded by POS.")
    TCARDVAL = models.BigIntegerField(help_text="Card payments (pence) recorded by POS.")
    TONACCOUNT = models.BigIntegerField(help_text="On account payments (pence) recorded by POS.")
    TSTAFFVAL = models.BigIntegerField(help_text="Crew food value (pence) recorded by POS.")
    TWASTEVAL = models.BigIntegerField(help_text="Cooked waste value (pence) recorded by POS.")
    TCOUPVAL = models.BigIntegerField(help_text="Coupons value (pence) recorded by POS.")
    TPAYOUTVA = models.BigIntegerField(help_text="Paid outs (pence) recorded by POS.")
    TTOKENVAL = models.BigIntegerField(help_text="Vouchers value (pence) recorded by POS.")
    # Amount of combination discount in pence recorded by POS on the given date. 
    # A = Total amount due for all the products in the order in pence 
    # B = Total amount due for all the combination products in the order in pence 
    # Combination discount for an order = A – B
    TDISCNTVA = models.BigIntegerField(help_text="Combination discount (pence) recorded by POS.")
    TTOKENNOVR = models.BigIntegerField(help_text="Voucher overage (pence) recorded by POS.")
    TGOLARGENU = models.IntegerField(help_text="Number of go large recorded by POS.")
    TMEAL_DISCNT = models.BigIntegerField(help_text="Discount for meals (pence) recorded by POS.")
    ACTCASH = models.BigIntegerField(help_text="Actual cash taken by POS (pence).")
    ACTCHQ = models.BigIntegerField(help_text="Actual cheques taken by POS (pence).")
    ACTCARD = models.BigIntegerField(help_text="Actual card payments taken by card machine (pence).")
    VAT = models.BigIntegerField(help_text="Total VAT due (pence) on the given date.")
    XPV = models.BigIntegerField(help_text="Extended product value (pence) on the given date. Not required.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 4: K_WK_VAT
# Tracks VAT rates and totals for each day of the week.
# Table K_Wk_Vat stores values of VAT at different rates on each day of the week. 
# There is one record for each VAT rate. 
# Table PdVat_Tb stores the details of VAT rates. There is one record for each VAT rate. 
# We initialize table K_Wk_Vat when we start a new week. 
# For each record in table PDVat_Tb, we add a record to table K_Wk_Vat. 
# We update table K_Wk_Vat on each day of the week.
class KWkVat(models.Model):
    VAT_CLASS = models.PositiveSmallIntegerField(help_text="VAT class.")
    VAT_RATE = models.FloatField(help_text="VAT rate for this class.")
    TOT_VAT_1 = models.FloatField(help_text="Total VAT due (Monday).")
    TOT_VAT_2 = models.FloatField(help_text="Total VAT due (Tuesday).")
    TOT_VAT_3 = models.FloatField(help_text="Total VAT due (Wednesday).")
    TOT_VAT_4 = models.FloatField(help_text="Total VAT due (Thursday).")
    TOT_VAT_5 = models.FloatField(help_text="Total VAT due (Friday).")
    TOT_VAT_6 = models.FloatField(help_text="Total VAT due (Saturday).")
    TOT_VAT_7 = models.FloatField(help_text="Total VAT due (Sunday).")
    T_VAL_EXCLVAT_1 = models.FloatField(help_text="Total value excluding VAT (Monday).")
    T_VAL_EXCLVAT_2 = models.FloatField(help_text="Total value excluding VAT (Tuesday).")
    T_VAL_EXCLVAT_3 = models.FloatField(help_text="Total value excluding VAT (Wednesday).")
    T_VAL_EXCLVAT_4 = models.FloatField(help_text="Total value excluding VAT (Thursday).")
    T_VAL_EXCLVAT_5 = models.FloatField(help_text="Total value excluding VAT (Friday).")
    T_VAL_EXCLVAT_6 = models.FloatField(help_text="Total value excluding VAT (Saturday).")
    T_VAL_EXCLVAT_7 = models.FloatField(help_text="Total value excluding VAT (Sunday).")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 5: PDVAT_TB
# Stores VAT class details.
# CSV file: PDVAT_TB.CSV
class PdVatTb(models.Model):
    VAT_CLASS = models.PositiveSmallIntegerField(help_text="VAT class.")
    VAT_RATE = models.FloatField(help_text="VAT rate for this class.")
    VAT_DESC = models.CharField(max_length=20, help_text="Description of this VAT class.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")
    

# Table 6: PDITEM
# Stores product details for each shop.
# CSV file: PDITEM<n>.CSV
# <n> is the shop number (1-15)
class PdItem(models.Model):
    PRODNUMB = models.IntegerField(help_text="Product code.")
    PRODNAME = models.CharField(max_length=16, help_text="Product name.")
    EAT_VAT_CLASS = models.PositiveSmallIntegerField(help_text="VAT class for Eatin order.")
    TAKE_VAT_CLASS = models.PositiveSmallIntegerField(help_text="VAT class for Takeaway order.")
    READBACK_ORD = models.PositiveSmallIntegerField(help_text="Read Back sorting order.")
    MEAL_ONLY = models.BooleanField(help_text="True if only sold as part of meal.")
    MEAL_CODE = models.PositiveSmallIntegerField(help_text="Meal code.")
    MEAL_DRINK = models.PositiveSmallIntegerField(help_text="Meal drink code.")
    T_DRINK_CD = models.IntegerField(help_text="Product code of trade up drink.")
    VATPR = models.IntegerField(help_text="Current price incl. VAT (standard price).")
    DC_VATPR = models.IntegerField(help_text="Discounted price incl. VAT (standard price).")
    VATPR_2 = models.IntegerField(help_text="Current price incl. VAT (price band 2).")
    DC_VATPR_2 = models.IntegerField(help_text="Discounted price incl. VAT (price band 2).")
    VATPR_3 = models.IntegerField(help_text="Current price incl. VAT (price band 3).")
    DC_VATPR_3 = models.IntegerField(help_text="Discounted price incl. VAT (price band 3).")
    VATPR_4 = models.IntegerField(help_text="Current price incl. VAT (price band 4).")
    DC_VATPR_4 = models.IntegerField(help_text="Discounted price incl. VAT (price band 4).")
    VATPR_5 = models.IntegerField(help_text="Current price incl. VAT (price band 5).")
    DC_VATPR_5 = models.IntegerField(help_text="Discounted price incl. VAT (price band 5).")
    VATPR_6 = models.IntegerField(help_text="Current price incl. VAT (price band 6).")
    DC_VATPR_6 = models.IntegerField(help_text="Discounted price incl. VAT (price band 6).")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 7: COMBTB
# Stores combination product details for each shop.
# CSV file: COMBTB<n>.CSV
# <n> is the shop number (1-15)
class CombTb(models.Model):
    COMBONUMB = models.IntegerField(help_text="Combination product code.")
    DESC = models.CharField(max_length=16, help_text="Name of combination product.")
    T_COMB_NUM = models.IntegerField(help_text="Trade up combination product code.")
    EAT_VAT_CLASS = models.PositiveSmallIntegerField(help_text="VAT class for Eatin order.")
    TAKE_VAT_CLASS = models.PositiveSmallIntegerField(help_text="VAT class for Takeaway order.")
    VATPR = models.IntegerField(help_text="Current price incl. VAT (standard price).")
    T_VATPR = models.IntegerField(help_text="Trade up price incl. VAT (standard price).")
    VATPR_2 = models.IntegerField(help_text="Current price incl. VAT (price band 2).")
    T_VATPR_2 = models.IntegerField(help_text="Trade up price incl. VAT (price band 2).")
    VATPR_3 = models.IntegerField(help_text="Current price incl. VAT (price band 3).")
    T_VATPR_3 = models.IntegerField(help_text="Trade up price incl. VAT (price band 3).")
    VATPR_4 = models.IntegerField(help_text="Current price incl. VAT (price band 4).")
    T_VATPR_4 = models.IntegerField(help_text="Trade up price incl. VAT (price band 4).")
    VATPR_5 = models.IntegerField(help_text="Current price incl. VAT (price band 5).")
    T_VATPR_5 = models.IntegerField(help_text="Trade up price incl. VAT (price band 5).")
    VATPR_6 = models.IntegerField(help_text="Current price incl. VAT (price band 6).")
    T_VATPR_6 = models.IntegerField(help_text="Trade up price incl. VAT (price band 6).")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 8: ACODES
# Stores 'A' code stock components for products.
# CSV file: ACODES.CSV
class ACodes(models.Model):
    PRODNUMB = models.IntegerField(help_text="Product code.")
    ST_CODENUM = models.IntegerField(help_text="A code stock component number.")
    QTY = models.FloatField(help_text="Quantity of this A code stock component.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 9: BCODES
# Stores 'B' code stock components for products.
# CSV file: BCODES.CSV
class BCodes(models.Model):
    PRODNUMB = models.IntegerField(help_text="Product code.")
    ST_CODENUM = models.IntegerField(help_text="B code stock component number.")
    QTY = models.FloatField(help_text="Quantity of this B code stock component.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 10: COMP_PRO
# Stores compulsory products for combinations.
# CSV file: COMP_PRO.CSV
class CompPro(models.Model):
    COMBONUMB = models.IntegerField(help_text="Combination product code.")
    PRODNUMB = models.IntegerField(help_text="Product code of compulsory product.")
    T_PRODNUMB = models.IntegerField(help_text="Trade up product code (0 if none).")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 11: OPT_PRO
# Stores optional products for combinations.
# CSV file: OPT_PRO.CSV
class OptPro(models.Model):
    COMBONUMB = models.IntegerField(help_text="Combination product code.")
    PRODNUMB = models.IntegerField(help_text="Product code of optional product.")
    T_PRODNUMB = models.IntegerField(help_text="Trade up product code (0 if none).")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 12: P_CHOICE
# Stores optional products for each product.
# CSV file: P_CHOICE.CSV
class PChoice(models.Model):
    PRODNUMB = models.IntegerField(help_text="Product code.")
    OPT_PRODNUMB = models.IntegerField(help_text="Optional product code for this product.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 13: ST_ITEMS
# Stores stock item codes and descriptions.
# CSV file: ST_ITEMS.CSV
class StItems(models.Model):
    CODEALPH = models.CharField(max_length=1, help_text="First part of stock item code (letter).")
    ST_CODENUM = models.IntegerField(help_text="Second part of stock item code (4-digit number).")
    ITEM = models.CharField(max_length=18, help_text="Description for this stock item.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 14: APP_COMB
# Stores combination products for reporting.
# CSV file: APP_COMB.CSV
class AppComb(models.Model):
    COMBONUMB = models.IntegerField(help_text="Combination product code.")
    DESC = models.CharField(max_length=16, help_text="Name of combination product.")
    GROUP_ID = models.PositiveSmallIntegerField(help_text="Section number for report printing.")
    GROUP_SUB_ID = models.IntegerField(help_text="Order in section for report printing.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 15: APP_PROD
# Stores products for reporting.
# CSV file: APP_PROD.CSV
class AppProd(models.Model):
    PRODNUMB = models.IntegerField(help_text="Product code.")
    PRODNAME = models.CharField(max_length=16, help_text="Product name.")
    GROUP_ID = models.PositiveSmallIntegerField(help_text="Section number for report printing.")
    GROUP_SUB_ID = models.IntegerField(help_text="Order in section for report printing.")
    MEAL_ID = models.PositiveSmallIntegerField(help_text="Section number for meal price on report.")
    MEAL_SUB_ID = models.IntegerField(help_text="Order in meal section for report printing.")
    DOUBLE_PDNUMB = models.IntegerField(help_text="Corresponding double product code.")
    TRIPLE_PDNUMB = models.IntegerField(help_text="Corresponding triple product code.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 16: GROUP_TB
# Stores report section details.
# CSV file: GROUP_TB.CSV
class GroupTb(models.Model):
    GROUP_ID = models.PositiveSmallIntegerField(help_text="Section number on report.")
    GROUP_NAME = models.CharField(max_length=16, help_text="Section name.")
    SOURCE_TYPE = models.CharField(max_length=1, help_text="'P' for products, 'C' for combinations.")
    MEAL_GROUP = models.PositiveSmallIntegerField(help_text="Section number for meal products.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 17: MISC_SEC
# Stores miscellaneous items for reporting.
# CSV file: MISC_SEC.CSV
class MiscSec(models.Model):
    PRODNUMB = models.IntegerField(help_text="Product code (0 if not a product).")
    PRODNAME = models.CharField(max_length=16, help_text="Product name (blank if not a product).")
    ITEM_DESC = models.CharField(max_length=20, help_text="Description printed in report column.")
    SEQ_ORDER = models.IntegerField(help_text="Order in Section 10 - Miscellaneous on report.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 18: COMB_EXT
# Stores extended combination product info.
# CSV file: COMB_EXT.CSV
class CombExt(models.Model):
    COMBONUMB = models.IntegerField(help_text="Combination product code.")
    DESC = models.CharField(max_length=16, help_text="Name of combination product.")
    NAME_ON_MENU = models.CharField(max_length=30, help_text="Name shown on the menu.")
    PROD_DESC = models.TextField(max_length=255, help_text="Description of combination product.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 19: PROD_EXT
# Stores extended product info.
# CSV file: PROD_EXT.CSV
class ProdExt(models.Model):
    PRODNUMB = models.IntegerField(help_text="Product code.")
    PRODNAME = models.CharField(max_length=16, help_text="Name of product.")
    NAME_ON_MENU = models.CharField(max_length=30, help_text="Name shown on the menu.")
    COOK_ZONE = models.PositiveSmallIntegerField(help_text="Cooking zone.")
    PROD_DESC = models.TextField(max_length=255, help_text="Description of product.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")

# Table 20: SHOPS_TB
# Stores shop details.
# CSV file: SHOPS_TB.CSV
class ShopsTb(models.Model):
    SHOP_CODE = models.PositiveSmallIntegerField(help_text="Shop code.")
    SHOP_NAME = models.CharField(max_length=10, help_text="Shop name.")
    SHOP_ABBREV = models.CharField(max_length=2, help_text="Shop abbreviation.")
    FRANCHISEE = models.CharField(max_length=25, help_text="Name of franchisee.")
    FULL_NAME = models.CharField(max_length=32, help_text="Company name.")
    ADDRESS_1 = models.CharField(max_length=22, help_text="First line of shop address.")
    ADDRESS_2 = models.CharField(max_length=20, help_text="Second line of shop address.")
    ADDRESS_3 = models.CharField(max_length=17, help_text="Third line of shop address.")
    POST_CODE = models.CharField(max_length=8, help_text="Postcode of shop address.")
    last_updated = models.DateTimeField(auto_now=True, help_text="Last updated timestamp.")
