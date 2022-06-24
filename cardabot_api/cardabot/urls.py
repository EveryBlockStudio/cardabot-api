from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

graphql_urls = [
    path("epoch/", views.Epoch.as_view()),
    path("pool/<str:pool_id>/", views.StakePool.as_view()),
    path("netparams/", views.NetParams.as_view()),
    path("pots/", views.Pots.as_view()),
    path("netstats/", views.Netstats.as_view()),
]

urlpatterns = [
    path("chats/", views.ChatList.as_view()),
    path("chats/<str:chat_id>/", views.ChatDetail.as_view()),
    path("users/", views.CardaBotUserList.as_view()),
    path("users/<int:pk>/", views.CardaBotUserDetail.as_view()),
    path("chats/<str:chat_id>/token/", views.TemporaryChatToken.as_view()),
    path("connect/", views.CreateAndConnectUser.as_view()),
    path("unsignedtx/", views.UnsignedTransaction.as_view()),
    path("unsignedtx/<str:pk>/", views.UnsignedTransaction.as_view()),
    *graphql_urls,
]

urlpatterns = format_suffix_patterns(urlpatterns)
