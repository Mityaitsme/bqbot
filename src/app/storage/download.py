from ...config import ADMIN
# [CHANGED] STORAGE_ROOT здесь больше не нужен для генерации, но оставим импорт, если нужен для проверок
from ..core import FileExtension, FileType, Team
from .paths import team_dir, RIDDLES_DIR
from .filetypes import EXTENSION_TO_FILETYPE
from datetime import datetime, timezone, timedelta

def download_team_file(team: Team, filename: str) -> FileExtension:
  """
  Returns a path marker for a team file.
  """
  folder = team_dir(team.id) # Используем ID, как договаривались
  file_path = f"{folder}/{filename}"

  ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
  file_type = EXTENSION_TO_FILETYPE.get(ext, FileType.DOCUMENT)

  # [FIX] Не генерируем ссылку сейчас! Ссылка протухнет в кэше.
  # Возвращаем "сырой" путь с префиксом.
  file_url_marker = f"supa://{file_path}"

  return FileExtension(
    type=file_type,
    creator_id=team.cur_member_id,
    team_id = team.id,
    filedata=file_url_marker, # Кладем маркер
    filename=filename,
    creation_time=datetime.now(timezone(timedelta(hours=3))),
    additional_data="team_file",
  )

def download_riddle_file(riddle: int | str, filename: str) -> FileExtension:
  """
  Returns a path marker for a riddle file.
  """
  folder = RIDDLES_DIR
  file_path = f"{folder}/{riddle}/{filename}"

  ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
  file_type = EXTENSION_TO_FILETYPE.get(ext, FileType.DOCUMENT)

  # [FIX] То же самое. Кладем маркер вместо живой ссылки.
  file_url_marker = f"supa://{file_path}"

  return FileExtension(
    type=file_type,
    creator_id=ADMIN[0],
    filedata=file_url_marker, # Маркер
    filename=filename,
    creation_time=datetime.now(timezone(timedelta(hours=3))),
    additional_data="riddle",
    )
