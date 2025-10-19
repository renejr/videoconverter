"""
Configurações centralizadas do Video Converter
"""

import logging
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)

# Informações da aplicação
APP_NAME = "Video Converter"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Video Converter Team"

# Formatos suportados
SUPPORTED_INPUT_FORMATS = [
    "mp4",
    "avi",
    "mov",
    "mkv",
    "wmv",
    "flv",
    "webm",
    "m4v",
    "3gp",
    "mpg",
    "mpeg",
    "ts",
    "mts",
    "m2ts",
    "vob",
    "ogv",
]

SUPPORTED_OUTPUT_FORMATS = [
    "MP4",
    "AVI",
    "MOV",
    "MKV",
    "WEBM",
    "WEBP",
    "FLV",
    "WMV",
    "M4V",
    "GIF (Animado)",
    "Extração de Frames",
    "Extração de Áudio",
]

# Configurações de qualidade
QUALITY_PRESETS = {
    "Baixa": {"crf": 28, "preset": "fast"},
    "Média": {"crf": 23, "preset": "medium"},
    "Alta": {"crf": 18, "preset": "slow"},
    "Muito Alta": {"crf": 15, "preset": "veryslow"},
}

# Configurações específicas para WebP
WEBP_QUALITY_PRESETS = {
    "Baixa": {"quality": 50, "method": 4},
    "Média": {"quality": 75, "method": 4},
    "Alta": {"quality": 90, "method": 6},
    "Muito Alta": {"quality": 100, "method": 6},
}

# Configurações específicas para AVI
AVI_QUALITY_PRESETS = {
    "Baixa": {
        "crf": 26,  # Ligeiramente melhor que o padrão
        "preset": "fast",
        "profile": "main",
        "level": "3.1",
        "tune": "film",
    },
    "Média": {
        "crf": 21,  # Melhor qualidade que o padrão
        "preset": "medium",
        "profile": "main",
        "level": "4.0",
        "tune": "film",
    },
    "Alta": {
        "crf": 16,  # Qualidade superior
        "preset": "slow",
        "profile": "high",
        "level": "4.1",
        "tune": "film",
    },
    "Muito Alta": {
        "crf": 13,  # Qualidade máxima
        "preset": "veryslow",
        "profile": "high",
        "level": "4.1",
        "tune": "film",
    },
}

# Configurações de áudio específicas para AVI
AVI_AUDIO_CONFIG = {
    "codec": "mp3",
    "bitrate": "192k",  # Bitrate otimizado para MP3
    "sample_rate": "44100",
    "channels": 2,
    "quality": 2,  # Qualidade VBR para MP3 (0=melhor, 9=pior)
}

# ========================================
# CONFIGURAÇÕES DE EXTRAÇÃO DE ÁUDIO
# ========================================

# Formatos de áudio suportados para extração
SUPPORTED_AUDIO_FORMATS = [
    "MP3",
    "AAC",
    "WAV", 
    "FLAC",
    "OGG",
    "M4A",
    "WMA",
    "OPUS"
]

