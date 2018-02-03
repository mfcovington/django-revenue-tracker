from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Min, Max
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import Customer, Transaction


class CustomerDetail(LoginRequiredMixin, DetailView):
    context_object_name = 'customer'
    model = Customer

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
        context = super(CustomerDetail, self).get_context_data(**kwargs)
        transaction_date_range = self._transaction_date_range()
        from_date=transaction_date_range[0]
        to_date=transaction_date_range[1]
        context['report'] = Transaction.objects.get_royalties_report(
            from_date=from_date,
            to_date=to_date,
            customer_id=self.object.pk)
        context['from_date'] = str(from_date)
        context['to_date'] = str(to_date)
        context['fulfilled_list'] = Transaction.objects.filter(
            date_fulfilled__gte=from_date,
            date_fulfilled__lte=to_date,
            customer__pk=self.object.pk)
        context['unfulfilled_list'] = Transaction.objects.filter(
            date_fulfilled=None,
            customer__pk=self.object.pk)
        context['report_unfulfilled'] = Transaction.objects.get_royalties_report(
            in_progress_only=True,
            customer_id=self.object.pk)
        context['tx_count'] = len(set(self.object.transaction_set.values_list('date')))
        return context


class CustomerList(LoginRequiredMixin, ListView):
    context_object_name = 'customer_list'
    model = Customer


class TransactionDetail(LoginRequiredMixin, DetailView):
    context_object_name = 'transaction'
    model = Transaction


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
        context['unfulfilled_list'] = Transaction.objects.filter(
            date_fulfilled=None)
        context['report_unfulfilled'] = Transaction.objects.get_royalties_report(
            in_progress_only=True)
        return context

    def get_queryset(self):
        transaction_date_range = self._transaction_date_range()
        return Transaction.objects.filter(
            date_fulfilled__gte=transaction_date_range[0],
            date_fulfilled__lte=transaction_date_range[1])
