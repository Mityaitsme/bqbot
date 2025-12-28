"""
This layer is responsible for interaction with the storage.
Uploads and downloads files.
"""

from .download import download_team_file, download_riddle
from .upload import upload_file

__all__ = [
  "download_team_file",
  "download_riddle",
  "upload_file"
]
