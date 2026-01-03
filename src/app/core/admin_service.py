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
    Sorted by:
    1. Score (DESC - highest first)
    2. Time of arrival (ASC - earliest first)
    """
    teams = TeamRepo.get_all()
    if not teams or len(teams) == 0:
      reply = Message(_text="Пока что ни одна команда не зарегистрировалась.")
      reply.recipient_id = ADMIN_CHAT
      return reply
    teams.sort(key=lambda t: (-t.score, t.stage_call_time))

    max_name_len = max((len(t.name) for t in teams), default=4)
    name_width = min(max_name_len, 15)

    # {rank:^2} centered
    # {name:^W} centered
    # {score:^5} centered
    # {stage:^5} centered
    # {time:^17} centered
    row_fmt = f"{{rank:^2}} | {{name:^{name_width}}} | {{score:^5}} | {{stage:^5}} | {{time:^17}}"

    lines = []
    
    # header
    header = row_fmt.format(rank="#", name="Team", score="Score", stage="Stage", time="Arrived at")
    lines.append(header)
    # separator
    lines.append("-" * len(header))

    # data
    for i, team in enumerate(teams, 1):
      # cut if it's too long
      display_name = team.name
      if len(display_name) > name_width:
          display_name = display_name[:name_width-1] + "…"
      
      time_str = team.stage_call_time.strftime("%H:%M:%S %D")
      
      lines.append(row_fmt.format(
          rank=i, 
          name=display_name,
          score=team.score,
          stage=team.cur_stage,
          time=time_str
      ))

    # all to one markdown code block
    table_text = "🏆 Leaderboard:" + "<pre>" + "\n".join(lines) + "</pre>"
    reply = Message(_text=table_text)
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
  
  @staticmethod
  def get_help() -> Message:
    """
    Returns a manual for admins which contains all commands available for admins.
    """
    text = (
      "Available commands:\n"
      "/help - returns admin manual with all existing commands;\n"
      "/info [team_name] - returns all data about the chosen team;\n"
      "/info_all - gets general data anout all team sorted by score;\n"
      "/cancel - restart verification (in case of making mistakes);\n"
      "/scoring_system - gets info about the scoring system."
    )
    reply = Message(_text=text)
    reply.recipient_id = ADMIN_CHAT
    return reply
