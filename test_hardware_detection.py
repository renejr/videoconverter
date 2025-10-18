"""
Teste do Detector de Hardware CUDA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.hardware_detector import get_hardware_detector, is_cuda_available, get_hardware_summary
import json

def test_hardware_detection():
    """
    Testa a detecção de hardware CUDA.
    """
    print("🔍 Testando Detecção de Hardware CUDA...")
    print("=" * 50)
    
    # Obter detector
    detector = get_hardware_detector()
    
    # Teste 1: Verificar disponibilidade do CUDA
    print("1. Verificando disponibilidade do CUDA...")
    cuda_available = is_cuda_available()
    print(f"   ✓ CUDA disponível: {'SIM' if cuda_available else 'NÃO'}")
    
    # Teste 2: Obter resumo do hardware
    print("\n2. Resumo do Hardware:")
    summary = get_hardware_summary()
    print(f"   📊 Resumo completo:")
    print(json.dumps(summary, indent=4, ensure_ascii=False))
    
    # Teste 3: Informações detalhadas da GPU
    if summary['nvidia_gpu']:
        gpu = summary['nvidia_gpu']
        print(f"\n3. Informações da GPU:")
        print(f"   🎮 Modelo: {gpu['name']}")
        print(f"   🔧 Driver: {gpu['driver_version']}")
        print(f"   🚀 CUDA: {gpu['cuda_version']}")
        print(f"   💾 Memória: {gpu['memory_gb']} GB")
    else:
        print("\n3. ❌ Nenhuma GPU NVIDIA detectada")
    
    # Teste 4: Encoders CUDA disponíveis
    print(f"\n4. Encoders CUDA:")
    encoders = detector.get_cuda_encoders()
    if encoders:
        for encoder in encoders:
            print(f"   ✓ {encoder}")
    else:
        print("   ❌ Nenhum encoder CUDA encontrado")
    
    # Teste 5: Decoders CUDA disponíveis
    print(f"\n5. Decoders CUDA:")
    decoders = detector.get_cuda_decoders()
    if decoders:
        for decoder in decoders:
            print(f"   ✓ {decoder}")
    else:
        print("   ❌ Nenhum decoder CUDA encontrado")
    
    # Teste 6: Teste de codificação (se CUDA disponível)
    if cuda_available:
        print(f"\n6. Testando codificação CUDA...")
        test_result = detector.test_cuda_encoding()
        print(f"   {'✓ Teste passou!' if test_result else '❌ Teste falhou!'}")
    else:
        print(f"\n6. ⏭️ Pulando teste de codificação (CUDA não disponível)")
    
    # Teste 7: Informações de memória
    memory_info = detector.get_gpu_memory_info()
    if memory_info:
        total_mb, free_mb = memory_info
        used_mb = total_mb - free_mb
        print(f"\n7. Uso de Memória da GPU:")
        print(f"   📊 Total: {total_mb} MB ({total_mb/1024:.1f} GB)")
        print(f"   🟢 Livre: {free_mb} MB ({free_mb/1024:.1f} GB)")
        print(f"   🔴 Usado: {used_mb} MB ({used_mb/1024:.1f} GB)")
        print(f"   📈 Uso: {(used_mb/total_mb)*100:.1f}%")
    
    print("\n" + "=" * 50)
    print("🎯 Resultado Final:")
    if cuda_available:
        print("   ✅ Sistema pronto para aceleração CUDA!")
        print("   🚀 Performance de conversão será significativamente melhorada")
    else:
        print("   ⚠️ CUDA não disponível - usando apenas CPU")
        print("   💡 Instale drivers NVIDIA atualizados para habilitar CUDA")

if __name__ == "__main__":
    test_hardware_detection()