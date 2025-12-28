"""
Casts extensions to class FileType.
"""
from ..core import FileType


EXTENSION_TO_FILETYPE: dict[str, FileType] = {
  ".jpg": FileType.PHOTO,
  ".jpeg": FileType.PHOTO,
  ".png": FileType.PHOTO,
  ".webp": FileType.PHOTO,

  ".mp4": FileType.VIDEO,
  ".mov": FileType.VIDEO,

  ".ogg": FileType.AUDIO,
  ".mp3": FileType.AUDIO,

  ".pdf": FileType.DOCUMENT,
  ".txt": FileType.DOCUMENT,
}

FILETYPE_TO_EXTENSION: dict[str, FileType] = {
  FileType.PHOTO: ".jpg",
  FileType.VIDEO: ".mp4",
  FileType.VIDEO_NOTE: ".mp4",
  FileType.AUDIO: ".ogg",
  FileType.DOCUMENT: ".bin",
  FileType.STICKER: ".webp",
}