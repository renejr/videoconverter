"""
Event Bus Configuration - User Service
Configurações para o Event Bus
"""

import os
from typing import Dict, Any


class EventBusConfig:
    """
    Configurações do Event Bus
    """
    
    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"
    
    # Connection Configuration
    CONNECTION_TIMEOUT = int(os.getenv("REDIS_CONNECTION_TIMEOUT", "10"))
    SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
    RETRY_ON_TIMEOUT = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
    HEALTH_CHECK_INTERVAL = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))
    
    # Event Configuration
    EVENT_CHANNEL_PREFIX = os.getenv("EVENT_CHANNEL_PREFIX", "vidconv.events")
    EVENT_RETRY_ATTEMPTS = int(os.getenv("EVENT_RETRY_ATTEMPTS", "3"))
    EVENT_RETRY_DELAY = int(os.getenv("EVENT_RETRY_DELAY", "1"))
    EVENT_TTL = int(os.getenv("EVENT_TTL", "86400"))  # 24 horas
    
    # Publisher Configuration
    PUBLISHER_BATCH_SIZE = int(os.getenv("PUBLISHER_BATCH_SIZE", "100"))
    PUBLISHER_FLUSH_INTERVAL = int(os.getenv("PUBLISHER_FLUSH_INTERVAL", "5"))
    
    # Monitoring Configuration
    ENABLE_METRICS = os.getenv("ENABLE_EVENT_METRICS", "true").lower() == "true"
    METRICS_INTERVAL = int(os.getenv("METRICS_INTERVAL", "60"))
    
    # Dead Letter Queue
    ENABLE_DLQ = os.getenv("ENABLE_DLQ", "true").lower() == "true"
    DLQ_CHANNEL_SUFFIX = os.getenv("DLQ_CHANNEL_SUFFIX", ".dlq")
    DLQ_MAX_RETRIES = int(os.getenv("DLQ_MAX_RETRIES", "5"))
    
    @classmethod
    def get_redis_url(cls) -> str:
        """
        Constrói a URL de conexão do Redis
        
        Returns:
            str: URL de conexão
        """
        if cls.REDIS_PASSWORD:
            auth = f":{cls.REDIS_PASSWORD}@"
        else:
            auth = ""
        
        protocol = "rediss" if cls.REDIS_SSL else "redis"
        
        return (
            f"{protocol}://{auth}{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        )
    
    @classmethod
    def get_connection_params(cls) -> Dict[str, Any]:
        """
        Obtém parâmetros de conexão do Redis
        
        Returns:
            dict: Parâmetros de conexão
        """
        params = {
            "host": cls.REDIS_HOST,
            "port": cls.REDIS_PORT,
            "db": cls.REDIS_DB,
            "socket_timeout": cls.SOCKET_TIMEOUT,
            "socket_connect_timeout": cls.CONNECTION_TIMEOUT,
            "retry_on_timeout": cls.RETRY_ON_TIMEOUT,
            "health_check_interval": cls.HEALTH_CHECK_INTERVAL,
            "decode_responses": True
        }
        
        if cls.REDIS_PASSWORD:
            params["password"] = cls.REDIS_PASSWORD
        
        if cls.REDIS_SSL:
            params["ssl"] = True
            params["ssl_cert_reqs"] = None
        
        return params
    
    @classmethod
    def get_event_config(cls) -> Dict[str, Any]:
        """
        Obtém configurações de eventos
        
        Returns:
            dict: Configurações de eventos
        """
        return {
            "channel_prefix": cls.EVENT_CHANNEL_PREFIX,
            "retry_attempts": cls.EVENT_RETRY_ATTEMPTS,
            "retry_delay": cls.EVENT_RETRY_DELAY,
            "ttl": cls.EVENT_TTL,
            "batch_size": cls.PUBLISHER_BATCH_SIZE,
            "flush_interval": cls.PUBLISHER_FLUSH_INTERVAL,
            "enable_metrics": cls.ENABLE_METRICS,
            "metrics_interval": cls.METRICS_INTERVAL,
            "enable_dlq": cls.ENABLE_DLQ,
            "dlq_channel_suffix": cls.DLQ_CHANNEL_SUFFIX,
            "dlq_max_retries": cls.DLQ_MAX_RETRIES
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Valida as configurações
        
        Returns:
            bool: True se válidas
        """
        try:
            # Validar configurações obrigatórias
            assert cls.REDIS_HOST, "REDIS_HOST é obrigatório"
            assert cls.REDIS_PORT > 0, "REDIS_PORT deve ser positivo"
            assert cls.REDIS_DB >= 0, "REDIS_DB deve ser não-negativo"
            assert cls.CONNECTION_TIMEOUT > 0, "CONNECTION_TIMEOUT deve ser positivo"
            assert cls.SOCKET_TIMEOUT > 0, "SOCKET_TIMEOUT deve ser positivo"
            assert cls.EVENT_RETRY_ATTEMPTS >= 0, "EVENT_RETRY_ATTEMPTS deve ser não-negativo"
            assert cls.EVENT_RETRY_DELAY >= 0, "EVENT_RETRY_DELAY deve ser não-negativo"
            assert cls.EVENT_TTL > 0, "EVENT_TTL deve ser positivo"
            
            return True
            
        except AssertionError as e:
            raise ValueError(f"Configuração inválida: {str(e)}")
    
    @classmethod
    def get_debug_info(cls) -> Dict[str, Any]:
        """
        Obtém informações de debug das configurações
        
        Returns:
            dict: Informações de debug
        """
        return {
            "redis": {
                "host": cls.REDIS_HOST,
                "port": cls.REDIS_PORT,
                "db": cls.REDIS_DB,
                "ssl": cls.REDIS_SSL,
                "has_password": bool(cls.REDIS_PASSWORD)
            },
            "connection": {
                "timeout": cls.CONNECTION_TIMEOUT,
                "socket_timeout": cls.SOCKET_TIMEOUT,
                "retry_on_timeout": cls.RETRY_ON_TIMEOUT,
                "health_check_interval": cls.HEALTH_CHECK_INTERVAL
            },
            "events": {
                "channel_prefix": cls.EVENT_CHANNEL_PREFIX,
                "retry_attempts": cls.EVENT_RETRY_ATTEMPTS,
                "retry_delay": cls.EVENT_RETRY_DELAY,
                "ttl": cls.EVENT_TTL
            },
            "publisher": {
                "batch_size": cls.PUBLISHER_BATCH_SIZE,
                "flush_interval": cls.PUBLISHER_FLUSH_INTERVAL
            },
            "monitoring": {
                "enable_metrics": cls.ENABLE_METRICS,
                "metrics_interval": cls.METRICS_INTERVAL
            },
            "dlq": {
                "enable_dlq": cls.ENABLE_DLQ,
                "channel_suffix": cls.DLQ_CHANNEL_SUFFIX,
                "max_retries": cls.DLQ_MAX_RETRIES
            }
        }