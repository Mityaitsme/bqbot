import logging
from aiogram import Bot

from ..core import Message

logger = logging.getLogger(__name__)


async def send_message(bot: Bot, message: Message) -> None:
  """
  Sends core.Message via Telegram bot.
  """
  if message.user_id is None:
    logger.error("Cannot send message without user_id")
    return

  await bot.send_message(
    chat_id=message.user_id,
    text=message.text,
  )

  logger.info(f"[SEND] → {message.user_id}: {message.text}")
