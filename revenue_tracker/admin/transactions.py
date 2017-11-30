from django.contrib import admin

from ..models import Quote, Invoice, Transaction


class TransactionInline(admin.StackedInline):
    model = Transaction


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    pass


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    pass


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'customer',
        'transaction_type',
        'number_of_reactions',
        'date_fulfilled',
    ]
    list_filter = ['transaction_type']
    search_fields = [
        'customer__name',
        'customer__institution__name',
        'customer__contact__name',
    ]
