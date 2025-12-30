from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from enum import Enum, auto
from dataclasses import dataclass
from typing import List

from ..core import Message, QuestEngine
from ..db import TeamRepo
from ...config import ADMIN, ADMIN_CHAT

import logging
logger = logging.getLogger(__name__)

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
  def _verdict_keyboard(cls, team_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
      [
        InlineKeyboardButton(text="✅ Да", callback_data=f"verification_verdict:{team_id}:yes:no"),
        InlineKeyboardButton(text="❌ Нет", callback_data=f"verification_verdict:{team_id}:no:no"),
      ],
      [
        InlineKeyboardButton(text="✅💬 Да + фидбек", callback_data=f"verification_verdict:{team_id}:yes:yes"),
        InlineKeyboardButton(text="❌💬 Нет + фидбек", callback_data=f"verification_verdict:{team_id}:no:yes"),
      ],
    ])

  @classmethod
  def handle_input(cls, msg: Message) -> Message | List[Message]:
    """
    Handles user input according to current verification step.
    """
    logger.info(f"HELLO THERE")
    if msg.user_id not in ADMIN:
      return cls._send_to_admin(msg)
    
    reply_text = msg.background_info.get("reply_text", None)
    logger.info(f"reply text: {reply_text}")
    if reply_text:
      team_name = reply_text.split("команде ")[1][:-1]
      logger.info(f"team name: {team_name}")
      team = TeamRepo.get_by_name(team_name)
    else:
      team = TeamRepo.get(msg.background_info["team_id"])
      logger.info(f"team name: {team.name}")
    ctx = cls._load_context(team.cur_member_id)

    if ctx.step == VerificationStep.ASK_ADMIN:
      return cls._handle_callback(ctx, msg)

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
    msg1.recipient_id = ADMIN_CHAT

    msg2 = Message(
      _text=f"Принять ответ команды {team.name}?",
      _recipient_id=ADMIN_CHAT,
      _reply_markup=cls._verdict_keyboard(team.id)
    )
    return [msg1, msg2]
  

  @classmethod
  def _handle_callback(cls, ctx: VerificationContext, msg: Message) -> Message | List[Message]:
    verdict_raw, feedback_raw = msg.background_info.get("other")
    team_id = msg.background_info.get("team_id")

    team = TeamRepo.get(team_id)

    if verdict_raw == "yes":
      ctx.verdict = True
    else:
      ctx.verdict = False
    if feedback_raw == "yes":
      ctx.feedback = True
    else:
      ctx.feedback = False

    if ctx.feedback:
      ctx.step = VerificationStep.ASK_FEEDBACK
      cls._save_context(ctx)

      return Message(
        _text=f"Ответьте на это сообщение, чтобы отправить фидбек команде {team.name}.",
        _recipient_id=ADMIN_CHAT,
      )

    cls._contexts.pop(ctx.user_id, None)

    return QuestEngine.get_binary_answer(team_id, msg, ctx.verdict)

  @classmethod
  def _handle_feedback(cls, ctx: VerificationContext, msg0: Message) -> List[Message]:
    """
    Handles admin feedback on the team answer.
    """
    # feedback comes via reply
    feedback_text = msg0.text

    msg_to_team = Message(
      _text=feedback_text,
      _recipient_id=ctx.user_id,
    )

    team = TeamRepo.get_by_member(ctx.user_id)
    verdict = ctx.verdict

    cls._contexts.pop(ctx.user_id, None)

    notify_admin = Message(
      _text=f"Фидбек отправлен команде {team.name}.",
      _recipient_id=ADMIN_CHAT,
    )

    if verdict:
      return [msg_to_team, notify_admin] + QuestEngine.correct_answer_pipeline(team)
    return [msg_to_team, notify_admin] + QuestEngine.wrong_answer_pipeline(team)
