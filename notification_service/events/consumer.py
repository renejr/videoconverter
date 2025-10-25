"""
Event Bus Consumer - Notification Service
Consome eventos do Redis e direciona para os handlers apropriados
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import redis.asyncio as redis
from config.settings import settings
from .user_handlers import UserEventHandlers
from services.email_service import EmailService

logger = logging.getLogger(__name__)


class EventBusConsumer:
    """
    Consumer responsável por escutar eventos do Event Bus (Redis)
    e direcioná-los para os handlers apropriados
    """
    
    def __init__(self):
        """
        Inicializa o consumer
        """
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
        # Inicializar EmailService
        self.email_service = EmailService()
        
        # Inicializar handlers com o EmailService
        self.user_handlers = UserEventHandlers(email_service=self.email_service)
        self.running = False
        
        # Canais que vamos escutar
        self.channels = [
            "vidconv.events.user.*",  # Todos os eventos de usuário
            "vidconv.events.test",    # Canal de teste
        ]
    
    async def connect(self) -> bool:
        """
        Conecta ao Redis
        
        Returns:
            bool: True se conectado com sucesso
        """
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True
            )
            
            # Testa a conexão
            await self.redis_client.ping()
            logger.info("✅ Conectado ao Redis Event Bus")
            
            # Inicializa PubSub
            self.pubsub = self.redis_client.pubsub()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao Redis: {str(e)}")
            return False
    
    async def disconnect(self):
        """
        Desconecta do Redis
        """
        try:
            if self.pubsub:
                await self.pubsub.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("🔌 Desconectado do Redis Event Bus")
            
        except Exception as e:
            logger.error(f"❌ Erro ao desconectar do Redis: {str(e)}")
    
    async def subscribe_to_channels(self):
        """
        Inscreve-se nos canais de eventos
        """
        try:
            if not self.pubsub:
                raise Exception("PubSub não inicializado")
            
            # Inscreve-se nos canais usando pattern matching
            for channel in self.channels:
                if "*" in channel:
                    await self.pubsub.psubscribe(channel)
                    logger.info(f"📡 Inscrito no padrão de canal: {channel}")
                else:
                    await self.pubsub.subscribe(channel)
                    logger.info(f"📡 Inscrito no canal: {channel}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao se inscrever nos canais: {str(e)}")
            raise
    
    async def start_consuming(self):
        """
        Inicia o consumo de eventos
        """
        try:
            if not await self.connect():
                raise Exception("Falha na conexão com Redis")
            
            await self.subscribe_to_channels()
            self.running = True
            
            logger.info("🚀 Iniciando consumo de eventos...")
            
            async for message in self.pubsub.listen():
                if not self.running:
                    break
                
                await self._process_message(message)
                
        except Exception as e:
            logger.error(f"❌ Erro no consumo de eventos: {str(e)}")
            raise
        finally:
            await self.disconnect()
    
    async def stop_consuming(self):
        """
        Para o consumo de eventos
        """
        self.running = False
        logger.info("🛑 Parando consumo de eventos...")
    
    async def _process_message(self, message: Dict[str, Any]):
        """
        Processa uma mensagem recebida
        
        Args:
            message: Mensagem do Redis PubSub
        """
        try:
            # Ignora mensagens de controle
            if message['type'] not in ['message', 'pmessage']:
                return
            
            # Extrai dados da mensagem
            channel = message.get('channel', '')
            data = message.get('data', '')
            
            if not data:
                return
            
            logger.info(f"📨 Mensagem recebida no canal {channel}")
            
            # Parse do JSON
            try:
                event_data = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Erro ao fazer parse do JSON: {str(e)}")
                return
            
            # Extrai tipo do evento
            event_type = event_data.get('event_type') or event_data.get('type')
            if not event_type:
                logger.warning("⚠️ Evento sem tipo definido")
                return
            
            # Direciona para o handler apropriado
            await self._route_event(event_type, event_data)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {str(e)}")
    
    async def _route_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Direciona o evento para o handler apropriado
        
        Args:
            event_type: Tipo do evento
            event_data: Dados do evento
        """
        try:
            # Eventos de usuário
            if event_type.startswith('user.'):
                await self.user_handlers.handle_event(event_type, event_data)
            
            # Eventos de teste
            elif event_type == 'test':
                logger.info(f"🧪 Evento de teste recebido: {event_data}")
            
            # Outros tipos de evento
            else:
                logger.warning(f"⚠️ Tipo de evento não reconhecido: {event_type}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao rotear evento {event_type}: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica a saúde do consumer
        
        Returns:
            Dict com informações de saúde
        """
        try:
            if not self.redis_client:
                return {
                    "status": "disconnected",
                    "redis_connected": False,
                    "consuming": False
                }
            
            # Testa conexão Redis
            await self.redis_client.ping()
            
            return {
                "status": "healthy" if self.running else "stopped",
                "redis_connected": True,
                "consuming": self.running,
                "subscribed_channels": self.channels
            }
            
        except Exception as e:
            return {
                "status": "error",
                "redis_connected": False,
                "consuming": False,
                "error": str(e)
            }


# Instância global do consumer
event_consumer = EventBusConsumer()