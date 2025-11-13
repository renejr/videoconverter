#!/usr/bin/env python3
"""
Módulo de Banco de Dados para Metadados de Vídeo
Sistema completo para armazenamento e gerenciamento de metadados de vídeo
"""

from .video_metadata_db import VideoMetadataDB
from .video_queries import VideoQueries
from .metadata_extractor import MetadataExtractor, extract_and_store_video_metadata
from .storyboard_downloader import StoryboardDownloader, download_video_storyboards

__version__ = "1.0.0"
__author__ = "VideoConverter Team"

# Exportar classes principais
__all__ = [
    'VideoMetadataDB',
    'VideoQueries', 
    'MetadataExtractor',
    'StoryboardDownloader',
    'extract_and_store_video_metadata',
    'download_video_storyboards'
]

# Configuração de logging para o módulo
import logging

# Configurar logger do módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Evitar duplicação de handlers
if not logger.handlers:
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)

# Função de inicialização do banco
def initialize_database(db_path: str = "video_metadata.db") -> VideoMetadataDB:
    """
    Inicializa o banco de dados de metadados
    
    Args:
        db_path: Caminho para o arquivo do banco
        
    Returns:
        Instância do banco de dados inicializada
    """
    
    logger.info(f"🔧 Inicializando banco de dados: {db_path}")
    
    db = VideoMetadataDB(db_path)
    db.create_tables()
    
    logger.info("✅ Banco de dados inicializado com sucesso")
    return db

# Função para verificar integridade do banco
def verify_database_integrity(db_path: str = "video_metadata.db") -> bool:
    """
    Verifica a integridade do banco de dados
    
    Args:
        db_path: Caminho para o arquivo do banco
        
    Returns:
        True se o banco está íntegro
    """
    
    try:
        with VideoMetadataDB(db_path) as db:
            connection = db.get_connection()
            cursor = connection.cursor()
            
            # Verificar se todas as tabelas existem
            expected_tables = [
                'videos', 'video_metadata', 'thumbnails', 'storyboards',
                'storyboard_fragments', 'chapters', 'video_formats', 'download_history'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = set(expected_tables) - set(existing_tables)
            if missing_tables:
                logger.error(f"❌ Tabelas faltando: {missing_tables}")
                return False
            
            # Verificar integridade referencial básica
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            
            if fk_violations:
                logger.error(f"❌ Violações de chave estrangeira: {len(fk_violations)}")
                return False
            
            logger.info("✅ Integridade do banco verificada")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar integridade: {e}")
        return False

# Função para obter estatísticas rápidas
def get_quick_stats(db_path: str = "video_metadata.db") -> dict:
    """
    Obtém estatísticas rápidas do banco
    
    Args:
        db_path: Caminho para o arquivo do banco
        
    Returns:
        Dicionário com estatísticas básicas
    """
    
    try:
        with VideoQueries(db_path) as queries:
            stats = queries.get_download_statistics()
            
            # Adicionar informações de tamanho do banco
            import os
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                stats['database_size_bytes'] = db_size
                stats['database_size_mb'] = round(db_size / (1024 * 1024), 2)
            
            return stats
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        return {}

# Função para backup do banco
def backup_database(db_path: str = "video_metadata.db", backup_path: str = None) -> bool:
    """
    Cria backup do banco de dados
    
    Args:
        db_path: Caminho do banco original
        backup_path: Caminho do backup (padrão: db_path + .backup)
        
    Returns:
        True se backup criado com sucesso
    """
    
    try:
        import shutil
        from datetime import datetime
        
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{db_path}.backup_{timestamp}"
        
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"✅ Backup criado: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar backup: {e}")
        return False

# Informações do módulo
def get_module_info() -> dict:
    """
    Retorna informações sobre o módulo
    
    Returns:
        Dicionário com informações do módulo
    """
    
    return {
        'name': 'VideoConverter Database Module',
        'version': __version__,
        'author': __author__,
        'description': 'Sistema completo para armazenamento e gerenciamento de metadados de vídeo',
        'components': [
            'VideoMetadataDB - Gerenciamento do banco de dados SQLite',
            'VideoQueries - Consultas e operações avançadas',
            'MetadataExtractor - Extração de metadados com yt-dlp',
            'StoryboardDownloader - Download e processamento de storyboards'
        ],
        'features': [
            'Armazenamento de metadados completos de vídeo',
            'Gerenciamento de thumbnails e storyboards',
            'Sistema de capítulos e formatos',
            'Histórico de downloads',
            'Busca e filtragem avançada',
            'Download automático de storyboards MHTML',
            'Extração de frames individuais',
            'Cache local de metadados'
        ]
    }

# Log de inicialização do módulo
logger.info(f"📦 Módulo Database v{__version__} carregado")