from __future__ import annotations
import logging
from ..core import Message
from typing import Optional

logger = logging.getLogger(__name__)

class MsgSender:
  """
  Sends messages via Telegram API.
  """

  @staticmethod
  def send(message: Message, id: Optional[int] = None) -> None:
    """
    Function that manages its class's job.
    """
    if not message.recipient_id and not id:
      logger.exception("Error while sending message: cannot send a message without recipient's ID")
      raise SendMessageException("Cannot send a message without recipient's ID")
    if not message.recipient_id:
      message.recipient_id = id
    # TODO: add the actual sending here
    logger.info(f"[SEND] → {message.recipient_id}: {message.text}")