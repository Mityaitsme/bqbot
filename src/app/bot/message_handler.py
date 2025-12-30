import io
from aiogram import types
from typing import List
from uuid import uuid4
from ..storage import upload_file, FILETYPE_TO_EXTENSION
from aiogram.types import Message as TgMessage
from ..core import Message, FileExtension, FileType
from ...config import AUTO_UPLOAD, ADMIN

import logging
logger = logging.getLogger(__name__)


class MessageHandler:

  @staticmethod
  async def from_tg(msg: TgMessage) -> Message:
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
      await upload_file(file)
  
  @staticmethod
  async def _build_callback_message(callback: TgMessage) -> Message:
    message = Message(
      _user_id=callback.from_user.id,
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

  @staticmethod
  async def _build_message(msgs: List[TgMessage]) -> Message:
    files: List[FileExtension] = []

    base = msgs[0]
    user_id = base.from_user.id if base.from_user else None
    tg_nickname = MessageHandler._get_tg_nickname(base)

    for msg in msgs:

      # ---- PHOTO ----
      if msg.photo:
        largest = max(msg.photo, key=lambda p: p.file_size or 0)
        # downloading the file
        downloaded = await msg.bot.download(largest.file_id)
        file_bytes = downloaded.read()
        downloaded.close()
        
        file = FileExtension(
          type=FileType.PHOTO,
          filedata=io.BytesIO(file_bytes),
          creator_id=user_id,
          filename=MessageHandler._make_filename(FileType.PHOTO),
        )
        await MessageHandler._maybe_upload(file)
        files.append(file)

      # ---- VIDEO ----
      if msg.video:
        downloaded = await msg.bot.download(msg.video.file_id)
        file_bytes = downloaded.read()
        downloaded.close()
        
        file = FileExtension(
          type=FileType.VIDEO,
          filedata=io.BytesIO(file_bytes),
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
        downloaded = await msg.bot.download(audio.file_id)
        file_bytes = downloaded.read()
        downloaded.close()
        
        file = FileExtension(
          type=FileType.AUDIO,
          filedata=io.BytesIO(file_bytes),
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
        downloaded = await msg.bot.download(msg.video_note.file_id)
        file_bytes = downloaded.read()
        downloaded.close()
        
        file = FileExtension(
          type=FileType.VIDEO_NOTE,
          filedata=io.BytesIO(file_bytes),
          creator_id=user_id,
          filename=MessageHandler._make_filename(FileType.VIDEO_NOTE),
        )
        await MessageHandler._maybe_upload(file)
        files.append(file)

      # ---- DOCUMENT ----
      if msg.document:
        downloaded = await msg.bot.download(msg.document.file_id)
        file_bytes = downloaded.read()
        downloaded.close()
        
        file = FileExtension(
          type=FileType.DOCUMENT,
          filedata=io.BytesIO(file_bytes),
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
        downloaded = await msg.bot.download(msg.sticker.file_id)
        file_bytes = downloaded.read()
        downloaded.close()
        
        file = FileExtension(
          type=FileType.STICKER,
          filedata=io.BytesIO(file_bytes),
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
