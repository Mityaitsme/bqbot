from uuid import uuid4
from ..storage import upload_file, FILETYPE_TO_EXTENSION
from aiogram.types import Message as TgMessage
from ..core import Message, FileExtension, FileType
from ...config import AUTO_UPLOAD


class MessageHandler:

  @staticmethod
  def from_tg(msg: TgMessage) -> Message:
    return MessageHandler._build_message([msg])

  @staticmethod
  def from_media_group(msgs: list[TgMessage]) -> Message:
    return MessageHandler._build_message(msgs)
  
  @staticmethod
  def _make_filename(filetype: FileType, original: str | None = None) -> str:
    if original:
      return original
    ext = FILETYPE_TO_EXTENSION.get(filetype, ".bin")
    return f"{uuid4().hex}{ext}"
  
  @staticmethod
  def _maybe_upload(file: FileExtension) -> None:
    if AUTO_UPLOAD:
      upload_file(file)

  @staticmethod
  def _build_message(msgs: list[TgMessage]) -> Message:
    files: list[FileExtension] = []

    base = msgs[0]
    user_id = base.from_user.id if base.from_user else None

    for msg in msgs:

      # ---- PHOTO ----
      if msg.photo:
        largest = max(msg.photo, key=lambda p: p.file_size or 0)
        file = FileExtension(
          type=FileType.PHOTO,
          filedata=largest.file_id,
          creator_id=user_id,
          filename=MessageHandler._make_filename(FileType.PHOTO),
        )
        MessageHandler._maybe_upload(file)
        files.append(file)

      # ---- VIDEO ----
      if msg.video:
        file = FileExtension(
          type=FileType.VIDEO,
          filedata=msg.video.file_id,
          creator_id=user_id,
          filename=MessageHandler._make_filename(
            FileType.VIDEO,
            msg.video.file_name,
          ),
        )
        MessageHandler._maybe_upload(file)
        files.append(file)

      # ---- AUDIO + VOICE ----
      if msg.audio or msg.voice:
        audio = msg.audio or msg.voice
        file = FileExtension(
          type=FileType.AUDIO,
          filedata=audio.file_id,
          creator_id=user_id,
          filename=MessageHandler._make_filename(
            FileType.AUDIO,
            getattr(audio, "file_name", None),
          ),
        )
        MessageHandler._maybe_upload(file)
        files.append(file)

      # ---- VIDEO_NOTE ----
      if msg.video_note:
        file = FileExtension(
          type=FileType.VIDEO_NOTE,
          filedata=msg.video_note.file_id,
          creator_id=user_id,
          filename=MessageHandler._make_filename(FileType.VIDEO_NOTE),
        )
        MessageHandler._maybe_upload(file)
        files.append(file)

      # ---- DOCUMENT ----
      if msg.document:
        file = FileExtension(
          type=FileType.DOCUMENT,
          filedata=msg.document.file_id,
          creator_id=user_id,
          filename=MessageHandler._make_filename(
            FileType.DOCUMENT,
            msg.document.file_name,
          ),
        )
        MessageHandler._maybe_upload(file)
        files.append(file)

      # ---- STICKER ----
      if msg.sticker:
        file = FileExtension(
          type=FileType.STICKER,
          filedata=msg.sticker.file_id,
          creator_id=user_id,
          filename=MessageHandler._make_filename(FileType.STICKER),
          additional_data=msg.sticker.emoji or "",
        )
        MessageHandler._maybe_upload(file)
        files.append(file)

    return Message(
      _user_id=user_id,
      _text=base.text or base.caption or "",
      _bot=base.bot,
      _files=files,
    )
