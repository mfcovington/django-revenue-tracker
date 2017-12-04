import os

from django.db import models
from django.db.models import Count, Min, Max, Sum

from djmoney.models.fields import MoneyField


ROYALTY_PERCENTAGE = 0.025 # import from settings (for first 1 million. After that, 2.75%)


TRANSACTION_TYPE_CHOICES = [
    ('kit', 'Kit Sale'),
    ('service', 'Service Contract'),
    ('other', 'Other')
]


def quote_or_invoice_path(instance, filename):
    return '{}/{}'.format(instance.doc_type, filename)


class QuoteOrInvoice(models.Model):

    class Meta:
        abstract = True

    date = models.DateField()
    number = models.CharField(max_length=255)
    pdf = models.FileField(
        max_length=500,
        upload_to=quote_or_invoice_path,
    )

    def __str__(self):
        return os.path.basename(self.number)


class Quote(QuoteOrInvoice):

    @property
    def doc_type(self):
        return 'quotes'


class Invoice(QuoteOrInvoice):
    date_paid = models.DateField(
        blank=True,
        null=True,
    )

    @property
    def doc_type(self):
        return 'invoices'


class RoyaltiesManager(models.Manager):
    # Adapted from:
    # https://github.com/barmassimo/Expense-Tracker/blob/master/src/expenses/models.py

    def get_royalties_report(self):

        aggregate_data = Transaction.objects.aggregate(
            Sum('ip_related_price'), Min('date'), Max('date'), Count('pk'))

        if (aggregate_data['pk__count'] == 0):
            return {'total': 0, 'total_per_month': 0}

        report = {}

        report['from_date'] = aggregate_data['date__min']
        report['to_date'] = aggregate_data['date__max']
        report['days'] = (report['to_date'] - report['from_date']).days + 1
        report['months'] = float(report['days']) / float(30)
        report['total'] = aggregate_data['ip_related_price__sum']
        report['total_per_month'] = float(report['total']) / report['months']

        by_type = Transaction.objects.values('transaction_type').annotate(
            total=Sum('ip_related_price')).order_by('transaction_type')
        by_type = sorted(
            by_type, key=lambda x: int(-1 * x['total']))

        report['by_type'] = by_type

        return report


class Transaction(models.Model):

    class Meta:
        ordering = ['-date', 'customer']

    transaction_type = models.CharField(
        choices=TRANSACTION_TYPE_CHOICES,
        max_length=7,
    )
    customer = models.ForeignKey('Customer')
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
    date = models.DateField()
    date_fulfilled = models.DateField(
        blank=True,
        null=True,
    )
    quote = models.OneToOneField(
        'Quote',
        blank=True,
        null=True,
        related_name='transaction'
    )
    invoice = models.OneToOneField(
        'Invoice',
        blank=True,
        null=True,
        related_name='transaction'
    )

    objects = RoyaltiesManager()

    def __str__(self):
        return '{} - {} - {} - {}'.format(
            self.date, self.customer, self.transaction_type,
            self.number_of_reactions)

    @property
    def royalties_owed(self):
        return self.ip_related_price * ROYALTY_PERCENTAGE

    @property
    def price_per_sample(self):
        return self.total_price / self.number_of_reactions
