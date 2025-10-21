from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone

from .forms import StartShiftForm, CashUpMainForm, ReportFilterForm
from .models import Shift, Float, CashUp, CashUpEntry, Denomination
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


def _has_group(user, name: str) -> bool:
    try:
        return user.is_superuser or user.groups.filter(name=name).exists()
    except Exception:
        return True  # if groups aren’t configured, do not block


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
    if request.user.groups.exists() and not _has_group(request.user, 'Cashier'):
        messages.error(request, 'You do not have permission to start a shift.')
        return redirect('cashup:index')
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
    if request.user.groups.exists() and not _has_group(request.user, 'Cashier'):
        messages.error(request, 'You do not have permission to do cash-up.')
        return redirect('cashup:index')
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
    if request.user.groups.exists() and not _has_group(request.user, 'Cashier'):
        messages.error(request, 'You do not have permission to close a shift.')
        return redirect('cashup:index')
    shift = Shift.objects.filter(user=request.user, is_closed=False).order_by('-start_time').first()
    if not shift:
        messages.error(request, 'No active shift to close.')
        return redirect('cashup:index')
    # Ensure a cash-up record exists before closing
    if not CashUp.objects.filter(shift=shift).exists():
        messages.error(request, 'Please complete a cash-up before closing the shift.')
        return redirect('cashup:do')
    shift.is_closed = True
    shift.end_time = timezone.now()
    shift.save(update_fields=['is_closed','end_time'])
    messages.success(request, 'Shift closed.')
    return redirect('cashup:index')


@login_required
def report(request):
    # Managers-only report; fall back to allow if no groups configured
    if request.user.groups.exists() and not _has_group(request.user, 'Manager'):
        messages.error(request, 'You do not have permission to view reports.')
        return redirect('cashup:index')
    form = ReportFilterForm(request.GET or None)
    qs = CashUp.objects.select_related('shift', 'shift__user').order_by('-created_at')
    if form.is_valid():
        sd = form.cleaned_data.get('start_date')
        ed = form.cleaned_data.get('end_date')
        usr = form.cleaned_data.get('user')
        if sd:
            qs = qs.filter(shift__start_time__date__gte=sd)
        if ed:
            qs = qs.filter(shift__start_time__date__lte=ed)
        if usr:
            qs = qs.filter(shift__user=usr)
    rows = list(qs)
    return render(request, 'cashup/report.html', { 'form': form, 'rows': rows })


class CrewLoginView(LoginView):
    template_name = 'cashup/crew_login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        # Respect ?next= if provided, otherwise go to cashup index
        next_url = self.get_redirect_url()
        return next_url or reverse_lazy('cashup:index')
