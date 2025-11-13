"""
Sistema de Gerenciamento de Fila de Conversões
Gerencia múltiplas conversões simultâneas com balanceamento de carga entre GPUs
"""

import threading
import queue
import time
import platform
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

from video_converter_module.utils.hardware_detector import get_hardware_detector
from video_converter_module.utils.hd_thermal_detector import HDThermalDetector
from video_converter_module.utils.config import HARDWARE_MONITORING
from video_converter_module.utils.universal_hardware_manager import UniversalHardwareManager
from video_converter_module.utils.hardware_integration import HardwareIntegration
from .video_converter import VideoConverter

# Helper para importação única de psutil, evitando duplicações e mantendo fallback
try:
    import psutil as PSUTIL
except Exception:
    PSUTIL = None

def get_psutil():
    """
    Obtém a referência a psutil de forma segura, com cache.
    Retorna None se psutil não estiver disponível.
    """
    global PSUTIL
    if PSUTIL is not None:
        return PSUTIL
    try:
        import importlib
        PSUTIL = importlib.import_module('psutil')
    except Exception:
        PSUTIL = None
    return PSUTIL

class ConversionStatus(Enum):
    """Status de uma conversão na fila"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class GPUType(Enum):
    """Tipos de GPU disponíveis"""

    NVIDIA = "nvidia"
    INTEL = "intel"
    AMD = "amd"
    CPU = "cpu"


@dataclass
class ConversionJob:
    """
    Representa um trabalho de conversão na fila
    """

    id: str
    input_file: str
    output_file: str
    settings: Dict[str, Any]
    callbacks: Dict[str, Callable] = field(default_factory=dict)
    status: ConversionStatus = ConversionStatus.PENDING
    progress: float = 0.0
    assigned_gpu: Optional[GPUType] = None
    thread: Optional[VideoConverter] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class HardwareProfile:
    """
    Perfil de hardware detectado automaticamente
    """

    profile_type: str  # "entry_level", "mid_range", "high_end", "workstation"
    max_concurrent_jobs: int
    nvidia_gpus: List[Dict[str, Any]]
    intel_gpu: Optional[Dict[str, Any]]
    total_vram: int
    recommended_settings: Dict[str, Any]


def get_system_temperatures():
    """
    Obtém temperaturas do sistema de forma compatível com Windows
    
    Returns:
        dict: Dicionário com temperaturas ou None se não disponível
    """
    psutil = get_psutil()
    # No Windows, psutil.sensors_temperatures() geralmente não é suportado
    if platform.system() == "Windows":
        return None
    if not psutil:
        return None
    try:
        return psutil.sensors_temperatures()
    except (AttributeError, OSError):
        return None


class ConversionQueueManager:
    """
    Gerenciador principal da fila de conversões com balanceamento de carga
    """

    def __init__(self):
        # Componentes principais
        self.hardware_detector = get_hardware_detector()
        
        # Inicializar sistema universal de hardware
        try:
            self.universal_hardware = UniversalHardwareManager()
            self.hardware_integration = HardwareIntegration()
            self.universal_hardware.initialize()
            print(f"[QueueManager] Sistema universal inicializado: {self.universal_hardware.get_hardware_tier()}")
        except Exception as e:
            print(f"[QueueManager] Erro ao inicializar sistema universal: {e}")
            self.universal_hardware = None
            self.hardware_integration = None
        
        self.hardware_profile = self._detect_hardware_profile()

        # Fila e controle
        self.job_queue = queue.Queue()
        self.active_jobs: Dict[str, ConversionJob] = {}
        self.completed_jobs: List[ConversionJob] = []
        self.job_counter = 0

        # Threading e controle
        self.queue_thread = None
        self.is_running = False
        self.is_paused = False
        self.lock = threading.RLock()

        # CORREÇÃO CRÍTICA: Limitadores de recursos para evitar superaquecimento
        # Reduzir drasticamente o número de jobs simultâneos
        original_max = self.hardware_profile.max_concurrent_jobs
        self.max_concurrent = min(2, max(1, original_max // 2))  # Máximo 2 jobs simultâneos
        
        # Limitadores de recursos dinâmicos
        self.base_resource_limits = {
            "max_cpu_percent": 70,  # Máximo 70% de CPU
            "max_memory_percent": 85,  # Máximo 85% de memória (base)
            "max_gpu_temp": 75,  # Máximo 75°C na GPU
            "cooldown_time": 5,  # 5 segundos entre jobs
            "max_threads_per_job": 2,  # Máximo 2 threads por job
        }
        
        # Limites dinâmicos que se ajustam baseado na situação
        self.resource_limits = self.base_resource_limits.copy()
        
        # Configurações de memória dinâmica
        self.memory_management = {
            "base_limit": 85,  # Limite base para 1 job
            "multi_job_limit": 92,  # Limite para múltiplos jobs
            "high_performance_limit": 95,  # Limite para alta performance
            "emergency_limit": 98,  # Limite de emergência antes de pausar
            "cleanup_threshold": 90,  # Quando fazer limpeza de memória
        }
        
        # Configurações de CPU dinâmica
        self.cpu_management = {
            "base_limit": 70,  # Limite base para modo auto/eco
            "balanced_limit": 80,  # Limite para modo balanceado
            "high_performance_limit": 90,  # Limite para alta performance
            "emergency_limit": 95,  # Limite de emergência antes de pausar
            "multi_job_penalty": 10,  # Redução do limite para múltiplos jobs
        }
        
        # Configurações de limites de segurança críticos
        self.safety_limits = {
            "critical_cpu": 95.0,      # CPU crítica - parar novos jobs
            "critical_memory": 90.0,   # Memória crítica - parar novos jobs
            "emergency_cpu": 98.0,     # CPU emergência - pausar jobs ativos
            "emergency_memory": 95.0,  # Memória emergência - pausar jobs ativos
            "temperature_limit": 85.0, # Temperatura limite (se disponível)
            "consecutive_failures": 3,  # Falhas consecutivas antes de pausar
            "recovery_time": 30,       # Tempo de recuperação em segundos
            "monitoring_interval": 5   # Intervalo de monitoramento em segundos
        }
        
        # Estado de segurança do sistema
        self.safety_state = {
            "emergency_mode": False,
            "critical_mode": False,
            "consecutive_failures": 0,
            "last_emergency": 0,
            "paused_jobs": [],
            "monitoring_active": False,
            "last_safety_check": 0
        }
        
        # Controle de temperatura
        self.last_job_time = 0
        self.temperature_warnings = 0
        self.temperature_monitor_thread = None
        self.temperature_monitoring = False
        
        # Monitoramento térmico de HD/SSD
        self.hd_thermal_detector = None
        self.hd_thermal_monitoring = False
        self.hd_thermal_status = "normal"  # normal, warning, critical
        self.hd_thermal_paused = False
        self.hd_thermal_last_check = 0
        
        # Inicializar detector térmico de HD se habilitado
        if HARDWARE_MONITORING.get("enable_hd_thermal_monitoring", True):
            try:
                self.hd_thermal_detector = HDThermalDetector()
                self.hd_thermal_monitoring = True
            except Exception as e:
                print(f"Aviso: Não foi possível inicializar monitoramento térmico de HD: {e}")
                self.hd_thermal_monitoring = False
        
        self.retry_rules = {
            "cuda_error": True,
            "memory_error": True,
            "codec_error": False,
            "permission_error": False,
            "timeout_error": True,
        }

        # Callbacks globais
        self.global_callbacks = {
            "queue_updated": None,
            "job_started": None,
            "job_completed": None,
            "job_failed": None,
            "queue_finished": None,
        }

        # Estatísticas
        self.stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "total_processing_time": 0.0,
        }

    def _detect_hardware_profile(self) -> HardwareProfile:
        """
        Detecta automaticamente o perfil de hardware da máquina
        """
        # Tentar usar o sistema universal primeiro
        if self.universal_hardware and self.hardware_integration:
            try:
                # Obter configurações otimizadas do sistema universal
                optimized_config = self.hardware_integration.get_optimized_queue_config()
                
                # Usar as configurações do sistema universal
                profile_type = self.universal_hardware.get_hardware_tier()
                max_concurrent = optimized_config.get('max_concurrent_jobs', 2)
                
                # Obter informações das GPUs do sistema universal
                gpu_info = self.universal_hardware.get_gpu_info()
                nvidia_gpus = []
                intel_gpu = None
                total_vram = 0
                
                for gpu in gpu_info:
                    if 'nvidia' in gpu.get('name', '').lower():
                        nvidia_gpus.append({
                            "name": gpu.get('name', 'NVIDIA GPU'),
                            "vram": gpu.get('memory_total', 4096),
                            "compute_capability": "6.0",  # Valor padrão
                        })
                        total_vram += gpu.get('memory_total', 4096)
                    elif 'intel' in gpu.get('name', '').lower():
                        intel_gpu = {
                            "name": gpu.get('name', 'Intel Graphics'),
                            "quicksync": True,
                        }
                
                recommended_settings = {
                    "prefer_nvidia_for_hevc": len(nvidia_gpus) > 0,
                    "prefer_intel_for_h264": intel_gpu is not None,
                    "auto_gpu_switching": True,
                    "temperature_monitoring": True,
                    "max_temperature_celsius": 85,
                }
                
                return HardwareProfile(
                    profile_type=profile_type,
                    max_concurrent_jobs=max_concurrent,
                    nvidia_gpus=nvidia_gpus,
                    intel_gpu=intel_gpu,
                    total_vram=total_vram,
                    recommended_settings=recommended_settings,
                )
                
            except Exception as e:
                print(f"[QueueManager] Erro ao usar sistema universal, usando fallback: {e}")
        
        # Fallback para o sistema antigo
        hardware_summary = self.hardware_detector.get_hardware_summary()

        # Detectar GPUs NVIDIA
        nvidia_gpus = []
        if hardware_summary.get("cuda_available", False):
            # Simular informações da GPU NVIDIA baseado no que está disponível
            nvidia_gpus.append(
                {
                    "name": "NVIDIA GPU",
                    "vram": 4096,  # Valor padrão, pode ser melhorado
                    "compute_capability": "6.0",  # Valor padrão
                }
            )

        # Detectar GPU Intel (assumir disponível se não for CUDA)
        intel_gpu = None
        if not hardware_summary.get("cuda_available", False):
            intel_gpu = {
                "name": "Intel Graphics",
                "quicksync": True,  # Assumir disponível
            }

        # Calcular VRAM total
        total_vram = sum(gpu["vram"] for gpu in nvidia_gpus)

        # Determinar perfil e configurações
        if total_vram >= 16000:  # 16GB+
            profile_type = "workstation"
            max_concurrent = min(6, len(nvidia_gpus) * 2)
        elif total_vram >= 8000:  # 8-16GB
            profile_type = "high_end"
            max_concurrent = min(4, len(nvidia_gpus) + 1)
        elif total_vram >= 4000:  # 4-8GB
            profile_type = "mid_range"
            max_concurrent = 2
        else:  # <4GB
            profile_type = "entry_level"
            max_concurrent = 1

        # Ajustar se tiver Intel GPU
        if intel_gpu and intel_gpu.get("quicksync", False):
            max_concurrent = min(max_concurrent + 1, 4)

        recommended_settings = {
            "prefer_nvidia_for_hevc": True,
            "prefer_intel_for_h264": intel_gpu is not None,
            "auto_gpu_switching": True,
            "temperature_monitoring": True,
            "max_temperature_celsius": 85,
        }

        return HardwareProfile(
            profile_type=profile_type,
            max_concurrent_jobs=max_concurrent,
            nvidia_gpus=nvidia_gpus,
            intel_gpu=intel_gpu,
            total_vram=total_vram,
            recommended_settings=recommended_settings,
        )

    def get_hardware_info(self) -> Dict[str, Any]:
        """
        Retorna informações detalhadas do hardware detectado
        """
        hardware_info = {
            "profile_type": self.hardware_profile.profile_type,
            "max_concurrent_jobs": self.hardware_profile.max_concurrent_jobs,
            "nvidia_gpus": self.hardware_profile.nvidia_gpus,
            "intel_gpu": self.hardware_profile.intel_gpu,
            "total_vram": self.hardware_profile.total_vram,
            "recommended_settings": self.hardware_profile.recommended_settings,
        }
        
        # Adicionar informações do sistema universal se disponível
        if self.universal_hardware:
            try:
                universal_info = {
                    "universal_system": {
                        "tier": self.universal_hardware.get_hardware_tier(),
                        "gpu_count": self.universal_hardware.get_gpu_count(),
                        "total_vram": self.universal_hardware.get_total_vram(),
                        "cuda_available": self.universal_hardware.is_cuda_available(),
                        "system_ram": self.universal_hardware.get_system_ram(),
                        "gpu_info": self.universal_hardware.get_gpu_info(),
                    }
                }
                hardware_info.update(universal_info)
            except Exception as e:
                print(f"[QueueManager] Erro ao obter informações do sistema universal: {e}")
        
        return hardware_info

    def _adjust_memory_limits(self, performance_mode: str = "auto") -> None:
        """
        Ajusta dinamicamente os limites de memória baseado na situação atual
        
        Args:
            performance_mode: "auto", "low", "medium", "high"
        """
        active_jobs_count = len(self.active_jobs)
        
        # Determinar limite baseado no número de jobs e performance
        if performance_mode == "high" or active_jobs_count > 1:
            if active_jobs_count > 1:
                # Múltiplos jobs - usar limite mais alto
                new_limit = self.memory_management["multi_job_limit"]
            else:
                # Alta performance - usar limite ainda mais alto
                new_limit = self.memory_management["high_performance_limit"]
        else:
            # Job único ou performance baixa/média - usar limite base
            new_limit = self.memory_management["base_limit"]
        
        # Atualizar o limite
        self.resource_limits["max_memory_percent"] = new_limit
        
        # Log da mudança se significativa
        old_limit = self.base_resource_limits["max_memory_percent"]
        if abs(new_limit - old_limit) > 5:
            print(f"📊 Limite de memória ajustado: {old_limit}% → {new_limit}% (jobs ativos: {active_jobs_count}, modo: {performance_mode})")

    def _cleanup_memory_if_needed(self) -> None:
        """
        Força limpeza de memória se necessário
        """
        try:
            import gc
            memory = psutil.virtual_memory()
            
            if memory.percent > self.memory_management["cleanup_threshold"]:
                print(f"🧹 Limpeza de memória iniciada (uso atual: {memory.percent:.1f}%)")
                gc.collect()
                
                # Verificar novamente após limpeza
                memory_after = psutil.virtual_memory()
                freed_mb = (memory.available - memory_after.available) / (1024 * 1024)
                print(f"🧹 Limpeza concluída: {memory_after.percent:.1f}% (liberados: {freed_mb:.1f}MB)")
        except Exception as e:
            print(f"⚠️ Erro na limpeza de memória: {e}")

    def _adjust_cpu_limits(self, performance_mode: str = "auto") -> None:
        """
        Ajusta dinamicamente os limites de CPU baseado no modo de performance e jobs ativos
        
        Args:
            performance_mode: Modo de performance atual ("auto", "eco", "balanced", "high")
        """
        active_jobs_count = len(self.active_jobs)
        
        # Determinar limite base baseado no modo de performance
        if performance_mode == "high":
            base_limit = self.cpu_management["high_performance_limit"]
        elif performance_mode == "balanced":
            base_limit = self.cpu_management["balanced_limit"]
        else:  # auto, eco ou outros
            base_limit = self.cpu_management["base_limit"]
        
        # Ajustar para múltiplos jobs (reduzir limite para evitar sobrecarga)
        if active_jobs_count > 1:
            penalty = min(self.cpu_management["multi_job_penalty"] * (active_jobs_count - 1), 20)
            new_limit = max(base_limit - penalty, self.cpu_management["base_limit"])
        else:
            new_limit = base_limit
        
        # Atualizar o limite
        old_limit = self.resource_limits["max_cpu_percent"]
        self.resource_limits["max_cpu_percent"] = new_limit
        
        # Log da mudança se significativa
        if abs(new_limit - old_limit) > 5:
            print(f"🖥️ Limite de CPU ajustado: {old_limit}% → {new_limit}% (jobs ativos: {active_jobs_count}, modo: {performance_mode})")

    def _adjust_max_concurrent_jobs(self, performance_mode: str = "auto") -> None:
        """
        Ajusta dinamicamente o número máximo de jobs simultâneos baseado nos recursos
        
        Args:
            performance_mode: Modo de performance atual
        """
        try:
            psutil = get_psutil()
            
            # Obter recursos atuais (com fallback)
            if psutil:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
            else:
                cpu_percent = 0.0
                class _Mem: percent = 0.0
                memory = _Mem()
            
            # Calcular capacidade baseada nos recursos
            base_max = self.hardware_profile.max_concurrent_jobs
            
            # Ajustar baseado no modo de performance
            if performance_mode == "high":
                # Alta performance - permitir mais jobs se recursos permitirem
                if cpu_percent < 60 and memory.percent < 70:
                    new_max = min(base_max + 1, 4)  # Máximo 4 jobs
                elif cpu_percent < 80 and memory.percent < 85:
                    new_max = base_max
                else:
                    new_max = max(1, base_max - 1)  # Reduzir se recursos altos
            elif performance_mode == "balanced":
                # Modo balanceado - ajustar baseado nos recursos
                if cpu_percent < 50 and memory.percent < 60:
                    new_max = base_max
                elif cpu_percent < 70 and memory.percent < 80:
                    new_max = max(1, base_max - 1)
                else:
                    new_max = 1  # Apenas 1 job se recursos altos
            else:  # auto, eco
                # Modo conservador - priorizar estabilidade
                if cpu_percent < 40 and memory.percent < 50:
                    new_max = min(base_max, 2)
                elif cpu_percent < 60 and memory.percent < 70:
                    new_max = 1
                else:
                    new_max = 1  # Apenas 1 job se recursos moderados/altos
            
            # Considerar número de GPUs disponíveis
            gpu_count = len(self.hardware_profile.nvidia_gpus) + (1 if self.hardware_profile.intel_gpu else 0)
            if gpu_count > 1:
                new_max = min(new_max + 1, gpu_count)  # Máximo igual ao número de GPUs
            
            # Atualizar se mudou significativamente
            old_max = self.max_concurrent
            if new_max != old_max:
                self.max_concurrent = new_max
                info_cpu = f"{cpu_percent:.1f}%" if psutil else "N/A"
                info_ram = f"{memory.percent:.1f}%" if psutil else "N/A"
                print(f"🔄 Jobs simultâneos ajustados: {old_max} → {new_max} (CPU: {info_cpu}, RAM: {info_ram}, modo: {performance_mode})")
                
        except Exception as e:
             print(f"⚠️ Erro ao ajustar jobs simultâneos: {e}")

    def _calculate_job_priority(self, job: ConversionJob) -> int:
        """
        Calcula a prioridade de um job baseado no tamanho e complexidade
        
        Args:
            job: Job para calcular prioridade
            
        Returns:
            int: Prioridade (menor número = maior prioridade)
        """
        try:
            import os
            
            # Prioridade base
            priority = 100
            
            # Ajustar baseado no tamanho do arquivo
            if os.path.exists(job.input_file):
                file_size_mb = os.path.getsize(job.input_file) / (1024 * 1024)
                
                if file_size_mb < 100:  # Arquivos pequenos têm prioridade
                    priority -= 30
                elif file_size_mb < 500:  # Arquivos médios
                    priority -= 10
                elif file_size_mb > 2000:  # Arquivos grandes têm menor prioridade
                    priority += 20
            
            # Ajustar baseado nas configurações
            settings = job.settings
            
            # Conversões simples têm prioridade
            if settings.get("format", "").lower() in ["mp4", "avi"]:
                priority -= 15
            
            # Conversões complexas têm menor prioridade
            if settings.get("format", "").lower() in ["hevc", "h.265", "av1"]:
                priority += 25
            
            # Qualidade alta tem menor prioridade
            quality = settings.get("quality", "medium")
            if quality == "high" or quality == "ultra":
                priority += 15
            elif quality == "low":
                priority -= 10
            
            # Modo de performance afeta prioridade
            performance_mode = settings.get("performance_mode", "auto")
            if performance_mode == "eco":
                priority -= 5  # Eco tem prioridade para economizar recursos
            elif performance_mode == "high":
                priority += 10  # Alta performance espera mais
            
            return max(1, priority)  # Mínimo 1
            
        except Exception as e:
            print(f"⚠️ Erro ao calcular prioridade do job {job.id}: {e}")
            return 100  # Prioridade padrão

    def _reorder_queue_by_priority(self) -> None:
        """
        Reordena a fila de jobs baseado na prioridade calculada
        """
        try:
            if self.job_queue.empty():
                return
            
            # Extrair todos os jobs da fila
            jobs = []
            while not self.job_queue.empty():
                try:
                    job = self.job_queue.get_nowait()
                    jobs.append(job)
                except queue.Empty:
                    break
            
            # Calcular prioridades e ordenar
            jobs_with_priority = [(self._calculate_job_priority(job), job) for job in jobs]
            jobs_with_priority.sort(key=lambda x: x[0])  # Ordenar por prioridade (menor = maior prioridade)
            
            # Recolocar na fila ordenada
            for priority, job in jobs_with_priority:
                self.job_queue.put(job)
            
            if len(jobs) > 1:
                print(f"📋 Fila reordenada por prioridade ({len(jobs)} jobs)")
                
        except Exception as e:
             print(f"⚠️ Erro ao reordenar fila: {e}")

    def _check_critical_safety(self) -> bool:
        """
        Verifica limites críticos de segurança do sistema
        
        Returns:
            bool: True se é seguro continuar, False se deve parar
        """
        try:
            psutil = get_psutil()
            
            current_time = time.time()
            
            # Verificar apenas a cada intervalo definido
            if current_time - self.safety_state["last_safety_check"] < self.safety_limits["monitoring_interval"]:
                return not self.safety_state["emergency_mode"]
            
            self.safety_state["last_safety_check"] = current_time
            
            # Obter métricas do sistema (se disponíveis)
            if psutil:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
            else:
                # Sem psutil não é possível aferir métricas; manter estado atual
                return not self.safety_state["emergency_mode"]
            
            # Verificar condições de emergência
            emergency_triggered = False
            critical_triggered = False
            
            if cpu_percent >= self.safety_limits["emergency_cpu"]:
                emergency_triggered = True
                print(f"🚨 EMERGÊNCIA: CPU em {cpu_percent:.1f}% (limite: {self.safety_limits['emergency_cpu']}%)")
            
            if memory.percent >= self.safety_limits["emergency_memory"]:
                emergency_triggered = True
                print(f"🚨 EMERGÊNCIA: Memória em {memory.percent:.1f}% (limite: {self.safety_limits['emergency_memory']}%)")
            
            # Verificar condições críticas
            if cpu_percent >= self.safety_limits["critical_cpu"]:
                critical_triggered = True
                print(f"⚠️ CRÍTICO: CPU em {cpu_percent:.1f}% (limite: {self.safety_limits['critical_cpu']}%)")
            
            if memory.percent >= self.safety_limits["critical_memory"]:
                critical_triggered = True
                print(f"⚠️ CRÍTICO: Memória em {memory.percent:.1f}% (limite: {self.safety_limits['critical_memory']}%)")
            
            # Ações de emergência
            if emergency_triggered and not self.safety_state["emergency_mode"]:
                self._activate_emergency_mode()
                return False
            
            # Ações críticas
            if critical_triggered and not self.safety_state["critical_mode"]:
                self._activate_critical_mode()
                return False
            
            # Verificar recuperação
            if self.safety_state["emergency_mode"] or self.safety_state["critical_mode"]:
                if not emergency_triggered and not critical_triggered:
                    recovery_time = current_time - self.safety_state["last_emergency"]
                    if recovery_time >= self.safety_limits["recovery_time"]:
                        self._deactivate_safety_modes()
                        return True
                return False
            
            return True
            
        except Exception as e:
            print(f"⚠️ Erro na verificação de segurança: {e}")
            return True  # Em caso de erro, permitir continuar

    def _activate_emergency_mode(self) -> None:
        """
        Ativa modo de emergência - pausa jobs ativos
        """
        try:
            
            self.safety_state["emergency_mode"] = True
            self.safety_state["critical_mode"] = True
            self.safety_state["last_emergency"] = time.time()
            
            print("🚨 MODO EMERGÊNCIA ATIVADO - Pausando jobs ativos")
            
            # Pausar jobs ativos
            for job_id in list(self.active_jobs.keys()):
                if job_id not in self.safety_state["paused_jobs"]:
                    self.safety_state["paused_jobs"].append(job_id)
                    print(f"⏸️ Job {job_id} pausado por emergência")
            
            # Forçar limpeza de memória
            self._cleanup_memory()
            
        except Exception as e:
            print(f"⚠️ Erro ao ativar modo emergência: {e}")

    def _activate_critical_mode(self) -> None:
        """
        Ativa modo crítico - impede novos jobs
        """
        try:
            
            self.safety_state["critical_mode"] = True
            self.safety_state["last_emergency"] = time.time()
            
            print("⚠️ MODO CRÍTICO ATIVADO - Bloqueando novos jobs")
            
        except Exception as e:
            print(f"⚠️ Erro ao ativar modo crítico: {e}")

    def _deactivate_safety_modes(self) -> None:
        """
        Desativa modos de segurança após recuperação
        """
        try:
            was_emergency = self.safety_state["emergency_mode"]
            
            self.safety_state["emergency_mode"] = False
            self.safety_state["critical_mode"] = False
            self.safety_state["consecutive_failures"] = 0
            
            if was_emergency:
                print("✅ Sistema recuperado - Retomando operação normal")
                
                # Retomar jobs pausados
                for job_id in self.safety_state["paused_jobs"]:
                    if job_id in self.active_jobs:
                        print(f"▶️ Retomando job {job_id}")
                
                self.safety_state["paused_jobs"].clear()
            else:
                print("✅ Modo crítico desativado - Novos jobs permitidos")
                
        except Exception as e:
            print(f"⚠️ Erro ao desativar modos de segurança: {e}")

    def set_global_callbacks(self, callbacks: Dict[str, Callable]):
        """
        Define callbacks globais para eventos da fila
        """
        self.global_callbacks.update(callbacks)

    def add_job(
        self,
        input_file: str,
        output_file: str,
        settings: Dict[str, Any],
        callbacks: Optional[Dict[str, Callable]] = None,
    ) -> str:
        """
        Adiciona um novo trabalho à fila

        Returns:
            str: ID único do trabalho
        """
        with self.lock:
            job_id = f"job_{self.job_counter:04d}"
            self.job_counter += 1

            job = ConversionJob(
                id=job_id,
                input_file=input_file,
                output_file=output_file,
                settings=settings,
                callbacks=callbacks or {},
            )

            self.job_queue.put(job)
            self.stats["total_jobs"] += 1

            # Reordenar fila por prioridade se há múltiplos jobs
            if self.job_queue.qsize() > 1:
                self._reorder_queue_by_priority()

            # Callback de atualização da fila
            self._notify_queue_updated()

            return job_id

    def add_multiple_jobs(self, jobs_data: List[Dict[str, Any]]) -> List[str]:
        """
        Adiciona múltiplos trabalhos à fila

        Args:
            jobs_data: Lista de dicionários com dados dos trabalhos

        Returns:
            List[str]: Lista de IDs dos trabalhos criados
        """
        job_ids = []
        for job_data in jobs_data:
            job_id = self.add_job(
                job_data["input_file"],
                job_data["output_file"],
                job_data["settings"],
                job_data.get("callbacks"),
            )
            job_ids.append(job_id)

        return job_ids

    def start_queue(self):
        """
        Inicia o processamento da fila
        """
        if self.is_running:
            return

        self.is_running = True
        self.is_paused = False

        self.queue_thread = threading.Thread(target=self._queue_worker, daemon=True)
        self.queue_thread.start()
        
        # CORREÇÃO CRÍTICA: Iniciar monitoramento de temperatura
        self.start_temperature_monitoring()

    def pause_queue(self):
        """
        Pausa o processamento da fila
        """
        self.is_paused = True

    def resume_queue(self):
        """
        Resume o processamento da fila
        """
        self.is_paused = False

    def stop_queue(self):
        """
        Para completamente o processamento da fila
        """
        self.is_running = False

        # Cancelar trabalhos ativos
        with self.lock:
            for job in self.active_jobs.values():
                if job.thread and job.thread.is_alive():
                    job.thread.cancel_conversion()
                job.status = ConversionStatus.CANCELLED

        # Aguardar thread principal
        if self.queue_thread and self.queue_thread.is_alive():
            self.queue_thread.join(timeout=5)
    
    def stop_all_conversions(self):
        """
        CORREÇÃO CRÍTICA: Para todas as conversões imediatamente
        Método chamado no fechamento da aplicação para evitar superaquecimento
        """
        print("🛑 Parando todas as conversões para evitar superaquecimento...")
        
        # Parar monitoramento de temperatura
        self.stop_temperature_monitoring()
        
        # Parar a fila
        self.stop_queue()
        
        # Forçar parada de todos os jobs ativos
        with self.lock:
            for job_id, job in list(self.active_jobs.items()):
                try:
                    if job.thread and hasattr(job.thread, 'process') and job.thread.process:
                        print(f"🛑 Terminando processo do job {job_id}")
                        job.thread.process.terminate()
                        # Aguardar um pouco e forçar kill se necessário
                        try:
                            job.thread.process.wait(timeout=3)
                        except:
                            job.thread.process.kill()
                    
                    job.status = ConversionStatus.CANCELLED
                    job.error_message = "Parado pelo usuário para evitar superaquecimento"
                    
                except Exception as e:
                    print(f"⚠️ Erro ao parar job {job_id}: {e}")
            
            # Limpar jobs ativos
            self.active_jobs.clear()
        
        print("✅ Todas as conversões foram paradas com segurança")
    
    def start_temperature_monitoring(self):
        """
        CORREÇÃO CRÍTICA: Inicia monitoramento contínuo de temperatura
        """
        if self.temperature_monitoring:
            return
        
        self.temperature_monitoring = True
        self.temperature_monitor_thread = threading.Thread(
            target=self._temperature_monitor_worker, 
            daemon=True
        )
        self.temperature_monitor_thread.start()
        print("🌡️ Monitoramento de temperatura iniciado")
    
    def stop_temperature_monitoring(self):
        """
        Para o monitoramento de temperatura
        """
        self.temperature_monitoring = False
        if self.temperature_monitor_thread and self.temperature_monitor_thread.is_alive():
            self.temperature_monitor_thread.join(timeout=2)
        print("🌡️ Monitoramento de temperatura parado")
    
    def _temperature_monitor_worker(self):
        """
        Worker que monitora temperatura continuamente (CPU/GPU e HD/SSD)
        """
        while self.temperature_monitoring:
            try:
                
                # Monitoramento de temperatura CPU/GPU (compatível com Windows)
                temps = get_system_temperatures()
                if temps:
                    max_temp = 0
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current:
                                max_temp = max(max_temp, entry.current)
                    
                    # Se temperatura muito alta, pausar conversões
                    if max_temp > self.resource_limits["max_gpu_temp"]:
                        print(f"🔥 TEMPERATURA CRÍTICA CPU/GPU: {max_temp}°C - PAUSANDO CONVERSÕES")
                        self.pause_queue()
                        
                        # Aguardar temperatura baixar
                        while max_temp > (self.resource_limits["max_gpu_temp"] - 5):
                            time.sleep(5)
                            temps = get_system_temperatures()
                            if temps:
                                max_temp = 0
                                for name, entries in temps.items():
                                    for entry in entries:
                                        if entry.current:
                                            max_temp = max(max_temp, entry.current)
                        
                        print(f"❄️ Temperatura CPU/GPU normalizada: {max_temp}°C - RESUMINDO CONVERSÕES")
                        self.resume_queue()
                else:
                    # No Windows ou sistemas sem suporte a sensores de temperatura
                    print("ℹ️ Monitoramento de temperatura não disponível neste sistema")
                
                # Monitoramento térmico de HD/SSD
                self._check_hd_thermal_status()
                
                time.sleep(10)  # Verificar a cada 10 segundos
                
            except Exception as e:
                print(f"⚠️ Erro no monitoramento de temperatura: {e}")
                time.sleep(10)

    def _check_hd_thermal_status(self):
        """
        Verifica o status térmico dos HDs/SSDs e aplica proteção térmica se necessário
        """
        if not self.hd_thermal_monitoring or not self.hd_thermal_detector:
            return
        
        current_time = time.time()
        check_interval = HARDWARE_MONITORING.get("hd_thermal_check_interval", 30.0)
        
        # Verificar apenas no intervalo configurado
        if current_time - self.hd_thermal_last_check < check_interval:
            return
        
        self.hd_thermal_last_check = current_time
        
        try:
            # Obter temperatura dos discos usando o método correto
            thermal_info = self.hd_thermal_detector.get_hd_temperatures()
            
            if not thermal_info:
                return
            
            # Verificar se algum disco está superaquecendo
            warning_threshold = HARDWARE_MONITORING.get("hd_temp_warning_threshold", 50)
            critical_threshold = HARDWARE_MONITORING.get("hd_temp_critical_threshold", 60)
            thermal_protection = HARDWARE_MONITORING.get("hd_thermal_protection", True)
            
            max_hd_temp = 0
            critical_disks = []
            warning_disks = []
            
            for drive_path, disk_info in thermal_info.items():
                temp = disk_info.get("temperature")
                disk_name = drive_path  # Usar o caminho do drive como nome
                
                if temp is not None:
                    max_hd_temp = max(max_hd_temp, temp)
                    
                    if temp >= critical_threshold:
                        critical_disks.append(f"{disk_name} ({temp}°C)")
                    elif temp >= warning_threshold:
                        warning_disks.append(f"{disk_name} ({temp}°C)")
            
            # Atualizar status térmico
            if critical_disks:
                self.hd_thermal_status = "critical"
                if thermal_protection and not self.hd_thermal_paused:
                    print(f"🔥 TEMPERATURA CRÍTICA HD/SSD: {', '.join(critical_disks)} - PAUSANDO CONVERSÕES")
                    self.pause_queue()
                    self.hd_thermal_paused = True
            elif warning_disks:
                self.hd_thermal_status = "warning"
                print(f"⚠️ Aviso de temperatura HD/SSD: {', '.join(warning_disks)}")
            else:
                # Temperatura normal
                if self.hd_thermal_status != "normal":
                    self.hd_thermal_status = "normal"
                    if self.hd_thermal_paused:
                        cooldown_time = HARDWARE_MONITORING.get("hd_thermal_cooldown_time", 120)
                        print(f"❄️ Temperatura HD/SSD normalizada (máx: {max_hd_temp}°C) - Aguardando {cooldown_time}s antes de resumir")
                        time.sleep(cooldown_time)
                        print("✅ Resumindo conversões após cooldown térmico")
                        self.resume_queue()
                        self.hd_thermal_paused = False
                        
        except Exception as e:
            print(f"⚠️ Erro no monitoramento térmico de HD: {e}")

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancela um trabalho específico

        Returns:
            bool: True se cancelado com sucesso
        """
        with self.lock:
            # Verificar se está ativo
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                if job.thread and job.thread.is_alive():
                    job.thread.cancel_conversion()
                job.status = ConversionStatus.CANCELLED
                return True

            # Remover da fila se ainda não iniciou
            temp_queue = queue.Queue()
            found = False

            while not self.job_queue.empty():
                try:
                    job = self.job_queue.get_nowait()
                    if job.id == job_id:
                        job.status = ConversionStatus.CANCELLED
                        found = True
                    else:
                        temp_queue.put(job)
                except queue.Empty:
                    break

            # Restaurar fila
            self.job_queue = temp_queue
            return found

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Retorna status atual da fila
        """
        with self.lock:
            pending_count = self.job_queue.qsize()
            active_count = len(self.active_jobs)

            return {
                "is_running": self.is_running,
                "is_paused": self.is_paused,
                "pending_jobs": pending_count,
                "active_jobs": active_count,
                "completed_jobs": len(self.completed_jobs),
                "total_jobs": self.stats["total_jobs"],
                "active_job_details": [
                    {
                        "id": job.id,
                        "input_file": Path(job.input_file).name,
                        "progress": job.progress,
                        "assigned_gpu": (
                            job.assigned_gpu.value if job.assigned_gpu else None
                        ),
                    }
                    for job in self.active_jobs.values()
                ],
                "hardware_profile": self.hardware_profile.profile_type,
                "max_concurrent": self.max_concurrent,
            }

    def get_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retorna detalhes de um trabalho específico
        """
        with self.lock:
            # Procurar em trabalhos ativos
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                return self._job_to_dict(job)

            # Procurar em trabalhos concluídos
            for job in self.completed_jobs:
                if job.id == job_id:
                    return self._job_to_dict(job)

            return None

    def _job_to_dict(self, job: ConversionJob) -> Dict[str, Any]:
        """
        Converte um ConversionJob para dicionário
        """
        return {
            "id": job.id,
            "input_file": job.input_file,
            "output_file": job.output_file,
            "status": job.status.value,
            "progress": job.progress,
            "assigned_gpu": job.assigned_gpu.value if job.assigned_gpu else None,
            "start_time": job.start_time,
            "end_time": job.end_time,
            "error_message": job.error_message,
            "retry_count": job.retry_count,
        }

    def _queue_worker(self):
        """
        Worker principal da fila - executa em thread separada
        """
        while self.is_running:
            try:
                # Verificar se está pausado
                if self.is_paused:
                    time.sleep(0.5)
                    continue

                # CORREÇÃO CRÍTICA: Verificar recursos antes de iniciar novos trabalhos
                with self.lock:
                    if len(self.active_jobs) >= self.max_concurrent:
                        time.sleep(0.5)
                        continue
                    
                    # Verificar se os recursos estão seguros
                    # Obter modo de performance do próximo job na fila (se disponível)
                    performance_mode = "auto"  # padrão
                    if not self.job_queue.empty():
                        try:
                            # Peek no próximo job sem removê-lo da fila
                            next_job = self.job_queue.queue[0]
                            performance_mode = next_job.settings.get("performance_mode", "auto")
                        except (IndexError, AttributeError):
                            performance_mode = "auto"
                    
                    if not self._check_resource_safety(performance_mode):
                        time.sleep(2)  # Aguardar mais tempo se recursos estão sobrecarregados
                        continue
                    
                    # Verificar cooldown entre jobs
                    current_time = time.time()
                    if current_time - self.last_job_time < self.resource_limits["cooldown_time"]:
                        time.sleep(1)
                        continue

                # Pegar próximo trabalho da fila
                try:
                    job = self.job_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # Iniciar trabalho
                self._start_job(job)
                self.last_job_time = time.time()

            except Exception as e:
                print(f"Erro no queue worker: {e}")
                time.sleep(1)

    def _check_resource_safety(self, performance_mode: str = "auto") -> bool:
        """
        CORREÇÃO CRÍTICA: Verifica se é seguro iniciar novos jobs
        Monitora CPU, memória e temperatura para evitar superaquecimento
        
        Args:
            performance_mode: Modo de performance para ajustar limites dinamicamente
            
        Returns:
            bool: True se é seguro iniciar novos jobs
        """
        try:
            psutil = get_psutil()
            
            # VERIFICAÇÃO CRÍTICA DE SEGURANÇA - Primeira prioridade
            if not self._check_critical_safety():
                return False
            
            # Ajustar limites dinamicamente baseado na situação atual
            self._adjust_memory_limits(performance_mode)
            self._adjust_cpu_limits(performance_mode)
            self._adjust_max_concurrent_jobs(performance_mode)
            
            # Sem psutil, seguimos com verificação básica após ajustes
            if not psutil:
                print("⚠️ psutil não disponível - usando verificação básica")
                return True
            
            # Verificar CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > self.resource_limits["max_cpu_percent"]:
                print(f"⚠️ CPU muito alta: {cpu_percent:.1f}% (limite: {self.resource_limits['max_cpu_percent']}%)")
                return False
            
            # Verificar memória com sistema dinâmico
            memory = psutil.virtual_memory()
            
            # Se memória está muito alta, tentar limpeza primeiro
            if memory.percent > self.memory_management["cleanup_threshold"]:
                self._cleanup_memory_if_needed()
                # Verificar novamente após limpeza
                memory = psutil.virtual_memory()
            
            # Verificar limite de emergência
            if memory.percent > self.memory_management["emergency_limit"]:
                print(f"🚨 MEMÓRIA CRÍTICA: {memory.percent:.1f}% (limite emergência: {self.memory_management['emergency_limit']}%)")
                return False
            
            # Verificar limite dinâmico atual
            if memory.percent > self.resource_limits["max_memory_percent"]:
                print(f"⚠️ Memória alta: {memory.percent:.1f}% (limite dinâmico: {self.resource_limits['max_memory_percent']}%)")
                return False
            
            # Verificar temperatura (se disponível)
            try:
                temps = get_system_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current and entry.current > self.resource_limits["max_gpu_temp"]:
                                self.temperature_warnings += 1
                                print(f"🔥 TEMPERATURA ALTA: {entry.label or name}: {entry.current}°C")
                                if self.temperature_warnings > 3:
                                    print("🛑 MUITOS AVISOS DE TEMPERATURA - PAUSANDO CONVERSÕES")
                                    return False
                                return False
            except:
                pass  # Sensores de temperatura podem não estar disponíveis
            
            return True
            
        except ImportError:
            print("⚠️ psutil não disponível - usando verificação básica")
            return True
        except Exception as e:
            print(f"⚠️ Erro ao verificar recursos: {e}")
            return True  # Em caso de erro, permitir execução
    
    def _start_job(self, job: ConversionJob):
        """
        Inicia um trabalho específico
        """
        with self.lock:
            # Selecionar GPU
            job.assigned_gpu = self._select_optimal_gpu(job)

            # Criar thread de conversão
            job.thread = VideoConverter()
            job.thread.set_conversion_parameters(
                job.input_file,
                job.output_file,
                job.settings,
                self._create_job_callbacks(job),
            )

            # Atualizar status
            job.status = ConversionStatus.PROCESSING
            job.start_time = time.time()

            # Adicionar aos trabalhos ativos
            self.active_jobs[job.id] = job

            # Iniciar thread
            job.thread.start()

            # Callback de trabalho iniciado
            if self.global_callbacks.get("job_started"):
                self.global_callbacks["job_started"](self._job_to_dict(job))

    def _select_optimal_gpu(self, job: ConversionJob) -> GPUType:
        """
        Seleciona a GPU ótima para um trabalho baseado nas configurações
        """
        settings = job.settings
        format_name = settings.get("format", "").lower()

        # Tentar usar o sistema universal primeiro
        if self.universal_hardware and self.hardware_integration:
            try:
                # Obter recomendação do sistema universal
                codec_preference = None
                if "h.265" in format_name or "hevc" in format_name:
                    codec_preference = "h265"
                elif "h.264" in format_name or "avc" in format_name:
                    codec_preference = "h264"
                
                recommended_encoder = self.hardware_integration.get_recommended_encoder(codec_preference)
                
                # Mapear encoder para tipo de GPU
                if "nvenc" in recommended_encoder:
                    return GPUType.NVIDIA
                elif "qsv" in recommended_encoder:
                    return GPUType.INTEL
                elif "vaapi" in recommended_encoder:
                    return GPUType.INTEL  # Intel VAAPI
                else:
                    return GPUType.CPU
                    
            except Exception as e:
                print(f"[QueueManager] Erro ao selecionar GPU via sistema universal: {e}")

        # Fallback para o sistema antigo
        # Verificar preferências do perfil de hardware
        if self.hardware_profile.recommended_settings.get(
            "prefer_nvidia_for_hevc", False
        ):
            if "h.265" in format_name or "hevc" in format_name:
                if self.hardware_profile.nvidia_gpus:
                    return GPUType.NVIDIA

        if self.hardware_profile.recommended_settings.get(
            "prefer_intel_for_h264", False
        ):
            if "h.264" in format_name or "avc" in format_name:
                if self.hardware_profile.intel_gpu:
                    return GPUType.INTEL

        # Fallback para NVIDIA se disponível
        if self.hardware_profile.nvidia_gpus:
            return GPUType.NVIDIA
        elif self.hardware_profile.intel_gpu:
            return GPUType.INTEL
        else:
            return GPUType.CPU

    def _create_job_callbacks(self, job: ConversionJob) -> Dict[str, Callable]:
        """
        Cria callbacks específicos para um trabalho
        """

        def on_progress(progress):
            job.progress = progress
            # Chamar callback de progresso da GUI (corrigido: usar 'job_progress' em vez de 'job_status')
            if "job_progress" in job.callbacks:
                job.callbacks["job_progress"](job.id, progress)
            # Chamar callback global se disponível
            if "job_progress" in self.global_callbacks:
                self.global_callbacks["job_progress"](job.id, progress)

        def on_status(status):
            # Usar 'job_progress' para status também, já que a GUI não fornece 'job_status'
            if "job_progress" in job.callbacks:
                # Extrair porcentagem do status se possível
                import re

                match = re.search(r"(\d+)%", status)
                if match:
                    progress = int(match.group(1))
                    job.callbacks["job_progress"](job.id, progress)
            # Chamar callback global se disponível
            if "job_status" in self.global_callbacks:
                self.global_callbacks["job_status"](job.id, status)

        def on_finished(success, message):
            # Primeiro processar no queue manager (atualiza status, estatísticas, etc.)
            self._handle_job_completion(job, success, message)

            # Depois chamar callback individual da GUI com parâmetros adaptados
            if "job_finished" in job.callbacks:
                output_file = job.output_file if success else None
                job.callbacks["job_finished"](job.id, success, message, output_file)

        def on_log(message):
            if "log" in job.callbacks:
                job.callbacks["log"](message)
            # Chamar callback global se disponível
            if "log" in self.global_callbacks:
                self.global_callbacks["log"](message)

        return {
            "progress": on_progress,
            "status": on_status,
            "finished": on_finished,
            "log": on_log,
        }

    def _handle_job_completion(self, job: ConversionJob, success: bool, message: str):
        """
        Manipula a conclusão de um trabalho
        """
        with self.lock:
            job.end_time = time.time()

            if success:
                job.status = ConversionStatus.COMPLETED
                self.stats["completed_jobs"] += 1

                # Callback de trabalho concluído
                if self.global_callbacks.get("job_completed"):
                    self.global_callbacks["job_completed"](self._job_to_dict(job))

            else:
                # Verificar se deve tentar novamente
                should_retry = self._should_retry_job(job, message)

                if should_retry and job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.status = ConversionStatus.PENDING
                    job.progress = 0.0
                    job.assigned_gpu = None
                    job.thread = None

                    # Recolocar na fila
                    self.job_queue.put(job)
                else:
                    job.status = ConversionStatus.FAILED
                    job.error_message = message
                    self.stats["failed_jobs"] += 1

                    # Callback de trabalho falhado
                    if self.global_callbacks.get("job_failed"):
                        self.global_callbacks["job_failed"](self._job_to_dict(job))

            # Remover dos trabalhos ativos
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]

            # Adicionar aos concluídos
            self.completed_jobs.append(job)

            # Atualizar estatísticas de tempo
            if job.start_time and job.end_time:
                processing_time = job.end_time - job.start_time
                self.stats["total_processing_time"] += processing_time

            # Verificar se todos os jobs terminaram
            if len(self.active_jobs) == 0 and self.job_queue.empty():
                # Todos os jobs terminaram, chamar callback de fila finalizada
                self._notify_queue_finished()

            # Callback de atualização da fila
            self._notify_queue_updated()

    def _notify_queue_updated(self):
        """
        Dispara o callback global de atualização da fila, se definido.

        Comentário: centraliza a chamada para evitar duplicação por todo o arquivo.
        """
        try:
            if self.global_callbacks.get("queue_updated"):
                self.global_callbacks["queue_updated"](self.get_queue_status())
        except Exception as e:
            # Falha em callback não deve quebrar fluxo
            print(f"⚠️ Erro em callback 'queue_updated': {e}")

    def _notify_queue_finished(self):
        """
        Dispara o callback global de fila finalizada, se definido.

        Comentário: concentra a lógica de cálculo e notificação.
        """
        try:
            if self.global_callbacks.get("queue_finished"):
                total_jobs = self.stats["completed_jobs"] + self.stats["failed_jobs"]
                successful_jobs = self.stats["completed_jobs"]
                failed_jobs = self.stats["failed_jobs"]
                self.global_callbacks["queue_finished"](
                    total_jobs, successful_jobs, failed_jobs
                )
        except Exception as e:
            print(f"⚠️ Erro em callback 'queue_finished': {e}")

    def _should_retry_job(self, job: ConversionJob, error_message: str) -> bool:
        """
        Determina se um trabalho deve ser tentado novamente baseado no erro
        """
        error_lower = error_message.lower()

        for error_type, should_retry in self.retry_rules.items():
            if error_type.replace("_", " ") in error_lower:
                return should_retry

        # Default: não tentar novamente
        return False

    def get_hd_thermal_status(self) -> Dict[str, Any]:
        """
        Retorna o status térmico atual dos HDs/SSDs
        
        Returns:
            Dict contendo informações térmicas dos discos
        """
        # Helper interno para montar o dicionário de status térmico de forma padronizada
        def _build_hd_thermal_info(
            monitoring_enabled: bool,
            status: str,
            temperatures: Optional[Dict[str, Any]] = None,
            max_temperature: Optional[float] = None,
            paused: Optional[bool] = None,
            last_check: Optional[Any] = None,
            error: Optional[str] = None,
        ) -> Dict[str, Any]:
            """
            Constrói um dicionário de informações térmicas com chaves padronizadas.

            Args:
                monitoring_enabled: Se o monitoramento está habilitado
                status: Estado atual do monitoramento ('ok', 'warning', 'critical', 'disabled', 'error')
                temperatures: Mapa de temperaturas por drive
                max_temperature: Temperatura máxima observada
                paused: Se proteção térmica está pausando conversões
                last_check: Timestamp/indicador da última checagem
                error: Mensagem de erro, quando aplicável

            Returns:
                dict: Estrutura padronizada de informações térmicas
            """
            info: Dict[str, Any] = {
                "monitoring_enabled": monitoring_enabled,
                "status": status,
                "temperatures": temperatures or {},
                "max_temperature": max_temperature,
                "warning_threshold": HARDWARE_MONITORING.get("hd_temp_warning_threshold", 50),
                "critical_threshold": HARDWARE_MONITORING.get("hd_temp_critical_threshold", 60),
            }

            # Campos opcionais preservando formato atual
            if paused is not None:
                info["paused"] = paused
            if last_check is not None:
                info["last_check"] = last_check
            if error is not None:
                info["error"] = error

            # Cálculo de proteção térmica ativa apenas quando monitoramento habilitado
            thermal_active = False
            if monitoring_enabled and status not in ("disabled", "error"):
                thermal_active = bool(paused) or status in ["warning", "critical"]

            info["thermal_protection_active"] = thermal_active
            return info

        if not self.hd_thermal_monitoring or not self.hd_thermal_detector:
            return _build_hd_thermal_info(
                monitoring_enabled=False,
                status="disabled",
                temperatures={},
                max_temperature=None,
            )
        
        try:
            # get_hd_temperatures retorna um dict de temperaturas por drive
            temperatures = self.hd_thermal_detector.get_hd_temperatures()
            max_temp = 0
            
            if temperatures and isinstance(temperatures, dict):
                # Encontrar a temperatura máxima
                for drive_info in temperatures.values():
                    temp = drive_info.get("temperature")
                    if temp is not None and temp > max_temp:
                        max_temp = temp
            
            return _build_hd_thermal_info(
                monitoring_enabled=True,
                status=self.hd_thermal_status,
                temperatures=temperatures,
                max_temperature=(max_temp if max_temp > 0 else None),
                paused=self.hd_thermal_paused,
                last_check=self.hd_thermal_last_check,
            )
            
        except Exception as e:
            return _build_hd_thermal_info(
                monitoring_enabled=True,
                status="error",
                error=str(e),
                temperatures={},
                max_temperature=None,
            )

    def is_hd_thermal_protection_active(self) -> bool:
        """
        Verifica se a proteção térmica de HD está ativa (pausando conversões)
        
        Returns:
            bool: True se a proteção térmica está pausando conversões
        """
        return self.hd_thermal_paused
