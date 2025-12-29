import logging
from typing import List
from aiogram import Bot
from aiogram.types import (
  InputMediaPhoto,
  InputMediaVideo,
  InputMediaDocument,
  BufferedInputFile
)
from ..core import Message, FileType
logger = logging.getLogger(__name__)


async def send_messages(messages: Message | List[Message], bot):
  """
  Sends core.Message via Telegram bot.
  """
  if isinstance(messages, Message):
    messages = [messages]

  for message in messages:
    if message.recipient_id is None:
      return

    # TODO: work out what to do using TGMember
    tg_bot = message.bot or bot

    # ---------- MEDIA ----------
    if message.files:
      media = []
      caption_used = False

      for file in message.files:
        caption = None
        if not caption_used and message.text:
          caption = message.text
          caption_used = True
        file.filedata.seek(0)  # BufferedReader
        file_bytes = file.filedata.read()
        input_file = BufferedInputFile(file_bytes, filename=file.filename)

        # ---- MEDIA GROUP ALLOWED ----
        if file.type == FileType.PHOTO:
          media.append(InputMediaPhoto(media=input_file, caption=caption))

        elif file.type == FileType.VIDEO:
          media.append(InputMediaVideo(media=input_file, caption=caption))

        elif file.type == FileType.DOCUMENT:
          media.append(InputMediaDocument(media=input_file, caption=caption))

        # ---- SEPARATE SEND ----
        elif file.type == FileType.AUDIO:
          await tg_bot.send_voice(
            chat_id=message.recipient_id,
            voice=input_file,
            caption=caption,
          )

        elif file.type == FileType.VIDEO_NOTE:
          await tg_bot.send_video_note(
            chat_id=message.recipient_id,
            video_note=input_file,
          )

        elif file.type == FileType.STICKER:
          await tg_bot.send_sticker(
            chat_id=message.recipient_id,
            sticker=input_file,
          )

      if media:
        await tg_bot.send_media_group(
          chat_id=message.recipient_id,
          media=media,
        )

      continue

    # ---------- TEXT ----------
    await tg_bot.send_message(
      chat_id=message.recipient_id,
      text=message.text,
    )

    logger.info(f"[SEND] → {message.recipient_id}: {message.text}")
