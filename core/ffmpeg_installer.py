"""
Instalador Automático do FFmpeg
Gerencia a instalação e verificação do FFmpeg no sistema
"""

import os
import sys
import subprocess
import requests
import zipfile
import shutil
from pathlib import Path


class FFmpegInstaller:
    """
    Classe responsável pela instalação automática do FFmpeg
    Detecta o sistema operacional e instala a versão apropriada
    """
    
    def __init__(self):
        self.system = sys.platform
        self.ffmpeg_dir = self.get_ffmpeg_directory()
        self.ffmpeg_executable = self.get_ffmpeg_executable_path()
    
    def get_ffmpeg_directory(self):
        """
        Retorna o diretório onde o FFmpeg será instalado
        """
        if self.system.startswith('win'):
            return Path.home() / "AppData" / "Local" / "FFmpeg"
        elif self.system.startswith('darwin'):  # macOS
            return Path.home() / "Applications" / "FFmpeg"
        else:  # Linux
            return Path.home() / ".local" / "bin" / "ffmpeg"
    
    def get_ffmpeg_executable_path(self):
        """
        Retorna o caminho completo para o executável do FFmpeg
        """
        if self.system.startswith('win'):
            return self.ffmpeg_dir / "bin" / "ffmpeg.exe"
        else:
            return self.ffmpeg_dir / "ffmpeg"
    
    def is_ffmpeg_installed(self):
        """
        Verifica se o FFmpeg está instalado e acessível
        Primeiro verifica no PATH do sistema, depois na instalação local
        """
        # Verificar no PATH do sistema
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Verificar na instalação local
        if self.ffmpeg_executable.exists():
            try:
                result = subprocess.run([str(self.ffmpeg_executable), '-version'], 
                                      capture_output=True, text=True, timeout=10)
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        return False
    
    def get_download_url(self):
        """
        Retorna a URL de download do FFmpeg para o sistema atual
        """
        if self.system.startswith('win'):
            # Windows - usar build estático do gyan.dev
            return "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        elif self.system.startswith('darwin'):  # macOS
            # macOS - usar build estático
            return "https://evermeet.cx/ffmpeg/ffmpeg-5.1.2.zip"
        else:  # Linux
            # Linux - usar build estático do johnvansickle
            return "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    
    def download_ffmpeg(self, progress_callback=None):
        """
        Baixa o FFmpeg da internet
        
        Args:
            progress_callback: Função callback para reportar progresso do download
        """
        url = self.get_download_url()
        
        # Criar diretório de destino
        self.ffmpeg_dir.mkdir(parents=True, exist_ok=True)
        
        # Determinar nome do arquivo
        if self.system.startswith('win'):
            filename = "ffmpeg-release-essentials.zip"
        elif self.system.startswith('darwin'):
            filename = "ffmpeg-5.1.2.zip"
        else:
            filename = "ffmpeg-release-amd64-static.tar.xz"
        
        file_path = self.ffmpeg_dir / filename
        
        # Baixar arquivo
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        progress_callback(progress)
        
        return file_path
    
    def extract_ffmpeg(self, archive_path):
        """
        Extrai o arquivo baixado do FFmpeg
        
        Args:
            archive_path: Caminho para o arquivo compactado
        """
        if self.system.startswith('win') or self.system.startswith('darwin'):
            # Extrair ZIP
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(self.ffmpeg_dir)
            
            # Mover arquivos para estrutura correta (Windows)
            if self.system.startswith('win'):
                # Encontrar pasta extraída
                extracted_folders = [f for f in self.ffmpeg_dir.iterdir() 
                                   if f.is_dir() and 'ffmpeg' in f.name.lower()]
                
                if extracted_folders:
                    extracted_folder = extracted_folders[0]
                    bin_folder = extracted_folder / "bin"
                    
                    if bin_folder.exists():
                        # Criar pasta bin no diretório principal
                        target_bin = self.ffmpeg_dir / "bin"
                        target_bin.mkdir(exist_ok=True)
                        
                        # Mover executáveis
                        for exe_file in bin_folder.glob("*.exe"):
                            shutil.move(str(exe_file), str(target_bin / exe_file.name))
                        
                        # Remover pasta temporária
                        shutil.rmtree(extracted_folder)
        
        else:  # Linux
            # Extrair TAR.XZ
            import tarfile
            with tarfile.open(archive_path, 'r:xz') as tar_ref:
                tar_ref.extractall(self.ffmpeg_dir)
            
            # Encontrar e mover executável
            for root, dirs, files in os.walk(self.ffmpeg_dir):
                if 'ffmpeg' in files:
                    source_ffmpeg = Path(root) / 'ffmpeg'
                    shutil.move(str(source_ffmpeg), str(self.ffmpeg_executable))
                    break
        
        # Remover arquivo compactado
        archive_path.unlink()
    
    def add_to_path(self):
        """
        Adiciona o FFmpeg ao PATH do sistema (Windows)
        """
        if self.system.startswith('win'):
            bin_path = str(self.ffmpeg_dir / "bin")
            
            # Verificar se já está no PATH
            current_path = os.environ.get('PATH', '')
            if bin_path not in current_path:
                # Adicionar ao PATH da sessão atual
                os.environ['PATH'] = f"{bin_path};{current_path}"
                
                # Tentar adicionar permanentemente (requer privilégios)
                try:
                    subprocess.run([
                        'setx', 'PATH', f"{bin_path};%PATH%"
                    ], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    # Falha silenciosa - PATH da sessão ainda funciona
                    pass
    
    def install_ffmpeg(self, progress_callback=None):
        """
        Instala o FFmpeg automaticamente
        
        Args:
            progress_callback: Função callback para reportar progresso
        
        Returns:
            bool: True se instalação foi bem-sucedida
        """
        try:
            # Verificar se já está instalado
            if self.is_ffmpeg_installed():
                return True
            
            # Baixar FFmpeg
            if progress_callback:
                progress_callback("Baixando FFmpeg...", 0)
            
            archive_path = self.download_ffmpeg(
                lambda p: progress_callback("Baixando FFmpeg...", p) if progress_callback else None
            )
            
            # Extrair arquivos
            if progress_callback:
                progress_callback("Extraindo arquivos...", 90)
            
            self.extract_ffmpeg(archive_path)
            
            # Adicionar ao PATH (Windows)
            if self.system.startswith('win'):
                self.add_to_path()
            
            # Verificar instalação
            if progress_callback:
                progress_callback("Verificando instalação...", 95)
            
            success = self.is_ffmpeg_installed()
            
            if progress_callback:
                if success:
                    progress_callback("Instalação concluída!", 100)
                else:
                    progress_callback("Erro na instalação", 100)
            
            return success
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Erro: {str(e)}", 100)
            return False
    
    def get_ffmpeg_command(self):
        """
        Retorna o comando correto para executar o FFmpeg
        Verifica primeiro na raiz do projeto, depois no PATH e instalação local
        """
        # Verificar primeiro na raiz do projeto (diretório atual)
        project_ffmpeg = Path.cwd() / "ffmpeg.exe" if self.system.startswith('win') else Path.cwd() / "ffmpeg"
        if project_ffmpeg.exists():
            try:
                result = subprocess.run([str(project_ffmpeg), '-version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    return str(project_ffmpeg)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        if self.is_ffmpeg_installed():
            # Tentar usar FFmpeg do PATH primeiro
            try:
                subprocess.run(['ffmpeg', '-version'], 
                             capture_output=True, timeout=5)
                return 'ffmpeg'
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Usar instalação local
            if self.ffmpeg_executable.exists():
                return str(self.ffmpeg_executable)
        
        return None