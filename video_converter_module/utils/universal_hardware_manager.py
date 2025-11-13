"""
Gerenciador Universal de Hardware
Integra todos os sistemas de detecção, configuração e monitoramento de hardware.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

from .universal_hardware_profiler import UniversalHardwareProfiler, HardwareCapabilities
from .adaptive_config_engine import AdaptiveConfigEngine, AdaptiveSettings
from .dynamic_monitor import DynamicMonitor, MonitoringEvent

logger = logging.getLogger(__name__)


class UniversalHardwareManager:
    """
    Gerenciador universal que integra detecção de hardware,
    configuração adaptativa e monitoramento dinâmico.
    """
    
    def __init__(self, config_dir: Optional[str] = None, enable_monitoring: bool = True):
        """
        Inicializa o gerenciador universal de hardware.
        
        Args:
            config_dir: Diretório para salvar configurações personalizadas
            enable_monitoring: Se deve habilitar monitoramento dinâmico
        """
        self.logger = logging.getLogger(__name__)
        
        # Configurar diretório de configurações
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Usar diretório padrão no projeto
            self.config_dir = Path(__file__).parent.parent / "config" / "hardware"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar componentes
        self.profiler = UniversalHardwareProfiler()
        
        config_file = self.config_dir / "user_overrides.json"
        self.config_engine = AdaptiveConfigEngine(str(config_file))
        
        self.monitor = None
        if enable_monitoring:
            self.monitor = DynamicMonitor(self.config_engine)
            self._setup_monitoring_callbacks()
        
        # Estado do gerenciador
        self._initialized = False
        self._current_capabilities = None
        self._current_settings = None
        
        self.logger.info("Gerenciador Universal de Hardware inicializado")
    
    def initialize(self, force_detection: bool = False) -> Dict[str, Any]:
        """
        Inicializa o sistema detectando hardware e gerando configurações.
        
        Args:
            force_detection: Força nova detecção de hardware
            
        Returns:
            Resumo da inicialização
        """
        self.logger.info("Inicializando sistema de hardware...")
        
        try:
            # Detectar capacidades de hardware
            self._current_capabilities = self.profiler.get_hardware_capabilities(force_detection)
            
            # Gerar configurações adaptativas
            self._current_settings = self.config_engine.get_adaptive_settings(force_detection)
            
            # Iniciar monitoramento se habilitado
            if self.monitor and self._current_settings.enable_monitoring:
                self.monitor.start_monitoring()
            
            self._initialized = True
            
            # Gerar resumo
            summary = self._generate_initialization_summary()
            
            self.logger.info(f"Sistema inicializado: {summary['hardware_profile']} com {summary['gpu_count']} GPU(s)")
            return summary
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização: {e}")
            raise
    
    def get_optimal_settings_for_task(self, 
                                    task_type: str = "video_conversion",
                                    estimated_memory_mb: int = 0,
                                    priority: str = "balanced") -> Dict[str, Any]:
        """
        Obtém configurações otimizadas para uma tarefa específica.
        
        Args:
            task_type: Tipo da tarefa (video_conversion, image_processing, etc.)
            estimated_memory_mb: Memória estimada necessária
            priority: Prioridade (speed, quality, balanced)
            
        Returns:
            Configurações otimizadas para a tarefa
        """
        if not self._initialized:
            self.initialize()
        
        # Obter configurações base
        base_settings = self.config_engine.get_adaptive_settings()
        
        # Selecionar GPU otimal para a tarefa
        optimal_gpu = self.profiler.get_optimal_gpu_for_task(estimated_memory_mb)
        
        # Ajustar configurações baseado na tarefa e prioridade
        task_settings = self._adjust_settings_for_task(
            base_settings, task_type, priority, optimal_gpu
        )
        
        return {
            "encoder": task_settings.preferred_encoder,
            "decoder": task_settings.preferred_decoder,
            "gpu_index": task_settings.preferred_gpu_index,
            "preset": task_settings.preset,
            "cq": task_settings.cq,
            "crf": task_settings.crf,
            "rc_mode": task_settings.rc_mode,
            "max_memory_usage": task_settings.max_memory_usage,
            "prealloc_size": task_settings.prealloc_size,
            "max_alloc_size": task_settings.max_alloc_size,
            "surfaces": task_settings.surfaces,
            "async_depth": task_settings.async_depth,
            "rc_lookahead": task_settings.rc_lookahead,
            "multipass": task_settings.multipass,
            "spatial_aq": task_settings.spatial_aq,
            "temporal_aq": task_settings.temporal_aq,
            "aq_strength": task_settings.aq_strength,
            "fallback_to_cpu": task_settings.fallback_to_cpu,
            "cpu_threads": task_settings.cpu_threads,
        }
    
    def _adjust_settings_for_task(self, 
                                base_settings: AdaptiveSettings,
                                task_type: str,
                                priority: str,
                                optimal_gpu: Optional[Any]) -> AdaptiveSettings:
        """Ajusta configurações baseado no tipo de tarefa e prioridade"""
        
        # Criar cópia das configurações
        import copy
        settings = copy.deepcopy(base_settings)
        
        # Ajustar GPU se uma específica foi selecionada
        if optimal_gpu:
            settings.preferred_gpu_index = optimal_gpu.index
        
        # Ajustes baseados na prioridade
        if priority == "speed":
            # Priorizar velocidade
            settings.preset = "fast"
            if settings.cq:
                settings.cq = min(settings.cq + 3, 35)  # Qualidade menor para mais velocidade
            settings.rc_mode = "cbr"  # CBR é mais rápido
            
        elif priority == "quality":
            # Priorizar qualidade
            settings.preset = "slow"
            if settings.cq:
                settings.cq = max(settings.cq - 3, 15)  # Qualidade maior
            settings.rc_mode = "vbr"  # VBR para melhor qualidade
            if settings.rc_lookahead:
                settings.rc_lookahead = min(settings.rc_lookahead + 16, 64)
        
        # Ajustes baseados no tipo de tarefa
        if task_type == "video_conversion":
            # Configurações padrão já são otimizadas para conversão de vídeo
            pass
            
        elif task_type == "streaming":
            # Otimizar para streaming (baixa latência)
            settings.preset = "fast"
            settings.rc_mode = "cbr"
            if settings.async_depth:
                settings.async_depth = max(settings.async_depth // 2, 2)
            if settings.rc_lookahead:
                settings.rc_lookahead = max(settings.rc_lookahead // 2, 8)
                
        elif task_type == "batch_processing":
            # Otimizar para processamento em lote
            settings.max_concurrent_jobs = min(settings.max_concurrent_jobs + 1, 8)
            if settings.surfaces:
                settings.surfaces = min(settings.surfaces + 8, 32)
        
        return settings
    
    def get_hardware_status(self) -> Dict[str, Any]:
        """Retorna status atual do hardware"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        # Status básico
        status = {
            "initialized": self._initialized,
            "hardware_profile": self._current_capabilities.profile.value,
            "gpu_count": len(self._current_capabilities.gpus),
            "cuda_available": self._current_capabilities.cuda_available,
            "monitoring_enabled": self.monitor is not None and self.monitor._running,
        }
        
        # Informações das GPUs
        if self._current_capabilities.gpus:
            primary_gpu = next(
                (gpu for gpu in self._current_capabilities.gpus if gpu.is_primary),
                self._current_capabilities.gpus[0]
            )
            status.update({
                "primary_gpu": {
                    "name": primary_gpu.name,
                    "memory_total_mb": primary_gpu.memory_total_mb,
                    "memory_free_mb": primary_gpu.memory_free_mb,
                    "temperature": primary_gpu.temperature,
                    "utilization": primary_gpu.utilization,
                }
            })
        
        # Status do monitoramento
        if self.monitor:
            monitor_status = self.monitor.get_current_status()
            status["monitoring"] = monitor_status
        
        return status
    
    def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Retorna recomendações de performance baseadas no hardware atual"""
        if not self._initialized:
            return [{"type": "error", "message": "Sistema não inicializado"}]
        
        recommendations = []
        
        # Validar configurações atuais
        warnings = self.config_engine.validate_settings(self._current_settings)
        for warning in warnings:
            recommendations.append({
                "type": "warning",
                "category": "configuration",
                "message": warning
            })
        
        # Analisar capacidades de hardware
        capabilities = self._current_capabilities
        
        # Recomendações baseadas no perfil de hardware
        if capabilities.profile.value == "cpu_only":
            recommendations.append({
                "type": "info",
                "category": "hardware",
                "message": "Considere adicionar uma GPU para melhor performance"
            })
        
        elif capabilities.profile.value in ["low_end", "entry_level"]:
            recommendations.append({
                "type": "tip",
                "category": "settings",
                "message": "Use preset 'fast' para melhor performance com sua GPU"
            })
        
        # Recomendações baseadas na memória
        if capabilities.gpus:
            total_vram_gb = sum(gpu.memory_total_mb for gpu in capabilities.gpus) / 1024
            if total_vram_gb < 4:
                recommendations.append({
                    "type": "warning",
                    "category": "memory",
                    "message": "VRAM limitada pode afetar conversões de vídeos grandes"
                })
            elif total_vram_gb > 8:
                recommendations.append({
                    "type": "tip",
                    "category": "performance",
                    "message": "Sua GPU tem VRAM abundante - considere aumentar concurrent jobs"
                })
        
        # Recomendações baseadas no monitoramento
        if self.monitor and self.monitor._monitoring_history:
            latest_data = self.monitor._monitoring_history[-1]
            
            if latest_data.avg_gpu_utilization < 30:
                recommendations.append({
                    "type": "tip",
                    "category": "utilization",
                    "message": "GPU subutilizada - considere aumentar concurrent jobs"
                })
            elif latest_data.avg_gpu_utilization > 95:
                recommendations.append({
                    "type": "warning",
                    "category": "utilization",
                    "message": "GPU muito utilizada - considere reduzir concurrent jobs"
                })
        
        return recommendations
    
    def set_user_preference(self, setting_name: str, value: Any, profile: Optional[str] = None):
        """Define uma preferência personalizada do usuário"""
        self.config_engine.set_user_override(profile, setting_name, value)
        self.logger.info(f"Preferência definida: {setting_name} = {value}")
    
    def remove_user_preference(self, setting_name: str, profile: Optional[str] = None):
        """Remove uma preferência personalizada do usuário"""
        self.config_engine.remove_user_override(profile, setting_name)
        self.logger.info(f"Preferência removida: {setting_name}")
    
    def get_user_preferences(self) -> Dict[str, Dict[str, Any]]:
        """Retorna todas as preferências personalizadas do usuário"""
        return self.config_engine.get_user_overrides()
    
    def enable_monitoring(self):
        """Habilita o monitoramento dinâmico"""
        if not self.monitor:
            self.monitor = DynamicMonitor(self.config_engine)
            self._setup_monitoring_callbacks()
        
        if not self.monitor._running:
            self.monitor.start_monitoring()
            self.logger.info("Monitoramento dinâmico habilitado")
    
    def disable_monitoring(self):
        """Desabilita o monitoramento dinâmico"""
        if self.monitor and self.monitor._running:
            self.monitor.stop_monitoring()
            self.logger.info("Monitoramento dinâmico desabilitado")
    
    def _setup_monitoring_callbacks(self):
        """Configura callbacks para eventos de monitoramento"""
        if not self.monitor:
            return
        
        # Callback para eventos de temperatura alta
        def on_high_temperature(event, data):
            self.logger.warning(f"Temperatura alta detectada: {data.max_gpu_temperature}°C")
        
        # Callback para eventos de sobrecarga
        def on_gpu_overload(event, data):
            self.logger.warning(f"GPU sobrecarregada: {data.avg_gpu_utilization}% utilização")
        
        self.monitor.register_event_callback(MonitoringEvent.TEMPERATURE_HIGH, on_high_temperature)
        self.monitor.register_event_callback(MonitoringEvent.GPU_OVERLOAD, on_gpu_overload)
    
    def _generate_initialization_summary(self) -> Dict[str, Any]:
        """Gera resumo da inicialização"""
        return {
            "hardware_profile": self._current_capabilities.profile.value,
            "gpu_count": len(self._current_capabilities.gpus),
            "total_vram_gb": sum(gpu.memory_total_mb for gpu in self._current_capabilities.gpus) / 1024,
            "system_ram_gb": self._current_capabilities.system.ram_total_gb,
            "cuda_available": self._current_capabilities.cuda_available,
            "preferred_encoder": self._current_settings.preferred_encoder,
            "max_concurrent_jobs": self._current_settings.max_concurrent_jobs,
            "monitoring_enabled": self.monitor is not None and self.monitor._running,
            "config_dir": str(self.config_dir),
        }
    
    def export_configuration(self, file_path: str):
        """Exporta a configuração atual para um arquivo"""
        if not self._initialized:
            raise RuntimeError("Sistema não inicializado")
        
        config_data = {
            "hardware_capabilities": {
                "profile": self._current_capabilities.profile.value,
                "gpu_count": len(self._current_capabilities.gpus),
                "total_vram_mb": sum(gpu.memory_total_mb for gpu in self._current_capabilities.gpus),
                "system_ram_gb": self._current_capabilities.system.ram_total_gb,
                "cuda_available": self._current_capabilities.cuda_available,
            },
            "adaptive_settings": self.config_engine.export_settings_to_dict(),
            "user_preferences": self.get_user_preferences(),
            "performance_recommendations": self.get_performance_recommendations(),
        }
        
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Configuração exportada para {file_path}")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Retorna informações detalhadas para debug"""
        debug_info = {
            "manager_state": {
                "initialized": self._initialized,
                "config_dir": str(self.config_dir),
                "monitoring_enabled": self.monitor is not None,
            }
        }
        
        if self._initialized:
            debug_info.update({
                "hardware_capabilities": self._current_capabilities.__dict__ if self._current_capabilities else None,
                "current_settings": self._current_settings.__dict__ if self._current_settings else None,
                "hardware_status": self.get_hardware_status(),
            })
            
            if self.monitor:
                debug_info["monitoring_status"] = self.monitor.get_current_status()
                debug_info["recent_monitoring_data"] = self.monitor.get_monitoring_history(last_n=5)
                debug_info["recent_adjustments"] = self.monitor.get_adjustment_history(last_n=10)
        
        return debug_info
    
    def cleanup(self):
        """Limpa recursos e para todos os serviços"""
        self.logger.info("Limpando recursos do gerenciador de hardware...")
        
        if self.monitor:
            self.monitor.stop_monitoring()
        
        self._initialized = False
        self.logger.info("Recursos limpos")


# Instância global para facilitar o uso
_global_manager = None

def get_hardware_manager(config_dir: Optional[str] = None, enable_monitoring: bool = True) -> UniversalHardwareManager:
    """
    Obtém a instância global do gerenciador de hardware.
    
    Args:
        config_dir: Diretório de configurações (apenas na primeira chamada)
        enable_monitoring: Habilitar monitoramento (apenas na primeira chamada)
        
    Returns:
        Instância do UniversalHardwareManager
    """
    global _global_manager
    
    if _global_manager is None:
        _global_manager = UniversalHardwareManager(config_dir, enable_monitoring)
    
    return _global_manager