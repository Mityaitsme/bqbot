from dataclasses import dataclass
import pytest
from unittest.mock import MagicMock, patch
from src.app.db.repos import TeamRepo, MemberRepo, RiddleRepo, Repo
from src.app.db.queries import Query
from src.app.core import Team
from typing import Dict, Any


def test_team_repo_get():
  with patch.object(TeamRepo.query, 'get') as mock_query_get:
    mock_team = MagicMock()
    mock_team.id = 1
    mock_query_get.return_value = mock_team
    
    with patch.object(TeamRepo.cache, 'put'):
      result = TeamRepo.get(1)
      
      mock_query_get.assert_called_once_with(1)
      assert result.id == 1


def test_member_repo_get():
  with patch.object(MemberRepo.query, 'get') as mock_query_get:
    mock_member = MagicMock()
    mock_member.id = 5
    mock_query_get.return_value = mock_member
    
    with patch.object(MemberRepo.cache, 'put'):
      result = MemberRepo.get(5)
      
      mock_query_get.assert_called_once_with(5)
      assert result.id == 5


def test_riddle_repo_get():
  with patch.object(RiddleRepo.query, 'get') as mock_query_get:
    mock_riddle = MagicMock()
    mock_riddle.id = 3
    mock_query_get.return_value = mock_riddle
    
    with patch.object(RiddleRepo.cache, 'put'):
      result = RiddleRepo.get(3)
      
      mock_query_get.assert_called_once_with(3)
      assert result.id == 3


# TODO: sort the tests below later (added for 100% coverage)

class DummyRepo(Repo[Team]):
  pass

def test_repo_get_cache_miss_db_miss():
  DummyRepo.cache = MagicMock()
  DummyRepo.query = MagicMock()
  
  DummyRepo.cache.get.return_value = None
  DummyRepo.query.get.return_value = None
  
  assert DummyRepo.get(1) is None
  DummyRepo.cache.put.assert_not_called()

def test_repo_insert_updates_private_id():
  DummyRepo.cache = MagicMock()
  DummyRepo.query = MagicMock()
  DummyRepo.query.insert.return_value = 999
  
  class ObjWithId:
    def __init__(self):
      self._id = None
  
  obj = ObjWithId()
  DummyRepo.insert(obj)
  assert obj._id == 999
  DummyRepo.cache.put.assert_called_with(obj)

def test_repo_update_no_id_raises():
  obj = MagicMock()
  obj.id = None
  with pytest.raises(ValueError):
    DummyRepo.update(obj)

def test_team_repo_get_by_member_not_found():
  with patch('src.app.db.repos.MemberRepo.get', return_value=None):
    assert TeamRepo.get_by_member(1) is None

def test_team_repo_get_by_member_found():
  mock_member = MagicMock()
  mock_member.team_id = 10
  
  with patch('src.app.db.repos.MemberRepo.get', return_value=mock_member):
    with patch('src.app.db.repos.TeamRepo.get', return_value="TeamObject") as mock_team_get:
      res = TeamRepo.get_by_member(1)
      assert res == "TeamObject"
      mock_team_get.assert_called_with(10)

def test_team_repo_get_by_name_not_found():
  with patch('src.app.db.repos.TeamQuery.get_by_name', return_value=[]):
    assert TeamRepo.get_by_name("A") is None

def test_team_repo_get_by_name_found():
  mock_team = MagicMock()
  with patch('src.app.db.repos.TeamQuery.get_by_name', return_value=[mock_team]):
    with patch('src.app.db.repos.TeamCache.put') as mock_put:
      res = TeamRepo.get_by_name("A")
      assert res == mock_team
      mock_put.assert_called_with(mock_team)

def test_team_repo_get_all():
  t1 = MagicMock(); t1.score = 10
  t2 = MagicMock(); t2.score = 20
  with patch('src.app.db.repos.TeamQuery.get_all', return_value=[t1, t2]):
    res = TeamRepo.get_all()
    assert res == [t2, t1]

def test_team_repo_update_invalid_event():
  with patch('src.app.db.repos.TeamRepo.get') as mock_get:
    TeamRepo.update(MagicMock(), "bad_event")
    mock_get.assert_not_called()

