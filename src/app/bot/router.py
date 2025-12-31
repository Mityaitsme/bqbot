import random
from typing import List
from ..core import Message
from ..db import MemberRepo, TeamRepo, RiddleRepo
from ..services import RegistrationService, VerificationService, MazeService
from ..core import QuestEngine
from ..core import AdminService
from ...config import ADMIN, ADMIN_CHAT, CHARACTER_LINES
import logging
logger = logging.getLogger(__name__)

class Router:
  """
  Routes messages to appropriate services depending on context.
  """

  @classmethod
  def route(cls, msg: Message) -> List[Message]:
    """
    Routes messages to appropriate services depending on context.
    """
    user_id = msg.user_id

    # 1. Admin commands
    if cls._is_admin(user_id):
      reply = cls._route_admin(msg)

    # 2. Registration
    elif MemberRepo.get(user_id) is None:
      reply = RegistrationService.handle_input(msg)

    # 3. Regular player
    else:
      reply = cls._route_player(msg)

    if isinstance(reply, Message):
      reply = [reply]
    for message in reply:
      if message.recipient_id is None:
        message.recipient_id = user_id if user_id not in ADMIN else ADMIN_CHAT
    return reply

  @staticmethod
  def _is_admin(user_id: int) -> bool:
    """
    Checks if the user is an admin.
    """
    return user_id in ADMIN

  @classmethod
  def _route_admin(cls, msg: Message) -> Message | List[Message]:
    """
    Routes admin messages to appropriate services.
    """
    text = msg.text

    # TODO: put admin commands somewhere out of code
    if text.split("@")[0] == "/info_all":
      return AdminService.get_all_teams_info()

    if text.startswith("/info "):
      team_name = text.split(" ")[1]
      return AdminService.get_team_info(team_name)

    if text.split("@")[0] == "/scoring_system":
      return AdminService.get_scoring_system()
    
    if text.split("@")[0] == "/help":
      return AdminService.get_help()
    
    if msg.background_info.get("reply_text", None) or msg.background_info.get("type", None) == "verification_verdict":
      return VerificationService.handle_input(msg)

    return Message(
      _user_id=msg.user_id,
      _text="Неизвестная админ-команда.",
    )

  @classmethod
  def _route_player(cls, msg: Message) -> Message | List[Message]:
    """
    Routes player messages to appropriate services.
    """
    text = msg.text.lower()
    user = MemberRepo.get(msg.user_id)
    team_id = user.team_id
    team = TeamRepo.get(team_id)
    if team.cur_member_id != msg.user_id and msg.user_id not in ADMIN:
      team.cur_member_id = msg.user_id
      TeamRepo.update(team, event="member switched")
    if text == "/riddle":
      return QuestEngine.get_riddle(team_id)
    if text.lower() in CHARACTER_LINES.keys():
      lines = CHARACTER_LINES[text.lower()]
      i = random.randint(0, len(lines) - 1)
      return Message(_text=lines[i])
    riddle = RiddleRepo.get(team.cur_stage)
    if riddle.type == "verification":
      return VerificationService.handle_input(msg)
    if riddle.type == "maze":
      return MazeService.handle_input(msg)
    if riddle.type == "finale":
      return Message(
        _text="Ты прошел квест до конца, поздравляю!",
        _recipient_id=msg.user_id,
      )
    # otherwise - handling answer
    return QuestEngine.get_binary_answer(team_id, msg)
