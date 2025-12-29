"""
Database query classes for interacting with database tables.
Query is an abstract base class that defines the interface for all query classes.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, TypeVar, Generic, Any
from datetime import datetime, timezone, timedelta
from ..core import Team, Member, Riddle, Message, FileExtension, FileType
from ..storage import EXTENSION_TO_FILETYPE, download_riddle_file
from .db_conn import DB
import logging
from ...config import TEAM_TABLE_NAME, MEMBER_TABLE_NAME, RIDDLE_TABLE_NAME
from ...config import ADMIN, RIDDLE_MESSAGE_TABLE_NAME, RIDDLE_FILE_TABLE_NAME

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Query(ABC, Generic[T]):
  """
  Generic base class for database queries.
  Defines the common interface for querying and manipulating database records.
  Child classes specify the type parameter to get proper type hints.
  """

  # set the name of the table
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
  def insert(cls, t: T) -> int:
    """
    Strict INSERT. Returns the new ID.
    """
    data = cls.pack(t)
    return DB.insert(table=cls.table_name, values=data)
  
  @classmethod
  def update(cls, id: int, t: T) -> None:
    """
    Strict UPDATE.
    """
    data = cls.pack(t)
    DB.update(table=cls.table_name, id=id, values=data)
    return

  @classmethod
  @abstractmethod
  def parse(cls, raw_data: Dict[str, Any]) -> T:
    """
    Parses raw database data into an object with appropriate type.
    Is an abstract method, should be implemented in all child classes.
    """
    pass
  
  @classmethod
  @abstractmethod
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

  table_name = TEAM_TABLE_NAME

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
    # parsing time to datetime format
    stage_call_time_str = raw_data["stage_call_time"]
    if isinstance(stage_call_time_str, datetime):
      stage_call_time = stage_call_time_str
    else:
      try:
        # ISO
        stage_call_time = datetime.fromisoformat(stage_call_time_str)
      except:
        try:
          stage_call_time = datetime.fromtimestamp(float(stage_call_time_str))
        except:
          stage_call_time = datetime.now(timezone(timedelta(hours=3)))
          logger.error(f"Failed to parse time for team {raw_data["name"]}.")

    return Team(
      _id=raw_data["id"],
      _name=raw_data["name"],
      _Team__password_hash=raw_data["password_hash"],
      _start_stage=raw_data["start_stage"],
      _cur_stage=raw_data["cur_stage"],
      _score=raw_data["score"],
      _stage_call_time=stage_call_time,
      _cur_member_id=raw_data.get("cur_member_id"),
    )

  @classmethod
  def pack(cls, team: Team) -> Dict[str, Any]:
    """
    Packs a Team object into a dictionary suitable for database insertion.
    """
    # packing datetime to time
    if isinstance(team.stage_call_time, datetime):
        stage_call_time_str = team.stage_call_time.isoformat()
    else:
        stage_call_time_str = str(team.stage_call_time)

    return {
      "id": team.id,
      "name": team.name,
      "password_hash": team._Team__password_hash,
      "start_stage": team.start_stage,
      "cur_stage": team.cur_stage,
      "score": team.score,
      "cur_member_id": team.cur_member_id,
      "stage_call_time": stage_call_time_str,
    }
  
  @classmethod
  def get_by_name(cls, name: str) -> List[Team]:
    """
    Gets a team by its name.
    """
    rows = DB.select(
      table=cls.table_name,
      where={"name": name}
    )
    return [cls.parse(row) for row in rows]



class MemberQuery(Query[Member]):
  """
  Query class for Member database operations.
  Inherits all methods from Query with Member type hints.
  """

  table_name = MEMBER_TABLE_NAME

  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> Member:
    """
    Parses a raw database row (dict) into a Member object.
    """
    return Member(
    id=raw_data["id"],
    tg_nickname=raw_data["tg_nickname"],
    name=raw_data["name"],
    team_id=raw_data["team_id"]
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
      "team_id": member.team_id,
    }


class RiddleFileQuery(Query[FileExtension]):
  """
  Query class for riddle_file table.
  """

  table_name = RIDDLE_FILE_TABLE_NAME

  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> FileExtension:
    # redundant functionality, works incorrectly, shall never be used!!
    filename = raw_data["filename"]
    ext = filename.rsplit(".", 1)[-1].lower()
    file_type = EXTENSION_TO_FILETYPE.get(ext, FileType.DOCUMENT)

    return FileExtension(
      type=file_type,
      creator_id=ADMIN,
      filename=filename,
      filedata=None
    )
  
  @classmethod
  def parse_with_riddle_id(cls, raw_data: Dict[str, Any], riddle_id: int) -> FileExtension:
    filename = raw_data["filename"]
    file = download_riddle_file(riddle_id, filename)

    return file

  @classmethod
  def pack(cls, file: FileExtension) -> Dict[str, Any]:
    # redundant functionality, never to be used
    return {
      "filename": file.filename,
      "message_id": -1,
    }

  @classmethod
  def get_by_message(cls, message_id: int, riddle_id: int) -> List[FileExtension]:
    rows = DB.select(
      table=cls.table_name,
      where={"message_id": message_id}
    )
    return [cls.parse_with_riddle_id(row, riddle_id) for row in rows]


class RiddleMessageQuery(Query[Message]):
  """
  Query class for riddle_message table.
  """

  table_name = RIDDLE_MESSAGE_TABLE_NAME

  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> Message:
    # redundant functionality, works incorrectly, shall never be used!!
    message_id = raw_data["id"]
    files = RiddleFileQuery.get_by_message(message_id, -1)

    return Message(
      _text=raw_data["text"],
      _files=files
    )
  
  @classmethod
  def parse_with_riddle_id(cls, raw_data: Dict[str, Any], riddle_id: int) -> Message:
    message_id = raw_data["id"]
    files = RiddleFileQuery.get_by_message(message_id, riddle_id)

    return Message(
      _text=raw_data["text"],
      _files=files
    )

  @classmethod
  def pack(cls, message: Message) -> Dict[str, Any]:
    # redundant functionality, never to be used
    return {
      "text": message.text,
      "riddle_id": -1
    }

  @classmethod
  def get_by_riddle(cls, riddle_id: int) -> List[Message]:
    rows = DB.select(
      table=cls.table_name,
      where={"riddle_id": riddle_id}
    )
    return [cls.parse_with_riddle_id(row, riddle_id) for row in rows]


class RiddleQuery(Query[Riddle]):
  """
  Query class for Riddle database operations.
  Inherits all methods from Query with Riddle type hints.
  """

  table_name = RIDDLE_TABLE_NAME

  @classmethod
  def parse(cls, raw_data: Dict[str, Any]) -> Riddle:
    """
    Parses a raw database row (dict) into a Riddle object.
    """
    riddle_id = raw_data["id"]
    messages = RiddleMessageQuery.get_by_riddle(riddle_id)

    return Riddle(
      id=riddle_id,
      messages=messages,
      answer=raw_data["answer"],
      type=raw_data["type"]
    )

  @classmethod
  def pack(cls, riddle: Riddle) -> Dict[str, Any]:
    """
    Packs a Riddle object into a dictionary suitable for database insertion.
    """
    return {
      "id": riddle.id,
      "answer": riddle.answer,
      "type": riddle.type,
    }
