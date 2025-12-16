"""
Repository classes for accessing database objects with caching.
Repo classes check cache first, then query database, and store results in cache.

Repo is an abstract base class that defines the interface for all repository classes.
Child classes specify the type parameter via Generic[T] and provide cache and query classes.
"""

from __future__ import annotations
from abc import ABC
from typing import TypeVar, Generic, Optional, List
import logging

from ..core import Team, Member, Riddle
from .cache import TeamCache, MemberCache, RiddleCache
from .queries import TeamQuery, MemberQuery, RiddleQuery, Query

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Repo(ABC, Generic[T]):
  """
  Generic base class for database repositories with caching.
  
  Repositories combine cache and query functionality:
  - First check cache for objects
  - If not found, query database via Query class
  - Store results in cache for future access
  
  Child classes specify the entity type (Team, Member, Riddle)
  """

  # Specifying cache and query classes
  cache = None
  query = None

  @classmethod
  def get(cls, id: int) -> Optional[T]:
    """
    Gets an object by its ID.
    First checks cache, then queries database if not found, then stores in cache.
    """
    # Check cache first
    cached_obj = cls.cache.get(id)
    if cached_obj is not None:
      logger.debug(f"Cache hit for {cls.__name__}.get({id})")
      return cached_obj
    
    # Not in cache, query database
    logger.debug(f"Cache miss for {cls.__name__}.get({id}), querying database")
    obj = cls.query.get(id)
    
    if obj is not None:
      # Store in cache for future access
      cls.cache.put(obj)
      logger.debug(f"Found in database and cached {cls.__name__} object with id={id}")
    else:
      logger.debug(f"No T {T} object with id={id} in database.")
    
    return obj

  @classmethod
  def put(cls, obj: T) -> None:
    """
    Adds a new object to both database and cache.
    """
    cls.query.put(obj)
    cls.cache.put(obj)
    logger.debug(f"Added and cached {cls.__name__} object")
    return


class TeamRepo(Repo[Team]):
  """
  Repository for Team objects.
  Inherits all methods from Repo with Team, TeamCache, and TeamQuery types.
  """

  cache = TeamCache
  query = TeamQuery

  @classmethod
  def get_by_member(cls, member_id: int) -> Optional[Team]:
    """
    Gets a team by member ID.
    First checks if member's team is cached, otherwise queries database.
    """
    # MemberRepo is defined in this same file, so no import needed
    member = MemberRepo.get(member_id)
    if member is None:
      return None

    return cls.get(member.team.id)

  @classmethod
  def get_all(cls) -> List[Team]:
    """
    Gets all teams from the database as Team objects.
    Caches all teams as they are loaded.
    
    Returns:
      List of Team objects
    """
    teams = cls.query.get_all()
    return teams

  @classmethod
  def update(cls, team: Team, event: str) -> None:
    """
    Updates a team in the database and cache.
    The only event available right now is "correct answer", but other options may be added later
    """
    
    if event != "correct answer":
      logger.warning(f"Incorrect update event for TeamRepo ({event}).")
      return

    team1 = cls.get(team.id)
    if team1 is None:
      logger.warning(f"No team with id {id} found in TeamRepo.")
      return
    team.next_stage()
    cls.put(team)
    logger.debug(f"Updated and cached Team object with id={team.id}, event: {event}")


class MemberRepo(Repo[Member]):
  """
  Repository for Member objects.
  Inherits all methods from Repo with Member, MemberCache, and MemberQuery types.
  """

  cache = MemberCache
  query = MemberQuery


class RiddleRepo(Repo[Riddle]):
  """
  Repository for Riddle objects.
  Inherits all methods from Repo with Riddle, RiddleCache, and RiddleQuery types.
  """

  cache = RiddleCache
  query = RiddleQuery