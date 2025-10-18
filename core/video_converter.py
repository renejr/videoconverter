"""
Motor de Conversão de Vídeos
Gerencia a conversão de vídeos usando FFmpeg com configurações avançadas
"""

import os
import subprocess
import threading
import time
import re
from pathlib import Path

from utils.config import (SUPPORTED_INPUT_FORMATS, QUALITY_PRESETS, 
                         RESOLUTION_PRESETS, FFMPEG_TIMEOUT, FFMPEG_PROGRESS_REGEX,
                         get_hardware_config, NVENC_QUALITY_PRESETS, NVENC_CODEC_SETTINGS)
from utils.validators import (validate_input_file, validate_output_directory,
                             validate_conversion_settings, generate_output_filename)
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
        
        # Configuração de hardware
        self.hardware_config_obj = get_hardware_config()
        self.hardware_config = self.hardware_config_obj.auto_configure()
        self.hw_settings = self.hardware_config.get('hardware_acceleration', {})
        self.cuda_available = self.hardware_config.get('hardware_acceleration', {}).get('enabled', False)
        self.cuda_fallback_attempted = False
    
    def set_conversion_parameters(self, input_file, output_file, settings, callbacks=None):
        """
        Define os parâmetros para conversão
        
        Args:
            input_file: Caminho do arquivo de entrada
            output_file: Caminho do arquivo de saída
            settings: Dicionário com configurações de conversão
            callbacks: Dicionário com funções callback
        """
        # Log dos parâmetros recebidos
        self._call_callback('log', f"Parâmetros de conversão - Input: {input_file}")
        self._call_callback('log', f"Parâmetros de conversão - Output: {output_file}")
        
        # Garantir que os caminhos sejam absolutos
        self.input_file = os.path.abspath(input_file) if input_file else input_file
        self.output_file = os.path.abspath(output_file) if output_file else output_file
        
        # Log dos caminhos processados
        self._call_callback('log', f"Caminho input processado: {self.input_file}")
        self._call_callback('log', f"Caminho output processado: {self.output_file}")
        
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
        ffprobe_cmd = ffmpeg_cmd.replace('ffmpeg', 'ffprobe')
        
        # Log do caminho original recebido
        self._call_callback('log', f"Caminho original recebido: {file_path}")
        
        # Garantir que o caminho do arquivo seja absoluto e exista
        abs_file_path = os.path.abspath(file_path)
        self._call_callback('log', f"Caminho absoluto: {abs_file_path}")
        
        if not os.path.exists(abs_file_path):
            self._call_callback('log', f"Arquivo não encontrado: {abs_file_path}")
            # Tentar verificar se existe em outros locais comuns
            possible_paths = [
                file_path,
                file_path.replace('/', '\\'),
                file_path.replace('\\', '/'),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    self._call_callback('log', f"Arquivo encontrado em: {path}")
                    abs_file_path = os.path.abspath(path)
                    break
            else:
                return None
        
        cmd = [
            ffprobe_cmd,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            abs_file_path
        ]
        
        try:
            # Log do comando completo que será executado
            self._call_callback('log', f"Comando FFprobe: {' '.join(cmd)}")
            self._call_callback('log', f"Diretório de trabalho: {os.getcwd()}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Log detalhado da execução
            self._call_callback('log', f"FFprobe returncode: {result.returncode}")
            if result.stdout:
                self._call_callback('log', f"FFprobe stdout: {result.stdout[:200]}...")
            if result.stderr:
                self._call_callback('log', f"FFprobe stderr: {result.stderr}")
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                return self.parse_video_info(info)
            else:
                self._call_callback('log', f"FFprobe falhou com código {result.returncode}: {result.stderr}")
        except subprocess.TimeoutExpired:
            self._call_callback('log', "FFprobe timeout - comando demorou mais de 30 segundos")
        except FileNotFoundError as e:
            self._call_callback('log', f"FFprobe não encontrado: {str(e)}")
        except Exception as e:
            self._call_callback('log', f"Erro ao obter informações do vídeo: {str(e)}")
            self._call_callback('log', f"Tipo do erro: {type(e).__name__}")
        
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
            'duration': 0,
            'width': 0,
            'height': 0,
            'fps': 0,
            'codec': '',
            'has_audio': False
        }
        
        try:
            # Duração total
            if 'format' in ffprobe_info and 'duration' in ffprobe_info['format']:
                video_info['duration'] = float(ffprobe_info['format']['duration'])
            
            # Informações dos streams
            for stream in ffprobe_info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_info['width'] = stream.get('width', 0)
                    video_info['height'] = stream.get('height', 0)
                    video_info['codec'] = stream.get('codec_name', '')
                    
                    # FPS
                    fps_str = stream.get('r_frame_rate', '0/1')
                    if '/' in fps_str:
                        num, den = fps_str.split('/')
                        if int(den) > 0:
                            video_info['fps'] = round(int(num) / int(den), 2)
                
                elif stream.get('codec_type') == 'audio':
                    video_info['has_audio'] = True
        
        except Exception as e:
            self._call_callback('log', f"Erro ao processar informações: {str(e)}")
        
        return video_info
    
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
        
        # Configurações de decodificação CUDA (se disponível)
        self.add_cuda_decoder_settings(cmd)
        
        # Arquivo de entrada
        cmd.extend(['-i', self.input_file])
        
        # Configurações de vídeo
        self.add_video_settings(cmd)
        
        # Configurações de áudio
        self.add_audio_settings(cmd)
        
        # Configurações gerais
        cmd.extend(['-y'])  # Sobrescrever arquivo de saída
        
        # Arquivo de saída
        cmd.append(self.output_file)
        
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
        use_hardware = settings.get('use_hardware_acceleration', True)
        
        if use_hardware and self.hw_settings.get('enabled', False):
            # Configurar decodificação CUVID
            cuda_config = self.hardware_config.get('cuda_config', {})
            gpu_index = cuda_config.get('gpu_index', 0)
            
            cmd.extend(['-hwaccel', 'cuda'])
            cmd.extend(['-hwaccel_device', str(gpu_index)])
            # Removido -hwaccel_output_format cuda para evitar conflitos de filtros
    
    def add_video_settings(self, cmd):
        """
        Adiciona configurações de vídeo ao comando FFmpeg
        
        Args:
            cmd: Lista do comando FFmpeg
        """
        settings = self.conversion_settings
        format_name = settings.get('format', 'MP4 (H.264)')
        use_hardware = settings.get('use_hardware_acceleration', True)
        
        # Obter configuração do modo de performance
        performance_config = settings.get('performance_config', {})
        cpu_preference = performance_config.get('cpu_preference', 'auto')
        nvidia_preference = performance_config.get('nvidia_preference', 'auto')
        
        # Determinar se usar CUDA ou CPU baseado no modo de performance
        if cpu_preference == 'force':
            # Modo Econômico: Forçar CPU sempre
            use_cuda = False
        elif nvidia_preference == 'force' and self.cuda_available:
            # Modo Performance: Forçar NVIDIA se disponível
            use_cuda = (not self.cuda_fallback_attempted and
                       self.hw_settings.get('enabled', False))
        else:
            # Modo Automático: Usar lógica original
            use_cuda = (self.cuda_available and 
                       use_hardware and 
                       not self.cuda_fallback_attempted and
                       self.hw_settings.get('enabled', False))
        
        # Codec de vídeo
        if 'H.264' in format_name:
            if use_cuda:
                self.add_cuda_video_settings(cmd, 'h264')
            else:
                self.add_cpu_video_settings(cmd, 'h264')
                
        elif 'H.265' in format_name:
            if use_cuda:
                self.add_cuda_video_settings(cmd, 'hevc')
            else:
                self.add_cpu_video_settings(cmd, 'hevc')
                
        elif 'VP9' in format_name:
            # VP9 não tem suporte NVENC, usar CPU
            self.add_cpu_video_settings(cmd, 'vp9')
                
        elif 'WEBP' in format_name:
            # WebP não tem suporte NVENC, usar CPU
            self.add_cpu_video_settings(cmd, 'webp')
            
        # Configurações de FPS
        fps = settings.get('fps')
        if fps and fps != 'Original':
            if fps == 'Custom':
                custom_fps = settings.get('custom_fps', 30)
                cmd.extend(['-r', str(custom_fps)])
            else:
                cmd.extend(['-r', str(fps)])
        
        # Configurações de resolução
        resolution = settings.get('resolution')
        if resolution and resolution != 'Original':
            if resolution == 'Custom':
                width = settings.get('custom_width', 1920)
                height = settings.get('custom_height', 1080)
                cmd.extend(['-s', f'{width}x{height}'])
            else:
                # Usar presets de resolução
                if resolution in RESOLUTION_PRESETS:
                    res_value = RESOLUTION_PRESETS[resolution]
                    if res_value and isinstance(res_value, tuple):
                        # Converter tupla (width, height) para string "widthxheight"
                        cmd.extend(['-s', f'{res_value[0]}x{res_value[1]}'])
                    elif res_value:
                        cmd.extend(['-s', res_value])
        
        # Configurações de transparência (para formatos suportados)
        if settings.get('transparency', False):
            if 'WEBP' in format_name or 'WebM' in format_name or 'MOV' in format_name:
                cmd.extend(['-pix_fmt', 'yuva420p'])
    
    def add_cuda_video_settings(self, cmd, codec_type):
        """
        Adiciona configurações de vídeo CUDA/NVENC ao comando FFmpeg
        
        Args:
            cmd: Lista do comando FFmpeg
            codec_type: Tipo do codec ('h264' ou 'hevc')
        """
        settings = self.conversion_settings
        quality = settings.get('quality', 'Alta')
        
        # Determinar encoder NVENC
        if codec_type == 'h264':
            encoder = 'h264_nvenc'
        elif codec_type == 'hevc':
            encoder = 'hevc_nvenc'
        else:
            # Fallback para CPU
            self.add_cpu_video_settings(cmd, codec_type)
            return
        
        cmd.extend(['-c:v', encoder])
        
        # Adicionar filtro de conversão de formato se usando CUDA decoder
        # Isso resolve o problema de incompatibilidade entre filtros CUDA e CPU
        if self.hw_settings.get('enabled', False):
            cmd.extend(['-vf', 'hwdownload,format=nv12'])
        
        # Configurações de qualidade NVENC
        quality_presets = self.hardware_config.get('quality_presets', {})
        nvenc_presets = quality_presets.get('nvenc', NVENC_QUALITY_PRESETS)
        
        # Obter preset NVENC do modo de performance
        performance_config = settings.get('performance_config', {})
        nvenc_preset = performance_config.get('nvenc_preset', 'medium')
        
        if quality in nvenc_presets:
            preset_config = nvenc_presets[quality]
            
            # Preset NVENC (usar do modo de performance se disponível)
            cmd.extend(['-preset', nvenc_preset])
            
            # Rate control
            rc_mode = preset_config.get('rc_mode', 'vbr')
            cmd.extend(['-rc', rc_mode])
            
            # Bitrate ou CQ
            if rc_mode == 'cq':
                cmd.extend(['-cq', str(preset_config.get('cq', 23))])
            else:
                bitrate = preset_config.get('bitrate', '5M')
                cmd.extend(['-b:v', bitrate])
                if 'maxrate' in preset_config:
                    cmd.extend(['-maxrate', preset_config['maxrate']])
                    cmd.extend(['-bufsize', preset_config.get('bufsize', preset_config['maxrate'])])
        
        # Configurações específicas do codec
        codec_settings = NVENC_CODEC_SETTINGS.get(encoder, {})
        
        # Profile
        if 'profiles' in codec_settings and codec_settings['profiles']:
            profile = codec_settings['profiles'][0]
            cmd.extend(['-profile:v', profile])
        
        # Level (se especificado)
        if 'levels' in codec_settings and codec_settings['levels']:
            level = codec_settings['levels'][0]
            cmd.extend(['-level', level])
        
        # GPU específica
        cuda_config = self.hardware_config.get('cuda_config', {})
        gpu_index = cuda_config.get('gpu_index', 0)
        cmd.extend(['-gpu', str(gpu_index)])
    
    def add_cpu_video_settings(self, cmd, codec_type):
        """
        Adiciona configurações de vídeo CPU ao comando FFmpeg
        
        Args:
            cmd: Lista do comando FFmpeg
            codec_type: Tipo do codec ('h264', 'hevc', 'vp9', 'webp')
        """
        settings = self.conversion_settings
        quality = settings.get('quality', 'Alta')
        
        if codec_type == 'h264':
            cmd.extend(['-c:v', 'libx264'])
            # Configurações de qualidade para H.264
            if quality == 'Alta':
                cmd.extend(['-crf', '18'])
            elif quality == 'Média':
                cmd.extend(['-crf', '23'])
            else:  # Baixa
                cmd.extend(['-crf', '28'])
                
        elif codec_type == 'hevc':
            cmd.extend(['-c:v', 'libx265'])
            if quality == 'Alta':
                cmd.extend(['-crf', '20'])
            elif quality == 'Média':
                cmd.extend(['-crf', '25'])
            else:  # Baixa
                cmd.extend(['-crf', '30'])
                
        elif codec_type == 'vp9':
            cmd.extend(['-c:v', 'libvpx-vp9'])
            if quality == 'Alta':
                cmd.extend(['-crf', '15', '-b:v', '0'])
            elif quality == 'Média':
                cmd.extend(['-crf', '20', '-b:v', '0'])
            else:  # Baixa
                cmd.extend(['-crf', '25', '-b:v', '0'])
                
        elif codec_type == 'webp':
            cmd.extend(['-c:v', 'libwebp'])
            # Configurações específicas para WebP animado
            from utils.config import WEBP_QUALITY_PRESETS
            webp_settings = WEBP_QUALITY_PRESETS.get(quality, WEBP_QUALITY_PRESETS['Média'])
            
            cmd.extend(['-quality', str(webp_settings['quality'])])
            cmd.extend(['-method', str(webp_settings['method'])])
            
            # Configurações para animação
            cmd.extend(['-loop', '0'])  # Loop infinito
    
    def add_audio_settings(self, cmd):
        """
        Adiciona configurações de áudio ao comando FFmpeg
        
        Args:
            cmd: Lista do comando FFmpeg
        """
        # Determinar codec de áudio baseado no formato de saída
        output_ext = Path(self.output_file).suffix.lower()
        
        if output_ext == '.webm':
            # WebM suporta apenas Vorbis ou Opus
            cmd.extend(['-c:a', 'libopus', '-b:a', '192k'])
        elif output_ext in ['.mp4', '.mov', '.m4v']:
            # MP4 e formatos relacionados usam AAC
            cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
        elif output_ext in ['.mkv', '.avi']:
            # MKV e AVI podem usar AAC ou outros codecs
            cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
        else:
            # Padrão para outros formatos
            cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
    
    def run(self):
        """
        Executa a conversão de vídeo em thread separada
        """
        try:
            self._call_callback('status', "Iniciando conversão...")
            self._call_callback('log', f"Convertendo: {os.path.basename(self.input_file)}")
            
            # Obter informações do vídeo para calcular progresso
            video_info = self.get_video_info(self.input_file)
            total_duration = video_info.get('duration', 0) if video_info else 0
            
            # Construir comando FFmpeg
            cmd = self.build_ffmpeg_command()
            self._call_callback('log', f"Comando FFmpeg: {' '.join(cmd)}")
            
            # Executar conversão
            self._call_callback('log', f"Executando FFmpeg no diretório: {os.getcwd()}")
            self._call_callback('log', f"Arquivo de entrada existe: {os.path.exists(self.input_file)}")
            self._call_callback('log', f"Diretório de saída existe: {os.path.exists(os.path.dirname(self.output_file))}")
            
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                self._call_callback('log', f"Processo FFmpeg iniciado com PID: {self.process.pid}")
            except Exception as e:
                self._call_callback('log', f"Erro ao iniciar processo FFmpeg: {str(e)}")
                self._call_callback('log', f"Tipo do erro: {type(e).__name__}")
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
                self._call_callback('finished', False, "Conversão cancelada pelo usuário")
                return
            
            if self.process.returncode == 0:
                self._call_callback('status', "Conversão concluída com sucesso!")
                self._call_callback('progress', 100)
                self._call_callback('finished', True, "Conversão concluída com sucesso!")
                self._call_callback('log', f"Arquivo salvo em: {self.output_file}")
            else:
                # Verificar se é erro relacionado ao CUDA e tentar fallback
                if self._is_cuda_error(stderr) and not self.cuda_fallback_attempted:
                    self._call_callback('log', "Erro CUDA detectado, tentando fallback para CPU...")
                    self._attempt_cpu_fallback()
                else:
                    error_msg = f"Erro na conversão: {stderr}"
                    self._call_callback('status', "Erro na conversão")
                    self._call_callback('finished', False, error_msg)
                    self._call_callback('log', error_msg)
                
        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            self._call_callback('status', "Erro na conversão")
            self._call_callback('finished', False, error_msg)
            self._call_callback('log', error_msg)
    
    def _is_cuda_error(self, error_message):
        """
        Verifica se o erro está relacionado ao CUDA/NVENC
        
        Args:
            error_message: Mensagem de erro do FFmpeg
            
        Returns:
            bool: True se for erro CUDA/NVENC
        """
        cuda_error_keywords = [
            'cuda error',
            'nvenc error',
            'nvenc initialization failed',
            'no cuda-capable device',
            'cuda driver version',
            'cuda runtime error',
            'nvenc encoder',
            'cuvid decoder',
            'cuvidcreatevideoparser',
            'cannot load cuvid',
            'gpu memory',
            'cuda context',
            'cuda out of memory',
            'nvenc not available',
            'cuda device',
            'impossible to convert between the formats',
            'error reinitializing filters',
            'function not implemented',
            'auto_scale_0'
        ]
        
        error_lower = error_message.lower()
        return any(keyword in error_lower for keyword in cuda_error_keywords)
    
    def _attempt_cpu_fallback(self):
        """
        Tenta executar a conversão novamente usando CPU
        """
        try:
            self.cuda_fallback_attempted = True
            self._call_callback('status', "Tentando conversão com CPU...")
            
            # Obter informações do vídeo para calcular progresso
            video_info = self.get_video_info(self.input_file)
            total_duration = video_info.get('duration', 0) if video_info else 0
            
            # Construir comando FFmpeg (agora forçará uso de CPU)
            cmd = self.build_ffmpeg_command()
            self._call_callback('log', f"Comando FFmpeg (CPU): {' '.join(cmd)}")
            
            # Executar conversão
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
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
                self._call_callback('finished', False, "Conversão cancelada pelo usuário")
                return
            
            if self.process.returncode == 0:
                self._call_callback('status', "Conversão concluída com sucesso (CPU)!")
                self._call_callback('progress', 100)
                self._call_callback('finished', True, "Conversão concluída com sucesso usando CPU!")
                self._call_callback('log', f"Arquivo salvo em: {self.output_file}")
            else:
                error_msg = f"Erro na conversão (CPU): {stderr}"
                self._call_callback('status', "Erro na conversão")
                self._call_callback('finished', False, error_msg)
                self._call_callback('log', error_msg)
                
        except Exception as e:
            error_msg = f"Erro no fallback CPU: {str(e)}"
            self._call_callback('status', "Erro na conversão")
            self._call_callback('finished', False, error_msg)
            self._call_callback('log', error_msg)
    
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
            self._call_callback('log', f"Monitor de progresso: processo={self.process is not None}, duração={total_duration}")
            return
        
        # Padrões regex para extrair tempo atual da saída do FFmpeg
        time_patterns = [
            re.compile(r'time=(\d+):(\d+):(\d+\.\d+)'),
            re.compile(r'time=(\d+):(\d+):(\d+)'),
            re.compile(r'out_time_ms=(\d+)'),
        ]
        
        self._call_callback('log', f"Iniciando monitoramento de progresso. Duração total: {total_duration}s")
        
        import threading
        import time
        
        def read_output(pipe, pipe_name):
            """Lê a saída do pipe em thread separada"""
            try:
                while self.process.poll() is None and not self.cancelled:
                    line = pipe.readline()
                    if line:
                        line = line.strip()
                        self._call_callback('log', f"FFmpeg {pipe_name}: {line}")
                        
                        # Procurar informação de tempo na linha
                        for pattern in time_patterns:
                            match = pattern.search(line)
                            if match:
                                try:
                                    if 'out_time_ms' in pattern.pattern:
                                        # Tempo em microssegundos
                                        current_time = int(match.group(1)) / 1000000
                                    else:
                                        # Formato HH:MM:SS
                                        if len(match.groups()) == 3:
                                            hours = int(match.group(1))
                                            minutes = int(match.group(2))
                                            seconds = float(match.group(3))
                                            current_time = hours * 3600 + minutes * 60 + seconds
                                        else:
                                            continue
                                    
                                    progress = min(int((current_time / total_duration) * 100), 99)
                                    self._call_callback('progress', progress)
                                    self._call_callback('status', f"Convertendo... {progress}%")
                                    self._call_callback('log', f"Progresso: {current_time:.1f}s / {total_duration:.1f}s ({progress}%)")
                                    break
                                except (ValueError, ZeroDivisionError) as e:
                                    self._call_callback('log', f"Erro ao calcular progresso: {e}")
                    else:
                        time.sleep(0.1)
            except Exception as e:
                self._call_callback('log', f"Erro no monitoramento {pipe_name}: {e}")
        
        # Criar threads para ler stdout e stderr
        if self.process.stdout:
            stdout_thread = threading.Thread(target=read_output, args=(self.process.stdout, "stdout"))
            stdout_thread.daemon = True
            stdout_thread.start()
        
        if self.process.stderr:
            stderr_thread = threading.Thread(target=read_output, args=(self.process.stderr, "stderr"))
            stderr_thread.daemon = True
            stderr_thread.start()
    
    def cancel_conversion(self):
        """
        Cancela a conversão em andamento
        """
        self.cancelled = True
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


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
        self.cuda_available = self.hardware_config.get('hardware_acceleration', {}).get('enabled', False)
        
        # Formatos suportados baseados na configuração de hardware
        self.supported_formats = self._build_supported_formats()
    
    def _build_supported_formats(self):
        """
        Constrói lista de formatos suportados baseada na configuração de hardware
        """
        formats = {
            'input': ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'],
            'output': {}
        }
        
        # Formatos básicos sempre disponíveis
        formats['output'].update({
            'WebM (VP9)': '.webm',
            'WEBP (Animado)': '.webp'
        })
        
        # Adicionar formatos H.264 e H.265 com indicação de aceleração
        if self.cuda_available:
            # Formatos com aceleração CUDA disponível
            formats['output'].update({
                'MP4 (H.264 - NVENC)': '.mp4',
                'AVI (H.264 - NVENC)': '.avi', 
                'MOV (H.264 - NVENC)': '.mov',
                'MKV (H.264 - NVENC)': '.mkv',
                'MP4 (H.265 - NVENC)': '.mp4',
                'MKV (H.265 - NVENC)': '.mkv',
                # Opções CPU como fallback
                'MP4 (H.264 - CPU)': '.mp4',
                'AVI (H.264 - CPU)': '.avi', 
                'MOV (H.264 - CPU)': '.mov',
                'MKV (H.264 - CPU)': '.mkv',
                'MP4 (H.265 - CPU)': '.mp4'
            })
        else:
            # Apenas formatos CPU
            formats['output'].update({
                'MP4 (H.264)': '.mp4',
                'AVI (H.264)': '.avi', 
                'MOV (H.264)': '.mov',
                'MKV (H.264)': '.mkv',
                'MP4 (H.265)': '.mp4'
            })
        
        return formats

    def get_max_concurrent_jobs(self, settings):
        """
        Obtém o número máximo de jobs simultâneos baseado no modo de performance
        
        Args:
            settings: Configurações de conversão incluindo performance_config
            
        Returns:
            int: Número máximo de jobs simultâneos
        """
        performance_config = settings.get('performance_config', {})
        max_jobs = performance_config.get('max_concurrent_jobs', 2)
        
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
            'cuda_available': self.cuda_available,
            'hardware_config': self.hardware_config,
            'gpu_info': gpu_info,
            'recommended_settings': self.hardware_config.get('recommended_settings', {}),
            'cuda_settings': self.hardware_config.get('cuda_config', {}),
            'quality_presets': self.hardware_config.get('quality_presets', {})
        }
    
    def is_cuda_format(self, format_name):
        """
        Verifica se o formato especificado usa aceleração CUDA
        
        Args:
            format_name: Nome do formato (ex: 'MP4 (H.264 - NVENC)')
            
        Returns:
            bool: True se usa CUDA/NVENC
        """
        return 'NVENC' in format_name
    
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
    
    def get_output_extension(self, format_name):
        """
        Retorna a extensão para o formato de saída
        
        Args:
            format_name: Nome do formato (ex: "MP4 (H.264)")
            
        Returns:
            str: Extensão do arquivo
        """
        return self.supported_formats['output'].get(format_name, '.mp4')
    
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
            if 'log' in callbacks:
                callbacks['log'](f"Erro na validação do arquivo: {error_msg}")
            if 'finished' in callbacks:
                callbacks['finished'](False, f"Arquivo inválido: {error_msg}")
            return None
        
        # Validar diretório de saída
        is_valid, error_msg = validate_output_directory(output_dir)
        if not is_valid:
            if 'log' in callbacks:
                callbacks['log'](f"Erro na validação do diretório: {error_msg}")
            if 'finished' in callbacks:
                callbacks['finished'](False, f"Diretório inválido: {error_msg}")
            return None
        
        # Validar configurações
        is_valid, error_msg = validate_conversion_settings(settings)
        if not is_valid:
            if 'log' in callbacks:
                callbacks['log'](f"Erro nas configurações: {error_msg}")
            if 'finished' in callbacks:
                callbacks['finished'](False, f"Configurações inválidas: {error_msg}")
            return None
        
        # Cancelar conversão anterior se existir
        self.cancel_conversion()
        
        # Gerar nome do arquivo de saída
        output_filename = generate_output_filename(
            input_file, 
            settings.get('format', 'MP4 (H.264)').lower(),
            "converted"
        )
        output_file = Path(output_dir) / output_filename
        
        # Criar thread de conversão
        self.converter_thread = VideoConverter()
        self.converter_thread.set_conversion_parameters(input_file, str(output_file), settings, callbacks)
        
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