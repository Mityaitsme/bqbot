import io
from uuid import uuid4
from ..storage import upload_file, FILETYPE_TO_EXTENSION
from aiogram.types import Message as TgMessage
from ..core import Message, FileExtension, FileType
from ...config import AUTO_UPLOAD, ADMIN


class MessageHandler:

  @staticmethod
  async def from_tg(msg: TgMessage) -> Message:
    return await MessageHandler._build_message([msg])

  @staticmethod
  async def from_media_group(msgs: list[TgMessage]) -> Message:
    return await MessageHandler._build_message(msgs)
  
  @staticmethod
  def _make_filename(filetype: FileType, original: str | None = None) -> str:
    if original:
      return original
    ext = FILETYPE_TO_EXTENSION.get(filetype, ".bin")
    return f"{uuid4().hex}{ext}"
  
  @staticmethod
  async def _maybe_upload(file: FileExtension) -> None:
    if AUTO_UPLOAD and file.creator_id != ADMIN:
      await upload_file(file)

  @staticmethod
  async def _build_message(msgs: list[TgMessage]) -> Message:
    files: list[FileExtension] = []

    base = msgs[0]
    user_id = base.from_user.id if base.from_user else None

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
    )
