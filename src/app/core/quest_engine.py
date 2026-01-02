"""
QuestEngine - core business logic for handling riddles and team progress.
"""

from __future__ import annotations
from typing import List
from .basic_classes import Message, Team
from ..db import TeamRepo, RiddleRepo
import logging
from ..exceptions import TeamError, RiddleError, AnswerError

logger = logging.getLogger(__name__)


class QuestEngine:
  """
  Core engine which coordinates reading team state, validating answers and
  mutating team progress.

  Although it does all the main stuff, it is kept lightweight because it delegates
  everything to other services.
  """
  @staticmethod
  def get_riddle(team_id: int) -> List[Message]:
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
    messages = [msg.copy() for msg in riddle.messages] 
    for msg in messages:
        msg.recipient_id = team.cur_member_id # Теперь меняем только в своей локальной копии
    return messages

  @staticmethod
  def get_binary_answer(team_id: int, message: Message, verdict: bool | None = None) -> List[Message]:
    """
    Checks if the provided answer is correct via database
    """
    team = TeamRepo.get(team_id)
    if team is None:
      logger.exception("Error while checking answer: team %s not found", team_id)
      raise TeamError(f"Team {team_id} not found")

    riddle = RiddleRepo.get(team.cur_stage)
    if riddle is None:
      logger.exception("Error while checking answer: riddle %s not found", team.cur_stage)
      raise RiddleError(f"Riddle for stage {team.cur_stage} not found")

    correct = False
    try:
      if verdict is not None:
        correct = verdict
      else:
        correct = riddle.check_answer(message)
    except Exception as exc:  # defensive: riddle check should not crash engine
      logger.exception("Error while checking answer: failed to validate answer: %s", exc)
      raise AnswerError("Failed to validate answer")

    if correct:
      # extracted verdicts for this quests
      reply1 = Message(
        _text="Верно!"
      )
      reply1.recipient_id = team.cur_member_id
      return QuestEngine.correct_answer_pipeline(team)
      
    # if the answer is incorrect
    # extracted verdicts for this quests
    reply = Message(
      _text="Неверно - попробуй ещё раз..."
    )
    reply.recipient_id = team.cur_member_id
    return [reply]
  
  @staticmethod
  def correct_answer_pipeline(team: Team) -> List[Message]:
    team.next_stage()
    TeamRepo.update(team, event="correct answer")
    # "next stage..." message if required
    new_riddle = RiddleRepo.get(team.cur_stage)
    messages = [msg.copy() for msg in new_riddle.messages] 
    for msg in messages:
        msg.recipient_id = team.cur_member_id # Теперь меняем только в своей локальной копии
    return messages
  
  @staticmethod
  def wrong_answer_pipeline(team: Team) -> List[Message]:
    # TODO: penalty points in later versions
    return []
