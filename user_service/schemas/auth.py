"""
Schemas Pydantic para autenticação e autorização
Sistema de Identidade e Transações - Domínio A

Este módulo contém todos os schemas para operações de
autenticação, autorização e segurança.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field, EmailStr, validator
from .base import BaseSchema, validate_password_strength


class LoginSchema(BaseSchema):
    """
    Schema para login de usuário
    """
    
    email: EmailStr = Field(
        description="Email do usuário",
        example="joao.silva@email.com"
    )
    
    password: str = Field(
        min_length=1,
        max_length=128,
        description="Senha do usuário",
        example="MinhaSenh@123"
    )
    
    remember_me: bool = Field(
        default=False,
        description="Manter login ativo por mais tempo",
        example=False
    )
    
    device_id: Optional[str] = Field(
        None,
        max_length=255,
        description="ID único do dispositivo",
        example="device_123456"
    )
    
    device_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Nome do dispositivo",
        example="iPhone 13 Pro"
    )
    
    device_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Tipo do dispositivo",
        example="mobile"
    )
    
    user_agent: Optional[str] = Field(
        None,
        max_length=500,
        description="User agent do navegador/app"
    )
    
    ip_address: Optional[str] = Field(
        None,
        max_length=45,
        description="Endereço IP do cliente"
    )


class LoginResponseSchema(BaseSchema):
    """
    Schema para resposta de login bem-sucedido
    """
    
    access_token: str = Field(
        description="Token de acesso JWT",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    
    refresh_token: str = Field(
        description="Token de refresh para renovação",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    
    token_type: str = Field(
        default="bearer",
        description="Tipo do token",
        example="bearer"
    )
    
    expires_in: int = Field(
        description="Tempo de expiração do token em segundos",
        example=3600
    )
    
    user: Dict[str, Any] = Field(
        description="Dados básicos do usuário logado"
    )
    
    session_id: str = Field(
        description="ID da sessão criada",
        example="session_123456"
    )
    
    requires_2fa: bool = Field(
        default=False,
        description="Indica se é necessário completar 2FA",
        example=False
    )


class RegisterSchema(BaseSchema):
    """
    Schema para registro de novo usuário
    Herda validações do UserCreateSchema mas com campos específicos para registro
    """
    
    email: EmailStr = Field(
        description="Email do usuário",
        example="joao.silva@email.com"
    )
    
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Senha do usuário",
        example="MinhaSenh@123"
    )
    
    confirm_password: str = Field(
        min_length=8,
        max_length=128,
        description="Confirmação da senha",
        example="MinhaSenh@123"
    )
    
    first_name: str = Field(
        min_length=2,
        max_length=50,
        description="Primeiro nome",
        example="João"
    )
    
    last_name: str = Field(
        min_length=2,
        max_length=50,
        description="Sobrenome",
        example="Silva"
    )
    
    accept_terms: bool = Field(
        description="Aceite dos termos de uso",
        example=True
    )
    
    accept_privacy: bool = Field(
        description="Aceite da política de privacidade",
        example=True
    )
    
    marketing_consent: bool = Field(
        default=False,
        description="Consentimento para marketing",
        example=False
    )
    
    referral_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Código de indicação",
        example="REF123456"
    )
    
    # Validadores
    @validator('password')
    def validate_password(cls, v):
        return validate_password_strength(v)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Senhas não coincidem')
        return v
    
    @validator('accept_terms', 'accept_privacy')
    def validate_required_consents(cls, v):
        if not v:
            raise ValueError('Aceite obrigatório para prosseguir')
        return v


class PasswordChangeSchema(BaseSchema):
    """
    Schema para alteração de senha
    """
    
    current_password: str = Field(
        min_length=1,
        max_length=128,
        description="Senha atual",
        example="SenhaAtual123"
    )
    
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="Nova senha",
        example="NovaSenha@456"
    )
    
    confirm_new_password: str = Field(
        min_length=8,
        max_length=128,
        description="Confirmação da nova senha",
        example="NovaSenha@456"
    )
    
    logout_all_devices: bool = Field(
        default=True,
        description="Deslogar de todos os dispositivos após alteração",
        example=True
    )
    
    @validator('new_password')
    def validate_new_password(cls, v):
        return validate_password_strength(v)
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Senhas não coincidem')
        return v


class PasswordResetRequestSchema(BaseSchema):
    """
    Schema para solicitação de reset de senha
    """
    
    email: EmailStr = Field(
        description="Email do usuário",
        example="joao.silva@email.com"
    )
    
    captcha_token: Optional[str] = Field(
        None,
        description="Token do captcha para validação",
        example="captcha_token_123"
    )


class PasswordResetSchema(BaseSchema):
    """
    Schema para reset de senha com token
    """
    
    token: str = Field(
        min_length=1,
        description="Token de reset recebido por email",
        example="reset_token_123456"
    )
    
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="Nova senha",
        example="NovaSenha@789"
    )
    
    confirm_new_password: str = Field(
        min_length=8,
        max_length=128,
        description="Confirmação da nova senha",
        example="NovaSenha@789"
    )
    
    @validator('new_password')
    def validate_new_password(cls, v):
        return validate_password_strength(v)
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Senhas não coincidem')
        return v


class EmailVerificationSchema(BaseSchema):
    """
    Schema para verificação de email
    """
    
    token: str = Field(
        min_length=1,
        description="Token de verificação recebido por email",
        example="verify_token_123456"
    )


class EmailVerificationRequestSchema(BaseSchema):
    """
    Schema para solicitação de reenvio de verificação de email
    """
    
    email: EmailStr = Field(
        description="Email para reenvio da verificação",
        example="joao.silva@email.com"
    )


class TwoFactorSetupSchema(BaseSchema):
    """
    Schema para configuração de autenticação de dois fatores
    """
    
    password: str = Field(
        min_length=1,
        description="Senha atual para confirmação",
        example="MinhaSenh@123"
    )


class TwoFactorSetupResponseSchema(BaseSchema):
    """
    Schema para resposta da configuração de 2FA
    """
    
    secret: str = Field(
        description="Chave secreta para configurar no app autenticador",
        example="JBSWY3DPEHPK3PXP"
    )
    
    qr_code_url: str = Field(
        description="URL do QR code para configuração",
        example="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
    )
    
    backup_codes: List[str] = Field(
        description="Códigos de backup para recuperação",
        example=["12345678", "87654321", "11223344"]
    )


class TwoFactorVerifySchema(BaseSchema):
    """
    Schema para verificação de código 2FA
    """
    
    code: str = Field(
        min_length=6,
        max_length=8,
        description="Código de 6 dígitos do app autenticador",
        example="123456"
    )
    
    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('Código deve conter apenas números')
        return v


class TwoFactorDisableSchema(BaseSchema):
    """
    Schema para desabilitar 2FA
    """
    
    password: str = Field(
        min_length=1,
        description="Senha atual para confirmação",
        example="MinhaSenh@123"
    )
    
    code: str = Field(
        min_length=6,
        max_length=8,
        description="Código atual do app autenticador",
        example="123456"
    )


class RefreshTokenSchema(BaseSchema):
    """
    Schema para renovação de token
    """
    
    refresh_token: str = Field(
        min_length=1,
        description="Token de refresh válido",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )


class LogoutSchema(BaseSchema):
    """
    Schema para logout
    """
    
    logout_all_devices: bool = Field(
        default=False,
        description="Deslogar de todos os dispositivos",
        example=False
    )


class SessionSchema(BaseSchema):
    """
    Schema para informações de sessão
    """
    
    session_id: str = Field(description="ID da sessão")
    device_id: Optional[str] = Field(None, description="ID do dispositivo")
    device_name: Optional[str] = Field(None, description="Nome do dispositivo")
    device_type: Optional[str] = Field(None, description="Tipo do dispositivo")
    ip_address: Optional[str] = Field(None, description="Endereço IP")
    location: Optional[str] = Field(None, description="Localização aproximada")
    is_current: bool = Field(description="Indica se é a sessão atual")
    created_at: datetime = Field(description="Data de criação da sessão")
    last_activity: datetime = Field(description="Última atividade")
    expires_at: datetime = Field(description="Data de expiração")


class ActiveSessionsResponseSchema(BaseSchema):
    """
    Schema para resposta de sessões ativas
    """
    
    sessions: List[SessionSchema] = Field(
        description="Lista de sessões ativas"
    )
    
    total: int = Field(
        description="Total de sessões ativas",
        example=3
    )


class RevokeSessionSchema(BaseSchema):
    """
    Schema para revogar sessão específica
    """
    
    session_id: str = Field(
        description="ID da sessão a ser revogada",
        example="session_123456"
    )


class SecurityEventSchema(BaseSchema):
    """
    Schema para eventos de segurança
    """
    
    event_type: str = Field(
        description="Tipo do evento de segurança",
        example="login_attempt"
    )
    
    description: str = Field(
        description="Descrição do evento",
        example="Tentativa de login com senha incorreta"
    )
    
    ip_address: Optional[str] = Field(
        None,
        description="Endereço IP do evento"
    )
    
    user_agent: Optional[str] = Field(
        None,
        description="User agent do evento"
    )
    
    location: Optional[str] = Field(
        None,
        description="Localização do evento"
    )
    
    timestamp: datetime = Field(
        description="Data e hora do evento"
    )
    
    severity: str = Field(
        description="Severidade do evento",
        example="medium"
    )


class SecurityLogResponseSchema(BaseSchema):
    """
    Schema para resposta do log de segurança
    """
    
    events: List[SecurityEventSchema] = Field(
        description="Lista de eventos de segurança"
    )
    
    total: int = Field(
        description="Total de eventos",
        example=25
    )


class AccountLockSchema(BaseSchema):
    """
    Schema para informações de bloqueio de conta
    """
    
    is_locked: bool = Field(
        description="Indica se a conta está bloqueada",
        example=False
    )
    
    locked_until: Optional[datetime] = Field(
        None,
        description="Data até quando a conta está bloqueada"
    )
    
    failed_attempts: int = Field(
        description="Número de tentativas falhadas",
        example=0
    )
    
    max_attempts: int = Field(
        description="Máximo de tentativas permitidas",
        example=5
    )


class UnlockAccountSchema(BaseSchema):
    """
    Schema para desbloqueio de conta
    """
    
    email: EmailStr = Field(
        description="Email da conta a ser desbloqueada"
    )
    
    unlock_token: str = Field(
        description="Token de desbloqueio recebido por email",
        example="unlock_token_123456"
    )