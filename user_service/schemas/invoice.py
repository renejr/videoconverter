"""
Schemas Pydantic para operações relacionadas a faturas
Sistema de Identidade e Transações - Domínio A

Este módulo contém todos os schemas para validação de dados
de entrada e saída relacionados às faturas.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import Field, validator
from .base import BaseSchema, TimestampMixin, CurrencyEnum


class InvoiceBaseSchema(BaseSchema):
    """
    Schema base para dados de fatura
    """
    
    subtotal: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Subtotal da fatura",
        example=29.90
    )
    
    tax_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        decimal_places=4,
        description="Taxa de imposto (%)",
        example=10.0000
    )
    
    tax_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Valor do imposto",
        example=2.99
    )
    
    discount_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        decimal_places=4,
        description="Taxa de desconto (%)",
        example=5.0000
    )
    
    discount_amount: Optional[Decimal] = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Valor do desconto",
        example=1.50
    )
    
    total: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Valor total da fatura",
        example=31.39
    )
    
    currency: str = Field(
        default="BRL",
        description="Moeda da fatura",
        example="BRL"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Descrição da fatura",
        example="Assinatura mensal - Plano Premium"
    )


class InvoiceCreateSchema(InvoiceBaseSchema):
    """
    Schema para criação de nova fatura
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
    
    invoice_type: str = Field(
        description="Tipo da fatura",
        example="subscription"
    )
    
    due_date: date = Field(
        description="Data de vencimento",
        example="2024-02-15"
    )
    
    billing_period_start: Optional[date] = Field(
        None,
        description="Início do período de cobrança",
        example="2024-01-15"
    )
    
    billing_period_end: Optional[date] = Field(
        None,
        description="Fim do período de cobrança",
        example="2024-02-14"
    )
    
    # Itens da fatura
    line_items: List[Dict[str, Any]] = Field(
        description="Itens da fatura",
        example=[
            {
                "description": "Plano Premium - Janeiro 2024",
                "quantity": 1,
                "unit_price": 29.90,
                "amount": 29.90
            }
        ]
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
    
    # Configurações
    auto_send: bool = Field(
        default=True,
        description="Enviar fatura automaticamente por email",
        example=True
    )
    
    auto_charge: bool = Field(
        default=False,
        description="Cobrar automaticamente no vencimento",
        example=False
    )
    
    payment_method_id: Optional[str] = Field(
        None,
        description="ID do método de pagamento para cobrança automática"
    )
    
    # Metadados
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados adicionais da fatura"
    )
    
    # Notas
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notas internas da fatura"
    )
    
    customer_notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Notas para o cliente"
    )
    
    @validator('line_items')
    def validate_line_items(cls, v):
        """Valida itens da fatura"""
        if not v:
            raise ValueError('Fatura deve ter pelo menos um item')
        
        for item in v:
            required_fields = ['description', 'quantity', 'unit_price', 'amount']
            for field in required_fields:
                if field not in item:
                    raise ValueError(f'Item deve ter o campo {field}')
            
            if item['quantity'] <= 0:
                raise ValueError('Quantidade deve ser maior que zero')
            
            if item['unit_price'] <= 0:
                raise ValueError('Preço unitário deve ser maior que zero')
            
            if item['amount'] <= 0:
                raise ValueError('Valor do item deve ser maior que zero')
        
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v):
        """Valida data de vencimento"""
        if v < date.today():
            raise ValueError('Data de vencimento não pode ser no passado')
        return v


class InvoiceUpdateSchema(BaseSchema):
    """
    Schema para atualização de fatura
    """
    
    status: Optional[str] = Field(
        None,
        description="Novo status da fatura"
    )
    
    due_date: Optional[date] = Field(
        None,
        description="Nova data de vencimento"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Nova descrição"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Novas notas internas"
    )
    
    customer_notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Novas notas para o cliente"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados da fatura"
    )


