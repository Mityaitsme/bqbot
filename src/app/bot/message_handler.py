from aiogram.types import Message as TgMessage
from ..core import Message


class MessageHandler:
  """
  Converts raw Telegram updates into core Message objects.
  """

  @staticmethod
  def from_tg(msg: TgMessage) -> Message:
    return Message(
      user_id=msg.from_user.id,
      text=msg.text or "",
    )
