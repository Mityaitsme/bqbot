import pytest
from datetime import datetime, timezone, timedelta

from src.app.core import Message, Member, Team

@pytest.fixture
def fixed_time():
  return datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=3)))


@pytest.fixture
def test_member():
  return Member(
    id=1,
    tg_nickname="tester",
    name="Test User",
    team_id=1,
  )


@pytest.fixture
def test_team(test_member, fixed_time):
  team = Team(
    _id=1,
    _name="TestTeam",
    _Team__password_hash="hash123",
    _cur_member_id=test_member.id,
    _stage_call_time=fixed_time,
  )
  return team


@pytest.fixture
def core_message():
  return Message(
    _user_id=123,
    _text="test",
  )
