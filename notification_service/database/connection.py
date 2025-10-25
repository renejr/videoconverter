"""
Database Connection - Notification Service
Plataforma VOD
"""

import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config.settings import settings


logger = logging.getLogger(__name__)

# Configuração do banco de dados
DATABASE_URL = f"mysql+pymysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

# Engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug  # Log SQL queries em modo debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# Metadata
metadata = MetaData()


def get_db():
    """
    Dependency para obter sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas
    """
    try:
        # Importa todos os modelos para garantir que sejam registrados
        from models.notification import Notification, Template, DeliveryLog
        
        # Cria todas as tabelas
        Base.metadata.create_all(bind=engine)
        
        logger.info("Banco de dados inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        raise


def test_connection():
    """
    Testa a conexão com o banco de dados
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("Conexão com banco de dados testada com sucesso")
            return True
            
    except Exception as e:
        logger.error(f"Erro na conexão com banco de dados: {str(e)}")
        return False


def get_db_info():
    """
    Obtém informações sobre o banco de dados
    """
    try:
        with engine.connect() as connection:
            # Informações básicas
            result = connection.execute("SELECT VERSION() as version")
            version = result.fetchone()[0]
            
            # Nome do banco
            result = connection.execute("SELECT DATABASE() as db_name")
            db_name = result.fetchone()[0]
            
            return {
                "version": version,
                "database": db_name,
                "url": f"{settings.DB_HOST}:{settings.DB_PORT}",
                "status": "connected"
            }
            
    except Exception as e:
        logger.error(f"Erro ao obter informações do banco: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }