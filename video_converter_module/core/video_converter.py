"""
Motor de Conversão de Vídeos
Gerencia a conversão de vídeos usando FFmpeg com configurações avançadas
"""

import os
import subprocess
import threading
import time
import re
import uuid
from pathlib import Path

from utils.config import (
    SUPPORTED_INPUT_FORMATS,
    QUALITY_PRESETS,
    RESOLUTION_PRESETS,
    FFMPEG_TIMEOUT,
    FFMPEG_PROGRESS_REGEX,
    get_hardware_config,
    NVENC_QUALITY_PRESETS,
    NVENC_CODEC_SETTINGS,
    AVI_QUALITY_PRESETS,
    AVI_AUDIO_CONFIG,
    GIF_QUALITY_PRESETS,
    GIF_FPS_OPTIONS,
    GIF_COLOR_OPTIONS,
    GIF_RESOLUTION_PRESETS,
    FRAME_EXTRACTION_FORMATS,
    FRAME_EXTRACTION_MODES,
    WEBP_FRAME_PRESETS,
    SUPPORTED_AUDIO_FORMATS,
    AUDIO_QUALITY_PRESETS,
    AUDIO_CODEC_CONFIG,
    AUDIO_EXTRACTION_DEFAULTS,
)
from utils.universal_hardware_manager import UniversalHardwareManager
from utils.hardware_integration import HardwareIntegration
from utils.validators import (
    validate_input_file,
    validate_output_directory,
    validate_conversion_settings,
    generate_output_filename,
)
from .ffmpeg_installer import FFmpegInstaller
from .video_converter_manager import VideoConverterManager


