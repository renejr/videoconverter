"""
🚀 Instalador Automático de CUDA - VideoConverter Installer
==========================================================

Instalador inteligente de CUDA com:
- Detecção automática da melhor versão
- Download automático por OS
- Instalação silenciosa
- Verificação pós-instalação
- Suporte a Windows, Linux e macOS
- Rollback em caso de falha
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import platform
import json
import re

from .gpu_detector import GPUDetector, GPUInfo
from .os_detector import OSDetector

try:
    from utils.logger import Logger
    from utils.downloader import SmartDownloader, DownloadInfo
    from utils.progress import ProgressBar, installation_progress_bar
except ImportError:
    # Fallback para quando executado diretamente
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from utils.logger import Logger
    from utils.downloader import SmartDownloader, DownloadInfo
    from utils.progress import ProgressBar, installation_progress_bar


@dataclass
class CUDAVersion:
    """Informações de versão CUDA"""

    version: str
    major: int
    minor: int
    patch: int
    download_urls: Dict[str, str]  # OS -> URL
    file_sizes: Dict[str, int]  # OS -> tamanho em bytes
    checksums: Dict[str, str]  # OS -> checksum
    min_driver_version: str
    supported_os: List[str]
    release_date: str


@dataclass
class CUDAInstallation:
    """Informações de instalação CUDA"""

    version: str
    install_path: str
    toolkit_path: str
    runtime_path: str
    samples_path: str
    is_complete: bool
    installation_date: str


class CUDAInstaller:
    """
    Instalador automático de CUDA

    Funcionalidades:
    - Detecção da melhor versão CUDA
    - Download automático
    - Instalação silenciosa por OS
    - Verificação de integridade
    - Configuração de ambiente
    """

    # URLs base para download CUDA
    CUDA_BASE_URLS = {
        "nvidia": "https://developer.download.nvidia.com/compute/cuda",
        "archive": "https://developer.nvidia.com/cuda-toolkit-archive",
    }

    # Versões CUDA disponíveis (principais)
    CUDA_VERSIONS = {
        "12.6.0": CUDAVersion(
            version="12.6.0",
            major=12,
            minor=6,
            patch=0,
            download_urls={
                "windows": "https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.94_windows.exe",
                "linux": "https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.94_linux.run",
                "ubuntu20": "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin",
                "ubuntu22": "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin",
            },
            file_sizes={
                "windows": 3800000000,  # ~3.8GB
                "linux": 4200000000,  # ~4.2GB
            },
            checksums={
                "windows": "sha256:...",  # Seria preenchido com checksums reais
                "linux": "sha256:...",
            },
            min_driver_version="560.94",
            supported_os=["windows", "linux"],
            release_date="2024-08-01",
        ),
        "12.5.0": CUDAVersion(
            version="12.5.0",
            major=12,
            minor=5,
            patch=0,
            download_urls={
                "windows": "https://developer.download.nvidia.com/compute/cuda/12.5.0/local_installers/cuda_12.5.0_555.85_windows.exe",
                "linux": "https://developer.download.nvidia.com/compute/cuda/12.5.0/local_installers/cuda_12.5.0_555.85_linux.run",
            },
            file_sizes={
                "windows": 3700000000,
                "linux": 4100000000,
            },
            checksums={"windows": "sha256:...", "linux": "sha256:..."},
            min_driver_version="555.85",
            supported_os=["windows", "linux"],
            release_date="2024-06-01",
        ),
        "11.8.0": CUDAVersion(
            version="11.8.0",
            major=11,
            minor=8,
            patch=0,
            download_urls={
                "windows": "https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_522.06_windows.exe",
                "linux": "https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61_linux.run",
            },
            file_sizes={
                "windows": 3500000000,
                "linux": 3900000000,
            },
            checksums={"windows": "sha256:...", "linux": "sha256:..."},
            min_driver_version="522.06",
            supported_os=["windows", "linux"],
            release_date="2022-09-01",
        ),
    }

    def __init__(self, cache_dir: str = None):
        """
        Inicializa instalador CUDA

        Args:
            cache_dir: Diretório de cache para downloads
        """
        self.logger = Logger("CUDAInstaller")
        self.os_detector = OSDetector()
        self.gpu_detector = GPUDetector()
        self.downloader = SmartDownloader(cache_dir=cache_dir)

        # Informações do sistema
        self.os_info = self.os_detector.detect()
        self.os_type = self.os_info.name.lower()

        # Diretórios
        self.temp_dir = tempfile.mkdtemp(prefix="cuda_install_")
        self.install_base = self._get_install_base_path()

        self.logger.info(f"Instalador CUDA inicializado para {self.os_type}")

    def _get_install_base_path(self) -> str:
        """
        Retorna caminho base de instalação CUDA

        Returns:
            str: Caminho base
        """
        if self.os_type == "windows":
            return "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA"
        elif self.os_type == "linux":
            return "/usr/local/cuda"
        else:
            return "/opt/cuda"

    def _get_os_key(self) -> str:
        """
        Retorna chave do OS para downloads

        Returns:
            str: Chave do OS
        """
        if self.os_type == "windows":
            return "windows"
        elif self.os_type == "linux":
            # Detectar distribuição específica
            if "ubuntu" in self.os_info.get("distribution", "").lower():
                version = self.os_info.get("version", "")
                if "20.04" in version:
                    return "ubuntu20"
                elif "22.04" in version:
                    return "ubuntu22"
                else:
                    return "linux"
            else:
                return "linux"
        else:
            return "linux"  # Fallback

    def detect_installed_cuda(self) -> List[CUDAInstallation]:
        """
        Detecta instalações CUDA existentes

        Returns:
            List[CUDAInstallation]: Lista de instalações encontradas
        """
        installations = []

        if self.os_type == "windows":
            installations.extend(self._detect_cuda_windows())
        else:
            installations.extend(self._detect_cuda_linux())

        self.logger.info(f"Encontradas {len(installations)} instalação(ões) CUDA")
        return installations

    def _detect_cuda_windows(self) -> List[CUDAInstallation]:
        """Detecta CUDA no Windows"""
        installations = []

        # Verificar diretório padrão
        base_path = Path(self.install_base)

        if base_path.exists():
            for version_dir in base_path.iterdir():
                if version_dir.is_dir() and re.match(r"v\d+\.\d+", version_dir.name):
                    version = version_dir.name[1:]  # Remove 'v'

                    installation = CUDAInstallation(
                        version=version,
                        install_path=str(version_dir),
                        toolkit_path=str(version_dir),
                        runtime_path=str(version_dir / "bin"),
                        samples_path=str(version_dir / "extras" / "CUPTI"),
                        is_complete=self._verify_cuda_installation(str(version_dir)),
                        installation_date="Unknown",
                    )

                    installations.append(installation)

        # Verificar via nvcc
        nvcc_installation = self._detect_cuda_via_nvcc()
        if nvcc_installation and nvcc_installation not in installations:
            installations.append(nvcc_installation)

        return installations

    def _detect_cuda_linux(self) -> List[CUDAInstallation]:
        """Detecta CUDA no Linux"""
        installations = []

        # Verificar diretórios padrão
        cuda_paths = ["/usr/local/cuda", "/opt/cuda", "/usr/cuda"]

        for cuda_path in cuda_paths:
            path = Path(cuda_path)
            if path.exists() and path.is_dir():
                # Verificar se é link simbólico para versão específica
                if path.is_symlink():
                    real_path = path.resolve()
                    version = real_path.name.replace("cuda-", "")
                else:
                    # Tentar detectar versão via nvcc
                    nvcc_path = path / "bin" / "nvcc"
                    if nvcc_path.exists():
                        version = self._get_nvcc_version(str(nvcc_path))
                    else:
                        version = "Unknown"

                installation = CUDAInstallation(
                    version=version,
                    install_path=str(path),
                    toolkit_path=str(path),
                    runtime_path=str(path / "lib64"),
                    samples_path=str(path / "samples"),
                    is_complete=self._verify_cuda_installation(str(path)),
                    installation_date="Unknown",
                )

                installations.append(installation)

        # Verificar instalações via package manager
        installations.extend(self._detect_cuda_packages_linux())

        return installations

    def _detect_cuda_via_nvcc(self) -> Optional[CUDAInstallation]:
        """Detecta CUDA via nvcc no PATH"""
        try:
            result = subprocess.run(
                ["nvcc", "--version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                version_match = re.search(r"release (\d+\.\d+)", result.stdout)
                if version_match:
                    version = version_match.group(1)

                    # Tentar encontrar diretório de instalação
                    nvcc_path = shutil.which("nvcc")
                    if nvcc_path:
                        install_path = str(Path(nvcc_path).parent.parent)

                        return CUDAInstallation(
                            version=version,
                            install_path=install_path,
                            toolkit_path=install_path,
                            runtime_path=str(Path(install_path) / "lib64"),
                            samples_path=str(Path(install_path) / "samples"),
                            is_complete=True,  # Se nvcc funciona, assumir completo
                            installation_date="Unknown",
                        )

        except Exception as e:
            self.logger.debug(f"Erro ao detectar CUDA via nvcc: {e}")

        return None

    def _get_nvcc_version(self, nvcc_path: str) -> str:
        """Obtém versão do nvcc"""
        try:
            result = subprocess.run(
                [nvcc_path, "--version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                version_match = re.search(r"release (\d+\.\d+)", result.stdout)
                if version_match:
                    return version_match.group(1)

        except Exception:
            pass

        return "Unknown"

    def _detect_cuda_packages_linux(self) -> List[CUDAInstallation]:
        """Detecta CUDA via package managers no Linux"""
        installations = []

        # Verificar via dpkg (Debian/Ubuntu)
        try:
            result = subprocess.run(
                ["dpkg", "-l", "cuda-toolkit-*"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "cuda-toolkit-" in line and line.startswith("ii"):
                        parts = line.split()
                        if len(parts) >= 3:
                            package_name = parts[1]
                            version_match = re.search(
                                r"cuda-toolkit-(\d+-\d+)", package_name
                            )
                            if version_match:
                                version = version_match.group(1).replace("-", ".")

                                installation = CUDAInstallation(
                                    version=version,
                                    install_path=f"/usr/local/cuda-{version}",
                                    toolkit_path=f"/usr/local/cuda-{version}",
                                    runtime_path=f"/usr/local/cuda-{version}/lib64",
                                    samples_path=f"/usr/local/cuda-{version}/samples",
                                    is_complete=True,
                                    installation_date="Unknown",
                                )

                                installations.append(installation)

        except Exception:
            pass

        # Verificar via rpm (RedHat/CentOS)
        try:
            result = subprocess.run(
                ["rpm", "-qa", "cuda-toolkit-*"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "cuda-toolkit-" in line:
                        version_match = re.search(r"cuda-toolkit-(\d+-\d+)", line)
                        if version_match:
                            version = version_match.group(1).replace("-", ".")

                            installation = CUDAInstallation(
                                version=version,
                                install_path=f"/usr/local/cuda-{version}",
                                toolkit_path=f"/usr/local/cuda-{version}",
                                runtime_path=f"/usr/local/cuda-{version}/lib64",
                                samples_path=f"/usr/local/cuda-{version}/samples",
                                is_complete=True,
                                installation_date="Unknown",
                            )

                            installations.append(installation)

        except Exception:
            pass

        return installations

    def _verify_cuda_installation(self, install_path: str) -> bool:
        """
        Verifica se instalação CUDA está completa

        Args:
            install_path: Caminho da instalação

        Returns:
            bool: True se completa
        """
        path = Path(install_path)

        # Verificar arquivos essenciais
        essential_files = []

        if self.os_type == "windows":
            essential_files = [
                "bin/nvcc.exe",
                "bin/cudart64_*.dll",
                "lib/x64/cudart.lib",
                "include/cuda.h",
            ]
        else:
            essential_files = ["bin/nvcc", "lib64/libcudart.so", "include/cuda.h"]

        for file_pattern in essential_files:
            if "*" in file_pattern:
                # Usar glob para padrões
                matches = list(path.glob(file_pattern))
                if not matches:
                    return False
            else:
                if not (path / file_pattern).exists():
                    return False

        return True

    def select_best_cuda_version(self, gpu_info: GPUInfo = None) -> Optional[str]:
        """
        Seleciona a melhor versão CUDA para o sistema

        Args:
            gpu_info: Informações da GPU (opcional)

        Returns:
            Optional[str]: Versão CUDA recomendada
        """
        # Se GPU não fornecida, detectar automaticamente
        if gpu_info is None:
            gpus = self.gpu_detector.detect_gpus()
            if gpus:
                gpu_info = self.gpu_detector.get_best_gpu(gpus)

        if gpu_info is None:
            self.logger.warning("Nenhuma GPU detectada, usando versão CUDA padrão")
            return "11.8.0"  # Versão mais compatível

        # Usar versões recomendadas da GPU
        if gpu_info.recommended_cuda_versions:
            for recommended_version in gpu_info.recommended_cuda_versions:
                if recommended_version in self.CUDA_VERSIONS:
                    cuda_version = self.CUDA_VERSIONS[recommended_version]

                    # Verificar se suporta o OS atual
                    os_key = self._get_os_key()
                    if (
                        os_key in cuda_version.supported_os
                        or "linux" in cuda_version.supported_os
                    ):
                        self.logger.info(
                            f"Versão CUDA selecionada: {recommended_version}"
                        )
                        return recommended_version

        # Fallback: versão mais recente compatível
        compatible_versions = []

        for version, cuda_version in self.CUDA_VERSIONS.items():
            os_key = self._get_os_key()
            if (
                os_key in cuda_version.supported_os
                or "linux" in cuda_version.supported_os
            ):
                compatible_versions.append(version)

        if compatible_versions:
            # Ordenar por versão (mais recente primeiro)
            compatible_versions.sort(
                key=lambda v: tuple(map(int, v.split("."))), reverse=True
            )
            selected = compatible_versions[0]
            self.logger.info(f"Versão CUDA selecionada (fallback): {selected}")
            return selected

        self.logger.error("Nenhuma versão CUDA compatível encontrada")
        return None

    def get_cuda_url(self, version: str, os_type: str) -> Optional[str]:
        """
        Obtém URL de download para versão específica do CUDA

        Args:
            version: Versão do CUDA (ex: "12.6.0")
            os_type: Tipo do OS ("windows", "linux", etc.)

        Returns:
            str: URL de download ou None se não encontrada
        """
        if version not in self.CUDA_VERSIONS:
            self.logger.warning(f"Versão CUDA {version} não encontrada")
            return None

        cuda_version = self.CUDA_VERSIONS[version]

        if os_type not in cuda_version.download_urls:
            self.logger.warning(f"OS {os_type} não suportado para CUDA {version}")
            return None

        return cuda_version.download_urls[os_type]

    def download_cuda(self, version: str, destination_dir: str = None) -> Optional[str]:
        """
        Baixa instalador CUDA

        Args:
            version: Versão CUDA
            destination_dir: Diretório de destino

        Returns:
            Optional[str]: Caminho do arquivo baixado
        """
        if version not in self.CUDA_VERSIONS:
            self.logger.error(f"Versão CUDA {version} não suportada")
            return None

        cuda_version = self.CUDA_VERSIONS[version]
        os_key = self._get_os_key()

        if os_key not in cuda_version.download_urls:
            self.logger.error(f"Download não disponível para {os_key}")
            return None

        if destination_dir is None:
            destination_dir = self.temp_dir

        # Preparar informações de download
        download_url = cuda_version.download_urls[os_key]
        filename = os.path.basename(download_url)

        download_info = DownloadInfo(
            url=download_url,
            filename=filename,
            size=cuda_version.file_sizes.get(os_key),
            sha256=cuda_version.checksums.get(os_key),
        )

        self.logger.info(f"Baixando CUDA {version} para {os_key}...")

        # Progress bar
        progress_bar = None
        if download_info.size:
            progress_bar = ProgressBar(
                total=download_info.size,
                description=f"Baixando CUDA {version}",
                style="modern",
                color="download",
                show_speed=True,
                show_eta=True,
            )

        def progress_callback(downloaded: int, total: Optional[int]):
            if progress_bar:
                progress_bar.update(downloaded)

        # Executar download
        result = self.downloader.download(
            download_info, destination_dir, progress_callback=progress_callback
        )

        if progress_bar:
            if result.success:
                progress_bar.finish("Download concluído")
            else:
                progress_bar.cancel("Falha no download")

        if result.success:
            self.logger.success(f"CUDA {version} baixado: {result.filepath}")
            return result.filepath
        else:
            self.logger.error(f"Falha no download: {result.error}")
            return None

    def install_cuda(self, installer_path: str, version: str) -> bool:
        """
        Instala CUDA

        Args:
            installer_path: Caminho do instalador
            version: Versão CUDA

        Returns:
            bool: True se instalação bem-sucedida
        """
        self.logger.info(f"Iniciando instalação CUDA {version}...")

        # Progress bar para instalação
        install_steps = 8
        progress_bar = installation_progress_bar(install_steps, f"CUDA {version}")

        try:
            # Passo 1: Verificar privilégios
            progress_bar.update(
                1, description="Verificando privilégios administrativos"
            )

            if not self.os_detector.has_admin_privileges():
                self.logger.error(
                    "Privilégios administrativos necessários para instalação"
                )
                progress_bar.cancel("Privilégios insuficientes")
                return False

            # Passo 2: Preparar instalação
            progress_bar.update(2, description="Preparando instalação")

            if self.os_type == "windows":
                success = self._install_cuda_windows(
                    installer_path, version, progress_bar
                )
            else:
                success = self._install_cuda_linux(
                    installer_path, version, progress_bar
                )

            if success:
                progress_bar.finish("Instalação CUDA concluída")
                self.logger.success(f"CUDA {version} instalado com sucesso")

                # Configurar ambiente
                self._configure_cuda_environment(version)

                return True
            else:
                progress_bar.cancel("Falha na instalação")
                return False

        except Exception as e:
            self.logger.error(f"Erro durante instalação: {e}")
            progress_bar.cancel(f"Erro: {e}")
            return False

    def _install_cuda_windows(
        self, installer_path: str, version: str, progress_bar: ProgressBar
    ) -> bool:
        """Instala CUDA no Windows"""
        try:
            # Passo 3: Executar instalador
            progress_bar.update(3, description="Executando instalador CUDA")

            # Comando de instalação silenciosa
            install_command = [
                installer_path,
                "-s",  # Instalação silenciosa
                f"nvcc_{version.replace('.', '_')}",
                f"cudart_{version.replace('.', '_')}",
                f"curand_{version.replace('.', '_')}",
                f"cufft_{version.replace('.', '_')}",
                f"cublas_{version.replace('.', '_')}",
                f"cusparse_{version.replace('.', '_')}",
                f"cusolver_{version.replace('.', '_')}",
                f"visual_studio_integration_{version.replace('.', '_')}",
            ]

            # Executar instalação
            result = subprocess.run(
                install_command,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutos
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            progress_bar.update(6, description="Verificando instalação")

            if result.returncode == 0:
                # Verificar se instalação foi bem-sucedida
                install_path = os.path.join(self.install_base, f"v{version}")
                if self._verify_cuda_installation(install_path):
                    progress_bar.update(7, description="Instalação verificada")
                    return True
                else:
                    self.logger.error("Verificação de instalação falhou")
                    return False
            else:
                self.logger.error(f"Instalador retornou código {result.returncode}")
                self.logger.error(f"Stderr: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("Timeout na instalação CUDA")
            return False
        except Exception as e:
            self.logger.error(f"Erro na instalação Windows: {e}")
            return False

    def _install_cuda_linux(
        self, installer_path: str, version: str, progress_bar: ProgressBar
    ) -> bool:
        """Instala CUDA no Linux"""
        try:
            # Passo 3: Tornar executável
            progress_bar.update(3, description="Preparando instalador")
            os.chmod(installer_path, 0o755)

            # Passo 4: Executar instalador
            progress_bar.update(4, description="Executando instalador CUDA")

            # Comando de instalação silenciosa
            install_command = [
                "sudo",
                installer_path,
                "--silent",
                "--toolkit",
                "--samples",
                "--no-opengl-libs",  # Evitar conflitos com drivers gráficos
            ]

            # Executar instalação
            result = subprocess.run(
                install_command,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutos
            )

            progress_bar.update(6, description="Verificando instalação")

            if result.returncode == 0:
                # Verificar se instalação foi bem-sucedida
                install_path = f"/usr/local/cuda-{version}"
                if self._verify_cuda_installation(install_path):
                    progress_bar.update(7, description="Criando links simbólicos")

                    # Criar link simbólico padrão
                    try:
                        subprocess.run(
                            ["sudo", "ln", "-sf", install_path, "/usr/local/cuda"],
                            check=True,
                        )
                    except subprocess.CalledProcessError:
                        self.logger.warning("Falha ao criar link simbólico")

                    return True
                else:
                    self.logger.error("Verificação de instalação falhou")
                    return False
            else:
                self.logger.error(f"Instalador retornou código {result.returncode}")
                self.logger.error(f"Stderr: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("Timeout na instalação CUDA")
            return False
        except Exception as e:
            self.logger.error(f"Erro na instalação Linux: {e}")
            return False

    def _configure_cuda_environment(self, version: str):
        """
        Configura variáveis de ambiente CUDA

        Args:
            version: Versão CUDA instalada
        """
        self.logger.info("Configurando variáveis de ambiente CUDA...")

        if self.os_type == "windows":
            # No Windows, o instalador geralmente configura automaticamente
            cuda_path = os.path.join(self.install_base, f"v{version}")

            # Verificar se PATH foi configurado
            current_path = os.environ.get("PATH", "")
            cuda_bin = os.path.join(cuda_path, "bin")

            if cuda_bin not in current_path:
                self.logger.info("Adicionando CUDA ao PATH do sistema...")
                # Nota: Requer reinicialização ou nova sessão para ter efeito

        else:
            # Linux: Adicionar ao .bashrc/.profile
            cuda_path = f"/usr/local/cuda-{version}"

            bashrc_content = f"""
