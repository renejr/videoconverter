#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da lógica de geração do nome do arquivo para extração de áudio
"""

from pathlib import Path

def test_filename_logic():
    """Testa a lógica de geração do nome do arquivo"""
    
    # Simular configurações de extração de áudio
    settings = {
        'format': 'Extração de Áudio',
        'audio_extraction_settings': {
            'enabled': True,
            'format': 'MP3'
        }
    }

    # Simular file_info
    file_info = {'path': 'test_video.avi'}

    # Testar a lógica
    input_path = Path(file_info['path'])
    format_name = settings.get('format', 'mp4')

    is_audio_extraction = (
        'Extração de Áudio' in format_name or 
        settings.get('audio_extraction_settings', {}).get('enabled', False)
    )

    if is_audio_extraction:
        if settings.get('audio_extraction_settings', {}).get('format'):
            audio_format = settings['audio_extraction_settings']['format']
        else:
            audio_format = 'MP3'
        
        audio_extensions = {
            'MP3': 'mp3', 'AAC': 'aac', 'WAV': 'wav', 'FLAC': 'flac',
            'OGG': 'ogg', 'M4A': 'm4a', 'WMA': 'wma', 'OPUS': 'opus'
        }
        output_format = audio_extensions.get(audio_format, 'mp3')
    else:
        output_format = format_name

    output_filename = f'{input_path.stem}.{output_format}'
    
    print(f'Formato detectado: {format_name}')
    print(f'É extração de áudio: {is_audio_extraction}')
    print(f'Formato de áudio: {audio_format if is_audio_extraction else "N/A"}')
    print(f'Extensão de saída: {output_format}')
    print(f'Nome do arquivo final: {output_filename}')
    
    return output_filename

if __name__ == "__main__":
    test_filename_logic()