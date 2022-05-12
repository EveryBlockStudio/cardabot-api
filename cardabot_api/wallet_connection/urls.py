from django.urls import path
from . import views


urlpatterns = [
    path("", views.wallet_connection, name="wallet_connection"),
    
]
