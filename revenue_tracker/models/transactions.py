import os
import datetime

from django.db import models
from django.db.models import Count, F, ExpressionWrapper, Sum

from djmoney.models.fields import MoneyField

from ..models import Customer


ROYALTY_PERCENTAGE = 0.025 # import from settings (for first 1 million. After that, 2.75%)


TRANSACTION_TYPE_CHOICES = [
    ('kit', 'Kit Sale'),
    ('service', 'Service Contract'),
    ('other', 'Other')
]


class BasePriceQuerySet(models.QuerySet):

    def delete(self, *args, **kwargs):
        for obj in self:
            obj.delete()
        super(BasePriceQuerySet, self).delete(*args, **kwargs)


class BasePrice(models.Model):

    class Meta:
        ordering = ['start_date', 'transaction_type']
        unique_together = ['start_date', 'transaction_type']

    objects = BasePriceQuerySet.as_manager()

    start_date = models.DateField()
    transaction_type = models.CharField(
        choices=TRANSACTION_TYPE_CHOICES,
        max_length=7,
    )
    price_per_reaction = MoneyField(
        decimal_places=2,
        default_currency='USD',
        max_digits=8,
    )

    def __str__(self):
        return '{} ({}: {}/rxn)'.format(
            self.start_date, self.transaction_type, self.price_per_reaction)

    def delete(self, *args, **kwargs):
        start_date = self.start_date
        transaction_type = self.transaction_type

        sorted_price_periods = BasePrice.objects.filter(
            transaction_type=transaction_type
        ).annotate(
            relevance=models.Case(
                models.When(start_date__gt=start_date, then=1),
                models.When(start_date__lt=start_date, then=2),
                output_field=models.IntegerField(),
            )
        ).order_by('relevance', 'start_date')
        previous_price_period = sorted_price_periods.filter(relevance=2).last()
        next_price_period = sorted_price_periods.filter(relevance=1).first()


        if next_price_period:
            end_date = next_price_period.start_date - datetime.timedelta(days=1)
        else:
            end_date = datetime.date.today()

        if previous_price_period:
            Transaction.objects.filter(
                transaction_type=transaction_type,
                date__gte=previous_price_period.start_date,
                date__lte=end_date,
            ).update(base_ip_related_price_per_reaction=previous_price_period.price_per_reaction)
        else:
            Transaction.objects.filter(
                transaction_type=transaction_type,
                date__lte=end_date,
            ).update(base_ip_related_price_per_reaction=0)

        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        start_date = self.start_date
        next_price_period = BasePrice.objects.filter(
            transaction_type=self.transaction_type, start_date__gt=start_date
        ).order_by('start_date').first()
        if next_price_period:
            end_date = next_price_period.start_date - datetime.timedelta(days=1)
        else:
            end_date = datetime.date.today()
        Transaction.objects.filter(
            transaction_type=self.transaction_type,
            date__gte=start_date,
            date__lte=end_date,
        ).update(base_ip_related_price_per_reaction=self.price_per_reaction)


def get_base_price_per_period(transaction_type):
    base_prices = []
    end_date = None
    for kp in BasePrice.objects.filter(transaction_type=transaction_type).order_by('-start_date'):
        start_date = kp.start_date
        price_per_reaction = kp.price_per_reaction
        if end_date:
            period_price = [start_date, end_date, price_per_reaction]
        else:
            period_price = [start_date, datetime.date.today(), price_per_reaction]
        base_prices.append(period_price)
        end_date = start_date - datetime.timedelta(days=1)
    return base_prices


def transaction_doc_path(instance, filename):
    return '{}/{}'.format(instance.doc_type, filename)


class TransactionDocument(models.Model):

    class Meta:
        abstract = True
        ordering = ['number']

    date = models.DateField()
    number = models.CharField(max_length=255)
    pdf = models.FileField(
        max_length=500,
        upload_to=transaction_doc_path,
    )

    def __str__(self):
        return os.path.basename(self.number)


