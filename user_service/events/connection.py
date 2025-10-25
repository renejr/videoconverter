"""
Event Bus Connection - User Service
Gerencia a conexão com Redis para comunicação assíncrona
"""

import redis.asyncio as redis
import logging
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class EventBusConnection:
    """
    Gerenciador de conexão com Redis para Event Bus
    """
    
    def __init__(self):
        """
        Inicializa a conexão com Redis
        """
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """
        Estabelece conexão com Redis
        
        Returns:
            bool: True se conectado com sucesso
        """
        try:
            # Configurar conexão Redis
            self._redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=settings.redis_connection_timeout,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=settings.redis_health_check_interval
            )
            
            # Testar conexão
            await self._redis.ping()
            self._connected = True
            
            logger.info("✅ Conexão Event Bus (Redis) estabelecida com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com Event Bus: {str(e)}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """
        Fecha a conexão com Redis
        """
        if self._redis:
            try:
                await self._redis.close()
                self._connected = False
                logger.info("🔌 Conexão Event Bus fechada")
            except Exception as e:
                logger.error(f"Erro ao fechar conexão Event Bus: {str(e)}")
    
    async def publish(self, channel: str, message: str) -> bool:
        """
        Publica mensagem no canal Redis
        
        Args:
            channel: Canal de destino
            message: Mensagem a ser enviada
            
        Returns:
            bool: True se publicado com sucesso
        """
        if not self._connected or not self._redis:
            logger.error("Event Bus não conectado")
            return False
        
        try:
            await self._redis.publish(channel, message)
            logger.debug(f"📤 Evento publicado no canal '{channel}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar evento: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Testa a conexão com Redis
        
        Returns:
            bool: True se conexão está ativa
        """
        if not self._redis:
            return False
        
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False
    
    @property
    def is_connected(self) -> bool:
        """
        Verifica se está conectado
        
        Returns:
            bool: Status da conexão
        """
        return self._connected
    
    async def get_info(self) -> dict:
        """
        Obtém informações da conexão Redis
        
        Returns:
            dict: Informações da conexão
        """
        if not self._redis:
            return {"status": "disconnected"}
        
        try:
            info = await self._redis.info()
            return {
                "status": "connected" if self._connected else "disconnected",
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed")
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Instância global da conexão
event_bus = EventBusConnection()