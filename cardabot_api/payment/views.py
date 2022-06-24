from django.shortcuts import get_object_or_404, render

from ..cardabot.models import UnsignedTransaction


def payment(request):
    tx_id = request.GET.get("tx_id")
    obj = get_object_or_404(UnsignedTransaction, pk=tx_id)
    context = {
        "amount": round(float(obj.amount), 6),
        "receiver_chat_id": obj.receiver_chat.chat_id,
        "tx_cbor": obj.tx_cbor,
        "tx_id": obj.tx_id,
        "username_receiver": obj.username_receiver,
    }
    return render(request, "payment.html", context)
