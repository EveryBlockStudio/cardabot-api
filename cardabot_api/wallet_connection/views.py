from django.shortcuts import render

def wallet_connection(request):
    return render(request, 'connect.html')

def wallet_connection_success(request):
    return render(request, 'connection-success.html')