# Configurações de qualidade para cada formato de áudio
AUDIO_QUALITY_PRESETS = {
    "MP3": {
        "Baixa": {"bitrate": "128k", "quality": 4},
        "Média": {"bitrate": "192k", "quality": 2},
        "Alta": {"bitrate": "256k", "quality": 0},
        "Muito Alta": {"bitrate": "320k", "quality": 0},
    },
    "AAC": {
        "Baixa": {"bitrate": "128k", "profile": "aac_low"},
        "Média": {"bitrate": "192k", "profile": "aac_low"},
        "Alta": {"bitrate": "256k", "profile": "aac_low"},
        "Muito Alta": {"bitrate": "320k", "profile": "aac_low"},
    },
    "WAV": {
        "Baixa": {"sample_rate": "22050", "bit_depth": "16"},
        "Média": {"sample_rate": "44100", "bit_depth": "16"},
        "Alta": {"sample_rate": "48000", "bit_depth": "24"},
        "Muito Alta": {"sample_rate": "96000", "bit_depth": "24"},
    },
    "FLAC": {
        "Baixa": {"compression_level": 0, "sample_rate": "44100"},
        "Média": {"compression_level": 5, "sample_rate": "44100"},
        "Alta": {"compression_level": 8, "sample_rate": "48000"},
        "Muito Alta": {"compression_level": 12, "sample_rate": "96000"},
    },
    "OGG": {
        "Baixa": {"quality": 3, "bitrate": "128k"},
        "Média": {"quality": 6, "bitrate": "192k"},
        "Alta": {"quality": 8, "bitrate": "256k"},
        "Muito Alta": {"quality": 10, "bitrate": "320k"},
    },
    "M4A": {
        "Baixa": {"bitrate": "128k", "profile": "aac_low"},
        "Média": {"bitrate": "192k", "profile": "aac_low"},
        "Alta": {"bitrate": "256k", "profile": "aac_low"},
        "Muito Alta": {"bitrate": "320k", "profile": "aac_low"},
    },
    "WMA": {
        "Baixa": {"bitrate": "128k"},
        "Média": {"bitrate": "192k"},
        "Alta": {"bitrate": "256k"},
        "Muito Alta": {"bitrate": "320k"},
    },
    "OPUS": {
        "Baixa": {"bitrate": "96k", "application": "audio"},
        "Média": {"bitrate": "128k", "application": "audio"},
        "Alta": {"bitrate": "192k", "application": "audio"},
        "Muito Alta": {"bitrate": "256k", "application": "audio"},
    },
}

# Configurações de codec para cada formato de áudio
AUDIO_CODEC_CONFIG = {
    "MP3": {
        "codec": "libmp3lame",
        "extension": ".mp3",
        "container": "mp3",
        "supports_metadata": True,
        "supports_album_art": True,
    },
    "AAC": {
        "codec": "aac",
        "extension": ".aac",
        "container": "adts",
        "supports_metadata": True,
        "supports_album_art": False,
    },
    "WAV": {
        "codec": "pcm_s16le",
        "extension": ".wav",
        "container": "wav",
        "supports_metadata": False,
        "supports_album_art": False,
    },
    "FLAC": {
        "codec": "flac",
        "extension": ".flac",
        "container": "flac",
        "supports_metadata": True,
        "supports_album_art": True,
    },
    "OGG": {
        "codec": "libvorbis",
        "extension": ".ogg",
        "container": "ogg",
        "supports_metadata": True,
        "supports_album_art": True,
    },
    "M4A": {
        "codec": "aac",
        "extension": ".m4a",
        "container": "ipod",
        "supports_metadata": True,
        "supports_album_art": True,
    },
    "WMA": {
        "codec": "wmav2",
        "extension": ".wma",
        "container": "asf",
        "supports_metadata": True,
        "supports_album_art": False,
    },
    "OPUS": {
        "codec": "libopus",
        "extension": ".opus",
        "container": "ogg",
        "supports_metadata": True,
        "supports_album_art": False,
    },
}

# Configurações padrão para extração de áudio
AUDIO_EXTRACTION_DEFAULTS = {
    "format": "MP3",
    "quality": "Média",
    "preserve_metadata": True,
    "preserve_album_art": True,
    "normalize_audio": False,
    "remove_silence": False,
    "fade_in": 0.0,  # segundos
    "fade_out": 0.0,  # segundos
}

# Configurações de FPS
FPS_OPTIONS = ["Original", "24", "25", "30", "50", "60", "Personalizado"]

# Configurações de resolução
RESOLUTION_PRESETS = {
    "Original": None,
    "480p (SD)": (854, 480),
    "720p (HD)": (1280, 720),
    "1080p (Full HD)": (1920, 1080),
    "1440p (2K)": (2560, 1440),
    "2160p (4K)": (3840, 2160),
    "Personalizada": None,
}

# ========================================
# CONFIGURAÇÕES DE ACELERAÇÃO POR HARDWARE
# ========================================

