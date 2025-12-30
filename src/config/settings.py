from dotenv import load_dotenv
import os

# loading environment variables from a .env file
load_dotenv()

# Telegram
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT = int(os.getenv("ADMIN_CHAT"))
admins = os.getenv("ADMIN", "")
ADMIN = [
    int(x.strip()) 
    for x in admins.split(",") 
    if x.strip().isdigit()
]

# Database
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
CACHE_SIZE: int = 50
TEAM_CACHE_SIZE: int = 50
RIDDLE_CACHE_SIZE: int = 50
MEMBER_CACHE_SIZE: int = 100
TEAM_TABLE_NAME: str = "team"
MEMBER_TABLE_NAME: str = "member"
RIDDLE_TABLE_NAME: str = "riddle"
RIDDLE_MESSAGE_TABLE_NAME: str = "riddle_message"
RIDDLE_FILE_TABLE_NAME: str = "riddle_file"

# Other
STAGE_COUNT: int = 17
START_TIME: int = 1701369600
STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "C:/Users/HP/bqbot/storage")
AUTO_UPLOAD: bool = True
