from ..core.quest_engine import QuestEngine
from ..core.admin_service import AdminService
from ..core.models import Message
from ..services.registration import RegistrationService
from ..db import MemberRepo




class Router:
  """
  Routes Message to appropriate domain service.
  """


  @staticmethod
  def route(msg: Message) -> str:
    # Registration flow has priority
    if not MemberRepo.get_by_tg_id(msg.user_id):
      if RegistrationService.is_active(msg.user_id):
        return RegistrationService.handle_input(msg.user_id, msg.text)
      return RegistrationService.start(msg.user_id)
    # Admin logic
    if AdminService.is_admin(msg.user_id):
      return AdminService.handle(msg)


    # Main quest logic
    return QuestEngine.handle(msg)