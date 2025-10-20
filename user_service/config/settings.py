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
    
    # Configurações de Email (para futuras funcionalidades)
    smtp_host: Optional[str] = Field(default=None, description="Host SMTP")
    smtp_port: Optional[int] = Field(default=587, description="Porta SMTP")
    smtp_user: Optional[str] = Field(default=None, description="Usuário SMTP")
    smtp_password: Optional[str] = Field(default=None, description="Senha SMTP")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global das configurações
settings = Settings()