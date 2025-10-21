from decimal import Decimal
from django import forms
from django.contrib.auth import get_user_model
from .models import Shift, Float, CashUp, CashUpEntry, Denomination


class StartShiftForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'), label="Float amount")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':3}), label="Notes")


class CashUpMainForm(forms.Form):
    expected_amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'), label="Expected amount")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':3}), label="Notes")


class ReportFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))
    user = forms.ModelChoiceField(queryset=get_user_model().objects.all().order_by('username'), required=False)