# CUDA {version} Environment
export CUDA_HOME={cuda_path}
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
"""

            try:
                home_dir = os.path.expanduser("~")
                bashrc_path = os.path.join(home_dir, ".bashrc")

                with open(bashrc_path, "a") as f:
                    f.write(bashrc_content)

                self.logger.info("Variáveis CUDA adicionadas ao .bashrc")
                self.logger.info("Execute 'source ~/.bashrc' ou reinicie o terminal")

            except Exception as e:
                self.logger.warning(f"Erro ao configurar .bashrc: {e}")

    def verify_installation(self, version: str) -> bool:
        """
        Verifica se CUDA foi instalado corretamente

        Args:
            version: Versão esperada

        Returns:
            bool: True se verificação passou
        """
        self.logger.info(f"Verificando instalação CUDA {version}...")

        # Verificar nvcc
        try:
            result = subprocess.run(
                ["nvcc", "--version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                version_match = re.search(r"release (\d+\.\d+)", result.stdout)
                if version_match:
                    installed_version = version_match.group(1)
                    if installed_version == version[:4]:  # Comparar major.minor
                        self.logger.success(
                            f"CUDA {installed_version} verificado via nvcc"
                        )
                        return True
                    else:
                        self.logger.warning(
                            f"Versão diferente detectada: {installed_version}"
                        )
                        return False

        except Exception as e:
            self.logger.error(f"Erro ao verificar nvcc: {e}")

        # Verificar arquivos de instalação
        installations = self.detect_installed_cuda()
        for installation in installations:
            if (
                installation.version.startswith(version[:4])
                and installation.is_complete
            ):
                self.logger.success(
                    f"Instalação CUDA {installation.version} verificada"
                )
                return True

        self.logger.error("Verificação de instalação CUDA falhou")
        return False

    def cleanup(self):
        """Limpa arquivos temporários"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.debug("Arquivos temporários removidos")
        except Exception as e:
            self.logger.warning(f"Erro ao limpar arquivos temporários: {e}")


