from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING
import logging
from datetime import datetime, timezone, timedelta
from typing import Callable, Any
import hashlib

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
  from ..core import Message

class Utils:
  """
  This class provides several unconnected helpful functions for bot's functioning.
  """

  @staticmethod
  def generate_properties(*, exclude: set[str] = None):
    """
    Decorator that creates a @property value for every hidden ariable starting with "_".
    """
    exclude = exclude or set()

    def decorator(cls):
      for attr in cls.__annotations__:
        if attr.startswith("_") and attr not in exclude:
          public = attr[1:]
          if not hasattr(cls, public):
            setattr(cls, public, property(lambda self, a=attr: getattr(self, a)))
      return cls

    return decorator
  
  @staticmethod
  def hash(s: str) -> str:
    """
    Returns the hash of a string
    """
    return hashlib.sha256(s.encode()).hexdigest()

  @staticmethod
  def verify_password(text, hashed_text):
    return Utils.hash(text) == hashed_text


class Timer:
  """
  Collection of helful utilities used across the bot:
    - now(): get current time in UTC+3
    - db_conn(): decorator for DB connection handling
    - send_message(): abstracted messaging sender (Telegram / logging / testing)
  """

  @staticmethod
  def now() -> datetime:
    """Return current time with timezone UTC+3."""
    return datetime.now(timezone(timedelta(hours=3)))
  
  @staticmethod
  def time_to_int(time: datetime) -> int:
    """Counts how many seconds have passed since the beginning of the quest"""
    # TODO: put START_TIME in .env, then uncomment the line below
    # TODO: return int(time.timestamp() - START_TIME)
    return 0 


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
      logger.error("Error while sending message: cannot send a message without recipient's ID")
      raise SendMessageException("Cannot send a message without recipient's ID")
    if not message.recipient_id:
      message.recipient_id = id
    # TODO: add the actual sending here
    logger.info(f"[SEND] → {message.recipient_id}: {message.text}")
