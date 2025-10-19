"""
Modelo de Pagamentos - Domínio A
Sistema de Identidade e Transações para Plataforma VOD
"""

from sqlalchemy import Column, BigInteger, String, Enum, DECIMAL, Boolean, TIMESTAMP, ForeignKey, Index, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import enum
from datetime import datetime


class PaymentStatus(enum.Enum):
    """
    Status dos pagamentos
    """
    PENDING = "pending"             # Pendente
    PROCESSING = "processing"       # Processando
    COMPLETED = "completed"         # Concluído
    FAILED = "failed"              # Falhou
    CANCELLED = "cancelled"         # Cancelado
    REFUNDED = "refunded"          # Reembolsado
    PARTIALLY_REFUNDED = "partially_refunded"  # Parcialmente reembolsado


class PaymentMethod(enum.Enum):
    """
    Métodos de pagamento
    """
    CREDIT_CARD = "credit_card"     # Cartão de crédito
    DEBIT_CARD = "debit_card"       # Cartão de débito
    PIX = "pix"                     # PIX
    BOLETO = "boleto"               # Boleto bancário
    PAYPAL = "paypal"               # PayPal
    APPLE_PAY = "apple_pay"         # Apple Pay
    GOOGLE_PAY = "google_pay"       # Google Pay
    BANK_TRANSFER = "bank_transfer" # Transferência bancária


class PaymentType(enum.Enum):
    """
    Tipos de pagamento
    """
    SUBSCRIPTION = "subscription"   # Pagamento de assinatura
    UPGRADE = "upgrade"             # Upgrade de plano
    DOWNGRADE = "downgrade"         # Downgrade de plano
    RENEWAL = "renewal"             # Renovação
    REFUND = "refund"              # Reembolso
    ADJUSTMENT = "adjustment"       # Ajuste


