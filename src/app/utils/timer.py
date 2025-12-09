from __future__ import annotations

import functools
import logging
from datetime import datetime, timezone, timedelta
from typing import Callable, Any

logger = logging.getLogger(__name__)

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
    # put START_TIME in .env, then uncomment the line below
    # return int(time.timestamp() - START_TIME)
    return 0 
