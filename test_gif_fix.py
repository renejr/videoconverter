#!/usr/bin/env python3
"""
Teste específico para validar as correções na conversão de GIF
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.video_converter import VideoConverter, VideoConverterManager


class TestGifFix(unittest.TestCase):
    """
    Testa as correções implementadas para conversão de GIF
    """
    
    def setUp(self):
        """
        Configuração inicial para os testes
        """
        self.temp_dir = tempfile.mkdtemp()
        self.test_input_file = os.path.join(self.temp_dir, "test_input.avi")
        
        # Criar arquivo de entrada fictício
        with open(self.test_input_file, 'wb') as f:
            f.write(b'fake video content')
        
        # Mock callbacks
        self.mock_callbacks = {
            'progress': MagicMock(),
            'log': MagicMock(),
            'finished': MagicMock()
        }
    
    def test_gif_filename_generation(self):
        """
        Testa se o nome do arquivo GIF é gerado corretamente
        """
        from utils.validators import generate_output_filename
        
        # Testar geração direta do nome do arquivo
        manager = VideoConverterManager()
        
        # Testar extensão para GIF
        extension = manager.get_output_extension('GIF (Animado)')
        self.assertEqual(extension, '.gif')
        
        # Testar geração do nome completo
        output_filename = generate_output_filename(
            self.test_input_file,
            extension,
            "converted"
        )
        
        print(f"[OK] Nome do arquivo de saída: {output_filename}")
        
        # Verificações
        self.assertTrue(output_filename.endswith('.gif'))
        self.assertNotIn('gif (animado)', output_filename.lower())
        self.assertNotIn('(animado)', output_filename.lower())
    
    def test_gif_command_generation(self):
        """
        Testa se o comando FFmpeg para GIF é gerado corretamente
        """
        # Configurações para GIF
        settings = {
            'format': 'GIF (Animado)',
            'quality': 'Média',
            'gif_settings': {
                'fps': '15',
                'colors': '256',
                'quality': 'Média',
                'max_resolution': '480p',
                'dithering': True,
                'optimization': True
            }
        }
        
        # Criar converter
        converter = VideoConverter()
        
        # Mock do arquivo de entrada
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True):
            
            # Configurar parâmetros de conversão
            output_file = os.path.join(self.temp_dir, "test_output.gif")
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
                command = converter.build_ffmpeg_command()
                command_str = ' '.join(command)
                
                print(f"[INFO] Comando FFmpeg gerado:")
                print(f"   {command_str}")

                # Validações do comando
                self.assertIn('-i', command)
                self.assertIn('-filter_complex', command)
                self.assertIn('palettegen', command_str)
                self.assertIn('paletteuse', command_str)
                self.assertIn('-loop', command)
                self.assertIn('0', command)
                self.assertTrue(command[-1].endswith('.gif'))

                # Verificar se não contém filtros incorretos do comando antigo
                self.assertNotIn('gif (animado)', command_str.lower())

                print("[OK] Comando FFmpeg válido para GIF!")
    
    def test_gif_filter_complex_structure(self):
        """
        Testa se a estrutura do filtro complexo está correta
        """
        settings = {
            'format': 'GIF (Animado)',
            'gif_settings': {
                'fps': '15',
                'colors': '256',
                'quality': 'Média',
                'max_resolution': '480p',
                'dithering': True,
                'optimization': True
            }
        }
        
        converter = VideoConverter()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True):
            
            output_file = os.path.join(self.temp_dir, "test_output.gif")
            converter.set_conversion_parameters(
                self.test_input_file,
                output_file,
                settings,
                self.mock_callbacks
            )
            
            mock_video_info = {
                'duration': 10.0,
                'fps': 30.0,
                'width': 1920,
                'height': 1080,
                'codec': 'h264'
            }
            
            with patch.object(converter, 'get_video_info', return_value=mock_video_info):
                command = converter.build_ffmpeg_command()
                
                # Encontrar o filtro complexo
                filter_complex_index = command.index('-filter_complex') + 1
                filter_complex = command[filter_complex_index]
                
                print(f"[DEBUG] Filtro complexo: {filter_complex}")
                
                # Validar estrutura do filtro complexo
                self.assertIn('palettegen', filter_complex)
                self.assertIn('paletteuse', filter_complex)
                self.assertIn('max_colors=256', filter_complex)
                self.assertIn('dither=floyd_steinberg', filter_complex)
                
                # Verificar se tem a estrutura correta de duas etapas
                self.assertIn('[p]', filter_complex)  # Referência da paleta
                
                print("[OK] Estrutura do filtro complexo está correta!")


def main():
    """
    Executa os testes
    """
    print("Testando correcoes para conversao de GIF...")
    print("=" * 60)
    
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()