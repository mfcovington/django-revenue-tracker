from django.db import models

from phonenumber_field.modelfields import PhoneNumberField


INSTITUTION_TYPE_CHOICES = [
    ('Academic', 'Academic'),
    ('Government', 'Government'),
    ('Industry', 'Industry'),
]


class Contact(models.Model):

    class Meta:
        ordering = ['name']

    name = models.CharField(
        max_length=255,
    )
    title = models.CharField(
        blank=True,
        max_length=255,
    )
    email = models.EmailField(
        blank=True,
        null=True,
    )
    phone = PhoneNumberField(blank=True)
    fax = PhoneNumberField(blank=True)
    website = models.URLField(
        blank=True,
    )

    def __str__(self):
        return self.name


class Country(models.Model):

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Countries'

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    def __str__(self):
        return self.name


class Customer(models.Model):

    class Meta:
        ordering = ['institution', 'name']

    institution = models.ForeignKey('Institution')
    name = models.CharField(
        blank=True,
        max_length=255,
    )
    contact = models.ForeignKey(
        'Contact',
        blank=True,
        null=True,
    )
    website = models.URLField(
        blank=True,
    )

    def __str__(self):
        return self.customer

    @property
    def contact_name(self):
        return self.contact.name

    @property
    def customer(self):
        if self.name == '':
            return self.institution.name
        else:
            return '{} – {}'.format(self.institution.name, self.name)

    @property
    def institution_type(self):
        return self.institution.institution_type

    @property
    def is_repeat_customer(self):
        if self.tx_count > 1:
            return True
        else:
            return False

    @property
    def tx_count(self):
        return len(set(self.transaction_set.values_list('date')))


class Institution(models.Model):

    class Meta:
        ordering = ['name']

    name = models.CharField(
        max_length=255,
        unique=True,
    )
    country = models.ForeignKey('Country')
    institution_type = models.CharField(
        choices=INSTITUTION_TYPE_CHOICES,
        max_length=15,
    )
    website = models.URLField(
        blank=True,
    )

    def __str__(self):
        return self.name


class Vendor(models.Model):

    class Meta:
        ordering = ['name']

    name = models.CharField(
        max_length=255,
        unique=True,
    )
    contact = models.ForeignKey('Contact')
    country = models.ForeignKey('Country')
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
