"""
Modelo de Sessões de Usuário - Domínio A
Sistema de Identidade e Transações para Plataforma VOD
"""

from sqlalchemy import Column, BigInteger, String, Boolean, TIMESTAMP, ForeignKey, Index, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime, timedelta
import secrets


class UserSession(Base):
    """
    Modelo de Sessões de Usuário
    
    Gerencia as sessões ativas dos usuários na plataforma,
    incluindo tokens de acesso, informações do dispositivo,
    localização e controle de expiração.
    
    Relacionamentos:
    - Uma sessão pertence a um usuário (N:1)
    
    Recursos:
    - Tokens seguros para autenticação
    - Informações detalhadas do dispositivo
    - Controle de expiração automática
    - Rastreamento de localização (IP/geolocalização)
    - Histórico de atividade
    """
    
    __tablename__ = 'user_sessions'
    
    # Chave primária
    id = Column(
        BigInteger, 
        primary_key=True, 
        autoincrement=True,
        comment="Identificador único da sessão"
    )
    
    # Chave estrangeira
    user_id = Column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        comment="ID do usuário proprietário da sessão"
    )
    
    # Token de sessão
    session_token = Column(
        String(255), 
        nullable=False, 
        unique=True,
        comment="Token único da sessão"
    )
    
    refresh_token = Column(
        String(255), 
        nullable=True, 
        unique=True,
        comment="Token de renovação da sessão"
    )
    
    # Informações do dispositivo
    device_id = Column(
        String(255), 
        nullable=True,
        comment="Identificador único do dispositivo"
    )
    
    device_name = Column(
        String(100), 
        nullable=True,
        comment="Nome do dispositivo (ex: 'iPhone de João')"
    )
    
    device_type = Column(
        String(50), 
        nullable=True,
        comment="Tipo do dispositivo (mobile, desktop, tablet, tv)"
    )
    
    operating_system = Column(
        String(50), 
        nullable=True,
        comment="Sistema operacional (iOS, Android, Windows, etc.)"
    )
    
    browser = Column(
        String(100), 
        nullable=True,
        comment="Navegador utilizado"
    )
    
    app_version = Column(
        String(20), 
        nullable=True,
        comment="Versão do aplicativo"
    )
    
    # Informações de localização
    ip_address = Column(
        String(45), 
        nullable=True,
        comment="Endereço IP da sessão (suporta IPv4 e IPv6)"
    )
    
    country = Column(
        String(2), 
        nullable=True,
        comment="Código do país (ISO 3166-1 alpha-2)"
    )
    
    region = Column(
        String(100), 
        nullable=True,
        comment="Estado/região"
    )
    
    city = Column(
        String(100), 
        nullable=True,
        comment="Cidade"
    )
    
    timezone = Column(
        String(50), 
        nullable=True,
        comment="Fuso horário do usuário"
    )
    
    # Controle de sessão
    is_active = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="Indica se a sessão está ativa"
    )
    
    expires_at = Column(
        TIMESTAMP, 
        nullable=False,
        comment="Data de expiração da sessão"
    )
    
    last_activity_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data da última atividade na sessão"
    )
    
    # Informações de login
    login_method = Column(
        String(50), 
        nullable=True,
        comment="Método de login (password, google, facebook, etc.)"
    )
    
    two_factor_verified = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="Indica se a autenticação de dois fatores foi verificada"
    )
    
    # Metadados da sessão
    session_metadata = Column(
        JSON, 
        nullable=True,
        comment="Metadados específicos da sessão em JSON"
    )
    
    # Informações de segurança
    is_suspicious = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="Indica se a sessão foi marcada como suspeita"
    )
    
    security_flags = Column(
        JSON, 
        nullable=True,
        comment="Flags de segurança em JSON"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=func.current_timestamp(),
        comment="Data de criação da sessão"
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
        back_populates="sessions"
    )
    
    # Índices para otimização
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_session_token', 'session_token'),
        Index('idx_refresh_token', 'refresh_token'),
        Index('idx_device_id', 'device_id'),
        Index('idx_is_active', 'is_active'),
        Index('idx_expires_at', 'expires_at'),
        Index('idx_last_activity', 'last_activity_at'),
        Index('idx_ip_address', 'ip_address'),
        Index('idx_user_active', 'user_id', 'is_active'),
        Index('idx_user_device', 'user_id', 'device_id'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'comment': 'Sessões ativas dos usuários na plataforma'
        }
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, device_type='{self.device_type}', is_active={self.is_active})>"
    
    @property
    def is_expired(self):
        """
        Verifica se a sessão expirou
        
        Returns:
            bool: True se a sessão expirou
        """
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """
        Verifica se a sessão é válida (ativa e não expirada)
        
        Returns:
            bool: True se a sessão é válida
        """
        return self.is_active and not self.is_expired
    
    @property
    def time_until_expiry(self):
        """
        Calcula o tempo restante até a expiração
        
        Returns:
            timedelta: Tempo restante (negativo se expirada)
        """
        return self.expires_at - datetime.utcnow()
    
    @property
    def minutes_until_expiry(self):
        """
        Calcula quantos minutos faltam para expirar
        
        Returns:
            int: Minutos até expirar (negativo se expirada)
        """
        delta = self.time_until_expiry
        return int(delta.total_seconds() / 60)
    
    @property
    def time_since_last_activity(self):
        """
        Calcula o tempo desde a última atividade
        
        Returns:
            timedelta: Tempo desde última atividade
        """
        return datetime.utcnow() - self.last_activity_at
    
    @property
    def minutes_since_last_activity(self):
        """
        Calcula quantos minutos desde a última atividade
        
        Returns:
            int: Minutos desde última atividade
        """
        delta = self.time_since_last_activity
        return int(delta.total_seconds() / 60)
    
    @staticmethod
    def generate_session_token():
        """
        Gera um token de sessão seguro
        
        Returns:
            str: Token de sessão
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_refresh_token():
        """
        Gera um token de renovação seguro
        
        Returns:
            str: Token de renovação
        """
        return secrets.token_urlsafe(32)
    
    def extend_session(self, hours: int = 24):
        """
        Estende a sessão por um número de horas
        
        Args:
            hours (int): Número de horas para estender
        """
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.update_activity()
    
    def update_activity(self):
        """
        Atualiza a última atividade da sessão
        """
        self.last_activity_at = datetime.utcnow()
    
    def invalidate(self):
        """
        Invalida a sessão
        """
        self.is_active = False
        self.expires_at = datetime.utcnow()
    
    def refresh(self):
        """
        Renova os tokens da sessão
        
        Returns:
            tuple: (novo_session_token, novo_refresh_token)
        """
        self.session_token = self.generate_session_token()
        self.refresh_token = self.generate_refresh_token()
        self.extend_session()
        
        return self.session_token, self.refresh_token
    
    def mark_as_suspicious(self, reason: str = None):
        """
        Marca a sessão como suspeita
        
        Args:
            reason (str): Motivo da suspeita
        """
        self.is_suspicious = True
        
        if reason:
            flags = self.security_flags or {}
            flags['suspicious_reason'] = reason
            flags['marked_suspicious_at'] = datetime.utcnow().isoformat()
            self.security_flags = flags
    
    def add_security_flag(self, flag: str, value=True, description: str = None):
        """
        Adiciona uma flag de segurança
        
        Args:
            flag (str): Nome da flag
            value: Valor da flag
            description (str): Descrição da flag
        """
        if not self.security_flags:
            self.security_flags = {}
        
        self.security_flags[flag] = {
            'value': value,
            'description': description,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_metadata(self, key: str, default=None):
        """
        Obtém um valor dos metadados
        
        Args:
            key (str): Chave do metadado
            default: Valor padrão
            
        Returns:
            Valor do metadado ou default
        """
        if not self.session_metadata:
            return default
        return self.session_metadata.get(key, default)
    
    def set_metadata(self, key: str, value):
        """
        Define um valor nos metadados
        
        Args:
            key (str): Chave do metadado
            value: Valor a ser definido
        """
        if not self.session_metadata:
            self.session_metadata = {}
        self.session_metadata[key] = value
    
    def get_location_string(self):
        """
        Retorna uma string formatada da localização
        
        Returns:
            str: Localização formatada
        """
        parts = []
        
        if self.city:
            parts.append(self.city)
        if self.region:
            parts.append(self.region)
        if self.country:
            parts.append(self.country.upper())
        
        return ', '.join(parts) if parts else 'Localização desconhecida'
    
    def get_device_string(self):
        """
        Retorna uma string formatada do dispositivo
        
        Returns:
            str: Dispositivo formatado
        """
        parts = []
        
        if self.device_name:
            return self.device_name
        
        if self.device_type:
            parts.append(self.device_type.title())
        
        if self.operating_system:
            parts.append(self.operating_system)
        
        if self.browser:
            parts.append(self.browser)
        
        return ' - '.join(parts) if parts else 'Dispositivo desconhecido'
    
    def to_dict(self, include_sensitive=False):
        """
        Converte o modelo para dicionário
        
        Args:
            include_sensitive (bool): Se deve incluir dados sensíveis
            
        Returns:
            dict: Dados da sessão
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'operating_system': self.operating_system,
            'browser': self.browser,
            'app_version': self.app_version,
            'country': self.country,
            'region': self.region,
            'city': self.city,
            'timezone': self.timezone,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'login_method': self.login_method,
            'two_factor_verified': self.two_factor_verified,
            'is_suspicious': self.is_suspicious,
            'is_expired': self.is_expired,
            'is_valid': self.is_valid,
            'minutes_until_expiry': self.minutes_until_expiry,
            'minutes_since_last_activity': self.minutes_since_last_activity,
            'location_string': self.get_location_string(),
            'device_string': self.get_device_string(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Inclui dados sensíveis apenas se solicitado
        if include_sensitive:
            data.update({
                'session_token': self.session_token,
                'refresh_token': self.refresh_token,
                'ip_address': self.ip_address,
                'session_metadata': self.session_metadata,
                'security_flags': self.security_flags,
            })
        
        return data