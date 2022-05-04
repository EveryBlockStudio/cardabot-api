from django.db import models


class Chat(models.Model):
    ebs_poolid = "pool1ndtsklata6rphamr6jw2p3ltnzayq3pezhg0djvn7n5js8rqlzh"  # bech32
    clients = (("TELEGRAM", "Telegram"), ("", "None"))

    chat_id = models.CharField(
        max_length=256,
    )

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

    class Meta:
        unique_together = ("chat_id", "client")
