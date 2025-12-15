"""
Database query classes for interacting with database tables.
Query is an abstract base class that defines the interface for all query classes.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, TypeVar, Generic
from ..core import Team, Member, Riddle
from .db_conn import DB
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Query(ABC, Generic[T]):
  """
  Generic base class for database queries.
  Defines the common interface for querying and manipulating database records.
  Child classes specify the type parameter to get proper type hints.
  """

  # set the name of the table with required data
  table_name = ""

  @classmethod
  def get(cls, id: int) -> T | None:
    """
    Gets an object via its ID.
    This implementation will be shared by all child classes.
    """
    t = cls.parse(DB.select(table=cls.table_name, where={"id": id}, column="*"))
    return t
  
  @classmethod
  def put(cls, t: T) -> None:
    """
    Adds a new object to the database.
    Access class-specific table_name via: cls.table_name
    """
    t_str = cls.pack(t)
    if not cls.get(t.id):
      DB.insert(table=cls.table_name, values=[t_str])
    else:
      DB.update(table=cls.table_name, id=t.id, value=t_str)
    return

  @abstractmethod
  @classmethod
  def parse(cls, raw_data: str) -> T:
    """
    Parses raw database data into an object with appropriate type.
    Is an abstract method, should be implemented in all child classes.
    """
    pass
  
  @abstractmethod
  @classmethod
  def pack(cls, object: T) -> str:
    """
    Packs an object into a string that can be later used by the appropriate database.
    Is an abstract method, should be implemented in all child classes.
    """
    pass


class TeamQuery(Query[Team]):
  """
  Query class for Team database operations.
  Inherits all methods from Query with Team type hints.
  """

  # TODO: replace it with an actual table name
  table_name = "team"

  @classmethod
  def get_by_member(cls, member_id: int) -> Team | None:
    """
    Get a team by member ID.
    """
    from .repos import MemberRepo
    # If anything crashes, mind the circular import: it might be the problem
    member = MemberRepo.get(member_id)
    if member is None:
      return None
    team_id = member.team.id
    if team_id is None:
      return None
    return cls.get(team_id)

  @classmethod
  def get_all(cls) -> List[Team]:
    """
    Gets all teams from the database.
    """
    request = f"SELECT * FROM {cls.table_name}"
    raw_data = DB.select(table=cls.table_name, column="*")
    raw_data_list = []
    # TODO: parse the str containing info about all teams to a list where each line
    # can be parsed via standart parse method
    teams = []
    for raw_t in raw_data_list:
      t = cls.parse(raw_t)
      teams.append(t)
    return teams
  
  @classmethod
  def update(cls, id: int, event: str) -> None:
    """
    Function that updates team's state in database after some event.
    The only event available for now is "correct answer", this may change in later versions
    """
    if event != "correct answer":
      return
    
    team = cls.get(id)
    if not team:
      logger.warning(f"Incorrect team for TeamQuery to update (id {id}).")
      return
    team.next_stage()
    cls.put(team)
    logger.info(f"Successfully updated team with id {id} in the database.")
    return

  @classmethod
  def parse(cls, raw_data: str) -> Team:
    """
    Parses a raw database row (str) into a Team object.
    """
    # TODO: specify when database format is better known
    return

  @classmethod
  def pack(cls, team: Team) -> str:
    """
    Packs a Team object into a string suitable for database insertion.
    """
    # TODO: specify when database format is better known
    return


class MemberQuery(Query[Member]):
  """
  Query class for Member database operations.
  Inherits all methods from Query with Member type hints.
  """

  # TODO: replace it with an actual table name
  table_name = "member"

  @classmethod
  def parse(cls, raw_data: str) -> Member:
    """
    Parses a raw database row (str) into a Member object.
    """
    # TODO: specify when database format is better known
    return

  @classmethod
  def pack(cls, member: Member) -> str:
    """
    Packs a Member object into a string suitable for database insertion.
    """
    # TODO: specify when database format is better known
    return


class RiddleQuery(Query[Riddle]):
  """
  Query class for Riddle database operations.
  Inherits all methods from Query with Riddle type hints.
  """

  # TODO: replace it with an actual table name
  table_name = "riddle"

  @classmethod
  def parse(cls, raw_data: str) -> Riddle:
    """
    Parses a raw database row (str) into a Riddle object.
    """
    # TODO: specify when database format is better known
    return

  @classmethod
  def pack(cls, riddle: Riddle) -> str:
    """
    Packs a Riddle object into a dict suitable for database insertion.
    """
    # TODO: specify when database format is better known
    return
