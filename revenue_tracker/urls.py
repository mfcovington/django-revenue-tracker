from django.conf.urls import url

from .views import TransactionDetail, TransactionList

urlpatterns = [
    url(r'^$', TransactionList.as_view(), name='transaction_list'),
    url(r'^(?P<pk>\d+)/$', TransactionDetail.as_view(), name='transaction_detail'),
]
