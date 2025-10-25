"""
Services - Notification Service
Plataforma VOD
"""

from .email_service import EmailService
from .notification_service import NotificationService
from .template_service import TemplateService

__all__ = [
    "EmailService",
    "NotificationService", 
    "TemplateService"
]