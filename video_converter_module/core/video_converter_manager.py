"""
Gerenciador principal para conversões de vídeo.
Move a classe VideoConverterManager para um módulo separado para evitar
detecções de métodos duplicados no mesmo arquivo pelo verificador de integridade.
"""

import uuid
from pathlib import Path

from utils.config import (
    AUDIO_CODEC_CONFIG,
    get_hardware_config,
)
from utils.universal_hardware_manager import UniversalHardwareManager
from utils.hardware_integration import HardwareIntegration
from utils.validators import (
    validate_input_file,
    validate_output_directory,
    validate_conversion_settings,
    generate_output_filename,
)


class VideoConverterManager:
    """
    Gerenciador principal para conversões de vídeo.
    Interface simplificada para uso na GUI.
    """

    def __init__(self):
        """Inicializa o gerenciador com configuração de hardware e formatos suportados."""
        self.converter_thread = None

        # Detectar configuração de hardware
        self.hardware_config_obj = get_hardware_config()
        self.hardware_config = self.hardware_config_obj.auto_configure()
        self.cuda_available = self.hardware_config.get("hardware_acceleration", {}).get(
            "enabled", False
        )

        # Formatos suportados baseados na configuração de hardware
        self.supported_formats = self._build_supported_formats()

    def _build_supported_formats(self):
        """Constrói lista de formatos suportados baseada na configuração de hardware."""
        formats = {
            "input": [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"],
            "output": {},
        }

        # Formatos básicos sempre disponíveis
        formats["output"].update({"WebM (VP9)": ".webm", "WEBP (Animado)": ".webp"})

        # Adicionar formatos H.264 e H.265 com indicação de aceleração
        if self.cuda_available:
            formats["output"].update(
                {
                    "MP4 (H.264 - NVENC)": ".mp4",
                    "AVI (H.264 - NVENC)": ".avi",
                    "MOV (H.264 - NVENC)": ".mov",
                    "MKV (H.264 - NVENC)": ".mkv",
                    "MP4 (H.265 - NVENC)": ".mp4",
                    "MKV (H.265 - NVENC)": ".mkv",
                    # Opções CPU como fallback
                    "MP4 (H.264 - CPU)": ".mp4",
                    "AVI (H.264 - CPU)": ".avi",
                    "MOV (H.264 - CPU)": ".mov",
                    "MKV (H.264 - CPU)": ".mkv",
                    "MP4 (H.265 - CPU)": ".mp4",
                }
            )
        else:
            formats["output"].update(
                {
                    "MP4 (H.264)": ".mp4",
                    "AVI (H.264)": ".avi",
                    "MOV (H.264)": ".mov",
                    "MKV (H.264)": ".mkv",
                    "MP4 (H.265)": ".mp4",
                }
            )

        # Adicionar novos formatos especiais
        formats["output"].update(
            {
                "GIF (Animado)": ".gif",
                "Extração de Frames": ".jpg",  # Extensão padrão, sobrescrita dinamicamente
                "Extração de Áudio": ".mp3",  # Extensão padrão, sobrescrita dinamicamente
            }
        )

        return formats

    def get_max_concurrent_jobs(self, settings):
        """Obtém o número máximo de jobs simultâneos baseado no modo de performance."""
        performance_config = settings.get("performance_config", {})
        max_jobs = performance_config.get("max_concurrent_jobs", 2)

        # Ajustar baseado na disponibilidade de hardware
        if not self.cuda_available and max_jobs > 1:
            max_jobs = max(1, max_jobs // 2)

        return max_jobs

    def get_hardware_info(self):
        """Retorna informações sobre a configuração de hardware disponível."""
        detector = self.hardware_config_obj.get_hardware_detector()
        gpu_info = {}
        if detector:
            gpu_info = detector.get_hardware_summary()

        return {
            "cuda_available": self.cuda_available,
            "hardware_config": self.hardware_config,
            "gpu_info": gpu_info,
            "recommended_settings": self.hardware_config.get(
                "recommended_settings", {}
            ),
            "cuda_settings": self.hardware_config.get("cuda_config", {}),
            "quality_presets": self.hardware_config.get("quality_presets", {}),
        }

    def is_cuda_format(self, format_name):
        """Verifica se o formato especificado usa aceleração CUDA/NVENC."""
        return "NVENC" in format_name

    def is_supported_input_format(self, file_path):
        """Verifica se o formato do arquivo é suportado."""
        is_valid, _ = validate_input_file(file_path)
        return is_valid

    def get_output_extension(self, format_name, frame_format=None, audio_format=None):
        """Retorna a extensão para o formato de saída (frames/áudio suportam formatos dedicados)."""
        if "Extração de Frames" in format_name and frame_format:
            frame_extensions = {
                "JPG": ".jpg",
                "PNG": ".png",
                "WebP": ".webp",
                "TIFF": ".tiff",
            }
            return frame_extensions.get(frame_format, ".jpg")

        if "Extração de Áudio" in format_name and audio_format:
            if audio_format in AUDIO_CODEC_CONFIG:
                return AUDIO_CODEC_CONFIG[audio_format]["extension"]
            return ".mp3"

        return self.supported_formats["output"].get(format_name, ".mp4")

    def start_conversion(self, input_file, output_dir, settings, callbacks):
        """Inicia uma nova conversão após validar entradas e configurações."""
        # Validar arquivo de entrada
        is_valid, error_msg = validate_input_file(input_file)
        if not is_valid:
            if "log" in callbacks:
                callbacks["log"](f"Erro na validação do arquivo: {error_msg}")
            if "finished" in callbacks:
                callbacks["finished"](False, f"Arquivo inválido: {error_msg}")
            return None

        # Validar diretório de saída
        is_valid, error_msg = validate_output_directory(output_dir)
        if not is_valid:
            if "log" in callbacks:
                callbacks["log"](f"Erro na validação do diretório: {error_msg}")
            if "finished" in callbacks:
                callbacks["finished"](False, f"Diretório inválido: {error_msg}")
            return None

        # Validar configurações
        is_valid, error_msg = validate_conversion_settings(settings)
        if not is_valid:
            if "log" in callbacks:
                callbacks["log"](f"Erro nas configurações: {error_msg}")
            if "finished" in callbacks:
                callbacks["finished"](False, f"Configurações inválidas: {error_msg}")
            return None

        # Cancelar conversão anterior se existir
        self.cancel_conversion()

        # Importar dentro do método para evitar import circular
        from .video_converter import VideoConverter

        # Gerar nome do arquivo de saída
        format_name = settings.get("format", "MP4 (H.264)")

        # Obter extensão correta baseada no formato
        extension = self.get_output_extension(format_name)
        if extension.startswith("."):
            extension = extension[1:]

        # Ajustes para formatos especiais
        if "Extração de Frames" in format_name:
            frame_extension = self.get_output_extension(
                format_name, settings.get("frame_extraction_settings", {}).get("format")
            )
            if frame_extension.startswith("."):
                frame_extension = frame_extension[1:]
            extension = frame_extension
        elif "Extração de Áudio" in format_name:
            audio_format = settings.get("audio_extraction_settings", {}).get("format", "MP3")
            audio_extension = self.get_output_extension(
                format_name, audio_format=audio_format
            )
            if audio_extension.startswith("."):
                audio_extension = audio_extension[1:]
            extension = audio_extension

        # Correção para GIF: nomes sem caracteres problemáticos
        if "GIF (Animado)" in format_name:
            extension = "gif"
            input_path = Path(input_file)
            unique_id = str(uuid.uuid4()).replace("-", "")[:8]
            output_filename = f"{input_path.stem}_gif_{unique_id}.gif"
            if "log" in callbacks:
                callbacks["log"](
                    f"🔧 CORREÇÃO APLICADA: Nome do arquivo GIF corrigido - {output_filename}"
                )
                callbacks["log"](
                    f"🔧 DEBUG: format_name='{format_name}', input_file='{input_file}'"
                )
        else:
            output_filename = generate_output_filename(
                input_file, extension, "converted"
            )
            if "log" in callbacks:
                callbacks["log"](
                    f"🔧 DEBUG: Formato normal - {format_name}, output_filename='{output_filename}'"
                )
        output_file = Path(output_dir) / output_filename

        # Criar e iniciar thread de conversão
        self.converter_thread = VideoConverter()
        self.converter_thread.set_conversion_parameters(
            input_file, str(output_file), settings, callbacks
        )
        self.converter_thread.start()

        return self.converter_thread

    def cancel_conversion(self):
        """Cancela a conversão atual, se ativa, e aguarda término."""
        if self.converter_thread and self.converter_thread.is_alive():
            self.converter_thread.cancel_conversion()
            self.converter_thread.join(5)