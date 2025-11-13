#!/usr/bin/env python3
"""
Módulo de Consultas e Operações do Banco de Dados de Metadados de Vídeo
Fornece métodos para buscar, filtrar e gerenciar dados armazenados
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging

from .video_metadata_db import VideoMetadataDB

logger = logging.getLogger(__name__)

class VideoQueries:
    """
    Classe para consultas e operações avançadas no banco de dados
    """
    
    def __init__(self, db_path: str = "video_metadata.db"):
        """
        Inicializa o sistema de consultas
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db = VideoMetadataDB(db_path)
    
    def search_videos(self, 
                     query: str = None,
                     uploader: str = None,
                     duration_min: int = None,
                     duration_max: int = None,
                     upload_date_from: str = None,
                     upload_date_to: str = None,
                     has_chapters: bool = None,
                     has_storyboards: bool = None,
                     limit: int = 50,
                     offset: int = 0) -> List[Dict[str, Any]]:
        """
        Busca vídeos com filtros avançados
        
        Args:
            query: Texto para buscar no título ou descrição
            uploader: Nome do canal/uploader
            duration_min: Duração mínima em segundos
            duration_max: Duração máxima em segundos
            upload_date_from: Data de upload inicial (YYYYMMDD)
            upload_date_to: Data de upload final (YYYYMMDD)
            has_chapters: Se deve ter capítulos
            has_storyboards: Se deve ter storyboards
            limit: Limite de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de vídeos encontrados
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        # Construir query dinamicamente
        where_conditions = []
        params = {}
        
        if query:
            where_conditions.append("(v.title LIKE :query OR v.description LIKE :query)")
            params['query'] = f"%{query}%"
        
        if uploader:
            where_conditions.append("v.uploader LIKE :uploader")
            params['uploader'] = f"%{uploader}%"
        
        if duration_min is not None:
            where_conditions.append("v.duration >= :duration_min")
            params['duration_min'] = duration_min
        
        if duration_max is not None:
            where_conditions.append("v.duration <= :duration_max")
            params['duration_max'] = duration_max
        
        if upload_date_from:
            where_conditions.append("v.upload_date >= :upload_date_from")
            params['upload_date_from'] = upload_date_from
        
        if upload_date_to:
            where_conditions.append("v.upload_date <= :upload_date_to")
            params['upload_date_to'] = upload_date_to
        
        if has_chapters is not None:
            if has_chapters:
                where_conditions.append("EXISTS (SELECT 1 FROM chapters c WHERE c.video_id = v.video_id)")
            else:
                where_conditions.append("NOT EXISTS (SELECT 1 FROM chapters c WHERE c.video_id = v.video_id)")
        
        if has_storyboards is not None:
            if has_storyboards:
                where_conditions.append("EXISTS (SELECT 1 FROM storyboards s WHERE s.video_id = v.video_id)")
            else:
                where_conditions.append("NOT EXISTS (SELECT 1 FROM storyboards s WHERE s.video_id = v.video_id)")
        
        # Montar query final
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        sql = f"""
            SELECT 
                v.*,
                vm.width,
                vm.height,
                vm.resolution,
                vm.fps,
                (SELECT COUNT(*) FROM thumbnails t WHERE t.video_id = v.video_id) as thumbnail_count,
                (SELECT COUNT(*) FROM storyboards s WHERE s.video_id = v.video_id) as storyboard_count,
                (SELECT COUNT(*) FROM chapters c WHERE c.video_id = v.video_id) as chapter_count
            FROM videos v
            LEFT JOIN video_metadata vm ON v.video_id = vm.video_id
            WHERE {where_clause}
            ORDER BY v.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        params.update({'limit': limit, 'offset': offset})
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        return [dict(row) for row in results]
    
    def get_all_videos(self) -> List[Dict[str, Any]]:
        """
        Obtém todos os vídeos do banco de dados
        
        Returns:
            Lista de dicionários com dados dos vídeos
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                v.*,
                COUNT(DISTINCT t.id) as thumbnail_count,
                COUNT(DISTINCT s.id) as storyboard_count,
                COUNT(DISTINCT c.id) as chapter_count
            FROM videos v
            LEFT JOIN thumbnails t ON v.id = t.video_id
            LEFT JOIN storyboards s ON v.id = s.video_id  
            LEFT JOIN chapters c ON v.id = c.video_id
            GROUP BY v.id
            ORDER BY v.created_at DESC
        """)
        
        videos = []
        for row in cursor.fetchall():
            video_dict = dict(row)
            videos.append(video_dict)
        
        logger.info(f"📚 Retornando {len(videos)} vídeos do banco de dados")
        return videos

    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes completos de um vídeo
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Dicionário com todos os dados do vídeo ou None se não encontrado
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        # Buscar informações básicas
        cursor.execute("""
            SELECT v.*, vm.*
            FROM videos v
            LEFT JOIN video_metadata vm ON v.video_id = vm.video_id
            WHERE v.video_id = ?
        """, (video_id,))
        
        video_data = cursor.fetchone()
        if not video_data:
            return None
        
        video_dict = dict(video_data)
        
        # Buscar thumbnails
        cursor.execute("""
            SELECT * FROM thumbnails 
            WHERE video_id = ? 
            ORDER BY preference DESC
        """, (video_id,))
        video_dict['thumbnails'] = [dict(row) for row in cursor.fetchall()]
        
        # Buscar storyboards
        cursor.execute("""
            SELECT s.*, 
                   (SELECT COUNT(*) FROM storyboard_fragments sf WHERE sf.storyboard_id = s.id) as fragment_count
            FROM storyboards s
            WHERE s.video_id = ?
            ORDER BY s.width DESC
        """, (video_id,))
        video_dict['storyboards'] = [dict(row) for row in cursor.fetchall()]
        
        # Buscar capítulos
        cursor.execute("""
            SELECT * FROM chapters 
            WHERE video_id = ? 
            ORDER BY start_time ASC
        """, (video_id,))
        video_dict['chapters'] = [dict(row) for row in cursor.fetchall()]
        
        # Buscar formatos
        cursor.execute("""
            SELECT * FROM video_formats 
            WHERE video_id = ? 
            ORDER BY height DESC, preference DESC
        """, (video_id,))
        video_dict['formats'] = [dict(row) for row in cursor.fetchall()]
        
        # Buscar histórico de downloads
        cursor.execute("""
            SELECT * FROM download_history 
            WHERE video_id = ? 
            ORDER BY created_at DESC
        """, (video_id,))
        video_dict['download_history'] = [dict(row) for row in cursor.fetchall()]
        
        return video_dict
    
    def get_storyboard_fragments(self, storyboard_id: int) -> List[Dict[str, Any]]:
        """
        Obtém fragmentos de um storyboard específico
        
        Args:
            storyboard_id: ID do storyboard
            
        Returns:
            Lista de fragmentos ordenados por índice
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT * FROM storyboard_fragments 
            WHERE storyboard_id = ? 
            ORDER BY fragment_index ASC
        """, (storyboard_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_best_thumbnail(self, video_id: str, quality: str = 'high') -> Optional[Dict[str, Any]]:
        """
        Obtém a melhor thumbnail de um vídeo
        
        Args:
            video_id: ID do vídeo
            quality: Qualidade desejada ('high', 'medium', 'default')
            
        Returns:
            Dados da thumbnail ou None se não encontrada
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT * FROM thumbnails 
            WHERE video_id = ? AND quality_level = ?
            ORDER BY preference DESC, width DESC
            LIMIT 1
        """, (video_id, quality))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def get_best_storyboard(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém o melhor storyboard de um vídeo (maior resolução)
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Dados do storyboard ou None se não encontrado
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT * FROM storyboards 
            WHERE video_id = ?
            ORDER BY width DESC, height DESC
            LIMIT 1
        """, (video_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else None

    def list_playlists(self) -> List[Dict[str, Any]]:
        """
        Lista playlists armazenadas na tabela de vídeos

        Returns:
            Lista com dados básicos das playlists
        """
        # Comentário de função: Encapsula a listagem de playlists usando o DB
        return self.db.list_playlists()

    def get_playlist_children(self, playlist_id: str) -> List[Dict[str, Any]]:
        """
        Lista os vídeos filhos de uma playlist

        Args:
            playlist_id: ID do vídeo que representa a playlist

        Returns:
            Lista de vídeos filhos com dados básicos
        """
        # Comentário de função: Encapsula a consulta de filhos para uso pela GUI
        return self.db.get_playlist_children(playlist_id)

    def count_playlist_children(self, playlist_id: str) -> int:
        """
        Conta a quantidade de vídeos filhos vinculados a uma playlist.

        Args:
            playlist_id: ID do vídeo que representa a playlist

        Returns:
            Número de vídeos filhos
        """
        # Comentário de função: Encapsula a contagem de filhos para uso pela GUI
        return self.db.count_playlist_children(playlist_id)
    
    def mark_thumbnail_downloaded(self, thumbnail_id: int, local_path: str, file_size: int = None):
        """
        Marca uma thumbnail como baixada
        
        Args:
            thumbnail_id: ID da thumbnail
            local_path: Caminho local do arquivo
            file_size: Tamanho do arquivo em bytes
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE thumbnails 
            SET downloaded = TRUE, 
                local_path = ?, 
                file_size = ?,
                download_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (local_path, file_size, thumbnail_id))
        
        connection.commit()
        logger.info(f"✅ Thumbnail {thumbnail_id} marcada como baixada")
    
    def mark_storyboard_downloaded(self, storyboard_id: int, local_path: str):
        """
        Marca um storyboard como baixado
        
        Args:
            storyboard_id: ID do storyboard
            local_path: Caminho local do arquivo
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE storyboards 
            SET downloaded = TRUE, 
                local_path = ?, 
                download_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (local_path, storyboard_id))
        
        connection.commit()
        logger.info(f"✅ Storyboard {storyboard_id} marcado como baixado")
    
    def add_download_record(self, 
                           video_id: str,
                           download_type: str,
                           local_path: str,
                           status: str = 'completed',
                           format_id: str = None,
                           file_size: int = None,
                           error_message: str = None,
                           download_duration: float = None) -> int:
        """
        Adiciona registro de download
        
        Args:
            video_id: ID do vídeo
            download_type: Tipo do download (video, audio, thumbnail, storyboard)
            local_path: Caminho local do arquivo
            status: Status do download (completed, failed, in_progress, cancelled)
            format_id: ID do formato baixado
            file_size: Tamanho do arquivo
            error_message: Mensagem de erro se houver
            download_duration: Duração do download em segundos
            
        Returns:
            ID do registro criado
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO download_history (
                video_id, download_type, format_id, local_path, file_size,
                download_status, error_message, download_started, 
                download_completed, download_duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 
                     CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END, ?)
        """, (video_id, download_type, format_id, local_path, file_size,
              status, error_message, status, download_duration))
        
        record_id = cursor.lastrowid
        connection.commit()
        
        logger.info(f"✅ Registro de download {record_id} adicionado")
        return record_id
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de downloads
        
        Returns:
            Dicionário com estatísticas
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        stats = {}
        
        # Total de vídeos
        cursor.execute("SELECT COUNT(*) FROM videos")
        stats['total_videos'] = cursor.fetchone()[0]
        
        # Total de downloads por tipo
        cursor.execute("""
            SELECT download_type, COUNT(*) 
            FROM download_history 
            GROUP BY download_type
        """)
        stats['downloads_by_type'] = dict(cursor.fetchall())
        
        # Downloads por status
        cursor.execute("""
            SELECT download_status, COUNT(*) 
            FROM download_history 
            GROUP BY download_status
        """)
        stats['downloads_by_status'] = dict(cursor.fetchall())
        
        # Espaço total usado
        cursor.execute("""
            SELECT SUM(file_size) 
            FROM download_history 
            WHERE download_status = 'completed' AND file_size IS NOT NULL
        """)
        total_size = cursor.fetchone()[0]
        stats['total_storage_bytes'] = total_size or 0
        stats['total_storage_mb'] = round((total_size or 0) / (1024 * 1024), 2)
        
        # Vídeos com storyboards
        cursor.execute("""
            SELECT COUNT(DISTINCT video_id) 
            FROM storyboards
        """)
        stats['videos_with_storyboards'] = cursor.fetchone()[0]
        
        # Vídeos com capítulos
        cursor.execute("""
            SELECT COUNT(DISTINCT video_id) 
            FROM chapters
        """)
        stats['videos_with_chapters'] = cursor.fetchone()[0]
        
        # Uploaders mais frequentes
        cursor.execute("""
            SELECT uploader, COUNT(*) as video_count
            FROM videos 
            WHERE uploader IS NOT NULL
            GROUP BY uploader 
            ORDER BY video_count DESC 
            LIMIT 10
        """)
        stats['top_uploaders'] = [{'uploader': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        return stats
    
    def cleanup_old_records(self, days_old: int = 30) -> int:
        """
        Remove registros antigos do banco
        
        Args:
            days_old: Idade em dias para considerar registro antigo
            
        Returns:
            Número de registros removidos
        """
        
        connection = self.db.get_connection()
        cursor = connection.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Remover registros de download antigos e falhos
        cursor.execute("""
            DELETE FROM download_history 
            WHERE created_at < ? AND download_status IN ('failed', 'cancelled')
        """, (cutoff_str,))
        
        removed_count = cursor.rowcount
        connection.commit()
        
        logger.info(f"🧹 {removed_count} registros antigos removidos")
        return removed_count
    
    def export_video_data(self, video_id: str, export_path: str) -> bool:
        """
        Exporta todos os dados de um vídeo para arquivo JSON
        
        Args:
            video_id: ID do vídeo
            export_path: Caminho para salvar o arquivo
            
        Returns:
            True se exportado com sucesso
        """
        
        try:
            video_data = self.get_video_details(video_id)
            if not video_data:
                logger.error(f"❌ Vídeo {video_id} não encontrado")
                return False
            
            # Converter datetime para string para serialização JSON
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(video_data, f, indent=2, ensure_ascii=False, default=json_serializer)
            
            logger.info(f"✅ Dados do vídeo {video_id} exportados para {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar dados: {e}")
            return False
    
    def close(self):
        """Fecha conexão com o banco"""
        self.db.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()