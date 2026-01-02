import logging
import asyncio
import socket
from typing import List, Callable, Any
import aiohttp
import yarl
from aiogram import Bot
from aiogram.types import (
  InputMediaPhoto,
  InputMediaVideo,
  InputMediaDocument,
  BufferedInputFile,
  URLInputFile,
  LinkPreviewOptions
)
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
# [CHANGED] Импортируем ClientTimeout для настройки таймингов скачивания
from aiohttp import ClientTimeout
from ..core import Message, FileType

logger = logging.getLogger(__name__)

async def _ensure_connection(bot: Bot, chat_id: int, action: str = "typing") -> None:
  try:
    await bot.send_chat_action(chat_id=chat_id, action=action, request_timeout=2)
  except Exception:
    await asyncio.sleep(0.5)

async def _safe_send(func: Callable, *args, **kwargs) -> Any:
  retries = 3
  for attempt in range(retries):
    try:
      return await func(*args, **kwargs)
    except TelegramRetryAfter as e:
      logger.warning(f"[SENDER] Flood limit, sleeping {e.retry_after}s")
      await asyncio.sleep(e.retry_after)
      continue
    except TelegramNetworkError as e:
      if attempt < retries - 1:
        logger.warning(f"[SENDER] Network error ({e}), retrying... (attempt {attempt+1})")
        await asyncio.sleep(0.5)
        continue
      logger.error(f"[SENDER] Network error persisted after {retries} attempts.")
      raise e
    except Exception as e:
      raise e

# [CHANGED] Функция для расчета динамического таймаута
def _calculate_timeout(total_bytes: int) -> int:
  """
  Calculates timeout based on file size.
  Base: 30s.
  Rate: ~10s per 1 MB.
  Max: 900s (15 min).
  """
  size_mb = total_bytes / (1024 * 1024)
  timeout = 30 + int(size_mb * 10)
  return min(timeout, 900)

