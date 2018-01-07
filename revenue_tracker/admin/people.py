from django.contrib import admin

from ..models import Contact, Country, Customer, Institution, Vendor
from .transactions import TransactionInline


class CustomerInline(admin.TabularInline):
    model = Customer


class VendorInline(admin.TabularInline):
    model = Vendor


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'title',
        'email',
        'phone',
        'fax',
        'website',
    ]
    save_on_top = True


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    inlines = [VendorInline]
    save_on_top = True
    search_fields = ['name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    inlines = [TransactionInline]
    list_display = [
        'customer',
        'contact_name',
        'institution_type',
        'website',
    ]
    list_filter = [
        'institution__institution_type',
        'institution__country'
    ]
    save_on_top = True
    search_fields = [
        'institution__name',
        'name',
        'contact__name',
        'vendor__name',
        'website',
    ]


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    inlines = [CustomerInline]
    list_display = [
        'name',
        'institution_type',
        'country',
        'website',
    ]
    list_filter = [
        'institution_type',
        'country',
    ]
    save_on_top = True
    search_fields = [
        'name',
        'website',
    ]


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
