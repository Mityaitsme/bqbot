from ..core import FileExtension
from .paths import TEAMS_DIR
from ...config import STORAGE_ROOT, MAX_FILE_SIZE_MB

import logging
logger = logging.getLogger(__name__)

async def upload_file(file: FileExtension) -> None:
  if file.creator_id is None:
    raise ValueError("File has no creator_id.")

  if not file.filename:
    raise ValueError("File has no name.")

  if file.filedata is None:
    raise ValueError("File has no data in it.")

  # [CHANGED] Добавлена проверка на размер файла (примерный лимит)
  # Этот лимит можно настроить в config.py
  if file.filedata.getbuffer().nbytes > MAX_FILE_SIZE_MB * 1024 * 1024:
    logger.warning(f"File from user {file.creator_id} is too large "
                   f"({file.filedata.getbuffer().nbytes / (1024*1024):.2f}MB). "
                   f"Max: {MAX_FILE_SIZE_MB}MB. Skipping upload.")
    # Здесь можно отправить сообщение админу о попытке загрузки большого файла
    return # Просто выходим, не пытаясь загрузить слишком большой файл

  from ..db import TeamRepo
  team = TeamRepo.get_by_member(file.creator_id)
  if team is None:
    # [CHANGED] Улучшено сообщение об ошибке для логов
    logger.error(f"Team not found for user {file.creator_id} during file upload.")
    return 
  
  file.filedata.seek(0)
  
  save_path = f"{TEAMS_DIR}/{team.id}/{file.filename}"
  
  file_bytes = file.filedata.read()

  try:
    STORAGE_ROOT.client.storage \
      .from_(STORAGE_ROOT.bucket_name) \
      .upload(
        path=save_path,
        file=file_bytes,
        file_options={"upsert": "true"}
      )
    logger.info(f"File '{file.filename}' uploaded successfully for team {team.id}.") # [CHANGED] Лог успешной загрузки
  except Exception as e:
    # [CHANGED] Логируем ошибку, но бот не падает
    logger.error(f"Failed to upload file '{file.filename}' for team {team.id}: {e}")
    # Можно отправить сообщение админу о проблеме загрузки
  finally:
    file.filedata.seek(0) # [CHANGED] Важно вернуть указатель в начало
