"""
📥 Sistema de Download Inteligente - VideoConverter Installer
===========================================================

Downloader avançado com:
- Resumo de downloads interrompidos
- Cache local inteligente
- Verificação de integridade (MD5, SHA256)
- Múltiplas fontes/mirrors
- Retry automático com backoff
- Progress tracking integrado
- Suporte a proxy
"""

import os
import sys
import time
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, List, Dict, Callable, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import json
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import ssl

from .progress import ProgressBar, download_progress_bar
from .logger import Logger


@dataclass
class DownloadInfo:
    """Informações de download"""

    url: str
    filename: str
    size: Optional[int] = None
    md5: Optional[str] = None
    sha256: Optional[str] = None
    mirrors: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None


@dataclass
class DownloadResult:
    """Resultado de download"""

    success: bool
    filepath: Optional[str] = None
    size: int = 0
    duration: float = 0.0
    error: Optional[str] = None
    source_url: Optional[str] = None


class DownloadCache:
    """
    Sistema de cache para downloads

    Gerencia cache local de arquivos baixados com verificação de integridade
    """

    def __init__(self, cache_dir: str = None):
        """
        Inicializa cache de downloads

        Args:
            cache_dir: Diretório de cache (padrão: temp/vidconv_cache)
        """
        if cache_dir is None:
            cache_dir = os.path.join(tempfile.gettempdir(), "vidconv_cache")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Arquivo de metadados do cache
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()

        self.logger = Logger("DownloadCache")

    def _load_metadata(self) -> Dict[str, Any]:
        """Carrega metadados do cache"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_metadata(self):
        """Salva metadados do cache"""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Erro ao salvar metadados do cache: {e}")

    def _calculate_hash(self, filepath: str, algorithm: str = "md5") -> str:
        """
        Calcula hash de arquivo

        Args:
            filepath: Caminho do arquivo
            algorithm: Algoritmo (md5, sha256)

        Returns:
            str: Hash calculado
        """
        hash_obj = hashlib.md5() if algorithm == "md5" else hashlib.sha256()

        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    def get_cache_path(self, url: str, filename: str = None) -> str:
        """
        Retorna caminho no cache para URL

        Args:
            url: URL do arquivo
            filename: Nome do arquivo (opcional)

        Returns:
            str: Caminho no cache
        """
        if filename is None:
            filename = os.path.basename(urllib.parse.urlparse(url).path)

        # Usar hash da URL para evitar conflitos
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        safe_filename = f"{url_hash}_{filename}"

        return str(self.cache_dir / safe_filename)

    def is_cached(
        self, url: str, filename: str = None, verify_integrity: bool = True
    ) -> bool:
        """
        Verifica se arquivo está em cache

        Args:
            url: URL do arquivo
            filename: Nome do arquivo
            verify_integrity: Verificar integridade

        Returns:
            bool: True se está em cache e válido
        """
        cache_path = self.get_cache_path(url, filename)

        if not os.path.exists(cache_path):
            return False

        if not verify_integrity:
            return True

        # Verificar metadados
        cache_key = os.path.basename(cache_path)
        if cache_key not in self.metadata:
            return False

        metadata = self.metadata[cache_key]

        # Verificar tamanho
        if os.path.getsize(cache_path) != metadata.get("size", 0):
            return False

        # Verificar hash se disponível
        if "md5" in metadata:
            current_md5 = self._calculate_hash(cache_path, "md5")
            if current_md5 != metadata["md5"]:
                return False

        return True

    def add_to_cache(self, url: str, filepath: str, download_info: DownloadInfo = None):
        """
        Adiciona arquivo ao cache

        Args:
            url: URL original
            filepath: Caminho do arquivo baixado
            download_info: Informações do download
        """
        cache_path = self.get_cache_path(
            url, download_info.filename if download_info else None
        )

        try:
            # Copiar arquivo para cache
            shutil.copy2(filepath, cache_path)

            # Salvar metadados
            cache_key = os.path.basename(cache_path)
            self.metadata[cache_key] = {
                "url": url,
                "size": os.path.getsize(cache_path),
                "timestamp": time.time(),
                "md5": self._calculate_hash(cache_path, "md5"),
            }

            if download_info:
                if download_info.md5:
                    self.metadata[cache_key]["original_md5"] = download_info.md5
                if download_info.sha256:
                    self.metadata[cache_key]["sha256"] = self._calculate_hash(
                        cache_path, "sha256"
                    )

            self._save_metadata()
            self.logger.info(f"Arquivo adicionado ao cache: {cache_key}")

        except Exception as e:
            self.logger.error(f"Erro ao adicionar arquivo ao cache: {e}")

    def get_from_cache(self, url: str, destination: str, filename: str = None) -> bool:
        """
        Copia arquivo do cache para destino

        Args:
            url: URL original
            destination: Diretório de destino
            filename: Nome do arquivo

        Returns:
            bool: True se copiado com sucesso
        """
        cache_path = self.get_cache_path(url, filename)

        if not self.is_cached(url, filename):
            return False

        try:
            dest_path = os.path.join(
                destination, filename or os.path.basename(cache_path)
            )
            shutil.copy2(cache_path, dest_path)
            self.logger.info(f"Arquivo copiado do cache: {dest_path}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao copiar do cache: {e}")
            return False

    def cleanup(self, max_age_days: int = 30, max_size_mb: int = 1000):
        """
        Limpa cache antigo

        Args:
            max_age_days: Idade máxima em dias
            max_size_mb: Tamanho máximo em MB
        """
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        max_size_bytes = max_size_mb * 1024 * 1024

        total_size = 0
        files_to_remove = []

        # Calcular tamanho total e identificar arquivos antigos
        for cache_key, metadata in self.metadata.items():
            cache_path = self.cache_dir / cache_key

            if cache_path.exists():
                file_size = cache_path.stat().st_size
                total_size += file_size

                # Verificar idade
                file_age = current_time - metadata.get("timestamp", 0)
                if file_age > max_age_seconds:
                    files_to_remove.append((cache_key, cache_path, file_size))

        # Remover arquivos antigos
        for cache_key, cache_path, file_size in files_to_remove:
            try:
                cache_path.unlink()
                del self.metadata[cache_key]
                total_size -= file_size
                self.logger.info(f"Arquivo antigo removido do cache: {cache_key}")
            except Exception as e:
                self.logger.warning(f"Erro ao remover arquivo do cache: {e}")

        # Se ainda excede tamanho, remover mais antigos
        if total_size > max_size_bytes:
            # Ordenar por timestamp (mais antigos primeiro)
            remaining_files = [
                (key, self.cache_dir / key, meta.get("timestamp", 0))
                for key, meta in self.metadata.items()
                if (self.cache_dir / key).exists()
            ]
            remaining_files.sort(key=lambda x: x[2])

            for cache_key, cache_path, _ in remaining_files:
                if total_size <= max_size_bytes:
                    break

                try:
                    file_size = cache_path.stat().st_size
                    cache_path.unlink()
                    del self.metadata[cache_key]
                    total_size -= file_size
                    self.logger.info(
                        f"Arquivo removido por limite de tamanho: {cache_key}"
                    )
                except Exception as e:
                    self.logger.warning(f"Erro ao remover arquivo: {e}")

        self._save_metadata()


class SmartDownloader:
    """
    Downloader inteligente com recursos avançados

    Funcionalidades:
    - Resumo de downloads
    - Cache inteligente
    - Múltiplas fontes
    - Verificação de integridade
    - Retry automático
    - Progress tracking
    """

    def __init__(
        self,
        cache_dir: str = None,
        max_retries: int = 3,
        timeout: int = 30,
        chunk_size: int = 8192,
        use_cache: bool = True,
    ):
        """
        Inicializa downloader

        Args:
            cache_dir: Diretório de cache
            max_retries: Máximo de tentativas
            timeout: Timeout em segundos
            chunk_size: Tamanho do chunk
            use_cache: Usar cache
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.use_cache = use_cache

        # Cache
        self.cache = DownloadCache(cache_dir) if use_cache else None

        # Logger
        self.logger = Logger("SmartDownloader")

        # Configurar SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def _get_file_size(self, url: str, headers: Dict[str, str] = None) -> Optional[int]:
        """
        Obtém tamanho do arquivo via HEAD request

        Args:
            url: URL do arquivo
            headers: Headers customizados

        Returns:
            Optional[int]: Tamanho em bytes ou None
        """
        try:
            req = urllib.request.Request(url, method="HEAD")

            if headers:
                for key, value in headers.items():
                    req.add_header(key, value)

            with urllib.request.urlopen(
                req, timeout=self.timeout, context=self.ssl_context
            ) as response:
                content_length = response.headers.get("Content-Length")
                return int(content_length) if content_length else None

        except Exception as e:
            self.logger.debug(f"Erro ao obter tamanho do arquivo: {e}")
            return None

    def _verify_integrity(self, filepath: str, download_info: DownloadInfo) -> bool:
        """
        Verifica integridade do arquivo

        Args:
            filepath: Caminho do arquivo
            download_info: Informações do download

        Returns:
            bool: True se íntegro
        """
        if not os.path.exists(filepath):
            return False

        # Verificar MD5
        if download_info.md5:
            file_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    file_md5.update(chunk)

            if file_md5.hexdigest().lower() != download_info.md5.lower():
                self.logger.error(
                    f"MD5 não confere: esperado {download_info.md5}, obtido {file_md5.hexdigest()}"
                )
                return False

        # Verificar SHA256
        if download_info.sha256:
            file_sha256 = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    file_sha256.update(chunk)

            if file_sha256.hexdigest().lower() != download_info.sha256.lower():
                self.logger.error(
                    f"SHA256 não confere: esperado {download_info.sha256}, obtido {file_sha256.hexdigest()}"
                )
                return False

        return True

    def _download_with_resume(
        self,
        url: str,
        filepath: str,
        download_info: DownloadInfo,
        progress_callback: Optional[Callable] = None,
    ) -> DownloadResult:
        """
        Download com suporte a resumo

        Args:
            url: URL do arquivo
            filepath: Caminho de destino
            download_info: Informações do download
            progress_callback: Callback de progresso

        Returns:
            DownloadResult: Resultado do download
        """
        start_time = time.time()

        # Verificar se arquivo parcial existe
        resume_pos = 0
        if os.path.exists(filepath):
            resume_pos = os.path.getsize(filepath)
            self.logger.info(f"Resumindo download a partir de {resume_pos} bytes")

        try:
            # Preparar request
            req = urllib.request.Request(url)

            # Headers customizados
            if download_info.headers:
                for key, value in download_info.headers.items():
                    req.add_header(key, value)

            # Range header para resumo
            if resume_pos > 0:
                req.add_header("Range", f"bytes={resume_pos}-")

            # Abrir conexão
            with urllib.request.urlopen(
                req, timeout=self.timeout, context=self.ssl_context
            ) as response:
                # Obter tamanho total
                content_length = response.headers.get("Content-Length")
                total_size = (
                    int(content_length) if content_length else download_info.size
                )

                if total_size:
                    total_size += resume_pos  # Adicionar bytes já baixados

                # Abrir arquivo para escrita
                mode = "ab" if resume_pos > 0 else "wb"
                with open(filepath, mode) as f:
                    downloaded = resume_pos

                    while True:
                        chunk = response.read(self.chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        # Callback de progresso
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            # Verificar integridade
            if not self._verify_integrity(filepath, download_info):
                return DownloadResult(
                    success=False, error="Falha na verificação de integridade"
                )

            duration = time.time() - start_time
            final_size = os.path.getsize(filepath)

            return DownloadResult(
                success=True,
                filepath=filepath,
                size=final_size,
                duration=duration,
                source_url=url,
            )

        except Exception as e:
            return DownloadResult(success=False, error=str(e), source_url=url)

    def download(
        self,
        download_info: DownloadInfo,
        destination_dir: str,
        filename: str = None,
        progress_callback: Optional[Callable] = None,
        force_download: bool = False,
    ) -> DownloadResult:
        """
        Download principal com todas as funcionalidades

        Args:
            download_info: Informações do download
            destination_dir: Diretório de destino
            filename: Nome do arquivo (opcional)
            progress_callback: Callback de progresso
            force_download: Forçar download mesmo se em cache

        Returns:
            DownloadResult: Resultado do download
        """
        # Preparar filename
        if filename is None:
            filename = download_info.filename or os.path.basename(
                urllib.parse.urlparse(download_info.url).path
            )

        destination_path = os.path.join(destination_dir, filename)

        # Verificar cache primeiro
        if self.use_cache and not force_download:
            if self.cache.is_cached(download_info.url, filename):
                self.logger.info(f"Arquivo encontrado no cache: {filename}")

                if self.cache.get_from_cache(
                    download_info.url, destination_dir, filename
                ):
                    return DownloadResult(
                        success=True,
                        filepath=destination_path,
                        size=os.path.getsize(destination_path),
                        duration=0.0,
                        source_url="cache",
                    )

        # Criar diretório de destino
        os.makedirs(destination_dir, exist_ok=True)

        # Lista de URLs para tentar
        urls_to_try = [download_info.url]
        if download_info.mirrors:
            urls_to_try.extend(download_info.mirrors)

        # Tentar download de cada URL
        last_error = None

        for attempt, url in enumerate(urls_to_try):
            self.logger.info(f"Tentativa {attempt + 1}: {url}")

            for retry in range(self.max_retries):
                if retry > 0:
                    wait_time = 2**retry  # Backoff exponencial
                    self.logger.info(f"Retry {retry + 1} em {wait_time}s...")
                    time.sleep(wait_time)

                result = self._download_with_resume(
                    url, destination_path, download_info, progress_callback
                )

                if result.success:
                    # Adicionar ao cache
                    if self.use_cache:
                        self.cache.add_to_cache(
                            download_info.url, destination_path, download_info
                        )

                    self.logger.success(f"Download concluído: {filename}")
                    return result

                last_error = result.error
                self.logger.warning(
                    f"Falha no download (tentativa {retry + 1}): {result.error}"
                )

        # Todas as tentativas falharam
        return DownloadResult(
            success=False, error=f"Falha após todas as tentativas: {last_error}"
        )

    def download_multiple(
        self,
        downloads: List[Tuple[DownloadInfo, str]],
        max_concurrent: int = 3,
        progress_callback: Optional[Callable] = None,
    ) -> List[DownloadResult]:
        """
        Download múltiplo com threading

        Args:
            downloads: Lista de (DownloadInfo, destination_dir)
            max_concurrent: Máximo de downloads simultâneos
            progress_callback: Callback de progresso

        Returns:
            List[DownloadResult]: Resultados dos downloads
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submeter todos os downloads
            future_to_info = {
                executor.submit(
                    self.download,
                    download_info,
                    dest_dir,
                    progress_callback=progress_callback,
                ): (download_info, dest_dir)
                for download_info, dest_dir in downloads
            }

            # Coletar resultados
            for future in as_completed(future_to_info):
                download_info, dest_dir = future_to_info[future]

                try:
                    result = future.result()
                    results.append(result)

                    if result.success:
                        self.logger.success(
                            f"Download concluído: {download_info.filename}"
                        )
                    else:
                        self.logger.error(
                            f"Falha no download: {download_info.filename} - {result.error}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Erro no download: {download_info.filename} - {e}"
                    )
                    results.append(DownloadResult(success=False, error=str(e)))

        return results


# Funções de conveniência
def download_file(
    url: str,
    destination: str,
    filename: str = None,
    md5: str = None,
    sha256: str = None,
    show_progress: bool = True,
) -> DownloadResult:
    """
    Download simples de arquivo

    Args:
        url: URL do arquivo
        destination: Diretório de destino
        filename: Nome do arquivo
        md5: Hash MD5 esperado
        sha256: Hash SHA256 esperado
        show_progress: Mostrar progress bar

    Returns:
        DownloadResult: Resultado do download
    """
    download_info = DownloadInfo(
        url=url,
        filename=filename or os.path.basename(urllib.parse.urlparse(url).path),
        md5=md5,
        sha256=sha256,
    )

    downloader = SmartDownloader()

    # Progress bar
    progress_bar = None
    if show_progress:
        # Tentar obter tamanho do arquivo
        file_size = downloader._get_file_size(url)
        if file_size:
            progress_bar = download_progress_bar(file_size, download_info.filename)

    def progress_callback(downloaded: int, total: Optional[int]):
        if progress_bar:
            progress_bar.update(downloaded)

    return downloader.download(
        download_info,
        destination,
        progress_callback=progress_callback if show_progress else None,
    )


if __name__ == "__main__":
    # Teste do sistema de download
    print("🧪 Teste do Sistema de Download\n")

    # Teste básico
    test_url = "https://httpbin.org/bytes/1024"  # 1KB de dados
    test_dest = tempfile.mkdtemp()

    print("1. Download básico:")
    result = download_file(test_url, test_dest, "test_file.bin", show_progress=True)

    if result.success:
        print(f"✅ Download concluído: {result.filepath}")
        print(f"   Tamanho: {result.size} bytes")
        print(f"   Duração: {result.duration:.2f}s")
    else:
        print(f"❌ Falha no download: {result.error}")

    # Limpeza
    shutil.rmtree(test_dest, ignore_errors=True)

    print("\n✅ Teste concluído!")
