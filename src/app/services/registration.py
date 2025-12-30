from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Literal

from ..core import Message, Team, Member
from ..db import TeamRepo, MemberRepo, RiddleRepo
from ..utils import Utils

class RegistrationStep(Enum):
  """
  Enumeration of registration steps.
  """
  ASK_ROLE = auto()
  ASK_TEAM_NAME = auto()
  CONFIRM_TEAM_NAME = auto()
  ASK_PASSWORD = auto()
  ASK_PASSWORD_REPEAT = auto()
  DONE = auto()

@dataclass
class RegistrationContext:
  """
  Holds the state of a user's registration process.
  """
  user_id: int
  step: RegistrationStep
  mode: Literal["join", "create"] | None = None
  team_name: str | None = None
  password_hash: str | None = None

class RegistrationService:
  """
  Handles user registration flow.
  Stateless in logic, state is stored externally (DB or memory).
  """

  _contexts: dict[int, RegistrationContext] = {}

  @classmethod
  def _start(cls, user_id: int) -> Message:
    """
    Initiates registration for a user.
    """
    if MemberRepo.get(user_id):
      return Message(_text="Вы уже зарегистрированы!")

    ctx = RegistrationContext(
      user_id=user_id,
      step=RegistrationStep.ASK_ROLE,
    )
    cls._save_context(ctx)
    return cls._ask_role_message()
  
  @classmethod
  def _clear_contexts(cls) -> None:
    """
    Deletes everything from the local _contexts dictionary.
    """
    cls._contexts.clear()
    return

  @classmethod
  def is_active(cls, id: int) -> bool:
    """
    Checks if a user is currently in registration process.
    """
    return id in cls._contexts

  @classmethod
  def handle_input(cls, user_id: int, text: str) -> Message:
    """
    Handles user input according to current registration step.
    """
    ctx = cls._load_context(user_id)

    if ctx is None:
      return cls._start(user_id)

    if ctx.step == RegistrationStep.ASK_ROLE:
      return cls._handle_role(ctx, text)

    if ctx.step == RegistrationStep.ASK_TEAM_NAME:
      return cls._handle_team_name(ctx, text)

    if ctx.step == RegistrationStep.CONFIRM_TEAM_NAME:
      return cls._handle_team_name_confirm(ctx, text)

    if ctx.step == RegistrationStep.ASK_PASSWORD:
      return cls._handle_password(ctx, text)

    if ctx.step == RegistrationStep.ASK_PASSWORD_REPEAT:
      return cls._handle_password_repeat(ctx, text)

    raise RuntimeError(f"Unexpected registration step: {ctx.step}")

  @classmethod
  def _save_context(cls, ctx: RegistrationContext) -> None:
    """
    Saves or updates the registration context for a user.
    """
    cls._contexts[ctx.user_id] = ctx

  @classmethod
  def _load_context(cls, user_id: int) -> RegistrationContext:
    """
    Loads the registration context for a user.
    Raises RuntimeError if no context exists.
    """
    try:
      return cls._contexts[user_id]
    except KeyError:
      return None

  @classmethod
  def _ask_role_message(cls) -> List[Message]:
    """
    Returns the initial message asking user to choose between joining or creating a team.
    """
    msg1 = Message(_text=
      "Привет, игрок!\n\n"
      "Небольшая методичка по пользованию ботом:\n"
      "Бот умеет принимать на вход сообщения с текстом, фото, видео, файлами, "
      "а также кружочки, голосовые сообщения и стикеры. Остальные сообщения он, к сожалению, "
      "не распознает, так что не стоит пытаться их отправлять.\n"
      "/riddle - попросить условие загадки.\n\n"
      "И давай сразу приступать к игре!"
    )
    msg2 = Message(_text=
      "Вы хотите:\n"
      "1) Присоединиться к существующей команде\n"
      "2) Зарегистрировать новую команду\n\n"
      "Ответь: 1 или 2."
    )
    return [msg1, msg2]

  @classmethod
  def _handle_role(cls, ctx: RegistrationContext, text: str) -> Message:
    """
    Handles if the user wants to register or join a team.
    """

    if text == "1":
      ctx.mode = "join"
    elif text == "2":
      ctx.mode = "create"
    else:
      return Message(_text="Пожалуйста, ответьте 1 или 2")

    ctx.step = RegistrationStep.ASK_TEAM_NAME
    cls._save_context(ctx)
    return Message(_text="Введите имя команды:")

  @classmethod
  def _handle_team_name(cls, ctx: RegistrationContext, text: str) -> Message:
    """
    Handles team name input and validation.
    """
    team_name = text.strip()

    if ctx.mode == "join":
      team = TeamRepo.get_by_name(team_name)
      if not team:
        return Message(_text="Команда с таким именем не найдена. Попробуйте ещё раз:")
      ctx.team_name = team_name
      ctx.step = RegistrationStep.ASK_PASSWORD
      cls._save_context(ctx)
      return Message(_text="Введите пароль:")

    team = TeamRepo.get_by_name(team_name)
    if team is not None:
      return Message(_text="К сожалению, это имя уже занято. Попробуйте какое-нибудь другое.")
    ctx.team_name = team_name
    ctx.step = RegistrationStep.CONFIRM_TEAM_NAME
    cls._save_context(ctx)
    # herringbone quotation because otherwise the line would be split in two
    return Message(_text=f"Подтвердите имя команды «{team_name}»? (да / нет)")

  @classmethod
  def _handle_team_name_confirm(cls, ctx: RegistrationContext, text: str) -> Message:
    """
    Handles confirmation of team name.
    """
    if text.lower() not in ("да", "нет"):
      return Message(_text="Ответьте «да» или «нет»")

    if text.lower() == "нет":
      ctx.step = RegistrationStep.ASK_TEAM_NAME
      cls._save_context(ctx)
      return Message(_text="Тогда введитете имя команды ещё раз, пожалуйста:")

    ctx.step = RegistrationStep.ASK_PASSWORD
    cls._save_context(ctx)
    return Message(_text="Введите пароль:")

  @classmethod
  def _handle_password(cls, ctx: RegistrationContext, text: str) -> List[Message]:
    """
    Handles password input.
    """

    if ctx.mode == "join":
      team = TeamRepo.get_by_name(ctx.team_name)

      if not team.verify_password(text):
        return Message(_text="Неверный пароль. Попробуйте ещё раз:")

      cls._create_member(ctx, team)
      ctx.step = RegistrationStep.DONE
      cls._contexts.pop(ctx.user_id, None)
      msg1 = Message(_text=f"Вы успешно вошли в команду {ctx.team_name}!")
      cur_riddle = RiddleRepo.get(team.cur_stage)
      return [msg1] + cur_riddle.messages

    ctx.password_hash = Utils.hash(text)
    ctx.step = RegistrationStep.ASK_PASSWORD_REPEAT
    cls._save_context(ctx)
    return Message(_text="Повторите пароль:")

  @classmethod
  def _handle_password_repeat(cls, ctx: RegistrationContext, text: str) -> List[Message]:
    """
    Handles password confirmation.
    """
    if not Utils.verify_password(text, ctx.password_hash):
      return Message(_text="Пароли не совпадают. Введите пароль ещё раз:")

    team = cls._create_team(ctx)
    cls._create_member(ctx, team)

    ctx.step = RegistrationStep.DONE
    cls._contexts.pop(ctx.user_id, None)
    msg1 = Message(_text=f"Команда {team.name} успешно зарегистрирована!")
    cur_riddle = RiddleRepo.get(team.cur_stage)
    return [msg1] + cur_riddle.messages

  @classmethod
  def _create_team(cls, ctx: RegistrationContext) -> Team:
    """
    Creates a new team in DB and cache.
    """
    team = Team(
      _id=None,  # autoincrement
      _name=ctx.team_name,
      _Team__password_hash=ctx.password_hash,
      _cur_member_id=ctx.user_id
    )
    team._id = TeamRepo.insert(team)
    TeamRepo.update(team, event="added id")
    return team

  @classmethod
  def _create_member(cls, ctx: RegistrationContext, team: Team) -> Member:
    """
    Creates new member in DB and cache.
    """
    # TODO: insert real name and nickname in later versions
    member = Member(
      id=ctx.user_id,
      tg_nickname="",
      name="",
      team_id=team.id,
    )
    MemberRepo.insert(member)
    return member
