"""
Serviço de Segurança - User Service
Sistema de Identidade e Transações - Domínio A

Este módulo contém a lógica de negócio para
operações relacionadas à segurança e auditoria.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SecurityService:
    """
    Serviço para operações de segurança
    
    Este serviço contém toda a lógica de negócio relacionada
    à segurança, auditoria e monitoramento.
    """
    
    def __init__(self):
        """
        Inicializa o serviço de segurança
        """
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.password_min_length = 8
        self.password_require_uppercase = True
        self.password_require_lowercase = True
        self.password_require_numbers = True
        self.password_require_special = True
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Valida a força da senha
        
        Args:
            password: Senha a ser validada
            
        Returns:
            Dict[str, Any]: Resultado da validação
        """
        errors = []
        score = 0
        
        # Verificar comprimento mínimo
        if len(password) < self.password_min_length:
            errors.append(f"Senha deve ter pelo menos {self.password_min_length} caracteres")
        else:
            score += 1
        
        # Verificar letra maiúscula
        if self.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Senha deve conter pelo menos uma letra maiúscula")
        else:
            score += 1
        
        # Verificar letra minúscula
        if self.password_require_lowercase and not any(c.islower() for c in password):
            errors.append("Senha deve conter pelo menos uma letra minúscula")
        else:
            score += 1
        
        # Verificar números
        if self.password_require_numbers and not any(c.isdigit() for c in password):
            errors.append("Senha deve conter pelo menos um número")
        else:
            score += 1
        
        # Verificar caracteres especiais
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if self.password_require_special and not any(c in special_chars for c in password):
            errors.append("Senha deve conter pelo menos um caractere especial")
        else:
            score += 1
        
        # Verificar padrões comuns
        common_patterns = [
            "123456", "password", "qwerty", "abc123", "admin", "user",
            "12345678", "password123", "123456789", "welcome"
        ]
        
        if password.lower() in common_patterns:
            errors.append("Senha muito comum, escolha uma senha mais segura")
            score = max(0, score - 2)
        
        # Calcular força
        if score >= 5:
            strength = "forte"
        elif score >= 3:
            strength = "média"
        else:
            strength = "fraca"
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength": strength,
            "score": score
        }
    
    async def log_security_event(
        self,
        db: Session,
        user_id: Optional[int],
        event_type: str,
        description: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra evento de segurança
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário (opcional)
            event_type: Tipo do evento
            description: Descrição do evento
            ip_address: Endereço IP
            user_agent: User agent
            additional_data: Dados adicionais
        """
        try:
            # TODO: Implementar tabela de eventos de segurança
            # Por enquanto, apenas log
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "event_type": event_type,
                "description": description,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "additional_data": additional_data
            }
            
            logger.info(f"Security Event: {log_data}")
            
        except Exception as e:
            logger.error(f"Erro ao registrar evento de segurança: {str(e)}")
    
    async def check_login_attempts(self, db: Session, email: str, ip_address: str) -> Dict[str, Any]:
        """
        Verifica tentativas de login
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            ip_address: Endereço IP
            
        Returns:
            Dict[str, Any]: Status das tentativas
        """
        # TODO: Implementar controle de tentativas de login
        # Por enquanto, sempre permitir
        return {
            "is_locked": False,
            "attempts_remaining": self.max_login_attempts,
            "lockout_until": None
        }
    
    async def record_failed_login(
        self,
        db: Session,
        email: str,
        ip_address: str,
        user_agent: str = None
    ) -> None:
        """
        Registra tentativa de login falhada
        
        Args:
            db: Sessão do banco de dados
            email: Email do usuário
            ip_address: Endereço IP
            user_agent: User agent
        """
        await self.log_security_event(
            db=db,
            user_id=None,
            event_type="failed_login",
            description=f"Tentativa de login falhada para {email}",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def record_successful_login(
        self,
        db: Session,
        user_id: int,
        ip_address: str,
        user_agent: str = None
    ) -> None:
        """
        Registra login bem-sucedido
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            ip_address: Endereço IP
            user_agent: User agent
        """
        await self.log_security_event(
            db=db,
            user_id=user_id,
            event_type="successful_login",
            description="Login realizado com sucesso",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def record_password_change(
        self,
        db: Session,
        user_id: int,
        ip_address: str,
        user_agent: str = None
    ) -> None:
        """
        Registra alteração de senha
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            ip_address: Endereço IP
            user_agent: User agent
        """
        await self.log_security_event(
            db=db,
            user_id=user_id,
            event_type="password_change",
            description="Senha alterada",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def record_account_creation(
        self,
        db: Session,
        user_id: int,
        ip_address: str,
        user_agent: str = None
    ) -> None:
        """
        Registra criação de conta
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            ip_address: Endereço IP
            user_agent: User agent
        """
        await self.log_security_event(
            db=db,
            user_id=user_id,
            event_type="account_creation",
            description="Conta criada",
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def record_account_deactivation(
        self,
        db: Session,
        user_id: int,
        admin_user_id: int,
        reason: str = None
    ) -> None:
        """
        Registra desativação de conta
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            admin_user_id: ID do administrador
            reason: Motivo da desativação
        """
        await self.log_security_event(
            db=db,
            user_id=user_id,
            event_type="account_deactivation",
            description=f"Conta desativada por admin {admin_user_id}",
            additional_data={"reason": reason, "admin_user_id": admin_user_id}
        )
    
    async def record_account_reactivation(
        self,
        db: Session,
        user_id: int,
        admin_user_id: int,
        reason: str = None
    ) -> None:
        """
        Registra reativação de conta
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            admin_user_id: ID do administrador
            reason: Motivo da reativação
        """
        await self.log_security_event(
            db=db,
            user_id=user_id,
            event_type="account_reactivation",
            description=f"Conta reativada por admin {admin_user_id}",
            additional_data={"reason": reason, "admin_user_id": admin_user_id}
        )
    
    async def record_permission_change(
        self,
        db: Session,
        user_id: int,
        admin_user_id: int,
        old_permissions: List[str],
        new_permissions: List[str]
    ) -> None:
        """
        Registra alteração de permissões
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            admin_user_id: ID do administrador
            old_permissions: Permissões antigas
            new_permissions: Novas permissões
        """
        await self.log_security_event(
            db=db,
            user_id=user_id,
            event_type="permission_change",
            description=f"Permissões alteradas por admin {admin_user_id}",
            additional_data={
                "admin_user_id": admin_user_id,
                "old_permissions": old_permissions,
                "new_permissions": new_permissions
            }
        )
    
    async def detect_suspicious_activity(
        self,
        db: Session,
        user_id: int,
        ip_address: str,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Detecta atividade suspeita
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            ip_address: Endereço IP
            user_agent: User agent
            
        Returns:
            Dict[str, Any]: Resultado da análise
        """
        # TODO: Implementar detecção de atividade suspeita
        # Por enquanto, sempre retornar como não suspeito
        return {
            "is_suspicious": False,
            "risk_score": 0,
            "reasons": []
        }
    
    async def get_user_security_events(
        self,
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtém eventos de segurança do usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            limit: Limite de resultados
            offset: Offset para paginação
            
        Returns:
            List[Dict[str, Any]]: Lista de eventos
        """
        # TODO: Implementar busca de eventos de segurança
        return []
    
    async def generate_security_report(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Gera relatório de segurança
        
        Args:
            db: Sessão do banco de dados
            start_date: Data de início
            end_date: Data de fim
            
        Returns:
            Dict[str, Any]: Relatório de segurança
        """
        # TODO: Implementar geração de relatório
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": 0,
            "failed_logins": 0,
            "successful_logins": 0,
            "password_changes": 0,
            "account_creations": 0,
            "suspicious_activities": 0
        }
    
    def sanitize_input(self, input_data: str) -> str:
        """
        Sanitiza entrada de dados
        
        Args:
            input_data: Dados de entrada
            
        Returns:
            str: Dados sanitizados
        """
        if not input_data:
            return ""
        
        # Remover caracteres perigosos
        dangerous_chars = ["<", ">", "&", "\"", "'", "/", "\\"]
        sanitized = input_data
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        return sanitized.strip()
    
    def validate_ip_address(self, ip_address: str) -> bool:
        """
        Valida endereço IP
        
        Args:
            ip_address: Endereço IP
            
        Returns:
            bool: True se válido
        """
        try:
            import ipaddress
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False
    
    def is_safe_redirect_url(self, url: str, allowed_hosts: List[str]) -> bool:
        """
        Verifica se URL de redirecionamento é segura
        
        Args:
            url: URL a ser verificada
            allowed_hosts: Lista de hosts permitidos
            
        Returns:
            bool: True se segura
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Verificar se é URL relativa (mais segura)
            if not parsed.netloc:
                return True
            
            # Verificar se o host está na lista permitida
            return parsed.netloc in allowed_hosts
            
        except Exception:
            return False