class InvoiceResponseSchema(InvoiceBaseSchema, TimestampMixin):
    """
    Schema para resposta com dados da fatura
    """
    
    id: int = Field(
        description="ID único da fatura",
        example=123
    )
    
    invoice_number: str = Field(
        description="Número da fatura",
        example="INV-2024-001234"
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
    
    status: str = Field(
        description="Status da fatura",
        example="paid"
    )
    
    invoice_type: str = Field(
        description="Tipo da fatura",
        example="subscription"
    )
    
    # Datas importantes
    issue_date: date = Field(
        description="Data de emissão",
        example="2024-01-15"
    )
    
    due_date: date = Field(
        description="Data de vencimento",
        example="2024-02-15"
    )
    
    paid_date: Optional[date] = Field(
        None,
        description="Data de pagamento",
        example="2024-01-20"
    )
    
    sent_date: Optional[date] = Field(
        None,
        description="Data de envio por email",
        example="2024-01-15"
    )
    
    # Período de cobrança
    billing_period_start: Optional[date] = Field(
        None,
        description="Início do período de cobrança",
        example="2024-01-15"
    )
    
    billing_period_end: Optional[date] = Field(
        None,
        description="Fim do período de cobrança",
        example="2024-02-14"
    )
    
    # Itens da fatura
    line_items: List[Dict[str, Any]] = Field(
        description="Itens da fatura"
    )
    
    # Endereço de cobrança
    billing_address: Optional[Dict[str, str]] = Field(
        None,
        description="Endereço de cobrança"
    )
    
    # Informações de pagamento
    payment_id: Optional[int] = Field(
        None,
        description="ID do pagamento associado",
        example=101112
    )
    
    payment_method: Optional[str] = Field(
        None,
        description="Método de pagamento utilizado",
        example="credit_card"
    )
    
    # Status calculados
    is_paid: bool = Field(
        description="Indica se a fatura foi paga",
        example=True
    )
    
    is_overdue: bool = Field(
        description="Indica se a fatura está vencida",
        example=False
    )
    
    is_draft: bool = Field(
        description="Indica se é um rascunho",
        example=False
    )
    
    is_cancelled: bool = Field(
        description="Indica se foi cancelada",
        example=False
    )
    
    days_until_due: Optional[int] = Field(
        None,
        description="Dias até o vencimento",
        example=25
    )
    
    days_overdue: Optional[int] = Field(
        None,
        description="Dias em atraso",
        example=0
    )
    
    # Configurações
    auto_charge: bool = Field(
        description="Cobrança automática habilitada",
        example=False
    )
    
    email_sent: bool = Field(
        description="Email foi enviado",
        example=True
    )
    
    # Notas
    notes: Optional[str] = Field(
        None,
        description="Notas internas"
    )
    
    customer_notes: Optional[str] = Field(
        None,
        description="Notas para o cliente"
    )
    
    # Metadados
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadados da fatura"
    )


class InvoiceListSchema(BaseSchema):
    """
    Schema para listagem simplificada de faturas
    """
    
    id: int = Field(description="ID da fatura")
    invoice_number: str = Field(description="Número da fatura")
    user_id: int = Field(description="ID do usuário")
    status: str = Field(description="Status")
    invoice_type: str = Field(description="Tipo da fatura")
    total: Decimal = Field(description="Valor total")
    currency: str = Field(description="Moeda")
    issue_date: date = Field(description="Data de emissão")
    due_date: date = Field(description="Data de vencimento")
    paid_date: Optional[date] = Field(None, description="Data de pagamento")
    is_overdue: bool = Field(description="Está vencida")
    days_until_due: Optional[int] = Field(None, description="Dias até vencimento")
    created_at: datetime = Field(description="Data de criação")


class InvoicePaySchema(BaseSchema):
    """
    Schema para pagamento de fatura
    """
    
    payment_method_id: Optional[str] = Field(
        None,
        description="ID do método de pagamento"
    )
    
    # Dados do cartão (se não usar método salvo)
    card_number: Optional[str] = Field(
        None,
        description="Número do cartão"
    )
    
    card_holder_name: Optional[str] = Field(
        None,
        description="Nome do portador"
    )
    
    card_expiry_month: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Mês de expiração"
    )
    
    card_expiry_year: Optional[int] = Field(
        None,
        description="Ano de expiração"
    )
    
    card_cvv: Optional[str] = Field(
        None,
        description="CVV do cartão"
    )
    
    # PIX
    pix_key: Optional[str] = Field(
        None,
        description="Chave PIX"
    )
    
    # Configurações
    save_payment_method: bool = Field(
        default=False,
        description="Salvar método de pagamento"
    )


class InvoiceSendSchema(BaseSchema):
    """
    Schema para envio de fatura por email
    """
    
    email: Optional[str] = Field(
        None,
        description="Email alternativo para envio"
    )
    
    subject: Optional[str] = Field(
        None,
        max_length=200,
        description="Assunto personalizado do email"
    )
    
    message: Optional[str] = Field(
        None,
        max_length=1000,
        description="Mensagem personalizada"
    )
    
    send_copy_to_admin: bool = Field(
        default=False,
        description="Enviar cópia para administrador"
    )


class InvoiceCancelSchema(BaseSchema):
    """
    Schema para cancelamento de fatura
    """
    
    reason: str = Field(
        min_length=5,
        max_length=500,
        description="Motivo do cancelamento",
        example="Erro na cobrança"
    )
    
    notify_customer: bool = Field(
        default=True,
        description="Notificar cliente sobre o cancelamento"
    )
    
    create_credit_note: bool = Field(
        default=False,
        description="Criar nota de crédito"
    )


