"""
This layer is responsible for throwing exceptions related to various services.
More exceptions will be added later as the project grows; only the most necessary
ones are here for now.
"""

from .base import *

__all__ = [
	"ApplicationError",
	"TeamError",
	"TeamNotFound",
	"RiddleError",
	"InvalidAnswerError",
  "StorageError"
]
