from django.apps import AppConfig

class CardabotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cardabot_api.cardabot"

    def ready(self):
        """ Loads the scheduler. """
        from datetime import datetime
        from cardabot_api.cardabot import cron

        cron.reset_cardabot_tmp_token_cron()
