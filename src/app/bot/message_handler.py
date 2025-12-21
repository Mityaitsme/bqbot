from aiogram.types import Message as TgMessage
from aiogram import Bot
from ..core import Message


class MessageHandler:
  """
  Converts raw Telegram updates into core Message objects.
  """

  @staticmethod
  def from_tg(msg: TgMessage) -> Message:
    """
    Converts raw Telegram updates into core Message objects.
    """
    return Message(
      _user_id=msg.from_user.id,
      _text=msg.text or "",
      _bot = msg.bot
    )
