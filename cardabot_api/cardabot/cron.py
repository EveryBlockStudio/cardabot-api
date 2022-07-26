from cardabot_api.cardabot.models import Chat
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from cardabot_api.cardabot.utils import Scheduler

def _reset_fn():
    return Chat.objects.filter(tmp_token__isnull=False).update(tmp_token=None)

def reset_cardabot_tmp_token_cron():
    """Reset all chats' temporary tokens."""

    Scheduler.queue.add_job(
        _reset_fn,
        "interval",
        seconds=60*15, # 15 minutes
        start_date=datetime.now(),
        # args=[updater.bot],
        id="reset_tmp_token",
    )
    