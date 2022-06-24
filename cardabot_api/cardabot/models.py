from django.db import models
from django.dispatch import receiver


class CardaBotUser(models.Model):
    # https://cips.cardano.org/cips/cip19/#userfacingencoding
    stake_key = models.CharField(max_length=256, unique=True)

    def __str__(self) -> str:
        return self.stake_key


class Chat(models.Model):
    ebs_poolid = "pool1ndtsklata6rphamr6jw2p3ltnzayq3pezhg0djvn7n5js8rqlzh"  # bech32
    clients = (("TELEGRAM", "Telegram"), ("", "None"))

    cardabot_user = models.ForeignKey(
        CardaBotUser, on_delete=models.SET_NULL, null=True
    )

    tmp_token = models.CharField(
        max_length=56, unique=True, null=True
    )  # temporary connection token

    # telegram: `chat_id` is the same as `user_id` for private chats
    chat_id = models.CharField(max_length=256)

    client = models.CharField(
        max_length=16,
        choices=clients,
        default="",
        null=False,
        blank=True,
    )

    default_language = models.CharField(
        max_length=2,
        default="",
        blank=True,
        null=False,
    )

    default_pool_id = models.CharField(
        max_length=56,
        default=ebs_poolid,
        blank=False,
        null=False,
    )

    def __str__(self) -> str:
        return self.chat_id

    class Meta:
        unique_together = ("chat_id", "client")


class UnsignedTransaction(models.Model):
    """
    Model of the unsigned transaction
    """

    tx_id = models.CharField(max_length=64, unique=True, primary_key=True)
    tx_cbor = models.CharField(max_length=4096)  # cbor, can we optimize field type?
    sender_chat = models.ForeignKey(
        Chat, on_delete=models.CASCADE, related_name="sender_chat"
    )
    receiver_chat = models.ForeignKey(
        Chat, on_delete=models.CASCADE, related_name="receiver_chat"
    )
    amount = models.DecimalField(max_digits=17, decimal_places=6)  # up to 45 bi ADA
    username_receiver = models.CharField(max_length=32)

    def __str__(self) -> str:
        return self.tx_id
