"""
Sistema de Monitoramento Dinâmico
Monitora o hardware em tempo real e ajusta configurações automaticamente.
"""

import threading
import time
import logging
import queue
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

from .universal_hardware_profiler import UniversalHardwareProfiler, GPUInfo
from .adaptive_config_engine import AdaptiveConfigEngine, AdaptiveSettings

logger = logging.getLogger(__name__)


class MonitoringEvent(Enum):
    """Tipos de eventos de monitoramento"""
    GPU_OVERLOAD = "gpu_overload"
    GPU_UNDERLOAD = "gpu_underload"
    MEMORY_PRESSURE = "memory_pressure"
    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_NORMAL = "temperature_normal"
    SYSTEM_OVERLOAD = "system_overload"
    SYSTEM_NORMAL = "system_normal"


@dataclass
class MonitoringData:
    """Dados de monitoramento coletados"""
    timestamp: float
    gpu_usage: Dict[int, Dict[str, Any]]
    system_memory_usage: float
    system_cpu_usage: float
    active_jobs: int
    queue_size: int
    
    # Métricas calculadas
    avg_gpu_utilization: float
    max_gpu_temperature: Optional[int]
    total_gpu_memory_used_mb: int
    total_gpu_memory_free_mb: int


@dataclass
class AdjustmentAction:
    """Ação de ajuste a ser executada"""
    setting_name: str
    old_value: Any
    new_value: Any
    reason: str
    priority: int  # 1=alta, 2=média, 3=baixa


