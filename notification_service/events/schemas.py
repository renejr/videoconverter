"""
Schemas de Eventos - Event Bus
Notification Service - Plataforma VOD
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """
    Tipos de eventos disponíveis no sistema
    """
    # Eventos de Usuário
    USER_REGISTERED = "user.registered"
    USER_VERIFIED = "user.verified"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PASSWORD_RESET = "user.password_reset"
    USER_PASSWORD_CHANGED = "user.password_changed"
    USER_PROFILE_UPDATED = "user.profile_updated"
    USER_DEACTIVATED = "user.deactivated"
    USER_REACTIVATED = "user.reactivated"
    
    # Eventos de Pagamento
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
    
    # Eventos de Conteúdo
    CONTENT_UPLOADED = "content.uploaded"
    CONTENT_PROCESSED = "content.processed"
    CONTENT_PUBLISHED = "content.published"
    CONTENT_DELETED = "content.deleted"
    
    # Eventos de Segurança
    SECURITY_SUSPICIOUS_LOGIN = "security.suspicious_login"
    SECURITY_ACCOUNT_LOCKED = "security.account_locked"
    SECURITY_2FA_ENABLED = "security.2fa_enabled"
    SECURITY_2FA_DISABLED = "security.2fa_disabled"


class BaseEvent(BaseModel):
    """
    Schema base para todos os eventos
    """
    event_type: EventType = Field(..., description="Tipo do evento")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do evento")
    source: str = Field(..., description="Serviço que originou o evento")
    version: str = Field(default="1.0", description="Versão do schema do evento")
    correlation_id: Optional[str] = Field(None, description="ID de correlação para rastreamento")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais")


class UserEvent(BaseEvent):
    """
    Schema para eventos relacionados a usuários
    """
    user_id: int = Field(..., description="ID do usuário")
    email: str = Field(..., description="Email do usuário")
    name: Optional[str] = Field(None, description="Nome do usuário")
    user_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dados adicionais do usuário")
    
    class Config:
        schema_extra = {
            "example": {
                "event_type": "user.registered",
                "user_id": 123,
                "email": "user@example.com",
                "name": "João Silva",
                "user_data": {
                    "registration_source": "web",
                    "plan": "basic"
                },
                "source": "user_service",
                "correlation_id": "reg_123456"
            }
        }


class PaymentEvent(BaseEvent):
    """
    Schema para eventos relacionados a pagamentos
    """
    user_id: int = Field(..., description="ID do usuário")
    payment_id: Optional[int] = Field(None, description="ID do pagamento")
    subscription_id: Optional[int] = Field(None, description="ID da assinatura")
    amount: Optional[float] = Field(None, description="Valor do pagamento")
    currency: Optional[str] = Field(default="BRL", description="Moeda do pagamento")
    plan_name: Optional[str] = Field(None, description="Nome do plano")
    payment_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dados adicionais do pagamento")
    
    class Config:
        schema_extra = {
            "example": {
                "event_type": "payment.completed",
                "user_id": 123,
                "payment_id": 456,
                "subscription_id": 789,
                "amount": 29.90,
                "currency": "BRL",
                "plan_name": "Premium",
                "payment_data": {
                    "payment_method": "credit_card",
                    "gateway": "stripe"
                },
                "source": "payment_service"
            }
        }


class ContentEvent(BaseEvent):
    """
    Schema para eventos relacionados a conteúdo
    """
    user_id: int = Field(..., description="ID do usuário proprietário")
    content_id: int = Field(..., description="ID do conteúdo")
    content_title: Optional[str] = Field(None, description="Título do conteúdo")
    content_type: Optional[str] = Field(None, description="Tipo do conteúdo")
    content_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dados adicionais do conteúdo")
    
    class Config:
        schema_extra = {
            "example": {
                "event_type": "content.published",
                "user_id": 123,
                "content_id": 456,
                "content_title": "Meu Vídeo Incrível",
                "content_type": "video",
                "content_data": {
                    "duration": 300,
                    "resolution": "1080p",
                    "category": "entertainment"
                },
                "source": "content_service"
            }
        }


class SecurityEvent(BaseEvent):
    """
    Schema para eventos relacionados à segurança
    """
    user_id: int = Field(..., description="ID do usuário")
    ip_address: Optional[str] = Field(None, description="Endereço IP")
    user_agent: Optional[str] = Field(None, description="User Agent")
    location: Optional[str] = Field(None, description="Localização geográfica")
    security_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dados adicionais de segurança")
    
    class Config:
        schema_extra = {
            "example": {
                "event_type": "security.suspicious_login",
                "user_id": 123,
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "location": "São Paulo, BR",
                "security_data": {
                    "risk_score": 0.8,
                    "reason": "unusual_location"
                },
                "source": "security_service"
            }
        }


class NotificationEvent(BaseEvent):
    """
    Schema para eventos de notificação
    """
    notification_id: int = Field(..., description="ID da notificação")
    recipient: str = Field(..., description="Destinatário da notificação")
    channel: str = Field(..., description="Canal de envio")
    status: str = Field(..., description="Status da notificação")
    notification_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dados da notificação")
    
    class Config:
        schema_extra = {
            "example": {
                "event_type": "notification.sent",
                "notification_id": 789,
                "recipient": "user@example.com",
                "channel": "email",
                "status": "sent",
                "notification_data": {
                    "template": "welcome_email",
                    "provider": "gmail"
                },
                "source": "notification_service"
            }
        }