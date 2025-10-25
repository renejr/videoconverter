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
    file_extension = Path(file_path).suffix.lower().lstrip(".")
    if file_extension not in SUPPORTED_INPUT_FORMATS:
        return False, f"Formato '{file_extension}' não suportado"

    # Verificar se o arquivo não está vazio
    if os.path.getsize(file_path) == 0:
        return False, "Arquivo está vazio"

    return True, ""


def validate_gif_settings(gif_settings):
    """
    Valida configurações específicas para exportação de GIF

    Args:
        gif_settings (dict): Configurações do GIF

    Returns:
        tuple: (is_valid, error_message)
    """
    # Validar FPS
    fps = gif_settings.get("fps", "15")
    if fps != "Original":
        try:
            fps_value = float(fps)
            if fps_value <= 0 or fps_value > 60:
                return False, "FPS deve estar entre 1 e 60"
        except (ValueError, TypeError):
            return False, "FPS deve ser um número válido"

    # Validar cores
    colors = gif_settings.get("colors", "256")
    try:
        colors_value = int(colors)
        if colors_value < 2 or colors_value > 256:
            return False, "Número de cores deve estar entre 2 e 256"
    except (ValueError, TypeError):
        return False, "Número de cores deve ser um número válido"

    # Validar qualidade
    quality = gif_settings.get("quality", "medium")
    valid_qualities = ["low", "medium", "high", "custom"]
    if quality not in valid_qualities:
        return False, f"Qualidade deve ser uma das opções: {', '.join(valid_qualities)}"

    return True, ""


def validate_frame_extraction_settings(frame_settings):
    """
    Valida configurações específicas para extração de frames

    Args:
        frame_settings (dict): Configurações de extração de frames

    Returns:
        tuple: (is_valid, error_message)
    """
    # Validar formato
    frame_format = frame_settings.get("format", "JPG")
    valid_formats = ["JPG", "PNG", "WebP", "TIFF"]
    if frame_format not in valid_formats:
        return False, f"Formato deve ser um dos: {', '.join(valid_formats)}"

    # Validar qualidade para formatos que suportam
    if frame_format in ["JPG", "WebP"]:
        quality = frame_settings.get("quality", 95)
        try:
            quality_value = int(quality)
            if quality_value < 1 or quality_value > 100:
                return False, f"Qualidade para {frame_format} deve estar entre 1 e 100"
        except (ValueError, TypeError):
            return False, f"Qualidade para {frame_format} deve ser um número válido"

    # Validar modo de extração
    extraction_mode = frame_settings.get("mode", "Todos os Frames")
    valid_modes = ["Todos os Frames", "Intervalo Regular", "Frames Específicos"]
    if extraction_mode not in valid_modes:
        return False, f"Modo de extração deve ser um dos: {', '.join(valid_modes)}"

    # Validar configurações específicas do modo
    if extraction_mode == "Intervalo Regular":
        interval = frame_settings.get("interval", 1)
        try:
            interval_value = int(interval)
            if interval_value < 1 or interval_value > 1000:
                return False, "Intervalo deve estar entre 1 e 1000 frames"
        except (ValueError, TypeError):
            return False, "Intervalo deve ser um número válido"

    elif extraction_mode == "Frames Específicos":
        specific_frames = frame_settings.get("specific_frames", "")
        if not specific_frames or not specific_frames.strip():
            return False, "Especifique os números dos frames separados por vírgula"

        try:
            frame_numbers = [
                int(f.strip()) for f in specific_frames.split(",") if f.strip()
            ]
            if not frame_numbers:
                return False, "Especifique pelo menos um número de frame válido"

            for frame_num in frame_numbers:
                if frame_num < 1:
                    return False, "Números de frames devem ser maiores que zero"
                if frame_num > 999999:
                    return False, "Números de frames muito altos (máximo: 999999)"

        except (ValueError, TypeError):
            return (
                False,
                "Números de frames devem ser números inteiros válidos separados por vírgula",
            )

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
    if settings.get("fps") == "Personalizado":
        fps_custom = settings.get("fps_custom", 0)
        if fps_custom <= 0 or fps_custom > 120:
            return False, "FPS personalizado deve estar entre 1 e 120"

    # Validar resolução personalizada
    if settings.get("resolution") == "Personalizada":
        width = settings.get("width", 0)
        height = settings.get("height", 0)

        if width <= 0 or height <= 0:
            return False, "Largura e altura devem ser maiores que zero"

        if width > 7680 or height > 4320:  # 8K máximo
            return False, "Resolução máxima suportada é 8K (7680x4320)"

        if width < 64 or height < 64:
            return False, "Resolução mínima é 64x64 pixels"

    # Validar configurações específicas de GIF
    format_name = settings.get("format", "")
    if "GIF (Animado)" in format_name:
        gif_settings = settings.get("gif_settings", {})
        is_valid, error_msg = validate_gif_settings(gif_settings)
        if not is_valid:
            return False, error_msg

    # Validar configurações específicas de extração de frames
    elif "Extração de Frames" in format_name:
        frame_settings = settings.get("frame_settings", {})
        is_valid, error_msg = validate_frame_extraction_settings(frame_settings)
        if not is_valid:
            return False, error_msg

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
    sanitized = re.sub(invalid_chars, "_", filename)

    # Remover espaços extras e pontos no final
    sanitized = sanitized.strip(". ")

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

    # CORREÇÃO ESPECÍFICA: Tratamento para formatos com nomes complexos
    if "GIF (Animado)" in output_format:
        # Para GIF, usar sempre extensão .gif simples
        extension = "gif"
        # Gerar nome único sem caracteres problemáticos usando timestamp
        import time

        unique_id = str(int(time.time()))[-6:]  # Últimos 6 dígitos do timestamp
        output_filename = f"{base_name}_gif_{unique_id}.{extension}"
    else:
        # CORREÇÃO: Não usar o formato diretamente como extensão
        # Mapear formatos para extensões corretas
        format_to_extension = {
            "mp4": "mp4",
            "avi": "avi",
            "mov": "mov",
            "mkv": "mkv",
            "webm": "webm",
            "gif": "gif",
            "webp": "webp",
            "jpg": "jpg",
            "png": "png",
            "tiff": "tiff",
        }

        # Extrair extensão do formato ou usar o próprio se for simples
        if output_format.startswith("."):
            extension = output_format[1:]  # Remover ponto inicial
        else:
            # Tentar encontrar extensão conhecida no formato
            extension_found = None
            for ext in format_to_extension.keys():
                if ext in output_format.lower():
                    extension_found = ext
                    break
            extension = extension_found or output_format.lower()

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
