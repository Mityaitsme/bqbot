from aiogram import Router as TgRouter
from aiogram.types import Message as TgMessage
import logging

from .message_handler import MessageHandler
from .router import Router
from .sender import send_messages

tg_router = TgRouter()
logger = logging.getLogger(__name__)


@tg_router.message()
async def handle_message(msg: TgMessage) -> None:
  """
  Handle incoming Telegram messages.
  1. Convert the Telegram message to a core message format.
  2. Route the core message to get a response.
  3. Send the response back via Telegram.
  """
  core_msg = MessageHandler.from_tg(msg)
  response = Router.route(core_msg)
  await send_messages(response, msg.bot)
