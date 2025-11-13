#!/usr/bin/env python3
"""
Módulo de Extração de Metadados com yt-dlp
Extrai e processa metadados completos de vídeos para armazenamento no banco
"""

import yt_dlp
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import re
import tempfile
import os

from .video_metadata_db import VideoMetadataDB

logger = logging.getLogger(__name__)

class MetadataExtractor:
    """
    Classe para extrair metadados completos usando yt-dlp
    """
    
    def __init__(self, db_path: str = "video_metadata.db"):
        """
        Inicializa o extrator de metadados
        
        Args:
            db_path: Caminho para o banco de dados
        """
        self.db = VideoMetadataDB(db_path)
        self.temp_dir = Path(tempfile.gettempdir()) / "vidconv_metadata"
        self.temp_dir.mkdir(exist_ok=True)
    
    def extract_metadata(self, url: str, save_thumbnails: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extrai metadados completos de um vídeo
        
        Args:
            url: URL do vídeo
            save_thumbnails: Se deve baixar thumbnails
            
        Returns:
            Dicionário com metadados extraídos ou None se erro
        """
        
        try:
            # Configurar yt-dlp para extração de metadados
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writeinfojson': True,
                'skip_download': True,
                'outtmpl': str(self.temp_dir / '%(id)s.%(ext)s'),
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            if save_thumbnails:
                ydl_opts.update({
                    'writethumbnail': True,
                    'writeallformats': True,
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"🔍 Extraindo metadados de: {url}")
                
                # Extrair informações
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    logger.error("❌ Não foi possível extrair metadados")
                    return None
                
                logger.info(f"✅ Metadados extraídos para: {info.get('title', 'Título não disponível')}")
                return info
                
        except Exception as e:
            logger.error(f"❌ Erro ao extrair metadados: {e}")
            return None
    
    def process_and_store_metadata(self, url: str, save_thumbnails: bool = False) -> Optional[str]:
        """
        Extrai metadados e armazena no banco de dados
        
        Args:
            url: URL do vídeo
            save_thumbnails: Se deve baixar thumbnails
            
        Returns:
            ID do vídeo se processado com sucesso, None caso contrário
        """
        
        # Extrair metadados
        metadata = self.extract_metadata(url, save_thumbnails)
        if not metadata:
            return None

        try:
            # Comentário de função: Detecta automaticamente se é playlist e processa filhos
            # - Para playlists, insere o registro da playlist (pai) com is_playlist=1
            # - Itera sobre 'entries' para inserir cada vídeo filho individualmente
            # - Cria vínculos na tabela 'playlist_videos' com posição

            video_id = metadata.get('id')
            if not video_id:
                raise ValueError("ID do vídeo não encontrado nos metadados")

            # Adicionar URL original aos metadados
            metadata['original_url'] = url

            is_playlist = str(metadata.get('_type', '')).lower() == 'playlist' or bool(metadata.get('entries'))

            if is_playlist:
                # Inserir registro da playlist (pai)
                parent_inserted = self.db.insert_video_metadata(metadata)
                if not parent_inserted:
                    raise ValueError("Falha ao inserir metadados da playlist no banco de dados")

                logger.info(f"📚 Playlist detectada: {metadata.get('title', video_id)} ({video_id})")

                # Processar vídeos filhos
                entries = metadata.get('entries') or []
                total = len(entries)
                logger.info(f"🧩 Processando {total} vídeos filhos da playlist...")

                processed_children = 0
                for idx, entry in enumerate(entries, start=1):
                    try:
                        if not entry or not isinstance(entry, dict):
                            logger.warning(f"⚠️ Entrada inválida na playlist (índice {idx})")
                            continue

                        child_id = entry.get('id')
                        if not child_id:
                            # Alguns modos retornam apenas URL; tentar extrair ou pular
                            possible_url = entry.get('webpage_url') or entry.get('url')
                            logger.warning(f"⚠️ Vídeo filho sem 'id' na entrada {idx}. URL: {possible_url}")
                            continue

                        # Garantir URL original do filho
                        child_url = entry.get('webpage_url') or entry.get('url') or url
                        entry['original_url'] = child_url

                        # Inserir metadados do filho
                        child_inserted = self.db.insert_video_metadata(entry)
                        if not child_inserted:
                            logger.error(f"❌ Falha ao inserir metadados do vídeo filho: {child_id}")
                            continue

                        # Posição na playlist
                        position = entry.get('playlist_index')
                        if position is None:
                            position = idx

                        # Vincular filho à playlist
                        linked = self.db.link_playlist_video(video_id, child_id, position)
                        if not linked:
                            logger.error(f"❌ Falha ao vincular filho {child_id} à playlist {video_id}")
                            continue

                        processed_children += 1
                    except Exception as child_err:
                        logger.error(f"❌ Erro ao processar filho {idx}: {child_err}")
                        continue

                logger.info(f"✅ Playlist '{metadata.get('title', video_id)}' armazenada com {processed_children}/{total} filhos")
                return video_id
            else:
                # Vídeo único
                success = self.db.insert_video_metadata(metadata)
                if not success:
                    raise ValueError("Falha ao inserir metadados do vídeo no banco de dados")

                logger.info(f"✅ Metadados armazenados para vídeo: {video_id}")
                return video_id

        except Exception as e:
            logger.error(f"❌ Erro ao armazenar metadados: {e}")
            return None
    

    
    def update_video_metadata(self, video_id: str, url: str = None) -> bool:
        """
        Atualiza metadados de um vídeo existente
        
        Args:
            video_id: ID do vídeo
            url: URL do vídeo (opcional, será buscada no banco se não fornecida)
            
        Returns:
            True se atualizado com sucesso
        """
        
        try:
            # Buscar URL se não fornecida
            if not url:
                connection = self.db.get_connection()
                cursor = connection.cursor()
                cursor.execute("SELECT original_url FROM videos WHERE video_id = ?", (video_id,))
                result = cursor.fetchone()
                if not result:
                    logger.error(f"❌ Vídeo {video_id} não encontrado no banco")
                    return False
                url = result[0]
            
            # Extrair novos metadados
            metadata = self.extract_metadata(url)
            if not metadata:
                return False
            
            # Atualizar dados (implementar lógica de update conforme necessário)
            logger.info(f"✅ Metadados do vídeo {video_id} atualizados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar metadados: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Remove arquivos temporários criados durante a extração"""
        
        try:
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            logger.info("🧹 Arquivos temporários removidos")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao limpar arquivos temporários: {e}")
    
    def close(self):
        """Fecha conexão e limpa recursos"""
        self.cleanup_temp_files()
        self.db.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Função utilitária para uso direto
def extract_and_store_video_metadata(url: str, db_path: str = "video_metadata.db", save_thumbnails: bool = False) -> Optional[str]:
    """
    Função utilitária para extrair e armazenar metadados de um vídeo
    
    Args:
        url: URL do vídeo
        db_path: Caminho do banco de dados
        save_thumbnails: Se deve baixar thumbnails
        
    Returns:
        ID do vídeo se processado com sucesso
    """
    
    with MetadataExtractor(db_path) as extractor:
        return extractor.process_and_store_metadata(url, save_thumbnails)