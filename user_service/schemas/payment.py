"""
Schemas Pydantic para operações relacionadas a pagamentos
Sistema de Identidade e Transações - Domínio A

Este módulo contém todos os schemas para validação de dados
de entrada e saída relacionados aos pagamentos.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import Field, validator
from .base import BaseSchema, TimestampMixin, CurrencyEnum


class PaymentBaseSchema(BaseSchema):
    """
    Schema base para dados de pagamento
    """
    
    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Valor do pagamento",
        example=29.90
    )
    
    currency: str = Field(
        default="BRL",
        description="Moeda do pagamento",
        example="BRL"
    )
    
    payment_method: str = Field(
        description="Método de pagamento",
        example="credit_card"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Descrição do pagamento",
        example="Assinatura mensal - Plano Premium"
    )


class PaymentCreateSchema(PaymentBaseSchema):
    """
    Schema para criação de novo pagamento
    """
    
    user_id: int = Field(
        gt=0,
        description="ID do usuário",
        example=123
    )
    
    subscription_id: Optional[int] = Field(
        None,
        description="ID da assinatura (se aplicável)",
        example=456
    )
    
    invoice_id: Optional[int] = Field(
        None,
        description="ID da fatura (se aplicável)",
        example=789
    )
    
    payment_type: str = Field(
        description="Tipo do pagamento",
        example="subscription"
    )
    
    # Dados do cartão de crédito
    card_number: Optional[str] = Field(
        None,
        min_length=13,
        max_length=19,
        description="Número do cartão (será tokenizado)",
        example="4111111111111111"
    )
    
    card_holder_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Nome do portador do cartão",
        example="João Silva"
    )
    
    card_expiry_month: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Mês de expiração do cartão",
        example=12
    )
    
    card_expiry_year: Optional[int] = Field(
        None,
        ge=2024,
        le=2050,
        description="Ano de expiração do cartão",
        example=2025
    )
    
    card_cvv: Optional[str] = Field(
        None,
        min_length=3,
        max_length=4,
        description="CVV do cartão",
        example="123"
    )
    
    # Dados PIX
    pix_key: Optional[str] = Field(
        None,
        max_length=100,
        description="Chave PIX para pagamento",
        example="usuario@email.com"
    )
    
    # Dados boleto
    boleto_due_date: Optional[date] = Field(
        None,
        description="Data de vencimento do boleto",
        example="2024-02-15"
    )
    
    # Endereço de cobrança
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
    
    # Metadados
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados adicionais do pagamento"
    )
    
    # Configurações
    save_payment_method: bool = Field(
        default=False,
        description="Salvar método de pagamento para uso futuro",
        example=False
    )
    
    auto_capture: bool = Field(
        default=True,
        description="Capturar pagamento automaticamente",
        example=True
    )
    
    @validator('card_number')
    def validate_card_number(cls, v):
        """Valida número do cartão de crédito"""
        if v is not None:
            # Remove espaços e hífens
            v = v.replace(' ', '').replace('-', '')
            # Verifica se contém apenas dígitos
            if not v.isdigit():
                raise ValueError('Número do cartão deve conter apenas dígitos')
            # Verifica comprimento
            if len(v) < 13 or len(v) > 19:
                raise ValueError('Número do cartão deve ter entre 13 e 19 dígitos')
        return v
    
    @validator('card_cvv')
    def validate_cvv(cls, v):
        """Valida CVV do cartão"""
        if v is not None:
            if not v.isdigit():
                raise ValueError('CVV deve conter apenas dígitos')
        return v


class PaymentUpdateSchema(BaseSchema):
    """
    Schema para atualização de pagamento
    """
    
    status: Optional[str] = Field(
        None,
        description="Novo status do pagamento"
    )
    
    gateway_transaction_id: Optional[str] = Field(
        None,
        description="ID da transação no gateway"
    )
    
    gateway_response: Optional[Dict[str, Any]] = Field(
        None,
        description="Resposta do gateway de pagamento"
    )
    
    failure_reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Motivo da falha (se aplicável)"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados do pagamento"
    )


class PaymentResponseSchema(PaymentBaseSchema, TimestampMixin):
    """
    Schema para resposta com dados do pagamento
    """
    
    id: int = Field(
        description="ID único do pagamento",
        example=123
    )
    
    user_id: int = Field(
        description="ID do usuário",
        example=456
    )
    
    subscription_id: Optional[int] = Field(
        None,
        description="ID da assinatura",
        example=789
    )
    
    invoice_id: Optional[int] = Field(
        None,
        description="ID da fatura",
        example=101112
    )
    
    status: str = Field(
        description="Status do pagamento",
        example="completed"
    )
    
    payment_type: str = Field(
        description="Tipo do pagamento",
        example="subscription"
    )
    
    # Informações do gateway
    gateway_name: Optional[str] = Field(
        None,
        description="Nome do gateway utilizado",
        example="stripe"
    )
    
    gateway_transaction_id: Optional[str] = Field(
        None,
        description="ID da transação no gateway",
        example="pi_1234567890"
    )
    
    gateway_response: Optional[Dict[str, Any]] = Field(
        None,
        description="Resposta completa do gateway"
    )
    
    # Informações de processamento
    processed_at: Optional[datetime] = Field(
        None,
        description="Data de processamento"
    )
    
    captured_at: Optional[datetime] = Field(
        None,
        description="Data de captura"
    )
    
    failed_at: Optional[datetime] = Field(
        None,
        description="Data de falha"
    )
    
    # Informações de reembolso
    refunded_amount: Optional[Decimal] = Field(
        None,
        description="Valor reembolsado",
        example=0.00
    )
    
    refunded_at: Optional[datetime] = Field(
        None,
        description="Data do reembolso"
    )
    
    refund_reason: Optional[str] = Field(
        None,
        description="Motivo do reembolso"
    )
    
    # Informações de falha
    failure_reason: Optional[str] = Field(
        None,
        description="Motivo da falha"
    )
    
    failure_code: Optional[str] = Field(
        None,
        description="Código da falha"
    )
    
    # Tentativas
    attempt_count: int = Field(
        default=1,
        description="Número de tentativas",
        example=1
    )
    
    max_attempts: int = Field(
        default=3,
        description="Máximo de tentativas",
        example=3
    )
    
    # Método de pagamento (dados mascarados)
    payment_method_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalhes mascarados do método de pagamento",
        example={
            "type": "credit_card",
            "last4": "1111",
            "brand": "visa",
            "exp_month": 12,
            "exp_year": 2025
        }
    )
    
    # Status calculados
    is_paid: bool = Field(
        description="Indica se o pagamento foi concluído",
        example=True
    )
    
    is_pending: bool = Field(
        description="Indica se o pagamento está pendente",
        example=False
    )
    
    is_failed: bool = Field(
        description="Indica se o pagamento falhou",
        example=False
    )
    
    is_refunded: bool = Field(
        description="Indica se foi reembolsado",
        example=False
    )
    
    can_be_refunded: bool = Field(
        description="Indica se pode ser reembolsado",
        example=True
    )
    
    # Metadados
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados do pagamento"
    )


class PaymentListSchema(BaseSchema):
    """
    Schema para listagem simplificada de pagamentos
    """
    
    id: int = Field(description="ID do pagamento")
    user_id: int = Field(description="ID do usuário")
    amount: Decimal = Field(description="Valor do pagamento")
    currency: str = Field(description="Moeda")
    status: str = Field(description="Status")
    payment_method: str = Field(description="Método de pagamento")
    payment_type: str = Field(description="Tipo do pagamento")
    description: Optional[str] = Field(None, description="Descrição")
    processed_at: Optional[datetime] = Field(None, description="Data de processamento")
    created_at: datetime = Field(description="Data de criação")


class PaymentRefundSchema(BaseSchema):
    """
    Schema para solicitação de reembolso
    """
    
    amount: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Valor a reembolsar (padrão: valor total)",
        example=29.90
    )
    
    reason: str = Field(
        min_length=5,
        max_length=500,
        description="Motivo do reembolso",
        example="Solicitação do cliente"
    )
    
    notify_customer: bool = Field(
        default=True,
        description="Notificar cliente sobre o reembolso",
        example=True
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados do reembolso"
    )


class PaymentCaptureSchema(BaseSchema):
    """
    Schema para captura de pagamento autorizado
    """
    
    amount: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Valor a capturar (padrão: valor total autorizado)"
    )


class PaymentSearchSchema(BaseSchema):
    """
    Schema para parâmetros de busca de pagamentos
    """
    
    user_id: Optional[int] = Field(
        None,
        description="Filtrar por usuário"
    )
    
    subscription_id: Optional[int] = Field(
        None,
        description="Filtrar por assinatura"
    )
    
    invoice_id: Optional[int] = Field(
        None,
        description="Filtrar por fatura"
    )
    
    status: Optional[str] = Field(
        None,
        description="Filtrar por status"
    )
    
    payment_method: Optional[str] = Field(
        None,
        description="Filtrar por método de pagamento"
    )
    
    payment_type: Optional[str] = Field(
        None,
        description="Filtrar por tipo de pagamento"
    )
    
    gateway_name: Optional[str] = Field(
        None,
        description="Filtrar por gateway"
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
    
    created_from: Optional[datetime] = Field(
        None,
        description="Data de criação a partir de"
    )
    
    created_to: Optional[datetime] = Field(
        None,
        description="Data de criação até"
    )
    
    processed_from: Optional[datetime] = Field(
        None,
        description="Data de processamento a partir de"
    )
    
    processed_to: Optional[datetime] = Field(
        None,
        description="Data de processamento até"
    )


class PaymentStatsSchema(BaseSchema):
    """
    Schema para estatísticas de pagamentos
    """
    
    total_payments: int = Field(description="Total de pagamentos")
    successful_payments: int = Field(description="Pagamentos bem-sucedidos")
    failed_payments: int = Field(description="Pagamentos falhados")
    pending_payments: int = Field(description="Pagamentos pendentes")
    refunded_payments: int = Field(description="Pagamentos reembolsados")
    
    total_amount: Decimal = Field(description="Valor total processado")
    successful_amount: Decimal = Field(description="Valor de pagamentos bem-sucedidos")
    refunded_amount: Decimal = Field(description="Valor total reembolsado")
    net_amount: Decimal = Field(description="Valor líquido")
    
    success_rate: Decimal = Field(description="Taxa de sucesso (%)")
    failure_rate: Decimal = Field(description="Taxa de falha (%)")
    refund_rate: Decimal = Field(description="Taxa de reembolso (%)")
    
    average_payment_amount: Decimal = Field(description="Valor médio por pagamento")
    
    # Por método de pagamento
    credit_card_payments: int = Field(description="Pagamentos com cartão")
    pix_payments: int = Field(description="Pagamentos PIX")
    boleto_payments: int = Field(description="Pagamentos boleto")
    
    # Por período
    payments_today: int = Field(description="Pagamentos hoje")
    payments_this_week: int = Field(description="Pagamentos esta semana")
    payments_this_month: int = Field(description="Pagamentos este mês")


class PaymentMethodSchema(BaseSchema):
    """
    Schema para métodos de pagamento salvos
    """
    
    id: str = Field(description="ID do método de pagamento")
    user_id: int = Field(description="ID do usuário")
    type: str = Field(description="Tipo do método")
    
    # Dados mascarados do cartão
    card_last4: Optional[str] = Field(None, description="Últimos 4 dígitos")
    card_brand: Optional[str] = Field(None, description="Bandeira do cartão")
    card_exp_month: Optional[int] = Field(None, description="Mês de expiração")
    card_exp_year: Optional[int] = Field(None, description="Ano de expiração")
    
    # PIX
    pix_key_type: Optional[str] = Field(None, description="Tipo da chave PIX")
    pix_key_masked: Optional[str] = Field(None, description="Chave PIX mascarada")
    
    is_default: bool = Field(description="Método padrão")
    is_active: bool = Field(description="Método ativo")
    
    created_at: datetime = Field(description="Data de criação")
    updated_at: datetime = Field(description="Data de atualização")


class PaymentWebhookSchema(BaseSchema):
    """
    Schema para webhooks de pagamento
    """
    
    event_type: str = Field(
        description="Tipo do evento",
        example="payment.succeeded"
    )
    
    payment_id: int = Field(
        description="ID do pagamento"
    )
    
    gateway_event_id: str = Field(
        description="ID do evento no gateway"
    )
    
    gateway_data: Dict[str, Any] = Field(
        description="Dados do evento do gateway"
    )
    
    processed: bool = Field(
        default=False,
        description="Indica se o webhook foi processado"
    )
    
    processed_at: Optional[datetime] = Field(
        None,
        description="Data de processamento do webhook"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Mensagem de erro (se houver)"
    )


class PaymentReportSchema(BaseSchema):
    """
    Schema para relatórios de pagamento
    """
    
    period: str = Field(
        description="Período do relatório",
        example="2024-01"
    )
    
    total_transactions: int = Field(
        description="Total de transações"
    )
    
    gross_revenue: Decimal = Field(
        description="Receita bruta"
    )
    
    net_revenue: Decimal = Field(
        description="Receita líquida"
    )
    
    fees_amount: Decimal = Field(
        description="Valor das taxas"
    )
    
    refunds_amount: Decimal = Field(
        description="Valor dos reembolsos"
    )
    
    chargebacks_amount: Decimal = Field(
        description="Valor dos chargebacks"
    )
    
    success_rate: Decimal = Field(
        description="Taxa de sucesso"
    )
    
    # Breakdown por método
    payment_methods_breakdown: Dict[str, Dict[str, Any]] = Field(
        description="Breakdown por método de pagamento"
    )
    
    # Breakdown por gateway
    gateways_breakdown: Dict[str, Dict[str, Any]] = Field(
        description="Breakdown por gateway"
    )