# Configurações gerais de hardware
HARDWARE_ACCELERATION = {
    "enabled": True,  # Habilitar aceleração por hardware quando disponível
    "auto_detect": True,  # Detectar automaticamente hardware disponível
    "fallback_to_cpu": True,  # Usar CPU se hardware falhar
    "prefer_quality_over_speed": False,  # Priorizar qualidade sobre velocidade
}

# Configurações específicas para CUDA/NVENC
CUDA_CONFIG = {
    "enabled": True,
    "preferred_encoder": "h264_nvenc",  # Encoder padrão: h264_nvenc, hevc_nvenc, av1_nvenc
    "preferred_decoder": "auto",  # auto, h264_cuvid, hevc_cuvid, etc.
    "preset": "medium",  # fast, medium, slow, hq, bd, ll, llhq, llhp
    "profile": "auto",  # auto, baseline, main, high, high444p
    "level": "auto",  # auto, 3.0, 3.1, 4.0, 4.1, 5.0, 5.1, etc.
    "rc_mode": "vbr",  # cbr, vbr, cqp, constqp
    "gpu_index": 0,  # Índice da GPU a ser usada (0 = primeira GPU)
    "max_memory_usage": 0.8,  # Máximo de memória GPU a usar (0.0-1.0)
}

# Presets de qualidade específicos para NVENC
NVENC_QUALITY_PRESETS = {
    "Rápida": {
        "preset": "fast",
        "rc_mode": "vbr",
        "cq": 28,
        "maxrate": None,
        "bufsize": None,
        "profile": "auto",
    },
    "Balanceada": {
        "preset": "medium",
        "rc_mode": "vbr",
        "cq": 23,
        "maxrate": None,
        "bufsize": None,
        "profile": "auto",
    },
    "Qualidade": {
        "preset": "slow",
        "rc_mode": "vbr",
        "cq": 18,
        "maxrate": None,
        "bufsize": None,
        "profile": "high",
    },
    "Máxima Qualidade": {
        "preset": "hq",
        "rc_mode": "vbr",
        "cq": 15,
        "maxrate": None,
        "bufsize": None,
        "profile": "high",
    },
}

# Configurações específicas para diferentes codecs NVENC
NVENC_CODEC_SETTINGS = {
    "h264_nvenc": {
        "supported_profiles": ["baseline", "main", "high", "high444p"],
        "supported_levels": ["3.0", "3.1", "4.0", "4.1", "5.0", "5.1", "5.2"],
        "max_resolution": (4096, 4096),
        "recommended_bitrate_factor": 1.0,
    },
    "hevc_nvenc": {
        "supported_profiles": ["main", "main10", "rext"],
        "supported_levels": ["4.0", "4.1", "5.0", "5.1", "5.2", "6.0", "6.1", "6.2"],
        "max_resolution": (8192, 8192),
        "recommended_bitrate_factor": 0.7,  # HEVC é mais eficiente
    },
    "av1_nvenc": {
        "supported_profiles": ["main"],
        "supported_levels": ["4.0", "4.1", "5.0", "5.1", "5.2", "6.0"],
        "max_resolution": (8192, 8192),
        "recommended_bitrate_factor": 0.5,  # AV1 é muito mais eficiente
    },
}

# Configurações de fallback para CPU
CPU_FALLBACK_CONFIG = {
    "h264_encoder": "libx264",
    "hevc_encoder": "libx265",
    "av1_encoder": "libaom-av1",
    "quality_preset_mapping": {
        "Rápida": "fast",
        "Balanceada": "medium",
        "Qualidade": "slow",
        "Máxima Qualidade": "veryslow",
    },
}

# Configurações de benchmark e monitoramento
HARDWARE_MONITORING = {
    "enable_gpu_monitoring": True,
    "memory_check_interval": 5.0,  # segundos
    "temperature_warning_threshold": 85,  # °C
    "memory_warning_threshold": 0.9,  # 90% da memória GPU
    "enable_performance_logging": True,
}

# Configurações do FFmpeg
FFMPEG_TIMEOUT = 300  # 5 minutos
FFMPEG_PROGRESS_REGEX = r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})"

