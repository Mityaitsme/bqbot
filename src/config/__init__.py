"""
Settings package.
Imports all secret settings from .env and makes them available for other modules;
Also imports public settings.
"""

from .settings import *

__all__ = [
    "BOT_TOKEN",
    "ADMIN",
    "ADMIN_CHAT",
    "STAGE_COUNT",
    "DATABASE_URL",
    "START_TIME",
    "STORAGE_ROOT",
    "AUTO_UPLOAD",

    "CACHE_SIZE",
    "TEAM_CACHE_SIZE",
    "RIDDLE_CACHE_SIZE",
    "MEMBER_CACHE_SIZE",

    "TEAM_TABLE_NAME",
    "MEMBER_TABLE_NAME",
    "RIDDLE_TABLE_NAME",
    "RIDDLE_MESSAGE_TABLE_NAME",
    "RIDDLE_FILE_TABLE_NAME"
]