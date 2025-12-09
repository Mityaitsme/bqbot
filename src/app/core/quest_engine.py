"""
QuestEngine - core business logic for handling riddles and team progress.
"""
# ДОБАВИТЬ ТЕКСТА

from __future__ import annotations
from .basic_classes import Message, Riddle

# @staticizer
class QuestEngine:
  """
  Core engine which coordinates reading team state, validating answers and
  mutating team progress.

  Although it does all the main stuff, it is kept lightweight because it delegates
  everything to other services.
  """

  def get_riddle(self, team_id: int) -> Riddle:
    """
    Return current riddle for team by reading its stage and fetching riddle.
    """
    team = TeamRepo.get(team_id)
    if team is None:
      raise TeamError(f"Team {team_id} not found")
    riddle = RiddleRepo.get(team.cur_stage)
    if riddle is None:
      raise RiddleError(f"Riddle for stage {team.cur_stage} not found")
    # cast message to riddle
    return Message.from_riddle(riddle)

  def check_answer(self, team_id: int, message: Message) -> Message:
    """
    Checks if the provided answer is correct
    """
    team = self._team_repo.get(team_id)
    if team is None:
      raise TeamNotFoundError(f"Team {team_id} not found")

    riddle = RiddleRepo.get(team.cur_stage)
    if riddle is None:
      raise RiddleNotFoundError(f"Riddle for stage {team.cur_stage} not found")

    try:
      correct = riddle.check_answer(message)
    except Exception as exc:  # defensive: riddle check should not crash engine
      raise InvalidAnswerError("Failed to validate answer") from exc

    if correct:
      team.next_stage()
      TeamRepo.update(team, event="answer_correct")
      reply = Message(
        text="Ответ верный! Переходим на следующий этап.",
        send_to_id=message.author
      )
      return reply

    # incorrect
    reply = Message(
      text="Неправильно — попробуйте ещё раз.",
      send_to_id=message.author
    )
    return reply