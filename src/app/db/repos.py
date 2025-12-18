"""
Repository classes for accessing database objects with caching.
Repo classes check cache first, then query database, and store results in cache.

Repo is an abstract base class that defines the interface for all repository classes.
Child classes specify the type parameter via Generic[T] and provide cache and query classes.
"""

from __future__ import annotations
from abc import ABC
from typing import TypeVar, Generic, Optional, List, Literal
import logging

from ..core import Team, Member, Riddle
from .cache import TeamCache, MemberCache, RiddleCache
from .queries import TeamQuery, MemberQuery, RiddleQuery
from .db_conn import DB

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
  def insert(cls, obj: T) -> int:
    """
    Inserts a new object.
    Returns the new ID.
    Updates the object's ID if it was None (for Teams).
    """
    new_id = cls.query.insert(obj)
    
    if hasattr(obj, "_id"): 
      try:
        object.__setattr__(obj, "_id", new_id)
      except AttributeError:
        pass
             
    cls.cache.put(obj)
    logger.debug(f"Inserted and cached {cls.__name__} object with id={new_id}")
    return new_id
  
  @classmethod
  def update(cls, obj: T) -> None:
    """
    ONLY UPDATES an existing object.
    Object MUST have an ID.
    """
    if not obj.id:
      logger.error(f"Cannot update object without ID: {obj}")
      raise ValueError("Cannot update object without ID")

    cls.query.update(obj.id, obj)
    cls.cache.put(obj)
    logger.debug(f"Updated and cached {cls.__name__} object with id={obj.id}")
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
    """
    # MemberRepo is defined in this same file, so no import needed
    member = MemberRepo.get(member_id)
    if member is None:
      return None

    return cls.get(member.team_id)

  @classmethod
  def get_by_name(cls, name: str) -> Optional[Team]:
    """
    Gets a team by its name.
    """
    rows = cls.query.get_by_name(name)
    if not rows:
      return None
    team = rows[0]
    cls.cache.put(team)
    return team

  @classmethod
  def get_all(cls) -> List[Team]:
    """
    Gets all teams from the database as Team objects.
    """
    teams = cls.query.get_all()
    return teams

  @classmethod
  def update(cls, team: Team, event: str) -> None:
    """
    Updates a team in the database and cache.
    """
    # TODO: change the way of validating event (later)
    if event not in {"correct answer", "member switched"}:
      logger.warning(f"Incorrect update event for TeamRepo ({event}).")
      return

    team_db = cls.get(team.id)
    if team_db is None:
      logger.warning(f"No team with id {team.id} found in TeamRepo.")
      return

    super().update(team)
    logger.debug(f"Updated and cached Team object with id={team.id}, event: {event}")


class MemberRepo(Repo[Member]):
  """
  Repository for Member objects.
  Inherits all methods from Repo with Member, MemberCache, and MemberQuery types.
  """

  cache = MemberCache
  query = MemberQuery

  @classmethod
  def get_by_team(cls, team_id: int) -> List[Member]:
    rows = DB.select(table=cls.query.table_name, where={"team_id": team_id})
    return [cls.query.parse(row) for row in rows]


class RiddleRepo(Repo[Riddle]):
  """
  Repository for Riddle objects.
  Inherits all methods from Repo with Riddle, RiddleCache, and RiddleQuery types.
  """

  cache = RiddleCache
  query = RiddleQuery