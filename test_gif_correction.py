#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para verificar se a correção GIF está funcionando
"""

import os
import sys
import tempfile
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.video_converter import VideoConverter


def test_gif_filename_correction():
    """
    Testa se a correção do nome do arquivo GIF está funcionando
    """
    print("🧪 Testando correção do nome do arquivo GIF...")

    # Criar um conversor
    converter = VideoConverter()

    # Simular um arquivo de saída com (Animado)
    test_output_file = "teste_video (Animado).GIF"

    # Configurar parâmetros básicos
    converter.output_file = test_output_file
    converter.settings = {
        "format": "GIF (Animado)",
        "quality": "Média",
        "fps": "15",
        "resolution": "Original",
        "colors": "256",
    }

    # Construir comando GIF
    base_cmd = ["ffmpeg", "-i", "input_test.mp4"]
    gif_cmd = converter.build_gif_command(base_cmd.copy())

    print(f"📁 Arquivo original: {test_output_file}")

    # Verificar se o comando contém o nome limpo
    output_file_in_cmd = gif_cmd[-1]  # Último elemento deve ser o arquivo de saída
    print(f"📁 Arquivo no comando: {output_file_in_cmd}")

    # Verificações
    success = True

    if "(Animado)" in output_file_in_cmd:
        print("❌ ERRO: O nome do arquivo ainda contém '(Animado)'")
        success = False
    else:
        print("✅ OK: '(Animado)' foi removido do nome do arquivo")

    if not output_file_in_cmd.endswith(".gif"):
        print("❌ ERRO: O arquivo não termina com '.gif'")
        success = False
    else:
        print("✅ OK: Arquivo termina com '.gif'")

    if ".GIF" in output_file_in_cmd:
        print("❌ ERRO: Ainda contém '.GIF' maiúsculo")
        success = False
    else:
        print("✅ OK: Não contém '.GIF' maiúsculo")

    # Verificar se não há espaços extras
    if "  " in output_file_in_cmd or output_file_in_cmd != output_file_in_cmd.strip():
        print("❌ ERRO: Arquivo contém espaços extras")
        success = False
    else:
        print("✅ OK: Não há espaços extras")

    print(f"\n📋 Comando FFmpeg completo:")
    print(" ".join(gif_cmd))

    if success:
        print("\n🎉 TESTE PASSOU: A correção GIF está funcionando corretamente!")
        return True
    else:
        print("\n💥 TESTE FALHOU: A correção GIF não está funcionando")
        return False


def test_gif_command_structure():
    """
    Testa se a estrutura do comando GIF está correta
    """
    print("\n🧪 Testando estrutura do comando GIF...")

    converter = VideoConverter()
    converter.output_file = "teste (Animado).GIF"
    converter.settings = {
        "format": "GIF (Animado)",
        "quality": "Alta",
        "fps": "24",
        "resolution": "720p",
        "colors": "256",
    }

    base_cmd = ["ffmpeg", "-i", "input.mp4"]
    gif_cmd = converter.build_gif_command(base_cmd.copy())

    print("📋 Comando gerado:")
    for i, arg in enumerate(gif_cmd):
        print(f"  {i}: {arg}")

    # Verificar elementos essenciais
    cmd_str = " ".join(gif_cmd)

    checks = [
        ("-vf", "Filtro de vídeo presente"),
        ("palettegen", "Geração de paleta presente"),
        ("paletteuse", "Uso de paleta presente"),
        ("-y", "Sobrescrita habilitada"),
        (".gif", "Extensão .gif presente"),
    ]

    all_passed = True
    for check, description in checks:
        if check in cmd_str:
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - FALTANDO")
            all_passed = False

    return all_passed


if __name__ == "__main__":
    print("🚀 Iniciando testes da correção GIF...\n")

    test1_passed = test_gif_filename_correction()
    test2_passed = test_gif_command_structure()

    print("\n" + "=" * 50)
    if test1_passed and test2_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ A correção GIF está funcionando corretamente")
    else:
        print("💥 ALGUNS TESTES FALHARAM!")
        print("❌ A correção GIF precisa de ajustes")
    print("=" * 50)
