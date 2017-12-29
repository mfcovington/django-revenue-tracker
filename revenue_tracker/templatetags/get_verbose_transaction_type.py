from django import template

from ..models.transactions import TRANSACTION_TYPE_CHOICES


register = template.Library()

@register.filter('get_verbose_transaction_type')
def get_verbose_transaction_type(transaction_type):
    """Lookup verbose version of transaction type"""
    return dict(TRANSACTION_TYPE_CHOICES)[transaction_type]
