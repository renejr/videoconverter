"""
Schemas Pydantic para operações relacionadas a planos
Sistema de Identidade e Transações - Domínio A

Este módulo contém todos os schemas para validação de dados
de entrada e saída relacionados aos planos de assinatura.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import Field, validator
from .base import BaseSchema, TimestampMixin, CurrencyEnum


class PlanBaseSchema(BaseSchema):
    """
    Schema base para dados de plano
    """
    
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Nome do plano",
        example="Premium"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Descrição detalhada do plano",
        example="Acesso completo a todo o catálogo com qualidade 4K"
    )
    
    plan_type: str = Field(
        description="Tipo do plano",
        example="premium"
    )
    
    billing_cycle: str = Field(
        description="Ciclo de cobrança",
        example="monthly"
    )
    
    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Preço do plano",
        example=29.90
    )
    
    currency: CurrencyEnum = Field(
        default=CurrencyEnum.BRL,
        description="Moeda do preço"
    )
    
    trial_days: Optional[int] = Field(
        None,
        ge=0,
        le=365,
        description="Dias de trial gratuito",
        example=7
    )
    
    is_active: bool = Field(
        default=True,
        description="Indica se o plano está ativo para novas assinaturas",
        example=True
    )
    
    is_featured: bool = Field(
        default=False,
        description="Indica se o plano é destacado",
        example=False
    )
    
    max_devices: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Número máximo de dispositivos simultâneos",
        example=4
    )
    
    max_quality: Optional[str] = Field(
        None,
        description="Qualidade máxima de streaming",
        example="4K"
    )
    
    features: Optional[List[str]] = Field(
        None,
        description="Lista de recursos inclusos no plano",
        example=["4K Ultra HD", "HDR", "Dolby Atmos", "Downloads offline"]
    )
    
    restrictions: Optional[List[str]] = Field(
        None,
        description="Lista de restrições do plano",
        example=["Máximo 4 dispositivos", "Sem acesso a conteúdo premium"]
    )


class PlanCreateSchema(PlanBaseSchema):
    """
    Schema para criação de novos planos
    """
    
    # Campos específicos para criação
    promotional_price: Optional[Decimal] = Field(
        None,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Preço promocional (se aplicável)",
        example=19.90
    )
    
    promotional_months: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Meses de preço promocional",
        example=3
    )
    
    sort_order: Optional[int] = Field(
        None,
        ge=0,
        description="Ordem de exibição do plano",
        example=1
    )
    
    # Validadores
    @validator('promotional_price')
    def validate_promotional_price(cls, v, values):
        if v is not None and 'price' in values and v >= values['price']:
            raise ValueError('Preço promocional deve ser menor que o preço regular')
        return v
    
    @validator('promotional_months')
    def validate_promotional_months(cls, v, values):
        if v is not None and 'promotional_price' not in values:
            raise ValueError('Meses promocionais requer preço promocional')
        return v


class PlanUpdateSchema(BaseSchema):
    """
    Schema para atualização de planos
    Todos os campos são opcionais
    """
    
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Nome do plano"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Descrição do plano"
    )
    
    price: Optional[Decimal] = Field(
        None,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Preço do plano"
    )
    
    promotional_price: Optional[Decimal] = Field(
        None,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Preço promocional"
    )
    
    promotional_months: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Meses promocionais"
    )
    
    trial_days: Optional[int] = Field(
        None,
        ge=0,
        le=365,
        description="Dias de trial"
    )
    
    is_active: Optional[bool] = Field(
        None,
        description="Status ativo"
    )
    
    is_featured: Optional[bool] = Field(
        None,
        description="Plano destacado"
    )
    
    max_devices: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Máximo de dispositivos"
    )
    
    max_quality: Optional[str] = Field(
        None,
        description="Qualidade máxima"
    )
    
    features: Optional[List[str]] = Field(
        None,
        description="Recursos do plano"
    )
    
    restrictions: Optional[List[str]] = Field(
        None,
        description="Restrições do plano"
    )
    
    sort_order: Optional[int] = Field(
        None,
        ge=0,
        description="Ordem de exibição"
    )


class PlanResponseSchema(PlanBaseSchema, TimestampMixin):
    """
    Schema para resposta com dados do plano
    """
    
    id: int = Field(
        description="ID único do plano",
        example=1
    )
    
    promotional_price: Optional[Decimal] = Field(
        None,
        description="Preço promocional atual",
        example=19.90
    )
    
    promotional_months: Optional[int] = Field(
        None,
        description="Meses de preço promocional",
        example=3
    )
    
    sort_order: int = Field(
        description="Ordem de exibição",
        example=1
    )
    
    active_subscriptions: int = Field(
        description="Número de assinaturas ativas",
        example=1250
    )
    
    total_subscriptions: int = Field(
        description="Total de assinaturas já criadas",
        example=2500
    )
    
    # Campos calculados
    effective_price: Decimal = Field(
        description="Preço efetivo (promocional ou regular)",
        example=19.90
    )
    
    is_promotional: bool = Field(
        description="Indica se está em promoção",
        example=True
    )
    
    monthly_equivalent: Optional[Decimal] = Field(
        None,
        description="Equivalente mensal (para planos anuais)",
        example=24.92
    )


class PlanListSchema(BaseSchema):
    """
    Schema para listagem simplificada de planos
    """
    
    id: int = Field(description="ID do plano")
    name: str = Field(description="Nome do plano")
    plan_type: str = Field(description="Tipo do plano")
    billing_cycle: str = Field(description="Ciclo de cobrança")
    price: Decimal = Field(description="Preço regular")
    effective_price: Decimal = Field(description="Preço efetivo")
    currency: str = Field(description="Moeda")
    is_active: bool = Field(description="Status ativo")
    is_featured: bool = Field(description="Plano destacado")
    is_promotional: bool = Field(description="Em promoção")
    trial_days: Optional[int] = Field(None, description="Dias de trial")
    active_subscriptions: int = Field(description="Assinaturas ativas")


class PlanComparisonSchema(BaseSchema):
    """
    Schema para comparação de planos
    """
    
    plans: List[PlanResponseSchema] = Field(
        description="Lista de planos para comparação"
    )
    
    comparison_matrix: Dict[str, Dict[str, Any]] = Field(
        description="Matriz de comparação de recursos",
        example={
            "quality": {"basic": "HD", "premium": "4K"},
            "devices": {"basic": 2, "premium": 4},
            "downloads": {"basic": False, "premium": True}
        }
    )


class PlanSearchSchema(BaseSchema):
    """
    Schema para parâmetros de busca de planos
    """
    
    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Busca por nome ou descrição"
    )
    
    plan_type: Optional[str] = Field(
        None,
        description="Filtrar por tipo de plano"
    )
    
    billing_cycle: Optional[str] = Field(
        None,
        description="Filtrar por ciclo de cobrança"
    )
    
    is_active: Optional[bool] = Field(
        None,
        description="Filtrar por status ativo"
    )
    
    is_featured: Optional[bool] = Field(
        None,
        description="Filtrar planos destacados"
    )
    
    is_promotional: Optional[bool] = Field(
        None,
        description="Filtrar planos em promoção"
    )
    
    min_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Preço mínimo"
    )
    
    max_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Preço máximo"
    )
    
    currency: Optional[CurrencyEnum] = Field(
        None,
        description="Filtrar por moeda"
    )


class PlanStatsSchema(BaseSchema):
    """
    Schema para estatísticas de planos
    """
    
    total_plans: int = Field(description="Total de planos")
    active_plans: int = Field(description="Planos ativos")
    featured_plans: int = Field(description="Planos destacados")
    promotional_plans: int = Field(description="Planos em promoção")
    total_subscriptions: int = Field(description="Total de assinaturas")
    active_subscriptions: int = Field(description="Assinaturas ativas")
    monthly_revenue: Decimal = Field(description="Receita mensal estimada")
    average_plan_price: Decimal = Field(description="Preço médio dos planos")
    most_popular_plan: Optional[str] = Field(None, description="Plano mais popular")


class PlanRevenueSchema(BaseSchema):
    """
    Schema para dados de receita por plano
    """
    
    plan_id: int = Field(description="ID do plano")
    plan_name: str = Field(description="Nome do plano")
    active_subscriptions: int = Field(description="Assinaturas ativas")
    monthly_revenue: Decimal = Field(description="Receita mensal")
    annual_revenue: Decimal = Field(description="Receita anual estimada")
    average_subscription_duration: Optional[int] = Field(
        None,
        description="Duração média das assinaturas em dias"
    )
    churn_rate: Optional[Decimal] = Field(
        None,
        description="Taxa de cancelamento (%)"
    )


class PlanActivationSchema(BaseSchema):
    """
    Schema para ativação/desativação de plano
    """
    
    is_active: bool = Field(
        description="Status de ativação",
        example=True
    )
    
    reason: Optional[str] = Field(
        None,
        max_length=200,
        description="Motivo da alteração",
        example="Plano descontinuado"
    )


class PlanPromotionSchema(BaseSchema):
    """
    Schema para configuração de promoção
    """
    
    promotional_price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Preço promocional",
        example=19.90
    )
    
    promotional_months: int = Field(
        ge=1,
        le=12,
        description="Duração da promoção em meses",
        example=3
    )
    
    start_date: Optional[datetime] = Field(
        None,
        description="Data de início da promoção"
    )
    
    end_date: Optional[datetime] = Field(
        None,
        description="Data de fim da promoção"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=200,
        description="Descrição da promoção",
        example="Oferta especial de lançamento"
    )
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('Data de fim deve ser posterior à data de início')
        return v