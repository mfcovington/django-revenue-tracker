from django.contrib import admin
from django.http import HttpResponseRedirect

from ..models import BasePrice, Invoice, Order, Quote, Transaction
from ..models import Customer


class SamplesArrivedForServiceStatusFilter(admin.SimpleListFilter):
    """
    Filter service Transaction records by whether it the samples have arrived.
    """
    title = 'service sample status'
    parameter_name = 'service_sample_status'

    def lookups(self, request, model_admin):
        return (
            ('arrived', 'Arrived'),
            ('not_arrived', 'Not Arrived'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not_arrived':
            return queryset.filter(
                transaction_type='service', date_samples_arrived=None)
        elif self.value() == 'arrived':
            return queryset.filter(
                transaction_type='service').exclude(date_samples_arrived=None)


class FulfillmentStatusFilter(admin.SimpleListFilter):
    """
    Filter Transaction records by whether it has been fulfilled.
    """
    title = 'fulfillment status'
    parameter_name = 'fulfillment_status'

    def lookups(self, request, model_admin):
        return (
            ('fulfilled', 'Fulfilled'),
            ('not_fulfilled', 'Not Fulfilled'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not_fulfilled':
            return queryset.filter(date_fulfilled=None)
        elif self.value() == 'fulfilled':
            return queryset.exclude(date_fulfilled=None)


class PaymentStatusFilter(admin.SimpleListFilter):
    """
    Filter Transaction records by whether it has been paid.
    """
    title = 'payment status'
    parameter_name = 'payment_status'

    def lookups(self, request, model_admin):
        return (
            ('paid', 'Paid'),
            ('not_paid', 'Not Paid'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not_paid':
            return queryset.filter(date_paid=None)
        elif self.value() == 'paid':
            return queryset.exclude(date_paid=None)


class TransactionInline(admin.StackedInline):
    model = Transaction


class TransactionDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'number',
        'date',
        'pdf',
    ]
    inlines = [TransactionInline]
    save_on_top = True


@admin.register(BasePrice)
class BasePriceAdmin(admin.ModelAdmin):
    save_on_top = True


@admin.register(Quote)
class QuoteAdmin(TransactionDocumentAdmin):
    pass


@admin.register(Order)
class OrderAdmin(TransactionDocumentAdmin):
    pass


@admin.register(Invoice)
class InvoiceAdmin(TransactionDocumentAdmin):
    pass


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'customer',
        'vendor',
        'transaction_type',
        'number_of_reactions',
        'project',
        'date_samples_arrived',
        'date_fulfilled',
        'date_paid',
        'total_price',
        'price_per_sample',
        'base_ip_related_price_per_reaction',
        'ip_related_price',
        'royalties_owed',
    ]
    list_filter = [
        'transaction_type',
        SamplesArrivedForServiceStatusFilter,
        FulfillmentStatusFilter,
        PaymentStatusFilter,
    ]
    readonly_fields = ['base_ip_related_price_per_reaction']
    save_on_top = True
    search_fields = [
        'customer__name',
        'customer__institution__name',
        'customer__contact__name',
        'description',
        'notes',
        'vendor__name',
        'vendor__contact__name',
    ]

    def get_changeform_initial_data(self, request):
        customer_pk = request.GET.get('customer_pk')
        try:
            customer = Customer.objects.get(pk=customer_pk)
        except:
            customer = None
        return {
            'customer': customer,
        }

    def response_add(self, request, obj, post_url_continue=None):
        result = super().response_add(request, obj, post_url_continue)
        if '_continue' not in request.POST and 'next' in request.GET:
            return HttpResponseRedirect(request.GET['next'])
        else:
            return result

    def response_change(self, request, obj):
        result = super().response_change(request, obj)
        if '_continue' not in request.POST and 'next' in request.GET:
            return HttpResponseRedirect(request.GET['next'])
        else:
            return result
