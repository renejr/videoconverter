"""
User Event Handlers - Notification Service
Handlers para processar eventos relacionados a usuários
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from services.email_service import EmailService
from services.template_service import TemplateService
from models.notification import Notification, NotificationType, NotificationStatus
from database.connection import get_db_session

logger = logging.getLogger(__name__)


class BaseEventHandler:
    """
    Classe base para handlers de eventos
    """
    
    def __init__(self):
        """
        Inicializa o handler base
        """
        self.email_service = EmailService()
        self.template_service = TemplateService()
    
    async def handle_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Processa um evento
        
        Args:
            event_data: Dados do evento
            
        Returns:
            bool: True se processado com sucesso
        """
        try:
            # Log do evento recebido
            event_type = event_data.get("event_type")
            event_id = event_data.get("event_id")
            user_id = event_data.get("user_id")
            
            logger.info(
                f"📨 Processando evento: {event_type} "
                f"(ID: {event_id}, User: {user_id})"
            )
            
            # Processar evento específico
            success = await self._process_event(event_data)
            
            if success:
                logger.info(
                    f"✅ Evento processado com sucesso: {event_type} "
                    f"(ID: {event_id})"
                )
            else:
                logger.error(
                    f"❌ Falha ao processar evento: {event_type} "
                    f"(ID: {event_id})"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar evento: {str(e)}")
            return False
    
    async def _process_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Método abstrato para processar evento específico
        
        Args:
            event_data: Dados do evento
            
        Returns:
            bool: True se processado com sucesso
        """
        raise NotImplementedError("Subclasses devem implementar _process_event")
    
    async def _create_notification_record(
        self,
        user_id: int,
        notification_type: NotificationType,
        template_name: str,
        recipient_email: str,
        template_data: Dict[str, Any],
        event_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Optional[Notification]:
        """
        Cria registro de notificação no banco
        
        Args:
            user_id: ID do usuário
            notification_type: Tipo da notificação
            template_name: Nome do template
            recipient_email: Email do destinatário
            template_data: Dados do template
            event_id: ID do evento
            correlation_id: ID de correlação
            
        Returns:
            Notification: Registro criado ou None se erro
        """
        try:
            async with get_db_session() as session:
                notification = Notification(
                    user_id=user_id,
                    type=notification_type,
                    template_name=template_name,
                    recipient_email=recipient_email,
                    template_data=template_data,
                    status=NotificationStatus.PENDING,
                    event_id=event_id,
                    correlation_id=correlation_id,
                    created_at=datetime.utcnow()
                )
                
                session.add(notification)
                await session.commit()
                await session.refresh(notification)
                
                return notification
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar registro de notificação: {str(e)}")
            return None


class UserRegisteredHandler(BaseEventHandler):
    """
    Handler para evento de usuário registrado
    """
    
    async def _process_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Processa evento de usuário registrado
        
        Args:
            event_data: Dados do evento
            
        Returns:
            bool: True se processado com sucesso
        """
        try:
            # Extrair dados do evento
            user_id = event_data.get("user_id")
            email = event_data.get("email")
            full_name = event_data.get("full_name")
            language_preference = event_data.get("language_preference", "pt-BR")
            event_id = event_data.get("event_id")
            correlation_id = event_data.get("correlation_id")
            
            # Validar dados obrigatórios
            if not all([user_id, email, full_name]):
                logger.error("❌ Dados obrigatórios ausentes no evento USER_REGISTERED")
                return False
            
            # Preparar dados do template
            template_data = {
                "user_name": full_name,
                "user_email": email,
                "platform_name": "VidConv",
                "welcome_message": "Bem-vindo à nossa plataforma!",
                "getting_started_url": "https://vidconv.com/getting-started",
                "support_url": "https://vidconv.com/support",
                "unsubscribe_url": f"https://vidconv.com/unsubscribe?user_id={user_id}",
                "current_year": datetime.now().year
            }
            
            # Criar registro de notificação
            notification = await self._create_notification_record(
                user_id=user_id,
                notification_type=NotificationType.WELCOME,
                template_name="welcome_email.html",
                recipient_email=email,
                template_data=template_data,
                event_id=event_id,
                correlation_id=correlation_id
            )
            
            if not notification:
                return False
            
            # Enviar email de boas-vindas
            success = await self.email_service.send_template_email(
                template_name="welcome_email.html",
                recipient_email=email,
                subject="Bem-vindo ao VidConv! 🎉",
                template_data=template_data,
                notification_id=notification.id
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar USER_REGISTERED: {str(e)}")
            return False


class EmailVerificationRequestedHandler(BaseEventHandler):
    """
    Handler para evento de verificação de email solicitada
    """
    
    async def _process_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Processa evento de verificação de email
        
        Args:
            event_data: Dados do evento
            
        Returns:
            bool: True se processado com sucesso
        """
        try:
            # Extrair dados do evento
            user_id = event_data.get("user_id")
            email = event_data.get("email")
            full_name = event_data.get("full_name")
            verification_token = event_data.get("verification_token")
            verification_url = event_data.get("verification_url")
            expires_at = event_data.get("expires_at")
            language_preference = event_data.get("language_preference", "pt-BR")
            event_id = event_data.get("event_id")
            correlation_id = event_data.get("correlation_id")
            
            # Validar dados obrigatórios
            if not all([user_id, email, full_name, verification_token, verification_url]):
                logger.error("❌ Dados obrigatórios ausentes no evento EMAIL_VERIFICATION_REQUESTED")
                return False
            
            # Converter data de expiração
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            # Preparar dados do template
            template_data = {
                "user_name": full_name,
                "user_email": email,
                "platform_name": "VidConv",
                "verification_url": verification_url,
                "verification_token": verification_token,
                "expires_at": expires_at.strftime("%d/%m/%Y às %H:%M") if expires_at else "24 horas",
                "support_url": "https://vidconv.com/support",
                "current_year": datetime.now().year
            }
            
            # Criar registro de notificação
            notification = await self._create_notification_record(
                user_id=user_id,
                notification_type=NotificationType.EMAIL_VERIFICATION,
                template_name="email_verification.html",
                recipient_email=email,
                template_data=template_data,
                event_id=event_id,
                correlation_id=correlation_id
            )
            
            if not notification:
                return False
            
            # Enviar email de verificação
            success = await self.email_service.send_template_email(
                template_name="email_verification.html",
                recipient_email=email,
                subject="Verifique seu email - VidConv 📧",
                template_data=template_data,
                notification_id=notification.id
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar EMAIL_VERIFICATION_REQUESTED: {str(e)}")
            return False


class PasswordResetRequestedHandler(BaseEventHandler):
    """
    Handler para evento de reset de senha solicitado
    """
    
    async def _process_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Processa evento de reset de senha
        
        Args:
            event_data: Dados do evento
            
        Returns:
            bool: True se processado com sucesso
        """
        try:
            # Extrair dados do evento
            user_id = event_data.get("user_id")
            email = event_data.get("email")
            full_name = event_data.get("full_name")
            reset_token = event_data.get("reset_token")
            reset_url = event_data.get("reset_url")
            expires_at = event_data.get("expires_at")
            ip_address = event_data.get("ip_address")
            user_agent = event_data.get("user_agent")
            language_preference = event_data.get("language_preference", "pt-BR")
            event_id = event_data.get("event_id")
            correlation_id = event_data.get("correlation_id")
            
            # Validar dados obrigatórios
            if not all([user_id, email, full_name, reset_token, reset_url]):
                logger.error("❌ Dados obrigatórios ausentes no evento PASSWORD_RESET_REQUESTED")
                return False
            
            # Converter data de expiração
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            # Preparar dados do template
            template_data = {
                "user_name": full_name,
                "user_email": email,
                "platform_name": "VidConv",
                "reset_url": reset_url,
                "reset_token": reset_token,
                "expires_at": expires_at.strftime("%d/%m/%Y às %H:%M") if expires_at else "1 hora",
                "request_timestamp": datetime.now().strftime("%d/%m/%Y às %H:%M"),
                "request_ip": ip_address or "Não disponível",
                "request_browser": user_agent or "Não disponível",
                "support_url": "https://vidconv.com/support",
                "security_url": "https://vidconv.com/security",
                "current_year": datetime.now().year
            }
            
            # Criar registro de notificação
            notification = await self._create_notification_record(
                user_id=user_id,
                notification_type=NotificationType.PASSWORD_RESET,
                template_name="password_reset.html",
                recipient_email=email,
                template_data=template_data,
                event_id=event_id,
                correlation_id=correlation_id
            )
            
            if not notification:
                return False
            
            # Enviar email de reset de senha
            success = await self.email_service.send_template_email(
                template_name="password_reset.html",
                recipient_email=email,
                subject="Reset de senha solicitado - VidConv 🔐",
                template_data=template_data,
                notification_id=notification.id
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar PASSWORD_RESET_REQUESTED: {str(e)}")
            return False


class UserProfileUpdatedHandler(BaseEventHandler):
    """
    Handler para evento de perfil atualizado
    """
    
    async def _process_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Processa evento de perfil atualizado
        
        Args:
            event_data: Dados do evento
            
        Returns:
            bool: True se processado com sucesso
        """
        try:
            # Extrair dados do evento
            user_id = event_data.get("user_id")
            email = event_data.get("email")
            full_name = event_data.get("full_name")
            updated_fields = event_data.get("updated_fields", {})
            language_preference = event_data.get("language_preference", "pt-BR")
            event_id = event_data.get("event_id")
            correlation_id = event_data.get("correlation_id")
            
            # Validar dados obrigatórios
            if not all([user_id, email, full_name]):
                logger.error("❌ Dados obrigatórios ausentes no evento USER_PROFILE_UPDATED")
                return False
            
            # Verificar se há campos relevantes para notificação
            important_fields = ["email", "password", "phone", "security_settings"]
            has_important_changes = any(field in updated_fields for field in important_fields)
            
            if not has_important_changes:
                logger.info(f"📝 Perfil atualizado sem campos importantes (User: {user_id})")
                return True  # Sucesso, mas sem necessidade de notificação
            
            # Preparar lista de alterações
            changes_list = []
            field_names = {
                "email": "Email",
                "password": "Senha",
                "phone": "Telefone",
                "full_name": "Nome completo",
                "security_settings": "Configurações de segurança"
            }
            
            for field in updated_fields.keys():
                if field in field_names:
                    changes_list.append(field_names[field])
            
            # Preparar dados do template
            template_data = {
                "user_name": full_name,
                "user_email": email,
                "platform_name": "VidConv",
                "updated_fields": changes_list,
                "update_timestamp": datetime.now().strftime("%d/%m/%Y às %H:%M"),
                "security_url": "https://vidconv.com/security",
                "support_url": "https://vidconv.com/support",
                "account_url": "https://vidconv.com/account",
                "current_year": datetime.now().year
            }
            
            # Criar registro de notificação
            notification = await self._create_notification_record(
                user_id=user_id,
                notification_type=NotificationType.PROFILE_UPDATE,
                template_name="profile_updated.html",
                recipient_email=email,
                template_data=template_data,
                event_id=event_id,
                correlation_id=correlation_id
            )
            
            if not notification:
                return False
            
            # Enviar email de notificação de alteração
            success = await self.email_service.send_template_email(
                template_name="profile_updated.html",
                recipient_email=email,
                subject="Perfil atualizado - VidConv 👤",
                template_data=template_data,
                notification_id=notification.id
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar USER_PROFILE_UPDATED: {str(e)}")
            return False