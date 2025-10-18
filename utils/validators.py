"""
Utilitários de validação para o Video Converter
"""

import os
import re
from pathlib import Path
from utils.config import SUPPORTED_INPUT_FORMATS

def validate_input_file(file_path):
    """
    Valida se o arquivo de entrada é válido
    
    Args:
        file_path (str): Caminho do arquivo
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file_path:
        return False, "Nenhum arquivo selecionado"
    
    if not os.path.exists(file_path):
        return False, "Arquivo não encontrado"
    
    if not os.path.isfile(file_path):
        return False, "Caminho não é um arquivo válido"
    
    # Verificar extensão
    file_extension = Path(file_path).suffix.lower().lstrip('.')
    if file_extension not in SUPPORTED_INPUT_FORMATS:
        return False, f"Formato '{file_extension}' não suportado"
    
    # Verificar se o arquivo não está vazio
    if os.path.getsize(file_path) == 0:
        return False, "Arquivo está vazio"
    
    return True, ""

def validate_output_directory(dir_path):
    """
    Valida se o diretório de saída é válido
    
    Args:
        dir_path (str): Caminho do diretório
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not dir_path:
        return False, "Nenhum diretório selecionado"
    
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception as e:
            return False, f"Não foi possível criar o diretório: {str(e)}"
    
    if not os.path.isdir(dir_path):
        return False, "Caminho não é um diretório válido"
    
    # Verificar permissões de escrita
    if not os.access(dir_path, os.W_OK):
        return False, "Sem permissão de escrita no diretório"
    
    return True, ""

def validate_conversion_settings(settings):
    """
    Valida as configurações de conversão
    
    Args:
        settings (dict): Configurações de conversão
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Validar FPS personalizado
    if settings.get('fps') == 'Personalizado':
        fps_custom = settings.get('fps_custom', 0)
        if fps_custom <= 0 or fps_custom > 120:
            return False, "FPS personalizado deve estar entre 1 e 120"
    
    # Validar resolução personalizada
    if settings.get('resolution') == 'Personalizada':
        width = settings.get('width', 0)
        height = settings.get('height', 0)
        
        if width <= 0 or height <= 0:
            return False, "Largura e altura devem ser maiores que zero"
        
        if width > 7680 or height > 4320:  # 8K máximo
            return False, "Resolução máxima suportada é 8K (7680x4320)"
        
        if width < 64 or height < 64:
            return False, "Resolução mínima é 64x64 pixels"
    
    return True, ""

def sanitize_filename(filename):
    """
    Remove caracteres inválidos do nome do arquivo
    
    Args:
        filename (str): Nome do arquivo
        
    Returns:
        str: Nome do arquivo sanitizado
    """
    # Caracteres inválidos no Windows
    invalid_chars = r'[<>:"/\\|?*]'
    
    # Substituir caracteres inválidos por underscore
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remover espaços extras e pontos no final
    sanitized = sanitized.strip('. ')
    
    # Garantir que não está vazio
    if not sanitized:
        sanitized = "video_convertido"
    
    return sanitized

def generate_output_filename(input_path, output_format, suffix=""):
    """
    Gera nome do arquivo de saída baseado no arquivo de entrada
    
    Args:
        input_path (str): Caminho do arquivo de entrada
        output_format (str): Formato de saída (ex: 'MP4')
        suffix (str): Sufixo adicional para o nome
        
    Returns:
        str: Nome do arquivo de saída
    """
    input_file = Path(input_path)
    base_name = input_file.stem
    
    # Adicionar sufixo se fornecido
    if suffix:
        base_name += f"_{suffix}"
    
    # Sanitizar nome
    base_name = sanitize_filename(base_name)
    
    # Adicionar extensão
    extension = output_format.lower()
    output_filename = f"{base_name}.{extension}"
    
    return output_filename

def check_disk_space(output_dir, estimated_size_mb=1000):
    """
    Verifica se há espaço suficiente em disco
    
    Args:
        output_dir (str): Diretório de saída
        estimated_size_mb (int): Tamanho estimado em MB
        
    Returns:
        tuple: (has_space, available_mb)
    """
    try:
        import shutil
        total, used, free = shutil.disk_usage(output_dir)
        free_mb = free // (1024 * 1024)
        
        # Adicionar margem de segurança de 100MB
        required_mb = estimated_size_mb + 100
        
        return free_mb >= required_mb, free_mb
    except Exception:
        # Se não conseguir verificar, assumir que há espaço
        return True, 0

def validate_ffmpeg_path(ffmpeg_path):
    """
    Valida se o caminho do FFmpeg é válido
    
    Args:
        ffmpeg_path (str): Caminho do executável FFmpeg
        
    Returns:
        bool: True se válido
    """
    if not ffmpeg_path:
        return False
    
    if not os.path.exists(ffmpeg_path):
        return False
    
    if not os.path.isfile(ffmpeg_path):
        return False
    
    # Verificar se é executável
    if not os.access(ffmpeg_path, os.X_OK):
        return False
    
    return True