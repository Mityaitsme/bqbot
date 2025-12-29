"""
This layer is responsible for interaction with the storage.
Uploads and downloads files.
"""

from .download import download_team_file, download_riddle_file
from .upload import upload_file
from .filetypes import EXTENSION_TO_FILETYPE, FILETYPE_TO_EXTENSION

__all__ = [
  "download_team_file",
  "download_riddle_file",
  "upload_file",
  "EXTENSION_TO_FILETYPE",
  "FILETYPE_TO_EXTENSION"
]
