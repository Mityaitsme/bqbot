"""
The core of this bot.

This package contains dataclasses that describe main entities (Team, Member,
Message, Riddle) and the core services: QuestEngine (processing user's message)
and AdminService (processing admin's message).
"""
# TODO: ADD SOMETHING ABOUT DEPENDENCIES INTO DESCRIPTION

from .basic_classes import Member, Message, Riddle, Team
from .quest_engine import QuestEngine
from .admin_service import AdminService

__all__ = [
  "Member",
  "Message",
  "Riddle",
  "Team",
  "QuestEngine"
  "AdminService"
]
