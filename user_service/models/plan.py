"""
Modelo de Planos - Domínio A
Sistema de Identidade e Transações para Plataforma VOD
"""

from sqlalchemy import Column, BigInteger, String, Enum, DECIMAL, Integer, Boolean, Text, TIMESTAMP, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import enum


class PlanType(enum.Enum):
    """
    Tipos de planos disponíveis
    """
    FREE = "free"           # Plano gratuito
    BASIC = "basic"         # Plano básico
    PREMIUM = "premium"     # Plano premium
    FAMILY = "family"       # Plano família
    STUDENT = "student"     # Plano estudante


class BillingCycle(enum.Enum):
    """
    Ciclos de cobrança
    """
    MONTHLY = "monthly"     # Mensal
    QUARTERLY = "quarterly" # Trimestral
    YEARLY = "yearly"       # Anual
    LIFETIME = "lifetime"   # Vitalício


class Plan(Base):
    """
    Modelo de Planos de Assinatura
    
    Define os diferentes tipos de planos disponíveis na plataforma,
    incluindo preços, recursos, limitações e configurações específicas.
    
    Relacionamentos:
    - Um plano pode ter muitas assinaturas (1:N)
    
    Recursos:
    - Diferentes tipos de planos (gratuito, básico, premium, etc.)
    - Ciclos de cobrança flexíveis
    - Configurações de recursos em JSON
    - Controle de ativação/desativação
    - Preços promocionais
    """
    
    __tablename__ = 'plans'
    
    # Chave primária
    id = Column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True,
        comment="Identificador único do plano"
    )
    
    # Informações básicas
    name = Column(
        String(100), 
        nullable=False,
        comment="Nome do plano (ex: 'Premium', 'Básico')"
    )
    
    description = Column(
        Text, 
        nullable=True,
        comment="Descrição detalhada do plano"
    )
    
    plan_type = Column(
        Enum(PlanType), 
        nullable=False,
        comment="Tipo do plano (free, basic, premium, family, student)"
    )
    
    # Configurações de preço
    price = Column(
        DECIMAL(10, 2), 
        nullable=False, 
        default=0.00,
        comment="Preço do plano"
    )
    
    promotional_price = Column(
        DECIMAL(10, 2), 
        nullable=True,
        comment="Preço promocional (se aplicável)"
    )
    
    billing_cycle = Column(
        Enum(BillingCycle), 
        nullable=False,
        comment="Ciclo de cobrança (monthly, quarterly, yearly, lifetime)"
    )
    
    currency = Column(
        String(3), 
        nullable=False, 
        default='BRL',
        comment="Moeda do preço (ISO 4217)"
    )
    
    # Limitações e recursos
    max_concurrent_streams = Column(
        Integer, 
        nullable=True,
        comment="Número máximo de streams simultâneos (null = ilimitado)"
    )
    
    max_download_quality = Column(
        String(10), 
        nullable=True, 
        default='HD',
        comment="Qualidade máxima de download (SD, HD, 4K)"
    )
    
    max_streaming_quality = Column(
        String(10), 
        nullable=True, 
        default='HD',
        comment="Qualidade máxima de streaming (SD, HD, 4K)"
    )
    
    offline_downloads_allowed = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="Permite downloads offline"
    )
    
    ads_free = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="Livre de anúncios"
    )
    
    # Configurações avançadas em JSON
    features = Column(
        JSON, 
        nullable=True,
        comment="Recursos específicos do plano em formato JSON"
    )
    
    restrictions = Column(
        JSON, 
        nullable=True,
        comment="Restrições específicas do plano em formato JSON"
    )
    
    # Controle de disponibilidade
    is_active = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="Indica se o plano está ativo para novas assinaturas"
    )
    
    is_visible = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="Indica se o plano é visível na interface"
    )
    
    sort_order = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Ordem de exibição dos planos"
    )
    
    # Período promocional
    promotional_start = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Início da promoção"
    )
    
    promotional_end = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Fim da promoção"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data de criação do plano"
    )
    
    updated_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="Data da última atualização"
    )
    
    # Relacionamentos
    subscriptions = relationship(
        "Subscription", 
        back_populates="plan"
    )
    
    # Índices para otimização
    __table_args__ = (
        Index('idx_plan_type', 'plan_type'),
        Index('idx_billing_cycle', 'billing_cycle'),
        Index('idx_is_active', 'is_active'),
        Index('idx_is_visible', 'is_visible'),
        Index('idx_sort_order', 'sort_order'),
        Index('idx_promotional_period', 'promotional_start', 'promotional_end'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'comment': 'Planos de assinatura da plataforma VOD'
        }
    )
    
    def __repr__(self):
        return f"<Plan(id={self.id}, name='{self.name}', type={self.plan_type.value}, price={self.price})>"
    
    @property
    def current_price(self):
        """
        Retorna o preço atual considerando promoções
        
        Returns:
            Decimal: Preço atual do plano
        """
        if self.is_promotional_active:
            return self.promotional_price or self.price
        return self.price
    
    @property
    def is_promotional_active(self):
        """
        Verifica se a promoção está ativa
        
        Returns:
            bool: True se a promoção estiver ativa
        """
        if not self.promotional_price or not self.promotional_start or not self.promotional_end:
            return False
        
        from datetime import datetime
        now = datetime.utcnow()
        return self.promotional_start <= now <= self.promotional_end
    
    @property
    def is_free(self):
        """
        Verifica se é um plano gratuito
        
        Returns:
            bool: True se for plano gratuito
        """
        return self.plan_type == PlanType.FREE or self.current_price == 0
    
    @property
    def monthly_equivalent_price(self):
        """
        Calcula o preço equivalente mensal
        
        Returns:
            Decimal: Preço mensal equivalente
        """
        price = self.current_price
        
        if self.billing_cycle == BillingCycle.MONTHLY:
            return price
        elif self.billing_cycle == BillingCycle.QUARTERLY:
            return price / 3
        elif self.billing_cycle == BillingCycle.YEARLY:
            return price / 12
        elif self.billing_cycle == BillingCycle.LIFETIME:
            # Assume 5 anos para cálculo de equivalência
            return price / (12 * 5)
        
        return price
    
    def get_feature(self, feature_name: str, default=None):
        """
        Obtém um recurso específico do plano
        
        Args:
            feature_name (str): Nome do recurso
            default: Valor padrão se não encontrado
            
        Returns:
            Valor do recurso ou default
        """
        if not self.features:
            return default
        return self.features.get(feature_name, default)
    
    def has_feature(self, feature_name: str) -> bool:
        """
        Verifica se o plano possui um recurso específico
        
        Args:
            feature_name (str): Nome do recurso
            
        Returns:
            bool: True se o plano possui o recurso
        """
        if not self.features:
            return False
        return feature_name in self.features and self.features[feature_name]
    
    def get_restriction(self, restriction_name: str, default=None):
        """
        Obtém uma restrição específica do plano
        
        Args:
            restriction_name (str): Nome da restrição
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da restrição ou default
        """
        if not self.restrictions:
            return default
        return self.restrictions.get(restriction_name, default)
    
    def to_dict(self, include_relationships=False):
        """
        Converte o modelo para dicionário
        
        Args:
            include_relationships (bool): Se deve incluir relacionamentos
            
        Returns:
            dict: Dados do plano
        """
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'plan_type': self.plan_type.value,
            'price': float(self.price),
            'promotional_price': float(self.promotional_price) if self.promotional_price else None,
            'current_price': float(self.current_price),
            'billing_cycle': self.billing_cycle.value,
            'currency': self.currency,
            'max_concurrent_streams': self.max_concurrent_streams,
            'max_download_quality': self.max_download_quality,
            'max_streaming_quality': self.max_streaming_quality,
            'offline_downloads_allowed': self.offline_downloads_allowed,
            'ads_free': self.ads_free,
            'features': self.features,
            'restrictions': self.restrictions,
            'is_active': self.is_active,
            'is_visible': self.is_visible,
            'is_free': self.is_free,
            'is_promotional_active': self.is_promotional_active,
            'monthly_equivalent_price': float(self.monthly_equivalent_price),
            'sort_order': self.sort_order,
            'promotional_start': self.promotional_start.isoformat() if self.promotional_start else None,
            'promotional_end': self.promotional_end.isoformat() if self.promotional_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_relationships:
            data['subscriptions_count'] = len(self.subscriptions) if self.subscriptions else 0
        
        return data