"""
The module which is responsible for all work with data.
We can either find the requiring data in cache or in the database. This module successfully
combines this two approaches for best efficiency.
This package contains classes MemberRepo, TeamRepo and RiddleRepo and some other classes
used by these 3.
"""

from .repos import TeamRepo, MemberRepo, RiddleRepo

__all__ = [
  "TeamRepo",
  "MemberRepo",
  "RiddleRepo"
]
