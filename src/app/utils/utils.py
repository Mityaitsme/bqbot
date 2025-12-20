from __future__ import annotations

import logging
import logging
from datetime import datetime, timezone, timedelta
import hashlib
from ...config import START_TIME

logger = logging.getLogger(__name__)

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
  def verify_password(text: str, hashed_text: str):
    """
    Compares the given password to the correct hashed password.
    """
    return Utils.hash(text) == hashed_text
  
  @staticmethod
  def normalize(text: str):
    """
    Turns a string to lowercase; deletes double spacings.
    """
    text = text.lower()
    text = " ".join(text.split())
    return text


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
    return int(time.timestamp() - START_TIME)
