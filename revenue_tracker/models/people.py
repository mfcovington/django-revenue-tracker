from django.db import models

from customer_tracker.models import Customer as CustomerBase


class Customer(CustomerBase):

    class Meta:
        proxy = True

    @property
    def is_repeat_customer(self):
        if self.tx_count > 1:
            return True
        else:
            return False

    @property
    def reaction_count(self):
        return sum(
            sum(self.transaction_set.values_list('number_of_reactions'), ()))

    @property
    def total_revenue(self):
        return sum(
            sum(self.transaction_set.values_list('total_price'), ()))

    @property
    def tx_count(self):
        return len(set(self.transaction_set.values_list('date')))


class Vendor(models.Model):

    class Meta:
        ordering = ['name']

    name = models.CharField(
        max_length=255,
        unique=True,
    )
    contact = models.ForeignKey(
        'customer_tracker.Contact',
        on_delete=models.PROTECT,
    )
    country = models.ForeignKey(
        'customer_tracker.Country',
        on_delete=models.PROTECT,
    )
    customers = models.ManyToManyField(
        'Customer',
        through='Transaction',
    )
    website = models.URLField(
        blank=True,
    )

    def __str__(self):
        return self.name

    @property
    def contact_name(self):
        return self.contact.name
