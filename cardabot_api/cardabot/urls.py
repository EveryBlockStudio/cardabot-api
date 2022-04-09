from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = [
    path("chats/", views.ChatList.as_view()),
    path("chats/<str:chat_id>/", views.ChatDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
