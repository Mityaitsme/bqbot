from aiogram import Router as TgRouter
from aiogram.types import Message as TgMessage
import logging

from .message_handler import MessageHandler
from .router import Router
from .sender import send_message

tg_router = TgRouter()
logger = logging.getLogger(__name__)


@tg_router.message()
async def handle_message(msg: TgMessage) -> None:
  core_msg = MessageHandler.from_tg(msg)
  response = Router.route(core_msg)
  await send_message(msg.bot, response)
