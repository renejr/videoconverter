"""
Event Handlers - Processamento de Eventos
Notification Service - Plataforma VOD
"""

import logging
from typing import Dict, Any, TYPE_CHECKING
from datetime import datetime

from .schemas import (
    EventType, UserEvent, PaymentEvent, 
    ContentEvent, SecurityEvent, BaseEvent
)
from services.email_service import EmailService

if TYPE_CHECKING:
    from services.notification_service import NotificationService


logger = logging.getLogger(__name__)


class EventHandlers:
    """
    Classe responsável por processar todos os eventos recebidos
    """
    
    def __init__(self, email_service: EmailService, notification_service: "NotificationService"):
        """
        Inicializa os handlers com os serviços necessários
        """
        self.email_service = email_service
        self.notification_service = notification_service
        
        # Mapeamento de eventos para handlers
        self.handlers = {
            # Eventos de Usuário
            EventType.USER_REGISTERED: self._handle_user_registered,
            EventType.USER_VERIFIED: self._handle_user_verified,
            EventType.USER_LOGIN: self._handle_user_login,
            EventType.USER_PASSWORD_RESET: self._handle_password_reset,
            EventType.USER_PASSWORD_CHANGED: self._handle_password_changed,
            EventType.USER_PROFILE_UPDATED: self._handle_profile_updated,
            
            # Eventos de Pagamento
            EventType.PAYMENT_COMPLETED: self._handle_payment_completed,
            EventType.PAYMENT_FAILED: self._handle_payment_failed,
            EventType.SUBSCRIPTION_CREATED: self._handle_subscription_created,
            EventType.SUBSCRIPTION_RENEWED: self._handle_subscription_renewed,
            EventType.SUBSCRIPTION_CANCELLED: self._handle_subscription_cancelled,
            EventType.SUBSCRIPTION_EXPIRED: self._handle_subscription_expired,
            
            # Eventos de Conteúdo
            EventType.CONTENT_UPLOADED: self._handle_content_uploaded,
            EventType.CONTENT_PROCESSED: self._handle_content_processed,
            EventType.CONTENT_PUBLISHED: self._handle_content_published,
            
            # Eventos de Segurança
            EventType.SECURITY_SUSPICIOUS_LOGIN: self._handle_suspicious_login,
            EventType.SECURITY_ACCOUNT_LOCKED: self._handle_account_locked,
            EventType.SECURITY_2FA_ENABLED: self._handle_2fa_enabled,
        }
    
    async def handle_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Processa um evento recebido
        """
        try:
            event_type = EventType(event_data.get("event_type"))
            handler = self.handlers.get(event_type)
            
            if not handler:
                logger.warning(f"Handler não encontrado para evento: {event_type}")
                return False
            
            # Executa o handler específico
            await handler(event_data)
            
            logger.info(f"Evento processado com sucesso: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar evento: {str(e)}")
            return False
    
    # ==================== HANDLERS DE USUÁRIO ====================
    
    async def _handle_user_registered(self, event_data: Dict[str, Any]):
        """
        Processa evento de registro de usuário
        """
        user_event = UserEvent(**event_data)
        
        # Envia email de boas-vindas
        await self.email_service.send_welcome_email(
            email=user_event.email,
            name=user_event.name or "Usuário",
            user_id=user_event.user_id
        )
        
        # Registra notificação
        await self.notification_service.create_notification(
            type=NotificationType.WELCOME,
            recipient=user_event.email,
            channel="email",
            priority=NotificationPriority.HIGH,
            template_name="welcome_email",
            template_data={
                "name": user_event.name,
                "user_id": user_event.user_id
            }
        )
    
    async def _handle_user_verified(self, event_data: Dict[str, Any]):
        """
        Processa evento de verificação de usuário
        """
        user_event = UserEvent(**event_data)
        
        # Envia email de confirmação de verificação
        await self.email_service.send_verification_success_email(
            email=user_event.email,
            name=user_event.name or "Usuário"
        )
    
    async def _handle_user_login(self, event_data: Dict[str, Any]):
        """
        Processa evento de login (apenas para logins suspeitos)
        """
        user_event = UserEvent(**event_data)
        
        # Verifica se é um login suspeito
        if user_event.metadata and user_event.metadata.get("suspicious", False):
            await self.email_service.send_security_alert_email(
                email=user_event.email,
                name=user_event.name or "Usuário",
                alert_type="Login Suspeito",
                details=user_event.metadata
            )
    
    async def _handle_password_reset(self, event_data: Dict[str, Any]):
        """
        Processa evento de reset de senha
        """
        user_event = UserEvent(**event_data)
        
        # Envia email com token de reset
        reset_token = user_event.user_data.get("reset_token")
        if reset_token:
            await self.email_service.send_password_reset_email(
                email=user_event.email,
                name=user_event.name or "Usuário",
                reset_token=reset_token
            )
    
    async def _handle_password_changed(self, event_data: Dict[str, Any]):
        """
        Processa evento de alteração de senha
        """
        user_event = UserEvent(**event_data)
        
        # Envia confirmação de alteração de senha
        await self.email_service.send_password_changed_email(
            email=user_event.email,
            name=user_event.name or "Usuário"
        )
    
    async def _handle_profile_updated(self, event_data: Dict[str, Any]):
        """
        Processa evento de atualização de perfil
        """
        user_event = UserEvent(**event_data)
        
        # Envia confirmação de atualização (apenas para mudanças importantes)
        important_changes = user_event.user_data.get("important_changes", [])
        if important_changes:
            await self.email_service.send_profile_updated_email(
                email=user_event.email,
                name=user_event.name or "Usuário",
                changes=important_changes
            )
    
    # ==================== HANDLERS DE PAGAMENTO ====================
    
    async def _handle_payment_completed(self, event_data: Dict[str, Any]):
        """
        Processa evento de pagamento concluído
        """
        payment_event = PaymentEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(payment_event.user_id)
        
        # Envia recibo de pagamento
        await self.email_service.send_payment_receipt_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            amount=payment_event.amount,
            currency=payment_event.currency,
            plan_name=payment_event.plan_name,
            payment_id=payment_event.payment_id
        )
    
    async def _handle_payment_failed(self, event_data: Dict[str, Any]):
        """
        Processa evento de falha no pagamento
        """
        payment_event = PaymentEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(payment_event.user_id)
        
        # Envia notificação de falha
        await self.email_service.send_payment_failed_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            amount=payment_event.amount,
            plan_name=payment_event.plan_name,
            reason=payment_event.payment_data.get("failure_reason", "Erro desconhecido")
        )
    
    async def _handle_subscription_created(self, event_data: Dict[str, Any]):
        """
        Processa evento de criação de assinatura
        """
        payment_event = PaymentEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(payment_event.user_id)
        
        # Envia confirmação de assinatura
        await self.email_service.send_subscription_created_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            plan_name=payment_event.plan_name,
            subscription_id=payment_event.subscription_id
        )
    
    async def _handle_subscription_renewed(self, event_data: Dict[str, Any]):
        """
        Processa evento de renovação de assinatura
        """
        payment_event = PaymentEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(payment_event.user_id)
        
        # Envia confirmação de renovação
        await self.email_service.send_subscription_renewed_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            plan_name=payment_event.plan_name,
            next_billing_date=payment_event.payment_data.get("next_billing_date")
        )
    
    async def _handle_subscription_cancelled(self, event_data: Dict[str, Any]):
        """
        Processa evento de cancelamento de assinatura
        """
        payment_event = PaymentEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(payment_event.user_id)
        
        # Envia confirmação de cancelamento
        await self.email_service.send_subscription_cancelled_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            plan_name=payment_event.plan_name,
            end_date=payment_event.payment_data.get("end_date")
        )
    
    async def _handle_subscription_expired(self, event_data: Dict[str, Any]):
        """
        Processa evento de expiração de assinatura
        """
        payment_event = PaymentEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(payment_event.user_id)
        
        # Envia notificação de expiração
        await self.email_service.send_subscription_expired_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            plan_name=payment_event.plan_name
        )
    
    # ==================== HANDLERS DE CONTEÚDO ====================
    
    async def _handle_content_uploaded(self, event_data: Dict[str, Any]):
        """
        Processa evento de upload de conteúdo
        """
        content_event = ContentEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(content_event.user_id)
        
        # Envia confirmação de upload
        await self.email_service.send_content_uploaded_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            content_title=content_event.content_title,
            content_id=content_event.content_id
        )
    
    async def _handle_content_processed(self, event_data: Dict[str, Any]):
        """
        Processa evento de processamento de conteúdo
        """
        content_event = ContentEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(content_event.user_id)
        
        # Envia notificação de processamento concluído
        await self.email_service.send_content_processed_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            content_title=content_event.content_title,
            content_id=content_event.content_id
        )
    
    async def _handle_content_published(self, event_data: Dict[str, Any]):
        """
        Processa evento de publicação de conteúdo
        """
        content_event = ContentEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(content_event.user_id)
        
        # Envia confirmação de publicação
        await self.email_service.send_content_published_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            content_title=content_event.content_title,
            content_id=content_event.content_id
        )
    
    # ==================== HANDLERS DE SEGURANÇA ====================
    
    async def _handle_suspicious_login(self, event_data: Dict[str, Any]):
        """
        Processa evento de login suspeito
        """
        security_event = SecurityEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(security_event.user_id)
        
        # Envia alerta de segurança
        await self.email_service.send_security_alert_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            alert_type="Login Suspeito",
            details={
                "ip_address": security_event.ip_address,
                "location": security_event.location,
                "timestamp": security_event.timestamp.isoformat()
            }
        )
    
    async def _handle_account_locked(self, event_data: Dict[str, Any]):
        """
        Processa evento de conta bloqueada
        """
        security_event = SecurityEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(security_event.user_id)
        
        # Envia notificação de conta bloqueada
        await self.email_service.send_account_locked_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário"),
            reason=security_event.security_data.get("reason", "Múltiplas tentativas de login")
        )
    
    async def _handle_2fa_enabled(self, event_data: Dict[str, Any]):
        """
        Processa evento de ativação do 2FA
        """
        security_event = SecurityEvent(**event_data)
        
        # Busca dados do usuário
        user_data = await self._get_user_data(security_event.user_id)
        
        # Envia confirmação de ativação do 2FA
        await self.email_service.send_2fa_enabled_email(
            email=user_data.get("email"),
            name=user_data.get("name", "Usuário")
        )
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    async def _get_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        Busca dados do usuário (implementar integração com User Service)
        """
        # TODO: Implementar chamada para User Service via API ou Event Bus
        # Por enquanto, retorna dados mock
        return {
            "email": f"user{user_id}@example.com",
            "name": f"Usuário {user_id}"
        }