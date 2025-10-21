from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import StartShiftForm, CashUpMainForm
from .models import Shift, Float, CashUp, CashUpEntry, Denomination


@login_required
def index(request):
    # Show current/last shift and actions
    active_shift = Shift.objects.filter(user=request.user, is_closed=False).order_by('-start_time').first()
    floats = Float.objects.filter(shift=active_shift).first() if active_shift else None
    cashup = CashUp.objects.filter(shift=active_shift).first() if active_shift else None
    ctx = { 'active_shift': active_shift, 'float': floats, 'cashup': cashup }
    return render(request, 'cashup/index.html', ctx)


@login_required
@transaction.atomic
def start_shift(request):
    if request.method == 'POST':
        form = StartShiftForm(request.POST)
        if form.is_valid():
            # Close any previous open shift for this user
            prev = Shift.objects.filter(user=request.user, is_closed=False).first()
            if prev:
                prev.is_closed = True
                prev.end_time = timezone.now()
                prev.save(update_fields=['is_closed','end_time'])
            # Create new shift and float
            sh = Shift.objects.create(user=request.user, start_time=timezone.now(), is_closed=False)
            Float.objects.create(shift=sh, amount=form.cleaned_data['amount'], notes=form.cleaned_data.get('notes',''))
            messages.success(request, 'Shift started and float recorded.')
            return redirect('cashup:index')
    else:
        form = StartShiftForm()
    return render(request, 'cashup/start_shift.html', { 'form': form })


@login_required
@transaction.atomic
def do_cashup(request):
    shift = Shift.objects.filter(user=request.user, is_closed=False).order_by('-start_time').first()
    if not shift:
        messages.error(request, 'No active shift. Start a shift first.')
        return redirect('cashup:index')
    denoms = Denomination.objects.order_by('-value')
    if request.method == 'POST':
        form = CashUpMainForm(request.POST)
        # parse counts
        counts = {}
        total_actual = Decimal('0.00')
        for d in denoms:
            key = f'denom_{d.pk}'
            try:
                c = int(request.POST.get(key,'0') or '0')
            except ValueError:
                c = 0
            c = max(0, c)
            counts[d] = c
            total_actual += (d.value * c)
        if form.is_valid():
            expected = form.cleaned_data['expected_amount']
            notes = form.cleaned_data.get('notes','')
            cashup = CashUp.objects.filter(shift=shift).first()
            if not cashup:
                cashup = CashUp.objects.create(shift=shift, expected_amount=expected, actual_amount=total_actual, difference=(total_actual-expected), notes=notes)
            else:
                cashup.expected_amount = expected
                cashup.actual_amount = total_actual
                cashup.difference = (total_actual-expected)
                cashup.notes = notes
                cashup.save()
            # replace entries
            CashUpEntry.objects.filter(cashup=cashup).delete()
            bulk = [CashUpEntry(cashup=cashup, denomination=d, count=counts[d]) for d in denoms if counts[d] > 0]
            if bulk:
                CashUpEntry.objects.bulk_create(bulk)
            messages.success(request, 'Cash-up saved.')
            return redirect('cashup:index')
    else:
        form = CashUpMainForm(initial={ 'expected_amount': Decimal('0.00') })
    return render(request, 'cashup/do_cashup.html', { 'form': form, 'denoms': denoms })


@login_required
@transaction.atomic
def close_shift(request):
    shift = Shift.objects.filter(user=request.user, is_closed=False).order_by('-start_time').first()
    if not shift:
        messages.error(request, 'No active shift to close.')
        return redirect('cashup:index')
    shift.is_closed = True
    shift.end_time = timezone.now()
    shift.save(update_fields=['is_closed','end_time'])
    messages.success(request, 'Shift closed.')
    return redirect('cashup:index')
