"""
Admin-facing utilities: overview, leaderboard and team inspection.

AdminService is intentionally simple: it queries TeamRepo (and optionally
RiddleRepo) and formats Message objects that can be sent to admins.
"""

from __future__ import annotations
from .basic_classes import Message
from ..db import TeamRepo


class AdminService:
  """
  This class resolves the pipeline where admin wants something from the bot.
  It creates a message that transport layer can send back to administrators or to participants.
  """

  @staticmethod
  def get_team_info(team_id: int) -> Message:
    from ..db import TeamRepo, MemberRepo
    members = MemberRepo.get_by_team(team.id)
    team = TeamRepo.get(team_id)
    member_names = [m.tg_nickname for m in members]
    if not team:
      raise TeamNotFound(f"Team {team_id} not found")

    text = (
    f"Team {team.name} (id={team.id})\n"
    f"Stage: {team.cur_stage}\n"
    f"Score: {team.score}\n"
    f"Members: {', '.join(member_names)}\n"
    f"Last call time: {team.call_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    # TODO: ADMIN поменять на его id через .env
    reply = Message(text=text)
    reply.recipient_id = ADMIN
    return reply

  @staticmethod
  def get_all_teams_info() -> Message:
    teams = TeamRepo.get_all()
    if not teams or len(teams) == 0:
      reply = Message(text="No teams registered yet")
      reply.recipient_id = ADMIN
      return reply

    lines = []
    for team in teams:
      lines.append(f"{team.id}: {team.name} - stage {team.cur_stage} - score {team.score}")
    text = "All teams:\n" + "\n".join(lines)
    reply = Message(text=text)
    reply.recipient_id = ADMIN
    return reply

  @staticmethod
  def get_scoring_system() -> Message:
    # This will become more complex in further versions; but for now the hints and easter eggs are not available.
    text = (
      "Scoring system:\n"
      "- Each correct riddle: +1 stage\n"
    )
    reply = Message(text=text)
    reply.recipient_id = ADMIN
    return reply
