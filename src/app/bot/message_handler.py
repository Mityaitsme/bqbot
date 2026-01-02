import io
import asyncio
from aiogram import types
from typing import List, Optional
from uuid import uuid4
from ..storage import upload_file, FILETYPE_TO_EXTENSION
from aiogram.types import Message as TgMessage
from ..core import Message, FileExtension, FileType
from ...config import AUTO_UPLOAD, ADMIN, MAX_FILE_SIZE_MB, TARGET_TOPIC_ID

import logging
logger = logging.getLogger(__name__)


class MessageHandler:

  @staticmethod
  async def from_tg(msg: TgMessage) -> Message:
    # ВАЖНО: ТУТ РЕАЛИЗОВАНО ИГНОРИРОВАНИЕ НЕНУЖНОГО ТОПИКА
    if msg.message_thread_id and msg.message_thread_id != TARGET_TOPIC_ID:
      return
    logger.info(f"[HANDLER] CHAT_ID: {msg.chat.id}")
    if isinstance(msg, types.CallbackQuery):
      return await MessageHandler._build_callback_message(msg)

    message = await MessageHandler._build_message([msg])
    if msg.reply_to_message:
      message.background_info["reply_text"] = msg.reply_to_message.text
    return message

  @staticmethod
  async def from_media_group(msgs: List[TgMessage]) -> Message:
    return await MessageHandler._build_message(msgs)
  
  @staticmethod
  def _make_filename(filetype: FileType, original: str | None = None) -> str:
    if original:
      return original
    ext = FILETYPE_TO_EXTENSION.get(filetype, ".bin")
    return f"{uuid4().hex}{ext}"
  
  @staticmethod
  async def _maybe_upload(file: FileExtension) -> None:
    if AUTO_UPLOAD and file.creator_id not in ADMIN:
      asyncio.create_task(upload_file(file))
  
  @staticmethod
  async def _build_callback_message(callback: TgMessage) -> Message:
    chat_id = callback.message.chat.id if callback.message else callback.from_user.id
    message = Message(
      _user_id=chat_id,
      _text="",
      _bot=callback.bot,
      _background_info={}
    )
    callback_data = callback.data.split(":")
    message.background_info["type"] = callback_data[0]
    message.background_info["team_id"] = callback_data[1]
    message.background_info["other"] = [] if len(callback_data) < 3 else callback_data[2:]
    return message
  
  @staticmethod
  def _get_tg_nickname(msg: TgMessage) -> str:
    if msg.from_user.username:
      return f"@{msg.from_user.username}"
    elif msg.from_user.first_name:
      return msg.from_user.first_name
    return f"user_{msg.from_user.id}"

  # [CHANGED] Новый метод для безопасного скачивания
  @staticmethod
  async def _safe_download(bot, file_id: str, file_size: int | None) -> Optional[io.BytesIO]:
    """
    Checks file size limit and downloads file safely.
    Returns BytesIO object or None if file is too big or download failed.
    """
    if file_size is not None:
      # Лимит в байтах (MB * 1024 * 1024)
      limit_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
      if file_size > limit_bytes:
        logger.warning(f"File {file_id} is too big ({file_size} bytes). Limit: {limit_bytes}. Skipping.")
        return None

    try:
      downloaded = await bot.download(file_id)
      file_bytes = downloaded.read()
      downloaded.close()
      return io.BytesIO(file_bytes)
    except Exception as e:
      logger.error(f"Failed to download file {file_id}: {e}")
      return None

  @staticmethod
  async def _build_message(msgs: List[TgMessage]) -> Message:
    files: List[FileExtension] = []

    base = msgs[0]
    user_id = base.chat.id
    tg_nickname = MessageHandler._get_tg_nickname(base)

    for msg in msgs:

      # ---- PHOTO ----
      if msg.photo:
        largest = max(msg.photo, key=lambda p: p.file_size or 0)
        
        file_data = await MessageHandler._safe_download(msg.bot, largest.file_id, largest.file_size)
        
        if file_data:
          file = FileExtension(
            type=FileType.PHOTO,
            filedata=file_data,
            creator_id=user_id,
            filename=MessageHandler._make_filename(FileType.PHOTO),
          )
          await MessageHandler._maybe_upload(file)
          files.append(file)

      # ---- VIDEO ----
      if msg.video:
        file_data = await MessageHandler._safe_download(msg.bot, msg.video.file_id, msg.video.file_size)
        
        if file_data:
          file = FileExtension(
            type=FileType.VIDEO,
            filedata=file_data,
            creator_id=user_id,
            filename=MessageHandler._make_filename(
              FileType.VIDEO,
              msg.video.file_name,
            ),
          )
          await MessageHandler._maybe_upload(file)
          files.append(file)

      # ---- AUDIO + VOICE ----
      if msg.audio or msg.voice:
        audio = msg.audio or msg.voice
        file_data = await MessageHandler._safe_download(msg.bot, audio.file_id, audio.file_size)
        
        if file_data:
          file = FileExtension(
            type=FileType.AUDIO,
            filedata=file_data,
            creator_id=user_id,
            filename=MessageHandler._make_filename(
              FileType.AUDIO,
              getattr(audio, "file_name", None),
            ),
          )
          await MessageHandler._maybe_upload(file)
          files.append(file)

      # ---- VIDEO_NOTE ----
      if msg.video_note:
        file_data = await MessageHandler._safe_download(msg.bot, msg.video_note.file_id, msg.video_note.file_size)
        
        if file_data:
          file = FileExtension(
            type=FileType.VIDEO_NOTE,
            filedata=file_data,
            creator_id=user_id,
            filename=MessageHandler._make_filename(FileType.VIDEO_NOTE),
          )
          await MessageHandler._maybe_upload(file)
          files.append(file)

      # ---- DOCUMENT ----
      if msg.document:
        file_data = await MessageHandler._safe_download(msg.bot, msg.document.file_id, msg.document.file_size)
        
        if file_data:
          file = FileExtension(
            type=FileType.DOCUMENT,
            filedata=file_data,
            creator_id=user_id,
            filename=MessageHandler._make_filename(
              FileType.DOCUMENT,
              msg.document.file_name,
            ),
          )
          await MessageHandler._maybe_upload(file)
          files.append(file)

      # ---- STICKER ----
      if msg.sticker:
        file_data = await MessageHandler._safe_download(msg.bot, msg.sticker.file_id, msg.sticker.file_size)
        
        if file_data:
          file = FileExtension(
            type=FileType.STICKER,
            filedata=file_data,
            creator_id=user_id,
            filename=MessageHandler._make_filename(FileType.STICKER),
            additional_data=msg.sticker.emoji or "",
          )
          await MessageHandler._maybe_upload(file)
          files.append(file)

    return Message(
      _user_id=user_id,
      _text=base.text or base.caption or "",
      _bot=base.bot,
      _files=files,
      _background_info = {"tg_nickname": tg_nickname}
    )