class InvoiceSearchSchema(BaseSchema):
    """
    Schema para parâmetros de busca de faturas
    """
    
    user_id: Optional[int] = Field(
        None,
        description="Filtrar por usuário"
    )
    
    subscription_id: Optional[int] = Field(
        None,
        description="Filtrar por assinatura"
    )
    
    status: Optional[str] = Field(
        None,
        description="Filtrar por status"
    )
    
    invoice_type: Optional[str] = Field(
        None,
        description="Filtrar por tipo"
    )
    
    is_overdue: Optional[bool] = Field(
        None,
        description="Filtrar faturas vencidas"
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
    
    issue_date_from: Optional[date] = Field(
        None,
        description="Data de emissão a partir de"
    )
    
    issue_date_to: Optional[date] = Field(
        None,
        description="Data de emissão até"
    )
    
    due_date_from: Optional[date] = Field(
        None,
        description="Data de vencimento a partir de"
    )
    
    due_date_to: Optional[date] = Field(
        None,
        description="Data de vencimento até"
    )
    
    paid_date_from: Optional[date] = Field(
        None,
        description="Data de pagamento a partir de"
    )
    
    paid_date_to: Optional[date] = Field(
        None,
        description="Data de pagamento até"
    )


class InvoiceStatsSchema(BaseSchema):
    """
    Schema para estatísticas de faturas
    """
    
    total_invoices: int = Field(description="Total de faturas")
    paid_invoices: int = Field(description="Faturas pagas")
    pending_invoices: int = Field(description="Faturas pendentes")
    overdue_invoices: int = Field(description="Faturas vencidas")
    cancelled_invoices: int = Field(description="Faturas canceladas")
    draft_invoices: int = Field(description="Rascunhos")
    
    total_amount: Decimal = Field(description="Valor total faturado")
    paid_amount: Decimal = Field(description="Valor total pago")
    pending_amount: Decimal = Field(description="Valor pendente")
    overdue_amount: Decimal = Field(description="Valor vencido")
    
    collection_rate: Decimal = Field(description="Taxa de cobrança (%)")
    average_payment_time: Optional[int] = Field(None, description="Tempo médio de pagamento (dias)")
    average_invoice_amount: Decimal = Field(description="Valor médio por fatura")
    
    # Por período
    invoices_today: int = Field(description="Faturas emitidas hoje")
    invoices_this_week: int = Field(description="Faturas emitidas esta semana")
    invoices_this_month: int = Field(description="Faturas emitidas este mês")
    
    # Vencimentos próximos
    due_in_7_days: int = Field(description="Faturas vencendo em 7 dias")
    due_in_30_days: int = Field(description="Faturas vencendo em 30 dias")


class InvoiceReportSchema(BaseSchema):
    """
    Schema para relatórios de faturamento
    """
    
    period: str = Field(
        description="Período do relatório",
        example="2024-01"
    )
    
    total_invoiced: Decimal = Field(
        description="Total faturado no período"
    )
    
    total_collected: Decimal = Field(
        description="Total coletado no período"
    )
    
    collection_rate: Decimal = Field(
        description="Taxa de cobrança do período"
    )
    
    average_invoice_value: Decimal = Field(
        description="Valor médio das faturas"
    )
    
    # Breakdown por status
    status_breakdown: Dict[str, Dict[str, Any]] = Field(
        description="Breakdown por status das faturas"
    )
    
    # Breakdown por tipo
    type_breakdown: Dict[str, Dict[str, Any]] = Field(
        description="Breakdown por tipo de fatura"
    )
    
    # Aging report
    aging_report: Dict[str, Dict[str, Any]] = Field(
        description="Relatório de aging das faturas em aberto"
    )


class InvoiceReminderSchema(BaseSchema):
    """
    Schema para lembretes de fatura
    """
    
    invoice_id: int = Field(
        description="ID da fatura"
    )
    
    reminder_type: str = Field(
        description="Tipo do lembrete",
        example="due_soon"
    )
    
    days_before_due: Optional[int] = Field(
        None,
        description="Dias antes do vencimento"
    )
    
    custom_message: Optional[str] = Field(
        None,
        max_length=1000,
        description="Mensagem personalizada"
    )
    
    send_email: bool = Field(
        default=True,
        description="Enviar lembrete por email"
    )
    
    send_sms: bool = Field(
        default=False,
        description="Enviar lembrete por SMS"
    )


class InvoiceTemplateSchema(BaseSchema):
    """
    Schema para templates de fatura
    """
    
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Nome do template"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Descrição do template"
    )
    
    template_data: Dict[str, Any] = Field(
        description="Dados do template (HTML, CSS, etc.)"
    )
    
    is_default: bool = Field(
        default=False,
        description="Template padrão"
    )
    
    is_active: bool = Field(
        default=True,
        description="Template ativo"
    )