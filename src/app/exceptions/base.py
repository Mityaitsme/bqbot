
"""Application-specific exceptions.

Place common, project-wide exception classes here so other modules can import
them from `app.exceptions.base`.
"""

from __future__ import annotations


class ApplicationError(Exception):
	"""Base class for non-built-in application errors."""


class TeamError(ApplicationError):
	"""Generic team-related error."""


class TeamNotFound(TeamError):
	"""Raised when a referenced team cannot be found."""


class RiddleError(ApplicationError):
	"""Riddle / stage related errors (missing riddle, malformed riddle, etc)."""


class AnswerError(ApplicationError):
	"""Raised when an answer cannot be validated (riddle check failed)."""

class StorageError(Exception):
  """Raised when file cannot be downloaded or uploaded for some reasons."""
