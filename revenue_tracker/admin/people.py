from django.contrib import admin

from customer_tracker.admin import CustomerAdmin, CountryAdmin
from customer_tracker.models import Country

from ..models import Customer, Vendor
from .transactions import TransactionInline


class VendorInline(admin.TabularInline):
    model = Vendor


@admin.register(Customer)
class CustomerAdmin(CustomerAdmin):
    inlines = [TransactionInline]
    search_fields = [
        'institution__name',
        'name',
        'contact__name',
        'vendor__name',
        'website',
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(transactions__isnull=False).distinct()


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    inlines = [TransactionInline]
    list_display = [
        'name',
        'contact_name',
        'country',
        'website',
    ]
    save_on_top = True
    search_fields = [
        'name',
        'contact__name',
        'country__name',
        'website',
    ]


class CountryAdmin(CountryAdmin):
    inlines = [VendorInline]

admin.site.unregister(Country)
admin.site.register(Country, CountryAdmin)
