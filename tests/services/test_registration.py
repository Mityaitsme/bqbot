import pytest
from unittest.mock import MagicMock, patch
from src.app.services.registration import RegistrationService, RegistrationContext, RegistrationStep
from src.app.core import Message
from src.app.db import TeamRepo, MemberRepo, RiddleRepo


# ---------- fixtures ----------

@pytest.fixture
def user_id():
  return 100


# ---------- start ----------

def test_start_sets_initial_state(user_id):
  with patch.object(MemberRepo, 'get', return_value=None):
    msg = RegistrationService._start(user_id)
    
    assert isinstance(msg, Message)
    assert "1) Присоединиться" in msg.text
    assert RegistrationService.is_active(user_id) is True


def test_start_already_registered(user_id):
  mock_member = MagicMock()
  with patch.object(RegistrationService, '_load_context', return_value=None):
    with patch('src.app.services.registration.MemberRepo.get', return_value=mock_member):
      msg = RegistrationService._start(user_id)
      
      assert "уже зарегистрированы" in msg.text


# ---------- role selection ----------

def test_handle_input_invalid_role(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_ROLE
  )
  
  msg = RegistrationService.handle_input(user_id, "invalid")
  
  assert "ответьте 1 или 2" in msg.text
  assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_ROLE


def test_handle_input_join_team(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_ROLE
  )
  
  msg = RegistrationService.handle_input(user_id, "1")
  
  assert RegistrationService._contexts[user_id].mode == "join"
  assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_TEAM_NAME
  assert "имя команды" in msg.text


def test_handle_input_create_team(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_ROLE
  )
  
  msg = RegistrationService.handle_input(user_id, "2")
  
  assert RegistrationService._contexts[user_id].mode == "create"
  assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_TEAM_NAME
  assert "имя команды" in msg.text


# ---------- team name (join mode) ----------

def test_handle_input_join_team_name_not_found(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_TEAM_NAME,
    mode="join"
  )
  
  with patch.object(TeamRepo, 'get_by_name', return_value=None):
    msg = RegistrationService.handle_input(user_id, "Nonexistent Team")
    
    assert "не найдена" in msg.text
    assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_TEAM_NAME


def test_handle_input_join_team_name_found(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_TEAM_NAME,
    mode="join"
  )
  
  mock_team = MagicMock()
  with patch.object(TeamRepo, 'get_by_name', return_value=mock_team):
    msg = RegistrationService.handle_input(user_id, "Existing Team")
    
    assert RegistrationService._contexts[user_id].team_name == "Existing Team"
    assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_PASSWORD
    assert "пароль" in msg.text


# ---------- team name (create mode) ----------

def test_handle_input_create_team_name_taken(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_TEAM_NAME,
    mode="create"
  )
  
  mock_team = MagicMock()
  with patch.object(TeamRepo, 'get_by_name', return_value=mock_team):
    msg = RegistrationService.handle_input(user_id, "Taken Team")
    
    assert "уже занято" in msg.text
    assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_TEAM_NAME


def test_handle_input_create_team_name_available(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_TEAM_NAME,
    mode="create"
  )
  
  with patch.object(TeamRepo, 'get_by_name', return_value=None):
    msg = RegistrationService.handle_input(user_id, "New Team")
    
    assert RegistrationService._contexts[user_id].team_name == "New Team"
    assert RegistrationService._contexts[user_id].step == RegistrationStep.CONFIRM_TEAM_NAME
    assert "Подтвердите" in msg.text


# ---------- team name confirmation ----------

def test_handle_input_confirm_name_invalid(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.CONFIRM_TEAM_NAME,
    team_name="New Team",
    mode="create"
  )
  
  msg = RegistrationService.handle_input(user_id, "maybe")
  
  assert "ответьте" in msg.text.lower()
  assert RegistrationService._contexts[user_id].step == RegistrationStep.CONFIRM_TEAM_NAME


def test_handle_input_confirm_name_no(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.CONFIRM_TEAM_NAME,
    team_name="New Team",
    mode="create"
  )
  
  msg = RegistrationService.handle_input(user_id, "нет")
  
  assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_TEAM_NAME
  assert "ещё раз" in msg.text


