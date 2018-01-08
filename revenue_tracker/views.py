from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Min, Max
from django.shortcuts import render
from django.views.generic import ListView

from .models import Transaction


class TransactionList(LoginRequiredMixin, ListView):
    context_object_name = 'transaction_list'
    model = Transaction

    def _transaction_date_range(self):
        dates_fulfilled = Transaction.objects.values('date_fulfilled').aggregate(
            Min('date_fulfilled'), Max('date_fulfilled'))
        from_date = self.request.GET.get(
            'from_date', dates_fulfilled['date_fulfilled__min'])
        to_date = self.request.GET.get(
            'to_date', dates_fulfilled['date_fulfilled__max'])
        if from_date == '':
            from_date = dates_fulfilled['date_fulfilled__min']
        if to_date == '':
            to_date = dates_fulfilled['date_fulfilled__max']
        return [from_date, to_date]

    def get_context_data(self, **kwargs):
        context = super(TransactionList, self).get_context_data(**kwargs)
        transaction_date_range = self._transaction_date_range()
        from_date=transaction_date_range[0]
        to_date=transaction_date_range[1]
        context['report'] = Transaction.objects.get_royalties_report(
            from_date=from_date,
            to_date=to_date)
        context['from_date'] = str(from_date)
        context['to_date'] = str(to_date)
        return context

    def get_queryset(self):
        transaction_date_range = self._transaction_date_range()
        return Transaction.objects.filter(
            date_fulfilled__gte=transaction_date_range[0],
            date_fulfilled__lte=transaction_date_range[1])
