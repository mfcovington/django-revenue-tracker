from django.shortcuts import render
from django.views.generic import ListView

from .models import Transaction


class TransactionList(ListView):
    context_object_name = 'transaction_list'
    model = Transaction
