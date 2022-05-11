from rest_framework import serializers
from .models import Chat, CardaBotUser
from .utils import check_pool_is_valid


class ChatSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        if not check_pool_is_valid(attrs["default_pool_id"]):
            raise serializers.ValidationError(
                "Field `default_pool_id` is not a valid pool id."
            )
        return attrs

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
