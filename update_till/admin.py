from django.contrib import admin
from .models import *

# Register all models with list_display for all fields
model_list = [
    KMeal, KPro, KRev, KWkVat, PdVatTb, PdItem, CombTb, ACodes, BCodes,
    CompPro, OptPro, PChoice, StItems, AppComb, AppProd, GroupTb, MiscSec,
    CombExt, ProdExt, ShopsTb, EposProd, EposGroup, EposFreeProd,
    EposCombFreeProd, EposComb
]

for model in model_list:
    class AllFieldsAdmin(admin.ModelAdmin):
        list_display = [field.name for field in model._meta.fields]
    admin.site.register(model, AllFieldsAdmin)
