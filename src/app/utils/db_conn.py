from __future__ import annotations
from functools import wraps
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class DB:
  """
  Creates and closes DB connection around the function call.
  """
  @staticmethod
  def connect(func: Callable) -> Callable:
    """
    Decorator that manages his classes's job.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
      # specify the connection here  

      conn = get_connection()
      logger.debug(f"Opening DB connection for {func.__name__}")

      try:
        result = func(*args, conn=conn, **kwargs)
        conn.commit()
        logger.debug(f"Committing DB transaction in {func.__name__}")
        return result
      except Exception as e:
        conn.rollback()
        logger.error(f"Error in {func.__name__}: {e}")
        raise
      finally:
        conn.close()
        logger.debug(f"Closing DB connection in {func.__name__}")

    return wrapper