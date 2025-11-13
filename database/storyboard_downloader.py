#!/usr/bin/env python3
"""
Módulo de Download e Processamento de Storyboards
Baixa e processa storyboards MHTML, extraindo frames individuais
"""

import requests
import logging
from typing import Dict, List, Optional, Tuple, Callable, Any
from pathlib import Path
import tempfile
import re
import base64
from PIL import Image
import io
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .video_queries import VideoQueries

logger = logging.getLogger(__name__)

class StoryboardDownloader:
    """
    Classe para download e processamento de storyboards
    """
    
    def __init__(self, db_path: str = "video_metadata.db", download_dir: str = None):
        """
        Inicializa o downloader de storyboards
        
        Args:
            db_path: Caminho para o banco de dados
            download_dir: Diretório para salvar storyboards (padrão: temp)
        """
        self.queries = VideoQueries(db_path)
        self.download_dir = Path(download_dir) if download_dir else Path(tempfile.gettempdir()) / "vidconv_storyboards"
        self.download_dir.mkdir(exist_ok=True, parents=True)
        
        # Configurações de download
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Controle de progresso
        self.progress_callback: Optional[Callable] = None
        self.cancel_event = threading.Event()
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        """
        Define callback para progresso do download
        
        Args:
            callback: Função que recebe (operação, atual, total)
        """
        self.progress_callback = callback
    
    def download_video_storyboards(self, video_id: str, quality: str = 'best') -> List[str]:
        """
        Baixa todos os storyboards de um vídeo
        
        Args:
            video_id: ID do vídeo
            quality: Qualidade desejada ('best', 'medium', 'low')
            
        Returns:
            Lista de caminhos dos arquivos baixados
        """
        
        try:
            # Buscar storyboards do vídeo
            video_details = self.queries.get_video_details(video_id)
            if not video_details:
                logger.error(f"❌ Vídeo {video_id} não encontrado")
                return []
            
            storyboards = video_details.get('storyboards', [])
            if not storyboards:
                logger.warning(f"⚠️ Nenhum storyboard encontrado para {video_id}")
                return []
            
            # Selecionar storyboard baseado na qualidade
            selected_storyboard = self._select_storyboard_by_quality(storyboards, quality)
            if not selected_storyboard:
                logger.error(f"❌ Nenhum storyboard adequado encontrado para qualidade '{quality}'")
                return []
            
            logger.info(f"📥 Baixando storyboard {selected_storyboard['storyboard_id']} para {video_id}")
            
            # Baixar storyboard
            downloaded_files = self._download_storyboard(video_id, selected_storyboard)
            
            if downloaded_files:
                # Marcar como baixado no banco
                storyboard_dir = self.download_dir / video_id / selected_storyboard['storyboard_id']
                self.queries.mark_storyboard_downloaded(
                    selected_storyboard['id'], 
                    str(storyboard_dir)
                )
                
                logger.info(f"✅ Storyboard baixado: {len(downloaded_files)} arquivos")
            
            return downloaded_files
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar storyboards: {e}")
            return []
    
    def _select_storyboard_by_quality(self, storyboards: List[Dict], quality: str) -> Optional[Dict]:
        """
        Seleciona o melhor storyboard baseado na qualidade
        
        Args:
            storyboards: Lista de storyboards disponíveis
            quality: Qualidade desejada
            
        Returns:
            Storyboard selecionado ou None
        """
        
        if not storyboards:
            return None
        
        # Ordenar por resolução (maior primeiro)
        sorted_storyboards = sorted(
            storyboards, 
            key=lambda x: (x.get('width', 0) * x.get('height', 0)), 
            reverse=True
        )
        
        if quality == 'best':
            return sorted_storyboards[0]
        elif quality == 'medium' and len(sorted_storyboards) > 1:
            return sorted_storyboards[len(sorted_storyboards) // 2]
        elif quality == 'low':
            return sorted_storyboards[-1]
        else:
            return sorted_storyboards[0]
    
    def _download_storyboard(self, video_id: str, storyboard: Dict) -> List[str]:
        """
        Baixa um storyboard específico
        
        Args:
            video_id: ID do vídeo
            storyboard: Dados do storyboard
            
        Returns:
            Lista de arquivos baixados
        """
        
        storyboard_url = storyboard.get('url')
        if not storyboard_url:
            logger.error("❌ URL do storyboard não encontrada")
            return []
        
        # Criar diretório para o storyboard
        storyboard_dir = self.download_dir / video_id / storyboard['storyboard_id']
        storyboard_dir.mkdir(exist_ok=True, parents=True)
        
        downloaded_files = []
        
        try:
            # Verificar se é MHTML ou URL direta
            if storyboard_url.endswith('.mhtml') or 'mhtml' in storyboard_url:
                downloaded_files = self._download_mhtml_storyboard(storyboard_url, storyboard_dir, storyboard)
            else:
                downloaded_files = self._download_direct_storyboard(storyboard_url, storyboard_dir, storyboard)
            
            # Baixar fragmentos se disponíveis
            fragments = self.queries.get_storyboard_fragments(storyboard['id'])
            if fragments:
                fragment_files = self._download_storyboard_fragments(fragments, storyboard_dir)
                downloaded_files.extend(fragment_files)
            
            return downloaded_files
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar storyboard: {e}")
            return []
    
    def _download_mhtml_storyboard(self, url: str, output_dir: Path, storyboard: Dict) -> List[str]:
        """
        Baixa e processa storyboard MHTML
        
        Args:
            url: URL do arquivo MHTML
            output_dir: Diretório de saída
            storyboard: Dados do storyboard
            
        Returns:
            Lista de arquivos extraídos
        """
        
        logger.info(f"📥 Baixando MHTML: {url}")
        
        try:
            # Baixar arquivo MHTML
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Salvar arquivo MHTML original
            mhtml_path = output_dir / "storyboard.mhtml"
            with open(mhtml_path, 'wb') as f:
                f.write(response.content)
            
            # Processar MHTML e extrair imagens
            extracted_files = self._extract_images_from_mhtml(response.content, output_dir, storyboard)
            extracted_files.append(str(mhtml_path))
            
            return extracted_files
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar MHTML: {e}")
            return []
    
    def _extract_images_from_mhtml(self, mhtml_content: bytes, output_dir: Path, storyboard: Dict) -> List[str]:
        """
        Extrai imagens de um arquivo MHTML
        
        Args:
            mhtml_content: Conteúdo do arquivo MHTML
            output_dir: Diretório de saída
            storyboard: Dados do storyboard
            
        Returns:
            Lista de arquivos de imagem extraídos
        """
        
        extracted_files = []
        
        try:
            # Converter bytes para string
            content_str = mhtml_content.decode('utf-8', errors='ignore')
            
            # Encontrar imagens base64 no MHTML
            image_pattern = r'Content-Type: image/(\w+).*?Content-Transfer-Encoding: base64\s*\n\s*([A-Za-z0-9+/=\s]+)'
            matches = re.findall(image_pattern, content_str, re.DOTALL | re.IGNORECASE)
            
            rows = storyboard.get('rows', 1)
            columns = storyboard.get('columns', 1)
            
            for i, (image_format, base64_data) in enumerate(matches):
                try:
                    # Limpar dados base64
                    clean_base64 = re.sub(r'\s+', '', base64_data)
                    
                    # Decodificar imagem
                    image_data = base64.b64decode(clean_base64)
                    
                    # Salvar imagem completa
                    image_path = output_dir / f"storyboard_{i:03d}.{image_format}"
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                    
                    extracted_files.append(str(image_path))
                    
                    # Extrair frames individuais se possível
                    if rows > 1 or columns > 1:
                        frame_files = self._extract_individual_frames(
                            image_data, output_dir, i, rows, columns, image_format
                        )
                        extracted_files.extend(frame_files)
                    
                    if self.progress_callback:
                        self.progress_callback("Extraindo imagens", i + 1, len(matches))
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar imagem {i}: {e}")
                    continue
            
            logger.info(f"✅ {len(extracted_files)} arquivos extraídos do MHTML")
            return extracted_files
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair imagens do MHTML: {e}")
            return []
    
    def _extract_individual_frames(self, image_data: bytes, output_dir: Path, 
                                 storyboard_index: int, rows: int, columns: int, 
                                 image_format: str) -> List[str]:
        """
        Extrai frames individuais de uma imagem de storyboard
        
        Args:
            image_data: Dados da imagem
            output_dir: Diretório de saída
            storyboard_index: Índice do storyboard
            rows: Número de linhas
            columns: Número de colunas
            image_format: Formato da imagem
            
        Returns:
            Lista de arquivos de frames extraídos
        """
        
        frame_files = []
        
        try:
            # Abrir imagem
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            # Calcular dimensões de cada frame
            frame_width = width // columns
            frame_height = height // rows
            
            # Criar diretório para frames
            frames_dir = output_dir / f"frames_{storyboard_index:03d}"
            frames_dir.mkdir(exist_ok=True)
            
            frame_count = 0
            for row in range(rows):
                for col in range(columns):
                    # Calcular coordenadas do frame
                    left = col * frame_width
                    top = row * frame_height
                    right = left + frame_width
                    bottom = top + frame_height
                    
                    # Extrair frame
                    frame = image.crop((left, top, right, bottom))
                    
                    # Salvar frame
                    frame_path = frames_dir / f"frame_{frame_count:04d}.{image_format}"
                    frame.save(frame_path)
                    
                    frame_files.append(str(frame_path))
                    frame_count += 1
            
            logger.info(f"✅ {frame_count} frames extraídos da imagem {storyboard_index}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair frames: {e}")
        
        return frame_files
    
    def _download_direct_storyboard(self, url: str, output_dir: Path, storyboard: Dict) -> List[str]:
        """
        Baixa storyboard de URL direta
        
        Args:
            url: URL da imagem
            output_dir: Diretório de saída
            storyboard: Dados do storyboard
            
        Returns:
            Lista de arquivos baixados
        """
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Determinar extensão do arquivo
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            elif 'png' in content_type:
                ext = 'png'
            elif 'webp' in content_type:
                ext = 'webp'
            else:
                ext = 'jpg'  # padrão
            
            # Salvar arquivo
            file_path = output_dir / f"storyboard.{ext}"
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Storyboard baixado: {file_path}")
            return [str(file_path)]
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar storyboard direto: {e}")
            return []
    
    def _download_storyboard_fragments(self, fragments: List[Dict], output_dir: Path) -> List[str]:
        """
        Baixa fragmentos de storyboard
        
        Args:
            fragments: Lista de fragmentos
            output_dir: Diretório de saída
            
        Returns:
            Lista de arquivos baixados
        """
        
        if not fragments:
            return []
        
        logger.info(f"📥 Baixando {len(fragments)} fragmentos")
        
        # Criar diretório para fragmentos
        fragments_dir = output_dir / "fragments"
        fragments_dir.mkdir(exist_ok=True)
        
        downloaded_files = []
        
        # Download paralelo dos fragmentos
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_fragment = {
                executor.submit(self._download_fragment, fragment, fragments_dir): fragment
                for fragment in fragments
            }
            
            for future in as_completed(future_to_fragment):
                if self.cancel_event.is_set():
                    break
                
                fragment = future_to_fragment[future]
                try:
                    file_path = future.result()
                    if file_path:
                        downloaded_files.append(file_path)
                    
                    if self.progress_callback:
                        self.progress_callback(
                            "Baixando fragmentos", 
                            len(downloaded_files), 
                            len(fragments)
                        )
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao baixar fragmento {fragment.get('fragment_index', '?')}: {e}")
        
        logger.info(f"✅ {len(downloaded_files)} fragmentos baixados")
        return downloaded_files
    
    def _download_fragment(self, fragment: Dict, output_dir: Path) -> Optional[str]:
        """
        Baixa um fragmento individual
        
        Args:
            fragment: Dados do fragmento
            output_dir: Diretório de saída
            
        Returns:
            Caminho do arquivo baixado ou None se erro
        """
        
        url = fragment.get('url')
        if not url:
            return None
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Nome do arquivo baseado no índice
            fragment_index = fragment.get('fragment_index', 0)
            file_path = output_dir / f"fragment_{fragment_index:04d}.jpg"
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return str(file_path)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao baixar fragmento: {e}")
            return None
    
    def download_video_thumbnails(self, video_id: str, quality: str = 'high') -> List[str]:
        """
        Baixa thumbnails de um vídeo
        
        Args:
            video_id: ID do vídeo
            quality: Qualidade desejada
            
        Returns:
            Lista de arquivos baixados
        """
        
        try:
            # Buscar melhor thumbnail
            thumbnail = self.queries.get_best_thumbnail(video_id, quality)
            if not thumbnail:
                logger.warning(f"⚠️ Nenhuma thumbnail encontrada para {video_id}")
                return []
            
            # Criar diretório
            thumb_dir = self.download_dir / video_id / "thumbnails"
            thumb_dir.mkdir(exist_ok=True, parents=True)
            
            # Baixar thumbnail
            url = thumbnail['url']
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Salvar arquivo
            ext = thumbnail.get('format', 'jpg')
            file_path = thumb_dir / f"thumbnail_{quality}.{ext}"
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Marcar como baixada
            self.queries.mark_thumbnail_downloaded(
                thumbnail['id'], 
                str(file_path), 
                len(response.content)
            )
            
            logger.info(f"✅ Thumbnail baixada: {file_path}")
            return [str(file_path)]
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar thumbnail: {e}")
            return []
    
    def cancel_downloads(self):
        """Cancela downloads em andamento"""
        self.cancel_event.set()
        logger.info("🛑 Downloads cancelados")
    
    def get_download_progress(self) -> Dict[str, Any]:
        """
        Obtém informações de progresso dos downloads
        
        Returns:
            Dicionário com informações de progresso
        """
        
        # Implementar lógica de progresso conforme necessário
        return {
            'active_downloads': 0,
            'completed_downloads': 0,
            'failed_downloads': 0,
            'total_size_downloaded': 0
        }
    
    def cleanup_downloads(self, video_id: str = None):
        """
        Remove arquivos de download
        
        Args:
            video_id: ID específico do vídeo (None para limpar tudo)
        """
        
        try:
            if video_id:
                video_dir = self.download_dir / video_id
                if video_dir.exists():
                    import shutil
                    shutil.rmtree(video_dir)
                    logger.info(f"🧹 Downloads do vídeo {video_id} removidos")
            else:
                import shutil
                if self.download_dir.exists():
                    shutil.rmtree(self.download_dir)
                    self.download_dir.mkdir(exist_ok=True)
                    logger.info("🧹 Todos os downloads removidos")
                    
        except Exception as e:
            logger.error(f"❌ Erro ao limpar downloads: {e}")
    
    def close(self):
        """Fecha recursos"""
        self.cancel_downloads()
        self.session.close()
        self.queries.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Função utilitária
def download_video_storyboards(video_id: str, 
                             db_path: str = "video_metadata.db",
                             download_dir: str = None,
                             quality: str = 'best') -> List[str]:
    """
    Função utilitária para baixar storyboards de um vídeo
    
    Args:
        video_id: ID do vídeo
        db_path: Caminho do banco de dados
        download_dir: Diretório de download
        quality: Qualidade desejada
        
    Returns:
        Lista de arquivos baixados
    """
    
    with StoryboardDownloader(db_path, download_dir) as downloader:
        return downloader.download_video_storyboards(video_id, quality)