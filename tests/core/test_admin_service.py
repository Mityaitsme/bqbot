import pytest
from unittest.mock import MagicMock, patch
from src.app.core.admin_service import AdminService, Message, TeamNotFound


def test_get_team_info_team_not_found():
  with patch('src.app.core.admin_service.TeamRepo') as mock_team_repo:
    mock_team_repo.get_by_name.return_value = None
    
    with pytest.raises(TeamNotFound) as exc_info:
      AdminService.get_team_info(team_name="nonexistent")
    
    assert "not found" in str(exc_info.value)


def test_get_team_info_success():
  mock_team = MagicMock()
  mock_team.id = 5
  mock_team.name = "Test Team"
  mock_team.cur_stage = 3
  mock_team.score = 42
  mock_team.stage_call_time.strftime.return_value = "2024-01-01 12:00:00"
  
  mock_member1 = MagicMock()
  mock_member1.tg_nickname = "@user1"
  mock_member2 = MagicMock()
  mock_member2.tg_nickname = "@user2"
  
  with patch('src.app.core.admin_service.TeamRepo') as mock_team_repo:
    with patch('src.app.core.admin_service.MemberRepo') as mock_member_repo:
      mock_team_repo.get_by_name.return_value = mock_team
      mock_member_repo.get_by_team.return_value = [mock_member1, mock_member2]
      
      with patch('src.app.core.admin_service.ADMIN', 123):
        result = AdminService.get_team_info(team_name="Test Team")
        
        assert isinstance(result, Message)
        assert "Test Team" in result.text
        assert "id=5" in result.text
        assert "Stage: 3" in result.text
        assert "Score: 42" in result.text
        assert "@user1" in result.text
        assert "@user2" in result.text
        assert "2024-01-01 12:00:00" in result.text
        assert result.recipient_id == 123


def test_get_all_teams_info_empty():
  with patch('src.app.core.admin_service.TeamRepo') as mock_team_repo:
    mock_team_repo.get_all.return_value = []
    
    with patch('src.app.core.admin_service.ADMIN', 123):
      msg = AdminService.get_all_teams_info()
      
      assert "no teams" in msg.text.lower()
      assert msg.recipient_id == 123


def test_get_all_teams_info_success():
  mock_team = MagicMock()
  mock_team.id = 1
  mock_team.name = "Test Team"
  mock_team.cur_stage = 2
  mock_team.score = 10
  
  with patch('src.app.core.admin_service.TeamRepo') as mock_team_repo:
    mock_team_repo.get_all.return_value = [mock_team]
    
    with patch('src.app.core.admin_service.ADMIN', 123):
      msg = AdminService.get_all_teams_info()
      
      assert "Test Team" in msg.text
      assert "1" in msg.text
      assert msg.recipient_id == 123


def test_get_scoring_system():
  with patch('src.app.core.admin_service.ADMIN', 123):
    msg = AdminService.get_scoring_system()
    
    assert isinstance(msg, Message)
    assert "scoring" in msg.text.lower()
    assert msg.recipient_id == 123
