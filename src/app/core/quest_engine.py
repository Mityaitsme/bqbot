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
  def get_riddle(team_id: int) -> Message | List[Message]:
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
    # TODO: fix when riddles will be made from several files
    return Message.from_riddle(riddle)

  @staticmethod
  def check_answer(team_id: int, message: Message) -> Message | List[Message]:
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
      return QuestEngine.correct_answer_pipeline(team)
      
    # if the answer is incorrect
    return QuestEngine.wrong_answer_pipeline(team)
  
  @staticmethod
  def correct_answer_pipeline(team: Team) -> List[Message]:
    team.next_stage()
    TeamRepo.update(team, event="correct answer")
    # TODO: first send the "correct!" message, then the riddle
    reply1 = Message(
      _text="Ответ верный! Переходим на следующий этап."
    )
    reply1.recipient_id = team.cur_member_id
    new_riddle = RiddleRepo.get(team.cur_stage)
    reply2 = Message.from_riddle(new_riddle)
    reply2.recipient_id = team.cur_member_id
    reply = [reply1, reply2]
    return reply
  
  @staticmethod
  def wrong_answer_pipeline(team: Team) -> List[Message]:
    reply = Message(
      _text="Неправильно — попробуйте ещё раз."
    )
    reply.recipient_id = team.cur_member_id
    return [reply]
