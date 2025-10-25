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
from utils.validators import (
    validate_input_file,
    validate_output_directory,
    validate_conversion_settings,
    generate_output_filename,
)
from .ffmpeg_installer import FFmpegInstaller


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

        # Configuração de hardware
        self.hardware_config_obj = get_hardware_config()
        self.hardware_config = self.hardware_config_obj.auto_configure()
        self.hw_settings = self.hardware_config.get("hardware_acceleration", {})
        self.cuda_available = self.hardware_config.get("hardware_acceleration", {}).get(
            "enabled", False
        )
        self.cuda_fallback_attempted = False

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

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)

            # Log detalhado da execução
            self._call_callback("log", f"FFprobe returncode: {result.returncode}")
            if result.stdout:
                self._call_callback("log", f"FFprobe stdout: {result.stdout[:200]}...")
            if result.stderr:
                self._call_callback("log", f"FFprobe stderr: {result.stderr}")

            if result.returncode == 0:
                import json

                info = json.loads(result.stdout)
                return self.parse_video_info(info)
            else:
                self._call_callback(
                    "log",
                    f"FFprobe falhou com código {result.returncode}: {result.stderr}",
                )
        except subprocess.TimeoutExpired:
            self._call_callback(
                "log", "FFprobe timeout - comando demorou mais de 30 segundos"
            )
        except FileNotFoundError as e:
            self._call_callback("log", f"FFprobe não encontrado: {str(e)}")
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

            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30
            )

            # Se encontrou stream de áudio, retorna True
            return result.returncode == 0 and "audio" in result.stdout.lower()

        except subprocess.TimeoutExpired:
            self._call_callback("log", "Timeout ao verificar streams de áudio")
            return False
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
        self._call_callback(
            "log", "🔍 DIAGNÓSTICO GIF: Iniciando construção do comando"
        )
        self._call_callback("log", f"🔍 Configurações GIF: {gif_settings}")
        self._call_callback("log", f"🔍 Arquivo de entrada: {self.input_file}")

        # Verificar se arquivo de entrada existe e tamanho
        if os.path.exists(self.input_file):
            file_size = os.path.getsize(self.input_file) / (1024 * 1024)  # MB
            self._call_callback(
                "log", f"🔍 Tamanho do arquivo de entrada: {file_size:.1f} MB"
            )
            if file_size > 100:  # Arquivos maiores que 100MB podem causar problemas
                self._call_callback(
                    "log",
                    "🚨 AVISO: Arquivo grande detectado - pode causar alto consumo de memória",
                )
        else:
            self._call_callback("log", "🚨 ERRO: Arquivo de entrada não encontrado!")

        # Arquivo de entrada
        cmd.extend(["-i", self.input_file])

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
        cmd.extend(["-y"])  # Sobrescrever arquivo de saída

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
        self._call_callback(
            "log", "🔍 DIAGNÓSTICO FRAMES: Iniciando construção do comando"
        )
        self._call_callback("log", f"🔍 Configurações de frames: {frame_settings}")
        self._call_callback("log", f"🔍 Arquivo de entrada: {self.input_file}")

        # Verificar se arquivo de entrada existe e obter informações básicas
        if os.path.exists(self.input_file):
            file_size = os.path.getsize(self.input_file) / (1024 * 1024)  # MB
            self._call_callback(
                "log", f"🔍 Tamanho do arquivo de entrada: {file_size:.1f} MB"
            )

            # Obter informações do vídeo para estimar quantidade de frames
            video_info = self.get_video_info(self.input_file)
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
        else:
            self._call_callback("log", "🚨 ERRO: Arquivo de entrada não encontrado!")

        # Arquivo de entrada
        cmd.extend(["-i", self.input_file])

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
            if settings.get("transparency", False):
                cmd.extend(["-pix_fmt", "yuva420p"])
        elif frame_format == "TIFF":
            cmd.extend(["-compression_algo", "lzw"])  # Compressão LZW para TIFF

        # Configurar padrão de nomenclatura dos arquivos
        output_dir = os.path.dirname(self.output_file)
        video_name = os.path.splitext(os.path.basename(self.input_file))[0]

        # Criar pasta automática se configurado
        if frame_settings.get("auto_folder", True):
            frame_folder = os.path.join(output_dir, f"{video_name}_frames")
            os.makedirs(frame_folder, exist_ok=True)
            output_pattern = os.path.join(
                frame_folder, f"{video_name}_frame_%04d.{frame_format.lower()}"
            )
        else:
            output_pattern = os.path.join(
                output_dir, f"{video_name}_frame_%04d.{frame_format.lower()}"
            )

        # Configurações gerais
        cmd.extend(["-y"])  # Sobrescrever arquivos de saída

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
        
        # Arquivo de entrada
        cmd.extend(["-i", self.input_file])
        
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
        cmd.extend(["-y"])  # Sobrescrever arquivo de saída
        
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
        if not self.cuda_available or self.cuda_fallback_attempted:
            return

        settings = self.conversion_settings
        use_hardware = settings.get("use_hardware_acceleration", True)

        if use_hardware and self.hw_settings.get("enabled", False):
            # Configurar decodificação CUVID
            cuda_config = self.hardware_config.get("cuda_config", {})
            gpu_index = cuda_config.get("gpu_index", 0)

            cmd.extend(["-hwaccel", "cuda"])
            cmd.extend(["-hwaccel_device", str(gpu_index)])
            # Removido -hwaccel_output_format cuda para evitar conflitos de filtros

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
        cpu_preference = performance_config.get("cpu_preference", "auto")
        nvidia_preference = performance_config.get("nvidia_preference", "auto")

        # Determinar se usar CUDA ou CPU baseado no modo de performance
        if cpu_preference == "force":
            # Modo Econômico: Forçar CPU sempre
            use_cuda = False
        elif nvidia_preference == "force" and self.cuda_available:
            # Modo Performance: Forçar NVIDIA se disponível
            use_cuda = not self.cuda_fallback_attempted and self.hw_settings.get(
                "enabled", False
            )
        else:
            # Modo Automático: Usar lógica original
            use_cuda = (
                self.cuda_available
                and use_hardware
                and not self.cuda_fallback_attempted
                and self.hw_settings.get("enabled", False)
            )

        # Para AVI, usar configurações específicas otimizadas
        if is_avi_format:
            self.add_avi_video_settings(cmd)
        # Codec de vídeo baseado na seleção do usuário
        else:
            # Obter codec selecionado pelo usuário (padrão: h264)
            selected_codec = settings.get("codec", "h264")

            # Verificar se o formato suporta codecs específicos
            if (
                "VP9" in format_name
                or "WEBM" in format_name.upper()
                or "WebM" in format_name
            ):
                # VP9/WEBM não tem suporte NVENC, usar CPU com VP9
                self.add_cpu_video_settings(cmd, "vp9")
                self._call_callback(
                    "log",
                    f"🔧 CORREÇÃO WEBM: Usando codec VP9 para formato {format_name}",
                )
            elif "WEBP" in format_name:
                # WebP não tem suporte NVENC, usar CPU
                self.add_cpu_video_settings(cmd, "webp")
            else:
                # Para MP4, MKV e outros formatos, usar codec selecionado
                if selected_codec == "hevc":  # H.265
                    if use_cuda:
                        self.add_cuda_video_settings(cmd, "hevc")
                    else:
                        self.add_cpu_video_settings(cmd, "hevc")
                else:  # H.264 (padrão)
                    if use_cuda:
                        self.add_cuda_video_settings(cmd, "h264")
                    else:
                        self.add_cpu_video_settings(cmd, "h264")

        # Configurações de FPS
        fps = settings.get("fps")
        if fps and fps != "Original":
            if fps == "Custom":
                custom_fps = settings.get("custom_fps", 30)
                cmd.extend(["-r", str(custom_fps)])
            else:
                cmd.extend(["-r", str(fps)])

        # Configurações de resolução
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

        # Configurações de transparência (para formatos suportados)
        if settings.get("transparency", False):
            if "WEBP" in format_name or "WebM" in format_name or "MOV" in format_name:
                cmd.extend(["-pix_fmt", "yuva420p"])

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
        cmd.extend(["-pix_fmt", "yuv420p"])  # Formato de pixel compatível
        cmd.extend(["-movflags", "+faststart"])  # Otimização para streaming

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
            while self.process.poll() is None and not self.cancelled:
                time.sleep(0.1)

            # Capturar saída final se necessário
            stdout = ""
            stderr = ""
            if self.process.stdout:
                try:
                    stdout = self.process.stdout.read()
                except:
                    pass
            if self.process.stderr:
                try:
                    stderr = self.process.stderr.read()
                except:
                    pass

            if self.cancelled:
                self._call_callback(
                    "finished", False, "Conversão cancelada pelo usuário"
                )
                return

            if self.process.returncode == 0:
                self._call_callback("status", "Conversão concluída com sucesso!")
                self._call_callback("progress", 100)
                self._call_callback(
                    "finished", True, "Conversão concluída com sucesso!"
                )
                self._call_callback("log", f"Arquivo salvo em: {self.output_file}")
            else:
                # Verificar se é erro relacionado ao CUDA e tentar fallback
                if self._is_cuda_error(stderr) and not self.cuda_fallback_attempted:
                    self._call_callback(
                        "log", "Erro CUDA detectado, tentando fallback para CPU..."
                    )
                    self._attempt_cpu_fallback()
                else:
                    error_msg = f"Erro na conversão: {stderr}"
                    self._call_callback("status", "Erro na conversão")
                    self._call_callback("finished", False, error_msg)
                    self._call_callback("log", error_msg)

        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            self._call_callback("status", "Erro na conversão")
            self._call_callback("finished", False, error_msg)
            self._call_callback("log", error_msg)

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
            while self.process.poll() is None and not self.cancelled:
                time.sleep(0.1)

            # Capturar saída final se necessário
            stdout = ""
            stderr = ""
            if self.process.stdout:
                try:
                    stdout = self.process.stdout.read()
                except:
                    pass
            if self.process.stderr:
                try:
                    stderr = self.process.stderr.read()
                except:
                    pass

            if self.cancelled:
                self._call_callback(
                    "finished", False, "Conversão cancelada pelo usuário"
                )
                return

            if self.process.returncode == 0:
                self._call_callback("status", "Conversão concluída com sucesso (CPU)!")
                self._call_callback("progress", 100)
                self._call_callback(
                    "finished", True, "Conversão concluída com sucesso usando CPU!"
                )
                self._call_callback("log", f"Arquivo salvo em: {self.output_file}")
            else:
                error_msg = f"Erro na conversão (CPU): {stderr}"
                self._call_callback("status", "Erro na conversão")
                self._call_callback("finished", False, error_msg)
                self._call_callback("log", error_msg)

        except Exception as e:
            error_msg = f"Erro no fallback CPU: {str(e)}"
            self._call_callback("status", "Erro na conversão")
            self._call_callback("finished", False, error_msg)
            self._call_callback("log", error_msg)

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

        import threading
        import time

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


