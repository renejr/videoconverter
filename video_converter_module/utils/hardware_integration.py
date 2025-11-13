"""
Integração do Sistema Universal de Hardware
Conecta o novo sistema universal com o código existente do projeto.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from .universal_hardware_manager import get_hardware_manager

logger = logging.getLogger(__name__)


class HardwareIntegration:
    """
    Classe de integração que adapta o sistema universal
    para trabalhar com o código existente do projeto.
    """
    
    def __init__(self):
        self.manager = get_hardware_manager()
        self._initialized = False
        self.logger = logging.getLogger(__name__)
    
    def initialize_for_project(self) -> Dict[str, Any]:
        """
        Inicializa o sistema de hardware para o projeto.
        
        Returns:
            Configurações adaptadas para o projeto existente
        """
        if not self._initialized:
            summary = self.manager.initialize()
            self._initialized = True
            self.logger.info("Sistema de hardware integrado ao projeto")
            return summary
        
        return self.manager.get_hardware_status()
    
    def get_config_for_video_converter(self, 
                                     video_size_mb: int = 0,
                                     target_quality: str = "balanced") -> Dict[str, Any]:
        """
        Obtém configurações otimizadas para o video_converter.py
        
        Args:
            video_size_mb: Tamanho estimado do vídeo em MB
            target_quality: Qualidade alvo (speed, balanced, quality)
            
        Returns:
            Configurações no formato esperado pelo video_converter.py
        """
        if not self._initialized:
            self.initialize_for_project()
        
        # Estimar memória necessária baseado no tamanho do vídeo
        estimated_memory = max(512, min(video_size_mb * 2, 4096))
        
        # Obter configurações otimizadas
        settings = self.manager.get_optimal_settings_for_task(
            task_type="video_conversion",
            estimated_memory_mb=estimated_memory,
            priority=target_quality
        )
        
        # Adaptar para o formato esperado pelo video_converter.py
        return {
            "gpu_index": settings.get("gpu_index", 0),
            "encoder": settings.get("encoder", "libx264"),
            "decoder": settings.get("decoder", "auto"),
            "preset": settings.get("preset", "medium"),
            "cq": settings.get("cq", 23),
            "crf": settings.get("crf", 23),
            "rc_mode": settings.get("rc_mode", "vbr"),
            "max_memory_usage": settings.get("max_memory_usage", 0.7),
            "prealloc_size": settings.get("prealloc_size", "256M"),
            "max_alloc_size": settings.get("max_alloc_size", "1G"),
            "surfaces": settings.get("surfaces", 16),
            "async_depth": settings.get("async_depth", 8),
            "rc_lookahead": settings.get("rc_lookahead", 32),
            "multipass": settings.get("multipass", "qres"),
            "spatial_aq": settings.get("spatial_aq", True),
            "temporal_aq": settings.get("temporal_aq", True),
            "aq_strength": settings.get("aq_strength", 8),
            "fallback_to_cpu": settings.get("fallback_to_cpu", True),
            "cpu_threads": settings.get("cpu_threads", 0),
        }
    
    def get_config_for_queue_manager(self) -> Dict[str, Any]:
        """
        Obtém configurações otimizadas para o queue_manager.py
        
        Returns:
            Configurações no formato esperado pelo queue_manager.py
        """
        if not self._initialized:
            self.initialize_for_project()
        
        settings = self.manager.get_optimal_settings_for_task(
            task_type="batch_processing",
            priority="balanced"
        )
        
        status = self.manager.get_hardware_status()
        
        # Adaptar para o formato esperado pelo queue_manager.py
        return {
            "max_concurrent_jobs": settings.get("max_concurrent_jobs", 2),
            "gpu_memory_threshold": 0.85,  # 85% da VRAM
            "cpu_fallback_enabled": settings.get("fallback_to_cpu", True),
            "preferred_gpu_index": settings.get("gpu_index", 0),
            "enable_gpu_switching": True,
            "temperature_limit": 85,  # °C
            "memory_cleanup_interval": 300,  # 5 minutos
            "profile_type": status.get("hardware_profile", "mid_range"),
        }
    
    def get_ffmpeg_args_for_hardware(self, 
                                   codec: str = "h264",
                                   quality_preset: str = "balanced") -> Tuple[list, list]:
        """
        Gera argumentos do FFmpeg otimizados para o hardware atual.
        
        Args:
            codec: Codec desejado (h264, h265, av1)
            quality_preset: Preset de qualidade (speed, balanced, quality)
            
        Returns:
            Tupla com (input_args, output_args) para FFmpeg
        """
        if not self._initialized:
            self.initialize_for_project()
        
        config = self.get_config_for_video_converter(target_quality=quality_preset)
        
        input_args = []
        output_args = []
        
        # Configurações de entrada
        if config["decoder"] != "auto":
            input_args.extend(["-c:v", config["decoder"]])
        
        # Configurações de GPU
        if config["gpu_index"] >= 0:
            input_args.extend(["-hwaccel", "cuda"])
            input_args.extend(["-hwaccel_device", str(config["gpu_index"])])
        
        # Configurações de saída baseadas no codec
        encoder = self._get_encoder_for_codec(codec, config["encoder"])
        output_args.extend(["-c:v", encoder])
        
        # Configurações específicas do encoder
        if "nvenc" in encoder:
            output_args.extend(self._get_nvenc_args(config))
        elif encoder == "libx264":
            output_args.extend(self._get_x264_args(config))
        elif encoder == "libx265":
            output_args.extend(self._get_x265_args(config))
        
        return input_args, output_args
    
    def _get_encoder_for_codec(self, codec: str, preferred_encoder: str) -> str:
        """Determina o encoder baseado no codec e preferência"""
        codec_map = {
            "h264": {
                "nvenc": "h264_nvenc",
                "qsv": "h264_qsv",
                "cpu": "libx264"
            },
            "h265": {
                "nvenc": "hevc_nvenc", 
                "qsv": "hevc_qsv",
                "cpu": "libx265"
            },
            "av1": {
                "nvenc": "av1_nvenc",
                "cpu": "libsvtav1"
            }
        }
        
        if codec in codec_map:
            # Tentar usar o encoder preferido
            if "nvenc" in preferred_encoder and "nvenc" in codec_map[codec]:
                return codec_map[codec]["nvenc"]
            elif "qsv" in preferred_encoder and "qsv" in codec_map[codec]:
                return codec_map[codec]["qsv"]
            else:
                return codec_map[codec]["cpu"]
        
        return "libx264"  # Fallback padrão
    
    def _get_nvenc_args(self, config: Dict[str, Any]) -> list:
        """Gera argumentos específicos para NVENC"""
        args = []
        
        # Preset
        args.extend(["-preset", config["preset"]])
        
        # Rate control
        if config["rc_mode"] == "cq":
            args.extend(["-rc", "constqp", "-cq", str(config["cq"])])
        elif config["rc_mode"] == "vbr":
            args.extend(["-rc", "vbr"])
        else:
            args.extend(["-rc", "cbr"])
        
        # Configurações avançadas
        if config.get("surfaces"):
            args.extend(["-surfaces", str(config["surfaces"])])
        
        if config.get("async_depth"):
            args.extend(["-async_depth", str(config["async_depth"])])
        
        if config.get("rc_lookahead"):
            args.extend(["-rc_lookahead", str(config["rc_lookahead"])])
        
        if config.get("multipass"):
            args.extend(["-multipass", config["multipass"]])
        
        if config.get("spatial_aq"):
            args.extend(["-spatial_aq", "1"])
        
        if config.get("temporal_aq"):
            args.extend(["-temporal_aq", "1"])
        
        if config.get("aq_strength"):
            args.extend(["-aq_strength", str(config["aq_strength"])])
        
        return args
    
    def _get_x264_args(self, config: Dict[str, Any]) -> list:
        """Gera argumentos específicos para x264"""
        args = []
        
        # Preset
        args.extend(["-preset", config["preset"]])
        
        # CRF
        args.extend(["-crf", str(config["crf"])])
        
        # Threads
        if config.get("cpu_threads", 0) > 0:
            args.extend(["-threads", str(config["cpu_threads"])])
        
        return args
    
    def _get_x265_args(self, config: Dict[str, Any]) -> list:
        """Gera argumentos específicos para x265"""
        args = []
        
        # Preset
        args.extend(["-preset", config["preset"]])
        
        # CRF
        args.extend(["-crf", str(config["crf"])])
        
        # Threads
        if config.get("cpu_threads", 0) > 0:
            args.extend(["-x265-params", f"threads={config['cpu_threads']}"])
        
        return args
    
    def should_use_gpu_for_task(self, estimated_memory_mb: int = 0) -> bool:
        """
        Determina se deve usar GPU para uma tarefa específica.
        
        Args:
            estimated_memory_mb: Memória estimada necessária
            
        Returns:
            True se deve usar GPU, False para usar CPU
        """
        if not self._initialized:
            self.initialize_for_project()
        
        status = self.manager.get_hardware_status()
        
        # Verificar se há GPU disponível
        if status.get("gpu_count", 0) == 0:
            return False
        
        # Verificar se CUDA está disponível
        if not status.get("cuda_available", False):
            return False
        
        # Verificar memória disponível
        if "primary_gpu" in status:
            gpu = status["primary_gpu"]
            available_memory = gpu.get("memory_free_mb", 0)
            
            # Deixar uma margem de segurança
            required_memory = estimated_memory_mb * 1.5
            
            if available_memory < required_memory:
                self.logger.warning(f"Memória GPU insuficiente: {available_memory}MB disponível, {required_memory}MB necessário")
                return False
        
        return True
    
    def get_optimal_concurrent_jobs(self) -> int:
        """
        Retorna o número otimal de jobs concorrentes baseado no hardware.
        
        Returns:
            Número de jobs concorrentes recomendado
        """
        if not self._initialized:
            self.initialize_for_project()
        
        config = self.get_config_for_queue_manager()
        return config.get("max_concurrent_jobs", 2)
    
    def get_memory_usage_limits(self) -> Dict[str, float]:
        """
        Retorna limites de uso de memória baseados no hardware.
        
        Returns:
            Dicionário com limites de memória
        """
        if not self._initialized:
            self.initialize_for_project()
        
        config = self.get_config_for_video_converter()
        
        return {
            "gpu_memory_usage": config.get("max_memory_usage", 0.7),
            "gpu_memory_threshold": 0.85,
            "prealloc_size_mb": self._parse_memory_size(config.get("prealloc_size", "256M")),
            "max_alloc_size_mb": self._parse_memory_size(config.get("max_alloc_size", "1G")),
        }
    
    def _parse_memory_size(self, size_str: str) -> int:
        """Converte string de tamanho de memória para MB"""
        if isinstance(size_str, int):
            return size_str
        
        size_str = size_str.upper()
        if size_str.endswith("G"):
            return int(size_str[:-1]) * 1024
        elif size_str.endswith("M"):
            return int(size_str[:-1])
        else:
            return int(size_str)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas de performance do hardware atual.
        
        Returns:
            Dicionário com métricas de performance
        """
        if not self._initialized:
            self.initialize_for_project()
        
        status = self.manager.get_hardware_status()
        recommendations = self.manager.get_performance_recommendations()
        
        metrics = {
            "hardware_profile": status.get("hardware_profile", "unknown"),
            "gpu_count": status.get("gpu_count", 0),
            "cuda_available": status.get("cuda_available", False),
            "monitoring_enabled": status.get("monitoring_enabled", False),
            "recommendations_count": len(recommendations),
            "performance_score": self._calculate_performance_score(status),
        }
        
        if "primary_gpu" in status:
            gpu = status["primary_gpu"]
            metrics.update({
                "gpu_name": gpu.get("name", "Unknown"),
                "gpu_memory_total_gb": gpu.get("memory_total_mb", 0) / 1024,
                "gpu_memory_free_gb": gpu.get("memory_free_mb", 0) / 1024,
                "gpu_temperature": gpu.get("temperature", 0),
                "gpu_utilization": gpu.get("utilization", 0),
            })
        
        return metrics
    
    def _calculate_performance_score(self, status: Dict[str, Any]) -> int:
        """Calcula um score de performance baseado no hardware"""
        score = 0
        
        # Score baseado no perfil de hardware
        profile_scores = {
            "workstation": 100,
            "high_end": 85,
            "mid_range": 65,
            "entry_level": 45,
            "low_end": 25,
            "cpu_only": 10
        }
        
        profile = status.get("hardware_profile", "cpu_only")
        score += profile_scores.get(profile, 10)
        
        # Bonus por CUDA
        if status.get("cuda_available", False):
            score += 10
        
        # Bonus por múltiplas GPUs
        gpu_count = status.get("gpu_count", 0)
        if gpu_count > 1:
            score += min(gpu_count * 5, 20)
        
        return min(score, 100)


