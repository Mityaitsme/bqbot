import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy import text
from src.app.db.db_conn import DB

def test_session_commit():
  mock_session = MagicMock()
  with patch('src.app.db.db_conn.SessionFactory', return_value=mock_session):
    with DB.session() as s:
      assert s == mock_session
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()

def test_session_rollback():
  mock_session = MagicMock()
  with patch('src.app.db.db_conn.SessionFactory', return_value=mock_session):
    with pytest.raises(ValueError):
      with DB.session() as s:
        raise ValueError("error")
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()

def test_select_simple():
  mock_session = MagicMock()
  mock_result = MagicMock()
  mock_result_row = MagicMock()
  mock_result_row._mapping = {"id": 1, "name": "test"}
  mock_result.__iter__.return_value = [mock_result_row]
  mock_session.execute.return_value = mock_result

  with patch('src.app.db.db_conn.SessionFactory', return_value=mock_session):
    res = DB.select(table="teams")
    
    assert res == [{"id": 1, "name": "test"}]
    args, kwargs = mock_session.execute.call_args
    assert "SELECT * FROM teams" in str(args[0])
    assert args[1] == {}

def test_select_with_where():
  mock_session = MagicMock()
  mock_session.execute.return_value = []
  
  with patch('src.app.db.db_conn.SessionFactory', return_value=mock_session):
    DB.select(table="teams", where={"id": 5, "active": True})
    
    args, kwargs = mock_session.execute.call_args
    sql = str(args[0])
    params = args[1]
    
    assert "WHERE" in sql
    assert "id = :id" in sql
    assert "active = :active" in sql
    assert params == {"id": 5, "active": True}

def test_insert():
  mock_session = MagicMock()
  mock_session.execute.return_value.scalar_one.return_value = 10
  
  with patch('src.app.db.db_conn.SessionFactory', return_value=mock_session):
    new_id = DB.insert(table="teams", values={"name": "A"})
    
    assert new_id == 10
    args, _ = mock_session.execute.call_args
    sql = str(args[0])
    assert "INSERT INTO teams" in sql
    assert "VALUES (:name)" in sql

def test_update():
  mock_session = MagicMock()
  
  with patch('src.app.db.db_conn.SessionFactory', return_value=mock_session):
    DB.update(table="teams", id=5, values={"score": 100})
    
    args, _ = mock_session.execute.call_args
    sql = str(args[0])
    params = args[1]
    
    assert "UPDATE teams SET" in sql
    assert "id = :id" in sql
    assert params["id"] == 5
    assert params["score"] == 100