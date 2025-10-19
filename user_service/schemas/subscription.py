"""
Schemas Pydantic para operações relacionadas a assinaturas
Sistema de Identidade e Transações - Domínio A

Este módulo contém todos os schemas para validação de dados
de entrada e saída relacionados às assinaturas de usuários.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import Field, validator
from .base import BaseSchema, TimestampMixin, CurrencyEnum


class SubscriptionBaseSchema(BaseSchema):
    """
    Schema base para dados de assinatura
    """
    
    plan_id: int = Field(
        gt=0,
        description="ID do plano de assinatura",
        example=1
    )
    
    status: str = Field(
        description="Status da assinatura",
        example="active"
    )
    
    start_date: date = Field(
        description="Data de início da assinatura",
        example="2024-01-15"
    )
    
    end_date: Optional[date] = Field(
        None,
        description="Data de fim da assinatura",
        example="2024-02-15"
    )
    
    auto_renew: bool = Field(
        default=True,
        description="Renovação automática habilitada",
        example=True
    )
    
    trial_end_date: Optional[date] = Field(
        None,
        description="Data de fim do período de trial",
        example="2024-01-22"
    )


class SubscriptionCreateSchema(SubscriptionBaseSchema):
    """
    Schema para criação de nova assinatura
    """
    
    payment_method_id: Optional[str] = Field(
        None,
        description="ID do método de pagamento",
        example="pm_1234567890"
    )
    
    coupon_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Código de cupom de desconto",
        example="WELCOME20"
    )
    
    use_trial: bool = Field(
        default=True,
        description="Usar período de trial se disponível",
        example=True
    )
    
    billing_address: Optional[Dict[str, str]] = Field(
        None,
        description="Endereço de cobrança",
        example={
            "street": "Rua das Flores, 123",
            "city": "São Paulo",
            "state": "SP",
            "postal_code": "01234-567",
            "country": "BR"
        }
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados adicionais da assinatura"
    )


class SubscriptionUpdateSchema(BaseSchema):
    """
    Schema para atualização de assinatura
    """
    
    auto_renew: Optional[bool] = Field(
        None,
        description="Renovação automática"
    )
    
    payment_method_id: Optional[str] = Field(
        None,
        description="Novo método de pagamento"
    )
    
    billing_address: Optional[Dict[str, str]] = Field(
        None,
        description="Endereço de cobrança"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados da assinatura"
    )


class SubscriptionResponseSchema(SubscriptionBaseSchema, TimestampMixin):
    """
    Schema para resposta com dados da assinatura
    """
    
    id: int = Field(
        description="ID único da assinatura",
        example=123
    )
    
    user_id: int = Field(
        description="ID do usuário",
        example=456
    )
    
    current_period_start: date = Field(
        description="Início do período atual de cobrança",
        example="2024-01-15"
    )
    
    current_period_end: date = Field(
        description="Fim do período atual de cobrança",
        example="2024-02-15"
    )
    
    next_billing_date: Optional[date] = Field(
        None,
        description="Próxima data de cobrança",
        example="2024-02-15"
    )
    
    cancelled_at: Optional[datetime] = Field(
        None,
        description="Data de cancelamento"
    )
    
    cancellation_reason: Optional[str] = Field(
        None,
        description="Motivo do cancelamento"
    )
    
    suspended_at: Optional[datetime] = Field(
        None,
        description="Data de suspensão"
    )
    
    suspension_reason: Optional[str] = Field(
        None,
        description="Motivo da suspensão"
    )
    
    # Informações do plano
    plan: Dict[str, Any] = Field(
        description="Dados do plano associado"
    )
    
    # Informações financeiras
    amount: Decimal = Field(
        description="Valor da assinatura",
        example=29.90
    )
    
    currency: str = Field(
        description="Moeda da assinatura",
        example="BRL"
    )
    
    discount_amount: Optional[Decimal] = Field(
        None,
        description="Valor do desconto aplicado",
        example=5.00
    )
    
    tax_amount: Optional[Decimal] = Field(
        None,
        description="Valor dos impostos",
        example=2.99
    )
    
    total_amount: Decimal = Field(
        description="Valor total da assinatura",
        example=27.89
    )
    
    # Status calculados
    is_active: bool = Field(
        description="Indica se a assinatura está ativa",
        example=True
    )
    
    is_trial: bool = Field(
        description="Indica se está em período de trial",
        example=False
    )
    
    is_cancelled: bool = Field(
        description="Indica se foi cancelada",
        example=False
    )
    
    is_suspended: bool = Field(
        description="Indica se está suspensa",
        example=False
    )
    
    days_until_renewal: Optional[int] = Field(
        None,
        description="Dias até a próxima renovação",
        example=15
    )
    
    # Metadados
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados da assinatura"
    )


class SubscriptionListSchema(BaseSchema):
    """
    Schema para listagem simplificada de assinaturas
    """
    
    id: int = Field(description="ID da assinatura")
    user_id: int = Field(description="ID do usuário")
    plan_name: str = Field(description="Nome do plano")
    status: str = Field(description="Status da assinatura")
    amount: Decimal = Field(description="Valor da assinatura")
    currency: str = Field(description="Moeda")
    start_date: date = Field(description="Data de início")
    next_billing_date: Optional[date] = Field(None, description="Próxima cobrança")
    auto_renew: bool = Field(description="Renovação automática")
    is_trial: bool = Field(description="Em trial")
    created_at: datetime = Field(description="Data de criação")


class SubscriptionCancelSchema(BaseSchema):
    """
    Schema para cancelamento de assinatura
    """
    
    reason: str = Field(
        min_length=5,
        max_length=200,
        description="Motivo do cancelamento",
        example="Não utilizo mais o serviço"
    )
    
    cancel_immediately: bool = Field(
        default=False,
        description="Cancelar imediatamente ou no fim do período",
        example=False
    )
    
    feedback: Optional[str] = Field(
        None,
        max_length=1000,
        description="Feedback adicional sobre o serviço"
    )
    
    retain_data: bool = Field(
        default=True,
        description="Manter dados do usuário após cancelamento",
        example=True
    )


class SubscriptionSuspendSchema(BaseSchema):
    """
    Schema para suspensão de assinatura
    """
    
    reason: str = Field(
        min_length=5,
        max_length=200,
        description="Motivo da suspensão",
        example="Pagamento em atraso"
    )
    
    suspend_until: Optional[date] = Field(
        None,
        description="Data até quando suspender (opcional)"
    )
    
    notify_user: bool = Field(
        default=True,
        description="Notificar usuário sobre a suspensão",
        example=True
    )


class SubscriptionReactivateSchema(BaseSchema):
    """
    Schema para reativação de assinatura
    """
    
    payment_method_id: Optional[str] = Field(
        None,
        description="Método de pagamento para reativação"
    )
    
    reason: Optional[str] = Field(
        None,
        max_length=200,
        description="Motivo da reativação"
    )


class SubscriptionUpgradeSchema(BaseSchema):
    """
    Schema para upgrade/downgrade de plano
    """
    
    new_plan_id: int = Field(
        gt=0,
        description="ID do novo plano",
        example=2
    )
    
    prorate: bool = Field(
        default=True,
        description="Aplicar cobrança proporcional",
        example=True
    )
    
    effective_date: Optional[date] = Field(
        None,
        description="Data efetiva da mudança (padrão: imediata)"
    )
    
    reason: Optional[str] = Field(
        None,
        max_length=200,
        description="Motivo da mudança de plano"
    )


class SubscriptionRenewalSchema(BaseSchema):
    """
    Schema para renovação manual de assinatura
    """
    
    payment_method_id: Optional[str] = Field(
        None,
        description="Método de pagamento para renovação"
    )
    
    extend_trial: Optional[int] = Field(
        None,
        ge=1,
        le=30,
        description="Dias adicionais de trial"
    )


class SubscriptionSearchSchema(BaseSchema):
    """
    Schema para parâmetros de busca de assinaturas
    """
    
    user_id: Optional[int] = Field(
        None,
        description="Filtrar por usuário"
    )
    
    plan_id: Optional[int] = Field(
        None,
        description="Filtrar por plano"
    )
    
    status: Optional[str] = Field(
        None,
        description="Filtrar por status"
    )
    
    is_trial: Optional[bool] = Field(
        None,
        description="Filtrar assinaturas em trial"
    )
    
    auto_renew: Optional[bool] = Field(
        None,
        description="Filtrar por renovação automática"
    )
    
    start_date_from: Optional[date] = Field(
        None,
        description="Data de início a partir de"
    )
    
    start_date_to: Optional[date] = Field(
        None,
        description="Data de início até"
    )
    
    next_billing_from: Optional[date] = Field(
        None,
        description="Próxima cobrança a partir de"
    )
    
    next_billing_to: Optional[date] = Field(
        None,
        description="Próxima cobrança até"
    )
    
    min_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Valor mínimo"
    )
    
    max_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Valor máximo"
    )


class SubscriptionStatsSchema(BaseSchema):
    """
    Schema para estatísticas de assinaturas
    """
    
    total_subscriptions: int = Field(description="Total de assinaturas")
    active_subscriptions: int = Field(description="Assinaturas ativas")
    trial_subscriptions: int = Field(description="Assinaturas em trial")
    cancelled_subscriptions: int = Field(description="Assinaturas canceladas")
    suspended_subscriptions: int = Field(description="Assinaturas suspensas")
    
    monthly_recurring_revenue: Decimal = Field(description="Receita recorrente mensal")
    annual_recurring_revenue: Decimal = Field(description="Receita recorrente anual")
    average_revenue_per_user: Decimal = Field(description="Receita média por usuário")
    
    churn_rate: Decimal = Field(description="Taxa de cancelamento (%)")
    growth_rate: Decimal = Field(description="Taxa de crescimento (%)")
    
    new_subscriptions_today: int = Field(description="Novas assinaturas hoje")
    new_subscriptions_this_week: int = Field(description="Novas assinaturas esta semana")
    new_subscriptions_this_month: int = Field(description="Novas assinaturas este mês")
    
    renewals_this_month: int = Field(description="Renovações este mês")
    cancellations_this_month: int = Field(description="Cancelamentos este mês")


class SubscriptionRevenueSchema(BaseSchema):
    """
    Schema para dados de receita de assinaturas
    """
    
    period: str = Field(
        description="Período da receita",
        example="2024-01"
    )
    
    total_revenue: Decimal = Field(
        description="Receita total do período"
    )
    
    new_subscriptions_revenue: Decimal = Field(
        description="Receita de novas assinaturas"
    )
    
    renewals_revenue: Decimal = Field(
        description="Receita de renovações"
    )
    
    upgrades_revenue: Decimal = Field(
        description="Receita de upgrades"
    )
    
    refunds_amount: Decimal = Field(
        description="Valor de reembolsos"
    )
    
    net_revenue: Decimal = Field(
        description="Receita líquida"
    )
    
    subscription_count: int = Field(
        description="Número de assinaturas ativas"
    )


class SubscriptionEventSchema(BaseSchema):
    """
    Schema para eventos de assinatura
    """
    
    event_type: str = Field(
        description="Tipo do evento",
        example="subscription_created"
    )
    
    subscription_id: int = Field(
        description="ID da assinatura"
    )
    
    user_id: int = Field(
        description="ID do usuário"
    )
    
    description: str = Field(
        description="Descrição do evento"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados do evento"
    )
    
    timestamp: datetime = Field(
        description="Data e hora do evento"
    )


class SubscriptionNotificationSchema(BaseSchema):
    """
    Schema para notificações de assinatura
    """
    
    subscription_id: int = Field(
        description="ID da assinatura"
    )
    
    notification_type: str = Field(
        description="Tipo da notificação",
        example="renewal_reminder"
    )
    
    days_before: Optional[int] = Field(
        None,
        description="Dias antes do evento para notificar"
    )
    
    send_email: bool = Field(
        default=True,
        description="Enviar notificação por email"
    )
    
    send_push: bool = Field(
        default=False,
        description="Enviar notificação push"
    )
    
    custom_message: Optional[str] = Field(
        None,
        max_length=500,
        description="Mensagem personalizada"
    )