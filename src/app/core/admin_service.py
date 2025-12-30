"""
Admin-facing utilities: overview, leaderboard and team inspection.

AdminService is intentionally simple: it queries TeamRepo (and optionally
RiddleRepo) and formats Message objects that can be sent to admins.
"""

from __future__ import annotations
from .basic_classes import Message
from ..db import TeamRepo, MemberRepo
from ...config import ADMIN_CHAT
from ..exceptions import TeamNotFound


class AdminService:
  """
  This class resolves the pipeline where admin wants something from the bot.
  It creates a message that transport layer can send back to administrators or to participants.
  """

  @staticmethod
  def get_team_info(team_name: str) -> Message:
    """
    Get detailed info about a specific team.
    Raises TeamNotFound if the team does not exist."""
    team = TeamRepo.get_by_name(team_name)
    if not team:
      raise TeamNotFound(f"Team {team_name} not found")

    members = MemberRepo.get_by_team(team.id)
    print(members)
    member_names = [m.tg_nickname for m in members]
    text = (
    f"Team {team.name} (id={team.id})\n"
    f"Stage: {team.cur_stage}\n"
    f"Score: {team.score}\n"
    f"Members: {', '.join(member_names)}\n"
    f"Last call time: {team.stage_call_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    reply = Message(_text=text)
    reply.recipient_id = ADMIN_CHAT
    return reply

  @staticmethod
  def get_all_teams_info() -> Message:
    """
    Get brief info about all registered teams.
    """
    teams = TeamRepo.get_all()
    if not teams or len(teams) == 0:
      reply = Message(_text="No teams registered yet")
      reply.recipient_id = ADMIN_CHAT
      return reply

    lines = []
    for team in teams:
      lines.append(f"{team.id}: {team.name} - stage {team.cur_stage} - score {team.score}")
    text = "All teams:\n" + "\n".join(lines)
    reply = Message(_text=text)
    reply.recipient_id = ADMIN_CHAT
    return reply

  @staticmethod
  def get_scoring_system() -> Message:
    """
    Gets the description of the scoring system.
    """
    # This will become more complex in further versions; but for now the hints and easter eggs are not available.
    text = (
      "Scoring system:\n"
      "- Each correct riddle: +1\n"
    )
    reply = Message(_text=text)
    reply.recipient_id = ADMIN_CHAT
    return reply
