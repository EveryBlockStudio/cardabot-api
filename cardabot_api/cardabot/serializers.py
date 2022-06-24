from rest_framework import serializers

from .models import CardaBotUser, Chat, UnsignedTransaction
from .utils import check_pool_is_valid, check_stake_addr_is_valid


class ChatSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        pool = attrs.get("default_pool_id")
        if pool and not check_pool_is_valid(pool):
            raise serializers.ValidationError(
                f"Field `default_pool_id`={pool} is not a valid pool id."
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
        stake_addr = attrs.get("stake_key")
        if stake_addr and not check_stake_addr_is_valid(stake_addr):
            raise serializers.ValidationError(
                f"Field `stake_key`={stake_addr} is not a valid stake address."
            )
        return attrs

    class Meta:
        model = CardaBotUser
        fields = ("id", "stake_key")


class TemporaryTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ("tmp_token",)


class UnsignedTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnsignedTransaction
        fields = ("tx_id",)
