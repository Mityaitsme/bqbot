import pytest
from unittest.mock import MagicMock, patch
from src.app.db.cache import LRUCache, TeamCache, MemberCache, RiddleCache
from collections import OrderedDict
from src.app.core import Team


# ----- BASE LRU CACHE -----

def test_cache_get():
  with patch.object(LRUCache, '_cache', OrderedDict([(1, "a")])):
    result = LRUCache.get(1)
    assert result == "a"


def test_cache_get_missing():
  with patch.object(LRUCache, '_cache', OrderedDict()):
    result = LRUCache.get(999)
    assert result is None


def test_cache_put_new():
  mock_obj = MagicMock()
  mock_obj.id = 1
  
  with patch.object(LRUCache, '_cache', OrderedDict()) as mock_cache:
    with patch.object(LRUCache, '_cache_size', 2):
      LRUCache.put(mock_obj)
      
      assert 1 in mock_cache
      assert mock_cache[1] == mock_obj


def test_cache_put_update():
  mock_obj = MagicMock()
  mock_obj.id = 1
  
  with patch.object(LRUCache, '_cache', OrderedDict([(1, "old")])) as mock_cache:
    with patch.object(LRUCache, '_cache_size', 2):
      LRUCache.put(mock_obj)
      
      assert mock_cache[1] == mock_obj
      assert len(mock_cache) == 1


def test_cache_put_eviction():
  mock_obj1 = MagicMock()
  mock_obj1.id = 1
  mock_obj2 = MagicMock()
  mock_obj2.id = 2
  mock_obj3 = MagicMock()
  mock_obj3.id = 3
  
  with patch.object(LRUCache, '_cache', OrderedDict()) as mock_cache:
    with patch.object(LRUCache, '_cache_size', 2):
      LRUCache.put(mock_obj1)
      LRUCache.put(mock_obj2)
      LRUCache.put(mock_obj3)
      
      assert 1 not in mock_cache
      assert 2 in mock_cache
      assert 3 in mock_cache


# ----- LRU EVICTION LOGIC -----

def test_cache_get_updates_order():
  mock_obj1 = MagicMock()
  mock_obj1.id = 1
  mock_obj2 = MagicMock()
  mock_obj2.id = 2
  mock_obj3 = MagicMock()
  mock_obj3.id = 3
  
  with patch.object(LRUCache, '_cache', OrderedDict()) as mock_cache:
    with patch.object(LRUCache, '_cache_size', 2):
      LRUCache.put(mock_obj1)
      LRUCache.put(mock_obj2)
      
      LRUCache.get(1)
      
      LRUCache.put(mock_obj3)
      
      assert 1 in mock_cache
      assert 2 not in mock_cache
      assert 3 in mock_cache


# ----- CHILD CLASSES -----

def test_team_cache_put():
  mock_team = MagicMock()
  mock_team.id = 1
  
  with patch.object(TeamCache, '_cache', OrderedDict()) as mock_cache:
    with patch.object(TeamCache, '_cache_size', 50):
      TeamCache.put(mock_team)
      
      assert 1 in mock_cache
      assert mock_cache[1] == mock_team


def test_member_cache_get():
  mock_member = MagicMock()
  mock_member.id = 5
  
  with patch.object(MemberCache, '_cache', OrderedDict([(5, mock_member)])):
    result = MemberCache.get(5)
    
    assert result == mock_member


def test_riddle_cache_eviction():
  mock_riddle1 = MagicMock()
  mock_riddle1.id = 1
  mock_riddle2 = MagicMock()
  mock_riddle2.id = 2
  mock_riddle3 = MagicMock()
  mock_riddle3.id = 3
  
  with patch.object(RiddleCache, '_cache', OrderedDict()) as mock_cache:
    with patch.object(RiddleCache, '_cache_size', 2):
      RiddleCache.put(mock_riddle1)
      RiddleCache.put(mock_riddle2)
      RiddleCache.put(mock_riddle3)
      
      assert 1 not in mock_cache
      assert len(mock_cache) == 2


# ----- BOUNDARY CASES -----

def test_cache_put_no_id():
  mock_obj = MagicMock()
  mock_obj.id = None
  
  with patch.object(LRUCache, '_cache', OrderedDict()) as mock_cache:
    LRUCache.put(mock_obj)
    
    assert len(mock_cache) == 0


def test_cache_multiple_same_id():
  mock_obj = MagicMock()
  mock_obj.id = 1
  
  with patch.object(LRUCache, '_cache', OrderedDict()) as mock_cache:
    with patch.object(LRUCache, '_cache_size', 2):
      LRUCache.put(mock_obj)
      LRUCache.put(mock_obj)
      LRUCache.put(mock_obj)
      
      assert len(mock_cache) == 1


def test_cache_put_existing_updates_and_moves_to_end():
  class TestCache(LRUCache[Team]):
    _cache_size = 3
  
  mock_obj1 = MagicMock()
  mock_obj1.id = 1
  mock_obj2 = MagicMock()
  mock_obj2.id = 2
  TestCache.put(mock_obj1)
  TestCache.put(mock_obj2)
  assert list(TestCache.cache().keys()) == [1, 2]
  
  mock_obj1_new = MagicMock()
  mock_obj1_new.id = 1
  mock_obj1_new.name = "Updated"  
  TestCache.put(mock_obj1_new)
  keys = list(TestCache.cache().keys())
  assert keys == [2, 1]
  assert TestCache.get(1).name == "Updated"