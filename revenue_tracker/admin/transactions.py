from django.contrib import admin

from ..models import Invoice, Order, Quote, Transaction


class TransactionInline(admin.StackedInline):
    model = Transaction


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    save_on_top = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    save_on_top = True


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    save_on_top = True


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'customer',
        'vendor',
        'transaction_type',
        'number_of_reactions',
        'date_fulfilled',
        'date_paid',
        'total_price',
        'price_per_sample',
        'ip_related_price',
        'royalties_owed',
    ]
    list_filter = ['transaction_type']
    save_on_top = True
    search_fields = [
        'customer__name',
        'customer__institution__name',
        'customer__contact__name',
        'vendor__name',
        'vendor__contact__name',
    ]
