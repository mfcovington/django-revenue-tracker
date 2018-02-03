from django.conf.urls import url

from .views import CustomerDetail, CustomerList, TransactionDetail, TransactionList

urlpatterns = [
    url(r'^customer/$', CustomerList.as_view(), name='customer_list'),
    url(r'^customer/(?P<pk>\d+)/$', CustomerDetail.as_view(), name='customer_detail'),
    url(r'^$', TransactionList.as_view(), name='transaction_list'),
    url(r'^(?P<pk>\d+)/$', TransactionDetail.as_view(), name='transaction_detail'),
]
