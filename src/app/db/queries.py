"""
Database query classes for interacting with database tables.
Query is an abstract base class that defines the interface for all query classes.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, TypeVar, Generic, Any
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
    rows = DB.select(table=cls.table_name, where={"id": id})
    if not rows:
      return None
    return cls.parse(rows[0])
  
  @classmethod
  def put(cls, t: T) -> None:
    """
    Adds a new object to the database.
    Access class-specific table_name via: cls.table_name
    """
    data = cls.pack(t)
    if cls.get(t.id) is None:
      DB.insert(table=cls.table_name, values=data)
    else:
      DB.update(table=cls.table_name, id=t.id, values=data)
    return

  @abstractmethod
  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> T:
    """
    Parses raw database data into an object with appropriate type.
    Is an abstract method, should be implemented in all child classes.
    """
    pass
  
  @abstractmethod
  @classmethod
  def pack(cls, object: T) -> Dict[str, Any]:
    """
    Packs an object into a dictionary that can be later used by the appropriate database.
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
  def get_all(cls) -> List[Team]:
    """
    Gets all teams from the database.
    """
    rows = DB.select(table=cls.table_name)
    teams = []
    for row in rows:
      try:
        teams.append(cls.parse(row))
      except Exception as e:
        logger.error(f"Failed to parse team row {row}: {e}")

    return teams

  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> Team:
    """
    Parses a raw database row (dict) into a Team object.
    """
    return Team(
      _id=raw_data["id"],
      _name=raw_data["name"],
      _password_hash=raw_data["password_hash"],
      _start_stage=raw_data["start_stage"],
      _cur_stage=raw_data["cur_stage"],
      _score=raw_data["score"],
      _call_time=raw_data["call_time"],
      _cur_member_id=raw_data.get("cur_member_id"),
    )

  @classmethod
  def pack(cls, team: Team) -> Dict[str, Any]:
    """
    Packs a Team object into a dictionary suitable for database insertion.
    """
    return {
      "id": team.id,
      "name": team.name,
      "password_hash": team.password_hash,
      "start_stage": team.start_stage,
      "cur_stage": team.cur_stage,
      "score": team.score,
      "cur_member_id": team.cur_member_id,
      "call_time": team.call_time,
    }


class MemberQuery(Query[Member]):
  """
  Query class for Member database operations.
  Inherits all methods from Query with Member type hints.
  """

  # TODO: replace it with an actual table name
  table_name = "member"

  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> Member:
    """
    Parses a raw database row (dict) into a Member object.
    """
    return Member(
    id=raw_data["id"],
    tg_nickname=raw_data["tg_nickname"],
    name=raw_data["name"],
    team_id=raw_data["team_id"],  # ← только ID
  )

  @classmethod
  def pack(cls, member: Member) -> Dict[str, Any]:
    """
    Packs a Member object into a dictionary suitable for database insertion.
    """
    return {
      "id": member.id,
      "tg_nickname": member.tg_nickname,
      "name": member.name,
      "team_id": member.team.id,
    }


class RiddleQuery(Query[Riddle]):
  """
  Query class for Riddle database operations.
  Inherits all methods from Query with Riddle type hints.
  """

  # TODO: replace it with an actual table name
  table_name = "riddle"

  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> Riddle:
    """
    Parses a raw database row (dict) into a Riddle object.
    """
    # TODO: a more complex way to parse question into several messages & files in later versions
    return Riddle(
      id=raw_data["id"],
      question=raw_data["question"],
      answer=raw_data["answer"],
      type=raw_data["type"],
      files=[],
    )

  @classmethod
  def pack(cls, riddle: Riddle) -> Dict[str, Any]:
    """
    Packs a Riddle object into a dictionary suitable for database insertion.
    """
    return {
      "id": riddle.id,
      "question": riddle.question,
      "answer": riddle.answer,
      "type": riddle.type,
    }