# Instância global para facilitar o uso
_integration_instance = None

def get_hardware_integration() -> HardwareIntegration:
    """
    Obtém a instância global da integração de hardware.
    
    Returns:
        Instância do HardwareIntegration
    """
    global _integration_instance
    
    if _integration_instance is None:
        _integration_instance = HardwareIntegration()
    
    return _integration_instance


# Funções de conveniência para uso direto
def initialize_hardware() -> Dict[str, Any]:
    """Inicializa o sistema de hardware"""
    return get_hardware_integration().initialize_for_project()


def get_video_converter_config(video_size_mb: int = 0, quality: str = "balanced") -> Dict[str, Any]:
    """Obtém configurações para o video converter"""
    return get_hardware_integration().get_config_for_video_converter(video_size_mb, quality)


def get_queue_manager_config() -> Dict[str, Any]:
    """Obtém configurações para o queue manager"""
    return get_hardware_integration().get_config_for_queue_manager()


def get_ffmpeg_args(codec: str = "h264", quality: str = "balanced") -> Tuple[list, list]:
    """Obtém argumentos do FFmpeg otimizados"""
    return get_hardware_integration().get_ffmpeg_args_for_hardware(codec, quality)


def should_use_gpu(estimated_memory_mb: int = 0) -> bool:
    """Determina se deve usar GPU"""
    return get_hardware_integration().should_use_gpu_for_task(estimated_memory_mb)


def get_concurrent_jobs() -> int:
    """Obtém número otimal de jobs concorrentes"""
    return get_hardware_integration().get_optimal_concurrent_jobs()


def get_memory_limits() -> Dict[str, float]:
    """Obtém limites de memória"""
    return get_hardware_integration().get_memory_usage_limits()


def get_performance_info() -> Dict[str, Any]:
    """Obtém informações de performance"""
    return get_hardware_integration().get_performance_metrics()