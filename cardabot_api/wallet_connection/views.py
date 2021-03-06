from django.shortcuts import render
from cardabot_api.cardabot.models import Chat
from django.shortcuts import get_object_or_404

def wallet_connection(request):
    """ Wallet connection page """
    if request.method == 'GET':
        # get token from request
        tmp_token = request.GET.get('token')
        
        # filter chat_id by tmp_token or return 404
        chat_id = get_object_or_404(Chat, tmp_token=tmp_token)

    return render(request, 'connect.html')

def wallet_connection_success(request):
    return render(request, 'connection-success.html')

def home(request):
    return render(request, 'home.html')