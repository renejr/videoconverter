"""
🚀 VideoConverter Universal Installer
=====================================

Instalador inteligente e automático para o VideoConverter que:
- Detecta sistema operacional automaticamente
- Instala Python 3.13 se necessário
- Detecta e configura GPU NVIDIA + CUDA
- Baixa e configura FFmpeg/FFprobe
- Configura ambiente completo

Autor: VideoConverter Team
Versão: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "VideoConverter Team"
__description__ = "Instalador Universal Inteligente para VideoConverter"

# Importações principais
from .core.os_detector import OSDetector
from .core.python_manager import PythonManager

__all__ = [
    "OSDetector",
    "PythonManager",
]