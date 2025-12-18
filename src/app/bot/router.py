from ..core import Message
from ..db import MemberRepo, TeamRepo
from ..services.registration import RegistrationService
from ..core import QuestEngine
from ..core import AdminService


class Router:
  """
  Routes messages to appropriate services depending on context.
  """

  @classmethod
  def route(cls, msg: Message) -> Message:
    user_id = msg.user_id
    text = msg.text.strip()

    # 1. Admin commands
    if cls._is_admin(user_id):
      return cls._route_admin(msg)

    # 2. User is not registered
    member = MemberRepo.get(user_id)
    if member is None:
      return RegistrationService.start(user_id)

    # 3. Registration in progress
    if RegistrationService.is_active(user_id):
      return RegistrationService.handle_input(user_id, text)

    # 4. Regular player
    return cls._route_player(msg)

  @staticmethod
  def _is_admin(user_id: int) -> bool:
    # TODO: USE ADMIN ID FROM .env
    return user_id == ADMIN

  @classmethod
  def _route_admin(cls, msg: Message) -> Message:
    text = msg.text.lower()

    if text.startswith("/info"):
      team_name = int(text.split(" ")[1])
      team_id = TeamRepo.get_by_name(team_name)
      return AdminService.get_team_info(team_id)

    if text.startswith("/info_all"):
      return AdminService.get_all_teams_info()

    if text.startswith("/scoring_system"):
      return AdminService.get_scoring_system()

    return Message(
      user_id=msg.user_id,
      text="Неизвестная админ-команда",
    )

  @classmethod
  def _route_player(cls, msg: Message) -> Message:
    text = msg.text.lower()
    user = MemberRepo.get(msg.user_id)
    team_id = user.team_id
    if text == "/riddle":
      return QuestEngine.get_riddle(team_id)

    # otherwise - handling answer
    return QuestEngine.handle_answer(team_id, msg)
