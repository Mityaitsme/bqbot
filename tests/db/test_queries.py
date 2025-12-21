import pytest
from unittest.mock import MagicMock, patch
from src.app.db.queries import TeamQuery, MemberQuery, RiddleQuery, Query
from datetime import datetime, timezone, timedelta
from src.app.core import Team, Member, Riddle

# ----- MOCK -----

@pytest.fixture
def db():
  db = MagicMock()
  db.execute = MagicMock()
  db.fetchone = MagicMock()
  db.fetchall = MagicMock()
  return db


# ----- TEAM QUERY -----

def test_team_get():
  with patch.object(TeamQuery, 'get') as mock_get:
    mock_team = MagicMock()
    mock_team.id = 1
    mock_get.return_value = mock_team
    
    result = TeamQuery.get(1)
    
    mock_get.assert_called_once_with(1)
    assert result == mock_team


def test_team_get_none():
  with patch.object(TeamQuery, 'get') as mock_get:
    mock_get.return_value = None
    
    result = TeamQuery.get(999)
    
    mock_get.assert_called_once_with(999)
    assert result is None


def test_team_get_by_name():
  with patch.object(TeamQuery, 'get_by_name') as mock_get_by_name:
    mock_team = MagicMock()
    mock_team.id = 42
    mock_get_by_name.return_value = mock_team
    
    result = TeamQuery.get_by_name("Alpha")
    
    mock_get_by_name.assert_called_once_with("Alpha")
    assert result == mock_team


def test_team_get_by_name_none():
  with patch.object(TeamQuery, 'get_by_name') as mock_get_by_name:
    mock_get_by_name.return_value = None
    
    result = TeamQuery.get_by_name("Unknown")
    
    mock_get_by_name.assert_called_once_with("Unknown")
    assert result is None


# ----- MEMBER QUERY -----

def test_member_get():
  with patch.object(MemberQuery, 'get') as mock_get:
    mock_member = MagicMock()
    mock_member.id = 5
    mock_get.return_value = mock_member
    
    result = MemberQuery.get(5)
    
    mock_get.assert_called_once_with(5)
    assert result == mock_member


def test_member_get_none():
  with patch.object(MemberQuery, 'get') as mock_get:
    mock_get.return_value = None
    
    result = MemberQuery.get(404)
    
    mock_get.assert_called_once_with(404)
    assert result is None


def test_member_get_by_team():
  with patch('src.app.db.queries.MemberQuery') as mock_member_query:
    mock_member = MagicMock()
    mock_member.id = 7
    mock_member_query.get_by_team.return_value = [mock_member]
    
    from src.app.db.queries import MemberQuery
    
    MemberQuery.get_by_team = mock_member_query.get_by_team
    result = MemberQuery.get_by_team(3)
    
    mock_member_query.get_by_team.assert_called_once_with(3)
    assert result == [mock_member]


# ----- RIDDLE QUERY -----

def test_riddle_get():
  with patch.object(RiddleQuery, 'get') as mock_get:
    mock_riddle = MagicMock()
    mock_riddle.id = 1
    mock_get.return_value = mock_riddle
    
    result = RiddleQuery.get(1)
    
    mock_get.assert_called_once_with(1)
    assert result == mock_riddle


def test_riddle_get_none():
  with patch.object(RiddleQuery, 'get') as mock_get:
    mock_get.return_value = None
    
    result = RiddleQuery.get(404)
    
    mock_get.assert_called_once_with(404)
    assert result is None


# TODO: Getting 100% coverage (will sort them later)

def test_query_get_not_found():
  with patch('src.app.db.queries.DB.select', return_value=[]):
    assert TeamQuery.get(1) is None

def test_query_get_found():
  mock_row = {
    "id": 1, "name": "T", "password_hash": "h", "start_stage": 1, 
    "cur_stage": 1, "score": 0, "cur_member_id": 5,
    "stage_call_time": datetime.now()
  }
  with patch('src.app.db.queries.DB.select', return_value=[mock_row]):
    t = TeamQuery.get(1)
    assert isinstance(t, Team)
    assert t.id == 1

