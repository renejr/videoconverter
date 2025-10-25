"""
Modelo de Notificação - Notification Service
Sistema de Mensageria para Plataforma VOD
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Any, Optional

Base = declarative_base()


class NotificationType(PyEnum):
    """
    Tipos de notificação disponíveis
    """
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationStatus(PyEnum):
    """
    Status de uma notificação
    """
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(PyEnum):
    """
    Prioridade de uma notificação
    """
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """
    Modelo para armazenar notificações
    
    Este modelo representa uma notificação que pode ser enviada
    por diferentes canais (email, SMS, push, etc.)
    """
    
    __tablename__ = "notifications"
    
    # Identificação
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    external_id = Column(String(255), unique=True, index=True, nullable=True,
                        comment="ID externo para rastreamento")
    
    # Tipo e canal
    type = Column(SQLEnum(NotificationType), nullable=False, index=True,
                 comment="Tipo de notificação")
    channel = Column(String(50), nullable=False, index=True,
                    comment="Canal de envio (email, sms, push)")
    
    # Destinatário
    recipient = Column(String(255), nullable=False, index=True,
                      comment="Destinatário da notificação")
    recipient_name = Column(String(255), nullable=True,
                           comment="Nome do destinatário")
    
    # Conteúdo
    subject = Column(String(500), nullable=True,
                    comment="Assunto da notificação")
    content = Column(Text, nullable=False,
                    comment="Conteúdo da notificação")
    html_content = Column(Text, nullable=True,
                         comment="Conteúdo HTML (para emails)")
    
    # Template
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True, index=True,
                        comment="ID do template utilizado")
    template_name = Column(String(100), nullable=True)
    template_data = Column(JSON, nullable=True,
                          comment="Dados para renderização do template")
    
    # Status e prioridade
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING,
                   nullable=False, index=True, comment="Status da notificação")
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL,
                     nullable=False, index=True, comment="Prioridade da notificação")
    
    # Agendamento
    scheduled_at = Column(DateTime, nullable=True, index=True,
                         comment="Data/hora agendada para envio")
    
    # Controle de tentativas
    attempts = Column(Integer, default=0, nullable=False,
                     comment="Número de tentativas de envio")
    max_attempts = Column(Integer, default=3, nullable=False,
                         comment="Máximo de tentativas permitidas")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True,
                       comment="Data/hora de criação")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(),
                       nullable=False, comment="Data/hora da última atualização")
    
    # Relacionamentos
    template = relationship("Template", backref="notifications")
    delivery_logs = relationship("DeliveryLog", back_populates="notification", cascade="all, delete-orphan")
    sent_at = Column(DateTime, nullable=True, index=True,
                    comment="Data/hora de envio")
    delivered_at = Column(DateTime, nullable=True, index=True,
                         comment="Data/hora de entrega confirmada")
    
    # Metadados
    notification_metadata = Column(JSON, nullable=True,
                                   comment="Metadados adicionais da notificação")
    
    # Configurações específicas
    provider_config = Column(JSON, nullable=True,
                           comment="Configurações específicas do provedor")
    
    # Rastreamento
    tracking_id = Column(String(255), nullable=True, index=True,
                        comment="ID de rastreamento do provedor")
    
    # Erro
    error_message = Column(Text, nullable=True,
                          comment="Mensagem de erro em caso de falha")
    error_code = Column(String(50), nullable=True,
                       comment="Código de erro")
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type}, recipient={self.recipient}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o modelo para dicionário
        """
        return {
            "id": self.id,
            "external_id": self.external_id,
            "type": self.type.value if self.type else None,
            "channel": self.channel,
            "recipient": self.recipient,
            "recipient_name": self.recipient_name,
            "subject": self.subject,
            "content": self.content,
            "html_content": self.html_content,
            "template_id": self.template_id,
            "template_data": self.template_data,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "metadata": self.metadata,
            "provider_config": self.provider_config,
            "tracking_id": self.tracking_id,
            "error_message": self.error_message,
            "error_code": self.error_code
        }
    
    @property
    def is_pending(self) -> bool:
        """Verifica se a notificação está pendente"""
        return self.status == NotificationStatus.PENDING
    
    @property
    def is_sent(self) -> bool:
        """Verifica se a notificação foi enviada"""
        return self.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED]
    
    @property
    def is_failed(self) -> bool:
        """Verifica se a notificação falhou"""
        return self.status == NotificationStatus.FAILED
    
    @property
    def can_retry(self) -> bool:
        """Verifica se a notificação pode ser reenviada"""
        return self.attempts < self.max_attempts and not self.is_sent