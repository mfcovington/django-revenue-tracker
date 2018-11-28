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
        context['tx_count'] = len(set(self.object.transactions.values_list('date')))
        return context


class CustomerList(LoginRequiredMixin, ListView):
    context_object_name = 'customer_list'
    model = Customer


class OutstandingInvoicesList(LoginRequiredMixin, ListView):
    context_object_name = 'transaction_list'
    model = Transaction
    template_name = 'revenue_tracker/outstanding_invoices_list.html'

    def get_context_data(self, **kwargs):
        context = super(OutstandingInvoicesList, self).get_context_data(**kwargs)
        context['outstanding'] = True
        context['report'] = Transaction.objects.get_royalties_report(
            outstanding=True)
        return context

    def get_queryset(self):
        return Transaction.objects.filter(
                date_fulfilled__isnull=False, date_paid__isnull=True
            ).order_by('date_fulfilled')


class PendingTransactionsList(LoginRequiredMixin, ListView):
    context_object_name = 'transaction_list'
    model = Transaction
    template_name = 'revenue_tracker/pending_transactions_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = Transaction.objects.get_royalties_report(
            in_progress_only=True)
        return context

    def get_queryset(self):
        return Transaction.objects.filter(date_fulfilled=None)


class TransactionDetail(LoginRequiredMixin, DetailView):
    context_object_name = 'transaction'
    model = Transaction


class TransactionList(LoginRequiredMixin, ListView):
    context_object_name = 'transaction_list'
    model = Transaction

    _quarters = {
        'Q1': ['01-01', '03-31'],
        'Q2': ['04-01', '06-30'],
        'Q3': ['07-01', '09-30'],
        'Q4': ['10-01', '12-31'],
    }

    def _transaction_date_range(self):
        year = self.request.GET.get('year', None)
        quarter = self.request.GET.get('quarter', None)

        dates_fulfilled = Transaction.objects.values('date_fulfilled').aggregate(
            Min('date_fulfilled'), Max('date_fulfilled'))

        if year:
            if quarter:
                period = self._quarters[quarter]
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

        if isinstance(from_date, str):
            from_date = datetime.date(*[int(d) for d in from_date.split('-')])
        if isinstance(to_date, str):
            to_date = datetime.date(*[int(d) for d in to_date.split('-')])

        first_date = dates_fulfilled['date_fulfilled__min'] or from_date
        last_date = dates_fulfilled['date_fulfilled__max'] or to_date

        return [from_date, to_date, first_date, last_date]

    def get_context_data(self, **kwargs):
        context = super(TransactionList, self).get_context_data(**kwargs)
        transaction_date_range = self._transaction_date_range()
        from_date=transaction_date_range[0]
        to_date=transaction_date_range[1]
        first_date=transaction_date_range[2]
        last_date=transaction_date_range[3]

        tx_date_range = {}
        for year in range(first_date.year, last_date.year + 1):
            tx_date_range[year] = []
            for quarter, quarter_range in self._quarters.items():
                if Transaction.objects.filter(
                    date_fulfilled__gte='{}-{}'.format(year, quarter_range[0]),
                    date_fulfilled__lte='{}-{}'.format(year, quarter_range[1])
                ):
                    tx_date_range[year].append(quarter)

        context['tx_date_range'] = tx_date_range
        context['year'] = self.request.GET.get('year', None)
        context['quarter'] = self.request.GET.get('quarter', None)
        transaction_type = self.request.GET.get('transaction_type', None)
        institution_type = self.request.GET.get('institution_type', None)
        context['transaction_type'] = transaction_type
        context['institution_type'] = institution_type
        context['report'] = Transaction.objects.get_royalties_report(
            from_date=from_date,
            to_date=to_date,
            institution_type=institution_type,
            transaction_type=transaction_type)
        context['from_date'] = str(from_date)
        context['to_date'] = str(to_date)

        type_kwargs = {}
        if institution_type:
            type_kwargs['customer__institution__institution_type'] = institution_type
        if transaction_type:
            type_kwargs['transaction_type'] = transaction_type
        context['unfulfilled_list'] = Transaction.objects.filter(
            date_fulfilled=None, **type_kwargs)

        context['report_including_unfulfilled'] = Transaction.objects.get_royalties_report(
            from_date=from_date,
            to_date=to_date,
            institution_type=institution_type,
            transaction_type=transaction_type,
            include_in_progress=True)
        context['report_unfulfilled'] = Transaction.objects.get_royalties_report(
            institution_type=institution_type,
            transaction_type=transaction_type,
            in_progress_only=True)
        return context

    def get_queryset(self):
        transaction_date_range = self._transaction_date_range()
        if transaction_date_range == [None, None]:
            return None
        else:
            type_kwargs = {}

            institution_type = self.request.GET.get('institution_type', None)
            transaction_type = self.request.GET.get('transaction_type', None)

            if institution_type:
                type_kwargs['customer__institution__institution_type'] = institution_type
            if transaction_type:
                type_kwargs['transaction_type'] = transaction_type

            return Transaction.objects.filter(
                date_fulfilled__gte=transaction_date_range[0],
                date_fulfilled__lte=transaction_date_range[1],
                **type_kwargs,
            )
