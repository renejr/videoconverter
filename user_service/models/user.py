"""
Modelo de Usuário - Domínio A
Sistema de Identidade e Transações para Plataforma VOD
"""

from sqlalchemy import Column, BigInteger, String, Date, Boolean, TIMESTAMP, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class User(Base):
    """
    Modelo de Usuário
    
    Representa a entidade principal do sistema de identidade.
    Armazena informações básicas do usuário como email, nome,
    preferências e status da conta.
    
    Relacionamentos:
    - Um usuário pode ter uma credencial (1:1)
    - Um usuário pode ter múltiplas assinaturas (1:N)
    - Um usuário pode ter múltiplos pagamentos (1:N)
    - Um usuário pode ter múltiplas faturas (1:N)
    - Um usuário pode ter múltiplas sessões (1:N)
    """
    
    __tablename__ = 'users'
    
    # Chave primária
    id = Column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True,
        comment="Identificador único do usuário"
    )
    
    # Informações básicas
    email = Column(
        String(255), 
        nullable=False, 
        unique=True,
        comment="Email do usuário (único no sistema)"
    )
    
    first_name = Column(
        String(100), 
        nullable=False,
        comment="Primeiro nome do usuário"
    )
    
    last_name = Column(
        String(100), 
        nullable=False,
        comment="Sobrenome do usuário"
    )
    
    phone = Column(
        String(20), 
        nullable=True,
        comment="Telefone do usuário (opcional)"
    )
    
    date_of_birth = Column(
        Date, 
        nullable=True,
        comment="Data de nascimento (opcional)"
    )
    
    # Configurações regionais
    country_code = Column(
        String(2), 
        nullable=False, 
        default='BR',
        comment="Código do país (ISO 3166-1 alpha-2)"
    )
    
    language_preference = Column(
        String(5), 
        nullable=False, 
        default='pt-BR',
        comment="Preferência de idioma (formato locale)"
    )
    
    timezone = Column(
        String(50), 
        nullable=False, 
        default='America/Sao_Paulo',
        comment="Timezone do usuário"
    )
    
    # Status da conta
    is_active = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="Indica se a conta está ativa"
    )
    
    is_verified = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="Indica se o email foi verificado"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data e hora de criação da conta"
    )
    
    updated_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="Data e hora da última atualização"
    )
    
    last_login_at = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data e hora do último login"
    )
    
    # Relacionamentos
    credential = relationship(
        "Credential", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    subscriptions = relationship(
        "Subscription", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    payments = relationship(
        "Payment", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    invoices = relationship(
        "Invoice", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    sessions = relationship(
        "UserSession", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Índices para otimização de consultas
    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_active_verified', 'is_active', 'is_verified'),
        Index('idx_created_at', 'created_at'),
        Index('idx_last_login', 'last_login_at'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'comment': 'Tabela principal de usuários - informações básicas e perfil'
        }
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.first_name} {self.last_name}')>"
    
    @property
    def full_name(self):
        """Retorna o nome completo do usuário"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_account_complete(self):
        """Verifica se a conta está completa (verificada e ativa)"""
        return self.is_active and self.is_verified
    
    @property
    def is_premium(self):
        """
        Verifica se o usuário tem assinatura premium ativa
        
        Returns:
            bool: True se o usuário tem assinatura premium ativa
        """
        if not self.subscriptions:
            return False
        
        # Importação local para evitar dependência circular
        from .subscription import SubscriptionStatus
        from .plan import PlanType
        
        for subscription in self.subscriptions:
            if (subscription.status == SubscriptionStatus.ACTIVE and 
                subscription.plan and 
                subscription.plan.plan_type == PlanType.PREMIUM):
                return True
        return False
    
    @property
    def profile_completion(self):
        """
        Calcula o percentual de completude do perfil do usuário
        
        Returns:
            int: Percentual de completude (0-100)
        """
        total_fields = 8  # Total de campos considerados
        completed_fields = 0
        
        # Campos obrigatórios (sempre preenchidos na criação)
        completed_fields += 3  # email, first_name, last_name
        
        # Campos opcionais
        if self.phone:
            completed_fields += 1
        if self.date_of_birth:
            completed_fields += 1
        if self.country_code and self.country_code != 'BR':  # Se mudou do padrão
            completed_fields += 1
        if self.language_preference and self.language_preference != 'pt-BR':  # Se mudou do padrão
            completed_fields += 1
        if self.is_verified:  # Email verificado
            completed_fields += 1
        
        return int((completed_fields / total_fields) * 100)
    
    def to_dict(self):
        """
        Converte o modelo para dicionário
        
        Útil para serialização JSON, excluindo campos sensíveis
        """
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'country_code': self.country_code,
            'language_preference': self.language_preference,
            'timezone': self.timezone,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_premium': self.is_premium,
            'profile_completion': self.profile_completion,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
        }