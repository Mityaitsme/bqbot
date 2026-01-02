from dotenv import load_dotenv
import os

# loading environment variables from a .env file
load_dotenv()

# Telegram
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT = int(os.getenv("ADMIN_CHAT"))
TARGET_TOPIC_ID: int = 1
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

# Storage
#STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "C:/Users/HP/bqbot/storage")
AUTO_UPLOAD: bool = True
MAX_FILE_SIZE_MB: int = 20

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from supabase import create_client, Client

class SecureStorage:
  """
  Smart storage which replaces constant links with temporary signed ones.
  """
  def __init__(self, bucket_name: str = "quests"):
    self.bucket_name = bucket_name
    self._client: Optional[Client] = None

  @property
  def client(self) -> Client:
    """
    Lazy client initialisation.
    """
    if self._client is None:
      # Используем getenv с дефолтными значениями, чтобы код не падал при импорте,
      # но ругался при попытке использования, если переменных нет.
      url = os.getenv("SUPABASE_URL")
      key = os.getenv("SUPABASE_SERVICE_KEY") # service_role key нужен для обхода RLS или приватных бакетов

      if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")

      self._client = create_client(url, key)

    return self._client

  def _generate_signed_url(self, file_path: str) -> str:
    """
    Generates signed URLs. 
    CACHING DISABLED to prevent 400 Bad Request issues with expired/double-encoded tokens.
    """
    file_path = file_path.lstrip('/')
    
    # [FIX] УБИРАЕМ ПРОВЕРКУ КЭША
    # cache_key = f"{self.bucket_name}/{file_path}"
    # cached = self._signed_cache.get(cache_key)
    # if cached and cached["expires_at"] > datetime.now() + timedelta(seconds=10):
    #   return cached["url"]
    
    try:
      # Генерируем ссылку каждый раз заново
      response = self.client.storage \
          .from_(self.bucket_name) \
          .create_signed_url(file_path, 600) # Ссылка живет 10 минут
      
      if isinstance(response, dict) and "signedURL" in response:
          signed_url = response["signedURL"]
      elif isinstance(response, dict) and "error" in response:
          raise ValueError(f"Supabase error: {response['error']}")
      else:
          signed_url = response.get("signedURL") # type: ignore

      if not signed_url:
          raise ValueError(f"Empty signedURL received for {file_path}")
      
      # [FIX] НЕ СОХРАНЯЕМ В КЭШ, просто возвращаем
      return signed_url
        
    except Exception as e:
      print(f"[SecureStorage] Ошибка генерации ссылки для {file_path}: {e}")
      return ""

  def path(self, file_path: str) -> str:
    """
    Основной метод получения ссылки.
    Использование: STORAGE_ROOT.path("folder/image.jpg")
    """
    return self._generate_signed_url(file_path)

  def __call__(self, file_path: str) -> str:
    """
    Позволяет вызывать объект как функцию: STORAGE_ROOT("folder/image.jpg")
    """
    return self.path(file_path)
  
  # [NEW] Метод для совместимости с os.path.join (на всякий случай)
  def __str__(self):
    return f"SecureStorage(bucket='{self.bucket_name}')"

# Инициализация
STORAGE_ROOT = SecureStorage(bucket_name="ROOT_FOLDER")


# character lines
CHARACTER_LINES: dict = {
  "/санта": [
    "[Санта] Хо-хо-хо! С новым годом!",
    "[Санта] Какая прекрасная снежная погода за окном, как раз для меня!",
    "[Санта] Подарки, друзья и хорошее настроение – вот залог удачного праздника!"
  ],
  "/олень": [
    "[Рудольф] Простите, у вас случайно нет клевера со вкусом малины и крем-чиза? Нет? Эх…",
    "[Рудольф] /звуки оленя/",
    "[Рудольф] Ух, какая прекрасная погода! Пойду побегаю по лесу."
  ],
  "/рудольф": [
    "[Рудольф] Простите, у вас случайно нет клевера со вкусом малины и крем-чиза? Нет? Эх…",
    "[Рудольф] /звуки оленя/",
    "[Рудольф] Ух, какая прекрасная погода! Пойду побегаю по лесу."
  ],
  "/снеговик": [
    "[Снеговик] Обожаю праздники! Давайте играть в снежки и радоваться жизни!",
    "[Снеговик] Мороз и солнце, день чудесный! Не правда ли?",
    "[Снеговик] Хочу как следует повеселиться в ближайшие дни! Кто со мной?"
  ],
  "/пряничный человек": [
    "[Пряничный человек] Где я? Кто я..?",
    "[Пряничный человек] Я потерявся...",
    "[Пряничный человек] Не ешь меня :("
  ],
  "/пряничный человечек": [
    "[Пряничный человек] Где я? Кто я..?",
    "[Пряничный человек] Я потерявся...",
    "[Пряничный человек] Не ешь меня :("
  ],
  "/эльф": [
    "[Старый эльф] Ну вот, опять меня разбудили. Что, нечем заняться больше?",
    "[Старый эльф] Опять маленькие эльфы что-то натворили…Вот они у меня сейчас получат!..",
    "[Старый эльф] Не надо меня отвлекать, у меня много дел."
  ],
  "/старый эльф": [
    "[Старый эльф] Ну вот, опять меня разбудили. Что, нечем заняться больше?",
    "[Старый эльф] Опять маленькие эльфы что-то натворили…Вот они у меня сейчас получат!..",
    "[Старый эльф] Не надо меня отвлекать, у меня много дел."
  ]}

DEER_FOUND = [
  "[Олень Рудольф] Какой сегодня замечательный день! Правда, есть ощущение, " \
  "что мы что-то потеряли, но я не уверен...",
  "[Второй олень] Рудольф, вот ты всегда слишком много думаешь о делах, "
  "иногда ведь надо и отдыхать. Смотри, какая трава чудная. Наверное, "
  "вкусная, надо попробовать!",
  "[Второй олень] ...ммм, действительно вкусная. Попробуй тоже, эээ, друг. "
  "Кстати, а напомни, как тебя зовут? Не могу вспомнить твоего имени..."
]


# Other
STAGE_COUNT: int = 17
START_TIME: int = 1701369600
