from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import graphql_views, views

graphql_urls = [
    path("epoch/", graphql_views.Epoch.as_view()),
    path("pool/<str:pool_id>/", graphql_views.StakePool.as_view()),
    path("netparams/", graphql_views.NetParams.as_view()),
    path("pots/", graphql_views.Pots.as_view()),
    path("netstats/", graphql_views.Netstats.as_view()),
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
    path("tx/", views.Transaction.as_view()),
    path("checktx/<tx_id>/", views.CheckTransaction.as_view()),
    path("claim/", views.ClaimUserFunds.as_view()),
    *graphql_urls,
]

urlpatterns = format_suffix_patterns(urlpatterns)
