"""
Sistema Universal de Detecção e Perfil de Hardware
Detecta e cria perfis adaptativos para qualquer configuração de hardware.
"""

import subprocess
import json
import re
import logging
import psutil
import platform
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import sys
import os

logger = logging.getLogger(__name__)


class HardwareProfile(Enum):
    """Perfis de hardware baseados em capacidades detectadas"""
    WORKSTATION = "workstation"      # 16GB+ VRAM, múltiplas GPUs
    HIGH_END = "high_end"           # 8-16GB VRAM, GPU potente
    MID_RANGE = "mid_range"         # 4-8GB VRAM, GPU média
    ENTRY_LEVEL = "entry_level"     # 2-4GB VRAM, GPU básica
    LOW_END = "low_end"             # <2GB VRAM, GPU limitada
    CPU_ONLY = "cpu_only"           # Sem GPU ou GPU não suportada


@dataclass
class GPUInfo:
    """Informações detalhadas de uma GPU"""
    index: int
    name: str
    memory_total_mb: int
    memory_free_mb: int
    memory_used_mb: int
    driver_version: str
    cuda_version: Optional[str] = None
    compute_capability: Optional[str] = None
    temperature: Optional[int] = None
    utilization: Optional[int] = None
    power_usage: Optional[int] = None
    max_power: Optional[int] = None
    is_primary: bool = False


@dataclass
class SystemInfo:
    """Informações do sistema"""
    cpu_count: int
    cpu_name: str
    ram_total_gb: float
    ram_available_gb: float
    os_name: str
    os_version: str
    architecture: str


@dataclass
class HardwareCapabilities:
    """Capacidades de hardware detectadas"""
    profile: HardwareProfile
    gpus: List[GPUInfo]
    system: SystemInfo
    cuda_available: bool
    opencl_available: bool
    quicksync_available: bool
    recommended_settings: Dict[str, Any]


