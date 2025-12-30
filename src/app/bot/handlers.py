import time
import asyncio
from aiogram import Router as TgRouter
from aiogram.types import Message as TgMessage
import logging

from .message_handler import MessageHandler
from .router import Router
from .sender import send_messages
from .mediagroup_collector import MediaGroupCollector
from ..core import Message

tg_router = TgRouter()
logger = logging.getLogger(__name__)


async def handle_ready_message(core_msg: Message):
  response = Router.route(core_msg)
  await send_messages(response, core_msg.bot)


collector = MediaGroupCollector(
  timeout=0.25,
  on_ready=lambda m: asyncio.ensure_future(handle_ready_message(m)),
)

@tg_router.message()
async def handle_message(msg: TgMessage) -> None:
  """
  Handle incoming Telegram messages.
  1. Convert the Telegram message to a core message format.
  2. Route the core message to get a response.
  3. Send the response back via Telegram.
  """
  core_msg = await collector.add(msg)

  if core_msg:
    response = Router.route(core_msg)
    await send_messages(response, msg.bot)

@tg_router.callback_query()
async def handle_callback(callback_query: TgMessage) -> None:
  """
  Handle callback queries (inline keyboard button presses).
  """
  core_msg = await MessageHandler.from_tg(callback_query)
  if core_msg:
    response = Router.route(core_msg)
    await send_messages(response, callback_query.bot)

  await callback_query.answer()
