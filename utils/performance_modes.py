"""
Modos de Performance para Processamento de Vídeo
Define os diferentes modos de prioridade de processamento disponíveis.
"""

from enum import Enum
from typing import Dict, Any


class PerformanceMode(Enum):
    """
    Enum para os diferentes modos de performance de processamento
    """
    ECONOMICA = 0      # Prioriza economia de energia
    AUTOMATICA = 1     # Balanceamento automático (padrão)
    PERFORMANCE = 2    # Prioriza máxima performance


class PerformanceModeConfig:
    """
    Configurações específicas para cada modo de performance
    """
    
    @staticmethod
    def get_mode_config(mode: PerformanceMode) -> Dict[str, Any]:
        """
        Retorna configurações específicas para o modo selecionado
        
        Args:
            mode: Modo de performance selecionado
            
        Returns:
            Dict com configurações otimizadas para o modo
        """
        configs = {
            PerformanceMode.ECONOMICA: {
                'name': 'Econômica',
                'description': 'Prioriza economia de energia e menor uso de recursos',
                'icon': '💰',
                'prefer_cpu': True,
                'prefer_nvidia': False,
                'max_concurrent_jobs': 1,
                'nvenc_preset': 'slow',
                'nvenc_rc_mode': 'vbr',
                'nvenc_cq': 28,
                'cpu_threads': 'auto',
                'memory_usage_limit': 0.5,
                'power_efficiency': True,
                'tooltip': 'Ideal para laptops e economia de energia.\nUsa CPU quando possível, configurações conservadoras.'
            },
            
            PerformanceMode.AUTOMATICA: {
                'name': 'Automática',
                'description': 'Detecta automaticamente o melhor hardware disponível',
                'icon': '🔄',
                'prefer_cpu': False,
                'prefer_nvidia': None,  # Auto-detectar
                'max_concurrent_jobs': 'auto',
                'nvenc_preset': 'medium',
                'nvenc_rc_mode': 'vbr',
                'nvenc_cq': 23,
                'cpu_threads': 'auto',
                'memory_usage_limit': 0.7,
                'power_efficiency': False,
                'tooltip': 'Balanceia performance e consumo.\nDetecta automaticamente o melhor hardware.'
            },
            
            PerformanceMode.PERFORMANCE: {
                'name': 'Performance',
                'description': 'Força uso da melhor GPU NVIDIA para máxima velocidade',
                'icon': '⚡',
                'prefer_cpu': False,
                'prefer_nvidia': True,
                'max_concurrent_jobs': 'max',
                'nvenc_preset': 'fast',
                'nvenc_rc_mode': 'cbr',
                'nvenc_cq': 20,
                'cpu_threads': 'max',
                'memory_usage_limit': 0.9,
                'power_efficiency': False,
                'tooltip': 'Máxima velocidade de conversão.\nForça uso da melhor GPU NVIDIA disponível.'
            }
        }
        
        return configs.get(mode, configs[PerformanceMode.AUTOMATICA])
    
    @staticmethod
    def get_mode_by_value(value: int) -> PerformanceMode:
        """
        Converte valor inteiro para PerformanceMode
        
        Args:
            value: Valor do slider (0, 1, 2)
            
        Returns:
            PerformanceMode correspondente
        """
        mode_map = {
            0: PerformanceMode.ECONOMICA,
            1: PerformanceMode.AUTOMATICA,
            2: PerformanceMode.PERFORMANCE
        }
        return mode_map.get(value, PerformanceMode.AUTOMATICA)
    
    @staticmethod
    def get_all_modes() -> Dict[int, Dict[str, Any]]:
        """
        Retorna todas as configurações de modos disponíveis
        
        Returns:
            Dict mapeando valores do slider para configurações
        """
        return {
            0: PerformanceModeConfig.get_mode_config(PerformanceMode.ECONOMICA),
            1: PerformanceModeConfig.get_mode_config(PerformanceMode.AUTOMATICA),
            2: PerformanceModeConfig.get_mode_config(PerformanceMode.PERFORMANCE)
        }


def get_performance_mode_labels() -> list:
    """
    Retorna lista de labels para o slider
    
    Returns:
        Lista com os nomes dos modos
    """
    modes = PerformanceModeConfig.get_all_modes()
    return [f"{modes[i]['icon']} {modes[i]['name']}" for i in range(3)]


def get_performance_mode_tooltips() -> list:
    """
    Retorna lista de tooltips para cada modo
    
    Returns:
        Lista com tooltips explicativos
    """
    modes = PerformanceModeConfig.get_all_modes()
    return [modes[i]['tooltip'] for i in range(3)]