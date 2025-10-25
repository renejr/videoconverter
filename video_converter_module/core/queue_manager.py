"""
Sistema de Gerenciamento de Fila de Conversões
Gerencia múltiplas conversões simultâneas com balanceamento de carga entre GPUs
"""

import threading
import queue
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

from video_converter_module.utils.hardware_detector import get_hardware_detector
from .video_converter import VideoConverter


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


class ConversionQueueManager:
    """
    Gerenciador principal da fila de conversões com balanceamento de carga
    """

    def __init__(self):
        # Componentes principais
        self.hardware_detector = get_hardware_detector()
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

        # Configurações adaptáveis
        self.max_concurrent = self.hardware_profile.max_concurrent_jobs
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
        # Usar o detector existente
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
        return {
            "profile_type": self.hardware_profile.profile_type,
            "max_concurrent_jobs": self.hardware_profile.max_concurrent_jobs,
            "nvidia_gpus": self.hardware_profile.nvidia_gpus,
            "intel_gpu": self.hardware_profile.intel_gpu,
            "total_vram": self.hardware_profile.total_vram,
            "recommended_settings": self.hardware_profile.recommended_settings,
        }

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

            # Callback de atualização da fila
            if self.global_callbacks.get("queue_updated"):
                self.global_callbacks["queue_updated"](self.get_queue_status())

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

                # Verificar se pode iniciar novos trabalhos
                with self.lock:
                    if len(self.active_jobs) >= self.max_concurrent:
                        time.sleep(0.5)
                        continue

                # Pegar próximo trabalho da fila
                try:
                    job = self.job_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # Iniciar trabalho
                self._start_job(job)

            except Exception as e:
                print(f"Erro no queue worker: {e}")
                time.sleep(1)

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
                if self.global_callbacks.get("queue_finished"):
                    total_jobs = (
                        self.stats["completed_jobs"] + self.stats["failed_jobs"]
                    )
                    successful_jobs = self.stats["completed_jobs"]
                    failed_jobs = self.stats["failed_jobs"]
                    self.global_callbacks["queue_finished"](
                        total_jobs, successful_jobs, failed_jobs
                    )

            # Callback de atualização da fila
            if self.global_callbacks.get("queue_updated"):
                self.global_callbacks["queue_updated"](self.get_queue_status())

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