class DynamicMonitor:
    """
    Sistema de monitoramento dinâmico que ajusta configurações
    automaticamente baseado na utilização do hardware.
    """
    
    def __init__(self, config_engine: AdaptiveConfigEngine, monitoring_interval: int = 30):
        """
        Inicializa o monitor dinâmico.
        
        Args:
            config_engine: Engine de configuração adaptativa
            monitoring_interval: Intervalo de monitoramento em segundos
        """
        self.logger = logging.getLogger(__name__)
        self.config_engine = config_engine
        self.profiler = UniversalHardwareProfiler()
        self.monitoring_interval = monitoring_interval
        
        # Estado do monitor
        self._running = False
        self._monitor_thread = None
        self._adjustment_thread = None
        
        # Filas de comunicação
        self._monitoring_queue = queue.Queue(maxsize=100)
        self._adjustment_queue = queue.Queue(maxsize=50)
        
        # Callbacks para eventos
        self._event_callbacks: Dict[MonitoringEvent, List[Callable]] = {}
        
        # Histórico de monitoramento
        self._monitoring_history: List[MonitoringData] = []
        self._max_history_size = 100
        
        # Configurações de limites
        self._thresholds = {
            "gpu_overload_threshold": 90,      # % utilização GPU
            "gpu_underload_threshold": 20,     # % utilização GPU
            "memory_pressure_threshold": 85,   # % memória GPU
            "temperature_high_threshold": 83,  # °C
            "temperature_normal_threshold": 75, # °C
            "cpu_overload_threshold": 90,      # % utilização CPU
            "adjustment_cooldown": 60,         # segundos entre ajustes
        }
        
        # Estado dos ajustes
        self._last_adjustment_time = 0
        self._adjustment_history: List[AdjustmentAction] = []
        
        # Métricas de performance
        self._performance_metrics = {
            "total_adjustments": 0,
            "successful_adjustments": 0,
            "failed_adjustments": 0,
            "monitoring_cycles": 0,
        }
    
    def start_monitoring(self):
        """Inicia o monitoramento dinâmico"""
        if self._running:
            self.logger.warning("Monitor já está em execução")
            return
            
        self.logger.info("Iniciando monitoramento dinâmico...")
        self._running = True
        
        # Iniciar thread de monitoramento
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="DynamicMonitor",
            daemon=True
        )
        self._monitor_thread.start()
        
        # Iniciar thread de ajustes
        self._adjustment_thread = threading.Thread(
            target=self._adjustment_loop,
            name="DynamicAdjustment",
            daemon=True
        )
        self._adjustment_thread.start()
        
        self.logger.info("Monitoramento dinâmico iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento dinâmico"""
        if not self._running:
            return
            
        self.logger.info("Parando monitoramento dinâmico...")
        self._running = False
        
        # Aguardar threads terminarem
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
            
        if self._adjustment_thread and self._adjustment_thread.is_alive():
            self._adjustment_thread.join(timeout=5)
            
        self.logger.info("Monitoramento dinâmico parado")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self._running:
            try:
                # Coletar dados de monitoramento
                monitoring_data = self._collect_monitoring_data()
                
                # Adicionar ao histórico
                self._add_to_history(monitoring_data)
                
                # Analisar dados e gerar eventos
                events = self._analyze_monitoring_data(monitoring_data)
                
                # Processar eventos
                for event in events:
                    self._process_monitoring_event(event, monitoring_data)
                
                # Adicionar dados à fila
                try:
                    self._monitoring_queue.put_nowait(monitoring_data)
                except queue.Full:
                    # Remover item mais antigo se fila estiver cheia
                    try:
                        self._monitoring_queue.get_nowait()
                        self._monitoring_queue.put_nowait(monitoring_data)
                    except queue.Empty:
                        pass
                
                self._performance_metrics["monitoring_cycles"] += 1
                
            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {e}")
            
            # Aguardar próximo ciclo
            time.sleep(self.monitoring_interval)
    
    def _adjustment_loop(self):
        """Loop de processamento de ajustes"""
        while self._running:
            try:
                # Aguardar ação de ajuste
                action = self._adjustment_queue.get(timeout=1)
                
                # Verificar cooldown
                current_time = time.time()
                if (current_time - self._last_adjustment_time) < self._thresholds["adjustment_cooldown"]:
                    self.logger.debug(f"Ajuste em cooldown: {action.setting_name}")
                    continue
                
                # Executar ajuste
                success = self._execute_adjustment(action)
                
                if success:
                    self._performance_metrics["successful_adjustments"] += 1
                    self._last_adjustment_time = current_time
                    self.logger.info(f"Ajuste executado: {action.setting_name} = {action.new_value} ({action.reason})")
                else:
                    self._performance_metrics["failed_adjustments"] += 1
                    self.logger.warning(f"Falha ao executar ajuste: {action.setting_name}")
                
                self._performance_metrics["total_adjustments"] += 1
                self._adjustment_history.append(action)
                
                # Manter histórico limitado
                if len(self._adjustment_history) > 50:
                    self._adjustment_history = self._adjustment_history[-50:]
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro no loop de ajustes: {e}")
    
    def _collect_monitoring_data(self) -> MonitoringData:
        """Coleta dados de monitoramento do sistema"""
        import psutil
        
        # Monitorar GPUs
        gpu_usage = self.profiler.monitor_gpu_usage()
        
        # Calcular métricas de GPU
        avg_gpu_utilization = 0
        max_gpu_temperature = None
        total_gpu_memory_used_mb = 0
        total_gpu_memory_free_mb = 0
        
        if gpu_usage:
            utilizations = [data["utilization"] for data in gpu_usage.values()]
            avg_gpu_utilization = sum(utilizations) / len(utilizations)
            
            temperatures = [data["temperature"] for data in gpu_usage.values() if data["temperature"] is not None]
            if temperatures:
                max_gpu_temperature = max(temperatures)
            
            total_gpu_memory_used_mb = sum(data["memory_used_mb"] for data in gpu_usage.values())
            total_gpu_memory_free_mb = sum(data["memory_free_mb"] for data in gpu_usage.values())
        
        # Monitorar sistema
        memory = psutil.virtual_memory()
        system_memory_usage = memory.percent
        system_cpu_usage = psutil.cpu_percent(interval=1)
        
        # Simular dados de jobs (seria obtido do queue manager real)
        active_jobs = 0  # TODO: Integrar com queue manager real
        queue_size = 0   # TODO: Integrar com queue manager real
        
        return MonitoringData(
            timestamp=time.time(),
            gpu_usage=gpu_usage,
            system_memory_usage=system_memory_usage,
            system_cpu_usage=system_cpu_usage,
            active_jobs=active_jobs,
            queue_size=queue_size,
            avg_gpu_utilization=avg_gpu_utilization,
            max_gpu_temperature=max_gpu_temperature,
            total_gpu_memory_used_mb=total_gpu_memory_used_mb,
            total_gpu_memory_free_mb=total_gpu_memory_free_mb
        )
    
    def _analyze_monitoring_data(self, data: MonitoringData) -> List[MonitoringEvent]:
        """Analisa dados de monitoramento e identifica eventos"""
        events = []
        
        # Verificar sobrecarga de GPU
        if data.avg_gpu_utilization > self._thresholds["gpu_overload_threshold"]:
            events.append(MonitoringEvent.GPU_OVERLOAD)
        elif data.avg_gpu_utilization < self._thresholds["gpu_underload_threshold"]:
            events.append(MonitoringEvent.GPU_UNDERLOAD)
        
        # Verificar pressão de memória GPU
        if data.total_gpu_memory_used_mb > 0:
            total_memory = data.total_gpu_memory_used_mb + data.total_gpu_memory_free_mb
            memory_usage_percent = (data.total_gpu_memory_used_mb / total_memory) * 100
            if memory_usage_percent > self._thresholds["memory_pressure_threshold"]:
                events.append(MonitoringEvent.MEMORY_PRESSURE)
        
        # Verificar temperatura
        if data.max_gpu_temperature:
            if data.max_gpu_temperature > self._thresholds["temperature_high_threshold"]:
                events.append(MonitoringEvent.TEMPERATURE_HIGH)
            elif data.max_gpu_temperature < self._thresholds["temperature_normal_threshold"]:
                events.append(MonitoringEvent.TEMPERATURE_NORMAL)
        
        # Verificar sobrecarga do sistema
        if data.system_cpu_usage > self._thresholds["cpu_overload_threshold"]:
            events.append(MonitoringEvent.SYSTEM_OVERLOAD)
        else:
            events.append(MonitoringEvent.SYSTEM_NORMAL)
        
        return events
    
    def _process_monitoring_event(self, event: MonitoringEvent, data: MonitoringData):
        """Processa um evento de monitoramento"""
        
        # Executar callbacks registrados
        if event in self._event_callbacks:
            for callback in self._event_callbacks[event]:
                try:
                    callback(event, data)
                except Exception as e:
                    self.logger.error(f"Erro em callback de evento {event}: {e}")
        
        # Gerar ajustes automáticos
        adjustments = self._generate_adjustments_for_event(event, data)
        
        for adjustment in adjustments:
            try:
                self._adjustment_queue.put_nowait(adjustment)
            except queue.Full:
                self.logger.warning("Fila de ajustes cheia, descartando ajuste")
    
    def _generate_adjustments_for_event(self, event: MonitoringEvent, data: MonitoringData) -> List[AdjustmentAction]:
        """Gera ajustes automáticos para um evento"""
        adjustments = []
        current_settings = self.config_engine.get_adaptive_settings()
        
        if event == MonitoringEvent.GPU_OVERLOAD:
            # Reduzir concurrent jobs
            if current_settings.max_concurrent_jobs > 1:
                adjustments.append(AdjustmentAction(
                    setting_name="max_concurrent_jobs",
                    old_value=current_settings.max_concurrent_jobs,
                    new_value=current_settings.max_concurrent_jobs - 1,
                    reason="GPU sobrecarregada",
                    priority=1
                ))
        
        elif event == MonitoringEvent.GPU_UNDERLOAD:
            # Aumentar concurrent jobs (com limite)
            if current_settings.max_concurrent_jobs < 6:
                adjustments.append(AdjustmentAction(
                    setting_name="max_concurrent_jobs",
                    old_value=current_settings.max_concurrent_jobs,
                    new_value=current_settings.max_concurrent_jobs + 1,
                    reason="GPU subutilizada",
                    priority=2
                ))
        
        elif event == MonitoringEvent.MEMORY_PRESSURE:
            # Reduzir uso de memória
            if current_settings.max_memory_usage > 0.5:
                adjustments.append(AdjustmentAction(
                    setting_name="max_memory_usage",
                    old_value=current_settings.max_memory_usage,
                    new_value=max(0.5, current_settings.max_memory_usage - 0.1),
                    reason="Pressão de memória GPU",
                    priority=1
                ))
        
        elif event == MonitoringEvent.TEMPERATURE_HIGH:
            # Reduzir carga para diminuir temperatura
            adjustments.extend([
                AdjustmentAction(
                    setting_name="max_concurrent_jobs",
                    old_value=current_settings.max_concurrent_jobs,
                    new_value=max(1, current_settings.max_concurrent_jobs - 1),
                    reason="Temperatura alta da GPU",
                    priority=1
                ),
                AdjustmentAction(
                    setting_name="max_memory_usage",
                    old_value=current_settings.max_memory_usage,
                    new_value=max(0.5, current_settings.max_memory_usage - 0.1),
                    reason="Temperatura alta da GPU",
                    priority=1
                )
            ])
        
        elif event == MonitoringEvent.SYSTEM_OVERLOAD:
            # Reduzir carga do sistema
            if current_settings.max_concurrent_jobs > 1:
                adjustments.append(AdjustmentAction(
                    setting_name="max_concurrent_jobs",
                    old_value=current_settings.max_concurrent_jobs,
                    new_value=max(1, current_settings.max_concurrent_jobs - 1),
                    reason="Sistema sobrecarregado",
                    priority=1
                ))
        
        return adjustments
    
    def _execute_adjustment(self, action: AdjustmentAction) -> bool:
        """Executa um ajuste de configuração"""
        try:
            # Aplicar override temporário
            self.config_engine.set_user_override(
                profile=None,  # Global override
                setting_name=action.setting_name,
                value=action.new_value
            )
            return True
        except Exception as e:
            self.logger.error(f"Erro ao executar ajuste {action.setting_name}: {e}")
            return False
    
    def _add_to_history(self, data: MonitoringData):
        """Adiciona dados ao histórico de monitoramento"""
        self._monitoring_history.append(data)
        
        # Manter tamanho do histórico limitado
        if len(self._monitoring_history) > self._max_history_size:
            self._monitoring_history = self._monitoring_history[-self._max_history_size:]
    
    def register_event_callback(self, event: MonitoringEvent, callback: Callable):
        """Registra um callback para um evento de monitoramento"""
        if event not in self._event_callbacks:
            self._event_callbacks[event] = []
        self._event_callbacks[event].append(callback)
    
    def unregister_event_callback(self, event: MonitoringEvent, callback: Callable):
        """Remove um callback de um evento de monitoramento"""
        if event in self._event_callbacks and callback in self._event_callbacks[event]:
            self._event_callbacks[event].remove(callback)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Retorna o status atual do monitoramento"""
        if not self._monitoring_history:
            return {"status": "no_data"}
        
        latest_data = self._monitoring_history[-1]
        
        return {
            "status": "running" if self._running else "stopped",
            "monitoring_interval": self.monitoring_interval,
            "latest_data": {
                "timestamp": latest_data.timestamp,
                "avg_gpu_utilization": latest_data.avg_gpu_utilization,
                "max_gpu_temperature": latest_data.max_gpu_temperature,
                "system_cpu_usage": latest_data.system_cpu_usage,
                "system_memory_usage": latest_data.system_memory_usage,
            },
            "performance_metrics": self._performance_metrics.copy(),
            "recent_adjustments": len(self._adjustment_history),
            "queue_sizes": {
                "monitoring": self._monitoring_queue.qsize(),
                "adjustments": self._adjustment_queue.qsize(),
            }
        }
    
    def get_monitoring_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retorna o histórico de monitoramento"""
        history = self._monitoring_history
        if last_n:
            history = history[-last_n:]
        
        return [
            {
                "timestamp": data.timestamp,
                "avg_gpu_utilization": data.avg_gpu_utilization,
                "max_gpu_temperature": data.max_gpu_temperature,
                "system_cpu_usage": data.system_cpu_usage,
                "system_memory_usage": data.system_memory_usage,
                "total_gpu_memory_used_mb": data.total_gpu_memory_used_mb,
                "total_gpu_memory_free_mb": data.total_gpu_memory_free_mb,
            }
            for data in history
        ]
    
    def get_adjustment_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retorna o histórico de ajustes"""
        history = self._adjustment_history
        if last_n:
            history = history[-last_n:]
        
        return [
            {
                "setting_name": action.setting_name,
                "old_value": action.old_value,
                "new_value": action.new_value,
                "reason": action.reason,
                "priority": action.priority,
            }
            for action in history
        ]
    
    def update_thresholds(self, thresholds: Dict[str, Any]):
        """Atualiza os limites de monitoramento"""
        self._thresholds.update(thresholds)
        self.logger.info(f"Limites de monitoramento atualizados: {thresholds}")
    
    def reset_adjustments(self):
        """Remove todos os ajustes temporários"""
        # Limpar overrides do usuário (apenas os temporários)
        # TODO: Implementar diferenciação entre overrides temporários e permanentes
        self.logger.info("Ajustes temporários removidos")
        
        # Forçar atualização das configurações
        self.config_engine._current_settings = None