def test_handle_input_confirm_name_yes(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.CONFIRM_TEAM_NAME,
    team_name="New Team",
    mode="create"
  )
  
  msg = RegistrationService.handle_input(user_id, "да")
  
  assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_PASSWORD
  assert "пароль" in msg.text


# ---------- password (join mode) ----------

def test_handle_input_join_password_wrong(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_PASSWORD,
    mode="join",
    team_name="Existing Team"
  )
  
  mock_team = MagicMock()
  mock_team.verify_password.return_value = False
  with patch.object(TeamRepo, 'get_by_name', return_value=mock_team):
    msg = RegistrationService.handle_input(user_id, "wrongpass")
    
    assert "Неверный пароль" in msg.text
    assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_PASSWORD


def test_handle_input_join_password_success(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_PASSWORD,
    mode="join",
    team_name="Existing Team"
  )
  
  mock_team = MagicMock()
  mock_team.verify_password.return_value = True
  mock_team.cur_stage = 1
  mock_team.id = 5
  
  mock_riddle = MagicMock()
  
  with patch.object(TeamRepo, 'get_by_name', return_value=mock_team):
    with patch.object(RiddleRepo, 'get', return_value=mock_riddle):
      with patch.object(MemberRepo, 'insert'):
        msg = RegistrationService.handle_input(user_id, "correctpass")
        
        assert user_id not in RegistrationService._contexts
        assert isinstance(msg, Message)


# ---------- password (create mode) ----------

def test_handle_input_create_password(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_PASSWORD,
    mode="create",
    team_name="New Team"
  )
  
  with patch('src.app.services.registration.Utils.hash', return_value="hashed_password"):
    msg = RegistrationService.handle_input(user_id, "mypassword")
    
    assert RegistrationService._contexts[user_id].password_hash == "hashed_password"
    assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_PASSWORD_REPEAT
    assert "Повторите" in msg.text


# ---------- password repeat ----------

def test_handle_input_password_repeat_mismatch(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_PASSWORD_REPEAT,
    mode="create",
    team_name="New Team",
    password_hash="hashed_password"
  )
  
  with patch('src.app.services.registration.Utils.verify_password', return_value=False):
    msg = RegistrationService.handle_input(user_id, "different")
    
    assert "не совпадают" in msg.text
    assert RegistrationService._contexts[user_id].step == RegistrationStep.ASK_PASSWORD_REPEAT


def test_handle_input_password_repeat_success(user_id):
  RegistrationService._contexts[user_id] = RegistrationContext(
    user_id=user_id,
    step=RegistrationStep.ASK_PASSWORD_REPEAT,
    mode="create",
    team_name="New Team",
    password_hash="hashed_password"
  )
  
  mock_team = MagicMock()
  mock_team.cur_stage = 1
  mock_team.id = 10
  
  mock_riddle = MagicMock()
  
  with patch('src.app.services.registration.Utils.verify_password', return_value=True):
    with patch('src.app.services.registration.TeamRepo.insert', return_value=10):
      with patch('src.app.services.registration.TeamRepo.update'):
        with patch('src.app.services.registration.MemberRepo.insert'):
          with patch('src.app.services.registration.RiddleRepo.get', return_value=mock_riddle):
            with patch('src.app.services.registration.Team') as MockTeam:
              MockTeam.return_value = mock_team
              msg = RegistrationService.handle_input(user_id, "mypassword")
              
              assert user_id not in RegistrationService._contexts
              assert isinstance(msg, Message)

def test_clear_contexts():
  RegistrationService._clear_contexts()
  assert len(RegistrationService._contexts) == 0

def test_handle_input_unexpected_step():
  mock_ctx = MagicMock()
  mock_ctx.step = "UNKNOWN_STEP"
  
  with patch('src.app.services.registration.RegistrationService._load_context', return_value=mock_ctx):
    with patch('src.app.services.registration.RegistrationService._start'):
      with pytest.raises(RuntimeError) as exc_info:
        RegistrationService.handle_input(user_id=1, text="test")
      
      assert "Unexpected registration step" in str(exc_info.value)
