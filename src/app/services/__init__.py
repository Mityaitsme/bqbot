"""
This layer is responsible for processes. It is only registration for now, but in later
versions other processes may be added (verification, notification etc.)
"""

from .registration import RegistrationService, RegistrationStep

__all__ = [
    "RegistrationService",
    "RegistrationStep" # for tests
]
