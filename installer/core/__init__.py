"""
🔧 Core Components - Instalador VideoConverter
==============================================

Componentes principais do instalador:
- OSDetector: Detecção avançada de sistema operacional
- PythonManager: Gerenciamento de instalação Python 3.13
- GPUDetector: Detecção de GPU NVIDIA e compatibilidade CUDA
- CUDAInstaller: Instalação automática de CUDA
- FFmpegManager: Gerenciamento de FFmpeg/FFprobe
"""

from .os_detector import OSDetector
from .python_manager import PythonManager

__all__ = [
    "OSDetector", 
    "PythonManager"
]