import asyncio
from logging.config import dictConfig

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from .app.bot import tg_router
from .config import BOT_TOKEN


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

# [ADD] Функция-заглушка, чтобы Render думал, что это сайт
async def health_check(request):
  return web.Response(text="Bot is alive!")

async def start_dummy_server():
  app = web.Application()
  app.add_routes([web.get('/', health_check)])
  runner = web.AppRunner(app)
  await runner.setup()
  # Render передает порт через переменную окружения PORT
  port = int(os.environ.get("PORT", 8080)) 
  site = web.TCPSite(runner, '0.0.0.0', port)
  await site.start()

def setup_logging() -> None:
  dictConfig(LOGGING_CONFIG)


async def main() -> None:
  """
  Main entry point of the application.
  Sets up logging, initializes the bot and dispatcher, and starts polling.
  """
  setup_logging()

  bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
  dp = Dispatcher()

  dp.include_router(tg_router)

  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
