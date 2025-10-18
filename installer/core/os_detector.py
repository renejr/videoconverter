"""
🖥️ Detector de Sistema Operacional - VideoConverter Installer
============================================================

Detecta automaticamente:
- Sistema operacional (Windows, Linux, macOS)
- Versão específica do OS
- Arquitetura (x64, ARM64, x86)
- Distribuição Linux (Ubuntu, Debian, CentOS, etc.)
- Compatibilidade com Python 3.13 e CUDA
"""

import platform
import sys
import os
import subprocess
import json
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OSInfo:
    """Informações detalhadas do sistema operacional"""
    name: str                    # windows, linux, darwin
    version: str                 # 10, 11, 20.04, etc.
    architecture: str            # x64, arm64, x86
    distribution: Optional[str]  # ubuntu, debian, centos, etc. (Linux only)
    release_name: Optional[str]  # focal, jammy, etc. (Linux only)
    is_64bit: bool              # True se 64-bit
    python_compatible: bool      # Compatível com Python 3.13
    cuda_compatible: bool        # Compatível com CUDA


class OSDetector:
    """
    Detector avançado de sistema operacional
    
    Funcionalidades:
    - Detecção automática de OS, versão e arquitetura
    - Identificação de distribuições Linux
    - Verificação de compatibilidade Python 3.13
    - Verificação de compatibilidade CUDA
    - Validação de privilégios administrativos
    """
    
    def __init__(self):
        """Inicializa o detector de sistema operacional"""
        self._os_info: Optional[OSInfo] = None
        self._admin_privileges: Optional[bool] = None
    
    def detect(self) -> OSInfo:
        """
        Detecta informações completas do sistema operacional
        
        Returns:
            OSInfo: Informações detalhadas do sistema
        """
        if self._os_info is None:
            self._os_info = self._perform_detection()
        
        return self._os_info
    
    def _perform_detection(self) -> OSInfo:
        """Executa a detecção completa do sistema"""
        # Informações básicas
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Arquitetura normalizada
        arch = self._normalize_architecture(machine)
        
        # Detecção específica por OS
        if system == "windows":
            return self._detect_windows(arch)
        elif system == "linux":
            return self._detect_linux(arch)
        elif system == "darwin":
            return self._detect_macos(arch)
        else:
            raise OSError(f"Sistema operacional não suportado: {system}")
    
    def _normalize_architecture(self, machine: str) -> str:
        """Normaliza a arquitetura para formato padrão"""
        arch_mapping = {
            'amd64': 'x64',
            'x86_64': 'x64',
            'x64': 'x64',
            'arm64': 'arm64',
            'aarch64': 'arm64',
            'i386': 'x86',
            'i686': 'x86',
            'x86': 'x86'
        }
        
        return arch_mapping.get(machine, machine)
    
    def _detect_windows(self, arch: str) -> OSInfo:
        """Detecta informações específicas do Windows"""
        version = platform.version()
        release = platform.release()
        
        # Determinar versão do Windows
        win_version = self._get_windows_version()
        
        return OSInfo(
            name="windows",
            version=win_version,
            architecture=arch,
            distribution=None,
            release_name=None,
            is_64bit=arch in ['x64', 'arm64'],
            python_compatible=self._check_python_compatibility("windows", win_version, arch),
            cuda_compatible=self._check_cuda_compatibility("windows", arch)
        )
    
    def _get_windows_version(self) -> str:
        """Obtém versão específica do Windows"""
        try:
            # Usar wmic para obter versão precisa
            result = subprocess.run(
                ['wmic', 'os', 'get', 'Caption', '/value'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Caption=' in line:
                        caption = line.split('=')[1].strip()
                        if 'Windows 11' in caption:
                            return "11"
                        elif 'Windows 10' in caption:
                            return "10"
                        elif 'Windows 8.1' in caption:
                            return "8.1"
                        elif 'Windows 8' in caption:
                            return "8"
                        elif 'Windows 7' in caption:
                            return "7"
            
            # Fallback para platform
            return platform.release()
            
        except Exception:
            return platform.release()
    
    def _detect_linux(self, arch: str) -> OSInfo:
        """Detecta informações específicas do Linux"""
        distribution, version, release_name = self._get_linux_distribution()
        
        return OSInfo(
            name="linux",
            version=version,
            architecture=arch,
            distribution=distribution,
            release_name=release_name,
            is_64bit=arch in ['x64', 'arm64'],
            python_compatible=self._check_python_compatibility("linux", version, arch),
            cuda_compatible=self._check_cuda_compatibility("linux", arch)
        )
    
    def _get_linux_distribution(self) -> Tuple[str, str, Optional[str]]:
        """Obtém informações da distribuição Linux"""
        try:
            # Tentar /etc/os-release primeiro
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    lines = f.readlines()
                
                info = {}
                for line in lines:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        info[key] = value.strip('"')
                
                distribution = info.get('ID', '').lower()
                version = info.get('VERSION_ID', '')
                release_name = info.get('VERSION_CODENAME', info.get('UBUNTU_CODENAME'))
                
                return distribution, version, release_name
            
            # Fallback para platform
            dist_info = platform.linux_distribution()
            return dist_info[0].lower(), dist_info[1], None
            
        except Exception:
            # Último recurso
            return "unknown", "unknown", None
    
    def _detect_macos(self, arch: str) -> OSInfo:
        """Detecta informações específicas do macOS"""
        version = platform.mac_ver()[0]
        
        return OSInfo(
            name="darwin",
            version=version,
            architecture=arch,
            distribution=None,
            release_name=None,
            is_64bit=arch in ['x64', 'arm64'],
            python_compatible=self._check_python_compatibility("darwin", version, arch),
            cuda_compatible=self._check_cuda_compatibility("darwin", arch)
        )
    
    def _check_python_compatibility(self, os_name: str, version: str, arch: str) -> bool:
        """Verifica compatibilidade com Python 3.13"""
        # Python 3.13 requirements
        if os_name == "windows":
            # Windows 10+ (build 1607+) ou Windows 11
            if version in ["10", "11"]:
                return arch in ['x64', 'arm64', 'x86']
            return False
        
        elif os_name == "linux":
            # Distribuições modernas com glibc 2.17+
            return arch in ['x64', 'arm64']
        
        elif os_name == "darwin":
            # macOS 10.9+ para Python 3.13
            try:
                major, minor = version.split('.')[:2]
                if int(major) >= 11 or (int(major) == 10 and int(minor) >= 9):
                    return arch in ['x64', 'arm64']
            except:
                pass
            return False
        
        return False
    
    def _check_cuda_compatibility(self, os_name: str, arch: str) -> bool:
        """Verifica compatibilidade básica com CUDA"""
        # CUDA suporte básico por OS/arquitetura
        if os_name == "windows":
            return arch == 'x64'  # CUDA no Windows só x64
        elif os_name == "linux":
            return arch == 'x64'  # CUDA no Linux principalmente x64
        elif os_name == "darwin":
            return False  # NVIDIA descontinuou CUDA no macOS
        
        return False
    
    def has_admin_privileges(self) -> bool:
        """
        Verifica se o usuário tem privilégios administrativos
        
        Returns:
            bool: True se tem privilégios admin
        """
        if self._admin_privileges is None:
            self._admin_privileges = self._check_admin_privileges()
        
        return self._admin_privileges
    
    def _check_admin_privileges(self) -> bool:
        """Verifica privilégios administrativos por OS"""
        os_info = self.detect()
        
        try:
            if os_info.name == "windows":
                # Windows: verificar se é admin
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            
            elif os_info.name in ["linux", "darwin"]:
                # Unix: verificar se é root ou pode usar sudo
                if os.geteuid() == 0:
                    return True
                
                # Verificar sudo
                result = subprocess.run(
                    ['sudo', '-n', 'true'],
                    capture_output=True,
                    timeout=5
                )
                return result.returncode == 0
            
        except Exception:
            pass
        
        return False
    
    def get_package_manager(self) -> Optional[str]:
        """
        Retorna o gerenciador de pacotes do sistema
        
        Returns:
            str: Nome do gerenciador (apt, yum, dnf, pacman, brew, choco)
        """
        os_info = self.detect()
        
        if os_info.name == "windows":
            # Verificar se tem chocolatey
            try:
                subprocess.run(['choco', '--version'], 
                             capture_output=True, timeout=5)
                return "choco"
            except:
                return None
        
        elif os_info.name == "linux":
            # Verificar gerenciadores Linux
            managers = {
                'apt': ['/usr/bin/apt', '/usr/bin/apt-get'],
                'yum': ['/usr/bin/yum'],
                'dnf': ['/usr/bin/dnf'],
                'pacman': ['/usr/bin/pacman'],
                'zypper': ['/usr/bin/zypper']
            }
            
            for manager, paths in managers.items():
                if any(os.path.exists(path) for path in paths):
                    return manager
        
        elif os_info.name == "darwin":
            # Verificar se tem homebrew
            try:
                subprocess.run(['brew', '--version'], 
                             capture_output=True, timeout=5)
                return "brew"
            except:
                return None
        
        return None
    
    def get_summary(self) -> Dict:
        """
        Retorna resumo completo das informações do sistema
        
        Returns:
            Dict: Informações formatadas do sistema
        """
        os_info = self.detect()
        
        return {
            "sistema": {
                "nome": os_info.name,
                "versao": os_info.version,
                "arquitetura": os_info.architecture,
                "distribuicao": os_info.distribution,
                "release": os_info.release_name,
                "64bit": os_info.is_64bit
            },
            "compatibilidade": {
                "python_3_13": os_info.python_compatible,
                "cuda": os_info.cuda_compatible
            },
            "privilegios": {
                "admin": self.has_admin_privileges(),
                "gerenciador_pacotes": self.get_package_manager()
            },
            "python_atual": {
                "versao": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "executavel": sys.executable,
                "64bit": sys.maxsize > 2**32
            }
        }


# Função de conveniência
def detect_system() -> OSInfo:
    """
    Função de conveniência para detectar o sistema
    
    Returns:
        OSInfo: Informações do sistema operacional
    """
    detector = OSDetector()
    return detector.detect()


if __name__ == "__main__":
    # Teste do detector
    detector = OSDetector()
    info = detector.detect()
    summary = detector.get_summary()
    
    print("🖥️ Informações do Sistema:")
    print(f"OS: {info.name} {info.version} ({info.architecture})")
    if info.distribution:
        print(f"Distribuição: {info.distribution}")
    print(f"Python 3.13 compatível: {info.python_compatible}")
    print(f"CUDA compatível: {info.cuda_compatible}")
    print(f"Privilégios admin: {detector.has_admin_privileges()}")
    print(f"Gerenciador de pacotes: {detector.get_package_manager()}")