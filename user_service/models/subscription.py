"""
Modelo de Assinaturas - Domínio A
Sistema de Identidade e Transações para Plataforma VOD
"""

from sqlalchemy import Column, BigInteger, String, Enum, DECIMAL, Boolean, TIMESTAMP, ForeignKey, Index, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import enum
from datetime import datetime, timedelta


class SubscriptionStatus(enum.Enum):
    """
    Status das assinaturas
    """
    ACTIVE = "active"               # Ativa
    INACTIVE = "inactive"           # Inativa
    SUSPENDED = "suspended"         # Suspensa
    CANCELLED = "cancelled"         # Cancelada
    EXPIRED = "expired"             # Expirada
    PENDING_PAYMENT = "pending_payment"  # Aguardando pagamento
    TRIAL = "trial"                 # Período de teste


class CancellationReason(enum.Enum):
    """
    Motivos de cancelamento
    """
    USER_REQUEST = "user_request"           # Solicitação do usuário
    PAYMENT_FAILURE = "payment_failure"     # Falha no pagamento
    POLICY_VIOLATION = "policy_violation"   # Violação de política
    FRAUD = "fraud"                         # Fraude
    TECHNICAL_ISSUE = "technical_issue"     # Problema técnico
    OTHER = "other"                         # Outro motivo


