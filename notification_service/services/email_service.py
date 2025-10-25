"""
Email Service - Serviço de Envio de Emails
Notification Service - Plataforma VOD
"""

import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from pathlib import Path
import aiosmtplib

from config.settings import settings
from .template_service import TemplateService


logger = logging.getLogger(__name__)


class EmailService:
    """
    Serviço responsável pelo envio de emails via SMTP
    """
    
    def __init__(self):
        """
        Inicializa o serviço de email
        """
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.use_tls = settings.smtp_use_tls
        self.use_ssl = settings.smtp_use_ssl
        self.timeout = settings.smtp_timeout
        self.sender_email = settings.from_email
        self.sender_name = settings.from_name
        
        # Inicializa o serviço de templates
        self.template_service = TemplateService()
        
        # Configurações de retry
        self.max_retries = settings.email_max_retries
        self.retry_delay = settings.email_retry_delay
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Envia um email genérico
        """
        try:
            # Cria a mensagem
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            
            if cc:
                message["Cc"] = ", ".join(cc)
            
            # Adiciona conteúdo texto
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)
            
            # Adiciona conteúdo HTML
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # Adiciona anexos
            if attachments:
                for attachment_path in attachments:
                    await self._add_attachment(message, attachment_path)
            
            # Prepara lista de destinatários
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Envia o email com retry
            success = await self._send_with_retry(message, recipients)
            
            if success:
                logger.info(f"Email enviado com sucesso para: {to_email}")
            else:
                logger.error(f"Falha ao enviar email para: {to_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")
            return False
    
    async def send_template_email(
        self,
        to_email: str,
        template_name: str,
        template_data: Dict[str, Any],
        subject: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Envia um email usando template
        """
        try:
            # Renderiza o template
            html_content, text_content, email_subject = await self.template_service.render_template(
                template_name, template_data
            )
            
            # Usa o subject do template se não fornecido
            final_subject = subject or email_subject
            
            return await self.send_email(
                to_email=to_email,
                subject=final_subject,
                html_content=html_content,
                text_content=text_content,
                attachments=attachments
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar email com template: {str(e)}")
            return False
    
    # ==================== EMAILS ESPECÍFICOS ====================
    
    async def send_welcome_email(self, email: str, name: str, user_id: int) -> bool:
        """
        Envia email de boas-vindas
        """
        return await self.send_template_email(
            to_email=email,
            template_name="welcome",
            template_data={
                "name": name,
                "user_id": user_id,
                "platform_name": settings.app_name,
                "support_email": settings.from_email
            }
        )
    
    async def send_verification_email(self, email: str, name: str, verification_token: str) -> bool:
        """
        Envia email de verificação de conta
        """
        verification_url = f"{settings.frontend_url}/verify?token={verification_token}"
        
        return await self.send_template_email(
            to_email=email,
            template_name="verification",
            template_data={
                "name": name,
                "verification_url": verification_url,
                "platform_name": settings.app_name
            }
        )
    
    async def send_verification_success_email(self, email: str, name: str) -> bool:
        """
        Envia email de confirmação de verificação
        """
        return await self.send_template_email(
            to_email=email,
            template_name="verification_success",
            template_data={
                "name": name,
                "platform_name": settings.app_name,
                "login_url": f"{settings.frontend_url}/login"
            }
        )
    
    async def send_password_reset_email(self, email: str, name: str, reset_token: str) -> bool:
        """
        Envia email de reset de senha
        """
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
        
        return await self.send_template_email(
            to_email=email,
            template_name="password_reset",
            template_data={
                "name": name,
                "reset_url": reset_url,
                "platform_name": settings.app_name,
                "expiry_hours": 24
            }
        )
    
    async def send_password_changed_email(self, email: str, name: str) -> bool:
        """
        Envia email de confirmação de alteração de senha
        """
        return await self.send_template_email(
            to_email=email,
            template_name="password_changed",
            template_data={
                "name": name,
                "platform_name": settings.app_name,
                "support_email": settings.from_email,
                "timestamp": datetime.utcnow().strftime("%d/%m/%Y às %H:%M")
            }
        )
    
    async def send_profile_updated_email(self, email: str, name: str, changes: List[str]) -> bool:
        """
        Envia email de confirmação de atualização de perfil
        """
        return await self.send_template_email(
            to_email=email,
            template_name="profile_updated",
            template_data={
                "name": name,
                "changes": changes,
                "platform_name": settings.app_name,
                "timestamp": datetime.utcnow().strftime("%d/%m/%Y às %H:%M")
            }
        )
    
    async def send_payment_receipt_email(
        self, 
        email: str, 
        name: str, 
        amount: float, 
        currency: str,
        plan_name: str,
        payment_id: int
    ) -> bool:
        """
        Envia recibo de pagamento
        """
        return await self.send_template_email(
            to_email=email,
            template_name="payment_receipt",
            template_data={
                "name": name,
                "amount": f"{amount:.2f}",
                "currency": currency,
                "plan_name": plan_name,
                "payment_id": payment_id,
                "platform_name": settings.app_name,
                "payment_date": datetime.utcnow().strftime("%d/%m/%Y")
            }
        )
    
    async def send_payment_failed_email(
        self, 
        email: str, 
        name: str, 
        amount: float,
        plan_name: str,
        reason: str
    ) -> bool:
        """
        Envia notificação de falha no pagamento
        """
        return await self.send_template_email(
            to_email=email,
            template_name="payment_failed",
            template_data={
                "name": name,
                "amount": f"{amount:.2f}",
                "plan_name": plan_name,
                "reason": reason,
                "platform_name": settings.app_name,
                "retry_url": f"{settings.frontend_url}/billing"
            }
        )
    
    async def send_subscription_created_email(
        self, 
        email: str, 
        name: str, 
        plan_name: str,
        subscription_id: int
    ) -> bool:
        """
        Envia confirmação de criação de assinatura
        """
        return await self.send_template_email(
            to_email=email,
            template_name="subscription_created",
            template_data={
                "name": name,
                "plan_name": plan_name,
                "subscription_id": subscription_id,
                "platform_name": settings.app_name,
                "manage_url": f"{settings.frontend_url}/subscription"
            }
        )
    
    async def send_subscription_renewed_email(
        self, 
        email: str, 
        name: str, 
        plan_name: str,
        next_billing_date: str
    ) -> bool:
        """
        Envia confirmação de renovação de assinatura
        """
        return await self.send_template_email(
            to_email=email,
            template_name="subscription_renewed",
            template_data={
                "name": name,
                "plan_name": plan_name,
                "next_billing_date": next_billing_date,
                "platform_name": settings.app_name,
                "manage_url": f"{settings.frontend_url}/subscription"
            }
        )
    
    async def send_subscription_cancelled_email(
        self, 
        email: str, 
        name: str, 
        plan_name: str,
        end_date: str
    ) -> bool:
        """
        Envia confirmação de cancelamento de assinatura
        """
        return await self.send_template_email(
            to_email=email,
            template_name="subscription_cancelled",
            template_data={
                "name": name,
                "plan_name": plan_name,
                "end_date": end_date,
                "platform_name": settings.app_name,
                "reactivate_url": f"{settings.frontend_url}/subscription"
            }
        )
    
    async def send_subscription_expired_email(
        self, 
        email: str, 
        name: str, 
        plan_name: str
    ) -> bool:
        """
        Envia notificação de expiração de assinatura
        """
        return await self.send_template_email(
            to_email=email,
            template_name="subscription_expired",
            template_data={
                "name": name,
                "plan_name": plan_name,
                "platform_name": settings.app_name,
                "renew_url": f"{settings.frontend_url}/plans"
            }
        )
    
    async def send_content_uploaded_email(
        self, 
        email: str, 
        name: str, 
        content_title: str,
        content_id: int
    ) -> bool:
        """
        Envia confirmação de upload de conteúdo
        """
        return await self.send_template_email(
            to_email=email,
            template_name="content_uploaded",
            template_data={
                "name": name,
                "content_title": content_title,
                "content_id": content_id,
                "platform_name": settings.app_name,
                "content_url": f"{settings.frontend_url}/content/{content_id}"
            }
        )
    
    async def send_content_processed_email(
        self, 
        email: str, 
        name: str, 
        content_title: str,
        content_id: int
    ) -> bool:
        """
        Envia notificação de processamento concluído
        """
        return await self.send_template_email(
            to_email=email,
            template_name="content_processed",
            template_data={
                "name": name,
                "content_title": content_title,
                "content_id": content_id,
                "platform_name": settings.app_name,
                "content_url": f"{settings.frontend_url}/content/{content_id}"
            }
        )
    
    async def send_content_published_email(
        self, 
        email: str, 
        name: str, 
        content_title: str,
        content_id: int
    ) -> bool:
        """
        Envia confirmação de publicação de conteúdo
        """
        return await self.send_template_email(
            to_email=email,
            template_name="content_published",
            template_data={
                "name": name,
                "content_title": content_title,
                "content_id": content_id,
                "platform_name": settings.app_name,
                "content_url": f"{settings.frontend_url}/content/{content_id}",
                "share_url": f"{settings.frontend_url}/watch/{content_id}"
            }
        )
    
    async def send_security_alert_email(
        self, 
        email: str, 
        name: str, 
        alert_type: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Envia alerta de segurança
        """
        return await self.send_template_email(
            to_email=email,
            template_name="security_alert",
            template_data={
                "name": name,
                "alert_type": alert_type,
                "details": details,
                "platform_name": settings.app_name,
                "security_url": f"{settings.frontend_url}/security",
                "timestamp": datetime.utcnow().strftime("%d/%m/%Y às %H:%M")
            }
        )
    
    async def send_account_locked_email(
        self, 
        email: str, 
        name: str, 
        reason: str
    ) -> bool:
        """
        Envia notificação de conta bloqueada
        """
        return await self.send_template_email(
            to_email=email,
            template_name="account_locked",
            template_data={
                "name": name,
                "reason": reason,
                "platform_name": settings.app_name,
                "support_email": settings.from_email,
                "unlock_url": f"{settings.frontend_url}/unlock-account"
            }
        )
    
    async def send_2fa_enabled_email(self, email: str, name: str) -> bool:
        """
        Envia confirmação de ativação do 2FA
        """
        return await self.send_template_email(
            to_email=email,
            template_name="2fa_enabled",
            template_data={
                "name": name,
                "platform_name": settings.app_name,
                "timestamp": datetime.utcnow().strftime("%d/%m/%Y às %H:%M")
            }
        )
    
    async def send_conversion_completed_email(
        self, 
        email: str, 
        name: str, 
        template_data: Dict[str, Any]
    ) -> bool:
        """
        Envia notificação de conversão de vídeo concluída
        """
        return await self.send_template_email(
            to_email=email,
            template_name="conversion_completed",
            template_data={
                "user_name": name,
                **template_data
            }
        )
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    async def _send_with_retry(self, message: MIMEMultipart, recipients: List[str]) -> bool:
        """
        Envia email com sistema de retry
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Cria conexão SMTP
                if self.use_ssl:
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=self.timeout, context=context)
                else:
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout)
                    if self.use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                
                # Autentica
                server.login(self.smtp_user, self.smtp_password)
                
                # Envia email
                server.send_message(message, to_addrs=recipients)
                server.quit()
                
                return True
                
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
                
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Falha após {self.max_retries + 1} tentativas")
                    return False
        
        return False
    
    async def _add_attachment(self, message: MIMEMultipart, attachment_path: str):
        """
        Adiciona anexo ao email
        """
        try:
            file_path = Path(attachment_path)
            if not file_path.exists():
                logger.warning(f"Arquivo não encontrado: {attachment_path}")
                return
            
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {file_path.name}",
            )
            
            message.attach(part)
            
        except Exception as e:
            logger.error(f"Erro ao adicionar anexo: {str(e)}")
    
    async def test_connection(self) -> bool:
        """
        Testa a conexão SMTP com Gmail
        """
        try:
            server = aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.use_tls,
                timeout=self.timeout
            )
            
            await server.connect()
            logger.info(f"Conectado ao Gmail SMTP: {self.smtp_host}:{self.smtp_port}")
            
            await server.login(self.smtp_user, self.smtp_password)
            logger.info(f"Autenticação Gmail bem-sucedida para: {self.smtp_user}")
            
            await server.quit()
            logger.info("✅ Conexão Gmail SMTP testada com sucesso")
            return True
            
        except aiosmtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Erro de autenticação Gmail: {str(e)}")
            logger.error("💡 Dica: Verifique se você está usando uma Senha de App do Gmail")
            return False
        except aiosmtplib.SMTPConnectError as e:
            logger.error(f"❌ Erro de conexão Gmail: {str(e)}")
            logger.error("💡 Dica: Verifique sua conexão com internet e configurações de firewall")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado na conexão Gmail: {str(e)}")
            return False
    
    async def get_gmail_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre a configuração do Gmail
        """
        return {
            "provider": "Gmail SMTP",
            "host": self.smtp_host,
            "port": self.smtp_port,
            "user": self.smtp_user,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "timeout": self.timeout,
            "from_email": self.sender_email,
            "from_name": self.sender_name,
            "daily_limit": "500 emails (conta gratuita)",
            "rate_limit": "~100 emails/minuto"
        }