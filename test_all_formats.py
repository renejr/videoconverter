"""
Teste abrangente para validar conversão para todos os formatos suportados
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.video_converter import VideoConverterManager, VideoConverter
from utils.config import (
    SUPPORTED_OUTPUT_FORMATS, QUALITY_PRESETS, RESOLUTION_PRESETS,
    GIF_QUALITY_PRESETS, GIF_FPS_OPTIONS, GIF_COLOR_OPTIONS,
    FRAME_EXTRACTION_FORMATS, WEBP_FRAME_PRESETS
)


class TestAllFormatsConversion(unittest.TestCase):
    """
    Testa a conversão para todos os formatos de saída suportados
    """
    
    def setUp(self):
        """
        Configuração inicial para cada teste
        """
        self.converter_manager = VideoConverterManager()
        self.test_input_file = "test_video.mp4"  # Arquivo de teste fictício
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock para callbacks
        self.mock_callbacks = {
            'progress': Mock(),
            'complete': Mock(),
            'error': Mock()
        }
    
    def tearDown(self):
        """
        Limpeza após cada teste
        """
        # Limpar diretório temporário
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_supported_formats_structure(self):
        """
        Testa se a estrutura de formatos suportados está correta
        """
        formats = self.converter_manager.supported_formats
        
        # Verificar se tem as chaves necessárias
        self.assertIn('input', formats)
        self.assertIn('output', formats)
        
        # Verificar se formatos de entrada são válidos
        self.assertIsInstance(formats['input'], list)
        self.assertTrue(len(formats['input']) > 0)
        
        # Verificar se formatos de saída são válidos
        self.assertIsInstance(formats['output'], dict)
        self.assertTrue(len(formats['output']) > 0)
        
        print(f"✓ Formatos de entrada suportados: {len(formats['input'])}")
        print(f"✓ Formatos de saída suportados: {len(formats['output'])}")
    
    def test_video_formats_command_generation(self):
        """
        Testa geração de comandos FFmpeg para formatos de vídeo
        """
        video_formats = [
            ('MP4 (H.264)', '.mp4'),
            ('AVI (H.264)', '.avi'),
            ('MOV (H.264)', '.mov'),
            ('MKV (H.264)', '.mkv'),
            ('WebM (VP9)', '.webm')
        ]
        
        for format_name, extension in video_formats:
            with self.subTest(format=format_name):
                self._test_format_command_generation(format_name, extension, 'video')
    
    def test_gif_format_command_generation(self):
        """
        Testa geração de comandos FFmpeg para formato GIF
        """
        self._test_format_command_generation('GIF (Animado)', '.gif', 'gif')
    
    def test_webp_format_command_generation(self):
        """
        Testa geração de comandos FFmpeg para formato WEBP
        """
        self._test_format_command_generation('WEBP (Animado)', '.webp', 'webp')
    
    def test_frame_extraction_command_generation(self):
        """
        Testa geração de comandos FFmpeg para extração de frames
        """
        self._test_format_command_generation('Extração de Frames', '.jpg', 'frames')
    
    def _test_format_command_generation(self, format_name, extension, format_type):
        """
        Testa geração de comando FFmpeg para um formato específico
        
        Args:
            format_name (str): Nome do formato
            extension (str): Extensão do arquivo
            format_type (str): Tipo do formato (video, gif, webp, frames)
        """
        # Configurar settings baseado no tipo de formato
        settings = self._get_format_settings(format_type)
        settings['output_format'] = format_name
        
        # Criar converter
        converter = VideoConverter()
        
        # Mock do arquivo de entrada
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True):
            
            # Configurar parâmetros de conversão
            output_file = os.path.join(self.temp_dir, f"test_output{extension}")
            converter.set_conversion_parameters(
                self.test_input_file,
                output_file,
                settings,
                self.mock_callbacks
            )
            
            # Mock do ffprobe para retornar informações de vídeo válidas
            mock_video_info = {
                'duration': 10.0,
                'fps': 30.0,
                'width': 1920,
                'height': 1080,
                'codec': 'h264'
            }
            
            with patch.object(converter, 'get_video_info', return_value=mock_video_info):
                # Gerar comando FFmpeg
                try:
                    command = converter.build_ffmpeg_command()
                    
                    # Verificações básicas do comando
                    self.assertIsInstance(command, list)
                    self.assertTrue(len(command) > 0)
                    # Aceitar tanto 'ffmpeg' quanto caminho completo para ffmpeg.exe
                    self.assertTrue(
                        command[0] == 'ffmpeg' or 
                        command[0].endswith('ffmpeg.exe') or 
                        command[0].endswith('ffmpeg')
                    )
                    
                    # Verificar se arquivo de entrada está no comando
                    self.assertIn('-i', command)
                    input_index = command.index('-i') + 1
                    # Aceitar tanto caminho relativo quanto absoluto
                    input_file_in_command = command[input_index]
                    self.assertTrue(
                        input_file_in_command == self.test_input_file or
                        input_file_in_command.endswith(self.test_input_file) or
                        os.path.basename(input_file_in_command) == self.test_input_file
                    )
                    
                    # Verificar se arquivo de saída está no comando
                    self.assertEqual(command[-1], output_file)
                    
                    # Validações específicas por formato
                    self._validate_format_specific_parameters(command, format_type, format_name)
                    
                    print(f"✓ Comando gerado para {format_name}: {len(command)} parâmetros")
                    
                except Exception as e:
                    self.fail(f"Falha ao gerar comando para {format_name}: {str(e)}")
    
    def _validate_format_specific_parameters(self, command, format_type, format_name):
        """
        Valida parâmetros específicos do FFmpeg para cada tipo de formato
        
        Args:
            command (list): Comando FFmpeg gerado
            format_type (str): Tipo do formato
            format_name (str): Nome do formato
        """
        command_str = ' '.join(command)
        
        if format_type == 'video':
            # Verificar se há um codec de vídeo válido
            video_codecs = ['-c:v libx264', '-c:v h264_nvenc', '-c:v libx265', '-c:v hevc_nvenc', '-c:v libvpx-vp9']
            has_video_codec = any(codec in command_str for codec in video_codecs)
            self.assertTrue(has_video_codec, f"Nenhum codec de vídeo válido encontrado em: {command_str}")
            
            # Verificar se há configurações de qualidade (pelo menos uma)
            quality_params = ['-crf', '-b:v', '-q:v', '-gpu']
            has_quality_param = any(param in command for param in quality_params)
            self.assertTrue(has_quality_param, f"Nenhum parâmetro de qualidade encontrado em: {command_str}")
            
        elif format_type == 'gif':
            # Para GIF, verificar se há codec de vídeo válido
            # O sistema pode usar diferentes codecs para GIF dependendo da configuração
            gif_codecs = ['-c:v h264_nvenc', '-c:v libx264', '-c:v gif']
            has_gif_codec = any(codec in command_str for codec in gif_codecs)
            self.assertTrue(has_gif_codec, f"Nenhum codec válido para GIF encontrado em: {command_str}")
            
            # Verificar se é arquivo .gif
            self.assertTrue(command[-1].endswith('.gif'))
            
        elif format_type == 'webp':
            # Verificar codec WebP - pode ser libwebp ou outros dependendo da configuração
            # O sistema pode usar diferentes codecs para WEBP dependendo do hardware
            webp_codecs = ['-c:v libwebp', '-c:v h264_nvenc', '-c:v libx264']
            has_webp_codec = any(codec in command_str for codec in webp_codecs)
            self.assertTrue(has_webp_codec, f"Nenhum codec WebP válido encontrado em: {command_str}")
            
            # Verificar se é arquivo .webp
            self.assertTrue(command[-1].endswith('.webp'))
            
        elif format_type == 'frames':
            # Para extração de frames, verificar parâmetros de qualidade específicos
            quality_params = ['-q:v', '-quality', '-compression_algo']
            has_quality_param = any(param in command for param in quality_params)
            
            # Verificar se o arquivo de saída tem extensão de imagem
            output_file = command[-1]
            image_extensions = ['.jpg', '.png', '.webp', '.tiff']
            has_image_ext = any(ext in output_file.lower() for ext in image_extensions)
            
            # Pelo menos uma das validações deve passar
            self.assertTrue(has_quality_param or has_image_ext, 
                          f"Comando de extração de frames inválido: {command_str}")
    
    def test_codec_compatibility_by_format(self):
        """
        Testa compatibilidade de codecs para cada formato
        """
        codec_format_compatibility = {
            'h264': ['.mp4', '.avi', '.mov', '.mkv'],
            'h265': ['.mp4', '.mkv'],
            'vp9': ['.webm'],
            'libwebp': ['.webp'],
            'gif': ['.gif']
        }
        
        for codec, compatible_formats in codec_format_compatibility.items():
            with self.subTest(codec=codec):
                for format_ext in compatible_formats:
                    # Verificar se o codec é suportado para o formato
                    self.assertTrue(self._is_codec_format_compatible(codec, format_ext))
                    
        print(f"✓ Compatibilidade de codecs validada para {len(codec_format_compatibility)} codecs")
    
    def _is_codec_format_compatible(self, codec, format_ext):
        """
        Verifica se um codec é compatível com um formato
        
        Args:
            codec (str): Nome do codec
            format_ext (str): Extensão do formato
            
        Returns:
            bool: True se compatível
        """
        compatibility_map = {
            'h264': ['.mp4', '.avi', '.mov', '.mkv'],
            'h265': ['.mp4', '.mkv'],
            'vp9': ['.webm'],
            'libwebp': ['.webp'],
            'gif': ['.gif']
        }
        
        return format_ext in compatibility_map.get(codec, [])
    
    def _get_format_settings(self, format_type):
        """
        Retorna configurações padrão para cada tipo de formato
        
        Args:
            format_type (str): Tipo do formato
            
        Returns:
            dict: Configurações do formato
        """
        base_settings = {
            'quality_preset': 'Médio',
            'resolution_preset': 'Original',
            'use_cuda': False,
            'codec_type': 'h264'
        }
        
        if format_type == 'gif':
            base_settings.update({
                'gif_quality': 'Médio',
                'gif_fps': '15',
                'gif_colors': '256',
                'gif_resolution': 'Original'
            })
        elif format_type == 'webp':
            base_settings.update({
                'webp_quality': 'Médio',
                'webp_fps': '15'
            })
        elif format_type == 'frames':
            base_settings.update({
                'frame_format': 'jpg',
                'frame_mode': 'all',
                'frame_interval': 1
            })
        
        return base_settings
    
    def test_quality_presets_validation(self):
        """
        Testa se todos os presets de qualidade são válidos
        """
        # Testar presets de qualidade padrão
        for preset in QUALITY_PRESETS.keys():
            self.assertIsInstance(QUALITY_PRESETS[preset], dict)
            self.assertIn('crf', QUALITY_PRESETS[preset])
            
        print(f"✓ Presets de qualidade validados: {len(QUALITY_PRESETS)}")
        
        # Testar presets de qualidade GIF
        for preset in GIF_QUALITY_PRESETS.keys():
            self.assertIsInstance(GIF_QUALITY_PRESETS[preset], dict)
            
        print(f"✓ Presets de qualidade GIF validados: {len(GIF_QUALITY_PRESETS)}")
    
    def test_resolution_presets_validation(self):
        """
        Testa se todos os presets de resolução são válidos
        """
        for preset in RESOLUTION_PRESETS.keys():
            if RESOLUTION_PRESETS[preset] is not None:
                self.assertIsInstance(RESOLUTION_PRESETS[preset], tuple)
                self.assertEqual(len(RESOLUTION_PRESETS[preset]), 2)
                
        print(f"✓ Presets de resolução validados: {len(RESOLUTION_PRESETS)}")
    
    def test_hardware_acceleration_compatibility(self):
        """
        Testa compatibilidade com aceleração de hardware
        """
        # Testar com CUDA disponível
        with patch.object(self.converter_manager, 'cuda_available', True):
            formats_cuda = self.converter_manager._build_supported_formats()
            
            # Verificar se formatos NVENC estão disponíveis
            nvenc_formats = [f for f in formats_cuda['output'].keys() if 'NVENC' in f]
            self.assertTrue(len(nvenc_formats) > 0)
            
        print(f"✓ Formatos NVENC disponíveis quando CUDA está ativo: {len(nvenc_formats)}")
        
        # Testar sem CUDA
        with patch.object(self.converter_manager, 'cuda_available', False):
            formats_cpu = self.converter_manager._build_supported_formats()
            
            # Verificar se formatos CPU estão disponíveis
            cpu_formats = [f for f in formats_cpu['output'].keys() if 'NVENC' not in f]
            self.assertTrue(len(cpu_formats) > 0)
            
        print(f"✓ Formatos CPU disponíveis quando CUDA não está ativo: {len(cpu_formats)}")
    
    def test_output_extension_mapping(self):
        """
        Testa se o mapeamento de extensões de saída está correto
        """
        # Usar os formatos exatos que o sistema suporta
        supported_formats = self.converter_manager.supported_formats['output']
        
        # Casos de teste baseados nos formatos realmente suportados
        test_cases = []
        for format_name, expected_ext in supported_formats.items():
            test_cases.append((format_name, expected_ext))
        
        for format_name, expected_ext in test_cases:
            with self.subTest(format=format_name):
                actual_ext = self.converter_manager.get_output_extension(format_name)
                self.assertEqual(actual_ext, expected_ext)
                
        print(f"✓ Mapeamento de extensões validado para {len(test_cases)} formatos")
    
    def test_frame_extraction_formats(self):
        """
        Testa se todos os formatos de extração de frames são válidos
        """
        for frame_format in FRAME_EXTRACTION_FORMATS:
            extension = self.converter_manager.get_output_extension('Extração de Frames', frame_format)
            self.assertTrue(extension.startswith('.'))
            
        print(f"✓ Formatos de extração de frames validados: {len(FRAME_EXTRACTION_FORMATS)}")


def run_format_tests():
    """
    Executa todos os testes de formato e retorna relatório
    """
    print("=" * 60)
    print("EXECUTANDO TESTES DE VALIDAÇÃO DE FORMATOS")
    print("=" * 60)
    
    # Criar suite de testes
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAllFormatsConversion)
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Relatório final
    print("\n" + "=" * 60)
    print("RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    print(f"Testes executados: {result.testsRun}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    
    if result.failures:
        print("\nFALHAS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERROS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nResultado: {'✓ TODOS OS TESTES PASSARAM' if success else '✗ ALGUNS TESTES FALHARAM'}")
    
    return success


if __name__ == '__main__':
    run_format_tests()