"""
Configurações do Notification Service - Domínio de Notificações
Sistema de Mensageria para Plataforma VOD
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Configurações do serviço de notificações usando Pydantic
    para validação e carregamento automático de variáveis de ambiente
    """
    
    # Configurações do Banco de Dados
    database_url: str = Field(
        default="mysql+pymysql://root:@localhost:3306/notifications",
        description="URL completa de conexão com o MySQL"
    )
    db_host: str = Field(default="localhost", description="Host do MySQL")
    db_port: int = Field(default=3306, description="Porta do MySQL")
    db_name: str = Field(default="notifications", description="Nome do banco de dados")
    db_user: str = Field(default="root", description="Usuário do MySQL")
    db_password: str = Field(default="", description="Senha do MySQL")
    
    # Configurações da Aplicação
    app_name: str = Field(default="VOD Notification Service", description="Nome da aplicação")
    app_version: str = Field(default="1.0.0", description="Versão da aplicação")
    debug: bool = Field(default=True, description="Modo debug")
    host: str = Field(default="0.0.0.0", description="Host da aplicação")
    port: int = Field(default=8001, description="Porta da aplicação")
    
    # Configurações de Segurança
    secret_key: str = Field(
        default="notification-secret-key-change-in-production",
        description="Chave secreta para autenticação"
    )
    
    # Configurações de Email - Gmail SMTP
    smtp_host: str = Field(default="smtp.gmail.com", description="Host SMTP do Gmail")
    smtp_port: int = Field(default=587, description="Porta SMTP (TLS)")
    smtp_user: Optional[str] = Field(default=None, description="Email do Gmail")
    smtp_password: Optional[str] = Field(default=None, description="Senha de app do Gmail")
    smtp_use_tls: bool = Field(default=True, description="Usar TLS")
    smtp_use_ssl: bool = Field(default=False, description="Usar SSL")
    smtp_timeout: int = Field(default=30, description="Timeout SMTP em segundos")
    
    # Configurações de Email Sender
    from_email: Optional[str] = Field(default=None, description="Email do remetente")
    from_name: str = Field(default="VidConv Platform", description="Nome do remetente")
    reply_to: Optional[str] = Field(default=None, description="Email para resposta")
    
    # Configurações de URLs
    frontend_url: str = Field(default="http://localhost:3000", description="URL do frontend")
    backend_url: str = Field(default="http://localhost:8000", description="URL do backend")
    
    # Configurações de SMS (para futuras implementações)
    sms_provider: str = Field(default="twilio", description="Provedor de SMS")
    sms_account_sid: Optional[str] = Field(default=None, description="SID da conta SMS")
    sms_auth_token: Optional[str] = Field(default=None, description="Token de autenticação SMS")
    sms_from_number: Optional[str] = Field(default=None, description="Número de origem SMS")
    
    # Configurações do Event Bus - Redis
    redis_host: str = Field(default="localhost", description="Host do Redis")
    redis_port: int = Field(default=6379, description="Porta do Redis")
    redis_password: Optional[str] = Field(default=None, description="Senha do Redis")
    redis_db: int = Field(default=0, description="Database do Redis")
    redis_url: Optional[str] = Field(default=None, description="URL completa do Redis")
    redis_timeout: int = Field(default=5, description="Timeout de conexão Redis")
    redis_health_check_interval: int = Field(default=30, description="Intervalo de health check Redis")
    
    # Configurações de Event Bus
    event_bus_enabled: bool = Field(default=True, description="Habilitar Event Bus")
    event_bus_channel_prefix: str = Field(default="vidconv", description="Prefixo dos canais")
    event_bus_retry_attempts: int = Field(default=3, description="Tentativas de retry")
    event_bus_retry_delay: int = Field(default=1, description="Delay entre retries")
    event_bus_batch_size: int = Field(default=100, description="Tamanho do batch")
    event_bus_flush_interval: int = Field(default=5, description="Intervalo de flush")
    
    # Configurações de Publisher
    publisher_enabled: bool = Field(default=True, description="Habilitar Publisher")
    publisher_channel_prefix: str = Field(default="notifications", description="Prefixo do Publisher")
    publisher_retry_attempts: int = Field(default=3, description="Tentativas de retry Publisher")
    publisher_retry_delay: int = Field(default=1, description="Delay entre retries Publisher")
    
    # Configurações de Monitoramento Event Bus
    monitoring_enabled: bool = Field(default=True, description="Habilitar monitoramento")
    monitoring_interval: int = Field(default=60, description="Intervalo de monitoramento")
    monitoring_retention_days: int = Field(default=7, description="Retenção de dados de monitoramento")
    
    # Configurações de Dead Letter Queue
    dlq_enabled: bool = Field(default=True, description="Habilitar Dead Letter Queue")
    dlq_max_retries: int = Field(default=5, description="Máximo de retries DLQ")
    dlq_retry_delay: int = Field(default=300, description="Delay entre retries DLQ")
    dlq_retention_hours: int = Field(default=24, description="Retenção DLQ em horas")
    
    # Configurações de Filas
    queue_default: str = Field(default="notifications", description="Fila padrão")
    queue_email: str = Field(default="email_notifications", description="Fila de emails")
    queue_sms: str = Field(default="sms_notifications", description="Fila de SMS")
    queue_push: str = Field(default="push_notifications", description="Fila de push notifications")
    
    # Configurações de Rate Limiting
    rate_limit_email_per_minute: int = Field(default=10, description="Limite de emails por minuto")
    rate_limit_sms_per_minute: int = Field(default=5, description="Limite de SMS por minuto")
    rate_limit_emails_per_minute: int = Field(default=50, description="Limite de emails por minuto")
    rate_limit_emails_per_hour: int = Field(default=400, description="Limite de emails por hora")
    rate_limit_emails_per_day: int = Field(default=450, description="Limite de emails por dia")
    
    # Configurações de Retry
    max_retries: int = Field(default=3, description="Máximo de tentativas")
    retry_delay: int = Field(default=60, description="Delay entre tentativas em segundos")
    email_max_retries: int = Field(default=3, description="Máximo de tentativas para email")
    email_retry_delay: int = Field(default=60, description="Delay entre tentativas de email")
    email_retry_backoff: int = Field(default=2, description="Backoff multiplicador para retry")
    
    # Configurações de Template
    template_cache_size: int = Field(default=100, description="Tamanho do cache de templates")
    
    # Configurações de Templates
    template_dir: str = Field(default="templates", description="Diretório de templates")
    
    # Configurações de Logs
    log_level: str = Field(default="INFO", description="Nível de log")
    log_file: str = Field(default="notification_service.log", description="Arquivo de log")
    
    # Configurações de Monitoramento
    enable_metrics: bool = Field(default=True, description="Habilitar métricas")
    metrics_port: int = Field(default=9001, description="Porta das métricas")
    
    # Configurações de CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Origens permitidas para CORS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global das configurações
settings = Settings()