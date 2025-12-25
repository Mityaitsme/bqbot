import time
import asyncio
from collections import defaultdict
from typing import Dict, List, Callable
from aiogram.types import Message as TgMessage

from .message_handler import MessageHandler
from ..core import Message


class MediaGroupCollector:
  """
  Collects Telegram media groups and converts them into a single core.Message.
  """
  def __init__(
    self,
    timeout: float,
    on_ready: Callable[[Message], None],
  ):
    self._groups: Dict[str, List[TgMessage]] = defaultdict(list)
    self._tasks: Dict[str, asyncio.Task] = {}
    self._timeout = timeout
    self._on_ready = on_ready

  def add(self, msg: TgMessage) -> Message | None:
    if msg.media_group_id is None:
      return MessageHandler.from_tg(msg)

    gid = msg.media_group_id
    self._groups[gid].append(msg)

    if gid in self._tasks:
      self._tasks[gid].cancel()

    self._tasks[gid] = asyncio.create_task(self._flush_later(gid))
    return None

  async def _flush_later(self, gid: str):
    try:
      await asyncio.sleep(self._timeout)
    except asyncio.CancelledError:
      return

    msgs = self._groups.pop(gid, [])
    self._tasks.pop(gid, None)

    if msgs:
      core_msg = MessageHandler.from_media_group(msgs)
      self._on_ready(core_msg)
