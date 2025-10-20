"""
Schemas base e mixins para validação Pydantic
Sistema de Identidade e Transações - Domínio A

Este módulo contém as classes base e mixins reutilizáveis
para todos os schemas Pydantic do sistema.
"""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, validator
from enum import Enum


class BaseSchema(BaseModel):
    """
    Schema base para todos os schemas Pydantic
    
    Configurações padrão:
    - Validação de atribuição
    - Uso de enums por valor
    - Serialização de campos por alias
    - Validação de campos extras
    """
    
    model_config = ConfigDict(
        # Permite validação durante atribuição
        validate_assignment=True,
        
        # Usa valores dos enums ao invés de nomes
        use_enum_values=True,
        
        # Serializa usando alias dos campos
        populate_by_name=True,
        
        # Não permite campos extras
        extra='forbid',
        
        # Configurações de serialização
        str_strip_whitespace=True,
        validate_default=True,
        
        # Configurações para trabalhar com SQLAlchemy
        from_attributes=True,
        
        # Configurações de JSON
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class TimestampMixin(BaseModel):
    """
    Mixin para campos de timestamp
    Usado em schemas que incluem created_at e updated_at
    """
    
    created_at: Optional[datetime] = Field(
        None,
        description="Data e hora de criação do registro",
        example="2024-01-15T10:30:00Z"
    )
    
    updated_at: Optional[datetime] = Field(
        None,
        description="Data e hora da última atualização",
        example="2024-01-15T15:45:00Z"
    )


class PaginationSchema(BaseSchema):
    """
    Schema para parâmetros de paginação
    """
    
    page: int = Field(
        default=1,
        ge=1,
        description="Número da página (começando em 1)",
        example=1
    )
    
    size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Número de itens por página (máximo 100)",
        example=20
    )
    
    @property
    def offset(self) -> int:
        """Calcula o offset para a consulta no banco"""
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        """Retorna o limite para a consulta no banco"""
        return self.size


class PaginatedResponseSchema(BaseSchema):
    """
    Schema para respostas paginadas
    """
    
    items: list = Field(
        description="Lista de itens da página atual"
    )
    
    total: int = Field(
        description="Total de itens disponíveis",
        example=150
    )
    
    page: int = Field(
        description="Página atual",
        example=1
    )
    
    size: int = Field(
        description="Tamanho da página",
        example=20
    )
    
    pages: int = Field(
        description="Total de páginas disponíveis",
        example=8
    )
    
    has_next: bool = Field(
        description="Indica se há próxima página",
        example=True
    )
    
    has_prev: bool = Field(
        description="Indica se há página anterior",
        example=False
    )


class SortSchema(BaseSchema):
    """
    Schema para parâmetros de ordenação
    """
    
    sort_by: str = Field(
        default="created_at",
        description="Campo para ordenação",
        example="created_at"
    )
    
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Direção da ordenação (asc ou desc)",
        example="desc"
    )


class FilterSchema(BaseSchema):
    """
    Schema base para filtros de busca
    """
    
    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Termo de busca geral",
        example="joão"
    )
    
    active_only: Optional[bool] = Field(
        None,
        description="Filtrar apenas registros ativos",
        example=True
    )


class ResponseMessageSchema(BaseSchema):
    """
    Schema para mensagens de resposta da API
    """
    
    message: str = Field(
        description="Mensagem de resposta",
        example="Operação realizada com sucesso"
    )
    
    success: bool = Field(
        description="Indica se a operação foi bem-sucedida",
        example=True
    )
    
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Dados adicionais da resposta"
    )


class ErrorResponseSchema(BaseSchema):
    """
    Schema para respostas de erro da API
    """
    
    error: str = Field(
        description="Tipo do erro",
        example="ValidationError"
    )
    
    message: str = Field(
        description="Mensagem de erro",
        example="Os dados fornecidos são inválidos"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalhes específicos do erro"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp do erro"
    )


