from django.contrib import admin
from .models import Order, OrderLine, ChannelMapping


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


@admin.register(ChannelMapping)
class ChannelMappingAdmin(admin.ModelAdmin):
    list_display = ("name", "band", "channel_code", "co_number", "active", "sort_order")
    list_filter = ("band", "active")
    search_fields = ("name", "channel_code", "co_number")
    list_editable = ("band", "active", "sort_order")
