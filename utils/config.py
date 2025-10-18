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
    'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v',
    '3gp', 'mpg', 'mpeg', 'ts', 'mts', 'm2ts', 'vob', 'ogv'
]

SUPPORTED_OUTPUT_FORMATS = [
    'MP4', 'AVI', 'MOV', 'MKV', 'WEBM', 'WEBP', 'FLV', 'WMV', 'M4V'
]

# Configurações de qualidade
QUALITY_PRESETS = {
    'Baixa': {'crf': 28, 'preset': 'fast'},
    'Média': {'crf': 23, 'preset': 'medium'},
    'Alta': {'crf': 18, 'preset': 'slow'},
    'Muito Alta': {'crf': 15, 'preset': 'veryslow'}
}

# Configurações específicas para WebP
WEBP_QUALITY_PRESETS = {
    'Baixa': {'quality': 50, 'method': 4},
    'Média': {'quality': 75, 'method': 4},
    'Alta': {'quality': 90, 'method': 6},
    'Muito Alta': {'quality': 100, 'method': 6}
}

# Configurações de FPS
FPS_OPTIONS = ['Original', '24', '25', '30', '50', '60', 'Personalizado']

# Configurações de resolução
RESOLUTION_PRESETS = {
    'Original': None,
    '480p (SD)': (854, 480),
    '720p (HD)': (1280, 720),
    '1080p (Full HD)': (1920, 1080),
    '1440p (2K)': (2560, 1440),
    '2160p (4K)': (3840, 2160),
    'Personalizada': None
}

# ========================================
# CONFIGURAÇÕES DE ACELERAÇÃO POR HARDWARE
# ========================================

# Configurações gerais de hardware
HARDWARE_ACCELERATION = {
    'enabled': True,  # Habilitar aceleração por hardware quando disponível
    'auto_detect': True,  # Detectar automaticamente hardware disponível
    'fallback_to_cpu': True,  # Usar CPU se hardware falhar
    'prefer_quality_over_speed': False,  # Priorizar qualidade sobre velocidade
}

# Configurações específicas para CUDA/NVENC
CUDA_CONFIG = {
    'enabled': True,
    'preferred_encoder': 'h264_nvenc',  # Encoder padrão: h264_nvenc, hevc_nvenc, av1_nvenc
    'preferred_decoder': 'auto',  # auto, h264_cuvid, hevc_cuvid, etc.
    'preset': 'medium',  # fast, medium, slow, hq, bd, ll, llhq, llhp
    'profile': 'auto',  # auto, baseline, main, high, high444p
    'level': 'auto',  # auto, 3.0, 3.1, 4.0, 4.1, 5.0, 5.1, etc.
    'rc_mode': 'vbr',  # cbr, vbr, cqp, constqp
    'gpu_index': 0,  # Índice da GPU a ser usada (0 = primeira GPU)
    'max_memory_usage': 0.8,  # Máximo de memória GPU a usar (0.0-1.0)
}

# Presets de qualidade específicos para NVENC
NVENC_QUALITY_PRESETS = {
    'Rápida': {
        'preset': 'fast',
        'rc_mode': 'vbr',
        'cq': 28,
        'maxrate': None,
        'bufsize': None,
        'profile': 'auto'
    },
    'Balanceada': {
        'preset': 'medium', 
        'rc_mode': 'vbr',
        'cq': 23,
        'maxrate': None,
        'bufsize': None,
        'profile': 'auto'
    },
    'Qualidade': {
        'preset': 'slow',
        'rc_mode': 'vbr', 
        'cq': 18,
        'maxrate': None,
        'bufsize': None,
        'profile': 'high'
    },
    'Máxima Qualidade': {
        'preset': 'hq',
        'rc_mode': 'vbr',
        'cq': 15,
        'maxrate': None,
        'bufsize': None,
        'profile': 'high'
    }
}

# Configurações específicas para diferentes codecs NVENC
NVENC_CODEC_SETTINGS = {
    'h264_nvenc': {
        'supported_profiles': ['baseline', 'main', 'high', 'high444p'],
        'supported_levels': ['3.0', '3.1', '4.0', '4.1', '5.0', '5.1', '5.2'],
        'max_resolution': (4096, 4096),
        'recommended_bitrate_factor': 1.0
    },
    'hevc_nvenc': {
        'supported_profiles': ['main', 'main10', 'rext'],
        'supported_levels': ['4.0', '4.1', '5.0', '5.1', '5.2', '6.0', '6.1', '6.2'],
        'max_resolution': (8192, 8192),
        'recommended_bitrate_factor': 0.7  # HEVC é mais eficiente
    },
    'av1_nvenc': {
        'supported_profiles': ['main'],
        'supported_levels': ['4.0', '4.1', '5.0', '5.1', '5.2', '6.0'],
        'max_resolution': (8192, 8192),
        'recommended_bitrate_factor': 0.5  # AV1 é muito mais eficiente
    }
}

# Configurações de fallback para CPU
CPU_FALLBACK_CONFIG = {
    'h264_encoder': 'libx264',
    'hevc_encoder': 'libx265', 
    'av1_encoder': 'libaom-av1',
    'quality_preset_mapping': {
        'Rápida': 'fast',
        'Balanceada': 'medium',
        'Qualidade': 'slow',
        'Máxima Qualidade': 'veryslow'
    }
}

