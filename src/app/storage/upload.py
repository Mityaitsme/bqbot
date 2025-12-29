from pathlib import Path

from ..core import FileExtension
from .paths import TEAMS_DIR

import aiofiles
from pathlib import Path

async def upload_file(file: FileExtension) -> None:
  if file.creator_id is None:
    raise ValueError("File has no creator_id.")

  if not file.filename:
    raise ValueError("File has no name.")

  if file.filedata is None:
    raise ValueError("File has no data in it.")

  from ..db import TeamRepo
  team = TeamRepo.get_by_member(file.creator_id)
  if team is None:
    raise ValueError(f"No team found for user {file.creator_id}")
  
  file.filedata.seek(0)
  save_path: Path = TEAMS_DIR / team.name / file.filename
  save_path.parent.mkdir(parents=True, exist_ok=True)

  async with aiofiles.open(save_path, 'wb') as f:
    while chunk := file.filedata.read(8192):
      await f.write(chunk)

  file.filedata.seek(0)
