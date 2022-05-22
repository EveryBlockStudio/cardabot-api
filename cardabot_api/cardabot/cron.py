from cardabot_api.cardabot.models import Chat


def reset_cardabot_tmp_token():
    """Reset all chats' temporary tokens."""
    Chat.objects.filter(tmp_token__isnull=False).update(tmp_token=None)
