"""
Basic classes used by the quest engine.
Contains dataclasses Team, Member, Message and Riddle.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


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


# TODO: @generate_properties()
@dataclass(slots=True)
class Message:
  """
  Telegram message converted into the format the bot core understands.
  Includes all nessessary information (author, their team, recipient, text, files, other data)
  Variable `type` shows if this message contains photos&videos, voice messages, other files or just text.
  """
  _text: str
  _author_id: Optional[int] = None
  _recipient_id: Optional[int] = None
  _files: List[FileExtension] = field(default_factory=list)
  _background_info: Dict[str, str] = field(default_factory=dict)
  _created_at: datetime = field(
    default_factory=lambda: datetime.now(timezone(timedelta(hours=3)))
  )

  @recipient_id.setter
  def recipient_id(self, id: int):
    self._recipient_id = id
    return

  @property
  def type(self) -> str:
    if not self.files or len(self.files) == 0:
      return "text"
    extensions = [f.extension for f in self.files]
    if all(ext in (".mp3", ".wav") for ext in extensions):
      return "voice"
    elif all(ext in (".jpg", ".jpeg", ".png", ".mp4") for ext in extensions):
      return "gallery"
    else:
      return "other"
  
  @classmethod
  def from_riddle(cls, riddle: Riddle) -> Message:
    text = riddle.question
    files = riddle.files
    # TODO: background info maybe
    created_at = Utils.now()
    return Message(_text=text, _files=files, _created_at=created_at)


@dataclass(frozen=True, slots=True)
class Riddle:
  """
  Immutable riddle definition.
  `type` describes if the answer should be checked in the db or in some other way (will be added in later versions).
  For now, this field is useless.
  """
  id: int
  question: str
  files: List[FileExtension] = field(default_factory=list)
  answer: str
  type: str = "db"

  def check_answer(self, message: Message) -> bool:
    """
    Checks whether given message is a correct answer.
    For text riddles we just compare normalized strings.
    Expect `verification` and other types of riddles in later versions of this bot.
    """
    if self.type == "db":
      expected = self.answer
      got = message.text()
      return expected == got
    
    # a plug if the team has finished the quest and shouldn't be moved anywhere
    elif self.type == "finale":
      return False 
    # OTHER OPTIONS IN LATER VERSIONS
    return


# TODO: @generate_properties(exclude={"_password_hash"})
@dataclass(slots=True)
class Team:
  """
  Represents a team participating in the quest.
  Actively uses @property for limited access.
  """
  _id: int
  _name: str
  __password_hash: str
  _start_stage: int = 0
  _cur_stage: int = 0
  _score: int = 0
  _cur_member_id: int
  _call_time: datetime = field(
    default_factory=lambda: datetime.now(timezone(timedelta(hours=3)))
  )
  _members: List[Member] = field(default_factory=list)

  def verify_password(self, password: str) -> bool:
    """
    Password verification. Hash is created via function from Utils.
    Then we just compare hash string directly.
    """
    # password = hash(password)
    return self._Team__password_hash == password
  
  @cur_member_id.setter
  def cur_member_id(self, value):
    self._cur_member_id = value
    return

  def next_stage(self) -> None:
    """Advance to next stage and adjust score if needed."""
    self.cur_stage += 1
    # TODO: put stage_count to config
    if self.cur_stage > STAGE_COUNT:
      self.cur_stage = 1
    self.score += 1
    self._call_time = Utils.now()
    # TODO: update call_time

  def add_member(self, member: Member) -> None:
    if any(m.id == member.id for m in self.members):
      return
    self.members.append(member)
    self.cur_member_id = member.id