class Subscription(Base):
    """
    Modelo de Assinaturas
    
    Gerencia as assinaturas dos usuários aos planos da plataforma,
    incluindo status, datas de início/fim, renovações automáticas,
    períodos de teste e histórico de alterações.
    
    Relacionamentos:
    - Uma assinatura pertence a um usuário (N:1)
    - Uma assinatura pertence a um plano (N:1)
    - Uma assinatura pode ter muitos pagamentos (1:N)
    - Uma assinatura pode ter muitas faturas (1:N)
    
    Recursos:
    - Controle de status da assinatura
    - Renovação automática
    - Períodos de teste
    - Histórico de alterações
    - Motivos de cancelamento
    """
    
    __tablename__ = 'subscriptions'
    
    # Chave primária
    id = Column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True,
        comment="Identificador único da assinatura"
    )
    
    # Chaves estrangeiras
    user_id = Column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        comment="ID do usuário proprietário da assinatura"
    )
    
    plan_id = Column(
        BigInteger, 
        ForeignKey('plans.id', ondelete='RESTRICT'), 
        nullable=False,
        comment="ID do plano da assinatura"
    )
    
    # Status e controle
    status = Column(
        Enum(SubscriptionStatus), 
        nullable=False, 
        default=SubscriptionStatus.ACTIVE,
        comment="Status atual da assinatura"
    )
    
    # Datas importantes
    start_date = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data de início da assinatura"
    )
    
    end_date = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data de fim da assinatura (null = sem data definida)"
    )
    
    next_billing_date = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data da próxima cobrança"
    )
    
    trial_start = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data de início do período de teste"
    )
    
    trial_end = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data de fim do período de teste"
    )
    
    # Configurações de cobrança
    auto_renew = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="Renovação automática habilitada"
    )
    
    current_price = Column(
        DECIMAL(10, 2), 
        nullable=False,
        comment="Preço atual da assinatura (pode diferir do plano por promoções)"
    )
    
    currency = Column(
        String(3), 
        nullable=False, 
        default='BRL',
        comment="Moeda da assinatura"
    )
    
    # Informações de cancelamento
    cancelled_at = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data do cancelamento"
    )
    
    cancellation_reason = Column(
        Enum(CancellationReason), 
        nullable=True,
        comment="Motivo do cancelamento"
    )
    
    cancellation_note = Column(
        Text, 
        nullable=True,
        comment="Observações sobre o cancelamento"
    )
    
    # Configurações específicas
    grace_period_end = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Fim do período de carência (para pagamentos em atraso)"
    )
    
    # Metadados e configurações
    subscription_metadata = Column(
        JSON, 
        nullable=True,
        comment="Metadados específicos da assinatura em JSON"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data de criação da assinatura"
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
        back_populates="subscriptions"
    )
    
    plan = relationship(
        "Plan", 
        back_populates="subscriptions"
    )
    
    payments = relationship(
        "Payment", 
        back_populates="subscription"
    )
    
    invoices = relationship(
        "Invoice", 
        back_populates="subscription"
    )
    
    # Índices para otimização
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_plan_id', 'plan_id'),
        Index('idx_status', 'status'),
        Index('idx_start_date', 'start_date'),
        Index('idx_end_date', 'end_date'),
        Index('idx_next_billing_date', 'next_billing_date'),
        Index('idx_trial_period', 'trial_start', 'trial_end'),
        Index('idx_auto_renew', 'auto_renew'),
        Index('idx_cancelled_at', 'cancelled_at'),
        Index('idx_user_status', 'user_id', 'status'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'comment': 'Assinaturas dos usuários aos planos da plataforma'
        }
    )
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan_id={self.plan_id}, status={self.status.value})>"
    
    @property
    def is_active(self):
        """
        Verifica se a assinatura está ativa
        
        Returns:
            bool: True se a assinatura estiver ativa
        """
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def is_trial(self):
        """
        Verifica se está em período de teste
        
        Returns:
            bool: True se estiver em período de teste
        """
        if not self.trial_start or not self.trial_end:
            return False
        
        now = datetime.utcnow()
        return self.trial_start <= now <= self.trial_end
    
    @property
    def is_expired(self):
        """
        Verifica se a assinatura expirou
        
        Returns:
            bool: True se a assinatura expirou
        """
        if not self.end_date:
            return False
        
        return datetime.utcnow() > self.end_date
    
    @property
    def days_until_expiry(self):
        """
        Calcula quantos dias faltam para expirar
        
        Returns:
            int: Dias até expirar (negativo se já expirou)
        """
        if not self.end_date:
            return None
        
        delta = self.end_date - datetime.utcnow()
        return delta.days
    
    @property
    def days_until_next_billing(self):
        """
        Calcula quantos dias faltam para a próxima cobrança
        
        Returns:
            int: Dias até próxima cobrança
        """
        if not self.next_billing_date:
            return None
        
        delta = self.next_billing_date - datetime.utcnow()
        return delta.days
    
    @property
    def trial_days_remaining(self):
        """
        Calcula quantos dias restam no período de teste
        
        Returns:
            int: Dias restantes do trial (0 se não em trial)
        """
        if not self.is_trial:
            return 0
        
        delta = self.trial_end - datetime.utcnow()
        return max(0, delta.days)
    
    def cancel(self, reason: CancellationReason, note: str = None):
        """
        Cancela a assinatura
        
        Args:
            reason (CancellationReason): Motivo do cancelamento
            note (str): Observações sobre o cancelamento
        """
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason
        self.cancellation_note = note
        self.auto_renew = False
    
    def suspend(self, note: str = None):
        """
        Suspende a assinatura
        
        Args:
            note (str): Observações sobre a suspensão
        """
        self.status = SubscriptionStatus.SUSPENDED
        if note:
            metadata = self.subscription_metadata or {}
            metadata['suspension_note'] = note
            metadata['suspended_at'] = datetime.utcnow().isoformat()
            self.subscription_metadata = metadata
    
    def reactivate(self):
        """
        Reativa uma assinatura suspensa ou inativa
        """
        if self.status in [SubscriptionStatus.SUSPENDED, SubscriptionStatus.INACTIVE]:
            self.status = SubscriptionStatus.ACTIVE
            
            # Remove informações de suspensão
            if self.subscription_metadata:
                self.subscription_metadata.pop('suspension_note', None)
                self.subscription_metadata.pop('suspended_at', None)
    
    def extend_trial(self, days: int):
        """
        Estende o período de teste
        
        Args:
            days (int): Número de dias para estender
        """
        if self.trial_end:
            self.trial_end += timedelta(days=days)
        else:
            # Inicia um novo período de teste
            now = datetime.utcnow()
            self.trial_start = now
            self.trial_end = now + timedelta(days=days)
            self.status = SubscriptionStatus.TRIAL
    
    def calculate_next_billing_date(self):
        """
        Calcula a próxima data de cobrança baseada no ciclo do plano
        """
        if not self.plan:
            return
        
        from models.plan import BillingCycle
        
        base_date = self.next_billing_date or self.start_date or datetime.utcnow()
        
        if self.plan.billing_cycle == BillingCycle.MONTHLY:
            self.next_billing_date = base_date + timedelta(days=30)
        elif self.plan.billing_cycle == BillingCycle.QUARTERLY:
            self.next_billing_date = base_date + timedelta(days=90)
        elif self.plan.billing_cycle == BillingCycle.YEARLY:
            self.next_billing_date = base_date + timedelta(days=365)
        # LIFETIME não tem próxima cobrança
    
    def get_metadata(self, key: str, default=None):
        """
        Obtém um valor dos metadados
        
        Args:
            key (str): Chave do metadado
            default: Valor padrão
            
        Returns:
            Valor do metadado ou default
        """
        if not self.subscription_metadata:
            return default
        return self.subscription_metadata.get(key, default)
    
    def set_metadata(self, key: str, value):
        """
        Define um valor nos metadados
        
        Args:
            key (str): Chave do metadado
            value: Valor a ser definido
        """
        if not self.subscription_metadata:
            self.subscription_metadata = {}
        self.subscription_metadata[key] = value
    
    def to_dict(self, include_relationships=False):
        """
        Converte o modelo para dicionário
        
        Args:
            include_relationships (bool): Se deve incluir relacionamentos
            
        Returns:
            dict: Dados da assinatura
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'plan_id': self.plan_id,
            'status': self.status.value,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'next_billing_date': self.next_billing_date.isoformat() if self.next_billing_date else None,
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'auto_renew': self.auto_renew,
            'current_price': float(self.current_price),
            'currency': self.currency,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'cancellation_reason': self.cancellation_reason.value if self.cancellation_reason else None,
            'cancellation_note': self.cancellation_note,
            'grace_period_end': self.grace_period_end.isoformat() if self.grace_period_end else None,
            'subscription_metadata': self.subscription_metadata,
            'is_active': self.is_active,
            'is_trial': self.is_trial,
            'is_expired': self.is_expired,
            'days_until_expiry': self.days_until_expiry,
            'days_until_next_billing': self.days_until_next_billing,
            'trial_days_remaining': self.trial_days_remaining,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_relationships:
            data['plan'] = self.plan.to_dict() if self.plan else None
            data['payments_count'] = len(self.payments) if self.payments else 0
            data['invoices_count'] = len(self.invoices) if self.invoices else 0
        
        return data