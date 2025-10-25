"""
User Event Handlers - Notification Service
Handlers específicos para eventos vindos do User Service
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class UserEventHandlers:
    """
    Classe responsável por processar eventos vindos do User Service
    """
    
    def __init__(self, email_service=None):
        """
        Inicializa os handlers com os serviços necessários
        
        Args:
            email_service: Serviço de email para envio de notificações
        """
        self.email_service = email_service
        
        # Mapeamento de eventos para handlers
        self.handlers = {
            "user.registered": self._handle_user_registered,
            "user.email_verification_requested": self._handle_email_verification_requested,
            "user.password_reset_requested": self._handle_password_reset_requested,
            "user.profile_updated": self._handle_user_profile_updated,
            "user.activated": self._handle_user_activated,
            "user.deactivated": self._handle_user_deactivated,
            "user.email_verified": self._handle_email_verified,
            "user.password_changed": self._handle_password_changed,
        }
    
    async def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Processa um evento baseado no seu tipo
        
        Args:
            event_type: Tipo do evento
            event_data: Dados do evento
            
        Returns:
            bool: True se processado com sucesso, False caso contrário
        """
        try:
            logger.info(f"📨 Processando evento: {event_type}")
            
            # Busca o handler apropriado
            handler = self.handlers.get(event_type)
            if not handler:
                logger.warning(f"⚠️ Handler não encontrado para evento: {event_type}")
                return False
            
            # Executa o handler
            await handler(event_data)
            logger.info(f"✅ Evento {event_type} processado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar evento {event_type}: {str(e)}")
            return False
    
    async def _handle_user_registered(self, event_data: Dict[str, Any]):
        """
        Processa evento de usuário registrado
        Envia email de boas-vindas e verificação
        """
        try:
            data = event_data.get('data', {})
            user_id = event_data.get('user_id')
            email = data.get('email')
            full_name = data.get('full_name', 'Usuário')
            
            logger.info(f"👤 Novo usuário registrado: {email} (ID: {user_id})")
            
            # TODO: Enviar email de boas-vindas
            if self.email_service:
                await self._send_welcome_email(email, full_name, user_id)
            
            # Log da ação
            logger.info(f"📧 Email de boas-vindas enviado para: {email}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar registro de usuário: {str(e)}")
            raise
    
    async def _handle_email_verification_requested(self, event_data: Dict[str, Any]):
        """
        Processa solicitação de verificação de email
        Envia email com link de verificação
        """
        try:
            data = event_data.get('data', {})
            user_id = event_data.get('user_id')
            email = data.get('email')
            full_name = data.get('full_name', 'Usuário')
            verification_token = data.get('verification_token')
            verification_url = data.get('verification_url')
            expires_at = data.get('expires_at')
            
            logger.info(f"📧 Verificação de email solicitada para: {email}")
            
            # TODO: Enviar email de verificação
            if self.email_service:
                await self._send_verification_email(
                    email, full_name, verification_token
                )
            
            logger.info(f"✅ Email de verificação enviado para: {email}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar verificação de email: {str(e)}")
            raise
    
    async def _handle_password_reset_requested(self, event_data: Dict[str, Any]):
        """
        Processa solicitação de reset de senha
        Envia email com link de reset
        """
        try:
            data = event_data.get('data', {})
            user_id = event_data.get('user_id')
            email = data.get('email')
            full_name = data.get('full_name', 'Usuário')
            reset_token = data.get('reset_token')
            reset_url = data.get('reset_url')
            expires_at = data.get('expires_at')
            ip_address = data.get('ip_address')
            
            logger.info(f"🔐 Reset de senha solicitado para: {email} (IP: {ip_address})")
            
            # TODO: Enviar email de reset de senha
            if self.email_service:
                await self._send_password_reset_email(
                    email, full_name, reset_token
                )
            
            logger.info(f"✅ Email de reset de senha enviado para: {email}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar reset de senha: {str(e)}")
            raise
    
    async def _handle_user_profile_updated(self, event_data: Dict[str, Any]):
        """
        Processa atualização de perfil do usuário
        Envia notificação sobre as alterações
        """
        try:
            data = event_data.get('data', {})
            user_id = event_data.get('user_id')
            email = data.get('email')
            full_name = data.get('full_name', 'Usuário')
            updated_fields = data.get('updated_fields', {})
            
            logger.info(f"👤 Perfil atualizado para usuário: {email}")
            logger.info(f"📝 Campos alterados: {list(updated_fields.keys())}")
            
            # TODO: Enviar notificação de alteração de perfil
            if self.email_service and self._should_notify_profile_update(updated_fields):
                await self._send_profile_update_notification(
                    email, full_name, updated_fields
                )
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar atualização de perfil: {str(e)}")
            raise
    
    async def _handle_user_activated(self, event_data: Dict[str, Any]):
        """
        Processa ativação de usuário
        """
        try:
            data = event_data.get('data', {})
            user_id = event_data.get('user_id')
            email = data.get('email')
            
            logger.info(f"✅ Usuário ativado: {email} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar ativação de usuário: {str(e)}")
            raise
    
    async def _handle_user_deactivated(self, event_data: Dict[str, Any]):
        """
        Processa desativação de usuário
        """
        try:
            data = event_data.get('data', {})
            user_id = event_data.get('user_id')
            email = data.get('email')
            
            logger.info(f"❌ Usuário desativado: {email} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar desativação de usuário: {str(e)}")
            raise
    
    async def _handle_email_verified(self, event_data: Dict[str, Any]):
        """
        Processa verificação de email confirmada
        """
        try:
            data = event_data.get('data', {})
            user_id = event_data.get('user_id')
            email = data.get('email')
            
            logger.info(f"✅ Email verificado: {email} (ID: {user_id})")
            
            # TODO: Enviar email de confirmação de verificação
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar verificação de email: {str(e)}")
            raise
    
    async def _handle_password_changed(self, event_data: Dict[str, Any]):
        """
        Processa alteração de senha
        """
        try:
            data = event_data.get('data', {})
            user_id = event_data.get('user_id')
            email = data.get('email')
            
            logger.info(f"🔐 Senha alterada para usuário: {email} (ID: {user_id})")
            
            # TODO: Enviar notificação de alteração de senha
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar alteração de senha: {str(e)}")
            raise
    
    # Métodos auxiliares para envio de emails (serão implementados com templates)
    
    async def _send_welcome_email(self, email: str, name: str, user_id: int):
        """Envia email de boas-vindas"""
        try:
            logger.info(f"📧 Enviando email de boas-vindas para {email}")
            
            if self.email_service:
                success = await self.email_service.send_welcome_email(
                    email=email,
                    name=name,
                    user_id=user_id
                )
                if success:
                    logger.info(f"✅ Email de boas-vindas enviado para {email}")
                else:
                    logger.error(f"❌ Falha ao enviar email de boas-vindas para {email}")
            else:
                logger.warning("⚠️ EmailService não disponível")
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de boas-vindas para {email}: {str(e)}")
    
    async def _send_verification_email(self, email: str, name: str, verification_token: str):
        """Envia email de verificação"""
        try:
            logger.info(f"📧 Enviando email de verificação para {email}")
            
            if self.email_service:
                success = await self.email_service.send_verification_email(
                    email=email,
                    name=name,
                    verification_token=verification_token
                )
                if success:
                    logger.info(f"✅ Email de verificação enviado para {email}")
                else:
                    logger.error(f"❌ Falha ao enviar email de verificação para {email}")
            else:
                logger.warning("⚠️ EmailService não disponível")
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de verificação para {email}: {str(e)}")
    
    async def _send_password_reset_email(self, email: str, name: str, reset_token: str):
        """Envia email de reset de senha"""
        try:
            logger.info(f"📧 Enviando email de reset de senha para {email}")
            
            if self.email_service:
                success = await self.email_service.send_password_reset_email(
                    email=email,
                    name=name,
                    reset_token=reset_token
                )
                if success:
                    logger.info(f"✅ Email de reset de senha enviado para {email}")
                else:
                    logger.error(f"❌ Falha ao enviar email de reset de senha para {email}")
            else:
                logger.warning("⚠️ EmailService não disponível")
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de reset de senha para {email}: {str(e)}")
    
    async def _send_profile_update_notification(self, email: str, name: str, changes: dict):
        """Envia notificação de atualização de perfil"""
        try:
            logger.info(f"📧 Enviando notificação de atualização de perfil para {email}")
            
            if self.email_service:
                success = await self.email_service.send_profile_update_notification(
                    email=email,
                    name=name,
                    changes=changes
                )
                if success:
                    logger.info(f"✅ Notificação de atualização de perfil enviada para {email}")
                else:
                    logger.error(f"❌ Falha ao enviar notificação de atualização de perfil para {email}")
            else:
                logger.warning("⚠️ EmailService não disponível")
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação de atualização de perfil para {email}: {str(e)}")
    
    def _should_notify_profile_update(self, updated_fields: Dict[str, Any]) -> bool:
        """
        Determina se deve notificar sobre atualização de perfil
        baseado nos campos alterados
        """
        # Campos que requerem notificação
        important_fields = {'email', 'password', 'phone', 'security_settings'}
        return bool(set(updated_fields.keys()) & important_fields)