def test_team_repo_update_team_not_found():
  mock_team = MagicMock()
  mock_team.id = 1
  with patch('src.app.db.repos.TeamRepo.get', return_value=None):
    TeamRepo.update(mock_team, "correct answer")


def test_repo_get_not_found_in_db():
  DummyRepo.cache = MagicMock()
  DummyRepo.query = MagicMock()
  DummyRepo.cache.get.return_value = None
  DummyRepo.query.get.return_value = None
  
  res = DummyRepo.get(1)
  assert res is None

def test_repo_insert_attribute_error_pass():
  DummyRepo.cache = MagicMock()
  DummyRepo.query = MagicMock()
  DummyRepo.query.insert.return_value = 100
  
  class BrokenObj:
    _id = 1
    @property
    def id(self): return 1
  
  mock_obj = BrokenObj()
  
  with patch.object(BrokenObj, '_id', side_effect=AttributeError):
    DummyRepo.insert(mock_obj)

def test_repo_update_no_id_raises_value_error():
  obj = MagicMock()
  obj.id = None
  with pytest.raises(ValueError):
    DummyRepo.update(obj)

def test_member_repo_get_by_team():
  mock_row = {"id": 1}
  with patch('src.app.db.repos.DB.select', return_value=[mock_row]):
    with patch('src.app.db.repos.MemberQuery.parse', return_value="MemberObj") as mock_parse:
      res = MemberRepo.get_by_team(10)
      assert res == ["MemberObj"]
      mock_parse.assert_called_with(mock_row)


class RepoBreaker:
  @property
  def _id(self):
    return 1

class BrokenQuery(Query[RepoBreaker]):
  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> RepoBreaker:
    return RepoBreaker()
  
  @classmethod
  def pack(cls, object: RepoBreaker) -> Dict[str, Any]:
    return {}
  
  @classmethod
  def insert(cls, t: RepoBreaker) -> int:
    return 100

class BrokenRepo(Repo[RepoBreaker]):
  query = BrokenQuery
  cache = MagicMock()

class GoodType:
  def __init__(self, id: int):
    self.id = id

class GoodQuery(Query[GoodType]):
  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> GoodType:
    return GoodType(5)
  
  @classmethod
  def pack(cls, object: GoodType) -> Dict[str, Any]:
    return {}
    
  @classmethod
  def update(cls, id: int, t: GoodType) -> None:
    pass

class GoodRepo(Repo[GoodType]):
  query = GoodQuery
  cache = MagicMock()

def test_repo_insert_attribute_error_coverage():
  breaker = RepoBreaker()
  BrokenRepo.insert(breaker)
  
  BrokenRepo.cache.put.assert_called_with(breaker)

def test_update_existing_id():
  goodie = GoodType(id=1)
  GoodRepo.update(goodie)
  
  GoodRepo.cache.put.assert_called_with(goodie)

def test_team_repo_update_team_not_found():
  mock_team = MagicMock()
  mock_team.id = 999
  
  with patch('src.app.db.repos.TeamRepo.get', return_value=None):
    TeamRepo.update(mock_team, "correct answer")

def test_repo_get_cache_hit():
  with patch.object(TeamRepo.cache, 'get') as mock_cache_get:
    with patch.object(TeamRepo.query, 'get') as mock_query_get:
      expected_obj = MagicMock()
      mock_cache_get.return_value = expected_obj
      
      result = TeamRepo.get(999)
      
      assert result == expected_obj
      mock_cache_get.assert_called_once_with(999)
      mock_query_get.assert_not_called()

def test_team_repo_update_full_coverage():
  mock_team = MagicMock()
  mock_team.id = 123
  
  with patch('src.app.db.repos.TeamRepo.get', return_value=mock_team):
    with patch('src.app.db.repos.TeamRepo.query') as mock_query:
      with patch('src.app.db.repos.TeamRepo.cache') as mock_cache:
        
        TeamRepo.update(mock_team, "correct answer")
        
        mock_query.update.assert_called_once_with(123, mock_team)
        mock_cache.put.assert_called_once_with(mock_team)
