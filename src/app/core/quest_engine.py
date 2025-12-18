"""
QuestEngine - core business logic for handling riddles and team progress.
"""

from __future__ import annotations
from .basic_classes import Message
from ..db import TeamRepo, RiddleRepo
import logging

logger = logging.getLogger(__name__)


class QuestEngine:
  """
  Core engine which coordinates reading team state, validating answers and
  mutating team progress.

  Although it does all the main stuff, it is kept lightweight because it delegates
  everything to other services.
  """
  @staticmethod
  def get_riddle(team_id: int) -> Message:
    """
    Return current riddle for team by reading its stage and fetching riddle.
    """
    team = TeamRepo.get(team_id)
    if team is None:
      logger.exception("Error while checking answer: team %s not found", team_id)
      raise TeamError(f"Team {team_id} not found")
    riddle = RiddleRepo.get(team.cur_stage)
    if riddle is None:
      logger.exception("Error while checking answer: riddle %s not found", team.cur_stage)
      raise RiddleError(f"Riddle for stage {team.cur_stage} not found")
    return Message.from_riddle(riddle)

  @staticmethod
  def check_answer(team_id: int, message: Message) -> Message:
    """
    Checks if the provided answer is correct
    """
    team = TeamRepo.get(team_id)
    if team is None:
      logger.exception("Error while checking answer: team %s not found", team_id)
      raise TeamError(f"Team {team_id} not found")

    riddle = RiddleRepo.get(team.cur_stage)
    if riddle is None:
      logger.exception("Error while checking answer: riddle %s not found", team.cur_stage)
      raise RiddleError(f"Riddle for stage {team.cur_stage} not found")

    try:
      correct = riddle.check_answer(message)
    except Exception as exc:  # defensive: riddle check should not crash engine
      logger.exception("Error while checking answer: failed to validate answer: %s", exc)
      raise AnswerError("Failed to validate answer")

    if correct:
      team.next_stage()
      TeamRepo.update(team, event="correct answer")
      reply = Message(
        text="Ответ верный! Переходим на следующий этап."
      )
      reply.recipient_id = message.author_id
      return reply

    # if the answer is incorrect
    reply = Message(
      text="Неправильно — попробуйте ещё раз."
    )
    reply.recipient_id = message.author_id
    return reply