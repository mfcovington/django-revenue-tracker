import os

from django.db import models
from django.db.models import Count, F, ExpressionWrapper, Sum

from djmoney.models.fields import MoneyField


ROYALTY_PERCENTAGE = 0.025 # import from settings (for first 1 million. After that, 2.75%)


TRANSACTION_TYPE_CHOICES = [
    ('kit', 'Kit Sale'),
    ('service', 'Service Contract'),
    ('other', 'Other')
]


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

    def get_royalties_report(self):

        aggregate_data = Transaction.objects.aggregate(
            Sum('total_price'), Sum('number_of_reactions'),
            Sum('ip_related_price'), Count('pk'))

        if (aggregate_data['pk__count'] == 0):
            return {'total': 0, 'total_per_month': 0}

        report = {}

        report['sum_total_price'] = aggregate_data['total_price__sum']
        report['sum_ip_related_price'] = aggregate_data['ip_related_price__sum']
        report['sum_number_of_reactions'] = aggregate_data['number_of_reactions__sum']
        report['average_total_price_per_reaction'] = aggregate_data['total_price__sum'] / aggregate_data['number_of_reactions__sum']
        report['sum_ip_related_price'] = aggregate_data['ip_related_price__sum']
        report['sum_royalties_owed'] = float(aggregate_data['ip_related_price__sum']) * ROYALTY_PERCENTAGE

        by_type = Transaction.objects.values('transaction_type').annotate(
            sum_total_price=Sum('total_price'),
            sum_ip_related_price=Sum('ip_related_price'),
            sum_number_of_reactions=Sum('number_of_reactions'),
            average_total_price_per_reaction=ExpressionWrapper(
                Sum('total_price') / Sum('number_of_reactions'),
                output_field=MoneyField(
                    decimal_places=2, default_currency='USD', max_digits=8)),
            sum_royalties_owed=ExpressionWrapper(
                Sum('ip_related_price') * ROYALTY_PERCENTAGE,output_field=MoneyField(
                    decimal_places=2, default_currency='USD', max_digits=8)),
        ).order_by('transaction_type')
        by_type = sorted(
            by_type, key=lambda x: int(-1 * x['sum_total_price']))

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
    )
    vendor = models.ForeignKey(
        'Vendor',
        blank=True,
        null=True,
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
    date = models.DateField()
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
        related_name='transaction'
    )
    order = models.ForeignKey(
        'Order',
        blank=True,
        null=True,
        related_name='transaction'
    )
    invoice = models.ForeignKey(
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
