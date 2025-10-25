"""
Configurações do Serviço de Usuários - Domínio A
Sistema de Identidade e Transações para Plataforma VOD
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Configurações da aplicação usando Pydantic para validação
    e carregamento automático de variáveis de ambiente
    """
    
    # Configurações do Banco de Dados MySQL
    database_url: str = Field(
        default="mysql+pymysql://root:@localhost:3306/play",
        description="URL completa de conexão com o MySQL"
    )
    db_host: str = Field(default="localhost", description="Host do MySQL")
    db_port: int = Field(default=3306, description="Porta do MySQL")
    db_name: str = Field(default="play", description="Nome do banco de dados")
    db_user: str = Field(default="root", description="Usuário do MySQL")
    db_password: str = Field(default="", description="Senha do MySQL")
    
    # Configurações de Segurança
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Chave secreta para JWT"
    )
    algorithm: str = Field(default="HS256", description="Algoritmo de criptografia JWT")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Tempo de expiração do token em minutos"
    )
    
    # Configurações da Aplicação
    app_name: str = Field(default="VOD User Service", description="Nome da aplicação")
    app_version: str = Field(default="1.0.0", description="Versão da aplicação")
    debug: bool = Field(default=True, description="Modo debug")
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="URL do frontend para construir links de verificação e reset"
    )
    
    # Configurações de Email (para futuras funcionalidades)
    smtp_host: Optional[str] = Field(default=None, description="Host SMTP")
    smtp_port: Optional[int] = Field(default=587, description="Porta SMTP")
    smtp_user: Optional[str] = Field(default=None, description="Usuário SMTP")
    smtp_password: Optional[str] = Field(default=None, description="Senha SMTP")
    
    # Configurações do Event Bus (Redis)
    redis_host: str = Field(default="localhost", description="Host do Redis")
    redis_port: int = Field(default=6379, description="Porta do Redis")
    redis_password: Optional[str] = Field(default=None, description="Senha do Redis")
    redis_db: int = Field(default=0, description="Banco do Redis")
    redis_ssl: bool = Field(default=False, description="SSL do Redis")
    redis_connection_timeout: int = Field(default=10, description="Timeout de conexão Redis")
    redis_socket_timeout: int = Field(default=5, description="Timeout de socket Redis")
    redis_retry_on_timeout: bool = Field(default=True, description="Retry on timeout Redis")
    redis_health_check_interval: int = Field(default=30, description="Intervalo de health check Redis")
    
    # Configurações de Eventos
    event_channel_prefix: str = Field(default="vidconv.events", description="Prefixo dos canais de evento")
    event_retry_attempts: int = Field(default=3, description="Tentativas de retry de eventos")
    event_retry_delay: int = Field(default=1, description="Delay entre retries de eventos")
    event_ttl: int = Field(default=86400, description="TTL dos eventos em segundos")
    publisher_batch_size: int = Field(default=100, description="Tamanho do batch do publisher")
    publisher_flush_interval: int = Field(default=5, description="Intervalo de flush do publisher")
    
    # Configurações de Monitoramento
    enable_event_metrics: bool = Field(default=True, description="Habilitar métricas de eventos")
    metrics_interval: int = Field(default=60, description="Intervalo de métricas")
    
    # Configurações de Dead Letter Queue
    enable_dlq: bool = Field(default=True, description="Habilitar Dead Letter Queue")
    dlq_channel_suffix: str = Field(default=".dlq", description="Sufixo do canal DLQ")
    dlq_max_retries: int = Field(default=5, description="Máximo de retries DLQ")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global das configurações
settings = Settings()