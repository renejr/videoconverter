"""
Modelo de Faturas - Domínio A
Sistema de Identidade e Transações para Plataforma VOD
"""

from sqlalchemy import Column, BigInteger, String, Enum, DECIMAL, Boolean, TIMESTAMP, ForeignKey, Index, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import enum
from datetime import datetime


class InvoiceStatus(enum.Enum):
    """
    Status das faturas
    """
    DRAFT = "draft"                 # Rascunho
    PENDING = "pending"             # Pendente
    SENT = "sent"                   # Enviada
    PAID = "paid"                   # Paga
    OVERDUE = "overdue"             # Vencida
    CANCELLED = "cancelled"         # Cancelada
    REFUNDED = "refunded"           # Reembolsada


class InvoiceType(enum.Enum):
    """
    Tipos de fatura
    """
    SUBSCRIPTION = "subscription"   # Fatura de assinatura
    UPGRADE = "upgrade"             # Fatura de upgrade
    DOWNGRADE = "downgrade"         # Fatura de downgrade
    ADJUSTMENT = "adjustment"       # Fatura de ajuste
    REFUND = "refund"              # Fatura de reembolso
    CREDIT = "credit"              # Fatura de crédito


class Invoice(Base):
    """
    Modelo de Faturas
    
    Gerencia as faturas geradas para pagamentos na plataforma,
    incluindo faturas de assinaturas, upgrades, ajustes e reembolsos.
    Cada fatura pode conter múltiplos itens e ter diferentes status.
    
    Relacionamentos:
    - Uma fatura pertence a um usuário (N:1)
    - Uma fatura pode pertencer a uma assinatura (N:1)
    - Uma fatura pode estar relacionada a um pagamento (1:1)
    
    Recursos:
    - Numeração sequencial de faturas
    - Múltiplos tipos e status
    - Cálculo automático de totais
    - Suporte a impostos e descontos
    - Histórico de envios
    """
    
    __tablename__ = 'invoices'
    
    # Chave primária
    id = Column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True,
        comment="Identificador único da fatura"
    )
    
    # Chaves estrangeiras
    user_id = Column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        comment="ID do usuário proprietário da fatura"
    )
    
    subscription_id = Column(
        BigInteger, 
        ForeignKey('subscriptions.id', ondelete='SET NULL'), 
        nullable=True,
        comment="ID da assinatura relacionada (se aplicável)"
    )
    
    payment_id = Column(
        BigInteger, 
        ForeignKey('payments.id', ondelete='SET NULL'), 
        nullable=True,
        comment="ID do pagamento relacionado (se aplicável)"
    )
    
    # Informações da fatura
    invoice_number = Column(
        String(50), 
        nullable=False, 
        unique=True,
        comment="Número único da fatura (ex: INV-2024-000001)"
    )
    
    status = Column(
        Enum(InvoiceStatus), 
        nullable=False, 
        default=InvoiceStatus.DRAFT,
        comment="Status atual da fatura"
    )
    
    invoice_type = Column(
        Enum(InvoiceType), 
        nullable=False, 
        default=InvoiceType.SUBSCRIPTION,
        comment="Tipo da fatura"
    )
    
    # Valores financeiros
    subtotal = Column(
        DECIMAL(10, 2), 
        nullable=False, 
        default=0.00,
        comment="Subtotal da fatura (antes de impostos e descontos)"
    )
    
    tax_amount = Column(
        DECIMAL(10, 2), 
        nullable=False, 
        default=0.00,
        comment="Valor dos impostos"
    )
    
    discount_amount = Column(
        DECIMAL(10, 2), 
        nullable=False, 
        default=0.00,
        comment="Valor do desconto"
    )
    
    total_amount = Column(
        DECIMAL(10, 2), 
        nullable=False, 
        default=0.00,
        comment="Valor total da fatura (calculado automaticamente)"
    )
    
    currency = Column(
        String(3), 
        nullable=False, 
        default='BRL',
        comment="Moeda da fatura (ISO 4217)"
    )
    
    # Datas importantes
    issue_date = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data de emissão da fatura"
    )
    
    due_date = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data de vencimento da fatura"
    )
    
    paid_date = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data de pagamento da fatura"
    )
    
    sent_date = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data de envio da fatura"
    )
    
    # Período de cobrança
    billing_period_start = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Início do período de cobrança"
    )
    
    billing_period_end = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Fim do período de cobrança"
    )
    
    # Informações adicionais
    description = Column(
        Text, 
        nullable=True,
        comment="Descrição da fatura"
    )
    
    notes = Column(
        Text, 
        nullable=True,
        comment="Observações internas"
    )
    
    customer_notes = Column(
        Text, 
        nullable=True,
        comment="Observações para o cliente"
    )
    
    # Informações de impostos
    tax_rate = Column(
        DECIMAL(5, 2), 
        nullable=False, 
        default=0.00,
        comment="Taxa de imposto aplicada (%)"
    )
    
    tax_description = Column(
        String(100), 
        nullable=True,
        comment="Descrição do imposto aplicado"
    )
    
    # Informações de desconto
    discount_rate = Column(
        DECIMAL(5, 2), 
        nullable=False, 
        default=0.00,
        comment="Taxa de desconto aplicada (%)"
    )
    
    discount_description = Column(
        String(100), 
        nullable=True,
        comment="Descrição do desconto aplicado"
    )
    
    # Metadados e configurações
    invoice_metadata = Column(
        JSON, 
        nullable=True,
        comment="Metadados específicos da fatura em JSON"
    )
    
    # Controle de envio
    email_sent_count = Column(
        BigInteger, 
        nullable=False, 
        default=0,
        comment="Número de vezes que a fatura foi enviada por email"
    )
    
    last_email_sent = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data do último envio por email"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data de criação da fatura"
    )
    
    updated_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="Data da última atualização"
    )
    
    # Relacionamentos
    user = relationship(
        "User", 
        back_populates="invoices"
    )
    
    subscription = relationship(
        "Subscription", 
        back_populates="invoices"
    )
    
    payment = relationship(
        "Payment", 
        back_populates="invoice"
    )
    
    # Índices para otimização
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_subscription_id', 'subscription_id'),
        Index('idx_payment_id', 'payment_id'),
        Index('idx_invoice_number', 'invoice_number'),
        Index('idx_status', 'status'),
        Index('idx_invoice_type', 'invoice_type'),
        Index('idx_issue_date', 'issue_date'),
        Index('idx_due_date', 'due_date'),
        Index('idx_paid_date', 'paid_date'),
        Index('idx_billing_period', 'billing_period_start', 'billing_period_end'),
        Index('idx_user_status', 'user_id', 'status'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'comment': 'Faturas geradas para pagamentos na plataforma'
        }
    )
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', user_id={self.user_id}, total={self.total_amount})>"
    
    @property
    def is_paid(self):
        """
        Verifica se a fatura foi paga
        
        Returns:
            bool: True se a fatura foi paga
        """
        return self.status == InvoiceStatus.PAID
    
    @property
    def is_overdue(self):
        """
        Verifica se a fatura está vencida
        
        Returns:
            bool: True se a fatura está vencida
        """
        if not self.due_date or self.is_paid:
            return False
        
        return datetime.utcnow() > self.due_date
    
    @property
    def days_until_due(self):
        """
        Calcula quantos dias faltam para o vencimento
        
        Returns:
            int: Dias até vencimento (negativo se vencida)
        """
        if not self.due_date:
            return None
        
        delta = self.due_date - datetime.utcnow()
        return delta.days
    
    @property
    def days_overdue(self):
        """
        Calcula quantos dias a fatura está vencida
        
        Returns:
            int: Dias em atraso (0 se não vencida)
        """
        if not self.is_overdue:
            return 0
        
        delta = datetime.utcnow() - self.due_date
        return delta.days
    
    def calculate_total(self):
        """
        Calcula o total da fatura baseado no subtotal, impostos e descontos
        """
        # Calcula impostos
        if self.tax_rate > 0:
            self.tax_amount = self.subtotal * (self.tax_rate / 100)
        
        # Calcula descontos
        if self.discount_rate > 0:
            self.discount_amount = self.subtotal * (self.discount_rate / 100)
        
        # Calcula total
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        
        # Garante que o total não seja negativo
        if self.total_amount < 0:
            self.total_amount = 0
    
    def mark_as_paid(self, paid_date: datetime = None):
        """
        Marca a fatura como paga
        
        Args:
            paid_date (datetime): Data do pagamento
        """
        self.status = InvoiceStatus.PAID
        self.paid_date = paid_date or datetime.utcnow()
    
    def mark_as_sent(self, sent_date: datetime = None):
        """
        Marca a fatura como enviada
        
        Args:
            sent_date (datetime): Data do envio
        """
        if self.status == InvoiceStatus.DRAFT:
            self.status = InvoiceStatus.SENT
        
        self.sent_date = sent_date or datetime.utcnow()
        self.email_sent_count += 1
        self.last_email_sent = self.sent_date
    
    def mark_as_overdue(self):
        """
        Marca a fatura como vencida
        """
        if self.status in [InvoiceStatus.PENDING, InvoiceStatus.SENT]:
            self.status = InvoiceStatus.OVERDUE
    
    def cancel(self, reason: str = None):
        """
        Cancela a fatura
        
        Args:
            reason (str): Motivo do cancelamento
        """
        self.status = InvoiceStatus.CANCELLED
        
        if reason:
            metadata = self.invoice_metadata or {}
            metadata['cancellation_reason'] = reason
            metadata['cancelled_at'] = datetime.utcnow().isoformat()
            self.invoice_metadata = metadata
    
    def apply_discount(self, discount_rate: float, description: str = None):
        """
        Aplica um desconto à fatura
        
        Args:
            discount_rate (float): Taxa de desconto (0-100)
            description (str): Descrição do desconto
        """
        if 0 <= discount_rate <= 100:
            self.discount_rate = discount_rate
            self.discount_description = description
            self.calculate_total()
    
    def apply_tax(self, tax_rate: float, description: str = None):
        """
        Aplica imposto à fatura
        
        Args:
            tax_rate (float): Taxa de imposto (0-100)
            description (str): Descrição do imposto
        """
        if tax_rate >= 0:
            self.tax_rate = tax_rate
            self.tax_description = description
            self.calculate_total()
    
    def get_metadata(self, key: str, default=None):
        """
        Obtém um valor dos metadados
        
        Args:
            key (str): Chave do metadado
            default: Valor padrão
            
        Returns:
            Valor do metadado ou default
        """
        if not self.invoice_metadata:
            return default
        return self.invoice_metadata.get(key, default)
    
    def set_metadata(self, key: str, value):
        """
        Define um valor nos metadados
        
        Args:
            key (str): Chave do metadado
            value: Valor a ser definido
        """
        if not self.invoice_metadata:
            self.invoice_metadata = {}
        self.invoice_metadata[key] = value
    
    @staticmethod
    def generate_invoice_number(year: int = None, sequence: int = None):
        """
        Gera um número de fatura único
        
        Args:
            year (int): Ano da fatura
            sequence (int): Número sequencial
            
        Returns:
            str: Número da fatura formatado
        """
        if year is None:
            year = datetime.utcnow().year
        
        if sequence is None:
            # Em uma implementação real, isso viria do banco de dados
            sequence = 1
        
        return f"INV-{year}-{sequence:06d}"
    
    def to_dict(self, include_relationships=False):
        """
        Converte o modelo para dicionário
        
        Args:
            include_relationships (bool): Se deve incluir relacionamentos
            
        Returns:
            dict: Dados da fatura
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'payment_id': self.payment_id,
            'invoice_number': self.invoice_number,
            'status': self.status.value,
            'invoice_type': self.invoice_type.value,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'total_amount': float(self.total_amount),
            'currency': self.currency,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'billing_period_start': self.billing_period_start.isoformat() if self.billing_period_start else None,
            'billing_period_end': self.billing_period_end.isoformat() if self.billing_period_end else None,
            'description': self.description,
            'notes': self.notes,
            'customer_notes': self.customer_notes,
            'tax_rate': float(self.tax_rate),
            'tax_description': self.tax_description,
            'discount_rate': float(self.discount_rate),
            'discount_description': self.discount_description,
            'invoice_metadata': self.invoice_metadata,
            'email_sent_count': self.email_sent_count,
            'last_email_sent': self.last_email_sent.isoformat() if self.last_email_sent else None,
            'is_paid': self.is_paid,
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due,
            'days_overdue': self.days_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_relationships:
            data['subscription'] = self.subscription.to_dict() if self.subscription else None
            data['payment'] = self.payment.to_dict() if self.payment else None
        
        return data