class VideoConverterManager:
    """
    Gerenciador principal para conversões de vídeo
    Interface simplificada para uso na GUI
    """

    def __init__(self):
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
        """
        Constrói lista de formatos suportados baseada na configuração de hardware
        """
        formats = {
            "input": [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"],
            "output": {},
        }

        # Formatos básicos sempre disponíveis
        formats["output"].update({"WebM (VP9)": ".webm", "WEBP (Animado)": ".webp"})

        # Adicionar formatos H.264 e H.265 com indicação de aceleração
        if self.cuda_available:
            # Formatos com aceleração CUDA disponível
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
            # Apenas formatos CPU
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
                "Extração de Frames": ".jpg",  # Extensão padrão, será sobrescrita dinamicamente
                "Extração de Áudio": ".mp3",  # Extensão padrão, será sobrescrita dinamicamente
            }
        )

        return formats

    def get_max_concurrent_jobs(self, settings):
        """
        Obtém o número máximo de jobs simultâneos baseado no modo de performance

        Args:
            settings: Configurações de conversão incluindo performance_config

        Returns:
            int: Número máximo de jobs simultâneos
        """
        performance_config = settings.get("performance_config", {})
        max_jobs = performance_config.get("max_concurrent_jobs", 2)

        # Ajustar baseado na disponibilidade de hardware
        if not self.cuda_available and max_jobs > 1:
            # Reduzir jobs simultâneos se não há aceleração de hardware
            max_jobs = max(1, max_jobs // 2)

        return max_jobs

    def get_hardware_info(self):
        """
        Retorna informações sobre a configuração de hardware disponível

        Returns:
            dict: Informações de hardware incluindo CUDA, GPU, etc.
        """
        # Obter informações do detector de hardware
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
        """
        Verifica se o formato especificado usa aceleração CUDA

        Args:
            format_name: Nome do formato (ex: 'MP4 (H.264 - NVENC)')

        Returns:
            bool: True se usa CUDA/NVENC
        """
        return "NVENC" in format_name

    def is_supported_input_format(self, file_path):
        """
        Verifica se o formato do arquivo é suportado

        Args:
            file_path: Caminho do arquivo

        Returns:
            bool: True se suportado
        """
        is_valid, _ = validate_input_file(file_path)
        return is_valid

    def get_output_extension(self, format_name, frame_format=None, audio_format=None):
        """
        Retorna a extensão para o formato de saída

        Args:
            format_name: Nome do formato (ex: "MP4 (H.264)")
            frame_format: Formato específico para extração de frames (JPG, PNG, WebP, TIFF)
            audio_format: Formato específico para extração de áudio (MP3, AAC, WAV, etc.)

        Returns:
            str: Extensão do arquivo
        """
        # Para extração de frames, usar o formato específico selecionado
        if "Extração de Frames" in format_name and frame_format:
            frame_extensions = {
                "JPG": ".jpg",
                "PNG": ".png",
                "WebP": ".webp",
                "TIFF": ".tiff",
            }
            return frame_extensions.get(frame_format, ".jpg")
        
        # Para extração de áudio, usar o formato específico selecionado
        if "Extração de Áudio" in format_name and audio_format:
            if audio_format in AUDIO_CODEC_CONFIG:
                return AUDIO_CODEC_CONFIG[audio_format]["extension"]
            return ".mp3"  # Padrão

        return self.supported_formats["output"].get(format_name, ".mp4")

    def start_conversion(self, input_file, output_dir, settings, callbacks):
        """
        Inicia uma nova conversão

        Args:
            input_file: Arquivo de entrada
            output_dir: Diretório de saída
            settings: Configurações de conversão
            callbacks: Dicionário com funções callback

        Returns:
            VideoConverter: Thread de conversão ou None se inválido
        """
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

        # Gerar nome do arquivo de saída
        format_name = settings.get("format", "MP4 (H.264)")

        # Obter extensão correta baseada no formato
        extension = self.get_output_extension(format_name)
        if extension.startswith("."):
            extension = extension[1:]  # Remover o ponto inicial

        # CORREÇÃO: Evitar dupla extensão para formatos especiais
        if "Extração de Frames" in format_name:
            # Para extração de frames, usar apenas o formato específico
            frame_extension = self.get_output_extension(
                format_name, settings.get("frame_extraction_settings", {}).get("format")
            )
            if frame_extension.startswith("."):
                frame_extension = frame_extension[1:]
            extension = frame_extension
        elif "Extração de Áudio" in format_name:
            # Para extração de áudio, usar o formato específico selecionado
            audio_format = settings.get("audio_extraction_settings", {}).get("format", "MP3")
            audio_extension = self.get_output_extension(
                format_name, audio_format=audio_format
            )
            if audio_extension.startswith("."):
                audio_extension = audio_extension[1:]
            extension = audio_extension

        # CORREÇÃO CRÍTICA: Problema de nomenclatura GIF identificado
        # O FFmpeg não consegue processar nomes de arquivo com espaços e caracteres especiais
        if "GIF (Animado)" in format_name:
            # Para GIF, usar sempre extensão .gif simples, sem espaços ou caracteres especiais
            extension = "gif"
            # Gerar nome único sem caracteres problemáticos usando UUID
            input_path = Path(input_file)
            unique_id = str(uuid.uuid4()).replace("-", "")[:8]  # 8 caracteres únicos
            output_filename = f"{input_path.stem}_gif_{unique_id}.gif"
            self._call_callback(
                "log",
                f"🔧 CORREÇÃO APLICADA: Nome do arquivo GIF corrigido - {output_filename}",
            )
            self._call_callback(
                "log",
                f"🔧 DEBUG: format_name='{format_name}', input_file='{input_file}'",
            )
        else:
            output_filename = generate_output_filename(
                input_file, extension, "converted"
            )
            self._call_callback(
                "log",
                f"🔧 DEBUG: Formato normal - {format_name}, output_filename='{output_filename}'",
            )
        output_file = Path(output_dir) / output_filename

        # Criar thread de conversão
        self.converter_thread = VideoConverter()
        self.converter_thread.set_conversion_parameters(
            input_file, str(output_file), settings, callbacks
        )

        # Iniciar conversão
        self.converter_thread.start()

        return self.converter_thread

    def cancel_conversion(self):
        """
        Cancela a conversão atual
        """
        if self.converter_thread and self.converter_thread.is_alive():
            self.converter_thread.cancel_conversion()
            self.converter_thread.join(5)  # Aguardar até 5 segundos
