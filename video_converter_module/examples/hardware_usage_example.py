"""
Exemplo de Uso do Sistema Universal de Hardware
Demonstra como usar o gerenciador universal para diferentes cenários.
"""

import sys
import os
from pathlib import Path

# Adicionar o módulo ao path
sys.path.append(str(Path(__file__).parent.parent))

from utils.universal_hardware_manager import get_hardware_manager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def exemplo_basico():
    """Exemplo básico de uso do sistema"""
    print("=== Exemplo Básico ===")
    
    # Obter o gerenciador (singleton)
    manager = get_hardware_manager()
    
    # Inicializar o sistema
    summary = manager.initialize()
    
    print(f"Hardware detectado: {summary['hardware_profile']}")
    print(f"GPUs encontradas: {summary['gpu_count']}")
    print(f"VRAM total: {summary['total_vram_gb']:.1f} GB")
    print(f"RAM do sistema: {summary['system_ram_gb']:.1f} GB")
    print(f"CUDA disponível: {summary['cuda_available']}")
    print(f"Encoder preferido: {summary['preferred_encoder']}")
    print(f"Jobs concorrentes: {summary['max_concurrent_jobs']}")
    print()


def exemplo_configuracao_para_tarefa():
    """Exemplo de obtenção de configurações para tarefas específicas"""
    print("=== Configurações para Tarefas Específicas ===")
    
    manager = get_hardware_manager()
    
    # Configurações para conversão de vídeo (balanceada)
    config_video = manager.get_optimal_settings_for_task(
        task_type="video_conversion",
        estimated_memory_mb=1024,  # 1GB estimado
        priority="balanced"
    )
    
    print("Configurações para conversão de vídeo (balanceada):")
    print(f"  Encoder: {config_video['encoder']}")
    print(f"  Preset: {config_video['preset']}")
    print(f"  GPU Index: {config_video['gpu_index']}")
    print(f"  Max Memory Usage: {config_video['max_memory_usage']}")
    print(f"  Surfaces: {config_video['surfaces']}")
    print()
    
    # Configurações para streaming (velocidade)
    config_stream = manager.get_optimal_settings_for_task(
        task_type="streaming",
        estimated_memory_mb=512,
        priority="speed"
    )
    
    print("Configurações para streaming (velocidade):")
    print(f"  Encoder: {config_stream['encoder']}")
    print(f"  Preset: {config_stream['preset']}")
    print(f"  RC Mode: {config_stream['rc_mode']}")
    print(f"  Async Depth: {config_stream['async_depth']}")
    print()
    
    # Configurações para qualidade máxima
    config_quality = manager.get_optimal_settings_for_task(
        task_type="video_conversion",
        estimated_memory_mb=2048,
        priority="quality"
    )
    
    print("Configurações para qualidade máxima:")
    print(f"  Encoder: {config_quality['encoder']}")
    print(f"  Preset: {config_quality['preset']}")
    print(f"  CQ: {config_quality['cq']}")
    print(f"  RC Lookahead: {config_quality['rc_lookahead']}")
    print(f"  Multipass: {config_quality['multipass']}")
    print()


def exemplo_status_hardware():
    """Exemplo de monitoramento do status do hardware"""
    print("=== Status do Hardware ===")
    
    manager = get_hardware_manager()
    status = manager.get_hardware_status()
    
    print(f"Sistema inicializado: {status['initialized']}")
    print(f"Perfil de hardware: {status['hardware_profile']}")
    print(f"Monitoramento ativo: {status['monitoring_enabled']}")
    
    if 'primary_gpu' in status:
        gpu = status['primary_gpu']
        print(f"GPU principal: {gpu['name']}")
        print(f"  VRAM total: {gpu['memory_total_mb']} MB")
        print(f"  VRAM livre: {gpu['memory_free_mb']} MB")
        print(f"  Temperatura: {gpu['temperature']}°C")
        print(f"  Utilização: {gpu['utilization']}%")
    
    print()


def exemplo_recomendacoes():
    """Exemplo de obtenção de recomendações de performance"""
    print("=== Recomendações de Performance ===")
    
    manager = get_hardware_manager()
    recommendations = manager.get_performance_recommendations()
    
    for rec in recommendations:
        icon = {
            "info": "ℹ️",
            "tip": "💡",
            "warning": "⚠️",
            "error": "❌"
        }.get(rec['type'], "📝")
        
        print(f"{icon} [{rec['category']}] {rec['message']}")
    
    print()