class VideoConverter(threading.Thread):
    """
    Thread para conversão de vídeo usando FFmpeg
    """

    def __init__(self):
        super().__init__()
        self.ffmpeg_installer = FFmpegInstaller()
        self.input_file = ""
        self.output_file = ""
        self.conversion_settings = {}
        self.process = None
        self.cancelled = False
        self.callbacks = {}
        self.monitor_threads = {'stdout': None, 'stderr': None}

        # Sistema Universal de Hardware
        self.hardware_manager = UniversalHardwareManager()
        self.hardware_integration = HardwareIntegration()
        
        # Configuração de hardware (compatibilidade com código antigo)
        self.hardware_config_obj = get_hardware_config()
        self.hardware_config = self.hardware_config_obj.auto_configure()
        self.hw_settings = self.hardware_config.get("hardware_acceleration", {})
        self.cuda_available = self.hardware_config.get("hardware_acceleration", {}).get(
            "enabled", False
        )
        self.cuda_fallback_attempted = False
        
        # Inicializar sistema universal
        try:
            self.hardware_manager.initialize()
            self._call_callback("log", f"Sistema universal de hardware inicializado: {self.hardware_manager.get_hardware_status()}")
        except Exception as e:
            self._call_callback("log", f"Erro ao inicializar sistema universal: {e}")
            self._call_callback("log", "Usando sistema de hardware legado")

    def set_conversion_parameters(
        self, input_file, output_file, settings, callbacks=None
    ):
        """
        Define os parâmetros para conversão

        Args:
            input_file: Caminho do arquivo de entrada
            output_file: Caminho do arquivo de saída
            settings: Dicionário com configurações de conversão
            callbacks: Dicionário com funções callback
        """
        # Log dos parâmetros recebidos
        self._call_callback("log", f"Parâmetros de conversão - Input: {input_file}")
        self._call_callback("log", f"Parâmetros de conversão - Output: {output_file}")

        # Garantir que os caminhos sejam absolutos
        self.input_file = os.path.abspath(input_file) if input_file else input_file
        self.output_file = os.path.abspath(output_file) if output_file else output_file

        # Log dos caminhos processados
        self._call_callback("log", f"Caminho input processado: {self.input_file}")
        self._call_callback("log", f"Caminho output processado: {self.output_file}")

        self.conversion_settings = settings
        self.callbacks = callbacks or {}
        self.cancelled = False

    def get_video_info(self, file_path):
        """
        Obtém informações do vídeo usando FFprobe

        Args:
            file_path: Caminho do arquivo de vídeo

        Returns:
            dict: Informações do vídeo (duração, resolução, fps, etc.)
        """
        ffmpeg_cmd = self.ffmpeg_installer.get_ffmpeg_command()
        if not ffmpeg_cmd:
            return None

        # Usar ffprobe para obter informações
        ffprobe_cmd = ffmpeg_cmd.replace("ffmpeg", "ffprobe")

        # Log do caminho original recebido
        self._call_callback("log", f"Caminho original recebido: {file_path}")

        # Garantir que o caminho do arquivo seja absoluto e exista
        abs_file_path = os.path.abspath(file_path)
        self._call_callback("log", f"Caminho absoluto: {abs_file_path}")

        if not os.path.exists(abs_file_path):
            self._call_callback("log", f"Arquivo não encontrado: {abs_file_path}")
            # Tentar verificar se existe em outros locais comuns
            possible_paths = [
                file_path,
                file_path.replace("/", "\\"),
                file_path.replace("\\", "/"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    self._call_callback("log", f"Arquivo encontrado em: {path}")
                    abs_file_path = os.path.abspath(path)
                    break
            else:
                return None

        cmd = [
            ffprobe_cmd,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            abs_file_path,
        ]

        try:
            # Log do comando completo que será executado
            self._call_callback("log", f"Comando FFprobe: {' '.join(cmd)}")
            self._call_callback("log", f"Diretório de trabalho: {os.getcwd()}")

            result = self._run_subprocess_with_logging(cmd, timeout=30, context="FFprobe")

            if result and result.returncode == 0:
                import json

                info = json.loads(result.stdout)
                return self.parse_video_info(info)
            elif result:
                self._call_callback(
                    "log",
                    f"FFprobe falhou com código {result.returncode}: {result.stderr}",
                )
        except Exception as e:
            self._call_callback("log", f"Erro ao obter informações do vídeo: {str(e)}")
            self._call_callback("log", f"Tipo do erro: {type(e).__name__}")

        return None

    def parse_video_info(self, ffprobe_info):
        """
        Processa informações do FFprobe

        Args:
            ffprobe_info: Dados JSON do FFprobe

        Returns:
            dict: Informações processadas do vídeo
        """
        video_info = {
            "duration": 0,
            "width": 0,
            "height": 0,
            "fps": 0,
            "codec": "",
            "has_audio": False,
        }

        try:
            # Duração total
            if "format" in ffprobe_info and "duration" in ffprobe_info["format"]:
                video_info["duration"] = float(ffprobe_info["format"]["duration"])

            # Informações dos streams
            for stream in ffprobe_info.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_info["width"] = stream.get("width", 0)
                    video_info["height"] = stream.get("height", 0)
                    video_info["codec"] = stream.get("codec_name", "")

                    # FPS
                    fps_str = stream.get("r_frame_rate", "0/1")
                    if "/" in fps_str:
                        fps_parts = fps_str.split("/")
                        if len(fps_parts) == 2:
                            try:
                                num, den = fps_parts
                                if int(den) > 0:
                                    video_info["fps"] = round(int(num) / int(den), 2)
                            except (ValueError, TypeError) as e:
                                self._call_callback(
                                    "log",
                                    f"Erro ao processar FPS '{fps_str}': {str(e)}",
                                )
                                video_info["fps"] = 0

                elif stream.get("codec_type") == "audio":
                    video_info["has_audio"] = True

        except Exception as e:
            self._call_callback("log", f"Erro ao processar informações: {str(e)}")

        return video_info

    def has_audio_stream(self, file_path):
        """
        Verifica se o arquivo de vídeo contém streams de áudio

        Args:
            file_path: Caminho para o arquivo de vídeo

        Returns:
            bool: True se contém áudio, False caso contrário
        """
        try:
            ffprobe_cmd = self.ffmpeg_installer.get_ffprobe_command()
            if not ffprobe_cmd:
                self._call_callback("log", "FFprobe não encontrado para verificar streams de áudio")
                return False

            # Comando para verificar streams de áudio
            cmd = [
                ffprobe_cmd,
                "-v", "quiet",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                file_path
            ]

            result = self._run_subprocess_with_logging(cmd, timeout=30, context="FFprobe-audio")

            # Se encontrou stream de áudio, retorna True
            return result.returncode == 0 and "audio" in result.stdout.lower()

        except Exception as e:
            self._call_callback("log", f"Erro ao verificar streams de áudio: {str(e)}")
            return False

    def build_ffmpeg_command(self):
        """
        Constrói o comando FFmpeg baseado nas configurações

        Returns:
            list: Lista com argumentos do comando FFmpeg
        """
        ffmpeg_cmd = self.ffmpeg_installer.get_ffmpeg_command()
        if not ffmpeg_cmd:
            raise Exception("FFmpeg não encontrado")

        cmd = [ffmpeg_cmd]

        # Verificar se é GIF ou extração de frames
        format_name = self.conversion_settings.get("format", "")

        if "GIF (Animado)" in format_name:
            return self.build_gif_command(cmd)
        elif "Extração de Frames" in format_name:
            return self.build_frame_extraction_command(cmd)
        elif "Extração de Áudio" in format_name:
            return self.build_audio_extraction_command(cmd)

        # Configurações de decodificação CUDA (se disponível)
        self.add_cuda_decoder_settings(cmd)

        # Arquivo de entrada
        cmd.extend(["-i", self.input_file])

        # Configurações de vídeo
        self.add_video_settings(cmd)

        # Configurações de áudio
        self.add_audio_settings(cmd)

        # Configurações gerais
        cmd.extend(["-y"])  # Sobrescrever arquivo de saída

        # Arquivo de saída
        cmd.append(self.output_file)

        return cmd

    def build_gif_command(self, cmd):
        """
        Constrói comando FFmpeg específico para exportação de GIF animado
        Implementa processo otimizado com filtros complexos para alta qualidade

        Args:
            cmd: Lista base do comando FFmpeg

        Returns:
            list: Comando FFmpeg completo para GIF
        """
        settings = self.conversion_settings
        gif_settings = settings.get("gif_settings", {})

        # LOG DETALHADO: Diagnóstico de processamento de GIF
        self._log_operation_start("GIF", gif_settings)

        # Preparar entrada e diagnósticos básicos
        self._prepare_input_and_basic_diagnostics(cmd, "GIF")

        # Configurações de FPS
        gif_fps = gif_settings.get("fps", "15")

        # Configurações de resolução máxima
        max_resolution = gif_settings.get("max_resolution", "480p")

        # Configurações de qualidade e cores
        quality = gif_settings.get("quality", "Média")
        colors = gif_settings.get("colors", "256")
        dithering = gif_settings.get("dithering", True)
        optimization = gif_settings.get("optimization", True)

        # Construir filtros de vídeo
        filters = []

        # Filtro de FPS
        if gif_fps != "Original":
            filters.append(f"fps={gif_fps}")

        # Filtro de resolução
        if max_resolution != "Original" and max_resolution in GIF_RESOLUTION_PRESETS:
            width, height = GIF_RESOLUTION_PRESETS[max_resolution]
            scale_filter = f"scale='min({width},iw)':'min({height},ih)':force_original_aspect_ratio=decrease"
            filters.append(scale_filter)

        # Configurações de paleta baseadas na qualidade
        palette_options = f"max_colors={colors}"
        if quality in GIF_QUALITY_PRESETS:
            preset = GIF_QUALITY_PRESETS[quality]
            if dithering and preset.get("dithering", True):
                palette_options += ":stats_mode=diff"
            else:
                palette_options += ":stats_mode=single"

        # Usar filtro complexo para processo de duas etapas otimizado
        # Isso gera a paleta e aplica em uma única passagem
        complex_filter = ""
        if filters:
            # Aplicar filtros de pré-processamento
            complex_filter = f"[0:v]{','.join(filters)}[v];"
            # Gerar paleta a partir do vídeo processado
            complex_filter += f"[v]palettegen={palette_options}[p];"
            # Aplicar paleta ao vídeo processado
            dither_option = "floyd_steinberg" if dithering else "none"
            complex_filter += f"[v][p]paletteuse=dither={dither_option}"
        else:
            # Sem filtros de pré-processamento
            complex_filter = f"[0:v]palettegen={palette_options}[p];"
            dither_option = "floyd_steinberg" if dithering else "none"
            complex_filter += f"[0:v][p]paletteuse=dither={dither_option}"

        cmd.extend(["-filter_complex", complex_filter])

        # Configurações de otimização
        if optimization:
            cmd.extend(["-loop", "0"])  # Loop infinito

        # Configurações gerais
        self._append_overwrite_flag(cmd)

        # CORREÇÃO CRÍTICA: Limpar nome do arquivo de saída para GIF
        # Remover caracteres problemáticos que causam erro no FFmpeg
        output_file_clean = self.output_file
        if "(Animado)" in output_file_clean:
            # Substituir (Animado) por extensão .gif limpa
            output_file_clean = output_file_clean.replace("(Animado)", "").replace(
                ".GIF", ".gif"
            )
            # Remover espaços extras e múltiplos espaços
            output_file_clean = " ".join(output_file_clean.split()).strip()
            # Garantir extensão correta
            if not output_file_clean.endswith(".gif"):
                output_file_clean = output_file_clean.rsplit(".", 1)[0] + ".gif"
            self._call_callback(
                "log", f"🔧 CORREÇÃO CRÍTICA GIF: Nome limpo - {output_file_clean}"
            )

        # Arquivo de saída
        cmd.append(output_file_clean)

        return cmd

    def build_frame_extraction_command(self, cmd):
        """
        Constrói comando FFmpeg específico para extração de frames

        Args:
            cmd: Lista base do comando FFmpeg

        Returns:
            list: Comando FFmpeg completo para extração de frames
        """
        settings = self.conversion_settings
        frame_settings = settings.get("frame_settings", {})

        # LOG DETALHADO: Diagnóstico de extração de frames
        self._log_operation_start("FRAMES", frame_settings)

        # Preparar entrada e diagnósticos básicos
        self._prepare_input_and_basic_diagnostics(cmd, "Frames")

        # Obter informações do vídeo para estimar quantidade de frames
        try:
            video_info = self.get_video_info(self.input_file)
        except Exception as e:
            video_info = None
            self._call_callback("log", f"Erro ao obter informações do vídeo: {e}")
        if video_info:
            duration = video_info.get("duration", 0)
            fps = video_info.get("fps", 0)
            if duration and fps:
                estimated_frames = int(duration * fps)
                self._call_callback(
                    "log",
                    f"🔍 Duração: {duration:.1f}s, FPS: {fps}, Frames estimados: {estimated_frames}",
                )

                # Avisos para operações potencialmente problemáticas
                if estimated_frames > 10000:  # Mais de 10k frames
                    self._call_callback(
                        "log",
                        "🚨 AVISO: Muitos frames estimados - pode causar alto consumo de disco e memória",
                    )
                if duration > 300:  # Vídeos muito longos
                    self._call_callback(
                        "log",
                        "🚨 AVISO: Vídeo muito longo - operação pode demorar muito tempo",
                    )

        # Configurações do formato de saída
        frame_format = frame_settings.get("format", "JPG")
        extraction_mode = frame_settings.get("mode", "Todos os Frames")
        quality = frame_settings.get("quality", 95)

        # Configurações específicas do modo de extração
        if extraction_mode == "Intervalo Regular":
            interval = frame_settings.get("interval", 1)
            cmd.extend(["-vf", f"select=not(mod(n\\,{interval}))"])
            cmd.extend(["-vsync", "vfr"])
        elif extraction_mode == "Frames Específicos":
            specific_frames = frame_settings.get("specific_frames", "1,10,20")
            # Converter string para lista de números
            frame_numbers = [
                int(f.strip())
                for f in specific_frames.split(",")
                if f.strip().isdigit()
            ]
            if frame_numbers:
                # Criar filtro select para frames específicos
                select_expr = "+".join(
                    [f"eq(n\\,{n-1})" for n in frame_numbers]
                )  # n é 0-indexado
                cmd.extend(["-vf", f"select={select_expr}"])
                cmd.extend(["-vsync", "vfr"])
        # Para 'Todos os Frames', não adicionar filtros especiais

        # Configurações de qualidade baseadas no formato
        if frame_format == "JPG":
            cmd.extend(["-q:v", str(int(quality / 10))])  # Converter 0-100 para 1-10
        elif frame_format == "PNG":
            # PNG é lossless, não precisa de qualidade
            pass
        elif frame_format == "WebP":
            cmd.extend(["-quality", str(quality)])
            # Suporte a transparência para WebP
            self._apply_transparency_if_supported(cmd, "WebP", settings)
        elif frame_format == "TIFF":
            cmd.extend(["-compression_algo", "lzw"])  # Compressão LZW para TIFF

        # Configurar padrão de nomenclatura dos arquivos
        output_dir = os.path.dirname(self.output_file)
        video_name = os.path.splitext(os.path.basename(self.input_file))[0]

        output_pattern = self._prepare_frame_output_pattern(
            output_dir=output_dir,
            video_name=video_name,
            frame_format=frame_format,
            auto_folder=frame_settings.get("auto_folder", True),
        )

        # Configurações gerais
        self._append_overwrite_flag(cmd)

        # Padrão de saída
        cmd.append(output_pattern)

        return cmd

    def build_audio_extraction_command(self, cmd):
        """
        Constrói comando FFmpeg para extração de áudio

        Args:
            cmd: Lista base do comando FFmpeg

        Returns:
            list: Comando FFmpeg completo para extração de áudio
        """
        # Obter configurações de extração de áudio
        audio_settings = self.conversion_settings.get("audio_extraction", {})
        
        # Formato de áudio (padrão: MP3)
        audio_format = audio_settings.get("format", AUDIO_EXTRACTION_DEFAULTS["format"])
        
        # Qualidade (padrão: standard)
        quality = audio_settings.get("quality", AUDIO_EXTRACTION_DEFAULTS["quality"])
        
        # Verificar se o formato é suportado
        if audio_format not in SUPPORTED_AUDIO_FORMATS:
            audio_format = AUDIO_EXTRACTION_DEFAULTS["format"]
            self._call_callback("log", f"Formato {audio_format} não suportado, usando MP3")

        # Obter configurações do codec
        codec_config = AUDIO_CODEC_CONFIG.get(audio_format, AUDIO_CODEC_CONFIG["MP3"])
        quality_presets = AUDIO_QUALITY_PRESETS.get(audio_format, AUDIO_QUALITY_PRESETS["MP3"])
        
        # Arquivo de entrada com diagnósticos básicos
        self._prepare_input_and_basic_diagnostics(cmd, "Áudio")
        
        # Desabilitar vídeo (apenas áudio)
        cmd.extend(["-vn"])
        
        # Configurar codec de áudio
        cmd.extend(["-c:a", codec_config["codec"]])
        
        # Configurar qualidade/bitrate
        if quality in quality_presets:
            preset = quality_presets[quality]
            if "bitrate" in preset:
                cmd.extend(["-b:a", preset["bitrate"]])
            if "vbr_quality" in preset and codec_config["codec"] in ["libmp3lame", "libvorbis"]:
                cmd.extend(["-q:a", str(preset["vbr_quality"])])
        
        # Configurações adicionais baseadas no formato
        if audio_format == "WAV":
            # WAV não comprimido
            cmd.extend(["-c:a", "pcm_s16le"])
        elif audio_format == "FLAC":
            # FLAC sem perdas
            cmd.extend(["-compression_level", "8"])
        elif audio_format == "OGG":
            # Vorbis para OGG
            cmd.extend(["-c:a", "libvorbis"])
        
        # Preservar metadados se configurado
        if audio_settings.get("preserve_metadata", AUDIO_EXTRACTION_DEFAULTS["preserve_metadata"]):
            cmd.extend(["-map_metadata", "0"])
        
        # Configurações gerais
        self._append_overwrite_flag(cmd)
        
        # Arquivo de saída
        cmd.append(self.output_file)
        
        self._call_callback("log", f"Extraindo áudio para {audio_format} - Qualidade: {quality}")
        
        return cmd

    def add_cuda_decoder_settings(self, cmd):
        """
        Adiciona configurações de decodificação CUDA ao comando FFmpeg

        Args:
            cmd: Lista do comando FFmpeg
        """
        try:
            settings = self.conversion_settings
            use_hardware = settings.get("use_hardware_acceleration", True)
            performance_config = settings.get("performance_config", {})

            use_cuda, device_index = self._decide_gpu_usage("video_decoding", use_hardware, performance_config)

            if use_cuda:
                cmd.extend(["-hwaccel", "cuda"])
                cmd.extend(["-hwaccel_device", str(device_index)])
                self._call_callback("log", f"Usando decodificação CUDA na GPU {device_index}")
                return
        except Exception as e:
            self._call_callback("log", f"Erro ao decidir uso de GPU para decodificação: {e}")

    def add_video_settings(self, cmd):
        """
        Adiciona configurações de vídeo ao comando FFmpeg

        Args:
            cmd: Lista do comando FFmpeg
        """
        settings = self.conversion_settings
        format_name = settings.get("format", "MP4 (H.264)")
        use_hardware = settings.get("use_hardware_acceleration", True)

        # Verificar se é formato AVI
        is_avi_format = self._is_avi_format()

        # Obter configuração do modo de performance
        performance_config = settings.get("performance_config", {})

        # Determinar se usar CUDA ou CPU via helper comum
        use_cuda, _device_index = self._decide_gpu_usage("video_encoding", use_hardware, performance_config)

        # Para AVI, usar configurações específicas otimizadas
        if is_avi_format:
            self.add_avi_video_settings(cmd)
        # Codec de vídeo baseado na seleção do usuário
        else:
            selected_codec = settings.get("codec", "h264")
            self._apply_encoder_selection(cmd, format_name, selected_codec, use_cuda)

        # Aplicar FPS e resolução através de helper unificado
        self._apply_video_scaling_and_fps(cmd, settings)

        # Configurações de transparência (para formatos suportados)
        self._apply_transparency_if_supported(cmd, format_name, settings)

    def _is_avi_format(self):
        """
        Verifica se o formato de saída é AVI

        Returns:
            bool: True se for formato AVI
        """
        if not self.output_file:
            return False

        output_ext = Path(self.output_file).suffix.lower()
        format_name = self.conversion_settings.get("format", "")

        # Verificar extensão do arquivo de saída primeiro (prioridade máxima)
        if output_ext == ".avi":
            return True

        # Verificar se o formato especificado é especificamente AVI (apenas se não for extensão .avi)
        if format_name:
            format_upper = format_name.upper()
            # Deve conter 'AVI' mas não outros formatos
            if format_upper == "AVI" or (
                format_upper.startswith("AVI")
                and not any(x in format_upper for x in ["MP4", "MKV", "MOV", "WEBM"])
            ):
                return True

        return False

    def add_avi_video_settings(self, cmd):
        """
        Adiciona configurações de vídeo específicas para formato AVI

        Args:
            cmd: Lista do comando FFmpeg
        """
        settings = self.conversion_settings
        quality = settings.get("quality", "Média")

        # Usar configurações específicas do AVI
        avi_preset = AVI_QUALITY_PRESETS.get(quality, AVI_QUALITY_PRESETS["Média"])

        # Codec de vídeo: sempre usar libx264 para AVI (melhor compatibilidade)
        cmd.extend(["-c:v", "libx264"])

        # Configurações de qualidade específicas para AVI
        cmd.extend(["-crf", str(avi_preset["crf"])])
        cmd.extend(["-preset", avi_preset["preset"]])
        cmd.extend(["-profile:v", avi_preset["profile"]])
        cmd.extend(["-level", avi_preset["level"]])
        cmd.extend(["-tune", avi_preset["tune"]])

        # Configurações adicionais para melhor compatibilidade AVI
        self._apply_common_output_flags(cmd, apply_pix_fmt=True, apply_faststart=True)

        self._call_callback(
            "log",
            f"Configurações AVI aplicadas - Qualidade: {quality}, CRF: {avi_preset['crf']}",
        )

    def add_cuda_video_settings(self, cmd, codec_type):
        """
        Adiciona configurações de vídeo CUDA/NVENC ao comando FFmpeg

        Args:
            cmd: Lista do comando FFmpeg
            codec_type: Tipo do codec ('h264' ou 'hevc')
        """
        settings = self.conversion_settings
        quality = settings.get("quality", "Alta")

        # Determinar encoder NVENC
        if codec_type == "h264":
            encoder = "h264_nvenc"
        elif codec_type == "hevc":
            encoder = "hevc_nvenc"
        else:
            # Fallback para CPU
            self.add_cpu_video_settings(cmd, codec_type)
            return

        cmd.extend(["-c:v", encoder])

        # Não adicionar filtros de conversão automáticos para evitar incompatibilidades
        # O NVENC pode trabalhar diretamente com formatos de entrada padrão

        # Configurações de qualidade NVENC
        quality_presets = self.hardware_config.get("quality_presets", {})
        nvenc_presets = quality_presets.get("nvenc", NVENC_QUALITY_PRESETS)

        # Obter preset NVENC do modo de performance
        performance_config = settings.get("performance_config", {})
        nvenc_preset = performance_config.get("nvenc_preset", "medium")

        if quality in nvenc_presets:
            preset_config = nvenc_presets[quality]

            # Preset NVENC (usar do modo de performance se disponível)
            cmd.extend(["-preset", nvenc_preset])

            # Rate control
            rc_mode = preset_config.get("rc_mode", "vbr")
            cmd.extend(["-rc", rc_mode])

            # Bitrate ou CQ
            if rc_mode == "cq":
                cmd.extend(["-cq", str(preset_config.get("cq", 23))])
            else:
                bitrate = preset_config.get("bitrate", "5M")
                cmd.extend(["-b:v", bitrate])
                if "maxrate" in preset_config:
                    cmd.extend(["-maxrate", preset_config["maxrate"]])
                    cmd.extend(
                        [
                            "-bufsize",
                            preset_config.get("bufsize", preset_config["maxrate"]),
                        ]
                    )

        # Configurações específicas do codec
        codec_settings = NVENC_CODEC_SETTINGS.get(encoder, {})

        # Profile
        if "profiles" in codec_settings and codec_settings["profiles"]:
            profile = codec_settings["profiles"][0]
            cmd.extend(["-profile:v", profile])

        # Level (se especificado)
        if "levels" in codec_settings and codec_settings["levels"]:
            level = codec_settings["levels"][0]
            cmd.extend(["-level", level])

        # GPU específica e configurações avançadas
        cuda_config = self.hardware_config.get("cuda_config", {})
        gpu_index = cuda_config.get("gpu_index", 0)
        cmd.extend(["-gpu", str(gpu_index)])
        
        # Configurações de otimização de memória
        memory_opt = cuda_config.get("memory_optimization", {})
        if memory_opt.get("enable_memory_pool", True):
            # Configurações de pool de memória
            prealloc_size = memory_opt.get("prealloc_size", "256M")
            cmd.extend(["-init_hw_device", f"cuda=gpu:{gpu_index}"])
            
        # Configurações de stream
        stream_opt = cuda_config.get("stream_optimization", {})
        max_streams = stream_opt.get("max_concurrent_streams", 4)
        
        # Configurações de performance
        perf_tuning = cuda_config.get("performance_tuning", {})
        # Nota: A flag '+fast' foi removida pois não é válida para FFmpeg
        # O enable_fast_math agora é usado apenas para outras otimizações
            
        # Configurações específicas do NVENC para melhor utilização de GPU
        cmd.extend(["-2pass", "0"])  # Desabilitar 2-pass para melhor performance
        cmd.extend(["-spatial_aq", "1"])  # Adaptive quantization espacial
        cmd.extend(["-temporal_aq", "1"])  # Adaptive quantization temporal
        cmd.extend(["-aq-strength", "8"])  # Força do AQ
        
        # Configurações de threading para GPU
        cmd.extend(["-threads", "0"])  # Auto-detectar threads
        
        # Log das configurações aplicadas
        monitoring = cuda_config.get("monitoring", {})
        if monitoring.get("log_gpu_stats", True):
            self._call_callback(
                "log",
                f"🚀 GPU Otimizada: GPU={gpu_index}, Streams={max_streams}, Encoder={encoder}",
            )

    def add_cpu_video_settings(self, cmd, codec_type):
        """
        Adiciona configurações de vídeo CPU ao comando FFmpeg

        Args:
            cmd: Lista do comando FFmpeg
            codec_type: Tipo do codec ('h264', 'hevc', 'vp9', 'webp')
        """
        settings = self.conversion_settings
        quality = settings.get("quality", "Alta")

        if codec_type == "h264":
            cmd.extend(["-c:v", "libx264"])
            # Configurações de qualidade para H.264
            if quality == "Alta":
                cmd.extend(["-crf", "18"])
            elif quality == "Média":
                cmd.extend(["-crf", "23"])
            else:  # Baixa
                cmd.extend(["-crf", "28"])

        elif codec_type == "hevc":
            cmd.extend(["-c:v", "libx265"])
            if quality == "Alta":
                cmd.extend(["-crf", "20"])
            elif quality == "Média":
                cmd.extend(["-crf", "25"])
            else:  # Baixa
                cmd.extend(["-crf", "30"])

        elif codec_type == "vp9":
            cmd.extend(["-c:v", "libvpx-vp9"])
            
            # Importar presets VP9 otimizados
            from utils.config import VP9_QUALITY_PRESETS
            
            vp9_preset = VP9_QUALITY_PRESETS.get(quality, VP9_QUALITY_PRESETS["Média"])
            
            # Configurações básicas de qualidade
            cmd.extend(["-crf", str(vp9_preset["crf"])])
            cmd.extend(["-b:v", "0"])  # Usar CRF mode
            
            # Configurações de performance otimizadas
            cmd.extend(["-speed", str(vp9_preset["speed"])])
            cmd.extend(["-threads", str(vp9_preset["threads"])])
            
            # Configurações de paralelização
            cmd.extend(["-tile-columns", str(vp9_preset["tile_columns"])])
            cmd.extend(["-tile-rows", str(vp9_preset["tile_rows"])])
            cmd.extend(["-frame-parallel", str(vp9_preset["frame_parallel"])])
            cmd.extend(["-row-mt", str(vp9_preset["row_mt"])])
            
            # Configurações de qualidade avançadas
            cmd.extend(["-auto-alt-ref", str(vp9_preset["auto_alt_ref"])])
            cmd.extend(["-lag-in-frames", str(vp9_preset["lag_in_frames"])])
            
            # Configurações adicionais para melhor performance
            cmd.extend(["-deadline", "good"])  # Modo de qualidade balanceada
            cmd.extend(["-cpu-used", str(vp9_preset["speed"])])  # Alias para speed
            
            self._call_callback(
                "log",
                f"🚀 VP9 Otimizado: CRF={vp9_preset['crf']}, Speed={vp9_preset['speed']}, Threads={vp9_preset['threads']}",
            )

        elif codec_type == "webp":
            cmd.extend(["-c:v", "libwebp"])
            # Configurações específicas para WebP animado
            from utils.config import WEBP_QUALITY_PRESETS

            webp_settings = WEBP_QUALITY_PRESETS.get(
                quality, WEBP_QUALITY_PRESETS["Média"]
            )

            cmd.extend(["-quality", str(webp_settings["quality"])])
            cmd.extend(["-method", str(webp_settings["method"])])

            # Configurações para animação
            cmd.extend(["-loop", "0"])  # Loop infinito

    def add_audio_settings(self, cmd):
        """
        Adiciona configurações de áudio ao comando FFmpeg

        Args:
            cmd: Lista do comando FFmpeg
        """
        # Determinar codec de áudio baseado no formato de saída
        output_ext = Path(self.output_file).suffix.lower()

        if output_ext == ".avi":
            # AVI: usar configurações específicas de MP3 otimizadas
            self.add_avi_audio_settings(cmd)
        elif output_ext == ".webm":
            # WebM suporta apenas Vorbis ou Opus
            cmd.extend(["-c:a", "libopus", "-b:a", "192k"])
        elif output_ext in [".mp4", ".mov", ".m4v"]:
            # MP4 e formatos relacionados usam AAC
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        elif output_ext == ".mkv":
            # MKV pode usar AAC ou outros codecs
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            # Padrão para outros formatos
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])

    def add_avi_audio_settings(self, cmd):
        """
        Adiciona configurações de áudio específicas para formato AVI

        Args:
            cmd: Lista do comando FFmpeg
        """
        # Usar configurações específicas do AVI
        audio_config = AVI_AUDIO_CONFIG

        # Codec de áudio MP3
        cmd.extend(["-c:a", "libmp3lame"])

        # Bitrate otimizado para MP3
        cmd.extend(["-b:a", audio_config["bitrate"]])

        # Sample rate
        cmd.extend(["-ar", audio_config["sample_rate"]])

        # Número de canais
        cmd.extend(["-ac", str(audio_config["channels"])])

        # Qualidade VBR para MP3 (opcional, para melhor qualidade)
        cmd.extend(["-q:a", str(audio_config["quality"])])

        self._call_callback(
            "log",
            f"Configurações de áudio AVI aplicadas - MP3 {audio_config['bitrate']} @ {audio_config['sample_rate']}Hz",
        )

    def run(self):
        """
        Executa a conversão de vídeo em thread separada
        """
        try:
            self._call_callback("status", "Iniciando conversão...")
            self._call_callback("log", f"🔍 DIAGNÓSTICO RUN: Iniciando conversão")
            self._call_callback(
                "log", f"🔍 Arquivo: {os.path.basename(self.input_file)}"
            )
            self._call_callback(
                "log", f"🔍 Formato: {self.conversion_settings.get('format', 'N/A')}"
            )
            self._call_callback("log", f"🔍 Thread ID: {threading.get_ident()}")

            # CORREÇÃO: Verificar se é operação problemática e adicionar proteções
            format_name = self.conversion_settings.get("format", "")
            if "GIF (Animado)" in format_name or "Extração de Frames" in format_name:
                self._call_callback(
                    "log",
                    "🛡️ CORREÇÃO: Operação de risco detectada - aplicando proteções adicionais",
                )

                # Verificar tamanho do arquivo e adicionar timeout específico
                if os.path.exists(self.input_file):
                    file_size_mb = os.path.getsize(self.input_file) / (1024 * 1024)
                    if file_size_mb > 500:  # Arquivos maiores que 500MB
                        self._call_callback(
                            "log",
                            "⚠️ Arquivo muito grande detectado - operação pode demorar",
                        )

            # Obter informações do vídeo para calcular progresso
            video_info = self.get_video_info(self.input_file)
            total_duration = video_info.get("duration", 0) if video_info else 0

            # Construir comando FFmpeg
            cmd = self.build_ffmpeg_command()
            self._call_callback("log", f"Comando FFmpeg: {' '.join(cmd)}")

            # CORREÇÃO: Timeout específico baseado no tipo de operação
            timeout_base = 300  # 5 minutos padrão
            if "GIF (Animado)" in format_name:
                timeout_base = 600  # 10 minutos para GIF
                self._call_callback(
                    "log", "⏱️ Timeout aumentado para 10 minutos (operação GIF)"
                )
            elif "Extração de Frames" in format_name:
                timeout_base = 900  # 15 minutos para extração de frames
                self._call_callback(
                    "log", "⏱️ Timeout aumentado para 15 minutos (extração de frames)"
                )

            # Executar conversão
            self._call_callback("log", f"Executando FFmpeg no diretório: {os.getcwd()}")
            self._call_callback(
                "log", f"Arquivo de entrada existe: {os.path.exists(self.input_file)}"
            )
            self._call_callback(
                "log",
                f"Diretório de saída existe: {os.path.exists(os.path.dirname(self.output_file))}",
            )

            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                self._call_callback(
                    "log", f"Processo FFmpeg iniciado com PID: {self.process.pid}"
                )
            except Exception as e:
                self._call_callback("log", f"Erro ao iniciar processo FFmpeg: {str(e)}")
                self._call_callback("log", f"Tipo do erro: {type(e).__name__}")
                raise

            # Monitorar progresso
            self.monitor_progress(total_duration)

            # Aguardar conclusão sem bloquear as streams
            self._wait_while_running()

            # Capturar saída final com helper e tratar cancelamento
            stdout, stderr = self._read_process_output()
            if self._check_and_handle_cancel():
                return

            if self.process.returncode == 0:
                self._finalize_success("Conversão concluída com sucesso!")
            else:
                # Verificar se é erro relacionado ao CUDA e tentar fallback
                if self._is_cuda_error(stderr) and not self.cuda_fallback_attempted:
                    self._call_callback(
                        "log", "Erro CUDA detectado, tentando fallback para CPU..."
                    )
                    self._attempt_cpu_fallback()
                else:
                    error_msg = f"Erro na conversão: {stderr}"
                    self._finalize_error(error_msg)

        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            self._finalize_error(error_msg)

    def _is_cuda_error(self, error_message):
        """
        Verifica se o erro está relacionado ao CUDA/NVENC

        Args:
            error_message: Mensagem de erro do FFmpeg

        Returns:
            bool: True se for erro CUDA/NVENC
        """
        cuda_error_keywords = [
            "cuda error",
            "nvenc error",
            "nvenc initialization failed",
            "no cuda-capable device",
            "cuda driver version",
            "cuda runtime error",
            "nvenc encoder",
            "cuvid decoder",
            "cuvidcreatevideoparser",
            "cannot load cuvid",
            "gpu memory",
            "cuda context",
            "cuda out of memory",
            "nvenc not available",
            "cuda device",
            "impossible to convert between the formats",
            "error reinitializing filters",
            "function not implemented",
            "auto_scale_0",
        ]

        error_lower = error_message.lower()
        return any(keyword in error_lower for keyword in cuda_error_keywords)

    def _attempt_cpu_fallback(self):
        """
        Tenta executar a conversão novamente usando CPU
        """
        try:
            self.cuda_fallback_attempted = True
            self._call_callback("status", "Tentando conversão com CPU...")

            # Obter informações do vídeo para calcular progresso
            video_info = self.get_video_info(self.input_file)
            total_duration = video_info.get("duration", 0) if video_info else 0

            # Construir comando FFmpeg (agora forçará uso de CPU)
            cmd = self.build_ffmpeg_command()
            self._call_callback("log", f"Comando FFmpeg (CPU): {' '.join(cmd)}")

            # Executar conversão
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            # Monitorar progresso
            self.monitor_progress(total_duration)

            # Aguardar conclusão sem bloquear as streams
            self._wait_while_running()

            # Capturar saída final com helper e tratar cancelamento
            stdout, stderr = self._read_process_output()
            if self._check_and_handle_cancel():
                return

            if self.process.returncode == 0:
                self._finalize_success(
                    "Conversão concluída com sucesso (CPU)!",
                    "Conversão concluída com sucesso usando CPU!",
                )
            else:
                error_msg = f"Erro na conversão (CPU): {stderr}"
                self._finalize_error(error_msg)

        except Exception as e:
            error_msg = f"Erro no fallback CPU: {str(e)}"
            self._finalize_error(error_msg)

    def _call_callback(self, callback_type, *args):
        """
        Chama callback se disponível
        """
        callback = self.callbacks.get(callback_type)
        if callback:
            try:
                callback(*args)
            except Exception as e:
                print(f"Erro no callback {callback_type}: {e}")

    def monitor_progress(self, total_duration):
        """
        Monitora o progresso da conversão através da saída do FFmpeg

        Args:
            total_duration: Duração total do vídeo em segundos
        """
        if not self.process or total_duration <= 0:
            self._call_callback(
                "log",
                f"🔍 DIAGNÓSTICO MONITOR: processo={self.process is not None}, duração={total_duration}",
            )
            return

        # CORREÇÃO: Verificação de segurança para operações críticas
        format_name = self.conversion_settings.get("format", "")
        if "GIF (Animado)" in format_name or "Extração de Frames" in format_name:
            self._call_callback(
                "log", "🛡️ MONITORAMENTO REFORÇADO: Operação crítica detectada"
            )

        # LOG DETALHADO: Diagnóstico do monitoramento de progresso
        self._call_callback(
            "log", "🔍 DIAGNÓSTICO MONITOR: Iniciando monitoramento de progresso"
        )
        self._call_callback("log", f"🔍 Processo PID: {self.process.pid}")
        self._call_callback("log", f"🔍 Duração total: {total_duration}s")

        # Padrões regex para extrair tempo atual da saída do FFmpeg
        time_patterns = [
            re.compile(r"time=(\d+):(\d+):(\d+\.\d+)"),
            re.compile(r"time=(\d+):(\d+):(\d+)"),
            re.compile(r"out_time_ms=(\d+)"),
        ]

        self._call_callback(
            "log",
            f"Iniciando monitoramento de progresso. Duração total: {total_duration}s",
        )

        def read_output(pipe, pipe_name):
            """Lê a saída do pipe em thread separada"""
            try:
                while self.process.poll() is None and not self.cancelled:
                    line = pipe.readline()
                    if line:
                        line = line.strip()
                        self._call_callback("log", f"FFmpeg {pipe_name}: {line}")

                        # Procurar informação de tempo na linha
                        for pattern in time_patterns:
                            match = pattern.search(line)
                            if match:
                                try:
                                    if "out_time_ms" in pattern.pattern:
                                        # Tempo em microssegundos
                                        current_time = int(match.group(1)) / 1000000
                                    else:
                                        # Formato HH:MM:SS
                                        if len(match.groups()) == 3:
                                            hours = int(match.group(1))
                                            minutes = int(match.group(2))
                                            seconds = float(match.group(3))
                                            current_time = (
                                                hours * 3600 + minutes * 60 + seconds
                                            )
                                        else:
                                            continue

                                    progress = min(
                                        int((current_time / total_duration) * 100), 99
                                    )
                                    self._call_callback("progress", progress)
                                    self._call_callback(
                                        "status", f"Convertendo... {progress}%"
                                    )
                                    self._call_callback(
                                        "log",
                                        f"Progresso: {current_time:.1f}s / {total_duration:.1f}s ({progress}%)",
                                    )
                                    break
                                except (ValueError, ZeroDivisionError) as e:
                                    self._call_callback(
                                        "log", f"Erro ao calcular progresso: {e}"
                                    )
                    else:
                        time.sleep(0.1)
            except Exception as e:
                self._call_callback("log", f"Erro no monitoramento {pipe_name}: {e}")

        # Criar threads para ler stdout e stderr
        stdout_thread = None
        stderr_thread = None
        
        if self.process.stdout:
            stdout_thread = threading.Thread(
                target=read_output, args=(self.process.stdout, "stdout")
            )
            stdout_thread.daemon = True
            stdout_thread.start()

        if self.process.stderr:
            stderr_thread = threading.Thread(
                target=read_output, args=(self.process.stderr, "stderr")
            )
            stderr_thread.daemon = True
            stderr_thread.start()
            
        # Armazenar referências das threads para cleanup posterior
        self.monitor_threads = {'stdout': stdout_thread, 'stderr': stderr_thread}

    def cancel_conversion(self):
        """
        Cancela a conversão em andamento
        """
        self.cancelled = True
        
        # Finalizar processo FFmpeg
        if self.process and self.process.poll() is None:
            self._call_callback("log", f"Finalizando processo FFmpeg (PID: {self.process.pid})")
            
            # Tentar finalização suave primeiro
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
                self._call_callback("log", "Processo FFmpeg finalizado com sucesso")
            except subprocess.TimeoutExpired:
                self._call_callback("log", "Processo FFmpeg não respondeu, forçando finalização...")
                self.process.kill()
                try:
                    self.process.wait(timeout=2)
                    self._call_callback("log", "Processo FFmpeg finalizado forçadamente")
                except subprocess.TimeoutExpired:
                    self._call_callback("log", "AVISO: Processo FFmpeg pode ainda estar ativo")
        
        # Cleanup das threads de monitoramento
        if hasattr(self, 'monitor_threads'):
            for thread_name, thread in self.monitor_threads.items():
                if thread and thread.is_alive():
                    self._call_callback("log", f"Aguardando finalização da thread {thread_name}")
                    thread.join(timeout=1)
                    if thread.is_alive():
                        self._call_callback("log", f"AVISO: Thread {thread_name} ainda ativa")
        
        # Fechar pipes se ainda estiverem abertos
        if self.process:
            try:
                if self.process.stdout and not self.process.stdout.closed:
                    self.process.stdout.close()
                if self.process.stderr and not self.process.stderr.closed:
                    self.process.stderr.close()
                if self.process.stdin and not self.process.stdin.closed:
                    self.process.stdin.close()
            except Exception as e:
                self._call_callback("log", f"Erro ao fechar pipes: {e}")

    # ===================== Helpers de Finalização =====================
    def _read_process_output(self):
        """
        Lê com segurança as saídas finais de stdout e stderr do processo FFmpeg.

        Retorna:
            tuple(str, str): Conteúdo de stdout e stderr, respectivamente.
        """
        stdout = ""
        stderr = ""
        try:
            if self.process and self.process.stdout:
                stdout = self.process.stdout.read()
        except Exception:
            pass
        try:
            if self.process and self.process.stderr:
                stderr = self.process.stderr.read()
        except Exception:
            pass
        return stdout, stderr

    def _check_and_handle_cancel(self) -> bool:
        """
        Verifica se a conversão foi cancelada e dispara o callback adequado.

        Retorna:
            bool: True se a operação foi cancelada e tratada, False caso contrário.
        """
        if self.cancelled:
            self._call_callback("finished", False, "Conversão cancelada pelo usuário")
            return True

    # ===================== Helpers Utilitários =====================
    def _prepare_input_and_basic_diagnostics(self, cmd, operation_label):
        """
        Prepara a entrada do FFmpeg e executa diagnósticos básicos.

        Args:
            cmd: Lista do comando FFmpeg que será extendida.
            operation_label: Rótulo amigável da operação (ex.: 'GIF', 'Frames', 'Áudio').
        """
        try:
            if os.path.exists(self.input_file):
                file_size = os.path.getsize(self.input_file) / (1024 * 1024)  # MB
                self._call_callback(
                    "log", f"🔍 Tamanho do arquivo de entrada: {file_size:.1f} MB"
                )
                if file_size > 100:
                    self._call_callback(
                        "log",
                        "🚨 AVISO: Arquivo grande detectado - pode causar alto consumo de memória",
                    )
            else:
                self._call_callback(
                    "log", "🚨 ERRO: Arquivo de entrada não encontrado!"
                )
        except Exception as e:
            self._call_callback(
                "log", f"Erro ao diagnosticar entrada ({operation_label}): {e}"
            )

        # Arquivo de entrada
        cmd.extend(["-i", self.input_file])

    def _append_overwrite_flag(self, cmd):
        """
        Adiciona a flag de sobrescrita ao comando FFmpeg.

        Args:
            cmd: Lista do comando FFmpeg
        """
        cmd.extend(["-y"])  # Sobrescrever arquivo(s) de saída

    def _run_subprocess_with_logging(self, cmd, timeout=30, context="subprocess"):
        """
        Executa subprocess.run com logs padronizados e tratamento de erros.

        Args:
            cmd: Comando a executar (lista)
            timeout: Tempo limite em segundos
            context: Rótulo de contexto para logs

        Returns:
            subprocess.CompletedProcess | None: Resultado da execução, se disponível
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
            )

            self._call_callback("log", f"{context} returncode: {result.returncode}")
            if result.stdout:
                preview = result.stdout[:200].replace("\n", " ")
                self._call_callback("log", f"{context} stdout: {preview}...")
            if result.stderr:
                self._call_callback("log", f"{context} stderr: {result.stderr}")

            return result
        except subprocess.TimeoutExpired:
            self._call_callback(
                "log", f"{context} timeout - comando demorou mais de {timeout} segundos"
            )
            return None

    def _log_operation_start(self, operation_label: str, settings_dict: dict):
        """
        Registra logs padronizados de início de operação (diagnóstico, configurações e arquivo de entrada).

        Args:
            operation_label: Rótulo da operação (ex.: 'GIF', 'FRAMES', 'ÁUDIO').
            settings_dict: Dicionário de configurações específicas da operação.
        """
        try:
            self._call_callback(
                "log", f"🔍 DIAGNÓSTICO {operation_label}: Iniciando construção do comando"
            )
            self._call_callback(
                "log", f"🔍 Configurações {operation_label}: {settings_dict}"
            )
            self._call_callback(
                "log", f"🔍 Arquivo de entrada: {self.input_file}"
            )
        except Exception as e:
            self._call_callback(
                "log", f"Erro ao registrar início de operação ({operation_label}): {e}"
            )
        except FileNotFoundError as e:
            self._call_callback("log", f"{context} não encontrado: {str(e)}")
            return None
        except Exception as e:
            self._call_callback("log", f"Erro em {context}: {str(e)}")
            return None

    def _decide_gpu_usage(self, task_label: str, use_hardware: bool, performance_config: dict):
        """
        Decide de forma unificada se a operação deve usar GPU (CUDA) ou CPU.

        Args:
            task_label: Rótulo da tarefa (ex.: 'video_encoding', 'video_decoding').
            use_hardware: Flag geral de uso de aceleração por hardware.
            performance_config: Dicionário de preferências de performance (cpu/nvidia).

        Returns:
            tuple[bool, int]: (use_cuda, device_index) onde use_cuda indica se deve usar GPU
            e device_index é o índice da GPU a ser utilizada (0 por padrão).
        """
        # Tentativa com o sistema universal (quando disponível)
        try:
            if hasattr(self, 'hardware_integration') and self.hardware_integration:
                if use_hardware and self.hardware_integration.should_use_gpu_for_task(task_label):
                    hw_config = self.hardware_integration.get_optimized_config_for_video_converter()
                    gpu_config = hw_config.get("gpu", {})
                    use_cuda = gpu_config.get("enabled", False)
                    device_index = gpu_config.get("device_index", 0)
                    self._call_callback(
                        "log",
                        f"Sistema universal: GPU {'habilitada' if use_cuda else 'desabilitada'} para {task_label}"
                    )
                    return use_cuda, device_index
                else:
                    self._call_callback("log", f"Sistema universal: Usando CPU para {task_label}")
                    return False, 0
        except Exception as e:
            self._call_callback("log", f"Erro no sistema universal, usando fallback: {e}")

        # Fallback para lógica original
        cpu_preference = performance_config.get("cpu_preference", "auto")
        nvidia_preference = performance_config.get("nvidia_preference", "auto")

        if cpu_preference == "force":
            use_cuda = False
        elif nvidia_preference == "force" and self.cuda_available:
            use_cuda = not getattr(self, 'cuda_fallback_attempted', False) and self.hw_settings.get("enabled", False)
        else:
            use_cuda = (
                self.cuda_available
                and use_hardware
                and not getattr(self, 'cuda_fallback_attempted', False)
                and self.hw_settings.get("enabled", False)
            )

        # Índice de GPU padrão em configurações locais
        device_index = self.hardware_config.get("cuda_config", {}).get("gpu_index", 0)
        return use_cuda, device_index

    def _apply_video_scaling_and_fps(self, cmd, settings: dict):
        """
        Aplica configurações de FPS e de resolução ao comando FFmpeg.

        Args:
            cmd: Lista do comando FFmpeg que será extendida com flags de FPS e escala.
            settings: Dicionário de configurações da conversão contendo chaves 'fps',
                      'custom_fps', 'resolution', 'custom_width' e 'custom_height'.
        """
        # FPS
        try:
            fps = settings.get("fps")
            if fps and fps != "Original":
                if fps == "Custom":
                    custom_fps = settings.get("custom_fps", 30)
                    cmd.extend(["-r", str(custom_fps)])
                else:
                    cmd.extend(["-r", str(fps)])
        except Exception as e:
            self._call_callback("log", f"Erro ao aplicar FPS: {e}")

        # Resolução
        try:
            resolution = settings.get("resolution")
            if resolution and resolution != "Original":
                if resolution == "Custom":
                    width = settings.get("custom_width", 1920)
                    height = settings.get("custom_height", 1080)
                    cmd.extend(["-s", f"{width}x{height}"])
                else:
                    # Usar presets de resolução
                    if resolution in RESOLUTION_PRESETS:
                        res_value = RESOLUTION_PRESETS[resolution]
                        if res_value and isinstance(res_value, tuple):
                            # Converter tupla (width, height) para string "widthxheight"
                            cmd.extend(["-s", f"{res_value[0]}x{res_value[1]}"])
                        elif res_value:
                            cmd.extend(["-s", res_value])
        except Exception as e:
            self._call_callback("log", f"Erro ao aplicar resolução: {e}")

    def _apply_transparency_if_supported(self, cmd, format_name: str, settings: dict):
        """
        Aplica transparência para formatos que suportam canal alfa quando habilitado nas configurações.

        Args:
            cmd: Lista do comando FFmpeg
            format_name: Nome do formato de saída (ex.: 'WEBP', 'WebM', 'MOV')
            settings: Dicionário de configurações, deve conter a chave 'transparency'.
        """
        try:
            if settings.get("transparency", False):
                if "WEBP" in format_name or "WebM" in format_name or "MOV" in format_name:
                    cmd.extend(["-pix_fmt", "yuva420p"])
        except Exception as e:
            self._call_callback("log", f"Erro ao aplicar transparência: {e}")

    def _apply_common_output_flags(self, cmd, apply_pix_fmt: bool = True, apply_faststart: bool = True):
        """
        Aplica flags comuns de saída que melhoram compatibilidade e streaming.

        Args:
            cmd: Lista do comando FFmpeg
            apply_pix_fmt: Se True, aplica '-pix_fmt yuv420p' para compatibilidade ampla.
            apply_faststart: Se True, aplica '-movflags +faststart' para otimizar streaming.
        """
        try:
            if apply_pix_fmt:
                cmd.extend(["-pix_fmt", "yuv420p"])  
            if apply_faststart:
                cmd.extend(["-movflags", "+faststart"])  
        except Exception as e:
            self._call_callback("log", f"Erro ao aplicar flags comuns de saída: {e}")

    def _prepare_frame_output_pattern(self, output_dir: str, video_name: str, frame_format: str, auto_folder: bool = True) -> str:
        """
        Prepara o padrão de saída para extração de frames, criando subpasta quando configurado.

        Args:
            output_dir: Diretório base para saída.
            video_name: Nome base do vídeo de entrada, sem extensão.
            frame_format: Formato dos frames (ex.: 'jpg', 'png').
            auto_folder: Se True, cria subpasta '<video_name>_frames'.

        Returns:
            Caminho padrão para saída com placeholder de contagem '%04d'.
        """
        try:
            fmt = frame_format.lower()
            if auto_folder:
                frame_folder = os.path.join(output_dir, f"{video_name}_frames")
                os.makedirs(frame_folder, exist_ok=True)
                return os.path.join(frame_folder, f"{video_name}_frame_%04d.{fmt}")
            return os.path.join(output_dir, f"{video_name}_frame_%04d.{fmt}")
        except Exception as e:
            self._call_callback("log", f"Erro ao preparar padrão de saída de frames: {e}")
            # Fallback simples para evitar quebra do fluxo
            return os.path.join(output_dir, f"{video_name}_frame_%04d.{frame_format}")

    def _apply_encoder_selection(self, cmd, format_name: str, selected_codec: str, use_cuda: bool):
        """
        Aplica a escolha de encoder com base no formato de saída, codec escolhido e disponibilidade de GPU.

        Args:
            cmd: Lista do comando FFmpeg a ser extendida.
            format_name: Nome do formato de saída (ex.: 'MP4 (H.264)', 'WEBM (VP9)').
            selected_codec: Codec preferido pelo usuário ('h264' ou 'hevc').
            use_cuda: Se True, prefere NVENC quando aplicável.
        """
        try:
            fmt_upper = format_name.upper()
            if "VP9" in fmt_upper or "WEBM" in fmt_upper:
                # VP9/WEBM não suporta NVENC; usar CPU com VP9
                self.add_cpu_video_settings(cmd, "vp9")
                self._call_callback("log", f"🔧 CORREÇÃO WEBM: Usando codec VP9 para formato {format_name}")
                return
            if "WEBP" in fmt_upper:
                # WebP não tem suporte NVENC; usar CPU
                self.add_cpu_video_settings(cmd, "webp")
                return

            # MP4/MKV/MOV e outros com H.264/HEVC
            if selected_codec == "hevc":
                if use_cuda:
                    self.add_cuda_video_settings(cmd, "hevc")
                else:
                    self.add_cpu_video_settings(cmd, "hevc")
            else:  # h264 padrão
                if use_cuda:
                    self.add_cuda_video_settings(cmd, "h264")
                else:
                    self.add_cpu_video_settings(cmd, "h264")
        except Exception as e:
            self._call_callback("log", f"Erro ao aplicar seleção de encoder: {e}")

    def _finalize_success(self, status_msg, finished_msg=None):
        """
        Finaliza o fluxo de sucesso de conversão, consolidando callbacks.

        Args:
            status_msg: Mensagem para o callback de status.
            finished_msg: Mensagem do callback de finished (padrão: status_msg).
        """
        try:
            self._call_callback("status", status_msg)
            self._call_callback("progress", 100)
            self._call_callback("finished", True, finished_msg or status_msg)
            self._call_callback("log", f"Arquivo salvo em: {self.output_file}")
        except Exception as e:
            # Em caso de erro nos callbacks, registrar para diagnóstico
            print(f"Erro ao finalizar sucesso: {e}")

    def _finalize_error(self, error_msg):
        """
        Finaliza o fluxo de erro de conversão, consolidando callbacks.

        Args:
            error_msg: Mensagem de erro detalhada para logs e finished.
        """
        try:
            self._call_callback("status", "Erro na conversão")
            self._call_callback("finished", False, error_msg)
            self._call_callback("log", error_msg)
        except Exception as e:
            # Em caso de erro nos callbacks, registrar para diagnóstico
            print(f"Erro ao finalizar erro: {e}")

    def _wait_while_running(self, sleep_seconds=0.1):
        """
        Aguarda o término do processo FFmpeg enquanto não houver cancelamento.

        Args:
            sleep_seconds: Intervalo entre verificações do estado do processo.
        """
        try:
            while self.process and self.process.poll() is None and not self.cancelled:
                time.sleep(sleep_seconds)
        except Exception as e:
            # Não bloquear fluxo por falha na espera; registrar para diagnóstico.
            self._call_callback("log", f"Erro durante espera do processo: {e}")
        return False


# VideoConverterManager foi movido para video_converter_manager.py