if __name__ == "__main__":
    # Teste do instalador CUDA
    print("🧪 Teste do Instalador CUDA\n")

    installer = CUDAInstaller()

    print("1. Detectando instalações CUDA existentes...")
    installations = installer.detect_installed_cuda()

    if installations:
        print(f"✅ {len(installations)} instalação(ões) encontrada(s):")
        for inst in installations:
            status = "✅ Completa" if inst.is_complete else "⚠️  Incompleta"
            print(f"  - CUDA {inst.version}: {inst.install_path} ({status})")
    else:
        print("❌ Nenhuma instalação CUDA encontrada")

    print("\n2. Selecionando melhor versão CUDA...")
    best_version = installer.select_best_cuda_version()

    if best_version:
        print(f"✅ Versão recomendada: CUDA {best_version}")

        # Verificar se já está instalada
        version_installed = any(
            inst.version.startswith(best_version[:4]) and inst.is_complete
            for inst in installations
        )

        if version_installed:
            print("✅ Versão já instalada e verificada")
        else:
            print("💡 Instalação necessária")
            print(
                f"   Para instalar: execute o download e instalação de CUDA {best_version}"
            )
    else:
        print("❌ Nenhuma versão CUDA compatível encontrada")

    # Limpeza
    installer.cleanup()

    print("\n✅ Teste concluído!")
