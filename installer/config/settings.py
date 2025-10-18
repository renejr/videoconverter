"""
⚙️ Configurações do Instalador VideoConverter
============================================

Configurações centralizadas para:
- URLs de download
- Versões de software
- Configurações padrão
- Caminhos de instalação
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class PythonConfig:
    """Configurações do Python"""
    default_version: str = "3.13.0"
    supported_versions: List[str] = None
    download_urls: Dict[str, str] = None
    install_path_windows: str = r"C:\Python313"
    install_path_linux: str = "/usr/local/python3.13"
    install_path_macos: str = "/usr/local/python3.13"
    
    def __post_init__(self):
        if self.supported_versions is None:
            self.supported_versions = ["3.13.0", "3.13.1", "3.13.2"]
        
        if self.download_urls is None:
            self.download_urls = {
                "windows_x64": "https://www.python.org/ftp/python/{version}/python-{version}-amd64.exe",
                "windows_x86": "https://www.python.org/ftp/python/{version}/python-{version}.exe",
                "linux_x64": "https://www.python.org/ftp/python/{version}/Python-{version}.tgz",
                "macos_x64": "https://www.python.org/ftp/python/{version}/python-{version}-macos11.pkg",
                "macos_arm64": "https://www.python.org/ftp/python/{version}/python-{version}-macos11.pkg"
            }


@dataclass
class CUDAConfig:
    """Configurações do CUDA"""
    supported_versions: List[str] = None
    download_urls: Dict[str, str] = None
    install_path_windows: str = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    install_path_linux: str = "/usr/local/cuda"
    
    def __post_init__(self):
        if self.supported_versions is None:
            self.supported_versions = [
                "12.6.0", "12.5.1", "12.4.1", "12.3.2", 
                "12.2.2", "12.1.1", "12.0.1", "11.8.0"
            ]
        
        if self.download_urls is None:
            self.download_urls = {
                "windows": "https://developer.download.nvidia.com/compute/cuda/{version}/local_installers/cuda_{version}_windows.exe",
                "linux": "https://developer.download.nvidia.com/compute/cuda/{version}/local_installers/cuda_{version}_linux.run",
                "linux_ubuntu": "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-toolkit-{major}-{minor}_{version}-1_amd64.deb"
            }


@dataclass
class FFmpegConfig:
    """Configurações do FFmpeg"""
    download_urls: Dict[str, str] = None
    install_path_windows: str = r"C:\ffmpeg"
    install_path_linux: str = "/usr/local/bin"
    install_path_macos: str = "/usr/local/bin"
    
    def __post_init__(self):
        if self.download_urls is None:
            self.download_urls = {
                "windows": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
                "windows_full": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.zip",
                "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
                "macos": "https://evermeet.cx/ffmpeg/ffmpeg-{version}.zip",
                "github_api": "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"
            }


@dataclass
class ValidationConfig:
    """Configurações de validação"""
    timeout_seconds: int = 30
    retry_attempts: int = 3
    benchmark_duration: int = 10
    test_file_size_mb: int = 1
    
    # Testes de performance
    python_performance_threshold: float = 10.0  # segundos
    cuda_memory_threshold_mb: int = 100
    ffmpeg_fps_threshold: int = 30


@dataclass
class NetworkConfig:
    """Configurações de rede"""
    timeout_seconds: int = 30
    retry_attempts: int = 3
    chunk_size_bytes: int = 8192
    max_concurrent_downloads: int = 3
    user_agent: str = "VideoConverter-Installer/1.0"
    
    # Mirrors alternativos
    mirror_urls: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.mirror_urls is None:
            self.mirror_urls = {
                "python": [
                    "https://www.python.org/ftp/python/",
                    "https://python.mirror.digitalpacific.com.au/",
                    "https://python.mirror.ac.za/"
                ],
                "ffmpeg": [
                    "https://www.gyan.dev/ffmpeg/builds/",
                    "https://johnvansickle.com/ffmpeg/releases/",
                    "https://github.com/BtbN/FFmpeg-Builds/releases/"
                ]
            }


@dataclass
class LoggingConfig:
    """Configurações de logging"""
    level: str = "INFO"
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5
    log_directory: str = "logs"
    
    # Formatação
    console_format: str = "%(asctime)s | %(levelname)8s | %(name)s | %(message)s"
    file_format: str = "%(asctime)s | %(levelname)8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class InstallerSettings:
    """
    Configurações centralizadas do instalador
    
    Gerencia todas as configurações do sistema:
    - Componentes de software
    - URLs de download
    - Caminhos de instalação
    - Configurações de rede
    - Validação e logging
    """
    
    def __init__(self, config_file: str = None):
        """
        Inicializa configurações
        
        Args:
            config_file: Arquivo de configuração personalizada
        """
        # Configurações padrão
        self.python = PythonConfig()
        self.cuda = CUDAConfig()
        self.ffmpeg = FFmpegConfig()
        self.validation = ValidationConfig()
        self.network = NetworkConfig()
        self.logging = LoggingConfig()
        
        # Configurações gerais
        self.installer_version = "1.0.0"
        self.cache_enabled = True
        self.cache_directory = "cache"
        self.temp_directory = "temp"
        self.offline_mode = False
        
        # Privilégios
        self.require_admin = True
        self.auto_elevate = True
        
        # Interface
        self.progress_style = "modern"
        self.color_enabled = True
        self.animation_enabled = True
        
        # Carregar configuração personalizada se fornecida
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """
        Carrega configurações de arquivo JSON
        
        Args:
            config_file: Caminho para arquivo de configuração
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Aplicar configurações carregadas
            self._apply_config(config_data)
            
        except Exception as e:
            print(f"Erro ao carregar configuração de {config_file}: {e}")
    
    def _apply_config(self, config_data: Dict[str, Any]):
        """Aplica configurações do dicionário"""
        for section, values in config_data.items():
            if hasattr(self, section) and isinstance(values, dict):
                section_obj = getattr(self, section)
                
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)
            elif hasattr(self, section):
                setattr(self, section, values)
    
    def save_to_file(self, config_file: str):
        """
        Salva configurações em arquivo JSON
        
        Args:
            config_file: Caminho para salvar configuração
        """
        try:
            config_data = {
                "python": asdict(self.python),
                "cuda": asdict(self.cuda),
                "ffmpeg": asdict(self.ffmpeg),
                "validation": asdict(self.validation),
                "network": asdict(self.network),
                "logging": asdict(self.logging),
                "installer_version": self.installer_version,
                "cache_enabled": self.cache_enabled,
                "cache_directory": self.cache_directory,
                "temp_directory": self.temp_directory,
                "offline_mode": self.offline_mode,
                "require_admin": self.require_admin,
                "auto_elevate": self.auto_elevate,
                "progress_style": self.progress_style,
                "color_enabled": self.color_enabled,
                "animation_enabled": self.animation_enabled
            }
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erro ao salvar configuração em {config_file}: {e}")
    
    def get_python_url(self, version: str, os_type: str, architecture: str) -> str:
        """
        Obtém URL de download do Python
        
        Args:
            version: Versão do Python
            os_type: Sistema operacional
            architecture: Arquitetura
            
        Returns:
            str: URL de download
        """
        key = f"{os_type}_{architecture}"
        if key in self.python.download_urls:
            return self.python.download_urls[key].format(version=version)
        return ""
    
    def get_cuda_url(self, version: str, os_type: str) -> str:
        """
        Obtém URL de download do CUDA
        
        Args:
            version: Versão do CUDA
            os_type: Sistema operacional
            
        Returns:
            str: URL de download
        """
        if os_type in self.cuda.download_urls:
            url_template = self.cuda.download_urls[os_type]
            
            # Extrair versões para templates específicos
            major, minor = version.split('.')[:2]
            
            return url_template.format(
                version=version,
                major=major,
                minor=minor
            )
        return ""
    
    def get_ffmpeg_url(self, os_type: str, build_type: str = "release") -> str:
        """
        Obtém URL de download do FFmpeg
        
        Args:
            os_type: Sistema operacional
            build_type: Tipo de build (release, full)
            
        Returns:
            str: URL de download
        """
        key = os_type
        if build_type == "full" and os_type == "windows":
            key = "windows_full"
        
        if key in self.ffmpeg.download_urls:
            return self.ffmpeg.download_urls[key]
        return ""
    
    def get_install_path(self, component: str, os_type: str) -> str:
        """
        Obtém caminho de instalação para componente
        
        Args:
            component: Nome do componente (python, cuda, ffmpeg)
            os_type: Sistema operacional
            
        Returns:
            str: Caminho de instalação
        """
        component_config = getattr(self, component, None)
        if not component_config:
            return ""
        
        path_attr = f"install_path_{os_type}"
        return getattr(component_config, path_attr, "")
    
    def is_version_supported(self, component: str, version: str) -> bool:
        """
        Verifica se versão é suportada
        
        Args:
            component: Nome do componente
            version: Versão a verificar
            
        Returns:
            bool: True se suportada
        """
        component_config = getattr(self, component, None)
        if not component_config:
            return False
        
        supported_versions = getattr(component_config, "supported_versions", [])
        return version in supported_versions
    
    def get_cache_path(self, component: str, filename: str) -> str:
        """
        Obtém caminho de cache para arquivo
        
        Args:
            component: Nome do componente
            filename: Nome do arquivo
            
        Returns:
            str: Caminho completo do cache
        """
        cache_dir = Path(self.cache_directory) / component
        cache_dir.mkdir(parents=True, exist_ok=True)
        return str(cache_dir / filename)
    
    def get_temp_path(self, filename: str) -> str:
        """
        Obtém caminho temporário para arquivo
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            str: Caminho temporário
        """
        temp_dir = Path(self.temp_directory)
        temp_dir.mkdir(parents=True, exist_ok=True)
        return str(temp_dir / filename)
    
    def validate_config(self) -> List[str]:
        """
        Valida configurações
        
        Returns:
            List[str]: Lista de erros encontrados
        """
        errors = []
        
        # Validar versões Python
        if not self.python.supported_versions:
            errors.append("Nenhuma versão Python configurada")
        
        # Validar URLs
        required_urls = ["windows_x64", "linux_x64"]
        for url_key in required_urls:
            if url_key not in self.python.download_urls:
                errors.append(f"URL Python não configurada: {url_key}")
        
        # Validar timeouts
        if self.network.timeout_seconds <= 0:
            errors.append("Timeout de rede deve ser positivo")
        
        if self.validation.timeout_seconds <= 0:
            errors.append("Timeout de validação deve ser positivo")
        
        # Validar caminhos
        for component in ["python", "cuda", "ffmpeg"]:
            for os_type in ["windows", "linux"]:
                path = self.get_install_path(component, os_type)
                if not path:
                    errors.append(f"Caminho de instalação não configurado: {component}/{os_type}")
        
        return errors
    
    def __str__(self) -> str:
        """Representação string das configurações"""
        return f"InstallerSettings(version={self.installer_version}, cache={self.cache_enabled})"
    
    def __repr__(self) -> str:
        """Representação detalhada das configurações"""
        return (f"InstallerSettings("
                f"version={self.installer_version}, "
                f"python={self.python.default_version}, "
                f"cuda_versions={len(self.cuda.supported_versions)}, "
                f"cache={self.cache_enabled})")


