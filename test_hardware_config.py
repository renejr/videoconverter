#!/usr/bin/env python3
"""
Script para testar a configuração automática de hardware.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import get_hardware_config, auto_configure_hardware
import json


def test_hardware_config():
    """Testa a configuração automática de hardware."""
    print("=== TESTE DE CONFIGURAÇÃO DE HARDWARE ===\n")

    # Obtém instância da configuração
    hw_config = get_hardware_config()

    # Testa configuração automática
    print("1. Configuração automática:")
    config = hw_config.auto_configure()

    print(
        f"   Hardware acceleration enabled: {config['hardware_acceleration']['enabled']}"
    )
    print(f"   CUDA enabled: {config['cuda_config']['enabled']}")

    if config["hardware_acceleration"]["enabled"]:
        print(f"   Preferred encoder: {config['cuda_config']['preferred_encoder']}")
        print(f"   Preferred decoder: {config['cuda_config']['preferred_decoder']}")
        print(f"   NVENC preset: {config['cuda_config']['preset']}")
        print(f"   Max memory usage: {config['cuda_config']['max_memory_usage']}")

    print(f"   Performance mode: {config['recommended_settings']['performance_mode']}")

    # Testa resumo do hardware
    print("\n2. Resumo do hardware:")
    summary = hw_config.get_hardware_summary()
    print(f"   CUDA available: {summary.get('cuda_available', False)}")

    if summary.get("nvidia_gpu"):
        gpu = summary["nvidia_gpu"]
        print(f"   GPU: {gpu.get('name', 'Unknown')}")
        print(f"   Driver: {gpu.get('driver_version', 'Unknown')}")
        print(f"   Memory: {gpu.get('memory_total', 'Unknown')} MB")

    # Testa encoders para diferentes formatos
    print("\n3. Encoders recomendados:")
    formats = ["MP4", "MKV", "WEBM", "AVI"]
    for fmt in formats:
        encoder_hw = hw_config.get_encoder_for_format(fmt, use_hardware=True)
        encoder_cpu = hw_config.get_encoder_for_format(fmt, use_hardware=False)
        print(f"   {fmt}: Hardware={encoder_hw}, CPU={encoder_cpu}")

    # Testa presets de qualidade
    print("\n4. Presets de qualidade:")
    quality_names = ["Baixa", "Média", "Alta", "Ultra"]
    for quality in quality_names:
        preset = hw_config.get_quality_preset(quality)
        print(f"   {quality}: {preset}")

    # Testa validação de configurações
    print("\n5. Validação de configurações:")
    test_configs = [
        ("h264_nvenc", (1920, 1080)),
        ("h264_nvenc", (7680, 4320)),  # 8K - pode falhar
        ("hevc_nvenc", (3840, 2160)),  # 4K
        ("libx264", (1920, 1080)),  # CPU encoder
    ]

    for encoder, resolution in test_configs:
        valid = hw_config.validate_settings(encoder, resolution)
        print(
            f"   {encoder} @ {resolution[0]}x{resolution[1]}: {'✓' if valid else '✗'}"
        )

    print("\n=== CONFIGURAÇÃO COMPLETA ===")
    print(json.dumps(config, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_hardware_config()
