"""
Configuração do ambiente Alembic para migrations
Sistema de Identidade e Transações - Domínio A
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.settings import settings
from database.connection import Base

# Configuração do Alembic
config = context.config

# Configura logging se o arquivo de config existir
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados dos modelos para auto-geração de migrations
target_metadata = Base.metadata

def get_url():
    """
    Retorna a URL do banco de dados das configurações
    """
    return settings.database_url

def run_migrations_offline() -> None:
    """
    Executa migrations em modo 'offline'.
    
    Este modo gera apenas o SQL das migrations sem
    executar contra o banco de dados.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    Executa migrations em modo 'online'.
    
    Este modo conecta ao banco de dados e executa
    as migrations diretamente.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# Executa migrations baseado no contexto
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()