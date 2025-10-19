"""
🎬 Gerenciador FFmpeg/FFprobe - VideoConverter Installer
======================================================

Gerenciador inteligente de FFmpeg com:
- Download automático da versão mais recente
- Instalação por OS (Windows/Linux/macOS)
- Configuração automática de PATH
- Verificação de integridade
- Suporte a builds estáticos e dinâmicos
- Detecção de instalações existentes
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
import zipfile
import tarfile
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import platform
import json
import re
import requests

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
class FFmpegBuild:
    """Informações de build FFmpeg"""

    version: str
    build_type: str  # "static", "shared", "gpl", "lgpl"
    architecture: str  # "x64", "x86", "arm64"
    os_type: str  # "windows", "linux", "macos"
    download_url: str
    file_size: Optional[int]
    checksum: Optional[str]
    features: List[str]  # Codecs e features incluídos
    release_date: str


@dataclass
class FFmpegInstallation:
    """Informações de instalação FFmpeg"""

    version: str
    install_path: str
    ffmpeg_path: str
    ffprobe_path: str
    ffplay_path: Optional[str]
    is_complete: bool
    build_info: Dict[str, Any]
    installation_date: str


class FFmpegManager:
    """
    Gerenciador automático de FFmpeg/FFprobe

    Funcionalidades:
    - Detecção de instalações existentes
    - Download automático da versão mais recente
    - Instalação por OS
    - Configuração de PATH
    - Verificação de funcionalidade
    """

    # URLs para download FFmpeg
    FFMPEG_URLS = {
        "windows": {
            "base": "https://www.gyan.dev/ffmpeg/builds/",
            "releases": "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest",
            "static": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
        },
        "linux": {
            "base": "https://johnvansickle.com/ffmpeg/",
            "releases": "https://johnvansickle.com/ffmpeg/releases/",
            "static": "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz",
        },
        "macos": {
            "base": "https://evermeet.cx/ffmpeg/",
            "releases": "https://evermeet.cx/ffmpeg/info/ffmpeg/release",
            "static": "https://evermeet.cx/ffmpeg/getrelease/zip",
        },
    }

    # Codecs e features essenciais
    ESSENTIAL_CODECS = [
        "libx264",
        "libx265",
        "libvpx",
        "libvpx-vp9",
        "aac",
        "mp3",
        "opus",
        "vorbis",
        "h264",
        "hevc",
        "vp8",
        "vp9",
        "av1",
    ]

    def __init__(self, cache_dir: str = None, install_dir: str = None):
        """
        Inicializa gerenciador FFmpeg

        Args:
            cache_dir: Diretório de cache para downloads
            install_dir: Diretório de instalação personalizado
        """
        self.logger = Logger("FFmpegManager")
        self.os_detector = OSDetector()
        self.downloader = SmartDownloader(cache_dir=cache_dir)

        # Informações do sistema
        self.os_info = self.os_detector.detect()
        self.os_type = self.os_info.name.lower()
        self.architecture = self.os_info.architecture

        # Diretórios
        self.temp_dir = tempfile.mkdtemp(prefix="ffmpeg_install_")
        self.install_dir = install_dir or self._get_default_install_dir()

        self.logger.info(
            f"Gerenciador FFmpeg inicializado para {self.os_type} {self.architecture}"
        )

    def _get_default_install_dir(self) -> str:
        """
        Retorna diretório padrão de instalação

        Returns:
            str: Caminho do diretório
        """
        if self.os_type == "windows":
            return os.path.join(
                os.environ.get("PROGRAMFILES", "C:\\Program Files"), "FFmpeg"
            )
        elif self.os_type == "linux":
            return "/usr/local/bin"
        else:  # macOS
            return "/usr/local/bin"

    def detect_installed_ffmpeg(self) -> List[FFmpegInstallation]:
        """
        Detecta instalações FFmpeg existentes

        Returns:
            List[FFmpegInstallation]: Lista de instalações encontradas
        """
        installations = []

        # Verificar no PATH
        path_installation = self._detect_ffmpeg_in_path()
        if path_installation:
            installations.append(path_installation)

        # Verificar diretórios comuns
        common_dirs = self._get_common_ffmpeg_dirs()
        for directory in common_dirs:
            installation = self._check_ffmpeg_in_directory(directory)
            if installation and installation not in installations:
                installations.append(installation)

        # Verificar package managers (Linux)
        if self.os_type == "linux":
            package_installation = self._detect_ffmpeg_packages()
            if package_installation and package_installation not in installations:
                installations.append(package_installation)

        self.logger.info(f"Encontradas {len(installations)} instalação(ões) FFmpeg")
        return installations

    def _detect_ffmpeg_in_path(self) -> Optional[FFmpegInstallation]:
        """Detecta FFmpeg no PATH do sistema"""
        try:
            # Verificar ffmpeg
            ffmpeg_path = shutil.which("ffmpeg")
            ffprobe_path = shutil.which("ffprobe")
            ffplay_path = shutil.which("ffplay")

            if ffmpeg_path and ffprobe_path:
                # Obter versão
                version = self._get_ffmpeg_version(ffmpeg_path)
                build_info = self._get_ffmpeg_build_info(ffmpeg_path)

                installation = FFmpegInstallation(
                    version=version,
                    install_path=str(Path(ffmpeg_path).parent),
                    ffmpeg_path=ffmpeg_path,
                    ffprobe_path=ffprobe_path,
                    ffplay_path=ffplay_path,
                    is_complete=True,
                    build_info=build_info,
                    installation_date="Unknown",
                )

                self.logger.info(f"FFmpeg {version} encontrado no PATH")
                return installation

        except Exception as e:
            self.logger.debug(f"Erro ao detectar FFmpeg no PATH: {e}")

        return None

    def _get_common_ffmpeg_dirs(self) -> List[str]:
        """Retorna diretórios comuns onde FFmpeg pode estar instalado"""
        dirs = []

        if self.os_type == "windows":
            dirs.extend(
                [
                    "C:\\ffmpeg\\bin",
                    "C:\\Program Files\\FFmpeg\\bin",
                    "C:\\Program Files (x86)\\FFmpeg\\bin",
                    os.path.join(os.environ.get("USERPROFILE", ""), "ffmpeg", "bin"),
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), "ffmpeg", "bin"),
                ]
            )
        elif self.os_type == "linux":
            dirs.extend(
                [
                    "/usr/bin",
                    "/usr/local/bin",
                    "/opt/ffmpeg/bin",
                    "/snap/bin",
                    os.path.join(os.environ.get("HOME", ""), ".local", "bin"),
                ]
            )
        else:  # macOS
            dirs.extend(
                [
                    "/usr/local/bin",
                    "/opt/homebrew/bin",
                    "/usr/bin",
                    "/Applications/FFmpeg",
                ]
            )

        # Filtrar diretórios que existem
        return [d for d in dirs if os.path.exists(d)]

    def _check_ffmpeg_in_directory(
        self, directory: str
    ) -> Optional[FFmpegInstallation]:
        """Verifica se FFmpeg está em um diretório específico"""
        try:
            path = Path(directory)

            # Procurar executáveis
            ffmpeg_exe = "ffmpeg.exe" if self.os_type == "windows" else "ffmpeg"
            ffprobe_exe = "ffprobe.exe" if self.os_type == "windows" else "ffprobe"
            ffplay_exe = "ffplay.exe" if self.os_type == "windows" else "ffplay"

            ffmpeg_path = path / ffmpeg_exe
            ffprobe_path = path / ffprobe_exe
            ffplay_path = path / ffplay_exe

            if ffmpeg_path.exists() and ffprobe_path.exists():
                # Obter informações
                version = self._get_ffmpeg_version(str(ffmpeg_path))
                build_info = self._get_ffmpeg_build_info(str(ffmpeg_path))

                installation = FFmpegInstallation(
                    version=version,
                    install_path=directory,
                    ffmpeg_path=str(ffmpeg_path),
                    ffprobe_path=str(ffprobe_path),
                    ffplay_path=str(ffplay_path) if ffplay_path.exists() else None,
                    is_complete=True,
                    build_info=build_info,
                    installation_date="Unknown",
                )

                return installation

        except Exception as e:
            self.logger.debug(f"Erro ao verificar {directory}: {e}")

        return None

    def _detect_ffmpeg_packages(self) -> Optional[FFmpegInstallation]:
        """Detecta FFmpeg via package managers (Linux)"""
        try:
            # Verificar via dpkg (Debian/Ubuntu)
            result = subprocess.run(
                ["dpkg", "-l", "ffmpeg"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and "ii" in result.stdout:
                # FFmpeg instalado via apt
                ffmpeg_path = "/usr/bin/ffmpeg"
                ffprobe_path = "/usr/bin/ffprobe"

                if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
                    version = self._get_ffmpeg_version(ffmpeg_path)
                    build_info = self._get_ffmpeg_build_info(ffmpeg_path)

                    return FFmpegInstallation(
                        version=version,
                        install_path="/usr/bin",
                        ffmpeg_path=ffmpeg_path,
                        ffprobe_path=ffprobe_path,
                        ffplay_path=(
                            "/usr/bin/ffplay"
                            if os.path.exists("/usr/bin/ffplay")
                            else None
                        ),
                        is_complete=True,
                        build_info=build_info,
                        installation_date="Unknown",
                    )

        except Exception:
            pass

        try:
            # Verificar via rpm (RedHat/CentOS)
            result = subprocess.run(
                ["rpm", "-q", "ffmpeg"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                # FFmpeg instalado via yum/dnf
                ffmpeg_path = "/usr/bin/ffmpeg"
                ffprobe_path = "/usr/bin/ffprobe"

                if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
                    version = self._get_ffmpeg_version(ffmpeg_path)
                    build_info = self._get_ffmpeg_build_info(ffmpeg_path)

                    return FFmpegInstallation(
                        version=version,
                        install_path="/usr/bin",
                        ffmpeg_path=ffmpeg_path,
                        ffprobe_path=ffprobe_path,
                        ffplay_path=(
                            "/usr/bin/ffplay"
                            if os.path.exists("/usr/bin/ffplay")
                            else None
                        ),
                        is_complete=True,
                        build_info=build_info,
                        installation_date="Unknown",
                    )

        except Exception:
            pass

        return None

    def _get_ffmpeg_version(self, ffmpeg_path: str) -> str:
        """
        Obtém versão do FFmpeg

        Args:
            ffmpeg_path: Caminho do executável FFmpeg

        Returns:
            str: Versão do FFmpeg
        """
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                # Procurar versão na primeira linha
                first_line = result.stdout.split("\n")[0]
                version_match = re.search(r"ffmpeg version (\S+)", first_line)
                if version_match:
                    return version_match.group(1)

        except Exception:
            pass

        return "Unknown"

    def _get_ffmpeg_build_info(self, ffmpeg_path: str) -> Dict[str, Any]:
        """
        Obtém informações de build do FFmpeg

        Args:
            ffmpeg_path: Caminho do executável FFmpeg

        Returns:
            Dict[str, Any]: Informações de build
        """
        build_info = {
            "configuration": "",
            "codecs": [],
            "formats": [],
            "protocols": [],
            "build_type": "unknown",
        }

        try:
            # Obter configuração de build
            result = subprocess.run(
                [ffmpeg_path, "-version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                output = result.stdout

                # Extrair configuração
                config_match = re.search(r"configuration: (.+)", output)
                if config_match:
                    build_info["configuration"] = config_match.group(1)

                # Determinar tipo de build
                if "--enable-static" in build_info["configuration"]:
                    build_info["build_type"] = "static"
                elif "--enable-shared" in build_info["configuration"]:
                    build_info["build_type"] = "shared"

                # Verificar codecs essenciais
                for codec in self.ESSENTIAL_CODECS:
                    if codec in build_info["configuration"]:
                        build_info["codecs"].append(codec)

            # Obter lista de codecs
            result = subprocess.run(
                [ffmpeg_path, "-codecs"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                # Contar codecs disponíveis
                codec_lines = [
                    line
                    for line in result.stdout.split("\n")
                    if line.strip() and not line.startswith(" ")
                ]
                build_info["total_codecs"] = len(codec_lines) - 2  # Remover header

        except Exception as e:
            self.logger.debug(f"Erro ao obter build info: {e}")

        return build_info

    def get_latest_ffmpeg_info(self) -> Optional[FFmpegBuild]:
        """
        Obtém informações da versão mais recente do FFmpeg

        Returns:
            Optional[FFmpegBuild]: Informações da versão mais recente
        """
        self.logger.info("Obtendo informações da versão mais recente do FFmpeg...")

        try:
            if self.os_type == "windows":
                return self._get_latest_windows_build()
            elif self.os_type == "linux":
                return self._get_latest_linux_build()
            else:  # macOS
                return self._get_latest_macos_build()

        except Exception as e:
            self.logger.error(f"Erro ao obter informações da versão mais recente: {e}")
            return None

    def _get_latest_windows_build(self) -> Optional[FFmpegBuild]:
        """Obtém build mais recente para Windows"""
        try:
            # Usar API do GitHub para builds BtbN (mais confiável)
            response = requests.get(self.FFMPEG_URLS["windows"]["releases"], timeout=30)

            if response.status_code == 200:
                release_data = response.json()

                # Procurar asset para Windows x64
                for asset in release_data.get("assets", []):
                    name = asset["name"].lower()
                    if "win64" in name and "gpl" in name and name.endswith(".zip"):
                        return FFmpegBuild(
                            version=release_data["tag_name"],
                            build_type="static",
                            architecture="x64",
                            os_type="windows",
                            download_url=asset["browser_download_url"],
                            file_size=asset["size"],
                            checksum=None,  # GitHub não fornece checksum
                            features=self.ESSENTIAL_CODECS,
                            release_date=release_data["published_at"],
                        )

            # Fallback: URL estática
            return FFmpegBuild(
                version="latest",
                build_type="static",
                architecture="x64",
                os_type="windows",
                download_url=self.FFMPEG_URLS["windows"]["static"],
                file_size=None,
                checksum=None,
                features=self.ESSENTIAL_CODECS,
                release_date="unknown",
            )

        except Exception as e:
            self.logger.error(f"Erro ao obter build Windows: {e}")
            return None

    def _get_latest_linux_build(self) -> Optional[FFmpegBuild]:
        """Obtém build mais recente para Linux"""
        try:
            # John Van Sickle builds (estáticos para Linux)
            return FFmpegBuild(
                version="latest",
                build_type="static",
                architecture="x64",
                os_type="linux",
                download_url=self.FFMPEG_URLS["linux"]["static"],
                file_size=None,
                checksum=None,
                features=self.ESSENTIAL_CODECS,
                release_date="unknown",
            )

        except Exception as e:
            self.logger.error(f"Erro ao obter build Linux: {e}")
            return None

    def _get_latest_macos_build(self) -> Optional[FFmpegBuild]:
        """Obtém build mais recente para macOS"""
        try:
            # Evermeet builds para macOS
            return FFmpegBuild(
                version="latest",
                build_type="static",
                architecture="x64",
                os_type="macos",
                download_url=self.FFMPEG_URLS["macos"]["static"],
                file_size=None,
                checksum=None,
                features=self.ESSENTIAL_CODECS,
                release_date="unknown",
            )

        except Exception as e:
            self.logger.error(f"Erro ao obter build macOS: {e}")
            return None

    def download_ffmpeg(
        self, build: FFmpegBuild, destination_dir: str = None
    ) -> Optional[str]:
        """
        Baixa FFmpeg

        Args:
            build: Informações do build
            destination_dir: Diretório de destino

        Returns:
            Optional[str]: Caminho do arquivo baixado
        """
        if destination_dir is None:
            destination_dir = self.temp_dir

        # Preparar informações de download
        filename = f"ffmpeg-{build.version}-{build.os_type}-{build.architecture}"
        if build.download_url.endswith(".zip"):
            filename += ".zip"
        elif build.download_url.endswith(".tar.xz"):
            filename += ".tar.xz"
        else:
            filename += ".archive"

        download_info = DownloadInfo(
            url=build.download_url,
            filename=filename,
            size=build.file_size,
            sha256=build.checksum,
        )

        self.logger.info(f"Baixando FFmpeg {build.version} para {build.os_type}...")

        # Progress bar
        progress_bar = None
        if download_info.size:
            progress_bar = ProgressBar(
                total=download_info.size,
                description=f"Baixando FFmpeg {build.version}",
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
            self.logger.success(f"FFmpeg {build.version} baixado: {result.filepath}")
            return result.filepath
        else:
            self.logger.error(f"Falha no download: {result.error}")
            return None

    def install_ffmpeg(self, archive_path: str, build: FFmpegBuild) -> bool:
        """
        Instala FFmpeg

        Args:
            archive_path: Caminho do arquivo baixado
            build: Informações do build

        Returns:
            bool: True se instalação bem-sucedida
        """
        self.logger.info(f"Iniciando instalação FFmpeg {build.version}...")

        # Progress bar para instalação
        install_steps = 6
        progress_bar = installation_progress_bar(
            install_steps, f"FFmpeg {build.version}"
        )

        try:
            # Passo 1: Extrair arquivo
            progress_bar.update(1, description="Extraindo arquivo")

            extract_dir = os.path.join(self.temp_dir, "ffmpeg_extract")
            os.makedirs(extract_dir, exist_ok=True)

            if archive_path.endswith(".zip"):
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif archive_path.endswith((".tar.xz", ".tar.gz")):
                with tarfile.open(archive_path, "r:*") as tar_ref:
                    tar_ref.extractall(extract_dir)
            else:
                self.logger.error("Formato de arquivo não suportado")
                progress_bar.cancel("Formato não suportado")
                return False

            # Passo 2: Encontrar executáveis
            progress_bar.update(2, description="Localizando executáveis")

            ffmpeg_exe = None
            ffprobe_exe = None
            ffplay_exe = None

            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().startswith("ffmpeg"):
                        if self.os_type == "windows" and file.endswith(".exe"):
                            ffmpeg_exe = os.path.join(root, file)
                        elif self.os_type != "windows" and not "." in file:
                            ffmpeg_exe = os.path.join(root, file)

                    elif file.lower().startswith("ffprobe"):
                        if self.os_type == "windows" and file.endswith(".exe"):
                            ffprobe_exe = os.path.join(root, file)
                        elif self.os_type != "windows" and not "." in file:
                            ffprobe_exe = os.path.join(root, file)

                    elif file.lower().startswith("ffplay"):
                        if self.os_type == "windows" and file.endswith(".exe"):
                            ffplay_exe = os.path.join(root, file)
                        elif self.os_type != "windows" and not "." in file:
                            ffplay_exe = os.path.join(root, file)

            if not ffmpeg_exe or not ffprobe_exe:
                self.logger.error("Executáveis FFmpeg não encontrados no arquivo")
                progress_bar.cancel("Executáveis não encontrados")
                return False

            # Passo 3: Criar diretório de instalação
            progress_bar.update(3, description="Criando diretório de instalação")

            os.makedirs(self.install_dir, exist_ok=True)

            # Passo 4: Copiar executáveis
            progress_bar.update(4, description="Copiando executáveis")

            # Nomes finais dos executáveis
            final_ffmpeg = os.path.join(
                self.install_dir,
                "ffmpeg" + (".exe" if self.os_type == "windows" else ""),
            )
            final_ffprobe = os.path.join(
                self.install_dir,
                "ffprobe" + (".exe" if self.os_type == "windows" else ""),
            )
            final_ffplay = os.path.join(
                self.install_dir,
                "ffplay" + (".exe" if self.os_type == "windows" else ""),
            )

            # Copiar arquivos
            shutil.copy2(ffmpeg_exe, final_ffmpeg)
            shutil.copy2(ffprobe_exe, final_ffprobe)

            if ffplay_exe:
                shutil.copy2(ffplay_exe, final_ffplay)

            # Tornar executáveis (Linux/macOS)
            if self.os_type != "windows":
                os.chmod(final_ffmpeg, 0o755)
                os.chmod(final_ffprobe, 0o755)
                if ffplay_exe:
                    os.chmod(final_ffplay, 0o755)

            # Passo 5: Configurar PATH
            progress_bar.update(5, description="Configurando PATH")

            self._configure_ffmpeg_path()

            # Passo 6: Verificar instalação
            progress_bar.update(6, description="Verificando instalação")

            if self._verify_ffmpeg_installation(final_ffmpeg, final_ffprobe):
                progress_bar.finish("Instalação FFmpeg concluída")
                self.logger.success(f"FFmpeg {build.version} instalado com sucesso")
                return True
            else:
                progress_bar.cancel("Falha na verificação")
                return False

        except Exception as e:
            self.logger.error(f"Erro durante instalação: {e}")
            progress_bar.cancel(f"Erro: {e}")
            return False

    def _configure_ffmpeg_path(self):
        """Configura FFmpeg no PATH do sistema"""
        self.logger.info("Configurando FFmpeg no PATH...")

        if self.os_type == "windows":
            # Windows: Adicionar ao PATH do usuário
            try:
                import winreg

                # Abrir chave do registro para PATH do usuário
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
                )

                # Obter PATH atual
                try:
                    current_path, _ = winreg.QueryValueEx(key, "PATH")
                except FileNotFoundError:
                    current_path = ""

                # Adicionar diretório FFmpeg se não estiver presente
                if self.install_dir not in current_path:
                    new_path = (
                        f"{current_path};{self.install_dir}"
                        if current_path
                        else self.install_dir
                    )
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                    self.logger.info("FFmpeg adicionado ao PATH do usuário")

                winreg.CloseKey(key)

                # Notificar mudança de ambiente
                import ctypes

                ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")

            except Exception as e:
                self.logger.warning(f"Erro ao configurar PATH no Windows: {e}")
                self.logger.info(f"Adicione manualmente ao PATH: {self.install_dir}")

        else:
            # Linux/macOS: Adicionar ao .bashrc/.profile
            try:
                home_dir = os.path.expanduser("~")
                bashrc_path = os.path.join(home_dir, ".bashrc")

                # Verificar se já está configurado
                path_export = f'export PATH="{self.install_dir}:$PATH"'

                if os.path.exists(bashrc_path):
                    with open(bashrc_path, "r") as f:
                        content = f.read()

                    if self.install_dir not in content:
                        with open(bashrc_path, "a") as f:
                            f.write(f"\n# FFmpeg\n{path_export}\n")

                        self.logger.info("FFmpeg adicionado ao .bashrc")
                        self.logger.info(
                            "Execute 'source ~/.bashrc' ou reinicie o terminal"
                        )
                else:
                    # Criar .bashrc se não existir
                    with open(bashrc_path, "w") as f:
                        f.write(f"# FFmpeg\n{path_export}\n")

                    self.logger.info(".bashrc criado com configuração FFmpeg")

            except Exception as e:
                self.logger.warning(f"Erro ao configurar PATH: {e}")
                self.logger.info(f"Adicione manualmente ao PATH: {self.install_dir}")

    def _verify_ffmpeg_installation(self, ffmpeg_path: str, ffprobe_path: str) -> bool:
        """
        Verifica se instalação FFmpeg está funcional

        Args:
            ffmpeg_path: Caminho do FFmpeg
            ffprobe_path: Caminho do FFprobe

        Returns:
            bool: True se verificação passou
        """
        try:
            # Verificar FFmpeg
            result = subprocess.run(
                [ffmpeg_path, "-version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                self.logger.error("FFmpeg não está funcionando")
                return False

            # Verificar FFprobe
            result = subprocess.run(
                [ffprobe_path, "-version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                self.logger.error("FFprobe não está funcionando")
                return False

            # Verificar codecs essenciais
            result = subprocess.run(
                [ffmpeg_path, "-codecs"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                codecs_output = result.stdout.lower()
                missing_codecs = []

                for codec in ["h264", "aac", "mp3"]:  # Codecs mais essenciais
                    if codec not in codecs_output:
                        missing_codecs.append(codec)

                if missing_codecs:
                    self.logger.warning(f"Codecs ausentes: {missing_codecs}")
                    # Não falhar por codecs ausentes, apenas avisar

            self.logger.success("Verificação FFmpeg passou")
            return True

        except Exception as e:
            self.logger.error(f"Erro na verificação: {e}")
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
    # Teste do gerenciador FFmpeg
    print("🧪 Teste do Gerenciador FFmpeg\n")

    manager = FFmpegManager()

    print("1. Detectando instalações FFmpeg existentes...")
    installations = manager.detect_installed_ffmpeg()

    if installations:
        print(f"✅ {len(installations)} instalação(ões) encontrada(s):")
        for inst in installations:
            status = "✅ Completa" if inst.is_complete else "⚠️  Incompleta"
            print(f"  - FFmpeg {inst.version}: {inst.install_path} ({status})")
            print(f"    Codecs: {len(inst.build_info.get('codecs', []))}")
    else:
        print("❌ Nenhuma instalação FFmpeg encontrada")

    print("\n2. Obtendo informações da versão mais recente...")
    latest_build = manager.get_latest_ffmpeg_info()

    if latest_build:
        print(f"✅ Versão mais recente: {latest_build.version}")
        print(f"   Tipo: {latest_build.build_type}")
        print(f"   Arquitetura: {latest_build.architecture}")
        print(f"   URL: {latest_build.download_url}")

        # Verificar se instalação é necessária
        needs_install = True
        if installations:
            for inst in installations:
                if inst.is_complete and "latest" in inst.version:
                    needs_install = False
                    break

        if needs_install:
            print("💡 Instalação/atualização recomendada")
        else:
            print("✅ FFmpeg atualizado já instalado")
    else:
        print("❌ Não foi possível obter informações da versão mais recente")

    # Limpeza
    manager.cleanup()

    print("\n✅ Teste concluído!")
