from django.db import models
from django.utils import timezone

# Creat Denomination model
class Denomination(models.Model):
    name = models.CharField(max_length=50, help_text="Name of the denomination (e.g., 'Five Pound Note')")
    value = models.DecimalField(max_digits=6, decimal_places=2, help_text="Monetary value of the denomination (e.g., 5.00)")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'value']

    def __str__(self):
        return f"{self.name} (£{self.value})"