"""
Event Publisher - User Service
Responsável por publicar eventos no Event Bus
"""

import json
import uuid
import logging
from typing import Optional
from datetime import datetime

from .connection import event_bus
from .schemas import (
    BaseEvent,
    UserRegisteredEvent,
    EmailVerificationRequestedEvent,
    PasswordResetRequestedEvent,
    UserProfileUpdatedEvent,
    EventType
)

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publisher de eventos para o Event Bus
    """
    
    def __init__(self):
        """
        Inicializa o publisher
        """
        self.channel_prefix = "vidconv.events"
    
    async def publish_event(self, event: BaseEvent) -> bool:
        """
        Publica um evento no Event Bus
        
        Args:
            event: Evento a ser publicado
            
        Returns:
            bool: True se publicado com sucesso
        """
        try:
            # Conectar se necessário
            if not event_bus.is_connected:
                await event_bus.connect()
            
            # Serializar evento
            event_data = event.json()
            
            # Determinar canal baseado no tipo do evento
            channel = f"{self.channel_prefix}.{event.event_type.value}"
            
            # Publicar no Redis
            success = await event_bus.publish(channel, event_data)
            
            if success:
                logger.info(
                    f"✅ Evento publicado: {event.event_type.value} "
                    f"(ID: {event.event_id}, User: {event.user_id})"
                )
            else:
                logger.error(
                    f"❌ Falha ao publicar evento: {event.event_type.value} "
                    f"(ID: {event.event_id})"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar evento: {str(e)}")
            return False
    
    async def publish_user_registered(
        self,
        user_id: int,
        email: str,
        full_name: str,
        language_preference: str = "pt-BR",
        timezone: str = "America/Sao_Paulo",
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publica evento de usuário registrado
        
        Args:
            user_id: ID do usuário
            email: Email do usuário
            full_name: Nome completo
            language_preference: Idioma preferido
            timezone: Fuso horário
            correlation_id: ID de correlação
            
        Returns:
            bool: True se publicado com sucesso
        """
        event = UserRegisteredEvent.create(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            email=email,
            full_name=full_name,
            language_preference=language_preference,
            timezone=timezone,
            correlation_id=correlation_id
        )
        
        return await self.publish_event(event)
    
    async def publish_email_verification_requested(
        self,
        user_id: int,
        email: str,
        full_name: str,
        verification_token: str,
        verification_url: str,
        expires_at: datetime,
        language_preference: str = "pt-BR",
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publica evento de verificação de email solicitada
        
        Args:
            user_id: ID do usuário
            email: Email a ser verificado
            full_name: Nome completo
            verification_token: Token de verificação
            verification_url: URL de verificação
            expires_at: Data de expiração
            language_preference: Idioma preferido
            correlation_id: ID de correlação
            
        Returns:
            bool: True se publicado com sucesso
        """
        event = EmailVerificationRequestedEvent.create(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            email=email,
            full_name=full_name,
            verification_token=verification_token,
            verification_url=verification_url,
            expires_at=expires_at,
            language_preference=language_preference,
            correlation_id=correlation_id
        )
        
        return await self.publish_event(event)
    
    async def publish_password_reset_requested(
        self,
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
    ) -> bool:
        """
        Publica evento de reset de senha solicitado
        
        Args:
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
            bool: True se publicado com sucesso
        """
        event = PasswordResetRequestedEvent.create(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            email=email,
            full_name=full_name,
            reset_token=reset_token,
            reset_url=reset_url,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            language_preference=language_preference,
            correlation_id=correlation_id
        )
        
        return await self.publish_event(event)
    
    async def publish_user_profile_updated(
        self,
        user_id: int,
        email: str,
        full_name: str,
        updated_fields: dict,
        language_preference: str = "pt-BR",
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publica evento de perfil atualizado
        
        Args:
            user_id: ID do usuário
            email: Email do usuário
            full_name: Nome completo
            updated_fields: Campos atualizados
            language_preference: Idioma preferido
            correlation_id: ID de correlação
            
        Returns:
            bool: True se publicado com sucesso
        """
        event = UserProfileUpdatedEvent.create(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            email=email,
            full_name=full_name,
            updated_fields=updated_fields,
            language_preference=language_preference,
            correlation_id=correlation_id
        )
        
        return await self.publish_event(event)
    
    async def test_connection(self) -> bool:
        """
        Testa a conexão do Event Bus
        
        Returns:
            bool: True se conectado
        """
        return await event_bus.test_connection()
    
    async def get_connection_info(self) -> dict:
        """
        Obtém informações da conexão
        
        Returns:
            dict: Informações da conexão
        """
        return await event_bus.get_info()


# Instância global do publisher
event_publisher = EventPublisher()