class HealthCheckSchema(BaseSchema):
    """
    Schema para verificação de saúde da API
    """
    
    status: str = Field(
        description="Status da aplicação",
        example="healthy"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp da verificação"
    )
    
    version: str = Field(
        description="Versão da aplicação",
        example="1.0.0"
    )
    
    database: str = Field(
        description="Status da conexão com banco de dados",
        example="connected"
    )
    
    uptime: Optional[str] = Field(
        None,
        description="Tempo de atividade da aplicação",
        example="2 days, 3 hours, 45 minutes"
    )


# Enums comuns para validação
class StatusEnum(str, Enum):
    """Enum para status gerais"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class GenderEnum(str, Enum):
    """Enum para gênero"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class CountryCodeEnum(str, Enum):
    """Enum para códigos de país (principais)"""
    BR = "BR"  # Brasil
    US = "US"  # Estados Unidos
    CA = "CA"  # Canadá
    MX = "MX"  # México
    AR = "AR"  # Argentina
    CL = "CL"  # Chile
    CO = "CO"  # Colômbia
    PE = "PE"  # Peru
    UY = "UY"  # Uruguai
    PY = "PY"  # Paraguai


class CurrencyEnum(str, Enum):
    """Enum para moedas"""
    BRL = "BRL"  # Real Brasileiro
    USD = "USD"  # Dólar Americano
    EUR = "EUR"  # Euro
    CAD = "CAD"  # Dólar Canadense
    MXN = "MXN"  # Peso Mexicano
    ARS = "ARS"  # Peso Argentino
    CLP = "CLP"  # Peso Chileno
    COP = "COP"  # Peso Colombiano
    PEN = "PEN"  # Sol Peruano


# Validadores customizados reutilizáveis
def validate_phone_number(v: str) -> str:
    """
    Valida número de telefone
    Aceita formatos: +55 11 99999-9999, (11) 99999-9999, 11999999999
    """
    if not v:
        return v
    
    # Remove caracteres não numéricos exceto +
    import re
    cleaned = re.sub(r'[^\d+]', '', v)
    
    # Verifica se tem código do país
    if cleaned.startswith('+'):
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError('Número de telefone inválido')
    else:
        if len(cleaned) < 10 or len(cleaned) > 11:
            raise ValueError('Número de telefone inválido')
    
    return v


def validate_cpf(v: str) -> str:
    """
    Valida CPF brasileiro
    """
    if not v:
        return v
    
    import re
    
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^\d]', '', v)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        raise ValueError('CPF deve ter 11 dígitos')
    
    # Verifica se não são todos iguais
    if cpf == cpf[0] * 11:
        raise ValueError('CPF inválido')
    
    # Validação dos dígitos verificadores
    def calculate_digit(cpf_digits, weights):
        total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    # Primeiro dígito
    first_digit = calculate_digit(cpf[:9], range(10, 1, -1))
    if int(cpf[9]) != first_digit:
        raise ValueError('CPF inválido')
    
    # Segundo dígito
    second_digit = calculate_digit(cpf[:10], range(11, 1, -1))
    if int(cpf[10]) != second_digit:
        raise ValueError('CPF inválido')
    
    return v


def validate_password_strength(v: str) -> str:
    """
    Valida força da senha
    Requisitos: mínimo 8 caracteres, pelo menos 1 maiúscula, 1 minúscula, 1 número
    """
    if not v:
        return v
    
    import re
    
    if len(v) < 8:
        raise ValueError('Senha deve ter pelo menos 8 caracteres')
    
    if not re.search(r'[A-Z]', v):
        raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
    
    if not re.search(r'[a-z]', v):
        raise ValueError('Senha deve conter pelo menos uma letra minúscula')
    
    if not re.search(r'\d', v):
        raise ValueError('Senha deve conter pelo menos um número')
    
    # Opcional: verificar caracteres especiais
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        raise ValueError('Senha deve conter pelo menos um caractere especial')
    
    return v