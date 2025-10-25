"""
Delivery Log Model - Modelo de Log de Entrega
Notification Service - Plataforma VOD
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional

from database.connection import Base


class DeliveryLog(Base):
    """
    Modelo para log de entrega de notificações
    """
    __tablename__ = "delivery_logs"
    
    # Identificação
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False, index=True)
    
    # Informações de entrega
    provider = Column(String(50), nullable=False)  # gmail, twilio, etc.
    channel = Column(String(20), nullable=False)  # email, sms, push
    recipient = Column(String(255), nullable=False, index=True)
    
    # Status da entrega
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, delivered, failed, bounced
    attempt_number = Column(Integer, default=1, nullable=False)
    
    # Detalhes técnicos
    provider_message_id = Column(String(255))  # ID do provedor (Gmail, Twilio, etc.)
    provider_response = Column(JSON)  # Resposta completa do provedor
    
    # Timing
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))  # Para emails
    clicked_at = Column(DateTime(timezone=True))  # Para links em emails
    
    # Erro
    error_code = Column(String(50))
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Metadados
    delivery_metadata = Column(JSON, default=dict)
    user_agent = Column(String(500))  # Para tracking de abertura
    ip_address = Column(String(45))  # Para tracking de abertura
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    notification = relationship("Notification", back_populates="delivery_logs")
    
    def __repr__(self):
        return f"<DeliveryLog(id={self.id}, notification_id={self.notification_id}, status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o log de entrega para dicionário
        """
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "provider": self.provider,
            "channel": self.channel,
            "recipient": self.recipient,
            "status": self.status,
            "attempt_number": self.attempt_number,
            "provider_message_id": self.provider_message_id,
            "provider_response": self.provider_response,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "metadata": self.metadata,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_successful(self) -> bool:
        """
        Verifica se a entrega foi bem-sucedida
        """
        return self.status in ["sent", "delivered"]
    
    def is_failed(self) -> bool:
        """
        Verifica se a entrega falhou
        """
        return self.status in ["failed", "bounced"]
    
    def is_pending(self) -> bool:
        """
        Verifica se a entrega está pendente
        """
        return self.status == "pending"
    
    def get_delivery_time(self) -> Optional[float]:
        """
        Calcula o tempo de entrega em segundos
        """
        if self.sent_at and self.delivered_at:
            delta = self.delivered_at - self.sent_at
            return delta.total_seconds()
        return None
    
    def get_processing_time(self) -> Optional[float]:
        """
        Calcula o tempo de processamento em segundos
        """
        if self.created_at and self.sent_at:
            delta = self.sent_at - self.created_at
            return delta.total_seconds()
        return None
    
    def mark_as_sent(self, provider_message_id: str = None, provider_response: Dict = None):
        """
        Marca como enviado
        """
        self.status = "sent"
        self.sent_at = datetime.utcnow()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        if provider_response:
            self.provider_response = provider_response
    
    def mark_as_delivered(self):
        """
        Marca como entregue
        """
        self.status = "delivered"
        self.delivered_at = datetime.utcnow()
    
    def mark_as_failed(self, error_code: str = None, error_message: str = None, error_details: Dict = None):
        """
        Marca como falhou
        """
        self.status = "failed"
        if error_code:
            self.error_code = error_code
        if error_message:
            self.error_message = error_message
        if error_details:
            self.error_details = error_details
    
    def mark_as_opened(self, user_agent: str = None, ip_address: str = None):
        """
        Marca como aberto (para emails)
        """
        self.opened_at = datetime.utcnow()
        if user_agent:
            self.user_agent = user_agent
        if ip_address:
            self.ip_address = ip_address
    
    def mark_as_clicked(self, user_agent: str = None, ip_address: str = None):
        """
        Marca como clicado (para links em emails)
        """
        self.clicked_at = datetime.utcnow()
        if user_agent:
            self.user_agent = user_agent
        if ip_address:
            self.ip_address = ip_address