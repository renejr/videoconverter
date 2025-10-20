"""
Configuração de Conexão com MySQL usando SQLAlchemy
Sistema de Identidade e Transações - Domínio A
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from config.settings import settings

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base para todos os modelos SQLAlchemy
Base = declarative_base()

class DatabaseManager:
    """
    Gerenciador de conexão com o banco de dados MySQL
    
    Esta classe implementa o padrão Singleton para garantir uma única
    instância de conexão com o banco de dados em toda a aplicação.
    """
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._engine is None:
            self._initialize_database()
    
    def _initialize_database(self):
        """
        Inicializa a conexão com o banco de dados MySQL
        
        Configurações importantes:
        - Pool de conexões para otimizar performance
        - Configurações de timeout para evitar conexões órfãs
        - Encoding UTF-8 para suporte completo a caracteres especiais
        """
        try:
            # Configurações do engine MySQL
            engine_config = {
                'poolclass': QueuePool,
                'pool_size': 10,  # Número de conexões no pool
                'max_overflow': 20,  # Conexões extras permitidas
                'pool_pre_ping': True,  # Verifica conexões antes de usar
                'pool_recycle': 3600,  # Recicla conexões a cada hora
                'echo': settings.debug,  # Log de queries SQL em modo debug
                'connect_args': {
                    'charset': 'utf8mb4',
                    'connect_timeout': 60,
                    'read_timeout': 30,
                    'write_timeout': 30,
                }
            }
            
            # Criação do engine
            self._engine = create_engine(
                settings.database_url,
                **engine_config
            )
            
            # Configuração da factory de sessões
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            # Event listeners para otimizações
            self._setup_event_listeners()
            
            logger.info("Conexão com MySQL estabelecida com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao conectar com MySQL: {e}")
            raise
    
    def _setup_event_listeners(self):
        """
        Configura event listeners para otimizações e monitoramento
        """
        
        @event.listens_for(self._engine, "connect")
        def set_mysql_pragma(dbapi_connection, connection_record):
            """
            Configura parâmetros MySQL para cada nova conexão
            """
            with dbapi_connection.cursor() as cursor:
                # Configura timezone para UTC
                cursor.execute("SET time_zone = '+00:00'")
                # Configura modo SQL para compatibilidade
                cursor.execute("SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
                # Configura charset
                cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        @event.listens_for(self._engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """
            Log quando uma conexão é retirada do pool
            """
            if settings.debug:
                logger.debug("Conexão retirada do pool")
        
        @event.listens_for(self._engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """
            Log quando uma conexão é retornada ao pool
            """
            if settings.debug:
                logger.debug("Conexão retornada ao pool")
    
    @property
    def engine(self):
        """Retorna o engine SQLAlchemy"""
        return self._engine
    
    @property
    def session_factory(self):
        """Retorna a factory de sessões"""
        return self._session_factory
    
    def create_tables(self):
        """
        Cria todas as tabelas definidas nos modelos
        
        IMPORTANTE: Este método deve ser usado apenas em desenvolvimento.
        Em produção, use migrations com Alembic.
        """
        try:
            Base.metadata.create_all(bind=self._engine)
            logger.info("Tabelas criadas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            raise
    
    def drop_tables(self):
        """
        Remove todas as tabelas (USE COM CUIDADO!)
        
        ATENÇÃO: Este método remove TODOS os dados!
        Use apenas em desenvolvimento ou testes.
        """
        try:
            Base.metadata.drop_all(bind=self._engine)
            logger.warning("Todas as tabelas foram removidas")
        except Exception as e:
            logger.error(f"Erro ao remover tabelas: {e}")
            raise
    
    def get_session(self) -> Session:
        """
        Cria uma nova sessão do banco de dados
        
        Returns:
            Session: Nova sessão SQLAlchemy
        """
        return self._session_factory()
    
    def close_all_connections(self):
        """
        Fecha todas as conexões do pool
        """
        if self._engine:
            self._engine.dispose()
            logger.info("Todas as conexões foram fechadas")


# Instância global do gerenciador de banco de dados
db_manager = DatabaseManager()

# Exportar engine e Base para compatibilidade
engine = db_manager.engine

def get_database_session() -> Generator[Session, None, None]:
    """
    Dependency injection para FastAPI
    
    Esta função é usada como dependência nas rotas FastAPI
    para fornecer uma sessão de banco de dados que é
    automaticamente fechada após o uso.
    
    Yields:
        Session: Sessão do banco de dados
    """
    session = db_manager.get_session()
    try:
        yield session
    except Exception as e:
        logger.error(f"Erro na sessão do banco de dados: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def init_database():
    """
    Inicializa o banco de dados
    
    Esta função deve ser chamada na inicialização da aplicação
    para garantir que todas as tabelas existam.
    """
    try:
        # Importa todos os modelos para garantir que sejam registrados
        from models import user, credential, plan, subscription, payment, invoice, session
        
        # Cria as tabelas se não existirem
        db_manager.create_tables()
        
        logger.info("Banco de dados inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise

# Função para testes e desenvolvimento
def reset_database():
    """
    Reseta o banco de dados (remove e recria todas as tabelas)
    
    ATENÇÃO: Esta função remove TODOS os dados!
    Use apenas em desenvolvimento ou testes.
    """
    if not settings.debug:
        raise RuntimeError("Reset de banco só é permitido em modo debug")
    
    try:
        logger.warning("ATENÇÃO: Resetando banco de dados - TODOS OS DADOS SERÃO PERDIDOS!")
        
        # Remove todas as tabelas
        db_manager.drop_tables()
        
        # Recria todas as tabelas
        init_database()
        
        logger.info("Banco de dados resetado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao resetar banco de dados: {e}")
        raise