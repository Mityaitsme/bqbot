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
  ASK_NAME = auto()
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
  player_name: str | None = None
  tg_nickname: str | None = None

class RegistrationService:
  """
  Handles user registration flow.
  Stateless in logic, state is stored externally (DB or memory).
  """

  _contexts: dict[int, RegistrationContext] = {}
  # [CHANGED] Добавлен set для временного хранения зарезервированных имен команд
  _reserved_names: set[str] = set()

  @classmethod
  def _start(cls, user_id: int, tg_nickname: str) -> Message | List[Message]:
    """
    Initiates registration for a user.
    """
    if MemberRepo.get(user_id):
      return Message(_text="Вы уже зарегистрированы!")

    ctx = RegistrationContext(
      user_id=user_id,
      step=RegistrationStep.ASK_ROLE,
      tg_nickname=tg_nickname
    )
    cls._save_context(ctx)
    msg1 = Message(
          _text="Привет! Добро пожаловать в игру.\n\n"
                "Сразу небольшая методичка по пользованию ботом:\n"
                "Бот умеет принимать на вход сообщения с текстом, фото, видео, файлами, "
                "а также кружочки, голосовые сообщения и стикеры. Остальные сообщения он, к сожалению, "
                "не распознает, так что не стоит пытаться их отправлять.\n"
                "/riddle - попросить условие загадки.\n"
                "/start - перезапустить регистрацию (если вы допустили ошибку при ней; работает "
                "только во время регистрации).\n"
                "/[имя персонажа] - поговорить с персонажем квеста (пример: /Санта).\n")
    msg2 = Message(
          _text = "Всё понятно? Тогда давай приступать к игре!\n"
                  "Ты хочешь <b><u>присоединиться к существующей команде (1)</u></b> или "
                  "<b><u>зарегистрировать новую команду (2)</u></b> ?\n"
                  "Ответь: 1 или 2."
          )
    return [msg1, msg2]
  
  @classmethod
  def _clear_contexts(cls) -> None:
    """
    Deletes everything from the local _contexts dictionary.
    """
    cls._contexts.clear()
    # [CHANGED] Очищаем также зарезервированные имена
    cls._reserved_names.clear()
    return

  @classmethod
  def is_active(cls, id: int) -> bool:
    """
    Checks if a user is currently in registration process.
    """
    return id in cls._contexts

  @classmethod
  def handle_input(cls, msg: Message) -> Message:
    """
    Handles user input according to current registration step.
    """
    text = msg.text
    user_id = msg.user_id
    ctx = cls._load_context(user_id)
    text = msg.text

    if ctx is None or text == '/start':
      if ctx:
        # [CHANGED] Если пользователь перезапускает регистрацию, нужно освободить занятое имя (если было)
        if ctx.mode == "create" and ctx.team_name in cls._reserved_names:
          cls._reserved_names.remove(ctx.team_name)
        cls._contexts.pop(ctx.user_id, None)
      tg_nickname = msg.background_info.get("tg_nickname")
      return cls._start(user_id, tg_nickname)

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
  def _handle_role(cls, ctx: RegistrationContext, text: str) -> Message:
    """
    Handles if the user wants to register or join a team.
    """

    if text == "1":
      ctx.mode = "join"
      ctx.step = RegistrationStep.ASK_TEAM_NAME
      cls._save_context(ctx)
      return Message(_text=
                    "Хорошо! Тогда введите имя команды, пожалуйста:"
                    )
    elif text == "2":
      ctx.mode = "create"
      ctx.step = RegistrationStep.ASK_TEAM_NAME
      cls._save_context(ctx)
      return Message(_text=
                    "Отлично!\nНовую команду нужно как-нибудь назвать. "
                    "Придумай ей какое-нибудь прикольное новогоднее имя, чтобы сразу всё "
                    "стало чуть более праздничным! Чем необычнее имя, тем веселее :)"
                    )

    return Message(_text="Пожалуйста, ответь 1 или 2")


  @classmethod
  def _handle_team_name(cls, ctx: RegistrationContext, text: str) -> Message:
    """
    Handles team name input and validation.
    """
    team_name = text.strip()

    if ctx.mode == "join":
      team = TeamRepo.get_by_name(team_name)
      if not team:
        return Message(_text="Команда с таким именем не найдена. Попробуй ещё раз:")
      ctx.team_name = team_name
      ctx.step = RegistrationStep.ASK_PASSWORD
      cls._save_context(ctx)
      return Message(_text="Введи пароль:")

    # [CHANGED] Проверка: занято ли имя уже в БД ИЛИ находится в процессе регистрации
    team = TeamRepo.get_by_name(team_name)
    if team is not None or team_name in cls._reserved_names:
      return Message(_text="К сожалению, это имя уже занято. Попробуй какое-нибудь другое.")
    
    # [CHANGED] Временно резервируем имя
    cls._reserved_names.add(team_name)
    ctx.team_name = team_name
    ctx.step = RegistrationStep.CONFIRM_TEAM_NAME
    cls._save_context(ctx)
    # herringbone quotation because otherwise the line would be split in two
    return Message(_text=f"Подтверди имя команды: «{team_name}»? (да / нет)")

  @classmethod
  def _handle_team_name_confirm(cls, ctx: RegistrationContext, text: str) -> Message:
    """
    Handles confirmation of team name.
    """
    if text.lower() not in ("да", "нет"):
      return Message(_text="Ответь «да» или «нет», пожалуйста")

    if text.lower() == "нет":
      # [CHANGED] Если пользователь отказался, удаляем имя из резерва
      if ctx.team_name in cls._reserved_names:
        cls._reserved_names.remove(ctx.team_name)
      ctx.team_name = None # Очищаем имя в контексте
      
      ctx.step = RegistrationStep.ASK_TEAM_NAME
      cls._save_context(ctx)
      return Message(_text="Тогда введи имя команды ещё раз, пожалуйста:")

    # Если "да" - имя остается в _reserved_names до конца регистрации
    ctx.step = RegistrationStep.ASK_PASSWORD
    cls._save_context(ctx)
    return Message(_text="Введи пароль:")

  @classmethod
  def _handle_password(cls, ctx: RegistrationContext, text: str) -> List[Message]:
    """
    Handles password input.
    """

    if ctx.mode == "join":
      team = TeamRepo.get_by_name(ctx.team_name)

      if not team.verify_password(text):
        return Message(_text="Неверный пароль. Попробуй ещё раз:")

      cls._create_member(ctx, team)
      ctx.step = RegistrationStep.DONE
      cls._contexts.pop(ctx.user_id, None)
      msg1 = Message(_text=f"Ты успешно вошел в команду {ctx.team_name}!")
      cur_riddle = RiddleRepo.get(team.cur_stage)
      return [msg1] + cur_riddle.messages

    ctx.password_hash = Utils.hash(text)
    ctx.step = RegistrationStep.ASK_PASSWORD_REPEAT
    cls._save_context(ctx)
    return Message(_text="Повтори пароль:")

  @classmethod
  def _handle_password_repeat(cls, ctx: RegistrationContext, text: str) -> List[Message]:
    """
    Handles password confirmation.
    """
    if not Utils.verify_password(text, ctx.password_hash):
      return Message(_text="Пароли не совпадают. Введи пароль ещё раз:")

    team = cls._create_team(ctx)
    cls._create_member(ctx, team)

    # [CHANGED] Регистрация успешна, удаляем имя из резерва (теперь оно есть в БД)
    if ctx.team_name in cls._reserved_names:
      cls._reserved_names.remove(ctx.team_name)

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
    member = Member(
      id=ctx.user_id,
      tg_nickname=ctx.tg_nickname,
      name=ctx.player_name,
      team_id=team.id,
    )
    MemberRepo.insert(member)
    return member
