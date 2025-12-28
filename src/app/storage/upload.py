from pathlib import Path

from ..core import FileExtension
from ..db import TeamRepo
from .paths import TEAMS_DIR


def upload_file(file: FileExtension) -> None:
  """
  Saves FileExtension to team storage using its filename.
  """
  if file.creator_id is None:
    raise ValueError("File has no creator_id")

  if not file.filename:
    raise ValueError("FileExtension.filename is empty")

  if file.filedata is None:
    raise ValueError("FileExtension.filedata is empty")

  team = TeamRepo.get_by_member(file.creator_id)
  if team is None:
    raise ValueError(f"No team found for user {file.creator_id}")

  team_dir: Path = TEAMS_DIR / team.name
  team_dir.mkdir(parents=True, exist_ok=True)

  file_path = team_dir / file.filename

  with open(file_path, "wb") as out:
    out.write(file.filedata.read())
