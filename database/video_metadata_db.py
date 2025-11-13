#!/usr/bin/env python3
"""
Sistema de Banco de Dados SQLite para Metadados de Vídeo
Armazena informações completas de vídeos, thumbnails, storyboards e histórico
"""

import sqlite3
import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoMetadataDB:
    """
    Classe principal para gerenciamento do banco de dados de metadados de vídeo
    Thread-safe implementation using thread-local storage
    """
    
    def __init__(self, db_path: str = "video_metadata.db"):
        """
        Inicializa o banco de dados
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        self._local = threading.local()  # Thread-local storage para conexões
        self._lock = threading.Lock()    # Lock para operações críticas
        self._ensure_database_exists()
        self._create_tables()
    
    def _ensure_database_exists(self):
        """Garante que o diretório do banco existe"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Obtém conexão thread-safe com o banco de dados
        Cada thread terá sua própria conexão
        
        Returns:
            Conexão SQLite thread-safe
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            # Criar nova conexão para esta thread com check_same_thread=False
            self._local.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0  # Timeout de 30 segundos para evitar deadlocks
            )
            self._local.connection.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
            # Configurar WAL mode para melhor concorrência
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")
            self._local.connection.execute("PRAGMA temp_store=memory")
        return self._local.connection
    
    def _create_tables(self):
        """Cria todas as tabelas necessárias no banco de dados"""
        
        connection = self.get_connection()
        cursor = connection.cursor()
        
        # Tabela principal de vídeos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                uploader TEXT,
                uploader_id TEXT,
                channel_url TEXT,
                description TEXT,
                duration INTEGER,
                view_count INTEGER,
                like_count INTEGER,
                comment_count INTEGER,
                upload_date TEXT,
                webpage_url TEXT NOT NULL,
                extractor TEXT,
                tags TEXT,  -- JSON array
                categories TEXT,  -- JSON array
                age_limit INTEGER,
                availability TEXT,
                live_status TEXT,
                was_live BOOLEAN,
                playable_in_embed BOOLEAN,
                is_playlist INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migração: adicionar coluna is_playlist se ainda não existir
        try:
            cursor.execute("PRAGMA table_info(videos)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'is_playlist' not in columns:
                logger.info("🔧 Adicionando coluna is_playlist em videos")
                cursor.execute("ALTER TABLE videos ADD COLUMN is_playlist INTEGER DEFAULT 0")
        except Exception as e:
            logger.error(f"❌ Falha ao migrar coluna is_playlist: {e}")
        
        # Tabela de metadados técnicos detalhados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                fps REAL,
                width INTEGER,
                height INTEGER,
                aspect_ratio REAL,
                resolution TEXT,
                vcodec TEXT,
                acodec TEXT,
                filesize_approx INTEGER,
                tbr REAL,
                vbr REAL,
                abr REAL,
                format_note TEXT,
                quality TEXT,
                language TEXT,
                subtitles_available TEXT,  -- JSON object
                automatic_captions_available TEXT,  -- JSON object
                raw_metadata TEXT,  -- JSON completo dos metadados originais
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (video_id) ON DELETE CASCADE
            )
        """)
        
        # Tabela de thumbnails/capas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thumbnails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                thumbnail_id TEXT NOT NULL,
                url TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                resolution TEXT,
                preference INTEGER,
                format_type TEXT,  -- jpg, webp, etc
                quality_level TEXT,  -- hq, mq, default
                local_path TEXT,  -- caminho local se baixado
                file_size INTEGER,
                downloaded BOOLEAN DEFAULT FALSE,
                download_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (video_id) ON DELETE CASCADE,
                UNIQUE(video_id, thumbnail_id)
            )
        """)
        
        # Tabela de storyboards
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storyboards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                storyboard_id TEXT NOT NULL,
                format_note TEXT,
                url TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                fps REAL,
                rows INTEGER,
                columns INTEGER,
                total_fragments INTEGER,
                resolution TEXT,
                local_path TEXT,  -- caminho local se baixado
                downloaded BOOLEAN DEFAULT FALSE,
                download_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (video_id) ON DELETE CASCADE,
                UNIQUE(video_id, storyboard_id)
            )
        """)
        
        # Tabela de fragmentos de storyboard
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storyboard_fragments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                storyboard_id INTEGER NOT NULL,
                fragment_index INTEGER NOT NULL,
                url TEXT NOT NULL,
                duration REAL,
                start_time REAL,
                end_time REAL,
                local_path TEXT,  -- caminho local se baixado
                downloaded BOOLEAN DEFAULT FALSE,
                download_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (storyboard_id) REFERENCES storyboards (id) ON DELETE CASCADE,
                UNIQUE(storyboard_id, fragment_index)
            )
        """)
        
        # Tabela de capítulos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                chapter_index INTEGER NOT NULL,
                title TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                duration REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (video_id) ON DELETE CASCADE,
                UNIQUE(video_id, chapter_index)
            )
        """)
        
        # Tabela de formatos disponíveis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_formats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                format_id TEXT NOT NULL,
                format_note TEXT,
                ext TEXT,
                protocol TEXT,
                width INTEGER,
                height INTEGER,
                fps REAL,
                vcodec TEXT,
                acodec TEXT,
                tbr REAL,
                vbr REAL,
                abr REAL,
                filesize_approx INTEGER,
                quality INTEGER,
                preference INTEGER,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (video_id) ON DELETE CASCADE,
                UNIQUE(video_id, format_id)
            )
        """)

        # Tabela de relação entre playlist e vídeos filhos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlist_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id TEXT NOT NULL,
                child_video_id TEXT NOT NULL,
                position INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(playlist_id, child_video_id),
                FOREIGN KEY (playlist_id) REFERENCES videos (video_id) ON DELETE CASCADE,
                FOREIGN KEY (child_video_id) REFERENCES videos (video_id) ON DELETE CASCADE
            )
        """)
        
        # Tabela de histórico de downloads
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                download_type TEXT NOT NULL,  -- video, audio, thumbnail, storyboard
                format_id TEXT,
                local_path TEXT NOT NULL,
                file_size INTEGER,
                download_status TEXT NOT NULL,  -- completed, failed, in_progress, cancelled
                error_message TEXT,
                download_started TIMESTAMP,
                download_completed TIMESTAMP,
                download_duration REAL,  -- em segundos
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (video_id) ON DELETE CASCADE
            )
        """)
        
        # Criar índices para melhor performance
        self._create_indexes(cursor)
        
        connection.commit()
        logger.info("✅ Tabelas do banco de dados criadas com sucesso")
    
    def _create_indexes(self, cursor: sqlite3.Cursor):
        """Cria índices para otimizar consultas"""
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_videos_uploader ON videos(uploader)",
            "CREATE INDEX IF NOT EXISTS idx_videos_upload_date ON videos(upload_date)",
            "CREATE INDEX IF NOT EXISTS idx_videos_duration ON videos(duration)",
            "CREATE INDEX IF NOT EXISTS idx_thumbnails_video_id ON thumbnails(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_thumbnails_quality ON thumbnails(quality_level)",
            "CREATE INDEX IF NOT EXISTS idx_storyboards_video_id ON storyboards(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_chapters_video_id ON chapters(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_formats_video_id ON video_formats(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_download_history_video_id ON download_history(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_download_history_status ON download_history(download_status)",
            "CREATE INDEX IF NOT EXISTS idx_download_history_type ON download_history(download_type)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        logger.info("✅ Índices criados com sucesso")
    
    def insert_video_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Insere metadados completos de um vídeo no banco de dados (thread-safe)
        
        Args:
            metadata: Dicionário com metadados do yt-dlp
            
        Returns:
            True se inserido com sucesso, False caso contrário
        """
        video_id = metadata.get('id')
        if not video_id:
            logger.error("❌ ID do vídeo não encontrado nos metadados")
            return False
        
        # Usar lock para operações críticas de inserção
        with self._lock:
            connection = None
            try:
                connection = self.get_connection()
                cursor = connection.cursor()
                
                # Iniciar transação explícita
                cursor.execute("BEGIN IMMEDIATE")
                
                # Inserir dados principais do vídeo
                self._insert_video_basic_info(cursor, metadata)
                
                # Inserir metadados técnicos
                self._insert_video_technical_metadata(cursor, metadata)
                
                # Inserir thumbnails
                self._insert_thumbnails(cursor, metadata)
                
                # Inserir storyboards
                self._insert_storyboards(cursor, metadata)
                
                # Inserir capítulos
                self._insert_chapters(cursor, metadata)
                
                # Inserir formatos
                self._insert_video_formats(cursor, metadata)
                
                connection.commit()
                logger.info(f"✅ Metadados do vídeo {video_id} inseridos com sucesso")
                return True
                
            except Exception as e:
                logger.error(f"❌ Erro ao inserir metadados: {e}")
                if connection:
                    try:
                        connection.rollback()
                    except:
                        pass  # Ignorar erros de rollback
                return False
    
    def insert_storyboard(self, storyboard_data: Dict[str, Any]) -> Optional[int]:
        """
        Insere um storyboard individual no banco de dados
        
        Args:
            storyboard_data: Dicionário com dados do storyboard
            
        Returns:
            ID do storyboard inserido ou None se falhou
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO storyboards (
                    video_id, storyboard_id, format_note, url, width, height,
                    fps, rows, columns, total_fragments, resolution
                ) VALUES (
                    :video_id, :storyboard_id, :format_note, :url, :width, :height,
                    :fps, :rows, :columns, :total_frames, :resolution
                )
            """, storyboard_data)
            
            storyboard_db_id = cursor.lastrowid
            connection.commit()
            
            logger.info(f"✅ Storyboard {storyboard_data.get('storyboard_id')} inserido com sucesso")
            return storyboard_db_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir storyboard: {e}")
            connection.rollback()
            return None
    
    def insert_storyboard_fragment(self, fragment_data: Dict[str, Any]) -> bool:
        """
        Insere um fragmento de storyboard no banco de dados
        
        Args:
            fragment_data: Dicionário com dados do fragmento
            
        Returns:
            True se inserido com sucesso, False caso contrário
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO storyboard_fragments (
                    storyboard_id, fragment_index, url, duration, start_time, end_time
                ) VALUES (
                    :storyboard_id, :fragment_index, :url, :duration, :start_time, :end_time
                )
            """, fragment_data)
            
            connection.commit()
            logger.info(f"✅ Fragmento de storyboard inserido com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir fragmento de storyboard: {e}")
            connection.rollback()
            return False
    
    def _insert_video_basic_info(self, cursor: sqlite3.Cursor, metadata: Dict[str, Any]):
        """Insere informações básicas do vídeo"""
        
        video_data = {
            'video_id': metadata.get('id'),
            'title': metadata.get('title'),
            'uploader': metadata.get('uploader'),
            'uploader_id': metadata.get('uploader_id'),
            'channel_url': metadata.get('channel_url'),
            'description': metadata.get('description'),
            'duration': metadata.get('duration'),
            'view_count': metadata.get('view_count'),
            'like_count': metadata.get('like_count'),
            'comment_count': metadata.get('comment_count'),
            'upload_date': metadata.get('upload_date'),
            'webpage_url': metadata.get('webpage_url'),
            'extractor': metadata.get('extractor'),
            'tags': json.dumps(metadata.get('tags', [])),
            'categories': json.dumps(metadata.get('categories', [])),
            'age_limit': metadata.get('age_limit'),
            'availability': metadata.get('availability'),
            'live_status': metadata.get('live_status'),
            'was_live': metadata.get('was_live'),
            'playable_in_embed': metadata.get('playable_in_embed'),
            'is_playlist': 1 if metadata.get('_type') == 'playlist' else 0
        }
        
        # Usar INSERT OR REPLACE para atualizar se já existir
        cursor.execute("""
            INSERT OR REPLACE INTO videos (
                video_id, title, uploader, uploader_id, channel_url, description,
                duration, view_count, like_count, comment_count, upload_date,
                webpage_url, extractor, tags, categories, age_limit, availability,
                live_status, was_live, playable_in_embed, is_playlist, updated_at
            ) VALUES (
                :video_id, :title, :uploader, :uploader_id, :channel_url, :description,
                :duration, :view_count, :like_count, :comment_count, :upload_date,
                :webpage_url, :extractor, :tags, :categories, :age_limit, :availability,
                :live_status, :was_live, :playable_in_embed, :is_playlist, CURRENT_TIMESTAMP
            )
        """, video_data)

    def link_playlist_video(self, playlist_id: str, child_video_id: str, position: Optional[int] = None) -> bool:
        """Cria o vínculo entre uma playlist e um vídeo filho.

        Args:
            playlist_id: ID do vídeo que representa a playlist (videos.video_id)
            child_video_id: ID do vídeo filho
            position: Ordem do vídeo dentro da playlist

        Returns:
            True se inserido com sucesso, False caso contrário
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO playlist_videos (
                    playlist_id, child_video_id, position
                ) VALUES (
                    :playlist_id, :child_video_id, :position
                )
                """,
                {
                    'playlist_id': str(playlist_id),
                    'child_video_id': str(child_video_id),
                    'position': position,
                }
            )
            connection.commit()
            logger.info(f"✅ Vínculo playlist->vídeo criado: {playlist_id} -> {child_video_id} (pos {position})")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao vincular vídeo à playlist: {e}")
            try:
                connection.rollback()
            except:
                pass
            return False

    def get_playlist_children(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Retorna lista de vídeos filhos de uma playlist.

        Args:
            playlist_id: ID do vídeo que representa a playlist

        Returns:
            Lista de dicionários com dados básicos dos filhos
        """
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 
                v.video_id,
                v.title,
                v.uploader,
                v.duration,
                v.webpage_url,
                pv.position
            FROM playlist_videos pv
            JOIN videos v ON v.video_id = pv.child_video_id
            WHERE pv.playlist_id = :playlist_id
            ORDER BY COALESCE(pv.position, 999999)
            """,
            {'playlist_id': str(playlist_id)}
        )
        rows = cursor.fetchall()
        return [
            {
                'video_id': row[0],
                'title': row[1],
                'uploader': row[2],
                'duration': row[3],
                'webpage_url': row[4],
                'position': row[5],
            }
            for row in rows
        ]

    def count_playlist_children(self, playlist_id: str) -> int:
        """Retorna a quantidade de vídeos filhos de uma playlist.

        Args:
            playlist_id: ID do vídeo que representa a playlist

        Returns:
            Número de vídeos filhos vinculados
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM playlist_videos
                WHERE playlist_id = :playlist_id
                """,
                {'playlist_id': str(playlist_id)}
            )
            result = cursor.fetchone()
            return int(result[0]) if result and result[0] is not None else 0
        except Exception as e:
            logger.error(f"❌ Erro ao contar filhos da playlist {playlist_id}: {e}")
            return 0

    def list_playlists(self) -> List[Dict[str, Any]]:
        """Lista todas as playlists existentes na tabela de vídeos."""
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT video_id, title, uploader, duration, webpage_url
            FROM videos
            WHERE COALESCE(is_playlist, 0) = 1
            ORDER BY updated_at DESC
            """
        )
        rows = cursor.fetchall()
        return [
            {
                'video_id': row[0],
                'title': row[1],
                'uploader': row[2],
                'duration': row[3],
                'webpage_url': row[4],
            }
            for row in rows
        ]
    
    def _insert_video_technical_metadata(self, cursor: sqlite3.Cursor, metadata: Dict[str, Any]):
        """Insere metadados técnicos do vídeo"""
        
        # Pegar informações do melhor formato disponível
        best_format = None
        formats = metadata.get('formats') or []
        
        if formats:
            # Procurar pelo melhor formato de vídeo
            video_formats = [f for f in formats if f.get('vcodec') != 'none']
            if video_formats:
                best_format = max(video_formats, key=lambda x: x.get('height', 0) or 0)
        
        if not best_format:
            best_format = {}
        
        tech_data = {
            'video_id': metadata.get('id'),
            'fps': best_format.get('fps'),
            'width': best_format.get('width'),
            'height': best_format.get('height'),
            'aspect_ratio': best_format.get('aspect_ratio'),
            'resolution': best_format.get('resolution'),
            'vcodec': best_format.get('vcodec'),
            'acodec': best_format.get('acodec'),
            'filesize_approx': best_format.get('filesize_approx'),
            'tbr': best_format.get('tbr'),
            'vbr': best_format.get('vbr'),
            'abr': best_format.get('abr'),
            'format_note': best_format.get('format_note'),
            'quality': best_format.get('quality'),
            'language': metadata.get('language'),
            'subtitles_available': json.dumps(metadata.get('subtitles', {})),
            'automatic_captions_available': json.dumps(metadata.get('automatic_captions', {})),
            'raw_metadata': json.dumps(metadata)
        }
        
        cursor.execute("""
            INSERT OR REPLACE INTO video_metadata (
                video_id, fps, width, height, aspect_ratio, resolution,
                vcodec, acodec, filesize_approx, tbr, vbr, abr,
                format_note, quality, language, subtitles_available,
                automatic_captions_available, raw_metadata
            ) VALUES (
                :video_id, :fps, :width, :height, :aspect_ratio, :resolution,
                :vcodec, :acodec, :filesize_approx, :tbr, :vbr, :abr,
                :format_note, :quality, :language, :subtitles_available,
                :automatic_captions_available, :raw_metadata
            )
        """, tech_data)
    
    def _insert_thumbnails(self, cursor: sqlite3.Cursor, metadata: Dict[str, Any]):
        """Insere thumbnails do vídeo"""
        
        video_id = metadata.get('id')
        thumbnails = metadata.get('thumbnails') or []
        
        for thumb in thumbnails:
            thumb_data = {
                'video_id': video_id,
                'thumbnail_id': thumb.get('id', ''),
                'url': thumb.get('url', ''),
                'width': thumb.get('width'),
                'height': thumb.get('height'),
                'resolution': thumb.get('resolution'),
                'preference': thumb.get('preference'),
                'format_type': self._extract_format_from_url(thumb.get('url', '')),
                'quality_level': self._extract_quality_from_url(thumb.get('url', ''))
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO thumbnails (
                    video_id, thumbnail_id, url, width, height, resolution,
                    preference, format_type, quality_level
                ) VALUES (
                    :video_id, :thumbnail_id, :url, :width, :height, :resolution,
                    :preference, :format_type, :quality_level
                )
            """, thumb_data)
    
    def _insert_storyboards(self, cursor: sqlite3.Cursor, metadata: Dict[str, Any]):
        """Insere storyboards do vídeo"""
        
        video_id = metadata.get('id')
        formats = metadata.get('formats') or []
        
        # Filtrar apenas formatos de storyboard
        storyboard_formats = [f for f in formats if f.get('format_note') == 'storyboard']
        
        for story in storyboard_formats:
            story_data = {
                'video_id': video_id,
                'storyboard_id': story.get('format_id', ''),
                'format_note': story.get('format_note'),
                'url': story.get('url', ''),
                'width': story.get('width'),
                'height': story.get('height'),
                'fps': story.get('fps'),
                'rows': story.get('rows'),
                'columns': story.get('columns'),
                'total_fragments': len(story.get('fragments', [])),
                'resolution': story.get('resolution')
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO storyboards (
                    video_id, storyboard_id, format_note, url, width, height,
                    fps, rows, columns, total_fragments, resolution
                ) VALUES (
                    :video_id, :storyboard_id, :format_note, :url, :width, :height,
                    :fps, :rows, :columns, :total_fragments, :resolution
                )
            """, story_data)
            
            # Obter ID do storyboard inserido
            storyboard_db_id = cursor.lastrowid
            
            # Inserir fragmentos do storyboard
            self._insert_storyboard_fragments(cursor, storyboard_db_id, story.get('fragments', []))
    
    def _insert_storyboard_fragments(self, cursor: sqlite3.Cursor, storyboard_id: int, fragments: List[Dict]):
        """Insere fragmentos de um storyboard"""
        
        for i, fragment in enumerate(fragments):
            fragment_data = {
                'storyboard_id': storyboard_id,
                'fragment_index': i,
                'url': fragment.get('url', ''),
                'duration': fragment.get('duration'),
                'start_time': i * fragment.get('duration', 0) if fragment.get('duration') else None,
                'end_time': (i + 1) * fragment.get('duration', 0) if fragment.get('duration') else None
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO storyboard_fragments (
                    storyboard_id, fragment_index, url, duration, start_time, end_time
                ) VALUES (
                    :storyboard_id, :fragment_index, :url, :duration, :start_time, :end_time
                )
            """, fragment_data)
    
    def _insert_chapters(self, cursor: sqlite3.Cursor, metadata: Dict[str, Any]):
        """Insere capítulos do vídeo"""
        
        video_id = metadata.get('id')
        chapters = metadata.get('chapters') or []
        
        for i, chapter in enumerate(chapters):
            chapter_data = {
                'video_id': video_id,
                'chapter_index': i,
                'title': chapter.get('title', ''),
                'start_time': chapter.get('start_time', 0),
                'end_time': chapter.get('end_time', 0),
                'duration': chapter.get('end_time', 0) - chapter.get('start_time', 0)
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO chapters (
                    video_id, chapter_index, title, start_time, end_time, duration
                ) VALUES (
                    :video_id, :chapter_index, :title, :start_time, :end_time, :duration
                )
            """, chapter_data)
    
    def _insert_video_formats(self, cursor: sqlite3.Cursor, metadata: Dict[str, Any]):
        """Insere formatos disponíveis do vídeo"""
        
        video_id = metadata.get('id')
        formats = metadata.get('formats') or []
        
        for fmt in formats:
            # Pular storyboards (já tratados separadamente)
            if fmt.get('format_note') == 'storyboard':
                continue
                
            format_data = {
                'video_id': video_id,
                'format_id': fmt.get('format_id', ''),
                'format_note': fmt.get('format_note'),
                'ext': fmt.get('ext'),
                'protocol': fmt.get('protocol'),
                'width': fmt.get('width'),
                'height': fmt.get('height'),
                'fps': fmt.get('fps'),
                'vcodec': fmt.get('vcodec'),
                'acodec': fmt.get('acodec'),
                'tbr': fmt.get('tbr'),
                'vbr': fmt.get('vbr'),
                'abr': fmt.get('abr'),
                'filesize_approx': fmt.get('filesize_approx'),
                'quality': fmt.get('quality'),
                'preference': fmt.get('preference'),
                'url': fmt.get('url')
            }
            
            cursor.execute("""
                INSERT OR REPLACE INTO video_formats (
                    video_id, format_id, format_note, ext, protocol, width, height,
                    fps, vcodec, acodec, tbr, vbr, abr, filesize_approx,
                    quality, preference, url
                ) VALUES (
                    :video_id, :format_id, :format_note, :ext, :protocol, :width, :height,
                    :fps, :vcodec, :acodec, :tbr, :vbr, :abr, :filesize_approx,
                    :quality, :preference, :url
                )
            """, format_data)
    
    def _extract_format_from_url(self, url: str) -> str:
        """Extrai formato da imagem da URL"""
        if '.webp' in url:
            return 'webp'
        elif '.jpg' in url:
            return 'jpg'
        elif '.png' in url:
            return 'png'
        return 'unknown'
    
    def _extract_quality_from_url(self, url: str) -> str:
        """Extrai nível de qualidade da URL"""
        if 'hq' in url:
            return 'high'
        elif 'mq' in url:
            return 'medium'
        elif 'maxres' in url:
            return 'maximum'
        return 'default'
    
    def create_tables(self):
        """
        Método público para criar tabelas do banco de dados
        Chama o método privado _create_tables
        """
        self._create_tables()
    
    def close_connection(self):
        """
        Fecha a conexão da thread atual
        """
        if hasattr(self._local, 'connection') and self._local.connection is not None:
            try:
                self._local.connection.close()
                self._local.connection = None
                logger.debug("🔒 Conexão SQLite fechada para thread atual")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao fechar conexão SQLite: {e}")
    
    def close_all_connections(self):
        """
        Força o fechamento de todas as conexões (usar com cuidado)
        """
        with self._lock:
            try:
                # Tentar fechar a conexão da thread atual
                self.close_connection()
                logger.info("🔒 Todas as conexões SQLite foram fechadas")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao fechar todas as conexões: {e}")
    
    def __del__(self):
        """
        Destructor da classe - fecha conexões ao destruir o objeto
        """
        try:
            self.close_all_connections()
        except:
            pass  # Ignorar erros durante destruição
    
    def close(self):
        """Fecha a conexão com o banco de dados (thread-safe)"""
        self.close_connection()
        logger.info("🔒 Conexão com banco de dados fechada")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
