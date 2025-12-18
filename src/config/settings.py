from dotenv import load_dotenv
import os

# loading environment variables from a .env file
load_dotenv()

# Telegram
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN: int = int(os.getenv("ADMIN_ID", "0"))

# Database
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Other
STAGE_COUNT: int = 17
CACHE_SIZE: int = 50
TEAM_CACHE_SIZE: int = 50
RIDDLE_CACHE_SIZE: int = 50
MEMBER_CACHE_SIZE: int = 100
TEAM_TABLE_NAME: str = "team"
MEMBER_TABLE_NAME: str = "member"
RIDDLE_TABLE_NAME: str = "riddle"
START_TIME: int = int(os.getenv("START_TIME", "1701369600"))