async def send_messages(messages: Message | List[Message], bot: Bot):
  """
  Sends core.Message via Telegram bot.
  """
  if isinstance(messages, Message):
    messages = [messages]

  connector = aiohttp.TCPConnector(force_close=True, family=socket.AF_INET)
  
  async with aiohttp.ClientSession(connector=connector) as http_session:
    for message in messages:
      if message.recipient_id is None:
        continue 

      tg_bot = message.bot or bot

      # ---------- MEDIA ----------
      if message.files:
        media = []
        caption_used = False
        
        # [CHANGED] Считаем общий вес файлов для таймаута
        total_payload_size = 0

        for idx, file in enumerate(message.files):
          caption = None
          if not caption_used and message.text and len(message.text) <= 1024:
            caption = message.text
            caption_used = True

          input_file = None
          
          # --- ЛОГИКА СКАЧИВАНИЯ ---
          if isinstance(file.filedata, str):
            url_to_download = file.filedata
            if url_to_download.startswith("supa://"):
              from ...config import STORAGE_ROOT
              path_in_bucket = url_to_download.split("supa://")[1]
              url_to_download = STORAGE_ROOT(path_in_bucket)
            
            if not url_to_download or not url_to_download.startswith("http"):
              logger.error(f"[SENDER] Skipping file {file.filename}: Invalid URL")
              continue
            
            download_success = False
            for attempt in range(3): 
              try:
                url = yarl.URL(url_to_download, encoded=True)
                
                # [CHANGED] Добавили жесткий таймаут на скачивание.
                # connect=5: если Supabase не ответит за 5 сек, мы идем в retry.
                # total=120: на само скачивание даем 2 минуты макс.
                dl_timeout = ClientTimeout(total=120, connect=5)

                async with http_session.get(url, headers={"Connection": "close"}, timeout=dl_timeout) as response:
                  if response.status != 200:
                    if response.status == 400: break 
                    await asyncio.sleep(0.5)
                    continue
                  
                  file_bytes = await response.read()
                  input_file = BufferedInputFile(file_bytes, filename=file.filename)
                  
                  # [CHANGED] Добавляем размер к общему весу
                  total_payload_size += len(file_bytes)
                  
                  download_success = True
                  break 

              except Exception as e:
                # logger.warning(f"[SENDER] Download attempt {attempt+1} failed: {e}")
                await asyncio.sleep(0.5)
            
            if not download_success:
              logger.error(f"[SENDER] Failed to download {file.filename}")
              continue
              
          elif hasattr(file.filedata, 'read'):
            file.filedata.seek(0)
            file_bytes = file.filedata.read()
            input_file = BufferedInputFile(file_bytes, filename=file.filename)
            # [CHANGED] Добавляем размер
            total_payload_size += len(file_bytes)
          else:
            logger.error(f"Unknown filedata type: {type(file.filedata)}")
            continue

          # ... (код сборки media без изменений) ...
          if file.type == FileType.PHOTO:
            media.append(InputMediaPhoto(media=input_file, caption=caption, parse_mode="HTML"))
          elif file.type == FileType.VIDEO:
            media.append(InputMediaVideo(media=input_file, caption=caption, parse_mode="HTML"))
          elif file.type == FileType.DOCUMENT:
            media.append(InputMediaDocument(media=input_file, caption=caption, parse_mode="HTML"))

          # --- ОТПРАВКА ОДИНОЧНЫХ (С ДИНАМИЧЕСКИМ ТАЙМАУТОМ) ---
          elif file.type == FileType.AUDIO:
            try:
              await _ensure_connection(tg_bot, message.recipient_id, "upload_voice")
              
              # [CHANGED] Рассчитываем таймаут
              dynamic_timeout = _calculate_timeout(len(file_bytes))
              
              await _safe_send(
                tg_bot.send_voice,
                chat_id=message.recipient_id,
                voice=input_file,
                caption=caption,
                parse_mode="HTML",
                request_timeout=dynamic_timeout # Используем расчетный
              )
            except Exception as e: logger.error(f"[SENDER ERROR] Audio: {e}")

          elif file.type == FileType.VIDEO_NOTE:
            try:
              await _ensure_connection(tg_bot, message.recipient_id, "upload_video_note")
              
              # [CHANGED] Рассчитываем таймаут
              dynamic_timeout = _calculate_timeout(len(file_bytes))

              await _safe_send(
                tg_bot.send_video_note,
                chat_id=message.recipient_id,
                video_note=input_file,
                request_timeout=dynamic_timeout
              )
            except Exception as e: logger.error(f"[SENDER ERROR] Video Note: {e}")

          elif file.type == FileType.STICKER:
            try:
              await _ensure_connection(tg_bot, message.recipient_id, "choose_sticker")
              await _safe_send(tg_bot.send_sticker, chat_id=message.recipient_id, sticker=input_file, request_timeout=60)
            except Exception as e: logger.error(f"[SENDER ERROR] Sticker: {e}")

        if media:
          try:
            action = "upload_photo" 
            if media and isinstance(media[0], InputMediaVideo): action = "upload_video"
            if media and isinstance(media[0], InputMediaDocument): action = "upload_document"
            
            await _ensure_connection(tg_bot, message.recipient_id, action)
            
            # [CHANGED] Рассчитываем таймаут для всей группы
            dynamic_timeout = _calculate_timeout(total_payload_size)
            
            await _safe_send(
              tg_bot.send_media_group,
              chat_id=message.recipient_id,
              media=media,
              request_timeout=dynamic_timeout
            )
          except Exception as e: logger.error(f"[SENDER ERROR] Media Group: {e}")

        if caption_used:
          continue

      # ---------- TEXT ----------
      if message.text:
        try:
          await _safe_send(
            tg_bot.send_message,
            chat_id=message.recipient_id,
            text=message.text,
            reply_markup=message.reply_markup,
            parse_mode="HTML",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            request_timeout=10 
          )
          logger.info(f"[SEND] → {message.recipient_id}: Text sent.")
        except Exception as e:
          logger.error(f"[SEND ERROR] Failed to send text to {message.recipient_id}: {e}")
