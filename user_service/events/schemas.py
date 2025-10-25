"""
Event Schemas - User Service
Schemas para padronização dos eventos publicados
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class EventType(str, Enum):
    """
    Tipos de eventos do User Service
    """
    USER_REGISTERED = "user.registered"
    EMAIL_VERIFICATION_REQUESTED = "user.email_verification_requested"
    PASSWORD_RESET_REQUESTED = "user.password_reset_requested"
    USER_PROFILE_UPDATED = "user.profile_updated"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    EMAIL_VERIFIED = "user.email_verified"
    PASSWORD_CHANGED = "user.password_changed"


class BaseEvent(BaseModel):
    """
    Schema base para todos os eventos
    """
    event_type: EventType = Field(description="Tipo do evento")
    event_id: str = Field(description="ID único do evento")
    user_id: int = Field(description="ID do usuário")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do evento")
    source: str = Field(default="user_service", description="Serviço de origem")
    version: str = Field(default="1.0", description="Versão do schema")
    correlation_id: Optional[str] = Field(None, description="ID de correlação para rastreamento")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserRegisteredEvent(BaseEvent):
    """
    Evento disparado quando um usuário se registra
    """
    event_type: EventType = Field(default=EventType.USER_REGISTERED)
    data: Dict[str, Any] = Field(description="Dados do usuário registrado")
    
    @classmethod
    def create(
        cls,
        event_id: str,
        user_id: int,
        email: str,
        full_name: str,
        language_preference: str = "pt-BR",
        timezone: str = "America/Sao_Paulo",
        correlation_id: Optional[str] = None
    ) -> "UserRegisteredEvent":
        """
        Cria evento de usuário registrado
        
        Args:
            event_id: ID único do evento
            user_id: ID do usuário
            email: Email do usuário
            full_name: Nome completo
            language_preference: Idioma preferido
            timezone: Fuso horário
            correlation_id: ID de correlação
            
        Returns:
            UserRegisteredEvent: Evento criado
        """
        return cls(
            event_id=event_id,
            user_id=user_id,
            correlation_id=correlation_id,
            data={
                "email": email,
                "full_name": full_name,
                "language_preference": language_preference,
                "timezone": timezone,
                "registration_timestamp": datetime.utcnow().isoformat()
            }
        )


class EmailVerificationRequestedEvent(BaseEvent):
    """
    Evento disparado quando verificação de email é solicitada
    """
    event_type: EventType = Field(default=EventType.EMAIL_VERIFICATION_REQUESTED)
    data: Dict[str, Any] = Field(description="Dados da verificação de email")
    
    @classmethod
    def create(
        cls,
        event_id: str,
        user_id: int,
        email: str,
        full_name: str,
        verification_token: str,
        verification_url: str,
        expires_at: datetime,
        language_preference: str = "pt-BR",
        correlation_id: Optional[str] = None
    ) -> "EmailVerificationRequestedEvent":
        """
        Cria evento de verificação de email solicitada
        
        Args:
            event_id: ID único do evento
            user_id: ID do usuário
            email: Email a ser verificado
            full_name: Nome completo
            verification_token: Token de verificação
            verification_url: URL de verificação
            expires_at: Data de expiração
            language_preference: Idioma preferido
            correlation_id: ID de correlação
            
        Returns:
            EmailVerificationRequestedEvent: Evento criado
        """
        return cls(
            event_id=event_id,
            user_id=user_id,
            correlation_id=correlation_id,
            data={
                "email": email,
                "full_name": full_name,
                "verification_token": verification_token,
                "verification_url": verification_url,
                "expires_at": expires_at.isoformat(),
                "language_preference": language_preference,
                "request_timestamp": datetime.utcnow().isoformat()
            }
        )


class PasswordResetRequestedEvent(BaseEvent):
    """
    Evento disparado quando reset de senha é solicitado
    """
    event_type: EventType = Field(default=EventType.PASSWORD_RESET_REQUESTED)
    data: Dict[str, Any] = Field(description="Dados do reset de senha")
    
    @classmethod
    def create(
        cls,
        event_id: str,
        user_id: int,
        email: str,
        full_name: str,
        reset_token: str,
        reset_url: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        language_preference: str = "pt-BR",
        correlation_id: Optional[str] = None
    ) -> "PasswordResetRequestedEvent":
        """
        Cria evento de reset de senha solicitado
        
        Args:
            event_id: ID único do evento
            user_id: ID do usuário
            email: Email do usuário
            full_name: Nome completo
            reset_token: Token de reset
            reset_url: URL de reset
            expires_at: Data de expiração
            ip_address: IP da solicitação
            user_agent: User agent
            language_preference: Idioma preferido
            correlation_id: ID de correlação
            
        Returns:
            PasswordResetRequestedEvent: Evento criado
        """
        return cls(
            event_id=event_id,
            user_id=user_id,
            correlation_id=correlation_id,
            data={
                "email": email,
                "full_name": full_name,
                "reset_token": reset_token,
                "reset_url": reset_url,
                "expires_at": expires_at.isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "language_preference": language_preference,
                "request_timestamp": datetime.utcnow().isoformat()
            }
        )


class UserProfileUpdatedEvent(BaseEvent):
    """
    Evento disparado quando perfil do usuário é atualizado
    """
    event_type: EventType = Field(default=EventType.USER_PROFILE_UPDATED)
    data: Dict[str, Any] = Field(description="Dados da atualização do perfil")
    
    @classmethod
    def create(
        cls,
        event_id: str,
        user_id: int,
        email: str,
        full_name: str,
        updated_fields: Dict[str, Any],
        language_preference: str = "pt-BR",
        correlation_id: Optional[str] = None
    ) -> "UserProfileUpdatedEvent":
        """
        Cria evento de perfil atualizado
        
        Args:
            event_id: ID único do evento
            user_id: ID do usuário
            email: Email do usuário
            full_name: Nome completo
            updated_fields: Campos atualizados
            language_preference: Idioma preferido
            correlation_id: ID de correlação
            
        Returns:
            UserProfileUpdatedEvent: Evento criado
        """
        return cls(
            event_id=event_id,
            user_id=user_id,
            correlation_id=correlation_id,
            data={
                "email": email,
                "full_name": full_name,
                "updated_fields": updated_fields,
                "language_preference": language_preference,
                "update_timestamp": datetime.utcnow().isoformat()
            }
        )