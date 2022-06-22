from django.shortcuts import render, get_object_or_404
from ..cardabot.models import UnsignedTransaction

def payment(request, tx_id):
    #return render(request, 'payment.html')
    #tx_id = request.GET.get("tx_id", "")
    obj = get_object_or_404(Transaction, pk=tx_id)
    context = {obj.__dict__.keys(): obj.__dict__.values()}
    return render(request, 'payment.html', context)