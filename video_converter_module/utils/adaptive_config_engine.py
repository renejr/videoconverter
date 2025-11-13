"""
Engine de Configuração Adaptativa
Ajusta automaticamente as configurações baseado no hardware detectado.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

from .universal_hardware_profiler import (
    UniversalHardwareProfiler, 
    HardwareProfile, 
    HardwareCapabilities,
    GPUInfo
)

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveSettings:
    """Configurações adaptativas geradas pelo engine"""
    profile_name: str
    hardware_profile: str
    timestamp: float
    
    # Configurações de GPU/CUDA
    use_hardware_acceleration: bool
    preferred_gpu_index: Optional[int]
    preferred_encoder: str
    preferred_decoder: str
    
    # Configurações de memória
    max_memory_usage: float
    prealloc_size: str
    max_alloc_size: str
    max_concurrent_streams: int
    enable_memory_pool: bool
    
    # Configurações de performance
    max_concurrent_jobs: int
    preset: str
    cq: Optional[int]
    crf: Optional[int]
    rc_mode: str
    
    # Configurações avançadas NVENC
    surfaces: Optional[int]
    async_depth: Optional[int]
    rc_lookahead: Optional[int]
    multipass: Optional[str]
    spatial_aq: bool
    temporal_aq: bool
    aq_strength: int
    
    # Configurações de fallback
    fallback_to_cpu: bool
    cpu_threads: int
    
    # Configurações de monitoramento
    enable_monitoring: bool
    monitoring_interval: int
    auto_adjust: bool


class AdaptiveConfigEngine:
    """
    Engine de configuração adaptativa que ajusta automaticamente
    as configurações baseado no hardware detectado.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa o engine de configuração adaptativa.
        
        Args:
            config_file: Arquivo para salvar/carregar configurações personalizadas
        """
        self.logger = logging.getLogger(__name__)
        self.profiler = UniversalHardwareProfiler()
        self.config_file = config_file
        self._current_settings = None
        self._last_update_time = 0
        self._update_interval = 60  # Atualizar a cada 60 segundos
        
        # Configurações personalizadas do usuário
        self._user_overrides = {}
        self._load_user_overrides()
        
    def get_adaptive_settings(self, force_refresh: bool = False) -> AdaptiveSettings:
        """
        Obtém configurações adaptativas baseadas no hardware atual.
        
        Args:
            force_refresh: Força nova detecção de hardware
            
        Returns:
            AdaptiveSettings otimizadas para o hardware atual
        """
        current_time = time.time()
        
        if (not force_refresh and 
            self._current_settings and 
            (current_time - self._last_update_time) < self._update_interval):
            return self._current_settings
            
        self.logger.info("Gerando configurações adaptativas...")
        
        # Obter capacidades de hardware
        capabilities = self.profiler.get_hardware_capabilities(force_refresh)
        
        # Gerar configurações base
        base_settings = self._generate_base_settings(capabilities)
        
        # Aplicar otimizações específicas
        optimized_settings = self._apply_optimizations(base_settings, capabilities)
        
        # Aplicar overrides do usuário
        final_settings = self._apply_user_overrides(optimized_settings)
        
        self._current_settings = final_settings
        self._last_update_time = current_time
        
        self.logger.info(f"Configurações geradas para perfil: {final_settings.hardware_profile}")
        return final_settings
    
    def _generate_base_settings(self, capabilities: HardwareCapabilities) -> AdaptiveSettings:
        """Gera configurações base baseadas nas capacidades de hardware"""
        
        recommended = capabilities.recommended_settings
        profile = capabilities.profile
        
        # Selecionar GPU primária se disponível
        primary_gpu = None
        if capabilities.gpus:
            primary_gpu = next((gpu for gpu in capabilities.gpus if gpu.is_primary), capabilities.gpus[0])
        
        # Configurações de memória
        memory_settings = recommended.get("memory_settings", {})
        
        # Configurações de qualidade
        quality_settings = recommended.get("quality_settings", {})
        
        # Configurações de performance
        performance_settings = recommended.get("performance_settings", {})
        
        return AdaptiveSettings(
            profile_name=f"adaptive_{profile.value}",
            hardware_profile=profile.value,
            timestamp=time.time(),
            
            # GPU/CUDA
            use_hardware_acceleration=recommended.get("use_hardware_acceleration", False),
            preferred_gpu_index=primary_gpu.index if primary_gpu else None,
            preferred_encoder=recommended.get("preferred_encoder", "libx264"),
            preferred_decoder=recommended.get("preferred_decoder", "h264"),
            
            # Memória
            max_memory_usage=memory_settings.get("max_memory_usage", 0.0),
            prealloc_size=memory_settings.get("prealloc_size", "64M"),
            max_alloc_size=memory_settings.get("max_alloc_size", "256M"),
            max_concurrent_streams=memory_settings.get("max_concurrent_streams", 2),
            enable_memory_pool=memory_settings.get("enable_memory_pool", False),
            
            # Performance
            max_concurrent_jobs=recommended.get("max_concurrent_jobs", 1),
            preset=quality_settings.get("preset", "medium"),
            cq=quality_settings.get("cq"),
            crf=quality_settings.get("crf"),
            rc_mode=quality_settings.get("rc_mode", "cbr"),
            
            # NVENC avançado
            surfaces=performance_settings.get("surfaces"),
            async_depth=performance_settings.get("async_depth"),
            rc_lookahead=performance_settings.get("rc_lookahead"),
            multipass=performance_settings.get("multipass"),
            spatial_aq=performance_settings.get("spatial_aq", True),
            temporal_aq=performance_settings.get("temporal_aq", True),
            aq_strength=performance_settings.get("aq_strength", 8),
            
            # Fallback
            fallback_to_cpu=True,
            cpu_threads=performance_settings.get("threads", capabilities.system.cpu_count),
            
            # Monitoramento
            enable_monitoring=profile != HardwareProfile.CPU_ONLY,
            monitoring_interval=30,
            auto_adjust=True
        )
    
    def _apply_optimizations(self, settings: AdaptiveSettings, capabilities: HardwareCapabilities) -> AdaptiveSettings:
        """Aplica otimizações específicas baseadas no hardware"""
        
        # Otimizações para múltiplas GPUs
        if len(capabilities.gpus) > 1:
            settings.max_concurrent_jobs = min(settings.max_concurrent_jobs * len(capabilities.gpus), 8)
            self.logger.info(f"Múltiplas GPUs detectadas: ajustando jobs para {settings.max_concurrent_jobs}")
        
        # Otimizações baseadas na RAM do sistema
        system_ram_gb = capabilities.system.ram_total_gb
        if system_ram_gb < 8:
            # Sistema com pouca RAM - reduzir concurrent jobs
            settings.max_concurrent_jobs = max(1, settings.max_concurrent_jobs // 2)
            settings.max_concurrent_streams = max(2, settings.max_concurrent_streams // 2)
            self.logger.info("RAM limitada detectada: reduzindo concurrent jobs")
        elif system_ram_gb > 32:
            # Sistema com muita RAM - pode aumentar concurrent jobs
            settings.max_concurrent_jobs = min(settings.max_concurrent_jobs + 2, 12)
            self.logger.info("RAM abundante detectada: aumentando concurrent jobs")
        
        # Otimizações baseadas na temperatura da GPU
        if capabilities.gpus:
            primary_gpu = next((gpu for gpu in capabilities.gpus if gpu.is_primary), capabilities.gpus[0])
            if primary_gpu.temperature and primary_gpu.temperature > 80:
                # GPU muito quente - reduzir carga
                settings.max_concurrent_jobs = max(1, settings.max_concurrent_jobs - 1)
                settings.max_memory_usage = max(0.5, settings.max_memory_usage - 0.1)
                self.logger.warning(f"GPU quente ({primary_gpu.temperature}°C): reduzindo carga")
        
        # Otimizações baseadas na utilização atual da GPU
        gpu_usage = self.profiler.monitor_gpu_usage()
        if gpu_usage and settings.preferred_gpu_index in gpu_usage:
            current_usage = gpu_usage[settings.preferred_gpu_index]
            if current_usage["utilization"] > 90:
                # GPU muito utilizada - reduzir concurrent jobs
                settings.max_concurrent_jobs = max(1, settings.max_concurrent_jobs - 1)
                self.logger.info("GPU altamente utilizada: reduzindo concurrent jobs")
        
        return settings
    
    def _apply_user_overrides(self, settings: AdaptiveSettings) -> AdaptiveSettings:
        """Aplica overrides personalizados do usuário"""
        
        if not self._user_overrides:
            return settings
            
        self.logger.info("Aplicando configurações personalizadas do usuário")
        
        # Aplicar overrides específicos do perfil
        profile_overrides = self._user_overrides.get(settings.hardware_profile, {})
        
        # Aplicar overrides globais
        global_overrides = self._user_overrides.get("global", {})
        
        # Combinar overrides (perfil específico tem prioridade)
        all_overrides = {**global_overrides, **profile_overrides}
        
        # Aplicar overrides aos settings
        for key, value in all_overrides.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
                self.logger.debug(f"Override aplicado: {key} = {value}")
        
        return settings
    
    def set_user_override(self, profile: Optional[str], setting_name: str, value: Any):
        """
        Define um override personalizado do usuário.
        
        Args:
            profile: Perfil específico ou None para global
            setting_name: Nome da configuração
            value: Valor da configuração
        """
        profile_key = profile or "global"
        
        if profile_key not in self._user_overrides:
            self._user_overrides[profile_key] = {}
            
        self._user_overrides[profile_key][setting_name] = value
        self._save_user_overrides()
        
        # Forçar atualização das configurações
        self._current_settings = None
        
        self.logger.info(f"Override definido: {profile_key}.{setting_name} = {value}")
    
    def remove_user_override(self, profile: Optional[str], setting_name: str):
        """Remove um override personalizado do usuário"""
        profile_key = profile or "global"
        
        if profile_key in self._user_overrides and setting_name in self._user_overrides[profile_key]:
            del self._user_overrides[profile_key][setting_name]
            
            # Remover perfil se vazio
            if not self._user_overrides[profile_key]:
                del self._user_overrides[profile_key]
                
            self._save_user_overrides()
            
            # Forçar atualização das configurações
            self._current_settings = None
            
            self.logger.info(f"Override removido: {profile_key}.{setting_name}")
    
    def get_user_overrides(self) -> Dict[str, Dict[str, Any]]:
        """Retorna todos os overrides personalizados do usuário"""
        return self._user_overrides.copy()
    
    def _load_user_overrides(self):
        """Carrega overrides personalizados do arquivo"""
        if not self.config_file:
            return
            
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._user_overrides = json.load(f)
                self.logger.info(f"Configurações personalizadas carregadas de {self.config_file}")
        except Exception as e:
            self.logger.warning(f"Erro ao carregar configurações personalizadas: {e}")
            self._user_overrides = {}
    
    def _save_user_overrides(self):
        """Salva overrides personalizados no arquivo"""
        if not self.config_file:
            return
            
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._user_overrides, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Configurações personalizadas salvas em {self.config_file}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar configurações personalizadas: {e}")
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """Retorna um resumo das configurações atuais"""
        settings = self.get_adaptive_settings()
        capabilities = self.profiler.get_hardware_capabilities()
        
        return {
            "hardware_profile": settings.hardware_profile,
            "gpu_count": len(capabilities.gpus),
            "primary_gpu": capabilities.gpus[0].name if capabilities.gpus else "Nenhuma",
            "total_vram_gb": sum(gpu.memory_total_mb for gpu in capabilities.gpus) / 1024,
            "system_ram_gb": capabilities.system.ram_total_gb,
            "use_hardware_acceleration": settings.use_hardware_acceleration,
            "max_concurrent_jobs": settings.max_concurrent_jobs,
            "preferred_encoder": settings.preferred_encoder,
            "max_memory_usage": settings.max_memory_usage,
            "preset": settings.preset,
            "user_overrides_count": sum(len(overrides) for overrides in self._user_overrides.values())
        }
    
    def export_settings_to_dict(self) -> Dict[str, Any]:
        """Exporta as configurações atuais para um dicionário"""
        settings = self.get_adaptive_settings()
        return asdict(settings)
    
    def validate_settings(self, settings: AdaptiveSettings) -> List[str]:
        """
        Valida as configurações e retorna lista de avisos/erros.
        
        Returns:
            Lista de mensagens de validação
        """
        warnings = []
        
        # Validar configurações de memória
        if settings.use_hardware_acceleration:
            if settings.max_memory_usage > 0.9:
                warnings.append("Uso de memória muito alto (>90%) pode causar instabilidade")
            
            if settings.max_concurrent_jobs > 8:
                warnings.append("Muitos jobs concorrentes podem sobrecarregar o sistema")
        
        # Validar configurações de GPU
        capabilities = self.profiler.get_hardware_capabilities()
        if settings.preferred_gpu_index is not None:
            if not any(gpu.index == settings.preferred_gpu_index for gpu in capabilities.gpus):
                warnings.append(f"GPU {settings.preferred_gpu_index} não encontrada")
        
        # Validar configurações de qualidade
        if settings.cq and (settings.cq < 10 or settings.cq > 51):
            warnings.append("Valor CQ fora da faixa recomendada (10-51)")
            
        if settings.crf and (settings.crf < 10 or settings.crf > 51):
            warnings.append("Valor CRF fora da faixa recomendada (10-51)")
        
        return warnings