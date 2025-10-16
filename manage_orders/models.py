from django.db import models
from django.utils import timezone


class ChannelMapping(models.Model):
	"""Represents a selectable sales channel that maps to a price band.

	Fields:
		name: Human readable description shown to operators (e.g. "Just Eat - Deliver").
		band: Integer price band (1..6) used to resolve price columns.
		channel_code: Short combined code including fulfilment (e.g. JE-D) displayed for clarity.
		co_number: Short code stored with the order (band_co_number) for reporting (e.g. JE, DV, SO).
		active: Soft enable/disable without deleting historic rows.
		sort_order: Allows deterministic ordering inside selection modal.
		is_third_party_delivery: True if this channel is a third‑party delivery platform (e.g., Just Eat - Deliver, Deliveroo - Deliver, Uber - Deliver).
	"""
	name = models.CharField(max_length=120)
	band = models.PositiveSmallIntegerField()
	channel_code = models.CharField(max_length=10, help_text="Code incl. fulfilment suffix e.g. JE-D, SO-C")
	co_number = models.CharField(max_length=4, help_text="Short channel/company code persisted on Order")
	active = models.BooleanField(default=True)
	sort_order = models.PositiveIntegerField(default=0)
	is_third_party_delivery = models.BooleanField(default=False, help_text="True if this channel is a third‑party delivery platform (e.g., Just Eat - Deliver, Deliveroo - Deliver, Uber - Deliver)")

	class Meta:
		ordering = ["sort_order", "name"]
		unique_together = [("channel_code", "band")]

	def __str__(self):
		return f"{self.name} (Band {self.band})"


class Order(models.Model):
	created_at = models.DateTimeField(default=timezone.now)
	packed_at = models.DateTimeField(null=True, blank=True)
	completed_at = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=12, default='preparing', choices=[('preparing','Preparing'),('packed','Packed'),('dispatched','Dispatched')])
	price_band = models.IntegerField()
	vat_basis = models.CharField(max_length=4, choices=[('take','Takeaway'),('eat','Eatin')])
	show_net = models.BooleanField(default=False)
	total_gross = models.IntegerField(default=0, help_text="Total in pence (gross)")
	total_net = models.IntegerField(default=0, help_text="Total in pence (net, takeaway basis)")
	payment_method = models.CharField(max_length=20, blank=True, default='')
	crew_id = models.CharField(max_length=20, blank=True, default='')
	band_co_number = models.CharField(max_length=4, blank=True, default='', help_text="Channel/company code associated with the selected price band (e.g. SO, JE, DV).")
	notes = models.TextField(blank=True)

	def __str__(self):
		return f"Order #{self.pk} ({self.created_at:%Y-%m-%d %H:%M})"


class OrderLine(models.Model):
	order = models.ForeignKey(Order, related_name='lines', on_delete=models.CASCADE)
	item_code = models.IntegerField()
	item_type = models.CharField(max_length=10, choices=[('product','Product'),('combo','Combo')])
	name = models.CharField(max_length=120)
	variant_label = models.CharField(max_length=40, blank=True)
	is_meal = models.BooleanField(default=False)
	qty = models.IntegerField(default=1)
	unit_price_gross = models.IntegerField(help_text="Pence")
	line_total_gross = models.IntegerField(help_text="Pence")
	meta = models.JSONField(default=dict, blank=True)

	def __str__(self):
		return f"{self.name} x{self.qty} @ {self.unit_price_gross}"
