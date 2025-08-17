from django.db import models
from django.utils import timezone


class Order(models.Model):
	created_at = models.DateTimeField(default=timezone.now)
	completed_at = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=12, default='pending', choices=[('pending','Pending'),('completed','Completed')])
	price_band = models.IntegerField()
	vat_basis = models.CharField(max_length=4, choices=[('take','Takeaway'),('eat','Eatin')])
	show_net = models.BooleanField(default=False)
	total_gross = models.IntegerField(default=0, help_text="Total in pence (gross)")
	total_net = models.IntegerField(default=0, help_text="Total in pence (net, takeaway basis)")
	payment_method = models.CharField(max_length=20, blank=True, default='')
	crew_id = models.CharField(max_length=20, blank=True, default='')
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
