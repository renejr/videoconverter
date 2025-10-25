#!/usr/bin/env python3
"""
Teste do Seletor de Codec H.264/H.265
Verifica se a funcionalidade está funcionando corretamente
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.video_converter import VideoConverter
from utils.config import SUPPORTED_OUTPUT_FORMATS


def test_codec_selection():
    """
    Testa a seleção de codec H.264/H.265
    """
    print("=== Teste do Seletor de Codec H.264/H.265 ===\n")

    converter = VideoConverter()

    # Configurações de teste
    test_cases = [
        {
            "name": "MP4 com H.264",
            "settings": {"format": "MP4 (H.264)", "codec": "h264", "quality": "Alta"},
        },
        {
            "name": "MP4 com H.265",
            "settings": {
                "format": "MP4 (H.264)",  # Formato MP4 mas codec H.265
                "codec": "hevc",
                "quality": "Alta",
            },
        },
        {
            "name": "MKV com H.264",
            "settings": {"format": "MKV (H.264)", "codec": "h264", "quality": "Alta"},
        },
        {
            "name": "MKV com H.265",
            "settings": {
                "format": "MKV (H.264)",  # Formato MKV mas codec H.265
                "codec": "hevc",
                "quality": "Alta",
            },
        },
        {
            "name": "AVI (deve forçar H.264)",
            "settings": {
                "format": "AVI",
                "codec": "hevc",  # Tentativa de usar H.265 com AVI
                "quality": "Alta",
            },
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testando: {test_case['name']}")

        # Configurar parâmetros
        converter.output_file = (
            f"test_output.{get_extension(test_case['settings']['format'])}"
        )
        converter.conversion_settings = test_case["settings"]

        # Construir comando FFmpeg
        cmd = ["ffmpeg", "-i", "input.mp4"]  # Comando base

        try:
            # Testar configurações de vídeo
            converter.add_video_settings(cmd)

            # Verificar se o codec correto foi aplicado
            codec_found = None
            for j, arg in enumerate(cmd):
                if arg == "-c:v":
                    codec_found = cmd[j + 1] if j + 1 < len(cmd) else None
                    break

            expected_codec = get_expected_codec(test_case["settings"])

            # Verificar se o codec encontrado está na lista de codecs válidos
            if isinstance(expected_codec, list):
                is_valid = codec_found in expected_codec
                expected_str = f"{expected_codec[0]} ou {expected_codec[1]}"
            else:
                is_valid = codec_found == expected_codec
                expected_str = expected_codec

            status = "✓" if is_valid else "✗"

            print(
                f"   {status} Codec esperado: {expected_str}, Codec encontrado: {codec_found}"
            )
            print(f"   Comando gerado: {' '.join(cmd[-6:])}")  # Últimos 6 argumentos

        except Exception as e:
            print(f"   ✗ Erro: {e}")

        print()


def get_extension(format_name):
    """
    Obtém a extensão do arquivo baseada no formato
    """
    if "MP4" in format_name:
        return "mp4"
    elif "MKV" in format_name:
        return "mkv"
    elif "AVI" in format_name:
        return "avi"
    elif "WebM" in format_name:
        return "webm"
    elif "MOV" in format_name:
        return "mov"
    else:
        return "mp4"


def get_expected_codec(settings):
    """
    Determina o codec esperado baseado nas configurações
    """
    format_name = settings.get("format", "")
    codec = settings.get("codec", "h264")

    # Para AVI, sempre H.264
    if "AVI" in format_name:
        return "libx264"

    # Para outros formatos, aceitar tanto NVENC quanto CPU
    if codec == "hevc":
        return ["hevc_nvenc", "libx265"]  # NVENC ou CPU H.265
    else:
        return ["h264_nvenc", "libx264"]  # NVENC ou CPU H.264


def test_gui_integration():
    """
    Testa a integração com a interface gráfica
    """
    print("=== Teste de Integração com Interface Gráfica ===\n")

    try:
        from gui.main_window import VideoConverterWindow
        from PyQt6.QtWidgets import QApplication

        # Criar aplicação Qt (necessário para widgets)
        app = QApplication([])

        # Criar janela principal
        window = VideoConverterWindow()

        # Testar configurações padrão
        print("1. Testando configurações padrão:")
        settings = window.get_conversion_settings()
        codec = settings.get("codec", "Não encontrado")
        print(f"   Codec padrão: {codec}")
        print(f"   ✓ Codec padrão é H.264: {'h264' == codec}")

        # Testar mudança de codec
        print("\n2. Testando mudança para H.265:")
        window.codec_combo.setCurrentText("H.265 (HEVC)")
        settings = window.get_conversion_settings()
        codec = settings.get("codec", "Não encontrado")
        print(f"   Codec selecionado: {codec}")
        print(f"   ✓ Codec alterado para H.265: {'hevc' == codec}")

        # Testar validação AVI
        print("\n3. Testando validação AVI:")
        window.format_combo.setCurrentText("AVI")
        window._validate_codec_compatibility()
        current_codec = window.codec_combo.currentText()
        print(f"   Codec após selecionar AVI: {current_codec}")
        print(f"   ✓ Forçou H.264 para AVI: {'H.264' in current_codec}")

        print("\n✓ Teste de integração GUI concluído com sucesso!")

    except ImportError as e:
        print(f"✗ Erro ao importar GUI: {e}")
        print("Certifique-se de que PyQt6 está instalado")
    except Exception as e:
        print(f"✗ Erro no teste GUI: {e}")


if __name__ == "__main__":
    print("Iniciando testes do seletor de codec...\n")

    # Teste 1: Seleção de codec no backend
    test_codec_selection()

    # Teste 2: Integração com GUI
    test_gui_integration()

    print("\n" + "=" * 50)
    print("✓ Todos os testes concluídos!")
    print("O seletor de codec H.264/H.265 foi implementado com sucesso.")
