"""
Schemas Pydantic para operações relacionadas a usuários
Sistema de Identidade e Transações - Domínio A

Este módulo contém todos os schemas para validação de dados
de entrada e saída relacionados aos usuários.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import Field, EmailStr, validator
from .base import (
    BaseSchema, 
    TimestampMixin, 
    GenderEnum, 
    CountryCodeEnum,
    validate_phone_number,
    validate_cpf
)


class UserBaseSchema(BaseSchema):
    """
    Schema base para dados de usuário
    Contém campos comuns entre criação e atualização
    """
    
    email: EmailStr = Field(
        description="Email do usuário (único no sistema)",
        example="joao.silva@email.com"
    )
    
    first_name: str = Field(
        min_length=2,
        max_length=50,
        description="Primeiro nome do usuário",
        example="João"
    )
    
    last_name: str = Field(
        min_length=2,
        max_length=50,
        description="Sobrenome do usuário",
        example="Silva"
    )
    
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Número de telefone",
        example="+55 11 99999-9999"
    )
    
    date_of_birth: Optional[date] = Field(
        None,
        description="Data de nascimento",
        example="1990-05-15"
    )
    
    gender: Optional[GenderEnum] = Field(
        None,
        description="Gênero do usuário"
    )
    
    country: Optional[CountryCodeEnum] = Field(
        None,
        description="Código do país de residência"
    )
    
    state: Optional[str] = Field(
        None,
        max_length=50,
        description="Estado/província de residência",
        example="São Paulo"
    )
    
    city: Optional[str] = Field(
        None,
        max_length=50,
        description="Cidade de residência",
        example="São Paulo"
    )
    
    timezone: Optional[str] = Field(
        None,
        max_length=50,
        description="Fuso horário do usuário",
        example="America/Sao_Paulo"
    )
    
    language: Optional[str] = Field(
        None,
        max_length=10,
        description="Idioma preferido (código ISO)",
        example="pt-BR"
    )
    
    # Validadores
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            return validate_phone_number(v)
        return v
    
    @validator('date_of_birth')
    def validate_birth_date(cls, v):
        if v:
            today = date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            
            if age < 13:
                raise ValueError('Usuário deve ter pelo menos 13 anos')
            if age > 120:
                raise ValueError('Data de nascimento inválida')
        
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v:
            # Remove espaços extras e valida caracteres
            v = v.strip()
            if not v.replace(' ', '').replace('-', '').replace("'", '').isalpha():
                raise ValueError('Nome deve conter apenas letras, espaços, hífens e apostrofes')
        return v


class UserCreateSchema(UserBaseSchema):
    """
    Schema para criação de novos usuários
    Inclui campos obrigatórios para registro
    """
    
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Senha do usuário (será hasheada)",
        example="MinhaSenh@123"
    )
    
    confirm_password: str = Field(
        min_length=8,
        max_length=128,
        description="Confirmação da senha",
        example="MinhaSenh@123"
    )
    
    cpf: Optional[str] = Field(
        None,
        description="CPF do usuário (apenas para Brasil)",
        example="123.456.789-00"
    )
    
    accept_terms: bool = Field(
        description="Aceite dos termos de uso",
        example=True
    )
    
    accept_privacy: bool = Field(
        description="Aceite da política de privacidade",
        example=True
    )
    
    marketing_consent: Optional[bool] = Field(
        False,
        description="Consentimento para receber comunicações de marketing",
        example=False
    )
    
    # Validadores específicos para criação
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
    
    @validator('cpf')
    def validate_cpf_field(cls, v):
        if v:
            return validate_cpf(v)
        return v


class UserUpdateSchema(BaseSchema):
    """
    Schema para atualização de dados do usuário
    Todos os campos são opcionais
    """
    
    first_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="Primeiro nome do usuário"
    )
    
    last_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="Sobrenome do usuário"
    )
    
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Número de telefone"
    )
    
    date_of_birth: Optional[date] = Field(
        None,
        description="Data de nascimento"
    )
    
    gender: Optional[GenderEnum] = Field(
        None,
        description="Gênero do usuário"
    )
    
    country: Optional[CountryCodeEnum] = Field(
        None,
        description="Código do país de residência"
    )
    
    state: Optional[str] = Field(
        None,
        max_length=50,
        description="Estado/província de residência"
    )
    
    city: Optional[str] = Field(
        None,
        max_length=50,
        description="Cidade de residência"
    )
    
    timezone: Optional[str] = Field(
        None,
        max_length=50,
        description="Fuso horário do usuário"
    )
    
    language: Optional[str] = Field(
        None,
        max_length=10,
        description="Idioma preferido"
    )
    
    marketing_consent: Optional[bool] = Field(
        None,
        description="Consentimento para marketing"
    )
    
    # Validadores (reutilizando do schema base)
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            return validate_phone_number(v)
        return v
    
    @validator('date_of_birth')
    def validate_birth_date(cls, v):
        if v:
            today = date.today()
            age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
            
            if age < 13:
                raise ValueError('Usuário deve ter pelo menos 13 anos')
            if age > 120:
                raise ValueError('Data de nascimento inválida')
        
        return v


class UserResponseSchema(UserBaseSchema, TimestampMixin):
    """
    Schema para resposta com dados do usuário
    Exclui informações sensíveis como senhas
    """
    
    id: int = Field(
        description="ID único do usuário",
        example=123
    )
    
    full_name: str = Field(
        description="Nome completo do usuário (first_name + last_name)",
        example="João Silva"
    )
    
    is_active: bool = Field(
        description="Indica se o usuário está ativo",
        example=True
    )
    
    is_verified: bool = Field(
        description="Indica se o email foi verificado",
        example=True
    )
    
    is_premium: bool = Field(
        description="Indica se o usuário tem assinatura premium",
        example=False
    )
    
    last_login_at: Optional[datetime] = Field(
        None,
        description="Data e hora do último login",
        example="2024-01-15T14:30:00Z"
    )
    
    profile_completion: int = Field(
        description="Percentual de completude do perfil",
        example=85
    )


class UserDetailSchema(UserResponseSchema):
    """
    Schema para detalhes completos do usuário
    Inclui apenas campos que existem no modelo User
    """
    
    # Removidos campos que não existem no modelo User:
    # - cpf, email_verified_at, phone_verified_at
    # - marketing_consent, marketing_consent_at
    # - two_factor_enabled, login_attempts, account_locked_until
    
    # Campos adicionais que existem no modelo User
    country_code: Optional[str] = Field(
        None,
        description="Código do país",
        example="BR"
    )
    
    language_preference: Optional[str] = Field(
        None,
        description="Idioma preferido",
        example="pt-BR"
    )


class UserListSchema(BaseSchema):
    """
    Schema para listagem simplificada de usuários
    Usado em listas e buscas
    """
    
    id: int = Field(description="ID do usuário")
    email: EmailStr = Field(description="Email do usuário")
    first_name: str = Field(description="Primeiro nome")
    last_name: str = Field(description="Sobrenome")
    is_active: bool = Field(description="Status ativo")
    is_verified: bool = Field(description="Email verificado")
    is_premium: bool = Field(description="Assinatura premium")
    created_at: datetime = Field(description="Data de criação")
    last_login_at: Optional[datetime] = Field(None, description="Último login")


class UserSearchSchema(BaseSchema):
    """
    Schema para parâmetros de busca de usuários
    """
    
    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Busca por nome ou email"
    )
    
    is_active: Optional[bool] = Field(
        None,
        description="Filtrar por status ativo"
    )
    
    is_verified: Optional[bool] = Field(
        None,
        description="Filtrar por email verificado"
    )
    
    is_premium: Optional[bool] = Field(
        None,
        description="Filtrar por assinatura premium"
    )
    
    country: Optional[CountryCodeEnum] = Field(
        None,
        description="Filtrar por país"
    )
    
    created_after: Optional[datetime] = Field(
        None,
        description="Criados após esta data"
    )
    
    created_before: Optional[datetime] = Field(
        None,
        description="Criados antes desta data"
    )


class UserStatsSchema(BaseSchema):
    """
    Schema para estatísticas de usuários
    """
    
    total_users: int = Field(description="Total de usuários")
    active_users: int = Field(description="Usuários ativos")
    verified_users: int = Field(description="Usuários verificados")
    premium_users: int = Field(description="Usuários premium")
    new_users_today: int = Field(description="Novos usuários hoje")
    new_users_this_week: int = Field(description="Novos usuários esta semana")
    new_users_this_month: int = Field(description="Novos usuários este mês")


class UserDeactivateSchema(BaseSchema):
    """
    Schema para desativação de conta
    """
    
    reason: str = Field(
        min_length=10,
        max_length=500,
        description="Motivo da desativação",
        example="Não utilizo mais o serviço"
    )
    
    feedback: Optional[str] = Field(
        None,
        max_length=1000,
        description="Feedback adicional sobre o serviço"
    )
    
    confirm_deactivation: bool = Field(
        description="Confirmação da desativação",
        example=True
    )
    
    @validator('confirm_deactivation')
    def validate_confirmation(cls, v):
        if not v:
            raise ValueError('Confirmação obrigatória para desativar conta')
        return v


class UserReactivateSchema(BaseSchema):
    """
    Schema para reativação de conta
    """
    
    email: EmailStr = Field(
        description="Email da conta a ser reativada"
    )
    
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Motivo da reativação"
    )