class UniversalHardwareProfiler:
    """
    Sistema universal de detecção e perfil de hardware.
    Adapta-se automaticamente a qualquer configuração de hardware.
    """

    def __init__(self):
        """Inicializa o profiler universal"""
        self.logger = logging.getLogger(__name__)
        self._capabilities = None
        self._last_detection_time = 0
        self._detection_cache_duration = 30  # Cache por 30 segundos
        
    def get_hardware_capabilities(self, force_refresh: bool = False) -> HardwareCapabilities:
        """
        Obtém capacidades completas do hardware.
        
        Args:
            force_refresh: Força nova detecção ignorando cache
            
        Returns:
            HardwareCapabilities com informações completas
        """
        import time
        current_time = time.time()
        
        if (not force_refresh and 
            self._capabilities and 
            (current_time - self._last_detection_time) < self._detection_cache_duration):
            return self._capabilities
            
        self.logger.info("Detectando capacidades de hardware...")
        
        # Detectar informações do sistema
        system_info = self._detect_system_info()
        
        # Detectar GPUs
        gpus = self._detect_all_gpus()
        
        # Verificar disponibilidade de tecnologias
        cuda_available = self._check_cuda_availability()
        opencl_available = self._check_opencl_availability()
        quicksync_available = self._check_quicksync_availability()
        
        # Determinar perfil de hardware
        profile = self._determine_hardware_profile(gpus, system_info)
        
        # Gerar configurações recomendadas
        recommended_settings = self._generate_recommended_settings(
            profile, gpus, system_info, cuda_available, opencl_available, quicksync_available
        )
        
        self._capabilities = HardwareCapabilities(
            profile=profile,
            gpus=gpus,
            system=system_info,
            cuda_available=cuda_available,
            opencl_available=opencl_available,
            quicksync_available=quicksync_available,
            recommended_settings=recommended_settings
        )
        
        self._last_detection_time = current_time
        
        self.logger.info(f"Hardware detectado: {profile.value} com {len(gpus)} GPU(s)")
        return self._capabilities
    
    def _detect_system_info(self) -> SystemInfo:
        """Detecta informações do sistema"""
        try:
            # Informações de CPU
            cpu_count = psutil.cpu_count(logical=True)
            cpu_name = platform.processor() or "Unknown CPU"
            
            # Informações de RAM
            memory = psutil.virtual_memory()
            ram_total_gb = memory.total / (1024**3)
            ram_available_gb = memory.available / (1024**3)
            
            # Informações do OS
            os_name = platform.system()
            os_version = platform.version()
            architecture = platform.architecture()[0]
            
            return SystemInfo(
                cpu_count=cpu_count,
                cpu_name=cpu_name,
                ram_total_gb=ram_total_gb,
                ram_available_gb=ram_available_gb,
                os_name=os_name,
                os_version=os_version,
                architecture=architecture
            )
        except Exception as e:
            self.logger.warning(f"Erro ao detectar informações do sistema: {e}")
            return SystemInfo(
                cpu_count=4, cpu_name="Unknown", ram_total_gb=8.0, ram_available_gb=4.0,
                os_name="Unknown", os_version="Unknown", architecture="Unknown"
            )
    
    def _detect_all_gpus(self) -> List[GPUInfo]:
        """Detecta todas as GPUs disponíveis"""
        gpus = []
        
        # Detectar GPUs NVIDIA
        nvidia_gpus = self._detect_nvidia_gpus()
        gpus.extend(nvidia_gpus)
        
        # Detectar GPUs AMD (futuro)
        # amd_gpus = self._detect_amd_gpus()
        # gpus.extend(amd_gpus)
        
        # Detectar GPUs Intel (futuro)
        # intel_gpus = self._detect_intel_gpus()
        # gpus.extend(intel_gpus)
        
        # Marcar GPU primária (primeira com mais VRAM)
        if gpus:
            primary_gpu = max(gpus, key=lambda g: g.memory_total_mb)
            primary_gpu.is_primary = True
            
        return gpus
    
    def _detect_nvidia_gpus(self) -> List[GPUInfo]:
        """Detecta GPUs NVIDIA usando nvidia-smi"""
        gpus = []
        
        try:
            # Comando nvidia-smi com informações detalhadas
            result = subprocess.run([
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.free,memory.used,driver_version,temperature.gpu,utilization.gpu,power.draw,power.limit",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 6:
                        try:
                            # Função auxiliar para converter valores seguros
                            def safe_int(value, default=None):
                                if value in ['[Not Supported]', '[N/A]', 'N/A', '']:
                                    return default
                                try:
                                    return int(float(value))
                                except (ValueError, TypeError):
                                    return default
                            
                            def safe_float(value, default=None):
                                if value in ['[Not Supported]', '[N/A]', 'N/A', '']:
                                    return default
                                try:
                                    return float(value)
                                except (ValueError, TypeError):
                                    return default
                            
                            gpu = GPUInfo(
                                index=int(parts[0]),
                                name=parts[1],
                                memory_total_mb=int(parts[2]),
                                memory_free_mb=int(parts[3]),
                                memory_used_mb=int(parts[4]),
                                driver_version=parts[5],
                                temperature=safe_int(parts[6]) if len(parts) > 6 else None,
                                utilization=safe_int(parts[7]) if len(parts) > 7 else None,
                                power_usage=safe_float(parts[8]) if len(parts) > 8 else None,
                                max_power=safe_float(parts[9]) if len(parts) > 9 else None,
                            )
                            gpus.append(gpu)
                        except (ValueError, IndexError) as e:
                            self.logger.warning(f"Erro ao processar linha GPU: {line} - {e}")
                            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.info(f"nvidia-smi não disponível: {e}")
            
        return gpus
    
    def _check_cuda_availability(self) -> bool:
        """Verifica se CUDA está disponível"""
        try:
            result = subprocess.run(
                ["nvidia-smi"], 
                capture_output=True, 
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_opencl_availability(self) -> bool:
        """Verifica se OpenCL está disponível"""
        # Implementação básica - pode ser expandida
        return False
    
    def _check_quicksync_availability(self) -> bool:
        """Verifica se Intel QuickSync está disponível"""
        # Implementação básica - pode ser expandida
        try:
            # Verificar se há GPU Intel
            cpu_info = platform.processor().lower()
            return 'intel' in cpu_info
        except:
            return False
    
    def _determine_hardware_profile(self, gpus: List[GPUInfo], system: SystemInfo) -> HardwareProfile:
        """Determina o perfil de hardware baseado nas capacidades detectadas"""
        if not gpus:
            return HardwareProfile.CPU_ONLY
            
        # Calcular VRAM total
        total_vram_mb = sum(gpu.memory_total_mb for gpu in gpus)
        
        # Determinar perfil baseado na VRAM total
        if total_vram_mb >= 16000:  # 16GB+
            return HardwareProfile.WORKSTATION
        elif total_vram_mb >= 8000:  # 8-16GB
            return HardwareProfile.HIGH_END
        elif total_vram_mb >= 4000:  # 4-8GB
            return HardwareProfile.MID_RANGE
        elif total_vram_mb >= 2000:  # 2-4GB
            return HardwareProfile.ENTRY_LEVEL
        else:  # <2GB
            return HardwareProfile.LOW_END
    
    def _generate_recommended_settings(
        self, 
        profile: HardwareProfile, 
        gpus: List[GPUInfo], 
        system: SystemInfo,
        cuda_available: bool,
        opencl_available: bool,
        quicksync_available: bool
    ) -> Dict[str, Any]:
        """Gera configurações recomendadas baseadas no perfil de hardware"""
        
        settings = {
            "use_hardware_acceleration": cuda_available and len(gpus) > 0,
            "preferred_encoder": "cpu",
            "preferred_decoder": "cpu",
            "max_concurrent_jobs": 1,
            "memory_settings": {},
            "quality_settings": {},
            "performance_settings": {}
        }
        
        if profile == HardwareProfile.WORKSTATION:
            settings.update({
                "max_concurrent_jobs": min(8, len(gpus) * 2),
                "preferred_encoder": "h264_nvenc",
                "preferred_decoder": "h264_cuvid",
                "memory_settings": {
                    "max_memory_usage": 0.85,
                    "prealloc_size": "1G",
                    "max_alloc_size": "4G",
                    "max_concurrent_streams": 16,
                    "enable_memory_pool": True,
                },
                "quality_settings": {
                    "preset": "slow",
                    "cq": 20,
                    "rc_mode": "vbr",
                },
                "performance_settings": {
                    "enable_fast_math": True,
                    "tensor_cores": "enabled",
                    "surfaces": 32,
                    "async_depth": 16,
                    "rc_lookahead": 64,
                }
            })
            
        elif profile == HardwareProfile.HIGH_END:
            settings.update({
                "max_concurrent_jobs": min(6, len(gpus) + 2),
                "preferred_encoder": "h264_nvenc",
                "preferred_decoder": "h264_cuvid",
                "memory_settings": {
                    "max_memory_usage": 0.80,
                    "prealloc_size": "512M",
                    "max_alloc_size": "2G",
                    "max_concurrent_streams": 12,
                    "enable_memory_pool": True,
                },
                "quality_settings": {
                    "preset": "medium",
                    "cq": 23,
                    "rc_mode": "vbr",
                },
                "performance_settings": {
                    "enable_fast_math": True,
                    "tensor_cores": "auto",
                    "surfaces": 24,
                    "async_depth": 12,
                    "rc_lookahead": 48,
                }
            })
            
        elif profile == HardwareProfile.MID_RANGE:
            settings.update({
                "max_concurrent_jobs": min(4, len(gpus) + 1),
                "preferred_encoder": "h264_nvenc",
                "preferred_decoder": "h264_cuvid",
                "memory_settings": {
                    "max_memory_usage": 0.75,
                    "prealloc_size": "256M",
                    "max_alloc_size": "1G",
                    "max_concurrent_streams": 8,
                    "enable_memory_pool": True,
                },
                "quality_settings": {
                    "preset": "medium",
                    "cq": 25,
                    "rc_mode": "vbr",
                },
                "performance_settings": {
                    "enable_fast_math": True,
                    "tensor_cores": "auto",
                    "surfaces": 16,
                    "async_depth": 8,
                    "rc_lookahead": 32,
                }
            })
            
        elif profile == HardwareProfile.ENTRY_LEVEL:
            settings.update({
                "max_concurrent_jobs": 2,
                "preferred_encoder": "h264_nvenc",
                "preferred_decoder": "h264_cuvid",
                "memory_settings": {
                    "max_memory_usage": 0.65,
                    "prealloc_size": "128M",
                    "max_alloc_size": "512M",
                    "max_concurrent_streams": 4,
                    "enable_memory_pool": True,
                },
                "quality_settings": {
                    "preset": "fast",
                    "cq": 28,
                    "rc_mode": "cbr",
                },
                "performance_settings": {
                    "enable_fast_math": True,
                    "tensor_cores": "disabled",
                    "surfaces": 8,
                    "async_depth": 4,
                    "rc_lookahead": 16,
                }
            })
            
        elif profile == HardwareProfile.LOW_END:
            settings.update({
                "max_concurrent_jobs": 1,
                "preferred_encoder": "h264_nvenc",
                "preferred_decoder": "h264_cuvid",
                "memory_settings": {
                    "max_memory_usage": 0.50,
                    "prealloc_size": "64M",
                    "max_alloc_size": "256M",
                    "max_concurrent_streams": 2,
                    "enable_memory_pool": False,
                },
                "quality_settings": {
                    "preset": "fast",
                    "cq": 30,
                    "rc_mode": "cbr",
                },
                "performance_settings": {
                    "enable_fast_math": False,
                    "tensor_cores": "disabled",
                    "surfaces": 4,
                    "async_depth": 2,
                    "rc_lookahead": 8,
                }
            })
            
        else:  # CPU_ONLY
            settings.update({
                "use_hardware_acceleration": False,
                "max_concurrent_jobs": min(system.cpu_count // 2, 4),
                "preferred_encoder": "libx264",
                "preferred_decoder": "h264",
                "memory_settings": {
                    "max_memory_usage": 0.0,
                    "enable_memory_pool": False,
                },
                "quality_settings": {
                    "preset": "medium",
                    "crf": 23,
                },
                "performance_settings": {
                    "threads": system.cpu_count,
                }
            })
        
        return settings
    
    def get_optimal_gpu_for_task(self, task_memory_requirement_mb: int = 0) -> Optional[GPUInfo]:
        """
        Seleciona a GPU mais adequada para uma tarefa específica.
        
        Args:
            task_memory_requirement_mb: Requisito de memória da tarefa
            
        Returns:
            GPUInfo da GPU mais adequada ou None se nenhuma disponível
        """
        capabilities = self.get_hardware_capabilities()
        
        if not capabilities.gpus:
            return None
            
        # Filtrar GPUs com memória suficiente
        suitable_gpus = [
            gpu for gpu in capabilities.gpus 
            if gpu.memory_free_mb >= task_memory_requirement_mb
        ]
        
        if not suitable_gpus:
            # Se nenhuma GPU tem memória suficiente, usar a com mais memória livre
            suitable_gpus = capabilities.gpus
            
        # Selecionar GPU com menor utilização e mais memória livre
        best_gpu = min(suitable_gpus, key=lambda g: (
            g.utilization or 0,  # Menor utilização
            -g.memory_free_mb    # Mais memória livre (negativo para ordem decrescente)
        ))
        
        return best_gpu
    
    def monitor_gpu_usage(self) -> Dict[int, Dict[str, Any]]:
        """
        Monitora o uso atual das GPUs.
        
        Returns:
            Dict com informações de uso por índice da GPU
        """
        usage_info = {}
        
        try:
            result = subprocess.run([
                "nvidia-smi",
                "--query-gpu=index,utilization.gpu,memory.used,memory.free,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 6:
                        try:
                            gpu_index = int(parts[0])
                            usage_info[gpu_index] = {
                                "utilization": int(parts[1]) if parts[1] != '[Not Supported]' else 0,
                                "memory_used_mb": int(parts[2]),
                                "memory_free_mb": int(parts[3]),
                                "temperature": int(parts[4]) if parts[4] != '[Not Supported]' else None,
                                "power_usage": float(parts[5]) if parts[5] != '[Not Supported]' else None,
                            }
                        except (ValueError, IndexError):
                            continue
                            
        except Exception as e:
            self.logger.warning(f"Erro ao monitorar GPUs: {e}")
            
        return usage_info