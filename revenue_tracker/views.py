import datetime

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
        if from_date is None:
            from_date = datetime.date.today()
        if to_date is None:
            to_date = datetime.date.today()
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
        context['report_including_unfulfilled'] = Transaction.objects.get_royalties_report(
            from_date=from_date,
            to_date=to_date,
            include_in_progress=True,
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

        quarters = {
            'Q1': ['01-01', '03-31'],
            'Q2': ['04-01', '06-30'],
            'Q3': ['07-01', '09-30'],
            'Q4': ['10-01', '12-31'],
        }

        year = self.request.GET.get('year', None)
        quarter = self.request.GET.get('quarter', None)

        dates_fulfilled = Transaction.objects.values('date_fulfilled').aggregate(
            Min('date_fulfilled'), Max('date_fulfilled'))

        if year:
            if quarter:
                period = quarters[quarter]
            else:
                period = ['01-01', '12-31']

            from_date='{}-{}'.format(year, period[0])
            to_date='{}-{}'.format(year, period[1])

        else:
            from_date = self.request.GET.get(
                'from_date', dates_fulfilled['date_fulfilled__min'])
            to_date = self.request.GET.get(
                'to_date', dates_fulfilled['date_fulfilled__max'])
            if from_date == '':
                from_date = dates_fulfilled['date_fulfilled__min']
            if to_date == '':
                to_date = dates_fulfilled['date_fulfilled__max']
            if from_date is None:
                from_date = datetime.date.today()
            if to_date is None:
                to_date = datetime.date.today()

        first_date = dates_fulfilled['date_fulfilled__min']
        last_date = dates_fulfilled['date_fulfilled__max']

        return [from_date, to_date, first_date, last_date]

    def get_context_data(self, **kwargs):
        context = super(TransactionList, self).get_context_data(**kwargs)
        transaction_date_range = self._transaction_date_range()
        from_date=transaction_date_range[0]
        to_date=transaction_date_range[1]
        first_date=transaction_date_range[2]
        last_date=transaction_date_range[3]
        context['year_range'] = range(first_date.year, last_date.year + 1)
        context['tx_date_range'] = {
            2016: ['Q2', 'Q3', 'Q4'],
            2017: ['Q1', 'Q2', 'Q3', 'Q4'],
            2018: ['Q1', 'Q2'],
        }
        context['year'] = self.request.GET.get('year', None)
        context['quarter'] = self.request.GET.get('quarter', None)
        context['report'] = Transaction.objects.get_royalties_report(
            from_date=from_date,
            to_date=to_date)
        context['from_date'] = str(from_date)
        context['to_date'] = str(to_date)
        context['unfulfilled_list'] = Transaction.objects.filter(
            date_fulfilled=None)
        context['report_including_unfulfilled'] = Transaction.objects.get_royalties_report(
            from_date=from_date,
            to_date=to_date,
            include_in_progress=True)
        context['report_unfulfilled'] = Transaction.objects.get_royalties_report(
            in_progress_only=True)
        return context

    def get_queryset(self):
        transaction_date_range = self._transaction_date_range()
        if transaction_date_range == [None, None]:
            return None
        else:
            return Transaction.objects.filter(
                date_fulfilled__gte=transaction_date_range[0],
                date_fulfilled__lte=transaction_date_range[1])
