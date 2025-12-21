import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, Mock

from src.app.bot.router import Router
from src.app.core import Message, Team
from src.app.exceptions.base import TeamNotFound
from src.app.services.registration import RegistrationService


@pytest.fixture(autouse=True)
def reset_registration_state():
  RegistrationService._contexts.clear()


def test_admin_routed_info_all(monkeypatch):
  monkeypatch.setattr("src.app.bot.router.ADMIN", 1)

  msg = Message(_user_id=1, _text="/info_all")
  response = Router.route(msg)

  assert isinstance(response, Message)


def test_admin_routed_info_one(monkeypatch):
  monkeypatch.setattr("src.app.bot.router.ADMIN", 1)
  
  mock_team = Team(_id=1, _name="Test Team", _cur_member_id=None, _Team__password_hash = "")
  monkeypatch.setattr(
      "src.app.core.admin_service.TeamRepo.get_by_name", 
      Mock(return_value=mock_team)
  )
  
  msg = Message(_user_id=1, _text="/info 1")
  response = Router.route(msg)
  
  assert isinstance(response, Message)


def test_unregistered_user_starts_registration(monkeypatch):
  monkeypatch.setattr("src.app.bot.router.ADMIN", -1)

  monkeypatch.setattr(
    "src.app.bot.router.MemberRepo.get",
    lambda _user_id: None,
  )

  msg = Message(_user_id=100, _text="hi")
  response = Router.route(msg)

  assert isinstance(response, Message)
  assert RegistrationService.is_active(100)


def test_registration_flow(monkeypatch):
  monkeypatch.setattr("src.app.bot.router.ADMIN", -1)
  
  def get_member_side_effect(user_id):
    if user_id == 200:
      return None
    return None
  
  monkeypatch.setattr(
    "src.app.bot.router.MemberRepo.get",
    get_member_side_effect,
  )
  
  def handle_input_side_effect(user_id, text):
    return Message(_user_id=user_id, _text=f"handled: {text}")
  
  monkeypatch.setattr(
    "src.app.bot.router.RegistrationService.handle_input",
    handle_input_side_effect,
  )
  
  msg1 = Message(_user_id=200, _text="start")
  response1 = Router.route(msg1)
  
  assert isinstance(response1, Message)
  assert response1.user_id == 200


def test_regular_player_riddle(monkeypatch):
  monkeypatch.setattr("src.app.bot.router.ADMIN", -1)

  member = SimpleNamespace(id=1, team_id=10)
  team = SimpleNamespace(
    id=10,
    cur_member_id=None,
  )

  monkeypatch.setattr(
    "src.app.bot.router.MemberRepo.get",
    lambda _user_id: member,
  )

  monkeypatch.setattr(
    "src.app.bot.router.TeamRepo.get",
    lambda team_id: team,
  )

  monkeypatch.setattr(
    "src.app.bot.router.TeamRepo.update",
    lambda team, event=None: None,
  )

  monkeypatch.setattr(
    "src.app.bot.router.QuestEngine.get_riddle",
    lambda team_id: Message(_user_id=1, _text="riddle"),
  )

  msg = Message(_user_id=1, _text="/riddle")
  response = Router.route(msg)

  assert response.text == "riddle"


def test_regular_player_answer(monkeypatch):
  monkeypatch.setattr("src.app.bot.router.ADMIN", -1)
  
  member = SimpleNamespace(id=1, team_id=10)
  team = SimpleNamespace(
    id=10,
    cur_member_id=1,
  )

  monkeypatch.setattr(
    "src.app.bot.router.MemberRepo.get",
    lambda user_id: member,
  )

  monkeypatch.setattr(
    "src.app.bot.router.TeamRepo.get",
    lambda team_id: team,
  )

  monkeypatch.setattr(
    "src.app.bot.router.QuestEngine.check_answer",
    lambda team_id, msg: Message(_user_id=msg.user_id, _text="ok"),
  )

  monkeypatch.setattr(
    "src.app.bot.router.TeamRepo.update",
    lambda team, event: None,
  )
  
  msg = Message(_user_id=1, _text="answer")
  response = Router.route(msg)
  
  assert response.text == "ok"
  assert response.user_id == 1


def test_route_admin_scoring_system():
  with patch('src.app.bot.router.Router._is_admin', return_value=True):
    with patch('src.app.bot.router.AdminService.get_scoring_system') as mock_scoring:
      msg = MagicMock()
      msg.text = "/scoring_system"
      msg.user_id = 123

      mock_reply = MagicMock()
      mock_reply.user_id = None
      mock_scoring.return_value = mock_reply
      
      from src.app.bot.router import Router
      res = Router.route(msg)
      
      mock_scoring.assert_called_once()
      assert res == mock_reply
      assert res.user_id == 123

def test_route_admin_unknown_command():
  with patch('src.app.bot.router.Router._is_admin', return_value=True):
    msg = MagicMock()
    msg.text = "/abrakadabra"
    msg.user_id = 777
    
    from src.app.bot.router import Router
    res = Router.route(msg)
    
    assert "Неизвестная админ-команда" in res.text
    assert res.user_id == 777


def test_route_sets_user_id_if_none():
  msg = MagicMock()
  msg.user_id = 999
  msg.text = "hello"
  
  mock_reply = Message(_text="reply")
  assert mock_reply.user_id is None
  
  with patch('src.app.bot.router.MemberRepo.get', return_value=MagicMock()):
    with patch('src.app.bot.router.Router._route_player', return_value=mock_reply):
      result = Router.route(msg)
      assert result.user_id == 999
