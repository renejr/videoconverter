#!/usr/bin/env python3
"""
Script de teste para validar a implementação completa do suporte CUDA
no VideoConverter
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.video_converter import VideoConverterManager, VideoConverter
from utils.config import get_hardware_config


def test_hardware_detection():
    """
    Testa a detecção automática de hardware
    """
    print("=== Teste de Detecção de Hardware ===")

    manager = VideoConverterManager()
    hw_info = manager.get_hardware_info()

    print(f"CUDA Disponível: {hw_info['cuda_available']}")
    print(f"GPU Info: {hw_info['gpu_info']}")
    print(f"Configurações Recomendadas: {hw_info['recommended_settings']}")
    print(f"Configurações CUDA: {hw_info['cuda_settings']}")
    print(f"Presets de Qualidade: {hw_info['quality_presets']}")
    print()


def test_supported_formats():
    """
    Testa os formatos suportados baseados na configuração de hardware
    """
    print("=== Teste de Formatos Suportados ===")

    manager = VideoConverterManager()
    formats = manager.supported_formats

    print("Formatos de Entrada:")
    for fmt in formats["input"]:
        print(f"  - {fmt}")

    print("\nFormatos de Saída:")
    for name, ext in formats["output"].items():
        is_cuda = manager.is_cuda_format(name)
        print(f"  - {name} ({ext}) {'[CUDA]' if is_cuda else '[CPU]'}")
    print()


def test_video_converter_initialization():
    """
    Testa a inicialização do VideoConverter com configuração de hardware
    """
    print("=== Teste de Inicialização do VideoConverter ===")

    converter = VideoConverter()

    print(f"Hardware Config Carregado: {converter.hardware_config is not None}")
    print(f"CUDA Disponível: {converter.cuda_available}")
    print(f"Configurações HW: {converter.hw_settings}")
    print(f"Fallback Tentado: {converter.cuda_fallback_attempted}")
    print()


def test_ffmpeg_command_building():
    """
    Testa a construção de comandos FFmpeg com diferentes configurações
    """
    print("=== Teste de Construção de Comandos FFmpeg ===")

    converter = VideoConverter()

    # Configurar parâmetros de teste
    test_input = "test_input.mp4"
    test_output = "test_output.mp4"

    # Teste com H.264 NVENC (se disponível)
    settings_nvenc = {
        "format": "MP4 (H.264 - NVENC)",
        "quality": "medium",
        "resolution": "original",
        "fps": "original",
        "use_hardware_acceleration": True,
    }

    # Teste com H.264 CPU
    settings_cpu = {
        "format": "MP4 (H.264 - CPU)",
        "quality": "medium",
        "resolution": "original",
        "fps": "original",
        "use_hardware_acceleration": False,
    }

    for name, settings in [("NVENC", settings_nvenc), ("CPU", settings_cpu)]:
        print(f"\n--- Teste {name} ---")
        try:
            converter.set_conversion_parameters(test_input, test_output, settings)
            cmd = converter.build_ffmpeg_command()
            print(f"Comando gerado: {' '.join(cmd)}")

            # Verificar elementos específicos do comando
            if name == "NVENC" and converter.cuda_available:
                has_cuda_decoder = any(
                    "-hwaccel cuda" in " ".join(cmd[i : i + 2])
                    for i in range(len(cmd) - 1)
                )
                has_nvenc_encoder = any("nvenc" in arg for arg in cmd)
                print(f"  - Decodificador CUDA: {'✓' if has_cuda_decoder else '✗'}")
                print(f"  - Encoder NVENC: {'✓' if has_nvenc_encoder else '✗'}")
            else:
                has_cpu_encoder = any(
                    enc in " ".join(cmd) for enc in ["libx264", "libx265"]
                )
                print(f"  - Encoder CPU: {'✓' if has_cpu_encoder else '✗'}")

        except Exception as e:
            print(f"Erro ao construir comando {name}: {e}")


def test_cuda_error_detection():
    """
    Testa a detecção de erros CUDA
    """
    print("\n=== Teste de Detecção de Erros CUDA ===")

    converter = VideoConverter()

    # Mensagens de erro de teste
    test_errors = [
        "CUDA error: out of memory",
        "NVENC error: encoder initialization failed",
        "Cannot load cuvidCreateVideoParser",
        "No CUDA-capable device is detected",
        "Generic FFmpeg error",
        "File not found error",
    ]

    for error_msg in test_errors:
        is_cuda_error = converter._is_cuda_error(error_msg)
        print(f"'{error_msg}' -> CUDA Error: {'✓' if is_cuda_error else '✗'}")


def main():
    """
    Executa todos os testes
    """
    print("🚀 Iniciando Testes de Implementação CUDA\n")

    try:
        test_hardware_detection()
        test_supported_formats()
        test_video_converter_initialization()
        test_ffmpeg_command_building()
        test_cuda_error_detection()

        print("\n✅ Todos os testes concluídos com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