class Quote(TransactionDocument):

    @property
    def doc_type(self):
        return 'quotes'


class Order(TransactionDocument):

    @property
    def doc_type(self):
        return 'orders'


class Invoice(TransactionDocument):

    @property
    def doc_type(self):
        return 'invoices'


class RoyaltiesManager(models.Manager):
    # Adapted from:
    # https://github.com/barmassimo/Expense-Tracker/blob/master/src/expenses/models.py

    def get_period_report(self, year, quarter=None, **kwargs):

        quarters = {
            'Q1': ['01-01', '03-31'],
            'Q2': ['04-01', '06-30'],
            'Q3': ['07-01', '09-30'],
            'Q4': ['10-01', '12-31'],
        }

        if quarter:
            period = quarters[quarter]
        else:
            period = ['01-01', '12-31']

        return self.get_royalties_report(
            from_date='{}-{}'.format(year, period[0]),
            to_date='{}-{}'.format(year, period[1]),
            **kwargs)

    def get_royalties_report(
        self, from_date=None, to_date=None, in_progress_only=False,
        customer_id=None, include_in_progress=False, outstanding=False,
        institution_type=None, transaction_type=None):

        type_kwargs = {}
        c_type_kwargs = {}
        c_kwargs = {}
        t_kwargs = {}

        if institution_type:
            type_kwargs['customer__institution__institution_type'] = institution_type
            c_type_kwargs['institution__institution_type'] = institution_type
        if transaction_type:
            type_kwargs['transaction_type'] = transaction_type
            c_type_kwargs['transaction__transaction_type'] = transaction_type

        if in_progress_only:
                t_kwargs['date_fulfilled'] = None
                c_kwargs['transaction__date_fulfilled'] = None
        elif outstanding:
            t_kwargs['date_fulfilled__isnull'] = False
            t_kwargs['date_paid__isnull'] = True
            c_kwargs['transaction__date_fulfilled__isnull'] = False
            c_kwargs['transaction__date_paid__isnull'] = True
        else:
            if from_date is not None:
                t_kwargs['date_fulfilled__gte'] = from_date
                c_kwargs['transaction__date_fulfilled__gte'] = from_date
            if to_date is not None:
                t_kwargs['date_fulfilled__lte'] = to_date
                c_kwargs['transaction__date_fulfilled__lte'] = to_date

        cid_c_kwargs = {}
        cid_t_kwargs = {}
        if customer_id:
            cid_t_kwargs['customer_id'] = customer_id
            cid_c_kwargs['id'] = customer_id

        transactions_by_date = Transaction.objects.filter(
            **t_kwargs, **cid_t_kwargs, **type_kwargs)

        if include_in_progress:
            in_progress = Transaction.objects.filter(
                date_fulfilled__isnull=True, **cid_t_kwargs, **type_kwargs)
            transactions_by_date = transactions_by_date | in_progress

        aggregate_data = transactions_by_date.annotate(
            ip_related_gross_price = ExpressionWrapper(
                F('number_of_reactions') * F('base_ip_related_price_per_reaction'),
                output_field=MoneyField(
                    decimal_places=2, default_currency='USD', max_digits=8)),
            ip_related_discount = ExpressionWrapper(
                F('number_of_reactions') * F('base_ip_related_price_per_reaction') - F('ip_related_price'),
                output_field=MoneyField(
                    decimal_places=2, default_currency='USD', max_digits=8)),
        ).aggregate(
            Sum('total_price'),
            Sum('number_of_reactions'),
            Sum('ip_related_price'),
            Count('pk'),
            Sum('ip_related_gross_price'),
            Sum('ip_related_discount'),
        )

        if (aggregate_data['pk__count'] == 0):
            return {'total': 0, 'total_per_month': 0}

        report = {}

        report['sum_total_price'] = aggregate_data['total_price__sum']
        report['sum_ip_related_price'] = aggregate_data['ip_related_price__sum']
        report['sum_number_of_reactions'] = aggregate_data['number_of_reactions__sum']
        report['average_total_price_per_reaction'] = aggregate_data['total_price__sum'] / aggregate_data['number_of_reactions__sum']
        report['sum_ip_related_price'] = aggregate_data['ip_related_price__sum']
        report['sum_ip_related_gross_price'] = aggregate_data['ip_related_gross_price__sum']
        report['sum_ip_related_discount'] = aggregate_data['ip_related_discount__sum']
        report['sum_ip_related_discount_pct'] = (
            aggregate_data['ip_related_discount__sum']
            / aggregate_data['ip_related_gross_price__sum'])
        report['sum_royalties_owed'] = float(aggregate_data['ip_related_price__sum']) * ROYALTY_PERCENTAGE

        customers_annotated = Customer.objects.annotate(
            c_tx_count=Count('transaction__date', distinct=True)
        )
        customers = customers_annotated.filter(
            c_tx_count__gt=0, **c_kwargs, **cid_c_kwargs, **c_type_kwargs)

        if include_in_progress:
            in_progress = Customer.objects.annotate(
                c_tx_count=Count('transaction__date', distinct=True)
            ).filter(
                transaction__date_fulfilled__isnull=True,
                c_tx_count__gt=0, **cid_c_kwargs)
            customers = customers | in_progress

        customers = customers.distinct()
        repeat_customers = customers.filter(c_tx_count__gt=1)

        report['customer_count'] = customers.count()
        report['repeat_customer_count'] = repeat_customers.count()
        try:
            repeat_customer_pct = repeat_customers.count() / customers.count()
        except ZeroDivisionError:
            repeat_customer_pct = 0
        report['repeat_customer_pct'] = repeat_customer_pct

        by_type = transactions_by_date.values('transaction_type').annotate(
            sum_total_price=Sum('total_price'),
            sum_ip_related_price=Sum('ip_related_price'),
            sum_ip_related_gross_price=ExpressionWrapper(
                Sum(F('number_of_reactions') * F('base_ip_related_price_per_reaction')),
                output_field=MoneyField(
                    decimal_places=2, default_currency='USD', max_digits=8)),
            sum_ip_related_discount = ExpressionWrapper(
                Sum(
                    F('number_of_reactions')
                    * F('base_ip_related_price_per_reaction')
                    - F('ip_related_price')),
                output_field=MoneyField(
                    decimal_places=2, default_currency='USD', max_digits=8)),
            sum_ip_related_discount_pct = ExpressionWrapper(
                float(1)
                * (Sum(
                    F('number_of_reactions')
                    * F('base_ip_related_price_per_reaction')
                    - F('ip_related_price')))
                / (Sum(
                    F('number_of_reactions')
                    * F('base_ip_related_price_per_reaction'))),
                output_field=models.FloatField()),
            sum_number_of_reactions=Sum('number_of_reactions'),
            average_total_price_per_reaction=ExpressionWrapper(
                1.0 * Sum('total_price') / Sum('number_of_reactions'),
                output_field=MoneyField(
                    decimal_places=2, default_currency='USD', max_digits=8)),
            sum_royalties_owed=ExpressionWrapper(
                Sum('ip_related_price') * ROYALTY_PERCENTAGE,output_field=MoneyField(
                    decimal_places=2, default_currency='USD', max_digits=8)),
        ).order_by('transaction_type')
        by_type = sorted(
            by_type, key=lambda x: int(-1 * x['sum_total_price']))

        for subreport in by_type:
            t_type = subreport['transaction_type']
            customers_by_type = customers.filter(
                transaction__transaction_type=t_type, **c_kwargs,
                **cid_c_kwargs)

            if include_in_progress:
                in_progress = Customer.objects.annotate(
                    c_tx_count=Count('transaction__date', distinct=True)
                ).filter(
                    transaction__transaction_type=t_type,
                    transaction__date_fulfilled__isnull=True, **cid_c_kwargs)
                customers_by_type = customers_by_type.distinct() | in_progress.distinct()

            repeat_customers_by_type = customers_by_type.filter(c_tx_count__gt=1)

            subreport['customer_count'] = customers_by_type.count()
            subreport['repeat_customer_count'] = repeat_customers_by_type.count()
            try:
                repeat_customer_pct = repeat_customers_by_type.count() / customers_by_type.count()
            except ZeroDivisionError:
                repeat_customer_pct = 0
            subreport['repeat_customer_pct'] = repeat_customer_pct

        report['by_type'] = by_type

        return report


