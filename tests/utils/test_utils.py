import pytest
from unittest.mock import MagicMock, patch

from dataclasses import dataclass
from datetime import datetime
from datetime import datetime, timezone, timedelta

from src.app.utils import Utils, Timer

# --- NOW ---

def test_now_returns_datetime():
  now = Timer.now()
  assert isinstance(now, datetime)


# --- HASH ---

def test_hash_returns_string():
  value = Utils.hash("password")

  assert isinstance(value, str)
  assert len(value) > 0


def test_hash_same_input_same_output():
  h1 = Utils.hash("password")
  h2 = Utils.hash("password")

  assert h1 == h2


def test_hash_different_input_different_output():
  h1 = Utils.hash("password")
  h2 = Utils.hash("password2")

  assert h1 != h2


def test_hash():
  h = Utils.hash("test")
  assert isinstance(h, str)
  assert len(h) == 64

def test_verify_password():
  h = Utils.hash("secret")
  assert Utils.verify_password("secret", h) is True
  assert Utils.verify_password("wrong", h) is False

def test_normalize():
  assert Utils.normalize("  HeLLo   WorlD  ") == "hello world"

def test_timer_now():
  now = Timer.now()
  assert now.tzinfo == timezone(timedelta(hours=3))

def test_timer_time_to_int():
  with patch('src.app.utils.utils.START_TIME', 1000):
    dt = datetime.fromtimestamp(1050)
    assert Timer.time_to_int(dt) == 50


# --- GENERATE PROPERTIES ---

def test_generate_properties_creates_property():
  @Utils.generate_properties()
  @dataclass
  class Test:
    _value: int

  t = Test(10)

  assert t.value == 10


def test_generate_properties_exclude():
  @Utils.generate_properties(exclude={"_secret"})
  @dataclass
  class Test:
    _value: int
    _secret: int

  t = Test(1, 2)

  assert t.value == 1
  assert not hasattr(t, "secret")

