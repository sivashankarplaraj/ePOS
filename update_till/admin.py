from django.contrib import admin
from .models import (
    KMeal, KPro, KRev, KWkVat, PdVatTb, PdItem, CombTb, ACodes, BCodes,
    CompPro, OptPro, PChoice, StItems, AppComb, AppProd, GroupTb, MiscSec,
    CombExt, ProdExt, ShopsTb
)

# Register all models in the admin site
admin.site.register(KMeal)
admin.site.register(KPro)
admin.site.register(KRev)
admin.site.register(KWkVat)
admin.site.register(PdVatTb)
admin.site.register(PdItem)
admin.site.register(CombTb)
admin.site.register(ACodes)
admin.site.register(BCodes)
admin.site.register(CompPro)
admin.site.register(OptPro)
admin.site.register(PChoice)
admin.site.register(StItems)
admin.site.register(AppComb)
admin.site.register(AppProd)
admin.site.register(GroupTb)
admin.site.register(MiscSec)
admin.site.register(CombExt)
admin.site.register(ProdExt)
admin.site.register(ShopsTb)

    



