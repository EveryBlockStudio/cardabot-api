from django.shortcuts import render
from cardabot_api.cardabot.models import Chat, FaqCategory, FaqQuestion
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
    """ Wallet connection success page """
    if request.method == 'GET':
        # get stake address from request
        stake_address = request.GET.get('stake')

    return render(request, 'connection-success.html' , {'stake_address': stake_address})

def home(request):
    """ Home page """
    return render(request, 'home.html')

def faq(request):
    """ FAQ page """
    # get all faq categories
    categories = FaqCategory.objects.all().values()
    faqs = FaqQuestion.objects.all().values()
    
    #pbj = {"tx_id": tx_id}
    context = {
        "categories": categories,
        "faqs": faqs,
    }
    return render(request, 'faq.html', context)

def terms(request):
    """ Terms page """
    return render(request, 'terms.html')

def privacy(request):
    """ Privacy page """
    return render(request, 'privacy.html')