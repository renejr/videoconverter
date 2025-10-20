"""
Modelo de Credenciais - Domínio A
Sistema de Identidade e Transações para Plataforma VOD
"""

from sqlalchemy import Column, BigInteger, String, Integer, Boolean, TIMESTAMP, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class Credential(Base):
    """
    Modelo de Credenciais
    
    Armazena informações de autenticação e segurança dos usuários.
    Inclui hash da senha, controle de tentativas de login,
    autenticação de dois fatores e códigos de recuperação.
    
    Relacionamentos:
    - Uma credencial pertence a um usuário (N:1)
    
    Segurança:
    - Senhas são armazenadas com hash + salt
    - Controle de tentativas de login falhadas
    - Suporte a 2FA (Two-Factor Authentication)
    - Códigos de recuperação em JSON
    """
    
    __tablename__ = 'credentials'
    
    # Chave primária
    id = Column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True,
        comment="Identificador único da credencial"
    )
    
    # Chave estrangeira para usuário
    user_id = Column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        comment="ID do usuário proprietário desta credencial"
    )
    
    # Informações de autenticação
    password_hash = Column(
        String(255), 
        nullable=False,
        comment="Hash da senha do usuário (bcrypt)"
    )
    
    salt = Column(
        String(255), 
        nullable=False,
        comment="Salt usado na geração do hash da senha"
    )
    
    password_changed_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data da última alteração de senha"
    )
    
    # Controle de segurança
    failed_login_attempts = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Número de tentativas de login falhadas consecutivas"
    )
    
    locked_until = Column(
        TIMESTAMP, 
        nullable=True,
        comment="Data até quando a conta está bloqueada (null = não bloqueada)"
    )
    
    # Autenticação de dois fatores (2FA)
    two_factor_enabled = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="Indica se a autenticação de dois fatores está habilitada"
    )
    
    two_factor_secret = Column(
        String(255), 
        nullable=True,
        comment="Chave secreta para TOTP (Time-based One-Time Password)"
    )
    
    recovery_codes = Column(
        JSON, 
        nullable=True,
        comment="Códigos de recuperação para 2FA (array JSON)"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data de criação da credencial"
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
        back_populates="credential"
    )
    
    # Índices para otimização
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_password_changed', 'password_changed_at'),
        Index('idx_locked_until', 'locked_until'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'comment': 'Credenciais de autenticação e segurança dos usuários'
        }
    )
    
    def __repr__(self):
        return f"<Credential(id={self.id}, user_id={self.user_id}, 2fa_enabled={self.two_factor_enabled})>"
    
    @property
    def is_locked(self):
        """
        Verifica se a conta está bloqueada
        
        Returns:
            bool: True se a conta estiver bloqueada
        """
        if self.locked_until is None:
            return False
        
        from datetime import datetime
        return datetime.utcnow() < self.locked_until
    
    @property
    def can_attempt_login(self):
        """
        Verifica se é possível tentar fazer login
        
        Returns:
            bool: True se login é permitido
        """
        return not self.is_locked
    
    def increment_failed_attempts(self):
        """
        Incrementa o contador de tentativas falhadas
        
        Se atingir o limite (5 tentativas), bloqueia a conta por 30 minutos
        """
        self.failed_login_attempts += 1
        
        # Bloqueia após 5 tentativas falhadas
        if self.failed_login_attempts >= 5:
            from datetime import datetime, timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_attempts(self):
        """
        Reseta o contador de tentativas falhadas após login bem-sucedido
        """
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def enable_two_factor(self, secret: str, recovery_codes: list):
        """
        Habilita autenticação de dois fatores
        
        Args:
            secret (str): Chave secreta TOTP
            recovery_codes (list): Lista de códigos de recuperação
        """
        self.two_factor_enabled = True
        self.two_factor_secret = secret
        self.recovery_codes = recovery_codes
    
    def disable_two_factor(self):
        """
        Desabilita autenticação de dois fatores
        """
        self.two_factor_enabled = False
        self.two_factor_secret = None
        self.recovery_codes = None
    
    def use_recovery_code(self, code: str) -> bool:
        """
        Usa um código de recuperação
        
        Args:
            code (str): Código de recuperação
            
        Returns:
            bool: True se o código foi válido e usado
        """
        if not self.recovery_codes or code not in self.recovery_codes:
            return False
        
        # Remove o código usado da lista
        self.recovery_codes.remove(code)
        return True
    
    def to_dict(self, include_sensitive=False):
        """
        Converte o modelo para dicionário
        
        Args:
            include_sensitive (bool): Se deve incluir dados sensíveis
            
        Returns:
            dict: Dados da credencial
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'password_changed_at': self.password_changed_at.isoformat() if self.password_changed_at else None,
            'failed_login_attempts': self.failed_login_attempts,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'two_factor_enabled': self.two_factor_enabled,
            'is_locked': self.is_locked,
            'can_attempt_login': self.can_attempt_login,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Inclui dados sensíveis apenas se solicitado (para debug/admin)
        if include_sensitive:
            data.update({
                'password_hash': self.password_hash,
                'salt': self.salt,
                'two_factor_secret': self.two_factor_secret,
                'recovery_codes': self.recovery_codes,
            })
        
        return data