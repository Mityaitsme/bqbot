import asyncio
from logging.config import dictConfig

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from app.bot.handlers import tg_router


LOGGING_CONFIG = {
  "version": 1,
  "disable_existing_loggers": False,

  "formatters": {
    "default": {
      "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    },
  },

  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "formatter": "default",
    },
  },

  "root": {
    "level": "INFO",
    "handlers": ["console"],
  },
}


def setup_logging() -> None:
  dictConfig(LOGGING_CONFIG)


async def main() -> None:
  """
  Main entry point of the application.
  Sets up logging, initializes the bot and dispatcher, and starts polling.
  """
  setup_logging()

  bot = Bot(token=BOT_TOKEN)
  dp = Dispatcher()

  dp.include_router(tg_router)

  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
