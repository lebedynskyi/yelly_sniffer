import asyncio
import logging

from telegram.ext import ApplicationBuilder

logger = logging.getLogger(__name__)


class TelegramApi:
    def __init__(self, config):
        self.config = config
        self.tele_bot = ApplicationBuilder().token(config["tele_token"]).build()
        self.channel_id = config["tele_channel"]

    def send_success(self, title, url):
        logger.info("Telegram sending success")

        try:
            msg_text = "Facebook success:\n%s\n%s" % (title, url)
            asyncio.run(self.tele_bot.bot.send_message(chat_id=self.channel_id, text=msg_text))
        except BaseException as e:
            logger.exception("Telegram Unable to send Telegram notification", e)

    def send_error(self, error):
        logger.info("Telegram sending error")

        try:
            msg_text = "Facebook Error:\n%s" % error
            asyncio.run(self.tele_bot.bot.send_message(chat_id=self.channel_id, text=msg_text))
        except BaseException as e:
            logger.exception("Telegram Unable to send Telegram notification", e)
