"""
LRU Cache implementation for caching database objects.
Uses OrderedDict to maintain insertion order and implement LRU eviction.
"""

from __future__ import annotations
from collections import OrderedDict
from typing import TypeVar, Generic, Optional

from ..core import Team, Member, Riddle
from config import CACHE_SIZE, TEAM_CACHE_SIZE, RIDDLE_CACHE_SIZE, MEMBER_CACHE_SIZE

T = TypeVar('T')


class LRUCache(Generic[T]):
  """
  Generic LRU (Least Recently Used) cache implementation.
  Automatically evicts least recently used items when cache is full.
  Child classes specify the type parameter to get proper type hints.
  
  This class uses class-level storage, so no instances are needed.
  Use classmethods to interact with the cache: TeamCache.get(id), TeamCache.put(id, obj)
  """

  # default cache size - can be overridden in child classes (hidden)
  _cache_size: int = CACHE_SIZE
  # cache itself (hidden)
  _cache: OrderedDict[int, T] = OrderedDict()

  # some hardcore stuff is actually going on down there, i'm so proud of myself
  def __init_subclass__(cls, **kwargs):
    """
    Initialize cache for each subclass.
    This ensures each child class has its own separate cache and cache size.
    """
    super().__init_subclass__(**kwargs)
    # Initialize cache for the class - each subclass gets its own OrderedDict
    setattr(cls, "_cache", OrderedDict())
    # Cache size is already set in child classes that override it
    # If not overridden, the parent's default will be used

  @classmethod
  def cache(cls) -> OrderedDict[int, T]:
    """
    Property-like getter for the cache dictionary.
    Use Classname.cache() to access the cache.
    """
    return cls._cache

  @classmethod
  def get(cls, id: int) -> Optional[T]:
    """
    Get an object from the cache by its ID.
    Moves the accessed item to the end (most recently used).
    """
    if id not in cls._cache:
      return None
    cls._cache.move_to_end(id)
    return cls._cache[id]

  @classmethod
  def put(cls, obj: T) -> None:
    """
    Put an object into the cache.
    If cache is full, removes the least recently used item (first item).
    If item already exists, updates it and moves to end.
    """
    id = obj.id
    if not id:
      return
    if id in cls._cache:
      cls._cache[id] = obj
      cls._cache.move_to_end(id)
      return
    if len(cls._cache) >= cls._cache_size:
      cls._cache.popitem(last=False)
    cls._cache[id] = obj
    return

class TeamCache(LRUCache[Team]):
  """
  LRU Cache for Team objects.
  Inherits all methods from LRUCache with Team type hints.
  """

  # Cache size for teams
  _cache_size: int = TEAM_CACHE_SIZE


class MemberCache(LRUCache[Member]):
  """
  LRU Cache for Member objects.
  Inherits all methods from LRUCache with Member type hints.
  """

  # Cache size for members
  _cache_size: int = MEMBER_CACHE_SIZE


class RiddleCache(LRUCache[Riddle]):
  """
  LRU Cache for Riddle objects.
  Inherits all methods from LRUCache with Riddle type hints.
  """

  # Cache size for riddles
  _cache_size: int = RIDDLE_CACHE_SIZE
