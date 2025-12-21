import pytest
from src.app.core import Message, Member, Team, Riddle
from datetime import datetime
from src.app.utils import Utils
from src.app.core import FileExtension, Riddle, Team, Message
from unittest.mock import MagicMock, patch
from src.config import STAGE_COUNT

# ----- MESSAGE -----

def test_message_creation():
  msg = Message(_user_id=1, _text="hello")

  assert msg._user_id == 1
  assert msg.text == "hello"


def test_message_empty_text():
  msg = Message(_user_id=1, _text="")

  assert msg.text == ""


def test_message_repr():
  msg = Message(_user_id=5, _text="hi")
  repr_str = repr(msg)

  assert "Message" in repr_str
  assert "_user_id=5" in repr_str


def test_message_type_text_only():
  msg = Message(_text="hello")
  assert msg.type == "text"

def test_message_type_voice():
  f1 = MagicMock(spec=FileExtension)
  f1.filename_extension = ".mp3"
  msg = Message(_text="", _files=[f1])
  assert msg.type == "voice"

def test_message_type_gallery():
  f1 = MagicMock(spec=FileExtension)
  f1.filename_extension = ".jpg"
  f2 = MagicMock(spec=FileExtension)
  f2.filename_extension = ".mp4"
  msg = Message(_text="", _files=[f1, f2])
  assert msg.type == "gallery"

def test_message_type_other():
  f1 = MagicMock(spec=FileExtension)
  f1.filename_extension = ".pdf"
  msg = Message(_text="", _files=[f1])
  assert msg.type == "other"

def test_message_recipient_id_setter():
  msg = Message(_text="test")
  msg.recipient_id = 123
  assert msg.recipient_id == 123
  assert msg._recipient_id == 123


# ----- MEMBER -----

def test_member_creation():
  member = Member(
    id=1,
    tg_nickname="tg_user",
    name="User",
    team_id=10,
  )

  assert member.id == 1
  assert member.tg_nickname == "tg_user"
  assert member.name == "User"
  assert member.team_id == 10


def test_member_is_immutable():
  member = Member(
    id=1,
    tg_nickname="tg_user",
    name="User",
    team_id=10,
  )

  try:
    member.name = "Other"
    assert False, "Member must be frozen"
  except Exception:
    assert True


# ----- TEAM -----

def make_team(password: str = "hash") -> Team:
  return Team(
    _id=1,
    _name="Team",
    _Team__password_hash=Utils.hash(password),
    _start_stage=1,
    _cur_stage=1,
    _score=0,
    _cur_member_id=1,
  )


def test_team_properties():
  team = make_team()

  assert team.id == 1
  assert team.name == "Team"
  assert team.start_stage == 1
  assert team.cur_stage == 1
  assert team.score == 0
  assert team.cur_member_id == 1


def test_team_verify_password_ok():
  team = make_team(password="secret")

  assert team.verify_password("secret") is True


def test_team_verify_password_fail():
  team = make_team(password="secret")

  assert team.verify_password("wrong") is False


def test_team_next_stage_increments_usual():
  team = make_team()

  old_stage = team.cur_stage
  old_score = team.score

  team.next_stage()

  assert team.cur_stage == old_stage + 1
  assert team.score == old_score + 1


def test_team_next_stage_increments_cycle():
  team = make_team()
  team._cur_stage = STAGE_COUNT

  old_score = team.score

  team.next_stage()

  assert team.cur_stage == 1
  assert team.score == old_score + 1


def test_team_next_stage_updates_call_time():
  team = make_team()
  old_time = team.stage_call_time

  team.next_stage()

  assert team.stage_call_time >= old_time


def test_team_verify_password():
  with patch('src.app.core.basic_classes.Utils.verify_password') as mock_verify:
    mock_verify.return_value = True
    team = Team(_id=1, _name="Test", _cur_member_id=10, _Team__password_hash="hashed_secret")
    assert team.verify_password("secret") is True
    mock_verify.assert_called_with("secret", "hashed_secret")

def test_team_setters():
  team = Team(_id=1, _name="Test", _cur_member_id=10, _Team__password_hash="hash")
  assert team.cur_member_id == 10
  team.cur_member_id = 99
  assert team.cur_member_id == 99

def test_message_user_id_setter():
  msg = Message(_text="T")
  assert msg.user_id is None
  msg.user_id = 555
  assert msg.user_id == 555

def test_team_cur_member_id_setter():
  team = Team(_id=1, _name="T", _cur_member_id=1, _Team__password_hash="pw")
  team.cur_member_id = 55
  assert team.cur_member_id == 55
  assert team._cur_member_id == 55


# ----- RIDDLE -----

def test_riddle_creation():
  riddle = Riddle(
    id=1,
    question="Question?",
    answer="answer",
    type="db",
  )

  assert riddle.id == 1
  assert riddle.question == "Question?"
  assert riddle.answer == "answer"
  assert riddle.type == "db"


def test_riddle_check_answer_finale():
  riddle = Riddle(id=1, question="End?", answer="Yes", type="finale")
  msg = Message(_text="Yes")
  assert riddle.check_answer(msg) is False


def test_riddle_check_answer_db():
  riddle = Riddle(id=1, question="Yes?", answer="Yes", type="db")
  msg = Message(_text="Yes")
  assert riddle.check_answer(msg) is True


def test_riddle_check_answer_unknown_type():
  riddle = Riddle(id=1, question="?", answer="!", type="unknown")
  msg = Message(_text="!")
  assert riddle.check_answer(msg) is None
