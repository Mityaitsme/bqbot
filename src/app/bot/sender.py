import logging
from typing import List, Optional
from aiogram import Bot

from ..core import Message

logger = logging.getLogger(__name__)


async def send_messages(messages : Message | List[Message], bot: Optional[Bot]) -> None:
  """
  Sends core.Message via Telegram bot.
  """
  if type(messages) == Message:
    messages = [messages]
  
  for message in messages:
    if message.recipient_id is None:
      logger.error("Cannot send message without recipient_id")
      return
    
    # TODO: work out what to do using TGMember
    if message.bot is not None:
      await message.bot.send_message(
        chat_id=message.recipient_id,
        text=message.text,
      )
    else:
      await bot.send_message(
        chat_id=message.recipient_id,
        text=message.text,
      )

    logger.info(f"[SEND] → {message.recipient_id}: {message.text}")
