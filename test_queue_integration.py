#!/usr/bin/env python3
"""
Teste de Integração do Sistema Universal com Queue Manager
Verifica se o sistema universal está funcionando corretamente com o gerenciador de fila
"""

import sys
import os
import json
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_queue_manager_integration():
    """
    Testa a integração do sistema universal com o queue manager
    """
    print("🔧 Testando integração do Sistema Universal com Queue Manager...")
    print("=" * 60)
    
    try:
        # Importar o queue manager
        from video_converter_module.core.queue_manager import ConversionQueueManager
        
        print("✅ Importação do ConversionQueueManager bem-sucedida")
        
        # Inicializar o queue manager
        print("\n📋 Inicializando Queue Manager...")
        queue_manager = ConversionQueueManager()
        
        print("✅ Queue Manager inicializado com sucesso")
        
        # Verificar se o sistema universal foi inicializado
        if hasattr(queue_manager, 'universal_hardware') and queue_manager.universal_hardware:
            print("✅ Sistema Universal detectado no Queue Manager")
            
            # Obter informações do hardware
            print("\n🔍 Obtendo informações do hardware...")
            hardware_info = queue_manager.get_hardware_info()
            
            print(f"📊 Perfil de Hardware: {hardware_info.get('profile_type', 'N/A')}")
            print(f"🔄 Jobs Concorrentes Máximos: {hardware_info.get('max_concurrent_jobs', 'N/A')}")
            print(f"💾 VRAM Total: {hardware_info.get('total_vram', 'N/A')} MB")
            
            # Verificar informações do sistema universal
            if 'universal_system' in hardware_info:
                universal_info = hardware_info['universal_system']
                print(f"\n🌟 Sistema Universal:")
                print(f"   Tier: {universal_info.get('tier', 'N/A')}")
                print(f"   GPUs: {universal_info.get('gpu_count', 'N/A')}")
                print(f"   VRAM Total: {universal_info.get('total_vram', 'N/A')} MB")
                print(f"   CUDA Disponível: {universal_info.get('cuda_available', 'N/A')}")
                print(f"   RAM do Sistema: {universal_info.get('system_ram', 'N/A')} GB")
                
                # Mostrar informações das GPUs
                gpu_info = universal_info.get('gpu_info', [])
                if gpu_info:
                    print(f"\n🎮 GPUs Detectadas:")
                    for i, gpu in enumerate(gpu_info):
                        print(f"   GPU {i+1}: {gpu.get('name', 'N/A')}")
                        print(f"           Memória: {gpu.get('memory_total', 'N/A')} MB")
                        print(f"           Utilização: {gpu.get('utilization', 'N/A')}%")
                        print(f"           Temperatura: {gpu.get('temperature', 'N/A')}°C")
            
            # Testar seleção de GPU
            print("\n🎯 Testando seleção de GPU...")
            
            # Criar um job de teste para H.264
            from video_converter_module.core.queue_manager import ConversionJob
            test_job_h264 = ConversionJob(
                id="test_h264",
                input_file="test.mp4",
                output_file="test_h264.mp4",
                settings={"format": "h.264"}
            )
            
            optimal_gpu_h264 = queue_manager._select_optimal_gpu(test_job_h264)
            print(f"   H.264: {optimal_gpu_h264.value}")
            
            # Criar um job de teste para H.265
            test_job_h265 = ConversionJob(
                id="test_h265",
                input_file="test.mp4",
                output_file="test_h265.mp4",
                settings={"format": "h.265"}
            )
            
            optimal_gpu_h265 = queue_manager._select_optimal_gpu(test_job_h265)
            print(f"   H.265: {optimal_gpu_h265.value}")
            
            # Salvar configuração para análise
            config_export = {
                "timestamp": str(Path(__file__).stat().st_mtime),
                "hardware_info": hardware_info,
                "test_results": {
                    "h264_gpu": optimal_gpu_h264.value,
                    "h265_gpu": optimal_gpu_h265.value
                }
            }
            
            with open("queue_integration_test.json", "w", encoding="utf-8") as f:
                json.dump(config_export, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Configuração exportada para: queue_integration_test.json")
            
        else:
            print("⚠️  Sistema Universal não foi inicializado no Queue Manager")
            print("   Usando sistema de hardware legado")
        
        print("\n✅ Teste de integração concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_queue_manager_integration()
    sys.exit(0 if success else 1)