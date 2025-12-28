"""
This file is responsible for making folder paths generic. 
"""

from pathlib import Path
from ...config import STORAGE_ROOT

if not STORAGE_ROOT:
  raise RuntimeError("STORAGE_ROOT is not set in .env")

ROOT = Path(STORAGE_ROOT).resolve()
TEAMS_DIR = ROOT / "teams"
RIDDLES_DIR = ROOT / "riddles"


def team_dir(team_name: str) -> Path:
  """
  Returns path to a team's directory.
  """
  return TEAMS_DIR / team_name