# Configurações de benchmark e monitoramento
HARDWARE_MONITORING = {
    'enable_gpu_monitoring': True,
    'memory_check_interval': 5.0,  # segundos
    'temperature_warning_threshold': 85,  # °C
    'memory_warning_threshold': 0.9,  # 90% da memória GPU
    'enable_performance_logging': True
}

# Configurações do FFmpeg
FFMPEG_TIMEOUT = 300  # 5 minutos
FFMPEG_PROGRESS_REGEX = r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})'

# URLs para download do FFmpeg
FFMPEG_DOWNLOAD_URLS = {
    'windows': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
    'darwin': 'https://evermeet.cx/ffmpeg/getrelease/zip',
    'linux': 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz'
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
            logger.warning("HardwareDetector não disponível, usando configuração padrão")
            return self._get_cpu_only_config()
        
        config = {
            'hardware_acceleration': HARDWARE_ACCELERATION.copy(),
            'cuda_config': CUDA_CONFIG.copy(),
            'quality_presets': {},
            'recommended_settings': {}
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
        config['hardware_acceleration']['enabled'] = True
        
        # Obtém encoders e decoders disponíveis
        cuda_encoders = detector.get_cuda_encoders()
        cuda_decoders = detector.get_cuda_decoders()
        
        # Configura encoder preferido baseado na disponibilidade
        if 'h264_nvenc' in cuda_encoders:
            config['cuda_config']['preferred_encoder'] = 'h264_nvenc'
        elif 'hevc_nvenc' in cuda_encoders:
            config['cuda_config']['preferred_encoder'] = 'hevc_nvenc'
        elif 'av1_nvenc' in cuda_encoders:
            config['cuda_config']['preferred_encoder'] = 'av1_nvenc'
        
        # Configura decoder preferido
        if 'h264_cuvid' in cuda_decoders:
            config['cuda_config']['preferred_decoder'] = 'h264_cuvid'
        
        # Obtém informações de memória da GPU
        memory_info = detector.get_gpu_memory_info()
        if memory_info:
            total_mb, free_mb = memory_info
            # Ajusta uso máximo de memória baseado na memória disponível
            if total_mb < 2048:  # Menos de 2GB
                config['cuda_config']['max_memory_usage'] = 0.6
                config['cuda_config']['preset'] = 'fast'
            elif total_mb < 4096:  # Menos de 4GB
                config['cuda_config']['max_memory_usage'] = 0.7
                config['cuda_config']['preset'] = 'medium'
            else:  # 4GB ou mais
                config['cuda_config']['max_memory_usage'] = 0.8
                config['cuda_config']['preset'] = 'slow'
        
        # Configura presets de qualidade para NVENC
        config['quality_presets'] = NVENC_QUALITY_PRESETS.copy()
        
        # Configurações recomendadas
        config['recommended_settings'] = {
            'use_hardware_acceleration': True,
            'preferred_format': 'MP4',
            'recommended_encoder': config['cuda_config']['preferred_encoder'],
            'recommended_decoder': config['cuda_config']['preferred_decoder'],
            'performance_mode': 'balanced'
        }
        
        return config
    
    def _configure_cpu_only(self, config: Dict) -> Dict:
        """Configura para uso apenas com CPU."""
        config['hardware_acceleration']['enabled'] = False
        config['cuda_config']['enabled'] = False
        
        # Usa presets de qualidade padrão para CPU
        config['quality_presets'] = QUALITY_PRESETS.copy()
        
        # Configurações recomendadas para CPU
        config['recommended_settings'] = {
            'use_hardware_acceleration': False,
            'preferred_format': 'MP4',
            'recommended_encoder': 'libx264',
            'recommended_decoder': 'auto',
            'performance_mode': 'quality'
        }
        
        return config
    
    def _get_cpu_only_config(self) -> Dict:
        """Retorna configuração padrão para CPU apenas."""
        return self._configure_cpu_only({
            'hardware_acceleration': HARDWARE_ACCELERATION.copy(),
            'cuda_config': CUDA_CONFIG.copy(),
            'quality_presets': {},
            'recommended_settings': {}
        })
    
    def get_encoder_for_format(self, output_format: str, use_hardware: bool = True) -> str:
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
        
        if use_hardware and self._current_config['hardware_acceleration']['enabled']:
            # Usa encoder de hardware se disponível
            if format_lower in ['mp4', 'mkv', 'mov']:
                return self._current_config['cuda_config']['preferred_encoder']
        
        # Fallback para CPU
        if format_lower in ['mp4', 'mkv', 'mov']:
            return CPU_FALLBACK_CONFIG['h264_encoder']
        elif format_lower == 'webm':
            return 'libvpx-vp9'
        else:
            return 'libx264'  # Padrão seguro
    
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
        
        presets = self._current_config.get('quality_presets', QUALITY_PRESETS)
        return presets.get(quality_name, presets.get('Média', {'crf': 23, 'preset': 'medium'}))
    
    def is_hardware_acceleration_available(self) -> bool:
        """Verifica se aceleração por hardware está disponível."""
        if not self._current_config:
            self.auto_configure()
        
        return self._current_config['hardware_acceleration']['enabled']
    
    def get_hardware_summary(self) -> Dict:
        """Retorna resumo do hardware detectado."""
        detector = self.get_hardware_detector()
        if detector:
            return detector.get_hardware_summary()
        return {'cuda_available': False, 'nvidia_gpu': None}
    
    def validate_settings(self, encoder: str, resolution: Tuple[int, int] = None) -> bool:
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
                max_width, max_height = codec_settings['max_resolution']
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