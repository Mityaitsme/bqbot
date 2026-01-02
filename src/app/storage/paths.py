"""
This file is responsible for making folder paths generic. 
"""

from ...config import STORAGE_ROOT

if not STORAGE_ROOT:
  raise RuntimeError("STORAGE_ROOT is not set in .env")

TEAMS_DIR = "teams"
RIDDLES_DIR = "riddles"


def team_dir(team_id: int) -> str:
  """
  Returns path to a team's directory in the bucket.
  """
  return f"{TEAMS_DIR}/{team_id}"