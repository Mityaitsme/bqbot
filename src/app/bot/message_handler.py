# src/app/tg/message_handler.py
from aiogram.types import Message as TgMessage
from ..core import Message, FileExtension, FileType


class MessageHandler:

  @staticmethod
  def from_tg(msg: TgMessage) -> Message:
    return MessageHandler._build_message([msg])

  @staticmethod
  def from_media_group(msgs: list[TgMessage]) -> Message:
    return MessageHandler._build_message(msgs)

  @staticmethod
  def _build_message(msgs: list[TgMessage]) -> Message:
    files: list[FileExtension] = []

    base = msgs[0]
    user_id = base.from_user.id if base.from_user else None

    for msg in msgs:

      # ---- PHOTO ----
      if msg.photo:
        largest = max(msg.photo, key=lambda p: p.file_size or 0)
        files.append(FileExtension(
          type=FileType.PHOTO,
          filedata=largest.file_id,
          creator_id=user_id,
        ))

      # ---- VIDEO ----
      if msg.video:
        files.append(FileExtension(
          type=FileType.VIDEO,
          filedata=msg.video.file_id,
          creator_id=user_id,
        ))

      # ---- AUDIO + VOICE (merged) ----
      if msg.audio or msg.voice:
        audio = msg.audio or msg.voice
        files.append(FileExtension(
          type=FileType.AUDIO,
          filedata=audio.file_id,
          creator_id=user_id,
        ))
      
      # ---- VIDEO_NOTE (circle) ----
      if msg.video_note:
        files.append(FileExtension(
          type=FileType.VIDEO_NOTE,
          filedata=msg.video_note.file_id,
          creator_id=user_id,
        ))


      # ---- DOCUMENT ----
      if msg.document:
        files.append(FileExtension(
          type=FileType.DOCUMENT,
          filedata=msg.document.file_id,
          creator_id=user_id,
          
        ))

      # ---- STICKER ----
      if msg.sticker:
        files.append(FileExtension(
          type=FileType.STICKER,
          filedata=msg.sticker.file_id,
          creator_id=user_id,
          additional_data=msg.sticker.emoji or "",
        ))

    return Message(
      _user_id=user_id,
      _text=base.text or base.caption or "",
      _bot=base.bot,
      _files=files,
    )
