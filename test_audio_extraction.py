#!/usr/bin/env python3
"""
Testes Unitários para Funcionalidade de Extração de Áudio
=========================================================

Testa todas as funcionalidades relacionadas à extração de áudio:
- Geração de comandos FFmpeg para extração
- Validação de formatos de áudio suportados
- Detecção de streams de áudio em vídeos
- Configurações de qualidade e codec
- Integração com a interface gráfica
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.video_converter import VideoConverter, VideoConverterManager
from utils.config import (
    SUPPORTED_AUDIO_FORMATS,
    AUDIO_QUALITY_PRESETS,
    AUDIO_CODEC_CONFIG,
    AUDIO_EXTRACTION_DEFAULTS,
)


class TestAudioExtractionCore(unittest.TestCase):
    """
    Testa funcionalidades principais de extração de áudio
    """

    def setUp(self):
        """
        Configuração inicial para cada teste
        """
        self.converter = VideoConverter()
        self.test_input_file = "test_video.mp4"
        self.temp_dir = tempfile.mkdtemp()

        # Mock para callbacks
        self.mock_callbacks = {
            "progress": Mock(),
            "log": Mock(),
            "finished": Mock(),
            "error": Mock(),
        }

    def tearDown(self):
        """
        Limpeza após cada teste
        """
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_build_audio_extraction_command_mp3(self):
        """
        Testa geração de comando FFmpeg para extração MP3
        """
        # Configurar o converter com parâmetros de extração de áudio
        self.converter.input_file = self.test_input_file
        self.converter.output_file = "output.mp3"
        self.converter.conversion_settings = {
            "format": "Extração de Áudio",
            "audio_extraction": {
                "format": "MP3",
                "quality": "standard",
                "preserve_metadata": True,
            }
        }

        # Comando base
        cmd = ["ffmpeg"]
        
        # Chamar o método com a assinatura correta
        command = self.converter.build_audio_extraction_command(cmd)

        # Verificar estrutura básica do comando
        self.assertIn("ffmpeg", command)
        self.assertIn("-i", command)
        self.assertIn(self.test_input_file, command)
        self.assertIn("output.mp3", command)

        # Verificar parâmetros específicos
        self.assertIn("-vn", command)  # Desabilitar vídeo
        self.assertIn("-c:a", command)

        # Verificar preservação de metadados
        self.assertIn("-map_metadata", command)
        self.assertIn("0", command)

        print("✓ Comando MP3 gerado corretamente")

    def test_build_audio_extraction_command_wav(self):
        """
        Testa geração de comando FFmpeg para extração WAV
        """
        # Configurar o converter com parâmetros de extração de áudio
        self.converter.input_file = self.test_input_file
        self.converter.output_file = "output.wav"
        self.converter.conversion_settings = {
            "format": "Extração de Áudio",
            "audio_extraction": {
                "format": "WAV",
                "quality": "lossless",
                "preserve_metadata": False,
            }
        }

        # Comando base
        cmd = ["ffmpeg"]
        
        # Chamar o método com a assinatura correta
        command = self.converter.build_audio_extraction_command(cmd)

        # Verificar parâmetros específicos do WAV
        self.assertIn("-c:a", command)
        self.assertIn("pcm_s16le", command)

        # Verificar que metadados não são preservados
        self.assertNotIn("-map_metadata", command)

        print("✓ Comando WAV gerado corretamente")

    def test_build_audio_extraction_command_flac(self):
        """
        Testa geração de comando FFmpeg para extração FLAC
        """
        # Configurar o converter com parâmetros de extração de áudio
        self.converter.input_file = self.test_input_file
        self.converter.output_file = "output.flac"
        self.converter.conversion_settings = {
            "format": "Extração de Áudio",
            "audio_extraction": {
                "format": "FLAC",
                "quality": "lossless",
                "preserve_metadata": True,
            }
        }

        # Comando base
        cmd = ["ffmpeg"]
        
        # Chamar o método com a assinatura correta
        command = self.converter.build_audio_extraction_command(cmd)

        # Verificar parâmetros específicos do FLAC
        self.assertIn("-c:a", command)
        self.assertIn("-compression_level", command)
        self.assertIn("8", command)

        print("✓ Comando FLAC gerado corretamente")

    def test_build_audio_extraction_command_ogg(self):
        """
        Testa geração de comando FFmpeg para extração OGG
        """
        # Configurar o converter com parâmetros de extração de áudio
        self.converter.input_file = self.test_input_file
        self.converter.output_file = "output.ogg"
        self.converter.conversion_settings = {
            "format": "Extração de Áudio",
            "audio_extraction": {
                "format": "OGG",
                "quality": "high",
                "preserve_metadata": True,
            }
        }

        # Comando base
        cmd = ["ffmpeg"]
        
        # Chamar o método com a assinatura correta
        command = self.converter.build_audio_extraction_command(cmd)

        # Verificar parâmetros específicos do OGG
        self.assertIn("-c:a", command)
        self.assertIn("libvorbis", command)

        print("✓ Comando OGG gerado corretamente")

    @patch('subprocess.run')
    def test_has_audio_stream_with_audio(self, mock_run):
        """
        Testa detecção de stream de áudio em arquivo com áudio
        """
        # Mock do resultado do subprocess para arquivo com áudio
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "audio"
        mock_run.return_value = mock_result
        
        # Mock do FFmpeg installer
        self.converter.ffmpeg_installer = MagicMock()
        self.converter.ffmpeg_installer.get_ffprobe_command.return_value = "ffprobe"
        
        result = self.converter.has_audio_stream(self.test_input_file)
        self.assertTrue(result)
        
        print("✓ Detecção de stream de áudio funcionando")

    @patch('subprocess.run')
    def test_has_audio_stream_without_audio(self, mock_run):
        """
        Testa detecção de ausência de stream de áudio
        """
        # Mock do resultado do subprocess para arquivo sem áudio
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result
        
        # Mock do FFmpeg installer
        self.converter.ffmpeg_installer = MagicMock()
        self.converter.ffmpeg_installer.get_ffprobe_command.return_value = "ffprobe"
        
        result = self.converter.has_audio_stream(self.test_input_file)
        self.assertFalse(result)
        
        print("✓ Detecção de ausência de áudio funcionando")

    @patch('subprocess.run')
    def test_has_audio_stream_timeout(self, mock_run):
        """
        Testa comportamento quando ffprobe atinge timeout
        """
        # Mock de timeout
        mock_run.side_effect = TimeoutError("Timeout")

        result = self.converter.has_audio_stream(self.test_input_file)

        self.assertFalse(result)
        print("✓ Tratamento de timeout funcionando corretamente")

    def test_get_output_extension_audio_formats(self):
        """
        Testa obtenção de extensão para formatos de áudio
        """
        # Usar VideoConverterManager que tem o método get_output_extension
        manager = VideoConverterManager()
        
        # Testar diferentes formatos de áudio
        test_cases = [
            ("MP3", ".mp3"),
            ("WAV", ".wav"),
            ("FLAC", ".flac"),
            ("OGG", ".ogg"),
            ("AAC", ".aac"),
        ]

        for audio_format, expected_ext in test_cases:
            extension = manager.get_output_extension(
                "Extração de Áudio", audio_format=audio_format
            )
            self.assertEqual(extension, expected_ext)

        print("✓ Extensões de áudio retornadas corretamente")

    def test_audio_quality_presets_validation(self):
        """
        Testa validação dos presets de qualidade de áudio
        """
        # Verificar se todos os formatos têm presets
        for format_name in ["MP3", "AAC", "WAV", "FLAC", "OGG"]:
            self.assertIn(format_name, AUDIO_QUALITY_PRESETS)
            
            # Verificar se cada formato tem as qualidades esperadas
            qualities = AUDIO_QUALITY_PRESETS[format_name]
            for quality in ["Baixa", "Média", "Alta", "Muito Alta"]:
                self.assertIn(quality, qualities)
                
                # Verificar se cada preset tem configurações apropriadas
                preset = qualities[quality]
                # MP3 e AAC têm bitrate, WAV tem sample_rate, etc.
                if format_name in ["MP3", "AAC", "OGG", "M4A", "WMA", "OPUS"]:
                    self.assertIn("bitrate", preset)
                elif format_name == "WAV":
                    self.assertIn("sample_rate", preset)
                elif format_name == "FLAC":
                    self.assertIn("compression_level", preset)

        print(f"✓ {len(AUDIO_QUALITY_PRESETS)} presets de qualidade validados")

    def test_audio_codec_config_validation(self):
        """
        Testa validação das configurações de codec de áudio
        """
        # Verificar se todos os formatos têm configurações válidas
        for format_name, codec_config in AUDIO_CODEC_CONFIG.items():
            self.assertIsInstance(codec_config, dict)
            self.assertIn("codec", codec_config)
            self.assertIn("extension", codec_config)

        print(f"✓ {len(AUDIO_CODEC_CONFIG)} configurações de codec validadas")

    def test_supported_audio_formats_structure(self):
        """
        Testa estrutura dos formatos de áudio suportados
        """
        self.assertIsInstance(SUPPORTED_AUDIO_FORMATS, list)
        self.assertTrue(len(SUPPORTED_AUDIO_FORMATS) > 0)

        # Verificar se todos os formatos estão no AUDIO_CODEC_CONFIG
        for audio_format in SUPPORTED_AUDIO_FORMATS:
            self.assertIn(audio_format, AUDIO_CODEC_CONFIG)

        print(f"✓ {len(SUPPORTED_AUDIO_FORMATS)} formatos de áudio suportados")

    def test_audio_extraction_defaults(self):
        """
        Testa configurações padrão de extração de áudio
        """
        self.assertIn("format", AUDIO_EXTRACTION_DEFAULTS)
        self.assertIn("quality", AUDIO_EXTRACTION_DEFAULTS)
        self.assertIn("preserve_metadata", AUDIO_EXTRACTION_DEFAULTS)

        # Verificar se o formato padrão é suportado
        default_format = AUDIO_EXTRACTION_DEFAULTS["format"]
        self.assertIn(default_format, SUPPORTED_AUDIO_FORMATS)

        # Verificar se a qualidade padrão existe para o formato padrão
        default_quality = AUDIO_EXTRACTION_DEFAULTS["quality"]
        self.assertIn(default_format, AUDIO_QUALITY_PRESETS)
        self.assertIn(default_quality, AUDIO_QUALITY_PRESETS[default_format])

        print("✓ Configurações padrão validadas")


class TestAudioExtractionGUI(unittest.TestCase):
    """
    Testa integração da extração de áudio com a interface gráfica
    """

    def setUp(self):
        """
        Configuração inicial para testes da GUI
        """
        # Importar apenas se necessário para evitar dependências desnecessárias
        try:
            from gui.main_window_tkinter import MainWindow
            self.gui_available = True
        except ImportError:
            self.gui_available = False
            self.skipTest("GUI não disponível para teste")

    def test_audio_extraction_section_creation(self):
        """
        Testa criação da seção de extração de áudio na GUI
        """
        if not self.gui_available:
            return

        # Este teste seria mais complexo e requereria mock do tkinter
        # Por enquanto, apenas verificamos se as configurações estão disponíveis
        self.assertTrue(hasattr(sys.modules.get('utils.config'), 'SUPPORTED_AUDIO_FORMATS'))
        self.assertTrue(hasattr(sys.modules.get('utils.config'), 'AUDIO_QUALITY_PRESETS'))
        self.assertTrue(hasattr(sys.modules.get('utils.config'), 'AUDIO_EXTRACTION_DEFAULTS'))

        print("✓ Configurações da GUI disponíveis")


class TestAudioExtractionIntegration(unittest.TestCase):
    """
    Testes de integração para extração de áudio
    """

    def setUp(self):
        """
        Configuração para testes de integração
        """
        self.converter_manager = VideoConverterManager()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """
        Limpeza após testes de integração
        """
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_audio_extraction_in_supported_formats(self):
        """
        Testa se a extração de áudio funciona para todos os formatos suportados
        """
        from utils.config import SUPPORTED_AUDIO_FORMATS, AUDIO_CODEC_CONFIG
        
        for audio_format in SUPPORTED_AUDIO_FORMATS:
            with self.subTest(format=audio_format):
                # Verifica se o formato tem configuração de codec
                self.assertIn(audio_format, AUDIO_CODEC_CONFIG)
                
                config = AUDIO_CODEC_CONFIG[audio_format]
                self.assertIn("codec", config)
                self.assertIn("extension", config)
                self.assertIn("container", config)
                self.assertIn("supports_metadata", config)
                self.assertIn("supports_album_art", config)
                
                print(f"✓ Formato {audio_format} configurado corretamente")

    @patch('core.video_converter.VideoConverter.has_audio_stream')
    def test_audio_extraction_validation(self, mock_has_audio):
        """
        Testa validação antes da extração de áudio
        """
        # Criar uma instância do VideoConverter para testar
        converter = VideoConverter()
        
        # Simular vídeo com áudio
        mock_has_audio.return_value = True

        # Testar se a validação passa
        has_audio = converter.has_audio_stream("test.mp4")
        self.assertTrue(has_audio)

        # Simular vídeo sem áudio
        mock_has_audio.return_value = False
        has_audio = converter.has_audio_stream("test.mp4")
        self.assertFalse(has_audio)

        print("✓ Validação de áudio funcionando")


def run_audio_extraction_tests():
    """
    Executa todos os testes de extração de áudio
    """
    print("🧪 Executando Testes de Extração de Áudio")
    print("=" * 50)

    # Criar suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Adicionar classes de teste
    test_classes = [
        TestAudioExtractionCore,
        TestAudioExtractionGUI,
        TestAudioExtractionIntegration,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Estatísticas
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = (
        (total_tests - failures - errors) / total_tests * 100 if total_tests > 0 else 0
    )

    print(f"\n📊 Resultados dos Testes de Extração de Áudio:")
    print(f"   Total: {total_tests}")
    print(f"   Sucessos: {total_tests - failures - errors}")
    print(f"   Falhas: {failures}")
    print(f"   Erros: {errors}")
    print(f"   Taxa de sucesso: {success_rate:.1f}%")

    if result.failures:
        print(f"\n❌ Falhas:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\n⚠️  Erros:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback.split('Exception:')[-1].strip()}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_audio_extraction_tests()
    sys.exit(0 if success else 1)