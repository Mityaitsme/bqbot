"""
Basic classes used by the quest engine.
Contains dataclasses Team, Member, Message and Riddle.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from aiogram import Bot

from ..utils import Utils, Timer
from ...config import STAGE_COUNT
from enum import Enum


class FileType(str, Enum):
  PHOTO = "photo"
  VIDEO = "video"
  VIDEO_NOTE = "video_note"
  AUDIO = "audio"
  DOCUMENT = "document"
  STICKER = "sticker"


@dataclass(frozen=True, slots=True)
class FileExtension:
  """
  Represents a file attached to a riddle or message.
  """

  type: FileType
  creator_id: int
  filename: str | None = None
  filedata: Any | None = None
  team_id: int | None = None
  creation_time: int = field(
    default_factory=lambda: datetime.now(timezone(timedelta(hours=3)))
  )
  additional_data: str = ""


@dataclass(frozen=True)
class Member:
  """
  Telegram participant in a team.
  Immutable dataclass.
  """
  id: int
  tg_nickname: str
  name: str
  team_id: int


@Utils.generate_properties()
@dataclass(slots=True)
class Message:
  """
  Telegram message converted into the format the bot core understands.
  Includes all nessessary information (author, their team, recipient, text, files, other data)
  Variable `type` shows if this message contains photos&videos, voice messages, other files or just text.
  """
  _text: str
  _user_id: Optional[int] = None
  _recipient_id: Optional[int] = None
  _bot: Optional[Bot] = None
  _files: List[FileExtension] = field(default_factory=list)
  _background_info: Dict[str, str] = field(default_factory=dict)
  _created_at: datetime = field(
    default_factory=lambda: datetime.now(timezone(timedelta(hours=3)))
  )

  @property
  def recipient_id(self):
    return self._recipient_id

  @recipient_id.setter
  def recipient_id(self, id: int):
    self._recipient_id = id
    return
  
  @property
  def user_id(self):
    return self._user_id

  @user_id.setter
  def user_id(self, id: int):
    self._user_id = id
    return
  
  def copy(self) -> Message:
    return Message(
      _text=self.text,
      _user_id=self.user_id,
      _recipient_id=self.recipient_id,
      _bot=self.bot,
      _files=self.files,
      _background_info=self.background_info,
      _created_at=self.created_at
    )
  
  @classmethod
  def from_riddle(cls, riddle: Riddle) -> Message:
    """
    Creates a Message instance from a Riddle instance.
    """
    text = riddle.question
    files = riddle.files
    # TODO: background info maybe
    created_at = Timer.now()
    return Message(_text=text, _files=files, _created_at=created_at)


@dataclass(slots=True, frozen=True)
class Riddle:
  """
  Immutable riddle definition.
  `type` describes if the answer should be checked in the db or in some other way (will be added in later versions).
  For now, this field is useless.
  """
  id: int
  question: str
  answer: str
  files: List[FileExtension] = field(default_factory=list)
  type: str = "db"

  def verification_type(self):
    if self.type == "verification":
      return True
    return False

  def check_answer(self, message: Message) -> bool:
    """
    Checks whether given message is a correct answer.
    For text riddles we just compare normalized strings.
    Expect `verification` and other types of riddles in later versions of this bot.
    """
    if self.type == "db":
      expected = Utils.normalize(self.answer)
      got = Utils.normalize(message.text)
      return expected == got
    
    # a plug if the team has finished the quest and shouldn't be moved anywhere
    elif self.type == "finale":
      return False 
    # OTHER OPTIONS IN LATER VERSIONS
    return


@Utils.generate_properties()
@dataclass(slots=True)
class Team:
  """
  Represents a team participating in the quest.
  Actively uses @property for limited access.
  """
  _id: int | None
  _name: str
  _cur_member_id: int
  __password_hash: str
  _start_stage: int = 1
  _cur_stage: int = 1
  _score: int = 0
  _stage_call_time: datetime = field(
    default_factory=lambda: datetime.now(timezone(timedelta(hours=3)))
  )

  def verify_password(self, password: str) -> bool:
    """
    Password verification. Hash is created via function from Utils.
    Then we just compare hash string directly.
    """
    return Utils.verify_password(password, self._Team__password_hash)
  
  @property
  def cur_member_id(self):
    return self._cur_member_id

  @cur_member_id.setter
  def cur_member_id(self, value: int):
    self._cur_member_id = value
    return

  def next_stage(self) -> None:
    """Advance to next stage and adjust score if needed."""
    self._cur_stage += 1
    if self.cur_stage > STAGE_COUNT:
      self._cur_stage = 1
    self._score += 1
    self._stage_call_time = Timer.now()
