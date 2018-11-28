from django.conf.urls import url

from . import views


app_name = 'revenue_tracker'

urlpatterns = [
    url(r'^customer/$', views.CustomerList.as_view(), name='customer_list'),
    url(r'^customer/(?P<pk>\d+)/$', views.CustomerDetail.as_view(), name='customer_detail'),
    url(r'^outstanding/$', views.OutstandingInvoicesList.as_view(), name='outstanding_invoices_list'),
    url(r'^$', views.TransactionList.as_view(), name='transaction_list'),
    url(r'^(?P<pk>\d+)/$', views.TransactionDetail.as_view(), name='transaction_detail'),
]
