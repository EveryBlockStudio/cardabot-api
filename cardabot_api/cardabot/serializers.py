from rest_framework import serializers

from .models import CardaBotUser, Chat
from .utils import check_pool_is_valid, check_stake_addr_is_valid


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
            "tmp_token",
        )


class CardaBotUserSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        if not check_stake_addr_is_valid(attrs["stake_key"]):
            raise serializers.ValidationError(
                "Field `stake_key` is not a valid stake address."
            )
        return attrs

    class Meta:
        model = CardaBotUser
        fields = ("id", "stake_key")


class TemporyTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ("tmp_token",)
