"""
Event Bus - Sistema de Comunicação entre Domínios
Notification Service - Plataforma VOD
"""

import json
import logging
import asyncio
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime
import redis.asyncio as redis
from config.settings import settings

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event Bus para comunicação assíncrona entre domínios
    
    Utiliza Redis como message broker para garantir
    entrega confiável de eventos entre microserviços.
    """
    
    def __init__(self):
        """
        Inicializa o Event Bus
        """
        self.redis_client: Optional[redis.Redis] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.is_running = False
        
    async def connect(self) -> None:
        """
        Conecta ao Redis
        """
        try:
            if settings.redis_url:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            else:
                self.redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                    db=settings.redis_db,
                    encoding="utf-8",
                    decode_responses=True
                )
            
            # Testa a conexão
            await self.redis_client.ping()
            logger.info("✅ Conectado ao Redis Event Bus")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """
        Desconecta do Redis
        """
        if self.redis_client:
            await self.redis_client.close()
            logger.info("🔌 Desconectado do Redis Event Bus")
    
    async def publish(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Publica um evento no bus
        
        Args:
            event_type: Tipo do evento (ex: user.registered, payment.completed)
            data: Dados do evento
            
        Returns:
            bool: True se publicado com sucesso
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            # Prepara o payload do evento
            event_payload = {
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "notification_service",
                "version": "1.0"
            }
            
            # Publica no canal específico do tipo de evento
            channel = f"events.{event_type}"
            await self.redis_client.publish(channel, json.dumps(event_payload))
            
            # Também adiciona à fila para processamento garantido
            queue_name = f"queue.{event_type}"
            await self.redis_client.lpush(queue_name, json.dumps(event_payload))
            
            logger.info(f"📤 Evento publicado: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar evento {event_type}: {e}")
            return False
    
    async def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Inscreve um handler para um tipo de evento
        
        Args:
            event_type: Tipo do evento para escutar
            handler: Função que processará o evento
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        logger.info(f"📥 Handler inscrito para evento: {event_type}")
    
    async def start_listening(self) -> None:
        """
        Inicia o loop de escuta de eventos
        """
        if not self.redis_client:
            await self.connect()
        
        self.is_running = True
        logger.info("🎧 Iniciando escuta de eventos...")
        
        # Cria tasks para cada tipo de evento inscrito
        tasks = []
        for event_type in self.subscribers.keys():
            task = asyncio.create_task(self._listen_queue(event_type))
            tasks.append(task)
        
        # Aguarda todas as tasks
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"❌ Erro no loop de eventos: {e}")
        finally:
            self.is_running = False
    
    async def stop_listening(self) -> None:
        """
        Para a escuta de eventos
        """
        self.is_running = False
        logger.info("⏹️ Parando escuta de eventos...")
    
    async def _listen_queue(self, event_type: str) -> None:
        """
        Escuta uma fila específica de eventos
        
        Args:
            event_type: Tipo do evento para escutar
        """
        queue_name = f"queue.{event_type}"
        
        while self.is_running:
            try:
                # Bloqueia até receber um evento (timeout de 1 segundo)
                result = await self.redis_client.brpop(queue_name, timeout=1)
                
                if result:
                    _, event_data = result
                    await self._process_event(event_type, event_data)
                    
            except Exception as e:
                logger.error(f"❌ Erro ao escutar fila {queue_name}: {e}")
                await asyncio.sleep(1)  # Evita loop infinito em caso de erro
    
    async def _process_event(self, event_type: str, event_data: str) -> None:
        """
        Processa um evento recebido
        
        Args:
            event_type: Tipo do evento
            event_data: Dados do evento em JSON
        """
        try:
            # Parse do JSON
            event_payload = json.loads(event_data)
            
            # Executa todos os handlers inscritos
            if event_type in self.subscribers:
                for handler in self.subscribers[event_type]:
                    try:
                        await handler(event_payload)
                        logger.info(f"✅ Evento processado: {event_type}")
                    except Exception as e:
                        logger.error(f"❌ Erro no handler para {event_type}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar evento {event_type}: {e}")
    
    async def get_queue_size(self, event_type: str) -> int:
        """
        Retorna o tamanho da fila de um tipo de evento
        
        Args:
            event_type: Tipo do evento
            
        Returns:
            int: Número de eventos na fila
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            queue_name = f"queue.{event_type}"
            return await self.redis_client.llen(queue_name)
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter tamanho da fila {event_type}: {e}")
            return 0
    
    async def clear_queue(self, event_type: str) -> bool:
        """
        Limpa a fila de um tipo de evento
        
        Args:
            event_type: Tipo do evento
            
        Returns:
            bool: True se limpou com sucesso
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            queue_name = f"queue.{event_type}"
            await self.redis_client.delete(queue_name)
            logger.info(f"🗑️ Fila limpa: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar fila {event_type}: {e}")
            return False


# Instância global do Event Bus
event_bus = EventBus()