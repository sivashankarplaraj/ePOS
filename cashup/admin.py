from django.contrib import admin
from .models import Denomination, Shift, Float, CashUp, CashUpEntry

@admin.register(Denomination)
class DenominationAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("value",)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("user", "start_time", "end_time", "is_closed")
    list_filter = ("is_closed", "start_time")
    search_fields = ("user__username",)

@admin.register(Float)
class FloatAdmin(admin.ModelAdmin):
    list_display = ("shift", "amount", "created_at")
    search_fields = ("shift__user__username",)

class CashUpEntryInline(admin.TabularInline):
    model = CashUpEntry
    extra = 0

@admin.register(CashUp)
class CashUpAdmin(admin.ModelAdmin):
    list_display = ("shift", "expected_amount", "actual_amount", "difference", "created_at")
    search_fields = ("shift__user__username",)
    inlines = [CashUpEntryInline]
