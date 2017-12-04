from django.conf.urls import url

from .views import TransactionList

urlpatterns = [
    url(r'^$', TransactionList.as_view(), name='transaction_list'),
]
