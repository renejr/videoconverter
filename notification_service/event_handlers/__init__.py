"""
Event Handlers - Notification Service
Handlers para processar eventos do Event Bus
"""

from .user_handlers import (
    UserRegisteredHandler,
    EmailVerificationRequestedHandler,
    PasswordResetRequestedHandler,
    UserProfileUpdatedHandler
)

__all__ = [
    "UserRegisteredHandler",
    "EmailVerificationRequestedHandler", 
    "PasswordResetRequestedHandler",
    "UserProfileUpdatedHandler"
]