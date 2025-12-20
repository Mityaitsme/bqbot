from ..core import Message
from ..db import MemberRepo, TeamRepo
from ..services.registration import RegistrationService
from ..core import QuestEngine
from ..core import AdminService
from ...config import ADMIN


class Router:
  """
  Routes messages to appropriate services depending on context.
  """

  @classmethod
  def route(cls, msg: Message) -> Message:
    """
    Routes messages to appropriate services depending on context.
    """
    user_id = msg.user_id
    text = msg.text.strip()

    # 1. Admin commands
    if cls._is_admin(user_id):
      reply = cls._route_admin(msg)

    # 2. Registration
    elif MemberRepo.get(user_id) is None:
      reply = RegistrationService.handle_input(user_id, text)

    # 3. Regular player
    else:
      reply = cls._route_player(msg)

    if reply.user_id is None:
      reply.user_id = user_id
    
    return reply

  @staticmethod
  def _is_admin(user_id: int) -> bool:
    """
    Checks if the user is an admin.
    """
    return user_id == ADMIN

  @classmethod
  def _route_admin(cls, msg: Message) -> Message:
    """
    Routes admin messages to appropriate services.
    """
    text = msg.text.lower()

    # TODO: put admin commands somewhere out of code
    if text == "/info_all":
      return AdminService.get_all_teams_info()

    if text.startswith("/info "):
      team_name = text.split(" ")[1]
      return AdminService.get_team_info(team_name)

    if text == "/scoring_system":
      return AdminService.get_scoring_system()

    return Message(
      _user_id=msg.user_id,
      _text="Неизвестная админ-команда",
    )

  @classmethod
  def _route_player(cls, msg: Message) -> Message:
    """
    Routes player messages to appropriate services.
    """
    text = msg.text.lower()
    user = MemberRepo.get(msg.user_id)
    team_id = user.team_id
    team = TeamRepo.get(team_id)
    if team.cur_member_id != msg.user_id:
      team.cur_member_id = msg.user_id
      TeamRepo.update(team, event="member switched")
    if text == "/riddle":
      return QuestEngine.get_riddle(team_id)

    # otherwise - handling answer
    return QuestEngine.check_answer(team_id, msg)