class Payment(Base):
    """
    Modelo de Pagamentos
    
    Gerencia todos os pagamentos realizados na plataforma,
    incluindo pagamentos de assinaturas, upgrades, downgrades,
    reembolsos e ajustes financeiros.
    
    Relacionamentos:
    - Um pagamento pertence a um usuário (N:1)
    - Um pagamento pode pertencer a uma assinatura (N:1)
    - Um pagamento pode gerar uma fatura (1:1)
    
    Recursos:
    - Múltiplos métodos de pagamento
    - Controle de status detalhado
    - Informações de gateway de pagamento
    - Histórico de tentativas
    - Suporte a reembolsos parciais
    """
    
    __tablename__ = 'payments'
    
    # Chave primária
    id = Column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True,
        comment="Identificador único do pagamento"
    )
    
    # Chaves estrangeiras
    user_id = Column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        comment="ID do usuário que realizou o pagamento"
    )
    
    subscription_id = Column(
        BigInteger, 
        ForeignKey('subscriptions.id', ondelete='SET NULL'), 
        nullable=True,
        comment="ID da assinatura relacionada (se aplicável)"
    )
    
    # Informações básicas do pagamento
    amount = Column(
        DECIMAL(10, 2), 
        nullable=False,
        comment="Valor do pagamento"
    )
    
    currency = Column(
        String(3), 
        nullable=False, 
        default='BRL',
        comment="Moeda do pagamento (ISO 4217)"
    )
    
    status = Column(
        Enum(PaymentStatus), 
        nullable=False, 
        default=PaymentStatus.PENDING,
        comment="Status atual do pagamento"
    )
    
    payment_method = Column(
        Enum(PaymentMethod), 
        nullable=False,
        comment="Método de pagamento utilizado"
    )
    
    payment_type = Column(
        Enum(PaymentType), 
        nullable=False, 
        default=PaymentType.SUBSCRIPTION,
        comment="Tipo do pagamento"
    )
    
    # Informações do gateway de pagamento
    gateway_provider = Column(
        String(50), 
        nullable=True,
        comment="Provedor do gateway (ex: 'stripe', 'pagseguro', 'mercadopago')"
    )
    
    gateway_transaction_id = Column(
        String(255), 
        nullable=True,
        comment="ID da transação no gateway"
    )
    
    gateway_reference = Column(
        String(255), 
        nullable=True,
        comment="Referência adicional do gateway"
    )
    
    # Datas importantes
    payment_date = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data efetiva do pagamento"
    )
    
    due_date = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data de vencimento (para boletos, etc.)"
    )
    
    # Informações de reembolso
    refunded_amount = Column(
        DECIMAL(10, 2), 
        nullable=False, 
        default=0.00,
        comment="Valor reembolsado"
    )
    
    refund_date = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data do reembolso"
    )
    
    refund_reason = Column(
        Text, 
        nullable=True,
        comment="Motivo do reembolso"
    )
    
    # Tentativas de pagamento
    attempt_count = Column(
        BigInteger, 
        nullable=False, 
        default=1,
        comment="Número de tentativas de pagamento"
    )
    
    last_attempt_date = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data da última tentativa"
    )
    
    # Informações adicionais
    description = Column(
        Text, 
        nullable=True,
        comment="Descrição do pagamento"
    )
    
    failure_reason = Column(
        Text, 
        nullable=True,
        comment="Motivo da falha (se aplicável)"
    )
    
    # Metadados do gateway e configurações
    gateway_metadata = Column(
        JSON, 
        nullable=True,
        comment="Metadados específicos do gateway em JSON"
    )
    
    payment_metadata = Column(
        JSON, 
        nullable=True,
        comment="Metadados adicionais do pagamento em JSON"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data de criação do pagamento"
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
        back_populates="payments"
    )
    
    subscription = relationship(
        "Subscription", 
        back_populates="payments"
    )
    
    invoice = relationship(
        "Invoice", 
        back_populates="payment",
        uselist=False
    )
    
    # Índices para otimização
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_subscription_id', 'subscription_id'),
        Index('idx_status', 'status'),
        Index('idx_payment_method', 'payment_method'),
        Index('idx_payment_type', 'payment_type'),
        Index('idx_gateway_provider', 'gateway_provider'),
        Index('idx_gateway_transaction_id', 'gateway_transaction_id'),
        Index('idx_payment_date', 'payment_date'),
        Index('idx_due_date', 'due_date'),
        Index('idx_created_at', 'created_at'),
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_subscription_status', 'subscription_id', 'status'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'comment': 'Pagamentos realizados na plataforma'
        }
    )
    
    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status.value})>"
    
    @property
    def is_completed(self):
        """
        Verifica se o pagamento foi concluído
        
        Returns:
            bool: True se o pagamento foi concluído
        """
        return self.status == PaymentStatus.COMPLETED
    
    @property
    def is_pending(self):
        """
        Verifica se o pagamento está pendente
        
        Returns:
            bool: True se o pagamento está pendente
        """
        return self.status in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]
    
    @property
    def is_failed(self):
        """
        Verifica se o pagamento falhou
        
        Returns:
            bool: True se o pagamento falhou
        """
        return self.status == PaymentStatus.FAILED
    
    @property
    def is_refunded(self):
        """
        Verifica se o pagamento foi reembolsado
        
        Returns:
            bool: True se foi reembolsado (total ou parcial)
        """
        return self.status in [PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED]
    
    @property
    def remaining_amount(self):
        """
        Calcula o valor restante após reembolsos
        
        Returns:
            Decimal: Valor restante
        """
        return self.amount - self.refunded_amount
    
    @property
    def refund_percentage(self):
        """
        Calcula a porcentagem reembolsada
        
        Returns:
            float: Porcentagem reembolsada (0-100)
        """
        if self.amount == 0:
            return 0.0
        return float((self.refunded_amount / self.amount) * 100)
    
    @property
    def is_overdue(self):
        """
        Verifica se o pagamento está em atraso
        
        Returns:
            bool: True se está em atraso
        """
        if not self.due_date or self.is_completed:
            return False
        
        return datetime.utcnow() > self.due_date
    
    def mark_as_completed(self, gateway_transaction_id: str = None, payment_date: datetime = None):
        """
        Marca o pagamento como concluído
        
        Args:
            gateway_transaction_id (str): ID da transação no gateway
            payment_date (datetime): Data do pagamento
        """
        self.status = PaymentStatus.COMPLETED
        self.payment_date = payment_date or datetime.utcnow()
        
        if gateway_transaction_id:
            self.gateway_transaction_id = gateway_transaction_id
    
    def mark_as_failed(self, reason: str = None):
        """
        Marca o pagamento como falhou
        
        Args:
            reason (str): Motivo da falha
        """
        self.status = PaymentStatus.FAILED
        self.failure_reason = reason
        self.attempt_count += 1
        self.last_attempt_date = datetime.utcnow()
    
    def process_refund(self, amount: float, reason: str = None):
        """
        Processa um reembolso
        
        Args:
            amount (float): Valor a ser reembolsado
            reason (str): Motivo do reembolso
        """
        if amount <= 0 or amount > self.remaining_amount:
            raise ValueError("Valor de reembolso inválido")
        
        self.refunded_amount += amount
        self.refund_date = datetime.utcnow()
        self.refund_reason = reason
        
        # Atualiza o status baseado no valor reembolsado
        if self.refunded_amount >= self.amount:
            self.status = PaymentStatus.REFUNDED
        else:
            self.status = PaymentStatus.PARTIALLY_REFUNDED
    
    def retry_payment(self):
        """
        Registra uma nova tentativa de pagamento
        """
        self.attempt_count += 1
        self.last_attempt_date = datetime.utcnow()
        self.status = PaymentStatus.PROCESSING
    
    def get_gateway_metadata(self, key: str, default=None):
        """
        Obtém um valor dos metadados do gateway
        
        Args:
            key (str): Chave do metadado
            default: Valor padrão
            
        Returns:
            Valor do metadado ou default
        """
        if not self.gateway_metadata:
            return default
        return self.gateway_metadata.get(key, default)
    
    def set_gateway_metadata(self, key: str, value):
        """
        Define um valor nos metadados do gateway
        
        Args:
            key (str): Chave do metadado
            value: Valor a ser definido
        """
        if not self.gateway_metadata:
            self.gateway_metadata = {}
        self.gateway_metadata[key] = value
    
    def get_payment_metadata(self, key: str, default=None):
        """
        Obtém um valor dos metadados do pagamento
        
        Args:
            key (str): Chave do metadado
            default: Valor padrão
            
        Returns:
            Valor do metadado ou default
        """
        if not self.payment_metadata:
            return default
        return self.payment_metadata.get(key, default)
    
    def set_payment_metadata(self, key: str, value):
        """
        Define um valor nos metadados do pagamento
        
        Args:
            key (str): Chave do metadado
            value: Valor a ser definido
        """
        if not self.payment_metadata:
            self.payment_metadata = {}
        self.payment_metadata[key] = value
    
    def to_dict(self, include_relationships=False, include_sensitive=False):
        """
        Converte o modelo para dicionário
        
        Args:
            include_relationships (bool): Se deve incluir relacionamentos
            include_sensitive (bool): Se deve incluir dados sensíveis
            
        Returns:
            dict: Dados do pagamento
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status.value,
            'payment_method': self.payment_method.value,
            'payment_type': self.payment_type.value,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'refunded_amount': float(self.refunded_amount),
            'refund_date': self.refund_date.isoformat() if self.refund_date else None,
            'refund_reason': self.refund_reason,
            'attempt_count': self.attempt_count,
            'last_attempt_date': self.last_attempt_date.isoformat() if self.last_attempt_date else None,
            'description': self.description,
            'failure_reason': self.failure_reason,
            'is_completed': self.is_completed,
            'is_pending': self.is_pending,
            'is_failed': self.is_failed,
            'is_refunded': self.is_refunded,
            'remaining_amount': float(self.remaining_amount),
            'refund_percentage': self.refund_percentage,
            'is_overdue': self.is_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Inclui dados sensíveis apenas se solicitado
        if include_sensitive:
            data.update({
                'gateway_provider': self.gateway_provider,
                'gateway_transaction_id': self.gateway_transaction_id,
                'gateway_reference': self.gateway_reference,
                'gateway_metadata': self.gateway_metadata,
                'payment_metadata': self.payment_metadata,
            })
        
        if include_relationships:
            data['subscription'] = self.subscription.to_dict() if self.subscription else None
            data['invoice'] = self.invoice.to_dict() if self.invoice else None
        
        return data