"""
Event Bus Module - User Service
Módulo responsável pela comunicação assíncrona via eventos
"""

from .connection import EventBusConnection
from .publisher import EventPublisher
from .schemas import (
    UserRegisteredEvent,
    EmailVerificationRequestedEvent,
    PasswordResetRequestedEvent,
    UserProfileUpdatedEvent,
    BaseEvent
)

__all__ = [
    "EventBusConnection",
    "EventPublisher", 
    "UserRegisteredEvent",
    "EmailVerificationRequestedEvent",
    "PasswordResetRequestedEvent",
    "UserProfileUpdatedEvent",
    "BaseEvent"
]