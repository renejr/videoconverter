"""
Interface gráfica principal do Video Converter usando Tkinter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
import yt_dlp
import json
import time
import random
import re
import platform
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("PyWebView não está disponível. Funcionalidade de navegador avançado desabilitada.")

from video_converter_module.core.queue_manager import ConversionQueueManager
from video_converter_module.core.ffmpeg_installer import FFmpegInstaller
from video_converter_module.utils.config import (
    SUPPORTED_OUTPUT_FORMATS,
    FPS_OPTIONS,
    RESOLUTION_PRESETS,
    GIF_QUALITY_PRESETS,
    GIF_FPS_OPTIONS,
    GIF_COLOR_OPTIONS,
    GIF_RESOLUTION_PRESETS,
    FRAME_EXTRACTION_FORMATS,
    FRAME_EXTRACTION_MODES,
    WEBP_FRAME_PRESETS,
    SUPPORTED_AUDIO_FORMATS,
    AUDIO_QUALITY_PRESETS,
    AUDIO_EXTRACTION_DEFAULTS,
)
from utils.validators import validate_input_file, validate_output_directory
from utils.performance_modes import (
    PerformanceMode,
    PerformanceModeConfig,
    get_performance_mode_labels,
    get_performance_mode_tooltips,
)
from utils.updater import UpdateChecker
from gui.update_widget import UpdateWidget
from gui.youtube_api_downloader import YouTubeAPIDownloader





class MainWindow:
    """
    Janela principal da aplicação Video Converter
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Video Converter - Conversor de Vídeo")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Iniciar em tela cheia (maximizada)
        self.root.state("zoomed")  # Windows
        # Para outros sistemas: self.root.attributes('-zoomed', True)

        # Inicializar componentes
        self.video_converter = ConversionQueueManager()
        self.queue_manager = ConversionQueueManager()
        self.conversion_thread = None
        self.ffmpeg_installer = FFmpegInstaller()
        
        # Inicializar sistema de atualização
        self.update_widget = UpdateWidget(self.root, "usuario/vidconv")
        self.update_checker = UpdateChecker("usuario/vidconv")
        
        # Inicializar YouTube API Downloader
        self.youtube_api_key = "AIzaSyBpZfgIsbwLEv7jlHQyOTE4jXdREMWkZNA"
        self.youtube_api_downloader = YouTubeAPIDownloader(self.youtube_api_key)
        
        # Inicializar extrator de navegador avançado


        # Configurar estilo
        self.setup_style()

        # Criar interface
        self.create_widgets()

        # Configurar callbacks globais do queue manager
        self._setup_queue_callbacks()

        # Verificar FFmpeg na inicialização
        self.check_ffmpeg_installation()

    def log(self, message):
        """
        Adiciona mensagem ao log de forma thread-safe
        """
        def update_gui():
            try:
                if hasattr(self, "log_text") and self.log_text.winfo_exists():
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log_entry = f"[{timestamp}] {message}\n"
                    self.log_text.insert(tk.END, log_entry)
                    self.log_text.see(tk.END)
                else:
                    print(f"[LOG] {message}")
            except RuntimeError:
                # Ocorre em testes quando a GUI não está no loop principal
                print(f"[LOG-FALLBACK] {message}")

        if hasattr(self, "root"):
            try:
                self.root.after(0, update_gui)
            except RuntimeError:
                # Fallback para quando o root não está mais no mainloop
                update_gui()
        else:
            update_gui() # Execução direta para testes

    def log_youtube(self, message):
        """
        Adiciona mensagem ao log do YouTube de forma thread-safe
        """
        def update_gui():
            try:
                if hasattr(self, "youtube_log_text") and self.youtube_log_text.winfo_exists():
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log_entry = f"[{timestamp}] {message}\n"
                    self.youtube_log_text.insert(tk.END, log_entry)
                    self.youtube_log_text.see(tk.END)
                else:
                    print(f"[YTLOG] {message}")
            except RuntimeError:
                # Ocorre em testes quando a GUI não está no loop principal
                print(f"[YTLOG-FALLBACK] {message}")

        if hasattr(self, "root"):
            try:
                self.root.after(0, update_gui)
            except RuntimeError:
                # Fallback para quando o root não está mais no mainloop
                update_gui()
        else:
            update_gui() # Execução direta para testes

    def setup_style(self):
        """
        Configura o estilo da aplicação
        """
        style = ttk.Style()
        style.theme_use("clam")

        # Configurar cores
        style.configure("Title.TLabel", font=("Arial", 12, "bold"))
        style.configure("Success.TLabel", foreground="green")
        style.configure("Error.TLabel", foreground="red")
        
        # Configurar estilo para barra de progresso de download (vermelha)
        style.configure("Download.Horizontal.TProgressbar", 
                       background="red", 
                       troughcolor="lightgray",
                       borderwidth=1, 
                       lightcolor="red", 
                       darkcolor="darkred")

    def create_widgets(self):
        """
        Cria todos os widgets da interface
        """
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Criar notebook (sistema de abas)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Criar aba "Arquivos"
        self.files_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.files_frame, text="Arquivos")
        
        # Criar aba "Logs"
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="Logs")

        # Configurar grid das abas
        self.files_frame.columnconfigure(1, weight=1)
        self.logs_frame.columnconfigure(0, weight=1)
        self.logs_frame.rowconfigure(0, weight=1)

        # Seção de arquivos (na aba Arquivos)
        self.create_file_section(self.files_frame, 0)

        # Seção de configurações (na aba Arquivos)
        self.create_settings_section(self.files_frame, 1)

        # Seção de progresso (na aba Arquivos)
        self.create_progress_section(self.files_frame, 2)

        # Seção de ações (na aba Arquivos)
        self.create_actions_section(self.files_frame, 3)

        # Seção de logs (na aba Logs)
        self.create_logs_tab_content(self.logs_frame)

        # Barra de status
        self.create_status_bar()

        # Configurar tooltips após criação de todos os widgets
        self.setup_performance_tooltips()

    def create_file_section(self, parent, row):
        """
        Cria a seção de seleção de arquivos
        """
        # Frame de arquivos
        file_frame = ttk.LabelFrame(parent, text="Arquivos", padding="10")
        file_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(1, weight=1)

        # Seção de Download de URL
        url_frame = ttk.Frame(file_frame)
        url_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(1, weight=1)

        ttk.Label(url_frame, text="URL do YouTube:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.youtube_url_var = tk.StringVar()
        self.youtube_url_entry = ttk.Entry(url_frame, textvariable=self.youtube_url_var, width=50)
        self.youtube_url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Seletor de método removido - agora usa estratégia automática inteligente

        ttk.Button(url_frame, text="Verificar", command=self.verify_youtube_url).grid(row=0, column=2, pady=2, padx=(0, 5))

        # Botão Navegador Avançado - OCULTO
        # browser_btn = ttk.Button(url_frame, text="🌐 Navegador", command=self.open_browser_extractor)
        # browser_btn.grid(row=0, column=3, pady=2, padx=(0, 5))
        # if not WEBVIEW_AVAILABLE:
        #     browser_btn.config(state="disabled")

        self.resolution_var = tk.StringVar()
        self.resolution_combobox = ttk.Combobox(url_frame, textvariable=self.resolution_var, state="disabled", width=15)
        self.resolution_combobox.grid(row=1, column=2, padx=5, pady=2)

        ttk.Button(url_frame, text="Baixar Vídeo", command=self.download_youtube_video).grid(row=1, column=3, pady=2)

        # Botões de seleção
        buttons_frame = ttk.Frame(file_frame)
        buttons_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        ttk.Button(
            buttons_frame, text="Adicionar Arquivos...", command=self.browse_input_files
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            buttons_frame,
            text="Remover Selecionados",
            command=self.remove_selected_files,
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            buttons_frame, text="Limpar Lista", command=self.clear_file_list
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            buttons_frame, text="Limpar Tudo", command=self.clear_fields
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Separador visual
        ttk.Separator(buttons_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=5)

        # Botões de ação
        self.convert_btn = ttk.Button(
            buttons_frame, text="Converter", command=self.start_conversion
        )
        self.convert_btn.pack(side=tk.LEFT, padx=(5, 5))

        self.cancel_btn = ttk.Button(
            buttons_frame,
            text="Cancelar",
            command=self.cancel_conversion,
            state="disabled",
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Botão de atualização (criado manualmente para usar pack)
        self.update_btn = tk.Button(
            buttons_frame,
            text="🔄 Verificar Atualizações",
            command=self.update_widget.manual_check,
            font=('Arial', 9),
            bg='#f0f0f0',
            relief='raised',
            bd=1,
            padx=10,
            pady=2
        )
        self.update_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Lista de arquivos
        list_frame = ttk.Frame(file_frame)
        list_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Treeview para mostrar arquivos
        columns = ("arquivo", "status", "progresso", "gpu")
        self.files_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=6
        )

        # Configurar colunas
        self.files_tree.heading("arquivo", text="Arquivo")
        self.files_tree.heading("status", text="Status")
        self.files_tree.heading("progresso", text="Progresso")
        self.files_tree.heading("gpu", text="GPU")

        self.files_tree.column("arquivo", width=300, minwidth=200)
        self.files_tree.column("status", width=100, minwidth=80)
        self.files_tree.column("progresso", width=100, minwidth=80)
        self.files_tree.column("gpu", width=80, minwidth=60)

        # Scrollbar para a lista
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.files_tree.yview
        )
        self.files_tree.configure(yscrollcommand=scrollbar.set)

        self.files_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Pasta de saída
        ttk.Label(file_frame, text="Pasta de Saída:").grid(
            row=3, column=0, sticky=tk.W, pady=2
        )
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(
            file_frame, textvariable=self.output_dir_var, width=50
        )
        self.output_dir_entry.grid(
            row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2
        )
        ttk.Button(file_frame, text="Procurar...", command=self.browse_output_dir).grid(
            row=3, column=2, pady=2
        )

        # Lista interna de arquivos
        self.selected_files = []

    def download_youtube_video(self):
        """
        Inicia o download de um vídeo do YouTube a partir da URL fornecida.
        Implementa sistema inteligente: API Oficial -> yt-dlp com estratégias -> yt-dlp básico
        """
        url = self.youtube_url_var.get()
        if not url:
            messagebox.showwarning("URL Ausente", "Por favor, insira a URL de um vídeo do YouTube.")
            return

        output_dir = self.output_dir_var.get()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showwarning("Pasta de Saída Inválida", "Por favor, selecione uma pasta de saída válida.")
            return

        try:
            self.log_youtube("🚀 Iniciando download com estratégia automática inteligente...")
            self.log_youtube(f"📺 URL: {url}")
            self.log_youtube("🔧 Usando método híbrido: API + Extrator Personalizado + Fallback")
            
            # Usar sempre o método híbrido mais eficaz
            download_thread = threading.Thread(target=self.run_youtube_api_download, args=(url, output_dir))
            download_thread.start()

        except Exception as e:
            self.log_youtube("Erro ao iniciar o download: {}".format(e))
            messagebox.showerror("Erro de Download", f"Ocorreu um erro ao iniciar o download: {e}")

    def run_youtube_download_with_fallback(self, url, output_dir):
        """
        Executa download com sistema de fallback automático:
        1. Tenta usar dados do PyWebView se disponíveis
        2. Fallback para yt-dlp com estratégias avançadas
        3. Fallback final para yt-dlp básico
        """
        try:
            # Método 1: Verificar se temos dados extraídos pelo navegador
            if hasattr(self, 'browser_extracted_data') and self.browser_extracted_data:
                self.log_youtube("🌐 Método 1: Tentando download com dados do navegador...")
                try:
                    success = self.download_with_browser_data(url, output_dir, self.browser_extracted_data)
                    if success:
                        self.log_youtube("✅ Download concluído com sucesso via navegador!")
                        return
                    else:
                        self.log_youtube("⚠ Falha no download via navegador, tentando fallback...")
                except Exception as e:
                    self.log_youtube(f"❌ Erro no download via navegador: {e}")
                    self.log_youtube("🔄 Prosseguindo para método de fallback...")

            # Método 2: yt-dlp com fallbacks (método original)
            self.log_youtube("🔧 Método 2: Tentando yt-dlp com fallbacks...")
            try:
                self.run_youtube_download(url, output_dir)
                return
            except Exception as e:
                self.log_youtube(f"❌ Falha no método com fallbacks: {e}")
                self.log_youtube("🔄 Tentando método básico como último recurso...")

            # Método 3: yt-dlp básico (último recurso)
            self.log_youtube("🔧 Método 3: Tentando yt-dlp básico (último recurso)...")
            try:
                self.run_youtube_download_basic(url, output_dir)
                return
            except Exception as e:
                self.log_youtube(f"❌ Falha no método básico: {e}")
                raise Exception("Todos os métodos de download falharam")

        except Exception as e:
            self.log_youtube(f"💥 Erro crítico no sistema de fallback: {e}")
            self.show_error_on_main_thread("Erro de Download", f"Todos os métodos de download falharam:\n\n{e}")

    def download_with_browser_data(self, url, output_dir, data):
        """
        Realiza download usando dados extraídos pelo navegador.
        """
        try:
            resolution = self.resolution_var.get()
            formats = self.browser_extractor.extract_formats_from_data(data)
            
            if not formats:
                return False

            # Selecionar formato baseado na resolução escolhida
            selected_format = None
            if resolution == "Original" or not resolution:
                # Pegar o melhor formato disponível
                selected_format = max(formats, key=lambda f: f.get('height', 0))
            else:
                # Procurar formato específico
                target_height = int(resolution[:-1])  # Remove 'p' do final
                for fmt in formats:
                    if fmt.get('height') == target_height:
                        selected_format = fmt
                        break
                
                # Se não encontrou exato, pegar o mais próximo
                if not selected_format:
                    selected_format = min(formats, 
                                        key=lambda f: abs(f.get('height', 0) - target_height))

            if not selected_format or not selected_format.get('url'):
                self.log_youtube("❌ Nenhum formato válido encontrado nos dados do navegador")
                return False

            # Usar yt-dlp para download direto com URL extraída
            ffmpeg_location = self.ffmpeg_installer.get_ffmpeg_command()
            
            ydl_opts = {
                'format': selected_format.get('format_id', 'best'),
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [self.on_yt_dlp_progress],
                'ffmpeg_location': ffmpeg_location,
                'nocheckcertificate': True,
                # Converter para MP4 automaticamente após o download
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.show_info_on_main_thread("Download Concluído", "O vídeo foi baixado com sucesso usando o navegador avançado!")
            return True

        except Exception as e:
            self.log_youtube(f"Erro no download com dados do navegador: {e}")
            return False

    def run_youtube_download_basic(self, url, output_dir):
        """
        Método básico de download sem estratégias avançadas (último recurso).
        Usa códigos específicos do YouTube para forçar resolução exata.
        """
        try:
            resolution = self.resolution_var.get()
            
            # Mapeamento de resoluções para códigos específicos do YouTube
            format_codes = {
                '2160p': '313+140',  # 4K + AAC
                '1440p': '271+140',  # 1440p + AAC  
                '1080p': '137+140',  # 1080p H.264 + AAC
                '720p': '136+140',   # 720p H.264 + AAC
                '480p': '135+140',   # 480p H.264 + AAC
                '360p': '134+140',   # 360p H.264 + AAC
                '240p': '133+140',   # 240p H.264 + AAC
                '144p': '160+140'    # 144p H.264 + AAC
            }
            
            if resolution == "Original" or not resolution:
                format_selector = "313+140/271+140/137+140/best"  # 4K -> 1440p -> 1080p -> melhor
            elif resolution in format_codes:
                # Força código específico + fallbacks inteligentes
                specific_code = format_codes[resolution]
                fallback_codes = []
                
                # Adiciona fallbacks para resoluções menores
                height = int(resolution[:-1])
                for res, code in format_codes.items():
                    res_height = int(res[:-1])
                    if res_height <= height and res != resolution:
                        fallback_codes.append(code)
                
                # Monta string final: específico + fallbacks + genérico
                format_selector = specific_code
                if fallback_codes:
                    format_selector += "/" + "/".join(fallback_codes)
                format_selector += f"/bestvideo[height<={height}]+bestaudio/best"
            else:
                format_selector = f'bestvideo[height<={resolution[:-1]}]+bestaudio/best'
            
            self.log_youtube(f"🎯 Resolução alvo: {resolution}")
            self.log_youtube(f"📋 Código de formato: {format_selector}")

            ffmpeg_location = self.ffmpeg_installer.get_ffmpeg_command()

            # Configuração básica do yt-dlp
            ydl_opts = {
                'format': format_selector,
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [self.on_yt_dlp_progress],
                'ffmpeg_location': ffmpeg_location,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                # Converter para MP4 automaticamente após o download
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }

            self.log_youtube("⚙ Usando configuração básica do yt-dlp...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.show_info_on_main_thread("Download Concluído", "O vídeo foi baixado com sucesso usando o método básico!")

        except Exception as e:
            self.log_youtube(f"Erro no download básico: {e}")
            raise e

    def validate_downloaded_resolution(self, download_info, target_resolution):
        """
        Valida se a resolução baixada corresponde à resolução solicitada.
        
        Args:
            download_info: Informações do download do yt-dlp
            target_resolution: Resolução alvo (ex: '1080p', '720p')
            
        Returns:
            bool: True se a resolução está correta, False caso contrário
        """
        try:
            if not download_info or target_resolution == 'Original':
                return True
            
            # Extrair altura do vídeo baixado
            filename = download_info.get('filename', '')
            if not filename:
                self.log_youtube("⚠ Não foi possível obter informações do arquivo baixado")
                return True  # Assumir sucesso se não conseguir validar
            
            # Tentar extrair resolução do nome do arquivo ou metadados
            height = None
            
            # Verificar se há informações de altura nos metadados
            if 'height' in download_info:
                height = download_info['height']
            elif 'format' in download_info:
                format_info = download_info['format']
                if 'height' in format_info:
                    height = format_info['height']
            
            if height:
                # Mapear altura para resolução
                resolution_map = {
                    2160: '2160p',
                    1440: '1440p', 
                    1080: '1080p',
                    720: '720p',
                    480: '480p',
                    360: '360p',
                    240: '240p',
                    144: '144p'
                }
                
                actual_resolution = resolution_map.get(height, f'{height}p')
                
                self.log_youtube(f"📊 Resolução baixada: {actual_resolution} (altura: {height}px)")
                self.log_youtube(f"🎯 Resolução alvo: {target_resolution}")
                
                # Verificar se a resolução corresponde
                if actual_resolution == target_resolution:
                    self.log_youtube("✅ Resolução validada com sucesso!")
                    return True
                else:
                    self.log_youtube(f"❌ Resolução incorreta! Esperado: {target_resolution}, Obtido: {actual_resolution}")
                    return False
            else:
                self.log_youtube("⚠ Não foi possível determinar a resolução do vídeo baixado")
                return True  # Assumir sucesso se não conseguir validar
                
        except Exception as e:
            self.log_youtube(f"⚠ Erro na validação de resolução: {e}")
            return True  # Assumir sucesso em caso de erro na validação

    def run_youtube_download_test_no_fallbacks(self, url, output_dir):
        """
        MÉTODO DE TESTE: Download sem fallbacks e sem conversão forçada para MP4.
        Para isolar o problema de arquivos MP4 vazios.
        """
        try:
            self.log_youtube("🧪 TESTE: Download sem fallbacks iniciado...")
            
            resolution = self.resolution_var.get()
            if resolution == "Original" or not resolution:
                format_selector = 'best'  # Formato único, melhor disponível
            else:
                # Tentar formato único primeiro, depois separado se necessário
                format_selector = f'best[height<={resolution[:-1]}]'

            ffmpeg_location = self.ffmpeg_installer.get_ffmpeg_command()

            # Configuração MÍNIMA do yt-dlp - SEM postprocessors
            ydl_opts = {
                'format': format_selector,
                'outtmpl': os.path.join(output_dir, '%(title)s_TEST.%(ext)s'),
                'progress_hooks': [self.on_yt_dlp_progress],
                'ffmpeg_location': ffmpeg_location,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                # SEM POSTPROCESSORS - deixar o arquivo no formato original
            }

            self.log_youtube(f"🔧 Formato selecionado: {format_selector}")
            self.log_youtube("⚙ Configuração mínima (sem conversão forçada)")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.log_youtube("✅ TESTE concluído - verificar se arquivo foi criado corretamente")
            self.show_info_on_main_thread("Teste Concluído", "Download de teste realizado sem fallbacks!")

        except Exception as e:
            self.log_youtube(f"❌ Erro no teste: {e}")
            raise e

    def run_youtube_download(self, url, output_dir):
        """
        Método de download anti-bot robusto que usa múltiplas estratégias
        para contornar a detecção de bot do YouTube.
        """
        try:
            resolution = self.resolution_var.get()
            
            # Mapeamento de resoluções para códigos específicos do YouTube
            format_codes = {
                '2160p': '313+140',  # 4K + AAC
                '1440p': '271+140',  # 1440p + AAC  
                '1080p': '137+140',  # 1080p H.264 + AAC
                '720p': '136+140',   # 720p H.264 + AAC
                '480p': '135+140',   # 480p H.264 + AAC
                '360p': '134+140',   # 360p H.264 + AAC
                '240p': '133+140',   # 240p H.264 + AAC
                '144p': '160+140'    # 144p H.264 + AAC
            }
            
            if resolution == "Original" or not resolution:
                format_selector = "313+140/271+140/137+140/best"  # 4K -> 1440p -> 1080p -> melhor
            elif resolution in format_codes:
                # Força código específico + fallbacks inteligentes
                specific_code = format_codes[resolution]
                fallback_codes = []
                
                # Adiciona fallbacks para resoluções menores
                height = int(resolution[:-1])
                for res, code in format_codes.items():
                    res_height = int(res[:-1])
                    if res_height <= height and res != resolution:
                        fallback_codes.append(code)
                
                # Monta string final: específico + fallbacks + genérico
                format_selector = specific_code
                if fallback_codes:
                    format_selector += "/" + "/".join(fallback_codes)
                format_selector += f"/best[height<={height}]/bestvideo[height<={height}]+bestaudio/best"
            else:
                # Fallback para formato genérico
                format_selector = f'best[height<={resolution[:-1]}]/bestvideo[height<={resolution[:-1]}]+bestaudio/best'
            
            self.log_youtube(f"🎯 Resolução alvo: {resolution}")
            self.log_youtube(f"📋 Código de formato: {format_selector}")

            ffmpeg_location = self.ffmpeg_installer.get_ffmpeg_command()

            # Lista de User Agents para rotação
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            ]
            
            import random
            selected_ua = random.choice(user_agents)

            # Configuração base anti-bot
            base_ydl_opts = {
                'format': format_selector,
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [self.on_yt_dlp_progress],
                'ffmpeg_location': ffmpeg_location,
                'nocheckcertificate': True,
                'http_headers': {
                    'User-Agent': selected_ua,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip,deflate',
                    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                    'Keep-Alive': '300',
                    'Connection': 'keep-alive',
                },
                'retries': 3,
                'fragment_retries': 3,
                'sleep_interval': 2,
                'max_sleep_interval': 8,
                'ignoreerrors': False,
                'no_warnings': False,
                # Remover conversão forçada para MP4 para evitar problemas
                # 'postprocessors': [{
                #     'key': 'FFmpegVideoConvertor',
                #     'preferedformat': 'mp4',
                # }],
            }

            # Estratégias anti-bot ordenadas por compatibilidade com códigos específicos
            download_strategies = [
                # Estratégia 1: Web + Firefox cookies (melhor suporte a códigos específicos)
                {
                    'name': 'Web + Firefox',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web'],
                        }
                    },
                    'cookiesfrombrowser': ('firefox',),
                    'supports_specific_formats': True,
                },
                
                # Estratégia 2: Web sem cookies (boa compatibilidade)
                {
                    'name': 'Web sem cookies',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web'],
                        }
                    },
                    'cookiesfrombrowser': None,
                    'supports_specific_formats': True,
                },
                
                # Estratégia 3: TV player + Edge cookies (suporte moderado)
                {
                    'name': 'TV Player + Edge',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['tv'],
                        }
                    },
                    'cookiesfrombrowser': ('edge',),
                    'supports_specific_formats': True,
                },
                
                # Estratégia 4: Fallback básico (sem argumentos específicos)
                {
                    'name': 'Básico',
                    'cookiesfrombrowser': None,
                    'supports_specific_formats': True,
                },
                
                # Estratégia 5: Mobile (mweb) - limitações de formato
                {
                    'name': 'Mobile Web',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['mweb'],
                            'player_skip': ['webpage'],
                        }
                    },
                    'cookiesfrombrowser': None,
                    'supports_specific_formats': False,
                },
                
                # Estratégia 6: Android player (último recurso - limitações de formato)
                {
                    'name': 'Android Player',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android'],
                            'player_skip': ['webpage'],
                        }
                    },
                    'cookiesfrombrowser': None,
                    'supports_specific_formats': False,
                }
            ]
            
            last_error = None
            
            for i, strategy in enumerate(download_strategies):
                try:
                    self.log_youtube(f"🔄 Tentativa {i+1}/6: Testando download com {strategy['name']}...")
                    
                    # Combinar configurações base com estratégia atual
                    ydl_opts = {**base_ydl_opts}
                    
                    # Aplicar configurações da estratégia
                    if 'extractor_args' in strategy:
                        ydl_opts['extractor_args'] = strategy['extractor_args']
                    
                    # Configurar cookies se especificado
                    if strategy.get('cookiesfrombrowser'):
                        browser_name = strategy['cookiesfrombrowser'][0]
                        try:
                            # Verificar se o navegador está disponível
                            can_use_cookies = False
                            if platform.system() == "Windows":
                                if browser_name == "firefox":
                                    firefox_path = os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles")
                                    can_use_cookies = os.path.exists(firefox_path)
                                elif browser_name == "edge":
                                    edge_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")
                                    can_use_cookies = os.path.exists(edge_path)
                            
                            if can_use_cookies:
                                ydl_opts['cookiesfrombrowser'] = strategy['cookiesfrombrowser']
                                self.log_youtube(f"   ✓ Usando cookies do {browser_name}")
                            else:
                                self.log_youtube(f"   ⚠ Cookies do {browser_name} não disponíveis, continuando sem cookies")
                        except Exception as cookie_error:
                            self.log_youtube(f"   ⚠ Erro ao configurar cookies do {browser_name}: {cookie_error}")
                    
                    # Delay entre tentativas para evitar rate limiting
                    if i > 0:
                        delay = random.uniform(1, 3)
                        self.log_youtube(f"   ⏱ Aguardando {delay:.1f}s antes da tentativa...")
                        time.sleep(delay)
                    
                    # Armazenar informações do download para validação
                    download_info = {}
                    
                    def info_hook(d):
                        if d['status'] == 'finished':
                            download_info.update(d)
                    
                    # Adicionar hook para capturar informações do download
                    if 'progress_hooks' not in ydl_opts:
                        ydl_opts['progress_hooks'] = []
                    ydl_opts['progress_hooks'].append(info_hook)
                    
                    # Tentar download
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # Primeiro, extrair informações do vídeo para validação
                        try:
                            video_info = ydl.extract_info(url, download=False)
                            available_formats = len(video_info.get('formats', []))
                            self.log_youtube(f"   📋 Formatos disponíveis: {available_formats}")
                        except Exception as e:
                            self.log_youtube(f"   ⚠ Não foi possível extrair informações do vídeo: {e}")
                        
                        # Fazer o download
                        ydl.download([url])
                    
                    # Validar resolução baixada se a estratégia suporta códigos específicos
                    resolution = self.resolution_var.get()
                    if strategy.get('supports_specific_formats', True) and resolution != 'Original':
                        if self.validate_downloaded_resolution(download_info, resolution):
                            self.log_youtube(f"✅ Download concluído com sucesso usando {strategy['name']} - Resolução validada!")
                            self.show_info_on_main_thread("Download Concluído", f"O vídeo foi baixado com sucesso usando {strategy['name']} na resolução {resolution}!")
                            return
                        else:
                            self.log_youtube(f"⚠ Estratégia {strategy['name']} baixou resolução incorreta, tentando próxima...")
                            # Não fazer return, continuar para próxima estratégia
                            continue
                    else:
                        # Se chegou aqui, sucesso!
                        self.log_youtube(f"✅ Download concluído com sucesso usando {strategy['name']}!")
                        self.show_info_on_main_thread("Download Concluído", f"O vídeo foi baixado com sucesso usando {strategy['name']}!")
                        return
                    
                except yt_dlp.utils.ExtractorError as e:
                    last_error = e
                    error_msg = str(e).lower()
                    if 'sign in' in error_msg or 'login' in error_msg or 'bot' in error_msg:
                        self.log_youtube(f"   ❌ Detecção de bot com {strategy['name']}: {e}")
                        continue
                    else:
                        # Erro diferente de autenticação, tentar próxima estratégia
                        self.log_youtube(f"   ❌ Erro com {strategy['name']}: {e}")
                        continue
                        
                except Exception as e:
                    last_error = e
                    self.log_youtube(f"   ❌ Erro inesperado com {strategy['name']}: {e}")
                    if i == len(download_strategies) - 1:  # Última tentativa
                        break
                    continue
            
            # Se chegou aqui, todas as estratégias falharam
            self.log_youtube("💥 Todas as estratégias anti-bot falharam")
            raise Exception(f"Não foi possível baixar o vídeo. Todas as estratégias falharam. Último erro: {last_error}")

        except yt_dlp.utils.ExtractorError as e:
            error_msg = str(e)
            if 'sign in' in error_msg.lower() or 'login' in error_msg.lower() or 'bot' in error_msg.lower():
                self.log_youtube("Erro de detecção de bot do YouTube: {}".format(e))
                self.show_error_on_main_thread(
                    "Detecção de Bot", 
                    "O YouTube detectou comportamento automatizado. Soluções:\n\n"
                    "1. Faça login no YouTube no seu navegador (Firefox/Edge)\n"
                    "2. Aguarde 10-15 minutos antes de tentar novamente\n"
                    "3. Tente um vídeo público diferente\n"
                    "4. Use uma VPN se disponível\n\n"
                    f"Erro técnico: {e}"
                )
            else:
                self.log_youtube("Erro do extrator: {}".format(e))
                self.show_error_on_main_thread("Erro de Extração", f"Erro ao extrair informações do vídeo: {e}")
        except Exception as e:
            self.log_youtube("Erro durante o download: {}".format(e))
            self.show_error_on_main_thread("Erro de Download", f"Ocorreu um erro durante o download: {e}")

    def on_yt_dlp_progress(self, d):
        """
        Hook para monitorar o progresso do download do yt-dlp.
        """
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                downloaded_bytes = d.get('downloaded_bytes', 0)
                progress = (downloaded_bytes / total_bytes) * 100
                
                def update_download_gui():
                    # Configurar barra de progresso para modo download (vermelha)
                    self.progress_bar.configure(style="Download.Horizontal.TProgressbar")
                    
                    # Atualizar valor da barra de progresso
                    self.progress_var.set(progress)
                    
                    # Atualizar labels com informações de download
                    self.status_var.set(f"Baixando vídeo do YouTube...")
                    self.progress_label_var.set(f"Progresso do Download: {progress:.1f}%")
                    
                    # Atualizar status bar
                    self.update_status_bar(f"Download em progresso: {progress:.1f}%")
                
                self.root.after(0, update_download_gui)

        elif d['status'] == 'finished':
            def finish_download():
                # Resetar barra de progresso para estilo padrão
                self.progress_bar.configure(style="Horizontal.TProgressbar")
                self.progress_var.set(0)
                self.status_var.set("Download concluído!")
                self.progress_label_var.set("Progresso Geral: 0.0%")
                
            self.root.after(0, finish_download)
            
            self.log_youtube("Download finalizado!")
            filename = d.get('filename')
            
            # Verificar se é o arquivo final ou um arquivo intermediário (parte do merge)
            # Arquivos intermediários geralmente têm padrões como .f399.mp4, .f251.webm
            # O arquivo final não tem esses padrões no nome
            if filename and os.path.exists(filename):
                file_basename = os.path.basename(filename)
                
                # Verificar se é arquivo intermediário (contém padrão .f[numero].[extensão] ou é temporário)
                is_intermediate = False
                import re
                
                # Padrão para arquivos intermediários do yt-dlp: .f123.mp4, .f456.webm, etc.
                if re.search(r'\.f\d+\.', file_basename):
                    is_intermediate = True
                    self.log_youtube(f"Arquivo intermediário ignorado: {file_basename}")
                
                # Só adicionar o arquivo final (não intermediário) à lista de conversão
                if not is_intermediate:
                    if self.add_file_to_list(filename):
                        self.log_youtube(f"Arquivo adicionado à lista de conversão: {file_basename}")
                    else:
                        self.log_youtube(f"Arquivo já existe na lista: {file_basename}")

    def update_download_progress(self, progress):
        self.progress_bar["value"] = progress

    def reset_download_progress(self):
        self.progress_bar["value"] = 0

    def show_info_on_main_thread(self, title, message):
        self.root.after(0, lambda: messagebox.showinfo(title, message))

    def show_error_on_main_thread(self, title, message):
        self.root.after(0, lambda: messagebox.showerror(title, message))

    def verify_youtube_url(self):
        """
        Verifica a URL do YouTube e busca as resoluções disponíveis.
        """
        url = self.youtube_url_var.get()
        if not url:
            self.show_error_on_main_thread("URL Inválida", "Por favor, insira uma URL do YouTube.")
            return

        # Executa a verificação em uma thread para não bloquear a UI
        thread = threading.Thread(target=self.run_verify_url_simple, args=(url,))
        thread.start()

    def run_verify_url_simple(self, url):
        """
        Método leve de verificação que evita detecção de bot.
        Mostra resoluções padrão sem fazer múltiplas requisições ao YouTube.
        """
        try:
            self.resolution_combobox.set("Buscando...")
            self.resolution_combobox.config(state="disabled")
            
            self.log_youtube(f"🔍 Verificação leve de URL: {url}")
            
            # Configuração mínima para evitar detecção de bot
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Não extrair formatos detalhados
                'skip_download': True,
                'no_check_certificate': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                },
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Apenas verificar se a URL é válida, sem extrair formatos
                    info = ydl.extract_info(url, download=False)
                    
                    if info:
                        self.log_youtube("✅ URL válida detectada")
                        
                        # Resoluções padrão do YouTube (720p como base conforme solicitado)
                        standard_resolutions = [
                            "1080p", "720p", "480p", "360p", "240p", "144p"
                        ]
                        
                        self.log_youtube(f"📺 Mostrando resoluções padrão (base: 720p): {', '.join(standard_resolutions)}")
                        
                        # Atualizar combobox na thread principal
                        self.resolution_combobox.config(state="normal")
                        self.resolution_combobox['values'] = standard_resolutions
                        self.resolution_combobox.set("720p")  # Define 720p como padrão
                        self.resolution_combobox.config(state="readonly")
                        
                        # Mostrar informações básicas se disponíveis
                        title = info.get('title', 'Título não disponível')
                        if title != 'Título não disponível':
                            self.log_youtube(f"📹 Título: {title}")
                        
                        self.log_youtube("🎯 Verificação leve concluída com sucesso!")
                        return
                        
            except Exception as e:
                self.log_youtube(f"⚠️ Verificação básica falhou: {str(e)}")
                
                # Fallback: mostrar resoluções padrão mesmo sem verificar a URL
                self.log_youtube("🔄 Usando resoluções padrão como fallback")
                standard_resolutions = ["1080p", "720p", "480p", "360p", "240p", "144p"]
                
                self.resolution_combobox.config(state="normal")
                self.resolution_combobox['values'] = standard_resolutions
                self.resolution_combobox.set("720p")  # Define 720p como padrão
                self.resolution_combobox.config(state="readonly")
                
                self.log_youtube("📺 Resoluções padrão carregadas")
                return
            
        except Exception as e:
            self.log_youtube(f"❌ Erro na verificação leve: {str(e)}")
            
            # Último fallback: resoluções básicas
            basic_resolutions = ["720p", "480p", "360p"]
            self.log_youtube(f"🔧 Usando resoluções básicas: {', '.join(basic_resolutions)}")
            
            self.resolution_combobox.config(state="normal")
            self.resolution_combobox['values'] = basic_resolutions
            self.resolution_combobox.set("720p")  # Define 720p como padrão
            self.resolution_combobox.config(state="readonly")

    def run_verify_url_fallback(self, url):
        """
        Método de fallback para verificação de resoluções usando estratégias múltiplas.
        Usado quando o método simplificado falha.
        """
        try:
            self.resolution_combobox.set("Buscando...")
            self.resolution_combobox.config(state="disabled")

            # Lista de User Agents para rotação
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            ]
            
            import random
            selected_ua = random.choice(user_agents)

            # Configuração avançada do yt-dlp para contornar detecção de bot
            base_ydl_opts = {
                'quiet': True,
                'listformats': True,
                'force_generic_extractor': False,
                'nocheckcertificate': True,
                'no_warnings': False,
                
                # Configurações avançadas para contornar verificação de bot do YouTube
                'extractor_args': {
                    'youtube': {
                        'player_client': ['mweb', 'web', 'android'],
                        'player_skip': ['webpage'],
                        'skip': ['hls', 'dash'],
                        'innertube_host': 'studio.youtube.com',
                        'innertube_key': None,
                        'comment_sort': 'top',
                    }
                },
                
                # Headers mais realistas para simular navegador real
                'http_headers': {
                    'User-Agent': selected_ua,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8,en-US;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                },
                
                # Configurações de retry e timeout mais robustas
                'retries': 5,
                'fragment_retries': 5,
                'socket_timeout': 30,
                'sleep_interval': 1,
                'max_sleep_interval': 5,
                
                # Configurações de proxy e rede
                'source_address': None,
                'force_ipv4': False,
                'force_ipv6': False,
            }
            
            # Estratégias de autenticação (sem Chrome para evitar lock do DB)
            cookie_strategies = [
                # Estratégia 1: Android sem cookies (bypass total)
                {
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android'],
                            'player_skip': ['webpage', 'configs', 'hls', 'dash'],
                        }
                    },
                    'format_selector': 'best[height<=1080]/best',
                },
                
                # Estratégia 2: Web client com cookies do Firefox
                {
                    'cookiesfrombrowser': ('firefox', None, None, None),
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web', 'mweb'],
                            'player_skip': ['webpage'],
                        }
                    },
                    'format_selector': 'best[height<=720]/best',
                },
                
                # Estratégia 3: TV client (contorna muitas restrições)
                {
                    'cookiesfrombrowser': ('edge', None, None, None),
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['tv_embedded'],
                            'player_skip': ['webpage', 'configs'],
                        }
                    },
                    'format_selector': 'best[height<=1080]/best',
                },
                
                # Estratégia 4: Web client sem cookies
                {
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web'],
                            'player_skip': ['configs'],
                            'skip': ['hls'],
                        }
                    },
                    'format_selector': 'best[height<=480]/best',
                },
                
                # Estratégia 5: Android com cookies do Firefox
                {
                    'cookiesfrombrowser': ('firefox', None, None, None),
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android'],
                            'player_skip': ['webpage', 'configs'],
                            'skip': ['hls', 'dash'],
                        }
                    },
                    'format_selector': 'best[height<=1080]/best',
                },
                
                # Estratégia 6: Mobile básico (mweb) sem cookies
                {
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['mweb'],
                            'player_skip': ['webpage'],
                        }
                    },
                    'format_selector': 'worst/best',
                }
            ]
            
            last_error = None
            
            for i, strategy in enumerate(cookie_strategies):
                try:
                    self.log_youtube(f"🔄 Tentativa {i+1}/6: Testando estratégia {['Android puro', 'Web+Firefox', 'TV+Edge', 'Web sem cookies', 'Android+Firefox', 'Mobile básico'][i]}...")
                    
                    # Combinar configurações base com estratégia atual
                    ydl_opts = {**base_ydl_opts, **strategy}
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        formats = info.get('formats', [])
                    
                    # Se chegou aqui, sucesso
                    self.log_youtube(f"✓ Sucesso com estratégia {i+1}: {len(formats)} formatos encontrados")
                    break
                    
                except yt_dlp.utils.ExtractorError as e:
                    last_error = e
                    error_msg = str(e).lower()
                    
                    if 'sign in' in error_msg or 'login' in error_msg or 'bot' in error_msg:
                        self.log_youtube(f"✗ Estratégia {i+1} falhou: Detecção de bot/login")
                        if i == len(cookie_strategies) - 1:  # Última tentativa
                            self.log_youtube("⚠ Todas as estratégias falharam - problema de autenticação")
                            raise e
                        continue
                    elif 'nsig' in error_msg:
                        self.log_youtube(f"✗ Estratégia {i+1} falhou: Problema de assinatura (nsig)")
                        if i == len(cookie_strategies) - 1:
                            self.log_youtube("⚠ Todas as estratégias falharam - problema de nsig")
                            raise e
                        continue
                    elif 'only images' in error_msg:
                        self.log_youtube(f"✗ Estratégia {i+1} falhou: Apenas imagens disponíveis")
                        if i == len(cookie_strategies) - 1:
                            self.log_youtube("⚠ Todas as estratégias falharam - apenas imagens")
                            raise e
                        continue
                    else:
                        self.log_youtube(f"✗ Estratégia {i+1} falhou: {str(e)[:100]}...")
                        if i == len(cookie_strategies) - 1:
                            raise e
                        continue
                        
                except Exception as e:
                    last_error = e
                    self.log_youtube(f"✗ Estratégia {i+1} falhou: Erro inesperado - {str(e)[:100]}...")
                    if i == len(cookie_strategies) - 1:  # Última tentativa
                        self.log_youtube("⚠ Todas as estratégias falharam - erro inesperado")
                        raise e
                    continue
            
            # Se chegou aqui sem break, todas as estratégias falharam
            if 'formats' not in locals():
                if last_error:
                    raise last_error
                else:
                    raise Exception("Todas as estratégias de autenticação falharam")

            resolutions = sorted(
                list(set(
                    f"{f['height']}p" 
                    for f in formats 
                    if f.get('height') and f.get('vcodec') != 'none'
                )),
                key=lambda r: int(r[:-1]), reverse=True
            )

            if not resolutions:
                self.show_error_on_main_thread("Nenhuma Resolução", "Nenhuma resolução de vídeo válida encontrada.")
                self.resolution_combobox.set("")
                return

            self.resolution_combobox['values'] = resolutions
            self.resolution_combobox.config(state="readonly")
            self.resolution_combobox.set(resolutions[0])

        except yt_dlp.utils.ExtractorError as e:
            error_msg = str(e)
            if 'sign in' in error_msg.lower() or 'login' in error_msg.lower():
                self.show_error_on_main_thread(
                    "Erro de Autenticação", 
                    "O YouTube está solicitando login para verificar este vídeo.\n\n"
                    "Tente fazer login no YouTube no seu navegador e tente novamente."
                )
            else:
                self.show_error_on_main_thread("Erro na Verificação", f"Não foi possível obter as resoluções: {e}")
            self.resolution_combobox.set("")
        except Exception as e:
            self.show_error_on_main_thread("Erro na Verificação", f"Não foi possível obter as resoluções: {e}")
            self.resolution_combobox.set("")

    def open_browser_extractor(self):
        """
        Abre o extrator de navegador avançado para contornar detecção de bot do YouTube.
        """
        if not WEBVIEW_AVAILABLE:
            self.show_error_on_main_thread(
                "PyWebView Não Disponível", 
                "O PyWebView não está instalado. Para usar o navegador avançado, instale com:\n\n"
                "pip install pywebview"
            )
            return

        url = self.youtube_url_var.get()
        if not url:
            self.show_error_on_main_thread("URL Ausente", "Por favor, insira a URL de um vídeo do YouTube.")
            return

        self.log_youtube("🌐 Iniciando extração via navegador avançado...")
        self.log_youtube(f"📺 URL: {url}")

        # Executar extração em thread separada para não bloquear a UI
        thread = threading.Thread(target=self.run_browser_extraction, args=(url,))
        thread.start()

    def run_browser_extraction(self, url):
        """
        Executa a extração usando o navegador integrado.
        """
        try:
            self.log_youtube("🔄 Carregando navegador integrado...")
            
            # Usar o extrator de navegador
            data = self.browser_extractor.extract_youtube_data(url)
            
            if data and 'formats' in data:
                self.log_youtube("✅ Dados extraídos com sucesso via navegador!")
                
                # Converter dados para formato compatível
                formats = self.browser_extractor.extract_formats_from_data(data)
                
                if formats:
                    # Extrair resoluções únicas
                    resolutions = sorted(
                        list(set(
                            f"{f['height']}p" 
                            for f in formats 
                            if f.get('height') and f.get('vcodec') != 'none'
                        )),
                        key=lambda r: int(r[:-1]), reverse=True
                    )
                    
                    if resolutions:
                        def update_ui():
                            self.resolution_combobox['values'] = resolutions
                            self.resolution_combobox.config(state="readonly")
                            self.resolution_combobox.set(resolutions[0])
                            self.log_youtube(f"📋 Resoluções encontradas: {', '.join(resolutions)}")
                        
                        self.root.after(0, update_ui)
                        
                        # Armazenar dados extraídos para uso no download
                        self.browser_extracted_data = data
                        self.log_youtube("💾 Dados armazenados para download futuro")
                    else:
                        self.log_youtube("⚠ Nenhuma resolução de vídeo válida encontrada")
                        self.show_error_on_main_thread("Nenhuma Resolução", "Nenhuma resolução de vídeo válida encontrada.")
                else:
                    self.log_youtube("⚠ Nenhum formato extraído dos dados")
                    self.show_error_on_main_thread("Erro de Extração", "Não foi possível extrair formatos dos dados obtidos.")
            else:
                self.log_youtube("❌ Falha na extração via navegador")
                self.show_error_on_main_thread(
                    "Falha na Extração", 
                    "Não foi possível extrair dados via navegador.\n\n"
                    "Tente usar o método de verificação padrão."
                )
                
        except Exception as e:
            self.log_youtube(f"❌ Erro durante extração via navegador: {e}")
            self.show_error_on_main_thread(
                "Erro do Navegador", 
                f"Erro durante a extração via navegador:\n\n{e}\n\n"
                "Tente usar o método de verificação padrão."
            )

    def create_settings_section(self, parent, row):
        """
        Cria a seção de configurações de conversão
        """
        # Frame de configurações
        settings_frame = ttk.LabelFrame(
            parent, text="Configurações de Conversão", padding="10"
        )
        settings_frame.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)
        settings_frame.columnconfigure(5, weight=1)

        # Formato
        ttk.Label(settings_frame, text="Formato:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.format_var = tk.StringVar(value="MP4")
        self.format_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.format_var,
            values=SUPPORTED_OUTPUT_FORMATS,
            state="readonly",
        )
        self.format_combo.grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2
        )
        self.format_combo.bind("<<ComboboxSelected>>", self.on_format_changed)

        # Qualidade
        ttk.Label(settings_frame, text="Qualidade:").grid(
            row=0, column=2, sticky=tk.W, pady=2
        )
        self.quality_var = tk.StringVar(value="Média")
        self.quality_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.quality_var,
            values=["Baixa", "Média", "Alta", "Muito Alta"],
            state="readonly",
        )
        self.quality_combo.grid(
            row=0, column=3, sticky=(tk.W, tk.E), padx=(5, 0), pady=2
        )

        # Codec de Vídeo
        ttk.Label(settings_frame, text="Codec de Vídeo:").grid(
            row=0, column=4, sticky=tk.W, pady=2, padx=(10, 0)
        )
        self.codec_var = tk.StringVar(value="H.264 (Recomendado)")
        self.codec_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.codec_var,
            values=["H.264 (Recomendado)", "H.265 (HEVC)"],
            state="readonly",
        )
        self.codec_combo.grid(row=0, column=5, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        self.codec_combo.bind("<<ComboboxSelected>>", self.on_codec_changed)

        # FPS
        ttk.Label(settings_frame, text="FPS:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.fps_var = tk.StringVar(value="Original")
        self.fps_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.fps_var,
            values=FPS_OPTIONS,
            state="readonly",
        )
        self.fps_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2)
        self.fps_combo.bind("<<ComboboxSelected>>", self.on_fps_changed)

        # FPS personalizado
        self.fps_custom_var = tk.IntVar(value=30)
        self.fps_custom_spin = ttk.Spinbox(
            settings_frame,
            from_=1,
            to=120,
            textvariable=self.fps_custom_var,
            width=10,
            state="disabled",
        )
        self.fps_custom_spin.grid(row=1, column=2, sticky=tk.W, padx=(5, 10), pady=2)

        # Resolução
        ttk.Label(settings_frame, text="Resolução:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.resolution_var = tk.StringVar(value="Original")
        self.resolution_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.resolution_var,
            values=list(RESOLUTION_PRESETS.keys()),
            state="readonly",
        )
        self.resolution_combo.grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2
        )
        self.resolution_combo.bind("<<ComboboxSelected>>", self.on_resolution_changed)

        # Resolução personalizada
        custom_frame = ttk.Frame(settings_frame)
        custom_frame.grid(
            row=2, column=2, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0), pady=2
        )

        self.width_var = tk.IntVar(value=1920)
        self.height_var = tk.IntVar(value=1080)

        ttk.Label(custom_frame, text="Largura:").grid(row=0, column=0, sticky=tk.W)
        self.width_spin = ttk.Spinbox(
            custom_frame,
            from_=64,
            to=7680,
            textvariable=self.width_var,
            width=8,
            state="disabled",
        )
        self.width_spin.grid(row=0, column=1, padx=(5, 10))

        ttk.Label(custom_frame, text="Altura:").grid(row=0, column=2, sticky=tk.W)
        self.height_spin = ttk.Spinbox(
            custom_frame,
            from_=64,
            to=4320,
            textvariable=self.height_var,
            width=8,
            state="disabled",
        )
        self.height_spin.grid(row=0, column=3, padx=(5, 0))

        # Transparência
        self.transparency_var = tk.BooleanVar()
        self.transparency_check = ttk.Checkbutton(
            settings_frame,
            text="Preservar Transparência",
            variable=self.transparency_var,
            state="disabled",
        )
        self.transparency_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Seções específicas para GIF, Extração de Frames e Extração de Áudio
        self.create_gif_settings_section(settings_frame)
        self.create_frame_extraction_section(settings_frame)
        self.create_audio_extraction_section(settings_frame)

        # Prioridade de Performance
        priority_frame = ttk.LabelFrame(
            settings_frame, text="Prioridade de Processamento", padding="5"
        )
        priority_frame.grid(
            row=7, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 5)
        )
        priority_frame.columnconfigure(1, weight=1)

        # Variável para o slider de prioridade
        self.performance_mode_var = tk.IntVar(value=1)  # Default: Automática

        # Labels dos modos
        mode_labels = get_performance_mode_labels()

        # Label esquerda (Econômica)
        ttk.Label(priority_frame, text=mode_labels[0], font=("TkDefaultFont", 9)).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )

        # Slider
        self.performance_slider = ttk.Scale(
            priority_frame,
            from_=0,
            to=2,
            variable=self.performance_mode_var,
            orient=tk.HORIZONTAL,
            length=200,
        )
        self.performance_slider.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.performance_slider.bind(
            "<ButtonRelease-1>", self.on_performance_mode_changed
        )
        self.performance_slider.bind("<B1-Motion>", self.on_performance_mode_changed)

        # Label direita (Performance)
        ttk.Label(priority_frame, text=mode_labels[2], font=("TkDefaultFont", 9)).grid(
            row=0, column=2, sticky=tk.E, padx=(5, 0)
        )

        # Label central mostrando modo atual
        self.current_mode_label = ttk.Label(
            priority_frame, text=mode_labels[1], font=("TkDefaultFont", 9, "bold")
        )
        self.current_mode_label.grid(row=1, column=0, columnspan=3, pady=(5, 0))

        # Tooltips serão configurados após criação de todos os widgets

    def create_gif_settings_section(self, parent):
        """
        Cria a seção de configurações específicas para GIF animado
        """
        # Frame para configurações de GIF (inicialmente oculto)
        self.gif_frame = ttk.LabelFrame(
            parent, text="Configurações de GIF Animado", padding="5"
        )
        self.gif_frame.grid(row=4, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=5)
        self.gif_frame.columnconfigure(1, weight=1)
        self.gif_frame.columnconfigure(3, weight=1)
        self.gif_frame.columnconfigure(5, weight=1)
        self.gif_frame.grid_remove()  # Ocultar inicialmente

        # Qualidade do GIF
        ttk.Label(self.gif_frame, text="Qualidade GIF:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.gif_quality_var = tk.StringVar(value="Média")
        self.gif_quality_combo = ttk.Combobox(
            self.gif_frame,
            textvariable=self.gif_quality_var,
            values=list(GIF_QUALITY_PRESETS.keys()),
            state="readonly",
        )
        self.gif_quality_combo.grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2
        )

        # FPS do GIF
        ttk.Label(self.gif_frame, text="FPS GIF:").grid(
            row=0, column=2, sticky=tk.W, pady=2
        )
        self.gif_fps_var = tk.StringVar(value="15")
        self.gif_fps_combo = ttk.Combobox(
            self.gif_frame,
            textvariable=self.gif_fps_var,
            values=GIF_FPS_OPTIONS,
            state="readonly",
        )
        self.gif_fps_combo.grid(
            row=0, column=3, sticky=(tk.W, tk.E), padx=(5, 10), pady=2
        )

        # Cores do GIF
        ttk.Label(self.gif_frame, text="Cores:").grid(
            row=0, column=4, sticky=tk.W, pady=2
        )
        self.gif_colors_var = tk.StringVar(value="256")
        self.gif_colors_combo = ttk.Combobox(
            self.gif_frame,
            textvariable=self.gif_colors_var,
            values=GIF_COLOR_OPTIONS,
            state="readonly",
        )
        self.gif_colors_combo.grid(
            row=0, column=5, sticky=(tk.W, tk.E), padx=(5, 0), pady=2
        )

        # Resolução máxima do GIF
        ttk.Label(self.gif_frame, text="Resolução Máx:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.gif_resolution_var = tk.StringVar(value="720p")
        self.gif_resolution_combo = ttk.Combobox(
            self.gif_frame,
            textvariable=self.gif_resolution_var,
            values=list(GIF_RESOLUTION_PRESETS.keys()),
            state="readonly",
        )
        self.gif_resolution_combo.grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2
        )

        # Opções avançadas de GIF
        self.gif_dithering_var = tk.BooleanVar(value=True)
        self.gif_dithering_check = ttk.Checkbutton(
            self.gif_frame, text="Dithering", variable=self.gif_dithering_var
        )
        self.gif_dithering_check.grid(row=1, column=2, sticky=tk.W, pady=2)

        self.gif_optimize_var = tk.BooleanVar(value=True)
        self.gif_optimize_check = ttk.Checkbutton(
            self.gif_frame, text="Otimizar", variable=self.gif_optimize_var
        )
        self.gif_optimize_check.grid(row=1, column=3, sticky=tk.W, pady=2)

    def create_frame_extraction_section(self, parent):
        """
        Cria a seção de configurações para extração de frames
        """
        # Frame para extração de frames (inicialmente oculto)
        self.frame_extraction_frame = ttk.LabelFrame(
            parent, text="Configurações de Extração de Frames", padding="5"
        )
        self.frame_extraction_frame.grid(
            row=5, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=5
        )
        self.frame_extraction_frame.columnconfigure(1, weight=1)
        self.frame_extraction_frame.columnconfigure(3, weight=1)
        self.frame_extraction_frame.columnconfigure(5, weight=1)
        self.frame_extraction_frame.grid_remove()  # Ocultar inicialmente

        # Formato da imagem
        ttk.Label(self.frame_extraction_frame, text="Formato:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.frame_format_var = tk.StringVar(value="PNG")
        self.frame_format_combo = ttk.Combobox(
            self.frame_extraction_frame,
            textvariable=self.frame_format_var,
            values=list(FRAME_EXTRACTION_FORMATS.keys()),
            state="readonly",
        )
        self.frame_format_combo.grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2
        )
        self.frame_format_combo.bind(
            "<<ComboboxSelected>>", self.on_frame_format_changed
        )

        # Modo de extração
        ttk.Label(self.frame_extraction_frame, text="Modo:").grid(
            row=0, column=2, sticky=tk.W, pady=2
        )
        self.frame_mode_var = tk.StringVar(value="Todos os Frames")
        self.frame_mode_combo = ttk.Combobox(
            self.frame_extraction_frame,
            textvariable=self.frame_mode_var,
            values=list(FRAME_EXTRACTION_MODES.keys()),
            state="readonly",
        )
        self.frame_mode_combo.grid(
            row=0, column=3, sticky=(tk.W, tk.E), padx=(5, 10), pady=2
        )
        self.frame_mode_combo.bind("<<ComboboxSelected>>", self.on_frame_mode_changed)

        # Qualidade (para formatos com compressão)
        ttk.Label(self.frame_extraction_frame, text="Qualidade:").grid(
            row=0, column=4, sticky=tk.W, pady=2
        )
        self.frame_quality_var = tk.IntVar(value=95)
        self.frame_quality_spin = ttk.Spinbox(
            self.frame_extraction_frame,
            from_=1,
            to=100,
            textvariable=self.frame_quality_var,
            width=8,
        )
        self.frame_quality_spin.grid(
            row=0, column=5, sticky=(tk.W, tk.E), padx=(5, 0), pady=2
        )

        # Configurações específicas do modo
        self.frame_config_frame = ttk.Frame(self.frame_extraction_frame)
        self.frame_config_frame.grid(
            row=1, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=5
        )
        self.frame_config_frame.columnconfigure(1, weight=1)
        self.frame_config_frame.columnconfigure(3, weight=1)

        # Intervalo (para modo intervalo)
        self.interval_label = ttk.Label(
            self.frame_config_frame, text="Intervalo (seg):"
        )
        self.frame_interval_var = tk.DoubleVar(value=1.0)
        self.frame_interval_spin = ttk.Spinbox(
            self.frame_config_frame,
            from_=0.1,
            to=60.0,
            textvariable=self.frame_interval_var,
            width=8,
            increment=0.1,
        )

        # Frames específicos (para modo específico)
        self.specific_label = ttk.Label(
            self.frame_config_frame, text="Frames (ex: 1,5,10-20):"
        )
        self.frame_specific_var = tk.StringVar()
        self.frame_specific_entry = ttk.Entry(
            self.frame_config_frame, textvariable=self.frame_specific_var
        )

        # Organização automática
        self.frame_auto_folder_var = tk.BooleanVar(value=True)
        self.frame_auto_folder_check = ttk.Checkbutton(
            self.frame_extraction_frame,
            text="Criar pasta automática com nome do vídeo",
            variable=self.frame_auto_folder_var,
        )
        self.frame_auto_folder_check.grid(
            row=2, column=0, columnspan=6, sticky=tk.W, pady=5
        )

        # Configurar visibilidade inicial
        self.update_frame_mode_visibility()

    def create_audio_extraction_section(self, parent):
        """
        Cria a seção de configurações de extração de áudio
        """
        # Frame principal para extração de áudio
        self.audio_extraction_frame = ttk.LabelFrame(
            parent, text="Configurações de Extração de Áudio", padding="10"
        )
        self.audio_extraction_frame.grid(
            row=3, column=0, columnspan=6, sticky=tk.EW, pady=5
        )

        # Checkbox para habilitar extração de áudio
        self.audio_extraction_var = tk.BooleanVar(value=False)
        self.audio_extraction_check = ttk.Checkbutton(
            self.audio_extraction_frame,
            text="Extrair apenas áudio do vídeo",
            variable=self.audio_extraction_var,
            command=self.on_audio_extraction_changed,
        )
        self.audio_extraction_check.grid(
            row=0, column=0, columnspan=6, sticky=tk.W, pady=5
        )

        # Formato de áudio
        ttk.Label(self.audio_extraction_frame, text="Formato de Áudio:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5)
        )
        self.audio_format_var = tk.StringVar(value=AUDIO_EXTRACTION_DEFAULTS["format"])
        self.audio_format_combo = ttk.Combobox(
            self.audio_extraction_frame,
            textvariable=self.audio_format_var,
            values=list(SUPPORTED_AUDIO_FORMATS),
            state="readonly",
            width=15,
        )
        self.audio_format_combo.grid(row=1, column=1, sticky=tk.W, padx=(0, 10))
        self.audio_format_combo.bind("<<ComboboxSelected>>", self.on_audio_format_changed)

        # Qualidade de áudio
        ttk.Label(self.audio_extraction_frame, text="Qualidade:").grid(
            row=1, column=2, sticky=tk.W, padx=(0, 5)
        )
        self.audio_quality_var = tk.StringVar(value=AUDIO_EXTRACTION_DEFAULTS["quality"])
        self.audio_quality_combo = ttk.Combobox(
            self.audio_extraction_frame,
            textvariable=self.audio_quality_var,
            state="readonly",
            width=15,
        )
        self.audio_quality_combo.grid(row=1, column=3, sticky=tk.W, padx=(0, 10))

        # Preservar metadados
        self.audio_metadata_var = tk.BooleanVar(value=AUDIO_EXTRACTION_DEFAULTS["preserve_metadata"])
        self.audio_metadata_check = ttk.Checkbutton(
            self.audio_extraction_frame,
            text="Preservar metadados",
            variable=self.audio_metadata_var,
        )
        self.audio_metadata_check.grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        # Configurar visibilidade inicial
        self.update_audio_extraction_visibility()

    def create_progress_section(self, parent, row):
        """
        Cria a seção de progresso
        """
        # Frame de progresso
        progress_frame = ttk.LabelFrame(parent, text="Progresso", padding="10")
        progress_frame.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        progress_frame.columnconfigure(0, weight=1)

        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, length=400
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)

        # Label de status
        self.status_var = tk.StringVar(value="Pronto para conversão")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, pady=2)

        # Label de progresso geral
        self.progress_label_var = tk.StringVar(value="Progresso Geral: 0.0%")
        self.progress_label = ttk.Label(
            progress_frame, textvariable=self.progress_label_var
        )
        self.progress_label.grid(row=2, column=0, pady=2)

    def create_actions_section(self, parent, row):
        """
        Cria a seção de ações (vazia - botões movidos para seção de arquivos)
        """
        pass

    def create_logs_tab_content(self, parent):
        """
        Cria o conteúdo da aba de Logs
        """
        # Configurar grid do parent
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Criar seção de logs de conversão
        self.create_conversion_log_section(parent, 0)

        # Criar seção de logs de download do YouTube
        self.create_youtube_log_section(parent, 1)

    def create_conversion_log_section(self, parent, row):
        """
        Cria a seção de logs de conversão
        """
        # Frame principal para a seção de logs de conversão
        log_main_frame = ttk.LabelFrame(parent, text="Log de Conversão", padding="5")
        log_main_frame.grid(
            row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5)
        )
        log_main_frame.columnconfigure(0, weight=1)
        log_main_frame.rowconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)

        # Frame superior com título e botões
        header_frame = ttk.Frame(log_main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        header_frame.columnconfigure(0, weight=1)

        # Botão de limpar logs de conversão
        self.clear_log_btn = ttk.Button(
            header_frame, text="🗑️Limpar", command=self.clear_conversion_logs, width=12
        )
        self.clear_log_btn.grid(row=0, column=1, sticky=tk.E, padx=(0, 5))

        # Botão de salvar log com ícone de disquete
        self.save_log_btn = ttk.Button(
            header_frame, text="💾 Salvar Log", command=self.save_log_manually, width=12
        )
        self.save_log_btn.grid(row=0, column=2, sticky=tk.E)

        # Área de texto para logs com scroll
        self.log_text = scrolledtext.ScrolledText(
            log_main_frame, height=8, width=80, wrap=tk.WORD, state=tk.NORMAL
        )
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Inicializar sistema de logs
        self.log_buffer = []  # Buffer para armazenar logs
        self.create_logs_directory()

    def create_youtube_log_section(self, parent, row):
        """
        Cria a seção de logs de download do YouTube
        """
        # Frame principal para a seção de logs do YouTube
        youtube_log_frame = ttk.LabelFrame(parent, text="Log de Download do YouTube", padding="5")
        youtube_log_frame.grid(
            row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0)
        )
        youtube_log_frame.columnconfigure(0, weight=1)
        youtube_log_frame.rowconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)

        # Frame superior com botões
        youtube_header_frame = ttk.Frame(youtube_log_frame)
        youtube_header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        youtube_header_frame.columnconfigure(0, weight=1)

        # Botão de limpar logs do YouTube
        self.clear_youtube_log_btn = tk.Button(
            youtube_header_frame, text="🗑️Limpar", command=self.clear_youtube_logs, width=12
        )
        self.clear_youtube_log_btn.grid(row=0, column=1, sticky=tk.E, padx=(0, 3))

        # Botão de salvar log do YouTube
        self.save_youtube_log_btn = ttk.Button(
            youtube_header_frame, text="💾 Salvar Log", command=self.save_youtube_log_manually, width=18
        )
        self.save_youtube_log_btn.grid(row=0, column=2, sticky=tk.E)

        # Área de texto para logs do YouTube com scroll
        self.youtube_log_text = scrolledtext.ScrolledText(
            youtube_log_frame, height=8, width=80, wrap=tk.WORD, state=tk.NORMAL
        )
        self.youtube_log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Inicializar buffer para logs do YouTube
        self.youtube_log_buffer = []

    def create_log_section(self, parent, row):
        """
        Cria a seção de logs com splitter redimensionável e botão de salvar
        """
        # Frame principal para a seção de logs
        log_main_frame = ttk.LabelFrame(parent, text="Log de Conversão", padding="5")
        log_main_frame.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )
        log_main_frame.columnconfigure(0, weight=1)
        log_main_frame.rowconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)

        # Frame superior com título e botão de salvar
        header_frame = ttk.Frame(log_main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        header_frame.columnconfigure(0, weight=1)

        # Botão de salvar log com ícone de disquete
        self.save_log_btn = ttk.Button(
            header_frame, text="💾 Salvar Log", command=self.save_log_manually, width=12
        )
        self.save_log_btn.grid(row=0, column=1, sticky=tk.E)

        # PanedWindow para criar splitter redimensionável
        self.log_paned = ttk.PanedWindow(log_main_frame, orient=tk.VERTICAL)
        self.log_paned.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Frame para a área de texto do log
        log_text_frame = ttk.Frame(self.log_paned)
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)

        # Área de texto para logs com scroll
        self.log_text = scrolledtext.ScrolledText(
            log_text_frame, height=8, width=80, wrap=tk.WORD, state=tk.NORMAL
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Adicionar o frame ao PanedWindow
        self.log_paned.add(log_text_frame, weight=1)

        # Inicializar sistema de logs
        self.log_buffer = []  # Buffer para armazenar logs
        self.create_logs_directory()

    def create_status_bar(self):
        """
        Cria a barra de status
        """
        self.status_bar = ttk.Label(
            self.root, text="Pronto para Conversão", relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))

    def create_logs_directory(self):
        """
        Cria o diretório de logs se não existir
        """
        logs_dir = Path("logs")
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)

    def save_log_manually(self):
        """
        Salva o log atual manualmente quando o usuário clica no botão
        """
        try:
            if hasattr(self, "log_text") and self.log_text:
                log_content = self.log_text.get("1.0", tk.END)
                if log_content.strip():
                    filename = self._generate_log_filename("manual")
                    self._save_log_to_file(log_content, filename)
                    messagebox.showinfo("Sucesso", f"Log salvo em: {filename}")
                else:
                    messagebox.showwarning(
                        "Aviso", "Não há conteúdo no log para salvar."
                    )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar log: {str(e)}")

    def save_youtube_log_manually(self):
        """
        Salva o log do YouTube atual manualmente quando o usuário clica no botão
        """
        try:
            if hasattr(self, "youtube_log_text") and self.youtube_log_text:
                log_content = self.youtube_log_text.get("1.0", tk.END)
                if log_content.strip():
                    filename = self._generate_youtube_log_filename("manual")
                    self._save_log_to_file(log_content, filename)
                    messagebox.showinfo("Sucesso", f"Log do YouTube salvo em: {filename}")
                else:
                    messagebox.showwarning(
                        "Aviso", "Não há conteúdo no log do YouTube para salvar."
                    )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar log do YouTube: {str(e)}")

    def _generate_log_filename(self, log_type="auto"):
        """
        Gera nome do arquivo de log com timestamp
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"logs/conversion_log_{log_type}_{timestamp}.log"

    def _generate_youtube_log_filename(self, log_type="auto"):
        """
        Gera nome do arquivo de log do YouTube com timestamp
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"logs/youtube_log_{log_type}_{timestamp}.log"

    def _save_log_to_file(self, content, filename):
        """
        Salva o conteúdo do log em arquivo
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Erro ao escrever arquivo: {str(e)}")

    def update_status_bar(self, message):
        """
        Atualiza a mensagem da barra de status de forma thread-safe
        """

        def update_gui():
            self.status_bar.config(text=message)

        # Executar na thread principal da GUI
        self.root.after(0, update_gui)

    def add_file_to_list(self, filepath):
        """
        Adiciona um arquivo à lista de conversão de forma programática
        """
        from utils.validators import validate_input_file
        
        # Validar o arquivo antes de adicionar
        is_valid, error_message = validate_input_file(filepath)
        if not is_valid:
            def show_error():
                self.log_message(f"Erro ao adicionar arquivo: {error_message}")
            self.root.after(0, show_error)
            return False
            
        # Verificar se o arquivo já está na lista
        if filepath not in [f["path"] for f in self.selected_files]:
            file_info = {
                "path": filepath,
                "name": os.path.basename(filepath),
                "status": "Pendente",
                "progress": "0%",
                "gpu": "-",
                "job_id": None,
            }
            self.selected_files.append(file_info)
            
            # Atualizar interface na thread principal
            def update_gui():
                self.update_files_tree()
                self.log_message(f"Arquivo adicionado à lista: {os.path.basename(filepath)}")
            
            self.root.after(0, update_gui)
            return True
        else:
            def show_duplicate():
                self.log_message(f"Arquivo já existe na lista: {os.path.basename(filepath)}")
            self.root.after(0, show_duplicate)
            return False

    def browse_input_files(self):
        """
        Abre diálogo para selecionar múltiplos arquivos de entrada
        """
        filetypes = [
            ("Arquivos de Vídeo", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
            ("Todos os Arquivos", "*.*"),
        ]

        filenames = filedialog.askopenfilenames(
            title="Selecionar Arquivos de Vídeo", filetypes=filetypes
        )

        if filenames:
            for filename in filenames:
                if filename not in [f["path"] for f in self.selected_files]:
                    file_info = {
                        "path": filename,
                        "name": os.path.basename(filename),
                        "status": "Pendente",
                        "progress": "0%",
                        "gpu": "-",
                        "job_id": None,
                    }
                    self.selected_files.append(file_info)

            self.update_files_tree()
            self.log_message(f"{len(filenames)} arquivo(s) adicionado(s) à lista")

    def remove_selected_files(self):
        """
        Remove arquivos selecionados da lista
        """
        selected_items = self.files_tree.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Selecione arquivos para remover")
            return

        # Remover da lista interna
        for item in selected_items:
            item_values = self.files_tree.item(item, "values")
            if item_values:
                file_path = item_values[0]  # Primeira coluna é o nome do arquivo
                # Encontrar e remover da lista
                self.selected_files = [
                    f for f in self.selected_files if f["name"] != file_path
                ]

        self.update_files_tree()
        self.log_message(f"{len(selected_items)} arquivo(s) removido(s) da lista")

    def clear_file_list(self):
        """
        Limpa toda a lista de arquivos
        """
        if self.selected_files:
            self.selected_files.clear()
            self.update_files_tree()
            self.log_message("Lista de arquivos limpa")

    def update_files_tree(self):
        """
        Atualiza a visualização da árvore de arquivos
        """
        # Limpar árvore
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        # Adicionar arquivos
        for file_info in self.selected_files:
            self.files_tree.insert(
                "",
                "end",
                values=(
                    file_info["name"],
                    file_info["status"],
                    file_info["progress"],
                    file_info["gpu"],
                ),
            )

    def browse_output_dir(self):
        """
        Abre diálogo para selecionar pasta de saída
        """
        dirname = filedialog.askdirectory(title="Selecionar Pasta de Saída")

        if dirname:
            self.output_dir_var.set(dirname)
            self.log_message(f"Pasta de saída: {dirname}")

    def on_fps_changed(self, event=None):
        """
        Callback para mudança de FPS
        """
        if self.fps_var.get() == "Personalizado":
            self.fps_custom_spin.config(state="normal")
        else:
            self.fps_custom_spin.config(state="disabled")

    def on_resolution_changed(self, event=None):
        """
        Callback para mudança de resolução
        """
        if self.resolution_var.get() == "Personalizada":
            self.width_spin.config(state="normal")
            self.height_spin.config(state="normal")
        else:
            self.width_spin.config(state="disabled")
            self.height_spin.config(state="disabled")

    def on_format_changed(self, event=None):
        """
        Callback para mudança de formato - controla opções específicas do WebP, GIF e Extração de Frames
        """
        format_selected = self.format_var.get()

        # Habilitar/desabilitar transparência baseado no formato
        if (
            "WEBP" in format_selected
            or "WebM" in format_selected
            or "MOV" in format_selected
        ):
            self.transparency_check.config(state="normal")
        else:
            self.transparency_check.config(state="disabled")
            self.transparency_var.set(False)

        # Mostrar/ocultar seções específicas baseado no formato
        if "GIF (Animado)" in format_selected:
            self.gif_frame.grid()
            self.frame_extraction_frame.grid_remove()
            self.log_message(
                "GIF Animado selecionado: Configurações avançadas disponíveis"
            )
        elif "Extração de Frames" in format_selected:
            self.frame_extraction_frame.grid()
            self.gif_frame.grid_remove()
            self.log_message(
                "Extração de Frames selecionada: Múltiplos formatos disponíveis"
            )
        else:
            self.gif_frame.grid_remove()
            self.frame_extraction_frame.grid_remove()

            # Mostrar dica específica para WebP
            if "WEBP" in format_selected:
                self.log_message(
                    "WebP selecionado: Suporte a animação e transparência disponível"
                )

        # Validar compatibilidade de codec
        self._validate_codec_compatibility()

    def on_frame_format_changed(self, event=None):
        """
        Callback para mudança de formato de frame - ajusta configurações específicas
        """
        format_selected = self.frame_format_var.get()

        # Ajustar configurações baseado no formato
        if format_selected == "PNG":
            self.frame_quality_spin.config(state="disabled")
            self.log_message(
                "PNG selecionado: Formato sem perda, qualidade não aplicável"
            )
        elif format_selected == "WebP":
            self.frame_quality_spin.config(state="normal")
            self.log_message(
                "WebP selecionado: Suporte a transparência e compressão avançada"
            )
        else:
            self.frame_quality_spin.config(state="normal")
            self.log_message(
                f"{format_selected} selecionado: Ajuste a qualidade conforme necessário"
            )

    def on_frame_mode_changed(self, event=None):
        """
        Callback para mudança de modo de extração - mostra/oculta controles específicos
        """
        self.update_frame_mode_visibility()

    def update_frame_mode_visibility(self):
        """
        Atualiza a visibilidade dos controles baseado no modo de extração selecionado
        """
        mode_selected = self.frame_mode_var.get()

        # Ocultar todos os controles primeiro
        self.interval_label.grid_remove()
        self.frame_interval_spin.grid_remove()
        self.specific_label.grid_remove()
        self.frame_specific_entry.grid_remove()

        # Mostrar controles específicos baseado no modo
        if mode_selected == "Intervalo Regular":
            self.interval_label.grid(row=0, column=0, sticky=tk.W, pady=2)
            self.frame_interval_spin.grid(
                row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2
            )
            self.log_message("Modo Intervalo: Extrair frames em intervalos regulares")
        elif mode_selected == "Frames Específicos":
            self.specific_label.grid(row=0, column=0, sticky=tk.W, pady=2)
            self.frame_specific_entry.grid(
                row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2
            )
            self.log_message(
                "Modo Específico: Digite os números dos frames (ex: 1,5,10-20)"
            )
        else:  # Todos os Frames
            self.log_message("Modo Completo: Extrair todos os frames do vídeo")

    def on_audio_extraction_changed(self):
        """
        Callback para quando a extração de áudio é habilitada/desabilitada
        """
        self.update_audio_extraction_visibility()

    def on_audio_format_changed(self, event=None):
        """
        Callback para quando o formato de áudio é alterado
        """
        audio_format = self.audio_format_var.get()
        if audio_format in AUDIO_QUALITY_PRESETS:
            # Atualizar opções de qualidade baseadas no formato
            quality_options = list(AUDIO_QUALITY_PRESETS[audio_format].keys())
            self.audio_quality_combo.config(values=quality_options)
            # Definir qualidade padrão
            if AUDIO_EXTRACTION_DEFAULTS["quality"] in quality_options:
                self.audio_quality_var.set(AUDIO_EXTRACTION_DEFAULTS["quality"])
            else:
                self.audio_quality_var.set(quality_options[0])

    def update_audio_extraction_visibility(self):
        """
        Atualiza a visibilidade dos controles de extração de áudio
        """
        is_enabled = self.audio_extraction_var.get()
        
        # Controlar estado dos widgets de áudio
        state = "normal" if is_enabled else "disabled"
        self.audio_format_combo.config(state=state)
        self.audio_quality_combo.config(state=state)
        self.audio_metadata_check.config(state=state)
        
        # Se habilitado, atualizar as opções de qualidade
        if is_enabled:
            self.on_audio_format_changed()

    def on_codec_changed(self, event=None):
        """
        Callback para mudança de codec de vídeo
        """
        codec_selected = self.codec_var.get()
        self.log_message(f"Codec selecionado: {codec_selected}")

        # Validar compatibilidade com formato
        self._validate_codec_compatibility()

    def _validate_codec_compatibility(self):
        """
        Valida a compatibilidade entre codec e formato
        """
        format_selected = self.format_var.get()
        codec_selected = self.codec_var.get()

        # AVI não suporta H.265
        if "AVI" in format_selected and "H.265" in codec_selected:
            self.codec_var.set("H.264 (Recomendado)")
            self.codec_combo.config(state="disabled")
            self.log_message("⚠️ AVI não suporta H.265. Codec alterado para H.264.")
        else:
            self.codec_combo.config(state="readonly")

    def on_performance_mode_changed(self, event=None):
        """
        Callback para mudança no modo de performance
        Atualiza o label central e aplica configurações
        """
        mode_value = int(self.performance_mode_var.get())
        mode_labels = get_performance_mode_labels()

        # Atualizar label central
        self.current_mode_label.config(text=mode_labels[mode_value])

        # Obter configuração do modo
        performance_mode = PerformanceMode(mode_value)
        config = PerformanceModeConfig.get_mode_config(performance_mode)

        # Log da mudança
        self.log_message(f"Modo de performance alterado para: {config['name']}")
        self.log_message(f"Descrição: {config['description']}")

        # Aplicar configurações específicas do modo
        self.apply_performance_mode_settings(config)

    def apply_performance_mode_settings(self, config):
        """
        Aplica as configurações específicas do modo de performance
        """
        # config agora é um dicionário com as configurações
        mode_name = config["name"]
        mode_icon = config["icon"]
        description = config["description"]

        # Log da aplicação das configurações
        self.log_message(f"{mode_icon} Modo {mode_name}: {description}")

        # Aplicar configurações específicas baseadas no modo
        if config["prefer_cpu"]:
            self.log_message("🖥️ Priorizando processamento por CPU")
        elif config["prefer_nvidia"]:
            self.log_message("🎮 Priorizando aceleração NVIDIA")

        # Log de configurações técnicas
        max_jobs = config["max_concurrent_jobs"]
        self.log_message(f"📊 Máximo de jobs simultâneos: {max_jobs}")

        if "nvenc_preset" in config:
            preset = config["nvenc_preset"]
            self.log_message(f"⚙️ Preset NVENC: {preset}")

    def setup_performance_tooltips(self):
        """
        Configura tooltips para o controle de prioridade de processamento
        """
        try:
            from utils.performance_modes import PerformanceMode, PerformanceModeConfig

            # Obter informações detalhadas de cada modo
            tooltips = {}
            for mode in PerformanceMode:
                config = PerformanceModeConfig.get_mode_config(mode)
                tooltip_text = f"{config['name']}\n"
                tooltip_text += f"📝 {config['description']}\n\n"
                tooltip_text += f"🖥️ CPU: {config['cpu_preference']}\n"
                tooltip_text += f"🎮 NVIDIA: {config['nvidia_preference']}\n"
                tooltip_text += (
                    f"⚡ Jobs simultâneos: {config['max_concurrent_jobs']}\n"
                )

                if config.get("nvenc_preset"):
                    tooltip_text += f"🎯 Preset NVENC: {config['nvenc_preset']}\n"

                tooltips[mode.value] = tooltip_text

            # Função para mostrar tooltip baseado na posição do slider
            def show_tooltip(event):
                try:
                    current_value = int(self.performance_mode_var.get())
                    if current_value in tooltips:
                        # Implementação simples de tooltip usando messagebox temporário
                        # Em uma implementação mais avançada, usaria um widget tooltip personalizado
                        self.update_status_bar(
                            f"Modo: {tooltips[current_value].split(chr(10))[0]}"
                        )
                except Exception as e:
                    self.log_message(f"Erro ao mostrar tooltip: {str(e)}")

            def hide_tooltip(event):
                self.update_status_bar("Pronto")

            # Vincular eventos
            self.performance_slider.bind("<Enter>", show_tooltip)
            self.performance_slider.bind("<Leave>", hide_tooltip)
            self.performance_slider.bind("<Motion>", show_tooltip)

        except Exception as e:
            self.log_message(f"Erro ao configurar tooltips: {str(e)}")

    def log_message(self, message, level='INFO'):
        """
        Adiciona mensagem ao log de forma thread-safe e salva em arquivo.
        """
        def update_gui():
            try:
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_entry = f"[{timestamp}] [{level}] {message}\n"

                if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                    self.log_text.insert(tk.END, log_entry)
                    self.log_text.see(tk.END)
                else:
                    print(log_entry.strip())

                if not hasattr(self, 'log_buffer'):
                    self.log_buffer = []
                self.log_buffer.append(log_entry)
                self._auto_save_log()
            except RuntimeError:
                print(f"[LOG-FALLBACK] {message}")
            except Exception as e:
                print(f"Erro interno no log_message: {e}")

        if hasattr(self, 'root'):
            try:
                self.root.after(0, update_gui)
            except RuntimeError:
                update_gui()
        else:
            update_gui()

    def _auto_save_log(self):
        """
        Salva automaticamente o log atual
        """
        try:
            if hasattr(self, "log_text") and self.log_text:
                log_content = self.log_text.get("1.0", tk.END)
                if log_content.strip():
                    filename = self._generate_log_filename("auto")
                    self._save_log_to_file(log_content, filename)
        except Exception as e:
            # Falha silenciosa no salvamento automático para não interromper o fluxo
            print(f"Erro no salvamento automático: {str(e)}")

    def get_conversion_settings(self):
        """
        Coleta configurações de conversão
        """
        # Obter modo de performance atual
        performance_mode = PerformanceMode(int(self.performance_mode_var.get()))
        performance_config = PerformanceModeConfig.get_mode_config(performance_mode)

        # Mapear codec da interface para o formato esperado pelo video_converter
        codec_text = self.codec_var.get()
        codec = "hevc" if "H.265" in codec_text else "h264"

        settings = {
            "format": self.format_var.get(),
            "quality": self.quality_var.get(),
            "transparency": self.transparency_var.get(),
            "fps": self.fps_var.get(),
            "resolution": self.resolution_var.get(),
            "codec": codec,
            "performance_mode": performance_mode,
            "performance_config": performance_config,
        }

        if settings["fps"] == "Personalizado":
            settings["fps_custom"] = self.fps_custom_var.get()

        if settings["resolution"] == "Personalizada":
            settings["width"] = self.width_var.get()
            settings["height"] = self.height_var.get()

        # Configurações específicas para GIF
        if "GIF (Animado)" in settings["format"]:
            settings["gif_settings"] = {
                "quality": self.gif_quality_var.get(),
                "fps": self.gif_fps_var.get(),
                "colors": self.gif_colors_var.get(),
                "resolution": self.gif_resolution_var.get(),
                "dithering": self.gif_dithering_var.get(),
                "optimize": self.gif_optimize_var.get(),
            }

        # Configurações específicas para extração de frames
        if "Extração de Frames" in settings["format"]:
            settings["frame_extraction_settings"] = {
                "format": self.frame_format_var.get(),
                "mode": self.frame_mode_var.get(),
                "quality": self.frame_quality_var.get(),
                "auto_folder": self.frame_auto_folder_var.get(),
            }

            # Configurações específicas do modo
            if settings["frame_extraction_settings"]["mode"] == "Intervalo Regular":
                settings["frame_extraction_settings"][
                    "interval"
                ] = self.frame_interval_var.get()
            elif settings["frame_extraction_settings"]["mode"] == "Frames Específicos":
                settings["frame_extraction_settings"][
                    "specific_frames"
                ] = self.frame_specific_var.get()

        # Configurações específicas para extração de áudio
        if hasattr(self, 'audio_extraction_var') and self.audio_extraction_var.get():
            settings["audio_extraction_settings"] = {
                "enabled": True,
                "format": self.audio_format_var.get(),
                "quality": self.audio_quality_var.get(),
                "preserve_metadata": self.audio_metadata_var.get(),
            }

        return settings

    def set_conversion_state(self, converting):
        """
        Habilita/desabilita controles durante conversão
        """
        state = "disabled" if converting else "normal"

        # Controles de arquivo
        self.output_dir_entry.config(state=state)

        # Controles de configuração
        self.format_combo.config(state="disabled" if converting else "readonly")
        self.quality_combo.config(state="disabled" if converting else "readonly")
        self.fps_combo.config(state="disabled" if converting else "readonly")
        self.resolution_combo.config(state="disabled" if converting else "readonly")
        self.transparency_check.config(state=state)

        # Controles personalizados
        if not converting:
            self.on_fps_changed()
            self.on_resolution_changed()
        else:
            self.fps_custom_spin.config(state="disabled")
            self.width_spin.config(state="disabled")
            self.height_spin.config(state="disabled")

        # Botões
        self.convert_btn.config(state="disabled" if converting else "normal")
        self.cancel_btn.config(state="normal" if converting else "disabled")

        # Atualizar status bar
        if converting:
            self.update_status_bar("Conversão em andamento...")
        else:
            self.update_status_bar("Pronto para Conversão")

    def start_conversion(self):
        """
        Inicia conversão de múltiplos arquivos usando o sistema de fila
        """
        # Validações
        if not self.selected_files:
            messagebox.showerror("Erro", "Adicione arquivos à lista para conversão.")
            return

        if not self.output_dir_var.get():
            messagebox.showerror("Erro", "Selecione uma pasta de destino.")
            return

        # Validar diretório
        is_valid, error_msg = validate_output_directory(self.output_dir_var.get())
        if not is_valid:
            messagebox.showerror("Erro", f"Diretório inválido: {error_msg}")
            return

        # Configurações
        settings = self.get_conversion_settings()

        # LOG DETALHADO: Diagnóstico de travamento
        self.log_message(
            "🔍 DIAGNÓSTICO: Iniciando análise de possíveis causas de travamento"
        )
        self.log_message(f"🔍 Formato selecionado: {settings.get('format', 'N/A')}")
        self.log_message(f"🔍 Número de arquivos: {len(self.selected_files)}")
        self.log_message(
            f"🔍 Modo de performance: {settings.get('performance_config', {}).get('name', 'N/A')}"
        )

        # CORREÇÃO: Verificar se é operação problemática (GIF ou Extração de Frames)
        format_selected = settings.get("format", "")
        if (
            "GIF (Animado)" in format_selected
            or "Extração de Frames" in format_selected
        ):
            self.log_message(
                "🚨 OPERAÇÃO DE RISCO DETECTADA: GIF ou Extração de Frames"
            )
            self.log_message("🚨 Possíveis causas de travamento:")
            self.log_message("   1. Processamento intensivo na thread principal")
            self.log_message("   2. Alto consumo de memória")
            self.log_message("   3. Falta de timeout para operações longas")
            self.log_message("   4. Problemas de threading com Tkinter")

            # CORREÇÃO: Avisar usuário sobre operação crítica
            warning_msg = (
                "⚠️ ATENÇÃO: Operação crítica detectada!\n\n"
                "Esta operação pode demorar muito tempo e consumir muitos recursos.\n"
                "Recomendações:\n"
                "- Mantenha a aplicação em foco\n"
                "- Não minimize a janela durante o processamento\n"
                "- Certifique-se de ter espaço suficiente em disco\n\n"
                "Deseja continuar?"
            )
            if not messagebox.askyesno("Operação Crítica", warning_msg):
                self.log_message("❌ Operação cancelada pelo usuário")
                return

        # Configurar callbacks para o queue manager
        # NOTA: Callbacks globais já estão configurados em _setup_queue_callbacks()
        # Aqui configuramos apenas callbacks específicos se necessário
        callbacks = {
            "log": self.log_message,  # Manter log individual para debug
        }

        # Adicionar arquivos à fila
        jobs_added = 0
        for file_info in self.selected_files:
            if file_info["status"] == "Pendente":
                # Validar arquivo
                is_valid, error_msg = validate_input_file(file_info["path"])
                if not is_valid:
                    self.log_message(
                        f"Arquivo inválido ignorado: {file_info['name']} - {error_msg}"
                    )
                    file_info["status"] = "Erro"
                    continue

                # Construir caminho de saída completo
                input_path = Path(file_info["path"])
                
                # Determinar formato de saída correto
                format_name = settings.get("format", "mp4")
                
                # Verificar se é extração de áudio (pelo formato ou pelo checkbox)
                is_audio_extraction = (
                    "Extração de Áudio" in format_name or 
                    settings.get("audio_extraction_settings", {}).get("enabled", False)
                )
                
                if is_audio_extraction:
                    # Para extração de áudio, usar o formato de áudio específico
                    if settings.get("audio_extraction_settings", {}).get("format"):
                        audio_format = settings["audio_extraction_settings"]["format"]
                    else:
                        # Formato padrão se não especificado
                        audio_format = "MP3"
                    
                    # Mapear formato de áudio para extensão
                    audio_extensions = {
                        "MP3": "mp3",
                        "AAC": "aac", 
                        "WAV": "wav",
                        "FLAC": "flac",
                        "OGG": "ogg",
                        "M4A": "m4a",
                        "WMA": "wma",
                        "OPUS": "opus"
                    }
                    output_format = audio_extensions.get(audio_format, "mp3")
                else:
                    output_format = format_name
                
                output_filename = f"{input_path.stem}.{output_format}"
                output_file = os.path.join(self.output_dir_var.get(), output_filename)

                # Adicionar à fila
                job_id = self.queue_manager.add_job(
                    input_file=file_info["path"],
                    output_file=output_file,
                    settings=settings,
                    callbacks=callbacks,
                )

                file_info["job_id"] = job_id
                file_info["status"] = "Na Fila"
                jobs_added += 1

        if jobs_added == 0:
            messagebox.showwarning("Aviso", "Nenhum arquivo válido para conversão.")
            return

        # Atualizar interface
        self.update_files_tree()
        self.set_conversion_state(True)
        self.log_message(f"Iniciando conversão de {jobs_added} arquivo(s)...")

        # Iniciar processamento da fila
        self.queue_manager.start_queue()

    def cancel_conversion(self):
        """
        Cancela conversões em andamento
        """
        if messagebox.askyesno(
            "Cancelar", "Tem certeza que deseja cancelar a conversão?"
        ):
            queue_status = self.queue_manager.get_queue_status()
            if queue_status["is_running"] and (
                queue_status["active_jobs"] > 0 or queue_status["pending_jobs"] > 0
            ):
                # Parar toda a fila
                self.queue_manager.stop_queue()

                # Atualizar status dos arquivos
                cancelled_count = 0
                for file_info in self.selected_files:
                    if file_info["status"] in ["Na Fila", "Convertendo"]:
                        file_info["status"] = "Cancelado"
                        file_info["progress"] = "0%"
                        file_info["gpu"] = "-"
                        cancelled_count += 1

                self.update_files_tree()
                self.set_conversion_state(False)
                self.progress_var.set(0)  # Resetar progresso
                self.update_status_bar(
                    f"Conversão cancelada - {cancelled_count} arquivos"
                )
                self.log_message(f"Conversões canceladas ({cancelled_count} arquivos)")
                self.status_var.set("Conversão cancelada")
            else:
                self.log_message("Nenhuma conversão em andamento")

    def clear_fields(self):
        """
        Limpa todos os campos
        """
        # Limpar lista de arquivos
        self.selected_files.clear()
        self.update_files_tree()

        self.output_dir_var.set("")
        self.format_var.set("MP4")
        self.quality_var.set("Média")
        self.codec_var.set("H.264 (Recomendado)")
        self.fps_var.set("Original")
        self.resolution_var.set("Original")
        self.transparency_var.set(False)
        self.fps_custom_var.set(30)
        self.width_var.set(1920)
        self.height_var.set(1080)
        self.progress_var.set(0)
        self.status_var.set("Pronto para conversão")
        
        # Limpar campos de extração de áudio
        if hasattr(self, 'audio_extraction_var'):
            self.audio_extraction_var.set(False)
            self.audio_format_var.set(AUDIO_EXTRACTION_DEFAULTS["format"])
            self.audio_quality_var.set(AUDIO_EXTRACTION_DEFAULTS["quality"])
            self.audio_metadata_var.set(AUDIO_EXTRACTION_DEFAULTS["preserve_metadata"])
            self.update_audio_extraction_visibility()
        
        self.log_message("Campos da aba Arquivos limpos")

    def on_job_started(self, job_id, input_file, gpu_info):
        """
        Callback quando um job inicia (thread-safe)
        """

        def update_gui():
            # Encontrar arquivo na lista e atualizar status
            for file_info in self.selected_files:
                if file_info["job_id"] == job_id:
                    file_info["status"] = "Convertendo"
                    file_info["gpu"] = gpu_info.get("name", "CPU")
                    break

            self.update_files_tree()
            filename = os.path.basename(input_file)

            # Atualizar status bar com arquivo atual
            self.update_status_bar(f"Convertendo: {filename}")

            self.log_message(
                f"Iniciando conversão: {filename} (GPU: {gpu_info.get('name', 'CPU')})"
            )

        # Executar na thread principal da GUI
        self.root.after(0, update_gui)

    def on_job_progress(self, job_id, progress):
        """
        Callback para atualização de progresso de um job (thread-safe)
        """

        def update_gui():
            # Encontrar arquivo na lista e atualizar progresso
            current_file = None
            for file_info in self.selected_files:
                if file_info["job_id"] == job_id:
                    file_info["progress"] = f"{progress}%"
                    current_file = file_info["name"]
                    break

            self.update_files_tree()

            # Atualizar progresso geral (média de todos os jobs)
            total_progress = 0
            active_jobs = 0
            for file_info in self.selected_files:
                if file_info["status"] in ["Convertendo", "Concluído"]:
                    progress_val = int(float(file_info["progress"].replace("%", "")))
                    total_progress += progress_val
                    active_jobs += 1

            if active_jobs > 0:
                avg_progress = total_progress // active_jobs
                self.progress_var.set(avg_progress)

            # Atualizar status bar com progresso
            if current_file:
                self.update_status_bar(f"Convertendo: {current_file} - {progress:.1f}%")

            # Log de progresso a cada 10%
            if progress % 10 == 0:
                self.log_message(f"Progresso: {progress:.1f}%")

        # Executar na thread principal da GUI
        self.root.after(0, update_gui)

    def on_job_finished(self, job_id, success, message, output_file=None):
        """
        Callback quando um job termina (thread-safe)
        """

        def update_gui():
            # Encontrar e atualizar arquivo na lista
            for file_info in self.selected_files:
                if file_info["job_id"] == job_id:
                    file_info["status"] = "Concluído" if success else "Erro"
                    file_info["progress"] = "100%" if success else "0%"
                    break

            # Atualizar a visualização da lista
            self.update_files_tree()

            # Log do resultado
            filename = os.path.basename(output_file) if output_file else "arquivo"
            if success:
                self.log_message(f"✓ Conversão concluída: {filename}")
                self.update_status_bar(f"Concluído: {filename}")
            else:
                self.log_message(f"✗ Erro na conversão: {message}")
                self.update_status_bar(f"Erro: {filename}")

        # Executar na thread principal da GUI
        self.root.after(0, update_gui)

    def on_queue_finished(self, total_jobs, successful_jobs, failed_jobs):
        """
        Callback quando toda a fila termina (thread-safe)
        """

        def update_gui():
            # Restaurar estado dos controles
            self.set_conversion_state(False)
            self.progress_var.set(0)  # Resetar progresso para 0

            # Atualizar status bar
            if failed_jobs == 0:
                self.update_status_bar(
                    f"Conversão finalizada - {successful_jobs} arquivos convertidos"
                )
            else:
                self.update_status_bar(
                    f"Conversão finalizada - {successful_jobs} sucessos, {failed_jobs} falhas"
                )

            message = f"Processamento concluído!\n"
            message += f"Total: {total_jobs} arquivos\n"
            message += f"Sucessos: {successful_jobs}\n"
            message += f"Falhas: {failed_jobs}"

            self.log_message(
                f"Fila de conversão finalizada - {successful_jobs}/{total_jobs} sucessos"
            )

            if failed_jobs == 0:
                messagebox.showinfo("Sucesso", message)
            else:
                messagebox.showwarning("Concluído com Erros", message)

        # Executar na thread principal da GUI
        self.root.after(0, update_gui)

    def check_ffmpeg_installation(self):
        """
        Verifica a instalação do FFmpeg de forma segura em uma thread separada,
        garantindo que todas as atualizações da GUI sejam executadas na thread principal.
        """

        def update_gui(callback, *args):
            """Agenda a execução de uma função na thread principal da GUI."""
            self.root.after(0, callback, *args)

        def check_and_install():
            """
            Lógica de verificação e instalação do FFmpeg.
            As interações com a GUI são delegadas para `update_gui`.
            """
            if not self.ffmpeg_installer.is_ffmpeg_installed():
                update_gui(self.log_message, "FFmpeg não encontrado. Iniciando instalação automática...")
                update_gui(self.status_var.set, "Instalando FFmpeg...")

                try:
                    success = self.ffmpeg_installer.install_ffmpeg()
                    if success:
                        update_gui(self.log_message, "✓ FFmpeg instalado com sucesso!")
                        update_gui(self.status_var.set, "FFmpeg instalado - Pronto para conversão")
                    else:
                        update_gui(self.log_message, "✗ Falha na instalação do FFmpeg")
                        update_gui(self.status_var.set, "Erro na instalação do FFmpeg")
                except Exception as e:
                    update_gui(self.log_message, f"✗ Erro na instalação do FFmpeg: {str(e)}")
                    update_gui(self.status_var.set, "Erro na instalação do FFmpeg")
                    update_gui(
                        messagebox.showwarning,
                        "Aviso",
                        "Não foi possível instalar o FFmpeg automaticamente. "
                        "Instale manualmente para usar o conversor.",
                    )
            else:
                update_gui(self.log_message, "✓ FFmpeg encontrado e pronto para uso")
                update_gui(self.status_var.set, "Pronto para conversão")

        # Executar verificação em thread separada para não bloquear a GUI
        threading.Thread(target=check_and_install, daemon=True).start()

    def setup_update_system(self):
        """
        Configura o sistema de atualização automática
        """
        # Conectar callbacks do widget de atualização com o sistema de logs
        self.update_widget.set_log_callback(self.log_message)
        self.update_widget.set_status_callback(self.update_status_bar)
        
        # Verificar atualizações na inicialização (desativado)
        # self.root.after(3000, self.check_updates_on_startup)
        
        # Configurar verificação periódica (a cada hora = 3600000 ms)
        self.setup_periodic_update_check()

    def check_updates_on_startup(self):
        """
        Verifica atualizações na inicialização da aplicação
        """
        def check_updates():
            try:
                self.log_message("🔍 Verificando atualizações disponíveis...")
                self.update_status_bar("Verificando atualizações...")
                
                # Verificar se há atualizações disponíveis
                has_update = self.update_checker.check_for_updates()
                
                if has_update:
                    latest_version = self.update_checker.get_latest_version()
                    self.log_message(f"✨ Nova versão disponível: {latest_version}")
                    self.update_status_bar(f"Atualização disponível: {latest_version}")
                    
                    # Notificar o widget sobre a atualização disponível
                    self.root.after(0, lambda: self.update_widget.show_update_notification(latest_version))
                else:
                    self.log_message("✓ Aplicação está atualizada")
                    self.update_status_bar("Pronto para conversão")
                    
            except Exception as e:
                self.log_message(f"⚠️ Erro ao verificar atualizações: {str(e)}")
                self.update_status_bar("Erro na verificação de atualizações")
        
        # Executar em thread separada para não bloquear a interface
        threading.Thread(target=check_updates, daemon=True).start()

    def setup_periodic_update_check(self):
        """
        Configura verificação periódica de atualizações (a cada hora)
        """
        def periodic_check():
            try:
                has_update = self.update_checker.check_for_updates()
                if has_update:
                    latest_version = self.update_checker.get_latest_version()
                    self.log_message(f"🔔 Nova atualização detectada: {latest_version}")
                    # Notificar o widget sobre a atualização
                    self.root.after(0, lambda: self.update_widget.show_update_notification(latest_version))
            except Exception as e:
                # Log silencioso para verificações periódicas
                pass
        
        def schedule_next_check():
            # Executar verificação em thread separada
            threading.Thread(target=periodic_check, daemon=True).start()
            # Agendar próxima verificação em 1 hora (3600000 ms)
            self.root.after(3600000, schedule_next_check)
        
        # Iniciar o ciclo de verificações periódicas
        schedule_next_check()

    def _setup_queue_callbacks(self):
        """
        Configura callbacks globais para o gerenciador de fila
        """
        callbacks = {
            "queue_updated": self._on_queue_updated,
            "job_started": self._on_job_started_global,
            "job_completed": self._on_job_completed,
            "job_failed": self._on_job_failed,
            "job_progress": self._on_job_progress_global,
            "queue_finished": self.on_queue_finished,  # ✅ ADICIONADO: callback para fila finalizada
            "log": self._on_log_message,
        }
        self.queue_manager.set_global_callbacks(callbacks)

    def _on_queue_updated(self, queue_data):
        """
        Callback para atualização da fila de conversão

        Args:
            queue_data: Dados atualizados da fila
        """

        def update_gui():
            self.log_message(f"Fila atualizada: {len(queue_data)} jobs na fila")

        self.root.after(0, update_gui)

    def _on_job_started_global(self, job_data):
        """
        Callback global para início de um job de conversão

        Args:
            job_data: Dicionário com dados do job iniciado
        """

        def update_gui():
            # Encontrar o arquivo na lista e atualizar status e GPU
            job_id = job_data.get("id")
            for file_info in self.selected_files:
                if file_info.get("job_id") == job_id:
                    file_info["status"] = "Processando"
                    assigned_gpu = job_data.get("assigned_gpu", "CPU")
                    file_info["gpu"] = assigned_gpu if assigned_gpu else "CPU"
                    break

            self.update_files_tree()
            input_file = job_data.get("input_file", "Arquivo desconhecido")
            assigned_gpu = job_data.get("assigned_gpu", "CPU")
            gpu_display = assigned_gpu if assigned_gpu else "CPU"
            self.log_message(
                f"Iniciando conversão: {os.path.basename(input_file)} (GPU: {gpu_display})"
            )

        self.root.after(0, update_gui)

    def _on_job_completed(self, job_data):
        """
        Callback para job completado com sucesso

        Args:
            job_data: Dicionário com dados do job completado
        """

        def update_gui():
            # Encontrar o arquivo na lista e atualizar status
            job_id = job_data.get("id")
            for file_info in self.selected_files:
                if file_info.get("job_id") == job_id:
                    file_info["status"] = "Concluído"
                    break

            self.update_files_tree()
            output_file = job_data.get("output_file", "Arquivo de saída")
            self.log_message(f"✓ Conversão concluída: {os.path.basename(output_file)}")

        self.root.after(0, update_gui)

    def _on_job_failed(self, job_data):
        """
        Callback para job que falhou

        Args:
            job_data: Dicionário com dados do job que falhou
        """

        def update_gui():
            # Encontrar o arquivo na lista e atualizar status
            job_id = job_data.get("id")
            error = job_data.get("error_message", "Erro desconhecido")
            for file_info in self.selected_files:
                if file_info.get("job_id") == job_id:
                    file_info["status"] = "Erro"
                    break

            self.update_files_tree()
            self.log_message(f"✗ Erro na conversão (Job {job_id}): {error}")

        self.root.after(0, update_gui)

    def _on_job_progress_global(self, job_id, progress_data):
        """
        Callback global para progresso de um job

        Args:
            job_id: ID do job
            progress_data: Dados de progresso (int representando porcentagem)
        """

        def update_gui():
            # Atualizar progresso individual do arquivo
            # progress_data é um int representando a porcentagem
            if isinstance(progress_data, dict):
                percentage = progress_data.get("percentage", 0)
            else:
                percentage = (
                    progress_data if isinstance(progress_data, (int, float)) else 0
                )
            for file_info in self.selected_files:
                if file_info.get("job_id") == job_id:
                    file_info["progress"] = f"{percentage:.1f}%"
                    break

            self.update_files_tree()

            # Calcular progresso geral
            total_files = len([f for f in self.selected_files if f.get("job_id")])
            if total_files > 0:
                # Extrair valores numéricos do progresso para calcular média
                progress_values = []
                for f in self.selected_files:
                    if f.get("job_id"):
                        progress_str = f.get("progress", "0%")
                        if isinstance(progress_str, str) and "%" in progress_str:
                            progress_values.append(float(progress_str.replace("%", "")))
                        else:
                            progress_values.append(0)

                if progress_values:
                    overall_progress = sum(progress_values) / len(progress_values)
                    self.progress_var.set(overall_progress)
                    self.progress_label_var.set(
                        f"Progresso Geral: {overall_progress:.1f}%"
                    )

        self.root.after(0, update_gui)

    def _on_log_message(self, message):
        """
        Callback para mensagens de log

        Args:
            message: Mensagem a ser logada
        """

        def update_gui():
            self.log_message(message)

        self.root.after(0, update_gui)

    def clear_conversion_logs(self):
        """
        Limpa apenas os logs de conversão
        """
        try:
            self.log_text.delete(1.0, tk.END)
            self.log_buffer.clear()  # Limpa também o buffer de logs
            self.log_message("Logs de conversão limpos")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao limpar logs de conversão: {str(e)}")

    def clear_youtube_logs(self):
        """
        Limpa apenas os logs de download do YouTube
        """
        try:
            if hasattr(self, 'youtube_log_text'):
                self.youtube_log_text.delete(1.0, tk.END)
                self.log_youtube("Logs de download do YouTube limpos")
            else:
                messagebox.showwarning("Aviso", "Área de logs do YouTube não encontrada")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao limpar logs do YouTube: {str(e)}")

    def run_youtube_api_download(self, url, output_dir):
        """
        Executa download usando abordagem híbrida:
        - YouTube Data API v3 para metadados oficiais
        - yt-dlp otimizado para URLs diretas (sem múltiplos fallbacks)
        """
        try:
            resolution = self.resolution_var.get() or "720p"
            
            self.log_youtube("🔑 Iniciando download híbrido (API + yt-dlp otimizado)...")
            self.log_youtube(f"🎯 Resolução alvo: {resolution}")
            
            def progress_callback(progress):
                """Callback para atualizar progresso do download"""
                self.log_youtube(f"📊 Progresso: {progress:.1f}%")
            
            def info_callback(message):
                """Callback para mensagens informativas"""
                self.log_youtube(message)
            
            # Usar o YouTube API Downloader híbrido
            success = self.youtube_api_downloader.download_video(
                url=url,
                output_path=output_dir,
                quality=resolution,
                progress_callback=progress_callback,
                info_callback=info_callback
            )
            
            if success:
                self.log_youtube("🎉 Download concluído com sucesso!")
                self.show_info_on_main_thread("Download Concluído", "Vídeo baixado com sucesso usando método híbrido!")
            else:
                # Se o método híbrido falhou, usar fallback tradicional
                self.log_youtube("🔄 Método híbrido falhou, tentando fallback tradicional...")
                self.run_youtube_download_with_fallback(url, output_dir)
                    
        except Exception as e:
            error_msg = f"Erro no download híbrido: {str(e)}"
            self.log_youtube(f"💥 {error_msg}")
            # Em caso de erro, tentar fallback tradicional uma única vez
            self.log_youtube("🔄 Tentando fallback tradicional...")
            try:
                self.run_youtube_download_with_fallback(url, output_dir)
            except Exception as fallback_error:
                final_error = f"API falhou: {str(e)}\nFallback yt-dlp também falhou: {str(fallback_error)}"
                self.show_error_on_main_thread("Erro de Download", final_error)


def main():
    """
    Função principal para executar a aplicação
    """
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
