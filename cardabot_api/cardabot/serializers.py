from rest_framework import serializers
from .models import Chat, CardaBotUser


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = (
            "id",
            "client",
            "chat_id",
            "default_language",
            "default_pool_id",
            "cardabot_user_id",
        )


class CardaBotUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardaBotUser
        fields = ("id", "stake_key")