# URLs para download do FFmpeg
FFMPEG_DOWNLOAD_URLS = {
    "windows": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "darwin": "https://evermeet.cx/ffmpeg/getrelease/zip",
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
}

# Configurações da interface
WINDOW_MIN_SIZE = (800, 600)
WINDOW_DEFAULT_SIZE = (900, 700)

# Estilos CSS para PyQt6
MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #f0f0f0;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #cccccc;
    border-radius: 5px;
    margin-top: 1ex;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}

QPushButton {
    background-color: #4CAF50;
    border: none;
    color: white;
    padding: 8px 16px;
    text-align: center;
    font-size: 14px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #45a049;
}

QPushButton:pressed {
    background-color: #3d8b40;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QPushButton#cancel_btn {
    background-color: #f44336;
}

QPushButton#cancel_btn:hover {
    background-color: #da190b;
}

QPushButton#clear_btn {
    background-color: #ff9800;
}

QPushButton#clear_btn:hover {
    background-color: #e68900;
}

QProgressBar {
    border: 2px solid #cccccc;
    border-radius: 5px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #4CAF50;
    border-radius: 3px;
}

QTextEdit {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 5px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
}

QLineEdit {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 5px;
    font-size: 14px;
}

QComboBox {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 5px;
    font-size: 14px;
}

QSpinBox {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 5px;
    font-size: 14px;
}

QCheckBox {
    font-size: 14px;
}

QLabel {
    font-size: 14px;
}

