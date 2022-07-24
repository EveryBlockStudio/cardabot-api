from django.urls import path
from . import views


urlpatterns = [
    path("", views.wallet_connection, name="wallet_connection"),
    path("success/", views.wallet_connection_success, name="wallet_connection_success"),
    
]
