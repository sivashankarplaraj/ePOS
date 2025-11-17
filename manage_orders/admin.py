from django.contrib import admin
from .models import Order, OrderLine


class OrderLineInline(admin.TabularInline):
	model = OrderLine
	extra = 0
	readonly_fields = ("item_code","item_type","name","variant_label","is_meal","qty","unit_price_gross","line_total_gross")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("id","created_at","status","completed_at","price_band","vat_basis","total_gross","total_net")
	list_filter = ("status","vat_basis","price_band")
	inlines = [OrderLineInline]
	readonly_fields = ("created_at","completed_at")


# ChannelMapping has been deprecated in favour of update_till.PriceBand
