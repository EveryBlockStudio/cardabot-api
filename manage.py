#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from cardabot_api.cardabot import cron
from cardabot_api.cardabot.utils import Scheduler


def main():
    """Run administrative tasks."""
    load_dotenv()

    Scheduler.queue.add_job(
        cron.reset_cardabot_tmp_token,
        "interval",
        seconds=60 * 15,
        start_date=datetime.now(),
        # args=[updater.bot],
        id="reset_tmp_token",
    )

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cardabot_api.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