def exemplo_preferencias_usuario():
    """Exemplo de configuração de preferências do usuário"""
    print("=== Preferências do Usuário ===")
    
    manager = get_hardware_manager()
    
    # Definir algumas preferências
    manager.set_user_preference("preferred_encoder", "h264_nvenc")
    manager.set_user_preference("max_concurrent_jobs", 3)
    manager.set_user_preference("preset", "medium", profile="mid_range")
    
    # Obter preferências atuais
    preferences = manager.get_user_preferences()
    
    print("Preferências definidas:")
    for profile, settings in preferences.items():
        print(f"  Perfil '{profile}':")
        for setting, value in settings.items():
            print(f"    {setting}: {value}")
    
    print()
    
    # Remover uma preferência
    manager.remove_user_preference("max_concurrent_jobs")
    print("Preferência 'max_concurrent_jobs' removida")
    print()


def exemplo_exportacao_configuracao():
    """Exemplo de exportação da configuração"""
    print("=== Exportação de Configuração ===")
    
    manager = get_hardware_manager()
    
    # Exportar configuração para arquivo
    export_file = "hardware_config_export.json"
    manager.export_configuration(export_file)
    
    print(f"Configuração exportada para: {export_file}")
    
    # Verificar se o arquivo foi criado
    if os.path.exists(export_file):
        size = os.path.getsize(export_file)
        print(f"Arquivo criado com {size} bytes")
    
    print()


def exemplo_debug_info():
    """Exemplo de obtenção de informações de debug"""
    print("=== Informações de Debug ===")
    
    manager = get_hardware_manager()
    debug_info = manager.get_debug_info()
    
    print("Estado do gerenciador:")
    for key, value in debug_info['manager_state'].items():
        print(f"  {key}: {value}")
    
    if 'hardware_status' in debug_info:
        print(f"\nStatus do hardware: {debug_info['hardware_status']['hardware_profile']}")
    
    print()


def exemplo_cenario_completo():
    """Exemplo de um cenário completo de uso"""
    print("=== Cenário Completo ===")
    
    # 1. Inicializar sistema
    manager = get_hardware_manager(enable_monitoring=True)
    summary = manager.initialize()
    
    print(f"✅ Sistema inicializado: {summary['hardware_profile']}")
    
    # 2. Configurar preferências do usuário
    if summary['gpu_count'] > 0:
        manager.set_user_preference("preferred_encoder", "h264_nvenc")
    else:
        manager.set_user_preference("preferred_encoder", "libx264")
    
    print("✅ Preferências configuradas")
    
    # 3. Obter configurações para uma tarefa
    config = manager.get_optimal_settings_for_task(
        task_type="video_conversion",
        estimated_memory_mb=1500,
        priority="balanced"
    )
    
    print(f"✅ Configurações obtidas: {config['encoder']} com preset {config['preset']}")
    
    # 4. Verificar recomendações
    recommendations = manager.get_performance_recommendations()
    if recommendations:
        print(f"✅ {len(recommendations)} recomendações disponíveis")
    
    # 5. Monitorar status (simulado)
    status = manager.get_hardware_status()
    print(f"✅ Status monitorado: {status['hardware_profile']}")
    
    # 6. Exportar configuração
    try:
        manager.export_configuration("final_config.json")
        print("✅ Configuração exportada")
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")
    
    # 7. Limpeza
    manager.cleanup()
    print("✅ Recursos limpos")
    
    print("\n🎉 Cenário completo executado com sucesso!")


def main():
    """Função principal que executa todos os exemplos"""
    print("🚀 Exemplos do Sistema Universal de Hardware\n")
    
    try:
        exemplo_basico()
        exemplo_configuracao_para_tarefa()
        exemplo_status_hardware()
        exemplo_recomendacoes()
        exemplo_preferencias_usuario()
        exemplo_exportacao_configuracao()
        exemplo_debug_info()
        exemplo_cenario_completo()
        
    except Exception as e:
        logger.error(f"Erro durante execução dos exemplos: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Garantir limpeza
        try:
            manager = get_hardware_manager()
            manager.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()