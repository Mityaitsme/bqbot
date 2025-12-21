import pytest
from unittest.mock import MagicMock, patch
from src.app.core import QuestEngine, Message
from src.app.exceptions import TeamError, RiddleError, AnswerError
from src.app.db import TeamRepo, RiddleRepo


# ---------- get_riddle ----------

def test_get_riddle_team_not_found():
  with patch.object(TeamRepo, 'get', return_value=None):
    with pytest.raises(TeamError) as exc_info:
      QuestEngine.get_riddle(team_id=999)
    
    assert "Team 999 not found" in str(exc_info.value)


def test_get_riddle_riddle_not_found():
  mock_team = MagicMock()
  mock_team.cur_stage = 1
  
  with patch.object(TeamRepo, 'get', return_value=mock_team):
    with patch.object(RiddleRepo, 'get', return_value=None):
      with pytest.raises(RiddleError) as exc_info:
        QuestEngine.get_riddle(team_id=1)
      
      assert "Riddle for stage 1 not found" in str(exc_info.value)


def test_get_riddle_success():
  mock_team = MagicMock()
  mock_team.cur_stage = 1
  
  mock_riddle = MagicMock()
  mock_riddle.question = "What?"
  mock_riddle.answer = "answer"
  mock_riddle.type = "text"
  
  mock_message = MagicMock()
  mock_message.text = "What?"
  
  with patch.object(TeamRepo, 'get', return_value=mock_team):
    with patch.object(RiddleRepo, 'get', return_value=mock_riddle):
      with patch.object(Message, 'from_riddle', return_value=mock_message):
        result = QuestEngine.get_riddle(team_id=1)
        
        assert result == mock_message
        Message.from_riddle.assert_called_once_with(mock_riddle)


# ---------- check_answer ----------

def test_check_answer_team_not_found():
  mock_message = MagicMock()
  mock_message.text = "answer"
  
  with patch.object(TeamRepo, 'get', return_value=None):
    with pytest.raises(TeamError) as exc_info:
      QuestEngine.check_answer(team_id=1, message=mock_message)
    
    assert "Team 1 not found" in str(exc_info.value)


def test_check_answer_riddle_not_found():
  mock_team = MagicMock()
  mock_team.cur_stage = 1
  
  mock_message = MagicMock()
  mock_message.text = "answer"
  
  with patch.object(TeamRepo, 'get', return_value=mock_team):
    with patch.object(RiddleRepo, 'get', return_value=None):
      with pytest.raises(RiddleError) as exc_info:
        QuestEngine.check_answer(team_id=1, message=mock_message)
      
      assert "Riddle for stage 1 not found" in str(exc_info.value)


def test_check_answer_exception_in_check():
  mock_team = MagicMock()
  mock_team.cur_stage = 1
  
  mock_riddle = MagicMock()
  mock_riddle.check_answer.side_effect = Exception("Check failed")
  
  mock_message = MagicMock()
  mock_message.text = "answer"
  
  with patch.object(TeamRepo, 'get', return_value=mock_team):
    with patch.object(RiddleRepo, 'get', return_value=mock_riddle):
      with pytest.raises(AnswerError) as exc_info:
        QuestEngine.check_answer(team_id=1, message=mock_message)
      
      assert "Failed to validate answer" in str(exc_info.value)


def test_check_answer_correct():
  mock_team = MagicMock()
  mock_team.cur_stage = 1
  mock_team.next_stage = MagicMock()
  
  mock_riddle = MagicMock()
  mock_riddle.check_answer.return_value = True
  
  mock_new_riddle = MagicMock()
  mock_message = MagicMock()
  mock_message.text = "answer"
  mock_message.recipient_id = 123
  
  mock_reply = MagicMock()
  
  with patch.object(TeamRepo, 'get', return_value=mock_team):
    with patch.object(RiddleRepo, 'get', side_effect=[mock_riddle, mock_new_riddle]):
      with patch.object(Message, 'from_riddle', return_value=mock_reply):
        with patch.object(TeamRepo, 'update'):
          result = QuestEngine.check_answer(team_id=1, message=mock_message)
          
          mock_team.next_stage.assert_called_once()
          TeamRepo.update.assert_called_once_with(mock_team, event="correct answer")
          Message.from_riddle.assert_called_once_with(mock_new_riddle)
          assert result.recipient_id == mock_message.recipient_id


def test_check_answer_incorrect():
  mock_team = MagicMock()
  mock_team.cur_stage = 1
  
  mock_riddle = MagicMock()
  mock_riddle.check_answer.return_value = False
  
  mock_message = MagicMock()
  mock_message.text = "wrong"
  mock_message.recipient_id = 123
  
  with patch.object(TeamRepo, 'get', return_value=mock_team):
    with patch.object(RiddleRepo, 'get', return_value=mock_riddle):
      result = QuestEngine.check_answer(team_id=1, message=mock_message)
      
      assert "Неправильно" in result.text
      assert result.recipient_id == mock_message.recipient_id
