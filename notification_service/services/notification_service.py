"""
Notification Service - Serviço Principal de Notificações
Notification Service - Plataforma VOD
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.notification import (
    Notification, NotificationType, NotificationStatus, 
    NotificationPriority
)
from models.delivery_log import DeliveryLog
from database.connection import get_db
from services.email_service import EmailService
from services.template_service import TemplateService


logger = logging.getLogger(__name__)


class NotificationService:
    """
    Serviço principal para gerenciamento de notificações
    """
    
    def __init__(self):
        """
        Inicializa o serviço de notificações
        """
        self.email_service = EmailService()
        self.template_service = TemplateService()
    
    async def create_notification(
        self,
        type: NotificationType,
        recipient: str,
        channel: str = "email",
        priority: NotificationPriority = NotificationPriority.NORMAL,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        subject: Optional[str] = None,
        content: Optional[str] = None,
        scheduled_for: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Cria uma nova notificação
        """
        try:
            db = next(get_db())
            
            # Cria a notificação
            notification = Notification(
                type=type,
                channel=channel,
                recipient=recipient,
                subject=subject,
                content=content,
                template_name=template_name,
                template_data=template_data or {},
                status=NotificationStatus.PENDING,
                priority=priority,
                scheduled_for=scheduled_for or datetime.utcnow(),
                metadata=metadata or {}
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            logger.info(f"Notificação criada: ID {notification.id}, Tipo: {type}, Destinatário: {recipient}")
            
            # Se não está agendada para o futuro, processa imediatamente
            if not scheduled_for or scheduled_for <= datetime.utcnow():
                await self._process_notification(notification, db)
            
            return notification
            
        except Exception as e:
            logger.error(f"Erro ao criar notificação: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    async def _process_notification(self, notification: Notification, db: Session):
        """
        Processa uma notificação específica
        """
        try:
            # Atualiza status para processando
            notification.status = NotificationStatus.PROCESSING
            notification.attempts += 1
            notification.last_attempt = datetime.utcnow()
            db.commit()
            
            # Processa baseado no canal
            if notification.channel == "email":
                success = await self._send_email_notification(notification)
            elif notification.channel == "sms":
                success = await self._send_sms_notification(notification)
            else:
                logger.error(f"Canal não suportado: {notification.channel}")
                success = False
            
            # Atualiza status baseado no resultado
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                logger.info(f"Notificação enviada com sucesso: ID {notification.id}")
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = "Falha no envio"
                logger.error(f"Falha ao enviar notificação: ID {notification.id}")
            
            db.commit()
            
            # Registra log de entrega
            await self._create_delivery_log(notification, success, db)
            
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            db.commit()
            logger.error(f"Erro ao processar notificação {notification.id}: {str(e)}")
    
    async def _send_email_notification(self, notification: Notification) -> bool:
        """
        Envia notificação por email
        """
        try:
            if notification.template_name:
                # Usa template
                return await self.email_service.send_template_email(
                    to_email=notification.recipient,
                    template_name=notification.template_name,
                    template_data=notification.template_data,
                    subject=notification.subject
                )
            else:
                # Usa conteúdo direto
                return await self.email_service.send_email(
                    to_email=notification.recipient,
                    subject=notification.subject or "Notificação",
                    html_content=notification.content or "",
                    text_content=None
                )
                
        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")
            return False
    
    async def _send_sms_notification(self, notification: Notification) -> bool:
        """
        Envia notificação por SMS (implementação futura)
        """
        # TODO: Implementar integração com provedor de SMS (Twilio, etc.)
        logger.warning("Envio de SMS não implementado ainda")
        return False
    
    async def _create_delivery_log(self, notification: Notification, success: bool, db: Session):
        """
        Cria log de entrega
        """
        try:
            delivery_log = DeliveryLog(
                notification_id=notification.id,
                attempt_number=notification.attempts,
                status="delivered" if success else "failed",
                provider=notification.provider_config.get("provider", "unknown") if notification.provider_config else "unknown",
                response_data={
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": notification.error_message if not success else None
                }
            )
            
            db.add(delivery_log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Erro ao criar log de entrega: {str(e)}")
    
    async def process_pending_notifications(self):
        """
        Processa notificações pendentes
        """
        try:
            db = next(get_db())
            
            # Busca notificações pendentes que devem ser enviadas
            pending_notifications = db.query(Notification).filter(
                and_(
                    Notification.status == NotificationStatus.PENDING,
                    Notification.scheduled_for <= datetime.utcnow()
                )
            ).order_by(
                Notification.priority.desc(),
                Notification.created_at.asc()
            ).limit(100).all()
            
            logger.info(f"Processando {len(pending_notifications)} notificações pendentes")
            
            for notification in pending_notifications:
                await self._process_notification(notification, db)
            
        except Exception as e:
            logger.error(f"Erro ao processar notificações pendentes: {str(e)}")
        finally:
            db.close()
    
    async def retry_failed_notifications(self, max_retries: int = 3):
        """
        Reprocessa notificações que falharam
        """
        try:
            db = next(get_db())
            
            # Busca notificações que falharam e ainda podem ser reprocessadas
            failed_notifications = db.query(Notification).filter(
                and_(
                    Notification.status == NotificationStatus.FAILED,
                    Notification.attempts < max_retries,
                    Notification.last_attempt < datetime.utcnow() - timedelta(minutes=30)  # Aguarda 30 min entre tentativas
                )
            ).limit(50).all()
            
            logger.info(f"Reprocessando {len(failed_notifications)} notificações que falharam")
            
            for notification in failed_notifications:
                await self._process_notification(notification, db)
            
        except Exception as e:
            logger.error(f"Erro ao reprocessar notificações: {str(e)}")
        finally:
            db.close()
    
    async def get_notification_by_id(self, notification_id: int) -> Optional[Notification]:
        """
        Busca notificação por ID
        """
        try:
            db = next(get_db())
            return db.query(Notification).filter(Notification.id == notification_id).first()
        except Exception as e:
            logger.error(f"Erro ao buscar notificação: {str(e)}")
            return None
        finally:
            db.close()
    
    async def get_notifications_by_recipient(
        self, 
        recipient: str, 
        limit: int = 50,
        status: Optional[NotificationStatus] = None
    ) -> List[Notification]:
        """
        Busca notificações por destinatário
        """
        try:
            db = next(get_db())
            
            query = db.query(Notification).filter(Notification.recipient == recipient)
            
            if status:
                query = query.filter(Notification.status == status)
            
            return query.order_by(Notification.created_at.desc()).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Erro ao buscar notificações por destinatário: {str(e)}")
            return []
        finally:
            db.close()
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de notificações
        """
        try:
            db = next(get_db())
            
            # Estatísticas gerais
            total = db.query(Notification).count()
            sent = db.query(Notification).filter(Notification.status == NotificationStatus.SENT).count()
            failed = db.query(Notification).filter(Notification.status == NotificationStatus.FAILED).count()
            pending = db.query(Notification).filter(Notification.status == NotificationStatus.PENDING).count()
            
            # Estatísticas por tipo
            type_stats = {}
            for notification_type in NotificationType:
                count = db.query(Notification).filter(Notification.type == notification_type).count()
                type_stats[notification_type.value] = count
            
            # Estatísticas por canal
            channel_stats = {}
            channels = db.query(Notification.channel).distinct().all()
            for (channel,) in channels:
                count = db.query(Notification).filter(Notification.channel == channel).count()
                channel_stats[channel] = count
            
            return {
                "total": total,
                "sent": sent,
                "failed": failed,
                "pending": pending,
                "success_rate": (sent / total * 100) if total > 0 else 0,
                "by_type": type_stats,
                "by_channel": channel_stats,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {}
        finally:
            db.close()
    
    async def cancel_notification(self, notification_id: int) -> bool:
        """
        Cancela uma notificação pendente
        """
        try:
            db = next(get_db())
            
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            
            if not notification:
                logger.warning(f"Notificação não encontrada: {notification_id}")
                return False
            
            if notification.status != NotificationStatus.PENDING:
                logger.warning(f"Notificação não pode ser cancelada (status: {notification.status})")
                return False
            
            notification.status = NotificationStatus.CANCELLED
            notification.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Notificação cancelada: {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao cancelar notificação: {str(e)}")
            return False
        finally:
            db.close()
    
    async def schedule_notification(
        self,
        type: NotificationType,
        recipient: str,
        scheduled_for: datetime,
        **kwargs
    ) -> Notification:
        """
        Agenda uma notificação para envio futuro
        """
        return await self.create_notification(
            type=type,
            recipient=recipient,
            scheduled_for=scheduled_for,
            **kwargs
        )