QStatusBar {
    background-color: #e0e0e0;
    border-top: 1px solid #cccccc;
}
"""

# ========================================
# CLASSE DE CONFIGURAÇÃO DE HARDWARE
# ========================================


class HardwareConfig:
    """
    Classe para gerenciar configurações de hardware de forma dinâmica.
    Integra com o HardwareDetector para configuração automática.
    """

    def __init__(self):
        """Inicializa a configuração de hardware."""
        self._hardware_detector = None
        self._current_config = None
        self._auto_configured = False

    def get_hardware_detector(self):
        """Obtém instância do HardwareDetector de forma lazy."""
        if self._hardware_detector is None:
            try:
                from .hardware_detector import get_hardware_detector

                self._hardware_detector = get_hardware_detector()
            except ImportError as e:
                logger.warning(f"Não foi possível importar HardwareDetector: {e}")
                self._hardware_detector = None
        return self._hardware_detector

    def auto_configure(self) -> Dict:
        """
        Configura automaticamente baseado no hardware detectado.

        Returns:
            Dict com configurações otimizadas para o hardware atual
        """
        detector = self.get_hardware_detector()
        if not detector:
            logger.warning(
                "HardwareDetector não disponível, usando configuração padrão"
            )
            return self._get_cpu_only_config()

        config = {
            "hardware_acceleration": HARDWARE_ACCELERATION.copy(),
            "cuda_config": CUDA_CONFIG.copy(),
            "quality_presets": {},
            "recommended_settings": {},
        }

        # Verifica se CUDA está disponível
        if detector.is_cuda_available():
            logger.info("CUDA detectado, configurando aceleração por hardware")
            config = self._configure_cuda(config, detector)
        else:
            logger.info("CUDA não disponível, configurando para CPU apenas")
            config = self._configure_cpu_only(config)

        self._current_config = config
        self._auto_configured = True
        return config

    def _configure_cuda(self, config: Dict, detector) -> Dict:
        """Configura para uso com CUDA."""
        # Habilita aceleração por hardware
        config["hardware_acceleration"]["enabled"] = True

        # Obtém encoders e decoders disponíveis
        cuda_encoders = detector.get_cuda_encoders()
        cuda_decoders = detector.get_cuda_decoders()

        # Configura encoder preferido baseado na disponibilidade
        if "h264_nvenc" in cuda_encoders:
            config["cuda_config"]["preferred_encoder"] = "h264_nvenc"
        elif "hevc_nvenc" in cuda_encoders:
            config["cuda_config"]["preferred_encoder"] = "hevc_nvenc"
        elif "av1_nvenc" in cuda_encoders:
            config["cuda_config"]["preferred_encoder"] = "av1_nvenc"

        # Configura decoder preferido
        if "h264_cuvid" in cuda_decoders:
            config["cuda_config"]["preferred_decoder"] = "h264_cuvid"

        # Obtém informações de memória da GPU
        memory_info = detector.get_gpu_memory_info()
        if memory_info:
            total_mb, free_mb = memory_info
            # Ajusta uso máximo de memória baseado na memória disponível
            if total_mb < 2048:  # Menos de 2GB
                config["cuda_config"]["max_memory_usage"] = 0.6
                config["cuda_config"]["preset"] = "fast"
            elif total_mb < 4096:  # Menos de 4GB
                config["cuda_config"]["max_memory_usage"] = 0.7
                config["cuda_config"]["preset"] = "medium"
            else:  # 4GB ou mais
                config["cuda_config"]["max_memory_usage"] = 0.8
                config["cuda_config"]["preset"] = "slow"

        # Configura presets de qualidade para NVENC
        config["quality_presets"] = NVENC_QUALITY_PRESETS.copy()

        # Configurações recomendadas
        config["recommended_settings"] = {
            "use_hardware_acceleration": True,
            "preferred_format": "MP4",
            "recommended_encoder": config["cuda_config"]["preferred_encoder"],
            "recommended_decoder": config["cuda_config"]["preferred_decoder"],
            "performance_mode": "balanced",
        }

        return config

    def _configure_cpu_only(self, config: Dict) -> Dict:
        """Configura para uso apenas com CPU."""
        config["hardware_acceleration"]["enabled"] = False
        config["cuda_config"]["enabled"] = False

        # Usa presets de qualidade padrão para CPU
        config["quality_presets"] = QUALITY_PRESETS.copy()

        # Configurações recomendadas para CPU
        config["recommended_settings"] = {
            "use_hardware_acceleration": False,
            "preferred_format": "MP4",
            "recommended_encoder": "libx264",
            "recommended_decoder": "auto",
            "performance_mode": "quality",
        }

        return config

    def _get_cpu_only_config(self) -> Dict:
        """Retorna configuração padrão para CPU apenas."""
        return self._configure_cpu_only(
            {
                "hardware_acceleration": HARDWARE_ACCELERATION.copy(),
                "cuda_config": CUDA_CONFIG.copy(),
                "quality_presets": {},
                "recommended_settings": {},
            }
        )

    def get_encoder_for_format(
        self, output_format: str, use_hardware: bool = True
    ) -> str:
        """
        Retorna o encoder recomendado para um formato específico.

        Args:
            output_format: Formato de saída (MP4, MKV, etc.)
            use_hardware: Se deve usar aceleração por hardware quando disponível

        Returns:
            Nome do encoder recomendado
        """
        if not self._current_config:
            self.auto_configure()

        format_lower = output_format.lower()

        if use_hardware and self._current_config["hardware_acceleration"]["enabled"]:
            # Usa encoder de hardware se disponível
            if format_lower in ["mp4", "mkv", "mov"]:
                return self._current_config["cuda_config"]["preferred_encoder"]

        # Fallback para CPU
        if format_lower in ["mp4", "mkv", "mov"]:
            return CPU_FALLBACK_CONFIG["h264_encoder"]
        elif format_lower == "webm":
            return "libvpx-vp9"
        else:
            return "libx264"  # Padrão seguro

    def get_quality_preset(self, quality_name: str) -> Dict:
        """
        Retorna configurações de qualidade baseadas no hardware.

        Args:
            quality_name: Nome do preset de qualidade

        Returns:
            Dict com configurações de qualidade
        """
        if not self._current_config:
            self.auto_configure()

        presets = self._current_config.get("quality_presets", QUALITY_PRESETS)
        return presets.get(
            quality_name, presets.get("Média", {"crf": 23, "preset": "medium"})
        )

    def is_hardware_acceleration_available(self) -> bool:
        """Verifica se aceleração por hardware está disponível."""
        if not self._current_config:
            self.auto_configure()

        return self._current_config["hardware_acceleration"]["enabled"]

    def get_hardware_summary(self) -> Dict:
        """Retorna resumo do hardware detectado."""
        detector = self.get_hardware_detector()
        if detector:
            return detector.get_hardware_summary()
        return {"cuda_available": False, "nvidia_gpu": None}

    def validate_settings(
        self, encoder: str, resolution: Tuple[int, int] = None
    ) -> bool:
        """
        Valida se as configurações são suportadas pelo hardware.

        Args:
            encoder: Nome do encoder
            resolution: Resolução (largura, altura)

        Returns:
            True se as configurações são válidas
        """
        if encoder in NVENC_CODEC_SETTINGS:
            codec_settings = NVENC_CODEC_SETTINGS[encoder]

            # Verifica resolução máxima
            if resolution:
                max_width, max_height = codec_settings["max_resolution"]
                if resolution[0] > max_width or resolution[1] > max_height:
                    return False

        return True


# Instância global da configuração de hardware
_hardware_config = None


def get_hardware_config() -> HardwareConfig:
    """
    Retorna instância singleton da configuração de hardware.

    Returns:
        Instância de HardwareConfig
    """
    global _hardware_config
    if _hardware_config is None:
        _hardware_config = HardwareConfig()
    return _hardware_config


def auto_configure_hardware() -> Dict:
    """
    Configura automaticamente o hardware e retorna as configurações.

    Returns:
        Dict com configurações otimizadas
    """
    return get_hardware_config().auto_configure()


# ========================================
# CONFIGURAÇÕES PARA GIF ANIMADO AVANÇADO
# ========================================

# Presets de qualidade para GIF
GIF_QUALITY_PRESETS = {
    "Baixa": {
        "fps": 10,
        "colors": 64,
        "scale_width": 480,
        "dithering": True,
        "optimize": "size",
        "description": "Menor tamanho, qualidade básica",
    },
    "Média": {
        "fps": 15,
        "colors": 128,
        "scale_width": 640,
        "dithering": True,
        "optimize": "balanced",
        "description": "Equilíbrio entre tamanho e qualidade",
    },
    "Alta": {
        "fps": 24,
        "colors": 256,
        "scale_width": 720,
        "dithering": True,
        "optimize": "quality",
        "description": "Alta qualidade, tamanho moderado",
    },
    "Muito Alta": {
        "fps": 30,
        "colors": 256,
        "scale_width": 1080,
        "dithering": False,
        "optimize": "quality",
        "description": "Máxima qualidade, maior tamanho",
    },
    "Personalizada": {
        "fps": 15,
        "colors": 256,
        "scale_width": 640,
        "dithering": True,
        "optimize": "balanced",
        "description": "Configurações personalizáveis",
    },
}

# Opções de FPS para GIF
GIF_FPS_OPTIONS = ["5", "10", "12", "15", "20", "24", "25", "30", "Personalizado"]

# Opções de cores para GIF
GIF_COLOR_OPTIONS = ["16", "32", "64", "128", "256", "Personalizado"]

# Opções de resolução para GIF
GIF_RESOLUTION_PRESETS = {
    "Original": None,
    "320p": (320, 240),
    "480p": (640, 480),
    "640p": (640, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "Personalizada": None,
}

# Configurações de otimização para GIF
GIF_OPTIMIZATION_MODES = {
    "size": {"flags": "lanczos", "stats_mode": "diff", "dither": "bayer:bayer_scale=2"},
    "balanced": {"flags": "lanczos", "stats_mode": "full", "dither": "floyd_steinberg"},
    "quality": {"flags": "lanczos", "stats_mode": "full", "dither": "none"},
}

# ========================================
# CONFIGURAÇÕES PARA EXTRAÇÃO DE FRAMES
# ========================================

# Formatos suportados para extração de frames
FRAME_EXTRACTION_FORMATS = {
    "JPG": {
        "extension": ".jpg",
        "quality_param": "-q:v",
        "quality_range": (1, 31),  # 1=melhor, 31=pior
        "default_quality": 2,
        "supports_transparency": False,
        "description": "JPEG - Alta compatibilidade, menor tamanho",
    },
    "PNG": {
        "extension": ".png",
        "quality_param": "-compression_level",
        "quality_range": (0, 9),  # 0=sem compressão, 9=máxima compressão
        "default_quality": 6,
        "supports_transparency": True,
        "description": "PNG - Sem perda, suporte à transparência",
    },
    "WebP": {
        "extension": ".webp",
        "quality_param": "-quality",
        "quality_range": (0, 100),  # 0=pior, 100=melhor
        "default_quality": 90,
        "supports_transparency": True,
        "lossless_option": True,
        "description": "WebP - Moderno, eficiente, com transparência",
    },
    "TIFF": {
        "extension": ".tiff",
        "quality_param": "-compression",
        "compression_options": ["none", "lzw", "zip"],
        "default_compression": "lzw",
        "supports_transparency": True,
        "description": "TIFF - Qualidade profissional, sem perda",
    },
}

# Modos de extração de frames
FRAME_EXTRACTION_MODES = {
    "all_frames": {
        "name": "Todos os Frames",
        "description": "Extrai todos os frames do vídeo",
        "ffmpeg_filter": "fps=fps=source_fps",
    },
    "interval_seconds": {
        "name": "Intervalo (Segundos)",
        "description": "Extrai 1 frame a cada X segundos",
        "ffmpeg_filter": "fps=1/{interval}",
    },
    "interval_frames": {
        "name": "Intervalo (Frames)",
        "description": "Extrai 1 frame a cada X frames",
        "ffmpeg_filter": "select=not(mod(n\\,{interval}))",
    },
    "specific_times": {
        "name": "Tempos Específicos",
        "description": "Extrai frames em timestamps específicos",
        "ffmpeg_filter": "select=eq(t\\,{timestamp})",
    },
    "key_points": {
        "name": "Pontos-Chave",
        "description": "Extrai frames no início, meio e fim",
        "ffmpeg_filter": "select=eq(n\\,0)+eq(n\\,{middle})+eq(n\\,{end})",
    },
}

# Configurações de qualidade para WebP com transparência
WEBP_FRAME_PRESETS = {
    "Rápida": {
        "quality": 75,
        "method": 4,
        "lossless": False,
        "alpha_quality": 90,
        "description": "Conversão rápida, boa qualidade",
    },
    "Balanceada": {
        "quality": 85,
        "method": 4,
        "lossless": False,
        "alpha_quality": 95,
        "description": "Equilíbrio entre velocidade e qualidade",
    },
    "Qualidade": {
        "quality": 95,
        "method": 6,
        "lossless": False,
        "alpha_quality": 100,
        "description": "Alta qualidade com transparência preservada",
    },
    "Lossless": {
        "quality": 100,
        "method": 6,
        "lossless": True,
        "alpha_quality": 100,
        "description": "Sem perda, máxima qualidade",
    },
}

# Configurações de resolução para frames
FRAME_RESOLUTION_PRESETS = {
    "Original": None,
    "480p": (854, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "2160p": (3840, 2160),
    "Personalizada": None,
}

# Configurações de nomenclatura para frames extraídos
FRAME_NAMING_PATTERNS = {
    "sequential": "frame_{:04d}",
    "timestamp": "frame_{timestamp}",
    "timecode": "frame_{hours:02d}h{minutes:02d}m{seconds:02d}s",
    "custom": "{custom_prefix}_{:04d}",
}

# Configurações padrão para extração de frames
DEFAULT_FRAME_EXTRACTION_SETTINGS = {
    "format": "PNG",
    "quality": "Balanceada",
    "resolution": "Original",
    "mode": "interval_seconds",
    "interval": 1,
    "create_subfolder": True,
    "naming_pattern": "sequential",
    "preserve_aspect_ratio": True,
}
