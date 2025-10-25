"""
Template Service - Serviço de Templates de Email
Notification Service - Plataforma VOD
"""

import logging
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
import json

from config.settings import settings


logger = logging.getLogger(__name__)


class TemplateService:
    """
    Serviço responsável por gerenciar e renderizar templates de email
    """
    
    def __init__(self):
        """
        Inicializa o serviço de templates
        """
        self.template_dir = Path(settings.template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Configura Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Cache de templates
        self._template_cache = {}
        
        # Metadados dos templates
        self._template_metadata = {}
        
        # Inicializa templates padrão
        self._ensure_default_templates()
    
    async def render_template(
        self, 
        template_name: str, 
        template_data: Dict[str, Any]
    ) -> Tuple[str, Optional[str], str]:
        """
        Renderiza um template de email
        
        Returns:
            Tuple[html_content, text_content, subject]
        """
        try:
            # Carrega metadados do template
            metadata = await self._get_template_metadata(template_name)
            
            # Renderiza HTML
            html_template = self.env.get_template(f"{template_name}.html")
            html_content = html_template.render(**template_data)
            
            # Renderiza texto (opcional)
            text_content = None
            try:
                text_template = self.env.get_template(f"{template_name}.txt")
                text_content = text_template.render(**template_data)
            except TemplateNotFound:
                # Template de texto é opcional
                pass
            
            # Renderiza subject
            subject = metadata.get("subject", "Notificação")
            if "{{" in subject:
                subject_template = Template(subject)
                subject = subject_template.render(**template_data)
            
            logger.info(f"Template renderizado com sucesso: {template_name}")
            return html_content, text_content, subject
            
        except TemplateNotFound:
            logger.error(f"Template não encontrado: {template_name}")
            raise
        except Exception as e:
            logger.error(f"Erro ao renderizar template {template_name}: {str(e)}")
            raise
    
    async def _get_template_metadata(self, template_name: str) -> Dict[str, Any]:
        """
        Obtém metadados do template
        """
        if template_name not in self._template_metadata:
            metadata_file = self.template_dir / f"{template_name}.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self._template_metadata[template_name] = json.load(f)
            else:
                # Metadados padrão
                self._template_metadata[template_name] = {
                    "subject": "Notificação",
                    "description": f"Template {template_name}",
                    "variables": []
                }
        
        return self._template_metadata[template_name]
    
    def _ensure_default_templates(self):
        """
        Garante que os templates padrão existam
        """
        templates = {
            "welcome": {
                "subject": "Bem-vindo à {{platform_name}}! 🎉",
                "description": "Email de boas-vindas para novos usuários",
                "variables": ["name", "platform_name", "support_email"]
            },
            "verification": {
                "subject": "Confirme seu email - {{platform_name}}",
                "description": "Email de verificação de conta",
                "variables": ["name", "verification_url", "platform_name"]
            },
            "verification_success": {
                "subject": "Email verificado com sucesso! ✅",
                "description": "Confirmação de verificação de email",
                "variables": ["name", "platform_name", "login_url"]
            },
            "password_reset": {
                "subject": "Redefinir sua senha - {{platform_name}}",
                "description": "Email de reset de senha",
                "variables": ["name", "reset_url", "platform_name", "expiry_hours"]
            },
            "password_changed": {
                "subject": "Senha alterada com sucesso 🔒",
                "description": "Confirmação de alteração de senha",
                "variables": ["name", "platform_name", "support_email", "timestamp"]
            },
            "profile_updated": {
                "subject": "Perfil atualizado - {{platform_name}}",
                "description": "Confirmação de atualização de perfil",
                "variables": ["name", "changes", "platform_name", "timestamp"]
            },
            "payment_receipt": {
                "subject": "Recibo de pagamento - {{platform_name}} 💳",
                "description": "Recibo de pagamento",
                "variables": ["name", "amount", "currency", "plan_name", "payment_id", "platform_name", "payment_date"]
            },
            "payment_failed": {
                "subject": "Falha no pagamento - {{platform_name}} ❌",
                "description": "Notificação de falha no pagamento",
                "variables": ["name", "amount", "plan_name", "reason", "platform_name", "retry_url"]
            },
            "subscription_created": {
                "subject": "Assinatura ativada! 🚀 - {{platform_name}}",
                "description": "Confirmação de criação de assinatura",
                "variables": ["name", "plan_name", "subscription_id", "platform_name", "manage_url"]
            },
            "subscription_renewed": {
                "subject": "Assinatura renovada 🔄 - {{platform_name}}",
                "description": "Confirmação de renovação de assinatura",
                "variables": ["name", "plan_name", "next_billing_date", "platform_name", "manage_url"]
            },
            "subscription_cancelled": {
                "subject": "Assinatura cancelada - {{platform_name}}",
                "description": "Confirmação de cancelamento de assinatura",
                "variables": ["name", "plan_name", "end_date", "platform_name", "reactivate_url"]
            },
            "subscription_expired": {
                "subject": "Assinatura expirada - {{platform_name}} ⏰",
                "description": "Notificação de expiração de assinatura",
                "variables": ["name", "plan_name", "platform_name", "renew_url"]
            },
            "content_uploaded": {
                "subject": "Upload concluído! 📹 - {{platform_name}}",
                "description": "Confirmação de upload de conteúdo",
                "variables": ["name", "content_title", "content_id", "platform_name", "content_url"]
            },
            "content_processed": {
                "subject": "Vídeo processado! ✅ - {{platform_name}}",
                "description": "Notificação de processamento concluído",
                "variables": ["name", "content_title", "content_id", "platform_name", "content_url"]
            },
            "content_published": {
                "subject": "Conteúdo publicado! 🎬 - {{platform_name}}",
                "description": "Confirmação de publicação de conteúdo",
                "variables": ["name", "content_title", "content_id", "platform_name", "content_url", "share_url"]
            },
            "security_alert": {
                "subject": "Alerta de Segurança 🚨 - {{platform_name}}",
                "description": "Alerta de segurança",
                "variables": ["name", "alert_type", "details", "platform_name", "security_url", "timestamp"]
            },
            "account_locked": {
                "subject": "Conta temporariamente bloqueada 🔒 - {{platform_name}}",
                "description": "Notificação de conta bloqueada",
                "variables": ["name", "reason", "platform_name", "support_email", "unlock_url"]
            },
            "2fa_enabled": {
                "subject": "Autenticação de dois fatores ativada! 🔐",
                "description": "Confirmação de ativação do 2FA",
                "variables": ["name", "platform_name", "security_url", "timestamp"]
            }
        }
        
        # Cria metadados dos templates
        for template_name, metadata in templates.items():
            metadata_file = self.template_dir / f"{template_name}.json"
            if not metadata_file.exists():
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Metadados criados para template: {template_name}")
    
    async def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Lista todos os templates disponíveis
        """
        templates = {}
        
        for metadata_file in self.template_dir.glob("*.json"):
            template_name = metadata_file.stem
            templates[template_name] = await self._get_template_metadata(template_name)
        
        return templates
    
    async def template_exists(self, template_name: str) -> bool:
        """
        Verifica se um template existe
        """
        html_file = self.template_dir / f"{template_name}.html"
        return html_file.exists()
    
    async def validate_template_data(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """
        Valida se os dados fornecidos são suficientes para o template
        """
        try:
            metadata = await self._get_template_metadata(template_name)
            required_vars = metadata.get("variables", [])
            
            missing_vars = [var for var in required_vars if var not in template_data]
            
            if missing_vars:
                logger.warning(f"Variáveis faltando no template {template_name}: {missing_vars}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar dados do template: {str(e)}")
            return False