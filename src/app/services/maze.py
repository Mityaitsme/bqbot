from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
import random
from typing import List, Tuple, Optional, Dict, Set

from ..storage import download_riddle_file
from ..core import Message, QuestEngine
from ..db import TeamRepo
from ...config import DEER_FOUND

import logging
logger = logging.getLogger(__name__)

class MazeStep(Enum):
  """
  Enumeration of maze game steps.
  """
  PLAYING = auto()
  DONE = auto()

@dataclass
class MazeContext:
  """
  Holds the state of a player in the maze.
  """
  user_id: int
  step: MazeStep
  x: int = -1
  y: int = -1
  found_key1: bool = False # Deer
  found_key2: bool = False # Sleigh

class MazeService:
  """
  Handles the Maze game logic.
  Map size: 5x5.
  Coordinates: x (0-4, Cols A-E), y (0-4, Rows 1-5).
  Walls are located BETWEEN cells.
  """

  _contexts: dict[int, MazeContext] = {}

  # Map definitions
  # Keys: (x, y)
  # Values: dict with 'type' and extra params
  _map: Dict[Tuple[int, int], Dict] = {
    # Portals (Cycle of 3)
    (0, 0): {"type": "portal", "next": (1, 1)}, # A1 -> B2
    (1, 1): {"type": "portal", "next": (2, 4)}, # B2 -> C5
    (2, 4): {"type": "portal", "next": (0, 0)}, # C5 -> A1

    # Rivers (Ice)
    (0, 2): {"type": "river", "dir": (0, -1), "end": False}, # A3 -> A2
    (0, 1): {"type": "river", "dir": (0, 0), "end": True}, # A2 (end)
    (3, 1): {"type": "river", "dir": (-1, 0), "end": False}, # D2 -> C2
    (2, 1): {"type": "river", "dir": (0, 1), "end": False}, # C2 -> C3
    (2, 2): {"type": "river", "dir": (0, 1), "end": False}, # C3 -> C4
    (2, 3): {"type": "river", "dir": (-1, 0), "end": False}, # C4 -> B4
    (1, 3): {"type": "river", "dir": (0, 0), "end": True}, # B4 (end)

    # Objectives
    (3, 3): {"type": "key1"}, # D4 (Deer)
    (1, 2): {"type": "key2"}, # B3 (Sleigh)
    (0, 4): {"type": "exit", "direction": (-1, 0)}, # A5 (Exit)
  }

  # Walls definition (Borders BETWEEN cells)
  # Set of frozensets, where each item contains 2 coordinates that are blocked
  _walls: Set[frozenset[Tuple[int, int]]] = {
    frozenset({(3, 0), (3, 1)}), # between D1 and D2
    frozenset({(3, 1), (4, 1)}), # between D2 and E2
    frozenset({(4, 2), (4, 3)}), # between E3 and E4
    frozenset({(1, 3), (1, 4)}), # between B4 and B5
  }

  @classmethod
  def _clear_contexts(cls) -> None:
    cls._contexts.clear()
    return

  @classmethod
  def is_active(cls, id: int) -> bool:
    return id in cls._contexts

  @classmethod
  def handle_input(cls, msg: Message) -> Message | List[Message]:
    """
    Handles user input for the maze.
    """
    user_id = msg.user_id
    text = msg.text.strip()
    ctx = cls._load_context(user_id)

    if ctx is None:
      return cls._handle_start_coord(msg)

    if ctx.step == MazeStep.PLAYING:
      return cls._handle_move_command(ctx, text)
    
    return Message(_text="Вы уже прошли лабиринт.")

  @classmethod
  def _save_context(cls, ctx: MazeContext) -> None:
    cls._contexts[ctx.user_id] = ctx

  @classmethod
  def _load_context(cls, user_id: int) -> MazeContext:
    try:
      return cls._contexts[user_id]
    except KeyError:
      return None

  @classmethod
  def _handle_start_coord(cls, msg: Message) -> Message:
    """
    Parses initial coordinates like 'B4'.
    """
    ctx = MazeContext(
      user_id=msg.user_id,
      step=MazeStep.PLAYING
    )
    coords = cls._parse_coordinates(msg.text)
    if not coords:
      return Message(_text="Неверный формат. Используйте английскую букву (A-E) и цифру (1-5). " \
                           "Например: B4")
    
    x, y = coords
    ctx.x = x
    ctx.y = y
    
    status_msg = cls._process_cell_events(ctx)
    if isinstance(status_msg, Message):
      status_msg = [status_msg]

    messages = [Message(_text=f"Вы приземлились в клетку {msg.text}.")]
    messages = messages + status_msg
    cls._save_context(ctx)
    return messages

  @classmethod
  def _handle_move_command(cls, ctx: MazeContext, text: str) -> Message | List[Message]:
    """
    Parses move direction.
    """
    text = text.lower()
    dx, dy = 0, 0
    
    if text in ("вверх", "w", "up"):
      dy = -1
    elif text in ("вниз", "s", "down"):
      dy = 1
    elif text in ("влево", "a", "left"):
      dx = -1
    elif text in ("вправо", "d", "right"):
      dx = 1
    else:
      return Message(_text="Непонятное направление. Используйте: вверх, вниз, влево, вправо.")
    
    curr_pos = (ctx.x, ctx.y)
    new_x, new_y = ctx.x + dx, ctx.y + dy
    next_pos = (new_x, new_y)

    # 1. Check if it is the exit
    in_map = cls._map.get(curr_pos, None)
    
    if in_map and in_map["type"] == "exit" and in_map["direction"] == (dx, dy):
      return cls._exit(ctx)
    
    # 2. Check if there is a border
    if not (0 <= new_x < 5 and 0 <= new_y < 5) or cls._has_wall(curr_pos, next_pos):
      return Message(_text="Вы уперлись в деревья! Густые ёлки не пускают вас.")

    # 2. Update position
    ctx.x = new_x
    ctx.y = new_y
    
    # 3. Process events
    return cls._process_cell_events(ctx)
  
  @classmethod
  def _exit(cls, ctx: MazeContext) -> Message:
    if ctx.found_key1 and ctx.found_key2:
      team = TeamRepo.get_by_member(ctx.user_id)
      cls._contexts.pop(ctx.user_id, None)
      messages = [Message(_text="Ура, вы выбрались из леса с оленями и санями!")]
      return messages + QuestEngine.correct_answer_pipeline(team)
    return Message(_text="Вы нашли выход! Но уходить рано. Нужно найти и оленей, и сани.")

  @classmethod
  def _process_cell_events(cls, ctx: MazeContext) -> Message | List[Message]:
    """
    Checks cell properties. Handles recursive portals/ice.
    """
    cell = cls._get_cell(ctx.x, ctx.y)
    c_type = cell.get("type", "empty")

    if c_type == "key1":
      if not ctx.found_key1:
        ctx.found_key1 = True
        cls._save_context(ctx)
        messages = [Message(
          _text="Ура! Вы нашли Оленей (🦌)!",
          _files=[download_riddle_file("maze", "deer.jpg")]
          )]
        return messages + [Message(_text=text) for text in DEER_FOUND]

    if c_type == "key2":
      if not ctx.found_key2:
        ctx.found_key2 = True
        cls._save_context(ctx)
        return Message(
          _text="Отлично! Вы нашли Сани (🛷)! Только они, кажется, сломанные...",
          _files=[download_riddle_file("maze", "sleigh.jpg")]
          )

    if c_type == "portal":
      next_portal = cell["next"]
      ctx.x, ctx.y = next_portal
      cls._save_context(ctx)
      return Message(_text="Ой! Вы провалились в магический сугроб и очутились в другом!")

    if c_type == "river":
      slid_dist = random.randint(1, 2)
      messages = []
      messages.append(Message(_text="Осторожно, лёд! Вы скользите..."))
      for i in range(slid_dist):
        dx, dy = cell["dir"]
        ctx.x, ctx.y = ctx.x + dx, ctx.y + dy
        cell = cls._get_cell(ctx.x, ctx.y)
      if cell["end"]:
        messages.append(Message(_text="Вы проскользили до конца ледяной горки."))
      cls._save_context(ctx)
      return messages

    cls._save_context(ctx)
    return Message(_text="Вы стоите на обычной лесной полянке.")
    


  @classmethod
  def _get_cell(cls, x: int, y: int) -> Dict:
    return cls._map.get((x, y), {"type": "empty"})

  @classmethod
  def _has_wall(cls, p1: Tuple[int, int], p2: Tuple[int, int]) -> bool:
    """
    Checks if there is a wall between p1 and p2.
    """
    return frozenset({p1, p2}) in cls._walls

  @classmethod
  def _parse_coordinates(cls, text: str) -> Optional[Tuple[int, int]]:
    """
    Converts 'B4' to (1, 3).
    """
    if len(text) < 2: return None
    col_char = text[0].upper()
    row_char = text[1:]
    cols = "ABCDE"
    if col_char not in cols: return None
    x = cols.index(col_char)
    if not row_char.isdigit(): return None
    y_raw = int(row_char)
    if not (1 <= y_raw <= 5): return None
    return x, y_raw - 1

  @classmethod
  def _coords_to_str(cls, x: int, y: int) -> str:
    cols = "ABCDE"
    return f"{cols[x]}{y + 1}"