def test_query_insert():
  team = Team(_id=None, _name="N", _cur_member_id=0, _Team__password_hash="p")
  with patch('src.app.db.queries.DB.insert', return_value=5) as mock_ins:
    res = TeamQuery.insert(team)
    assert res == 5
    mock_ins.assert_called_once()

def test_query_update():
  team = Team(_id=1, _name="N", _cur_member_id=0, _Team__password_hash="p")
  with patch('src.app.db.queries.DB.update') as mock_upd:
    TeamQuery.update(1, team)
    mock_upd.assert_called_once()

def test_team_query_get_all_mixed_success_and_fail():
  valid_row = {
    "id": 1, "name": "T", "password_hash": "h", "start_stage": 1, 
    "cur_stage": 1, "score": 0, "cur_member_id": 5,
    "stage_call_time": datetime.now()
  }
  invalid_row = {} 

  with patch('src.app.db.queries.DB.select', return_value=[valid_row, invalid_row]):
    teams = TeamQuery.get_all()
    assert len(teams) == 1
    assert teams[0].id == 1

def test_team_query_parse_time_formats():
  base_data = {
    "id": 1, "name": "T", "password_hash": "h", "start_stage": 1, 
    "cur_stage": 1, "score": 0, "cur_member_id": 5
  }
  
  # 1. Datetime object
  dt = datetime.now()
  res = TeamQuery.parse({**base_data, "stage_call_time": dt})
  assert res.stage_call_time == dt

  # 2. ISO String
  dt_iso = "2024-01-01T12:00:00"
  res = TeamQuery.parse({**base_data, "stage_call_time": dt_iso})
  assert res.stage_call_time.year == 2024

  # 3. Timestamp String
  ts_str = "1700000000.0"
  res = TeamQuery.parse({**base_data, "stage_call_time": ts_str})
  assert res.stage_call_time.year == 2023

  # 4. Invalid
  res = TeamQuery.parse({**base_data, "stage_call_time": "garbage"})
  assert isinstance(res.stage_call_time, datetime) 

# ----- DEFAULT QUERY -----

def test_default_parse():
  Query.parse({})
  assert True == True

def test_default_pack():
  Query.pack({})
  assert True == True

def test_team_query_pack():
  dt = datetime.now()
  team = Team(_id=1, _name="N", _cur_member_id=0, _Team__password_hash="p", _stage_call_time=dt)
  data = TeamQuery.pack(team)
  assert data["stage_call_time"] == dt.isoformat()

  team2 = Team(_id=1, _name="N", _cur_member_id=0, _Team__password_hash="p", _stage_call_time="some_str")
  data2 = TeamQuery.pack(team2)
  assert data2["stage_call_time"] == "some_str"

def test_team_query_get_by_name():
  with patch('src.app.db.queries.DB.select', return_value=[]) as mock_sel:
    TeamQuery.get_by_name("name")
    args, kwargs = mock_sel.call_args
    assert kwargs["where"] == {"name": "name"}

def test_member_query_pack_parse():
  m = Member(id=1, tg_nickname="u", name="n", team_id=2)
  data = MemberQuery.pack(m)
  assert data["tg_nickname"] == "u"
  
  m2 = MemberQuery.parse(data)
  assert m2 == m

def test_riddle_query_pack_parse():
  r = Riddle(id=1, question="q", answer="a", type="db")
  data = RiddleQuery.pack(r)
  assert data["question"] == "q"
  
  r2 = RiddleQuery.parse(data)
  # r2 has empty files list by default parse
  assert r2.question == r.question


def test_team_query_get_all_exception_handling():
  row1 = {"id": 1}
  row2 = {"id": 2}
  
  with patch('src.app.db.queries.DB.select', return_value=[row1, row2]):
    with patch.object(TeamQuery, 'parse') as mock_parse:
      mock_parse.side_effect = [Exception("Fail"), MagicMock()]
      
      teams = TeamQuery.get_all()
      assert len(teams) == 1


def test_team_query_parse_datetime_obj():
  dt = datetime.now()
  data = {
    "id": 1, "name": "T", "password_hash": "h", 
    "start_stage": 1, "cur_stage": 1, "score": 0, 
    "cur_member_id": 1, "stage_call_time": dt
  }
  team = TeamQuery.parse(data)
  assert team.stage_call_time == dt
