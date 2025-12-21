import pytest
from types import SimpleNamespace

from src.app.bot.message_handler import MessageHandler
from src.app.core import Message


def make_tg_message(user_id=1, text="hello"):
  return SimpleNamespace(
    from_user=SimpleNamespace(id=user_id),
    text=text,
  )


def test_from_tg_basic():
  tg_msg = make_tg_message(42, "hi")
  msg = MessageHandler.from_tg(tg_msg)

  assert isinstance(msg, Message)
  assert msg.user_id == 42
  assert msg.text == "hi"


def test_from_tg_empty_text():
  tg_msg = make_tg_message(10, None)
  msg = MessageHandler.from_tg(tg_msg)

  assert msg.text == ""


def test_from_tg_whitespace_preserved():
  tg_msg = make_tg_message(5, "  test ")
  msg = MessageHandler.from_tg(tg_msg)

  assert msg.text == "  test "
