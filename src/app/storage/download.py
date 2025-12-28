from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List

from ...config import ADMIN
from ..core import FileExtension, FileType, Team
from .paths import ROOT, team_dir, RIDDLES_DIR
from .filetypes import EXTENSION_TO_FILETYPE
from ..exceptions import StorageError


def download_team_file(team: Team, filename: str) -> FileExtension:
  """
  Loads a file from the team storage and returns it as FileExtension.
  """
  folder = team_dir(team.name).resolve()

  # defensive from leaving STORAGE_ROOT as a root
  if ROOT not in folder.parents and folder != ROOT:
    raise ValueError("Access outside STORAGE_ROOT is forbidden")

  file_path = folder / filename

  if not file_path.exists() or not file_path.is_file():
    raise StorageError(f"File not found: {file_path}")

  ext = file_path.suffix.lower()
  file_type = EXTENSION_TO_FILETYPE.get(ext, FileType.DOCUMENT)

  filedata = file_path.open("rb")

  return FileExtension(
    type=file_type,
    creator_id=team.cur_member_id,
    team_id = team.id,
    filedata=filedata,
    filename=filename,
    creation_time=datetime.now(timezone(timedelta(hours=3))),
    additional_data="team_file",
  )

def download_riddle(riddle_id: int, filenames: List[str]) -> List[FileExtension]:
  """
  Loads all files connected to the riddle, returns a list of FileExtensions.
  """
  riddle_files = []
  folder = RIDDLES_DIR.resolve()

  # defensive from leaving STORAGE_ROOT as a root
  if ROOT not in folder.parents and folder != ROOT:
    raise ValueError("Access outside STORAGE_ROOT is forbidden")

  for filename in filenames:

    file_path = folder / str(riddle_id) / filename

    if not file_path.exists() or not file_path.is_file():
      raise StorageError(f"File not found: {file_path}")

    ext = file_path.suffix.lower()
    file_type = EXTENSION_TO_FILETYPE.get(ext, FileType.DOCUMENT)

    filedata = file_path.open("rb")

    riddle_files.append(FileExtension(
      type=file_type,
      creator_id=ADMIN,
      filedata=filedata,
      filename=filename,
      creation_time=datetime.now(timezone(timedelta(hours=3))),
      additional_data="riddle",
    ))

  return riddle_files