class Transaction(models.Model):

    class Meta:
        ordering = ['-date', 'customer']

    transaction_type = models.CharField(
        choices=TRANSACTION_TYPE_CHOICES,
        max_length=7,
    )
    customer = models.ForeignKey(
        'Customer',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    vendor = models.ForeignKey(
        'Vendor',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    number_of_reactions = models.PositiveSmallIntegerField()
    total_price = MoneyField(
        decimal_places=2,
        default_currency='USD',
        max_digits=8,
    )
    ip_related_price = MoneyField(
        decimal_places=2,
        default_currency='USD',
        help_text='For kit sales, this will likely equal <strong>Total price</strong>.<br>'
            'For service contracts, enter the line item related to library synthesis.',
        max_digits=8,
        verbose_name='IP-related price'
    )
    base_ip_related_price_per_reaction = MoneyField(
        blank=True,
        decimal_places=2,
        default_currency='USD',
        max_digits=5,
        verbose_name='Base IP-related price per reaction',
    )
    date = models.DateField()
    date_samples_arrived = models.DateField(
        blank=True,
        help_text='If this is a service transaction, what date did the samples arrive?',
        null=True,
    )
    date_fulfilled = models.DateField(
        blank=True,
        null=True,
    )
    date_paid = models.DateField(
        blank=True,
        null=True,
    )
    quote = models.ForeignKey(
        'Quote',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='transactions',
    )
    order = models.ForeignKey(
        'Order',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='transactions',
    )
    invoice = models.ForeignKey(
        'Invoice',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='transactions',
    )

    description = models.TextField(
        blank=True,
    )
    notes = models.TextField(
        blank=True,
    )

    objects = RoyaltiesManager()

    def __str__(self):
        return '{} - {} - {} - {}'.format(
            self.date, self.customer, self.transaction_type,
            self.number_of_reactions)

    def save(self, *args, **kwargs):
        for base_price_data in get_base_price_per_period(self.transaction_type):
            start_date = base_price_data[0]
            end_date = base_price_data[1]
            price = base_price_data[2]
            if start_date <= self.date <= end_date:
                self.base_ip_related_price_per_reaction = price
                break
        super().save(*args, **kwargs)

    @property
    def ip_related_discount(self):
        if self.base_ip_related_price_per_reaction == 0:
            return '-'
        else:
            return (self.base_ip_related_price_per_reaction
                * self.number_of_reactions
                - self.ip_related_price)

    @property
    def ip_related_discount_pct(self):
        if self.base_ip_related_price_per_reaction == 0:
            return '-'
        elif self.number_of_reactions == 0:
            return '-'
        else:
            return (self.ip_related_discount
                / (self.ip_related_price + self.ip_related_discount))

    @property
    def ip_related_gross_price(self):
        if self.base_ip_related_price_per_reaction == 0:
            return '-'
        elif self.number_of_reactions == 0:
            return '-'
        else:
            return (self.base_ip_related_price_per_reaction
                * self.number_of_reactions)

    @property
    def is_outstanding(self):
        if self.date_fulfilled is not None and self.date_paid is None:
            return True
        else:
            return False

    @property
    def is_prepaid(self):
        if self.date_fulfilled is None and self.date_paid is not None:
            return True
        else:
            return False

    @property
    def royalties_owed(self):
        return self.ip_related_price * ROYALTY_PERCENTAGE

    @property
    def price_per_sample(self):
        if self.number_of_reactions == 0:
            return "-"
        else:
            return self.total_price / self.number_of_reactions
