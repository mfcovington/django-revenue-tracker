from django.shortcuts import render
from django.views.generic import ListView

from .models import Transaction


class TransactionList(ListView):
    context_object_name = 'transaction_list'
    model = Transaction

    def get_context_data(self, **kwargs):
        context = super(TransactionList, self).get_context_data(**kwargs)
        context['report'] = Transaction.objects.get_royalties_report()
        return context
