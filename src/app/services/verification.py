from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import List

from ..core import Message, QuestEngine
from ..db import TeamRepo
from ...config import ADMIN

class VerificationStep(Enum):
  """
  Enumeration of verification steps.
  """
  ASK_ADMIN = auto()
  ASK_FEEDBACK = auto()
  DONE = auto()

@dataclass
class VerificationContext:
  """
  Holds the state of a riddle verification process.
  """
  user_id: int
  msg: Message
  step: VerificationStep
  verdict: bool | None = None
  feedback: bool | None = None
  feedback_msg: Message | None = None

class VerificationService:
  """
  Handles riddle verification flow.
  Stateless in logic, state is stored externally (DB or memory).
  """

  _contexts: dict[int, VerificationContext] = {}

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
    Checks if user's answer is currently in verification process.
    """
    return id in cls._contexts

  @classmethod
  def handle_input(cls, msg: Message) -> Message | List[Message]:
    """
    Handles user input according to current verification step.
    """
    if msg.user_id != ADMIN:
      return cls._send_to_admin(msg)
    
    text = msg.text
    team = TeamRepo.get_by_name(text.split(" ")[1])
    ctx = cls._load_context(team.cur_member_id)

    if ctx.step == VerificationStep.ASK_ADMIN:
      return cls._handle_verdict(ctx, msg)

    if ctx.step == VerificationStep.ASK_FEEDBACK:
      return cls._handle_feedback(ctx, msg)

    raise RuntimeError(f"Unexpected verification step: {ctx.step}")

  @classmethod
  def _save_context(cls, ctx: VerificationContext) -> None:
    """
    Saves or updates the verification context for a user.
    """
    cls._contexts[ctx.user_id] = ctx

  @classmethod
  def _load_context(cls, user_id: int) -> VerificationContext:
    """
    Loads the verification context for a user.
    Raises RuntimeError if no context exists.
    """
    try:
      return cls._contexts[user_id]
    except KeyError:
      return None

  @classmethod
  def _send_to_admin(cls, msg0: Message) -> List[Message]:
    """
    Forwards team's answer to admin.
    """
    ctx = VerificationContext(
      user_id=msg0.user_id,
      step=VerificationStep.ASK_ADMIN,
      msg=msg0,
    )
    cls._save_context(ctx)
    team = TeamRepo.get_by_member(msg0.user_id)
    msg1 = msg0.copy()
    msg1.recipient_id = ADMIN
    msg2 = Message(_text=f"Принять ответ команды {team.name}?\nОтвечай в формате\n" \
                   "/verification [название команды] [да/нет] [да/нет]\n" \
                   ", где первое - верный ли ответ, второе - будет ли фидбек.",
                   _recipient_id = ADMIN)
    msg = [msg1, msg2]
    return msg

  @classmethod
  def _handle_verdict(cls, ctx: VerificationContext, msg: Message) -> Message | List[Message]:
    """
    Handles the admin's verdict on team's answer.
    """
    text = msg.text
    verdict = text.split(" ")[2].lower()
    feedback = text.split(" ")[3].lower()
    team = TeamRepo.get_by_member(ctx.user_id)

    if verdict == "да":
      ctx.verdict = True
    elif verdict == "нет":
      ctx.verdict = False
    else:
      return Message(_text=f"Пожалуйста, укажите вердикт по ответу {team.name}.")
    
    if feedback == "да":
      ctx.feedback = True
    elif feedback == "нет":
      ctx.feedback = False
    else:
      return Message(_text=f"Пожалуйста, укажите, будет ли фидбек по ответу {team.name}.")

    if ctx.feedback:
      ctx.step = VerificationStep.ASK_FEEDBACK
      cls._save_context(ctx)
      return Message(_text=f"Пожалуйста, укажите фидбек по ответу {team.name}..\n"\
                    "Отвечай в формате\n" \
                    "/verification [название команды] [фидбек].\n",
                    _recipient_id=ADMIN)
    
    ctx.step = VerificationStep.DONE
    cls._contexts.pop(ctx.user_id, None)
    if ctx.verdict:
      return QuestEngine.correct_answer_pipeline(team)
    return QuestEngine.wrong_answer_pipeline(team)
    

  @classmethod
  def _handle_feedback(cls, ctx: VerificationContext, msg0: Message) -> Message | List[Message]:
    """
    Handles admin feedback on the team answer.
    """
    ctx.step = VerificationStep.DONE
    verdict = ctx.verdict
    msg1 = msg0.copy()
    msg1.recipient_id = ctx.user_id
    msg1._text = " ".join(msg1.text.split(" ")[2:])
    team = TeamRepo.get_by_member(ctx.user_id)
    cls._contexts.pop(ctx.user_id, None)
    msg2 = Message(_text=f"Фидбек отправлен команде {team.name}.", _recipient_id=ADMIN)
    msg = [msg1, msg2]
    if verdict:
      return msg + QuestEngine.correct_answer_pipeline(team)
    return msg + QuestEngine.wrong_answer_pipeline(team)
