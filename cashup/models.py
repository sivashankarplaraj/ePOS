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
    
# Create shift model
class Shift(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_time']
    def __str__(self):
        return f"Shift for {self.user.username} starting at {self.start_time}"
    
# Create Float model
class Float(models.Model):
    # One-to-one relationship with Shift
    shift = models.OneToOneField(Shift, on_delete=models.CASCADE, related_name='float')
    created_at = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total float amount at the start of the shift")
    notes = models.TextField(blank=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"Float for Shift {self.shift.id} (£{self.amount})"
    
# Create CashUp model
class CashUp(models.Model):
    shift = models.OneToOneField(Shift, on_delete=models.CASCADE, related_name='cashup')
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Expected cash amount based on transactions")
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Actual cash amount counted at the end of the shift")
    difference = models.DecimalField(max_digits=10, decimal_places=2, help_text="Difference between expected and actual amounts")
    created_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"CashUp for Shift {self.shift.id} (£{self.actual_amount}, Diff: £{self.difference})"
    
# Create CashUpEntry model
class CashUpEntry(models.Model):
    cashup = models.ForeignKey(CashUp, on_delete=models.CASCADE, related_name='entries')
    denomination = models.ForeignKey(Denomination, on_delete=models.CASCADE)
    count = models.IntegerField(default=0, help_text="Number of this denomination counted")
    # total value property = denomination.value * count
    @property
    def total_value(self):
        return self.denomination.value * self.count
    class Meta:
        ordering = ['denomination__value']
    def __str__(self):
        return f"{self.count} x {self.denomination.name} (£{self.total_value})"
    