# Configurações globais padrão
DEFAULT_SETTINGS = InstallerSettings()


def load_settings(config_file: str = None) -> InstallerSettings:
    """
    Carrega configurações do instalador
    
    Args:
        config_file: Arquivo de configuração opcional
        
    Returns:
        InstallerSettings: Configurações carregadas
    """
    return InstallerSettings(config_file)


def create_default_config(output_file: str):
    """
    Cria arquivo de configuração padrão
    
    Args:
        output_file: Caminho para salvar configuração
    """
    settings = InstallerSettings()
    settings.save_to_file(output_file)
    print(f"Configuração padrão criada em: {output_file}")


if __name__ == "__main__":
    # Teste das configurações
    settings = InstallerSettings()
    
    print("🔧 Configurações do Instalador VideoConverter")
    print("=" * 50)
    print(f"Versão: {settings.installer_version}")
    print(f"Python padrão: {settings.python.default_version}")
    print(f"Versões CUDA: {len(settings.cuda.supported_versions)}")
    print(f"Cache habilitado: {settings.cache_enabled}")
    
    # Validar configurações
    errors = settings.validate_config()
    if errors:
        print("\n❌ Erros de configuração:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("\n✅ Configurações válidas")
    
    # Exemplo de URLs
    print(f"\n🔗 Exemplo de URLs:")
    print(f"Python Windows: {settings.get_python_url('3.13.0', 'windows', 'x64')}")
    print(f"CUDA Linux: {settings.get_cuda_url('12.6.0', 'linux')}")
    print(f"FFmpeg Windows: {settings.get_ffmpeg_url('windows')}")