"""
🐍 Gerenciador de Python 3.13 - VideoConverter Installer
========================================================

Funcionalidades:
- Verificação de versão Python atual
- Download automático Python 3.13 do python.org
- Instalação silenciosa por sistema operacional
- Configuração de PATH e variáveis de ambiente
- Validação de instalação funcional
- Suporte a instalação offline com cache
"""

import sys
import os
import subprocess
import urllib.request
import urllib.parse
import json
import hashlib
import tempfile
import shutil
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from dataclasses import dataclass

from .os_detector import OSDetector, OSInfo


@dataclass
class PythonInfo:
    """Informações da instalação Python"""
    version: str                 # 3.13.0
    executable: str             # Caminho do executável
    is_64bit: bool              # True se 64-bit
    has_pip: bool               # True se pip disponível
    has_venv: bool              # True se venv disponível
    installation_path: str      # Diretório de instalação
    is_compatible: bool         # Compatível com VideoConverter


class PythonManager:
    """
    Gerenciador completo de Python 3.13
    
    Funcionalidades:
    - Detecção de Python atual
    - Download e instalação Python 3.13
    - Configuração de ambiente
    - Validação de funcionalidade
    - Cache offline
    """
    
    # URLs oficiais Python 3.13
    PYTHON_URLS = {
        "windows": {
            "x64": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe",
            "x86": "https://www.python.org/ftp/python/3.13.0/python-3.13.0.exe",
            "arm64": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-arm64.exe"
        },
        "linux": {
            "x64": "https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz",
            "arm64": "https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz"
        },
        "darwin": {
            "x64": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-macos11.pkg",
            "arm64": "https://www.python.org/ftp/python/3.13.0/python-3.13.0-macos11.pkg"
        }
    }
    
    # Checksums para verificação
    PYTHON_CHECKSUMS = {
        "python-3.13.0-amd64.exe": "a1234567890abcdef...",  # Placeholder
        "python-3.13.0.exe": "b1234567890abcdef...",
        "Python-3.13.0.tgz": "c1234567890abcdef...",
        "python-3.13.0-macos11.pkg": "d1234567890abcdef..."
    }
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Inicializa o gerenciador Python
        
        Args:
            cache_dir: Diretório para cache offline (opcional)
        """
        self.os_detector = OSDetector()
        self.os_info = self.os_detector.detect()
        
        # Configurar diretório de cache
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".vidconv_installer" / "cache"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_python: Optional[PythonInfo] = None
    
    def get_current_python(self) -> Optional[PythonInfo]:
        """
        Obtém informações do Python atual
        
        Returns:
            PythonInfo: Informações do Python ou None se não encontrado
        """
        if self._current_python is None:
            self._current_python = self._detect_current_python()
        
        return self._current_python
    
    def _detect_current_python(self) -> Optional[PythonInfo]:
        """Detecta Python atual no sistema"""
        try:
            # Informações básicas
            version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            executable = sys.executable
            is_64bit = sys.maxsize > 2**32
            
            # Verificar pip
            has_pip = self._check_pip_available()
            
            # Verificar venv
            has_venv = self._check_venv_available()
            
            # Diretório de instalação
            installation_path = str(Path(sys.executable).parent)
            
            # Verificar compatibilidade
            is_compatible = self._check_python_compatibility(version)
            
            return PythonInfo(
                version=version,
                executable=executable,
                is_64bit=is_64bit,
                has_pip=has_pip,
                has_venv=has_venv,
                installation_path=installation_path,
                is_compatible=is_compatible
            )
            
        except Exception as e:
            print(f"❌ Erro ao detectar Python: {e}")
            return None
    
    def _check_pip_available(self) -> bool:
        """Verifica se pip está disponível"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_venv_available(self) -> bool:
        """Verifica se venv está disponível"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "venv", "--help"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_python_compatibility(self, version: str) -> bool:
        """Verifica se a versão Python é compatível"""
        try:
            major, minor, patch = map(int, version.split('.'))
            
            # VideoConverter requer Python 3.8+
            if major == 3 and minor >= 8:
                return True
            
            return False
        except:
            return False
    
    def needs_python_install(self) -> bool:
        """
        Verifica se precisa instalar Python 3.13
        
        Returns:
            bool: True se precisa instalar
        """
        current = self.get_current_python()
        
        if not current:
            return True
        
        # Verificar se é Python 3.13
        if not current.version.startswith("3.13"):
            return True
        
        # Verificar se tem pip e venv
        if not (current.has_pip and current.has_venv):
            return True
        
        return False
    
    def get_download_url(self) -> Optional[str]:
        """
        Obtém URL de download para o sistema atual
        
        Returns:
            str: URL de download ou None se não suportado
        """
        os_urls = self.PYTHON_URLS.get(self.os_info.name)
        if not os_urls:
            return None
        
        return os_urls.get(self.os_info.architecture)
    
    def download_python(self, progress_callback=None) -> Optional[str]:
        """
        Baixa Python 3.13 para o sistema atual
        
        Args:
            progress_callback: Função para callback de progresso
            
        Returns:
            str: Caminho do arquivo baixado ou None se erro
        """
        url = self.get_download_url()
        if not url:
            print(f"❌ Python 3.13 não disponível para {self.os_info.name} {self.os_info.architecture}")
            return None
        
        # Nome do arquivo
        filename = url.split('/')[-1]
        file_path = self.cache_dir / filename
        
        # Verificar se já existe no cache
        if file_path.exists():
            if self._verify_checksum(file_path, filename):
                print(f"✅ Python encontrado no cache: {file_path}")
                return str(file_path)
            else:
                print("⚠️ Arquivo no cache corrompido, baixando novamente...")
                file_path.unlink()
        
        print(f"📥 Baixando Python 3.13 de {url}...")
        
        try:
            # Download com progress
            def report_progress(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100, (downloaded * 100) // total_size)
                    progress_callback(percent, downloaded, total_size)
            
            urllib.request.urlretrieve(url, file_path, report_progress)
            
            # Verificar checksum
            if self._verify_checksum(file_path, filename):
                print(f"✅ Download concluído: {file_path}")
                return str(file_path)
            else:
                print("❌ Checksum inválido!")
                file_path.unlink()
                return None
                
        except Exception as e:
            print(f"❌ Erro no download: {e}")
            if file_path.exists():
                file_path.unlink()
            return None
    
    def _verify_checksum(self, file_path: Path, filename: str) -> bool:
        """Verifica checksum do arquivo"""
        expected_checksum = self.PYTHON_CHECKSUMS.get(filename)
        if not expected_checksum:
            print("⚠️ Checksum não disponível, pulando verificação")
            return True
        
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            return file_hash == expected_checksum
        except:
            return False
    
    def install_python(self, installer_path: str, custom_path: Optional[str] = None) -> bool:
        """
        Instala Python 3.13 no sistema
        
        Args:
            installer_path: Caminho do instalador baixado
            custom_path: Caminho customizado de instalação (opcional)
            
        Returns:
            bool: True se instalação bem-sucedida
        """
        if not os.path.exists(installer_path):
            print(f"❌ Instalador não encontrado: {installer_path}")
            return False
        
        print(f"🔧 Instalando Python 3.13...")
        
        if self.os_info.name == "windows":
            return self._install_python_windows(installer_path, custom_path)
        elif self.os_info.name == "linux":
            return self._install_python_linux(installer_path, custom_path)
        elif self.os_info.name == "darwin":
            return self._install_python_macos(installer_path, custom_path)
        else:
            print(f"❌ Instalação não suportada para {self.os_info.name}")
            return False
    
    def _install_python_windows(self, installer_path: str, custom_path: Optional[str]) -> bool:
        """Instala Python no Windows"""
        try:
            # Argumentos para instalação silenciosa
            args = [
                installer_path,
                "/quiet",                    # Instalação silenciosa
                "InstallAllUsers=1",         # Para todos os usuários
                "PrependPath=1",             # Adicionar ao PATH
                "Include_test=0",            # Não incluir testes
                "Include_doc=0",             # Não incluir documentação
                "Include_dev=1",             # Incluir headers para desenvolvimento
                "Include_pip=1",             # Incluir pip
                "Include_tcltk=1"            # Incluir Tkinter
            ]
            
            # Caminho customizado
            if custom_path:
                args.append(f"TargetDir={custom_path}")
            
            # Executar instalação
            result = subprocess.run(args, timeout=600)  # 10 minutos timeout
            
            if result.returncode == 0:
                print("✅ Python 3.13 instalado com sucesso!")
                return True
            else:
                print(f"❌ Erro na instalação (código: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"❌ Erro na instalação: {e}")
            return False
    
    def _install_python_linux(self, installer_path: str, custom_path: Optional[str]) -> bool:
        """Instala Python no Linux (compilação do source)"""
        try:
            # Extrair source
            extract_dir = self.cache_dir / "python_source"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            
            extract_dir.mkdir()
            
            # Extrair tar.gz
            result = subprocess.run([
                "tar", "-xzf", installer_path, "-C", str(extract_dir), "--strip-components=1"
            ], timeout=60)
            
            if result.returncode != 0:
                print("❌ Erro ao extrair source do Python")
                return False
            
            # Configurar build
            configure_args = ["./configure"]
            if custom_path:
                configure_args.append(f"--prefix={custom_path}")
            else:
                configure_args.append("--prefix=/usr/local")
            
            configure_args.extend([
                "--enable-optimizations",
                "--with-ensurepip=install"
            ])
            
            # Executar configure
            result = subprocess.run(
                configure_args,
                cwd=extract_dir,
                timeout=300
            )
            
            if result.returncode != 0:
                print("❌ Erro no configure")
                return False
            
            # Compilar
            print("🔨 Compilando Python (pode demorar alguns minutos)...")
            result = subprocess.run(
                ["make", "-j", str(os.cpu_count() or 4)],
                cwd=extract_dir,
                timeout=1800  # 30 minutos
            )
            
            if result.returncode != 0:
                print("❌ Erro na compilação")
                return False
            
            # Instalar
            result = subprocess.run(
                ["sudo", "make", "altinstall"],
                cwd=extract_dir,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ Python 3.13 compilado e instalado!")
                return True
            else:
                print("❌ Erro na instalação")
                return False
                
        except Exception as e:
            print(f"❌ Erro na instalação: {e}")
            return False
    
    def _install_python_macos(self, installer_path: str, custom_path: Optional[str]) -> bool:
        """Instala Python no macOS"""
        try:
            # Instalar .pkg
            args = ["sudo", "installer", "-pkg", installer_path, "-target", "/"]
            
            result = subprocess.run(args, timeout=600)
            
            if result.returncode == 0:
                print("✅ Python 3.13 instalado com sucesso!")
                return True
            else:
                print(f"❌ Erro na instalação (código: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"❌ Erro na instalação: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """
        Configura variáveis de ambiente para Python 3.13
        
        Returns:
            bool: True se configuração bem-sucedida
        """
        try:
            # Encontrar Python 3.13 instalado
            python_path = self._find_python_313()
            if not python_path:
                print("❌ Python 3.13 não encontrado após instalação")
                return False
            
            print(f"🔧 Configurando ambiente para {python_path}")
            
            if self.os_info.name == "windows":
                return self._configure_windows_environment(python_path)
            else:
                return self._configure_unix_environment(python_path)
                
        except Exception as e:
            print(f"❌ Erro na configuração: {e}")
            return False
    
    def _find_python_313(self) -> Optional[str]:
        """Encontra executável Python 3.13"""
        possible_names = ["python3.13", "python3", "python"]
        
        for name in possible_names:
            try:
                result = subprocess.run(
                    [name, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and "3.13" in result.stdout:
                    # Obter caminho completo
                    result = subprocess.run(
                        ["which" if self.os_info.name != "windows" else "where", name],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        return result.stdout.strip().split('\n')[0]
                        
            except:
                continue
        
        return None
    
    def _configure_windows_environment(self, python_path: str) -> bool:
        """Configura ambiente Windows"""
        # No Windows, o instalador já deve ter configurado o PATH
        # Verificar se está funcionando
        return self._validate_installation()
    
    def _configure_unix_environment(self, python_path: str) -> bool:
        """Configura ambiente Unix (Linux/macOS)"""
        python_dir = str(Path(python_path).parent)
        
        # Adicionar ao PATH no .bashrc/.zshrc
        shell_configs = [
            Path.home() / ".bashrc",
            Path.home() / ".zshrc",
            Path.home() / ".profile"
        ]
        
        path_line = f'export PATH="{python_dir}:$PATH"'
        
        for config_file in shell_configs:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                    
                    if path_line not in content:
                        with open(config_file, 'a') as f:
                            f.write(f"\n# Python 3.13 - VideoConverter Installer\n")
                            f.write(f"{path_line}\n")
                        
                        print(f"✅ PATH adicionado ao {config_file}")
                        
                except Exception as e:
                    print(f"⚠️ Erro ao configurar {config_file}: {e}")
        
        return True
    
    def validate_installation(self) -> bool:
        """
        Valida se Python 3.13 foi instalado corretamente
        
        Returns:
            bool: True se instalação válida
        """
        return self._validate_installation()
    
    def _validate_installation(self) -> bool:
        """Executa validação completa da instalação"""
        try:
            # Redetectar Python atual
            self._current_python = None
            current = self.get_current_python()
            
            if not current:
                print("❌ Python não detectado após instalação")
                return False
            
            # Verificar versão 3.13
            if not current.version.startswith("3.13"):
                print(f"❌ Versão incorreta: {current.version} (esperado 3.13.x)")
                return False
            
            # Verificar pip
            if not current.has_pip:
                print("❌ pip não disponível")
                return False
            
            # Verificar venv
            if not current.has_venv:
                print("❌ venv não disponível")
                return False
            
            # Teste funcional básico
            test_code = "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
            
            result = subprocess.run(
                [current.executable, "-c", test_code],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"❌ Teste funcional falhou: {result.stderr}")
                return False
            
            print("✅ Python 3.13 validado com sucesso!")
            print(f"   Versão: {current.version}")
            print(f"   Executável: {current.executable}")
            print(f"   Pip: {'✅' if current.has_pip else '❌'}")
            print(f"   Venv: {'✅' if current.has_venv else '❌'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na validação: {e}")
            return False
    
    def get_summary(self) -> Dict:
        """
        Retorna resumo do status Python
        
        Returns:
            Dict: Informações formatadas
        """
        current = self.get_current_python()
        
        return {
            "python_atual": {
                "detectado": current is not None,
                "versao": current.version if current else "N/A",
                "executavel": current.executable if current else "N/A",
                "64bit": current.is_64bit if current else False,
                "pip": current.has_pip if current else False,
                "venv": current.has_venv if current else False,
                "compativel": current.is_compatible if current else False
            },
            "python_313": {
                "necessario": self.needs_python_install(),
                "url_download": self.get_download_url(),
                "cache_dir": str(self.cache_dir)
            },
            "sistema": {
                "os": self.os_info.name,
                "arquitetura": self.os_info.architecture,
                "compativel": self.os_info.python_compatible
            }
        }


# Função de conveniência
def check_python() -> PythonInfo:
    """
    Função de conveniência para verificar Python
    
    Returns:
        PythonInfo: Informações do Python atual
    """
    manager = PythonManager()
    return manager.get_current_python()


if __name__ == "__main__":
    # Teste do gerenciador
    manager = PythonManager()
    
    print("🐍 Status do Python:")
    current = manager.get_current_python()
    
    if current:
        print(f"Versão: {current.version}")
        print(f"Executável: {current.executable}")
        print(f"Pip: {'✅' if current.has_pip else '❌'}")
        print(f"Venv: {'✅' if current.has_venv else '❌'}")
        print(f"Compatível: {'✅' if current.is_compatible else '❌'}")
    else:
        print("❌ Python não detectado")
    
    print(f"\nPrecisa instalar Python 3.13: {'✅' if manager.needs_python_install() else '❌'}")
    
    if manager.needs_python_install():
        url = manager.get_download_url()
        if url:
            print(f"URL de download: {url}")
        else:
            print("❌ Download não disponível para este sistema")