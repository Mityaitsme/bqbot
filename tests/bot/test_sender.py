import pytest
from unittest.mock import AsyncMock

from src.app.bot.sender import send_message
from src.app.core import Message

@pytest.mark.asyncio
async def test_send_message_ok():
  bot = AsyncMock()
  msg = Message(_user_id=123, _text="hello")

  await send_message(bot, msg)

  bot.send_message.assert_awaited_once_with(
    chat_id=123,
    text="hello",
  )


@pytest.mark.asyncio
async def test_send_message_no_user_id():
  bot = AsyncMock()
  msg = Message(_user_id=None, _text="oops")

  await send_message(bot, msg)

  bot.send_message.assert_not_called()
