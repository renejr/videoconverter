"""
Interface gráfica principal do Video Converter usando Tkinter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path

from core.video_converter import VideoConverterManager
from core.ffmpeg_installer import FFmpegInstaller
from utils.config import (SUPPORTED_OUTPUT_FORMATS, FPS_OPTIONS, RESOLUTION_PRESETS)
from utils.validators import validate_input_file, validate_output_directory


class MainWindow:
    """
    Janela principal da aplicação Video Converter
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Video Converter - Conversor de Vídeo")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Inicializar componentes
        self.video_converter = VideoConverterManager()
        self.conversion_thread = None
        self.ffmpeg_installer = FFmpegInstaller()
        
        # Configurar estilo
        self.setup_style()
        
        # Criar interface
        self.create_widgets()
        
        # Verificar FFmpeg na inicialização
        self.check_ffmpeg_installation()
    
    def setup_style(self):
        """
        Configura o estilo da aplicação
        """
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar cores
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
    
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
        main_frame.columnconfigure(1, weight=1)
        
        # Seção de arquivos
        self.create_file_section(main_frame, 0)
        
        # Seção de configurações
        self.create_settings_section(main_frame, 1)
        
        # Seção de progresso
        self.create_progress_section(main_frame, 2)
        
        # Seção de ações
        self.create_actions_section(main_frame, 3)
        
        # Seção de logs
        self.create_log_section(main_frame, 4)
        
        # Barra de status
        self.create_status_bar()
    
    def create_file_section(self, parent, row):
        """
        Cria a seção de seleção de arquivos
        """
        # Frame de arquivos
        file_frame = ttk.LabelFrame(parent, text="Arquivos", padding="10")
        file_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(1, weight=1)
        
        # Arquivo de entrada
        ttk.Label(file_frame, text="Arquivo de Entrada:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.input_file_var = tk.StringVar()
        self.input_file_entry = ttk.Entry(file_frame, textvariable=self.input_file_var, width=50)
        self.input_file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="Procurar...", command=self.browse_input_file).grid(row=0, column=2, pady=2)
        
        # Pasta de saída
        ttk.Label(file_frame, text="Pasta de Saída:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(file_frame, textvariable=self.output_dir_var, width=50)
        self.output_dir_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(file_frame, text="Procurar...", command=self.browse_output_dir).grid(row=1, column=2, pady=2)
    
    def create_settings_section(self, parent, row):
        """
        Cria a seção de configurações de conversão
        """
        # Frame de configurações
        settings_frame = ttk.LabelFrame(parent, text="Configurações de Conversão", padding="10")
        settings_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)
        
        # Formato
        ttk.Label(settings_frame, text="Formato:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.format_var = tk.StringVar(value="MP4")
        self.format_combo = ttk.Combobox(settings_frame, textvariable=self.format_var, 
                                        values=SUPPORTED_OUTPUT_FORMATS, state="readonly")
        self.format_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2)
        self.format_combo.bind('<<ComboboxSelected>>', self.on_format_changed)
        
        # Qualidade
        ttk.Label(settings_frame, text="Qualidade:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.quality_var = tk.StringVar(value="Média")
        self.quality_combo = ttk.Combobox(settings_frame, textvariable=self.quality_var,
                                         values=["Baixa", "Média", "Alta", "Muito Alta"], state="readonly")
        self.quality_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        
        # FPS
        ttk.Label(settings_frame, text="FPS:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fps_var = tk.StringVar(value="Original")
        self.fps_combo = ttk.Combobox(settings_frame, textvariable=self.fps_var,
                                     values=FPS_OPTIONS, state="readonly")
        self.fps_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2)
        self.fps_combo.bind('<<ComboboxSelected>>', self.on_fps_changed)
        
        # FPS personalizado
        self.fps_custom_var = tk.IntVar(value=30)
        self.fps_custom_spin = ttk.Spinbox(settings_frame, from_=1, to=120, 
                                          textvariable=self.fps_custom_var, width=10, state="disabled")
        self.fps_custom_spin.grid(row=1, column=2, sticky=tk.W, padx=(5, 10), pady=2)
        
        # Resolução
        ttk.Label(settings_frame, text="Resolução:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.resolution_var = tk.StringVar(value="Original")
        self.resolution_combo = ttk.Combobox(settings_frame, textvariable=self.resolution_var,
                                           values=list(RESOLUTION_PRESETS.keys()), state="readonly")
        self.resolution_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=2)
        self.resolution_combo.bind('<<ComboboxSelected>>', self.on_resolution_changed)
        
        # Resolução personalizada
        custom_frame = ttk.Frame(settings_frame)
        custom_frame.grid(row=2, column=2, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        
        self.width_var = tk.IntVar(value=1920)
        self.height_var = tk.IntVar(value=1080)
        
        ttk.Label(custom_frame, text="Largura:").grid(row=0, column=0, sticky=tk.W)
        self.width_spin = ttk.Spinbox(custom_frame, from_=64, to=7680, 
                                     textvariable=self.width_var, width=8, state="disabled")
        self.width_spin.grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(custom_frame, text="Altura:").grid(row=0, column=2, sticky=tk.W)
        self.height_spin = ttk.Spinbox(custom_frame, from_=64, to=4320,
                                      textvariable=self.height_var, width=8, state="disabled")
        self.height_spin.grid(row=0, column=3, padx=(5, 0))
        
        # Transparência
        self.transparency_var = tk.BooleanVar()
        self.transparency_check = ttk.Checkbutton(settings_frame, text="Preservar Transparência",
                                                 variable=self.transparency_var, state="disabled")
        self.transparency_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
    
    def create_progress_section(self, parent, row):
        """
        Cria a seção de progresso
        """
        # Frame de progresso
        progress_frame = ttk.LabelFrame(parent, text="Progresso", padding="10")
        progress_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Label de status
        self.status_var = tk.StringVar(value="Pronto para conversão")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, pady=2)
    
    def create_actions_section(self, parent, row):
        """
        Cria a seção de ações
        """
        # Frame de ações
        actions_frame = ttk.Frame(parent)
        actions_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        # Botões
        self.convert_btn = ttk.Button(actions_frame, text="Converter", command=self.start_conversion)
        self.convert_btn.grid(row=0, column=0, padx=5)
        
        self.cancel_btn = ttk.Button(actions_frame, text="Cancelar", command=self.cancel_conversion, state="disabled")
        self.cancel_btn.grid(row=0, column=1, padx=5)
        
        self.clear_btn = ttk.Button(actions_frame, text="Limpar", command=self.clear_fields)
        self.clear_btn.grid(row=0, column=2, padx=5)
    
    def create_log_section(self, parent, row):
        """
        Cria a seção de logs
        """
        # Frame de logs
        log_frame = ttk.LabelFrame(parent, text="Log de Conversão", padding="10")
        log_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
        
        # Área de texto para logs
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_status_bar(self):
        """
        Cria a barra de status
        """
        self.status_bar = ttk.Label(self.root, text="Pronto", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def browse_input_file(self):
        """
        Abre diálogo para selecionar arquivo de entrada
        """
        filetypes = [
            ("Arquivos de Vídeo", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
            ("Todos os Arquivos", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Selecionar Arquivo de Vídeo",
            filetypes=filetypes
        )
        
        if filename:
            self.input_file_var.set(filename)
            self.log_message(f"Arquivo selecionado: {os.path.basename(filename)}")
    
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
        Callback para mudança de formato - controla opções específicas do WebP
        """
        format_selected = self.format_var.get()
        
        # Habilitar/desabilitar transparência baseado no formato
        if 'WEBP' in format_selected or 'WebM' in format_selected or 'MOV' in format_selected:
            self.transparency_check.config(state="normal")
        else:
            self.transparency_check.config(state="disabled")
            self.transparency_var.set(False)
        
        # Mostrar dica específica para WebP
        if 'WEBP' in format_selected:
            self.log_message("WebP selecionado: Suporte a animação e transparência disponível")
    
    def log_message(self, message):
        """
        Adiciona mensagem ao log
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def get_conversion_settings(self):
        """
        Coleta configurações de conversão
        """
        settings = {
            'format': self.format_var.get(),
            'quality': self.quality_var.get(),
            'transparency': self.transparency_var.get(),
            'fps': self.fps_var.get(),
            'resolution': self.resolution_var.get()
        }
        
        if settings['fps'] == 'Personalizado':
            settings['fps_custom'] = self.fps_custom_var.get()
        
        if settings['resolution'] == 'Personalizada':
            settings['width'] = self.width_var.get()
            settings['height'] = self.height_var.get()
        
        return settings
    
    def set_conversion_state(self, converting):
        """
        Habilita/desabilita controles durante conversão
        """
        state = "disabled" if converting else "normal"
        
        # Controles de arquivo
        self.input_file_entry.config(state=state)
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
        self.clear_btn.config(state=state)
    
    def start_conversion(self):
        """
        Inicia conversão
        """
        # Validações
        if not self.input_file_var.get():
            messagebox.showerror("Erro", "Selecione um arquivo de vídeo de entrada.")
            return
        
        if not self.output_dir_var.get():
            messagebox.showerror("Erro", "Selecione uma pasta de destino.")
            return
        
        # Validar arquivo
        is_valid, error_msg = validate_input_file(self.input_file_var.get())
        if not is_valid:
            messagebox.showerror("Erro", f"Arquivo inválido: {error_msg}")
            return
        
        # Validar diretório
        is_valid, error_msg = validate_output_directory(self.output_dir_var.get())
        if not is_valid:
            messagebox.showerror("Erro", f"Diretório inválido: {error_msg}")
            return
        
        # Configurar callbacks
        callbacks = {
            'progress': self.on_progress_updated,
            'status': self.on_status_updated,
            'finished': self.on_conversion_finished,
            'log': self.log_message
        }
        
        # Configurações
        settings = self.get_conversion_settings()
        
        # Iniciar conversão
        self.set_conversion_state(True)
        self.log_message("Iniciando conversão...")
        
        self.conversion_thread = self.video_converter.start_conversion(
            self.input_file_var.get(),
            self.output_dir_var.get(),
            settings,
            callbacks
        )
    
    def cancel_conversion(self):
        """
        Cancela conversão
        """
        if messagebox.askyesno("Cancelar", "Tem certeza que deseja cancelar a conversão?"):
            self.video_converter.cancel_conversion()
            self.log_message("Conversão cancelada pelo usuário")
            self.set_conversion_state(False)
            self.status_var.set("Conversão cancelada")
    
    def clear_fields(self):
        """
        Limpa todos os campos
        """
        self.input_file_var.set("")
        self.output_dir_var.set("")
        self.format_var.set("MP4")
        self.quality_var.set("Média")
        self.fps_var.set("Original")
        self.resolution_var.set("Original")
        self.transparency_var.set(False)
        self.fps_custom_var.set(30)
        self.width_var.set(1920)
        self.height_var.set(1080)
        self.progress_var.set(0)
        self.status_var.set("Pronto para conversão")
        self.log_text.delete(1.0, tk.END)
        self.log_message("Campos limpos")
    
    def on_progress_updated(self, progress):
        """
        Callback para progresso
        """
        self.progress_var.set(progress)
        self.root.update_idletasks()
    
    def on_status_updated(self, status):
        """
        Callback para status
        """
        self.status_var.set(status)
        self.root.update_idletasks()
    
    def on_conversion_finished(self, success, message):
        """
        Callback para conclusão
        """
        self.set_conversion_state(False)
        
        if success:
            messagebox.showinfo("Sucesso", message)
            self.log_message("✓ Conversão concluída com sucesso!")
        else:
            messagebox.showerror("Erro", message)
            self.log_message(f"✗ Erro na conversão: {message}")
        
        self.status_var.set("Pronto para conversão")
    
    def check_ffmpeg_installation(self):
        """
        Verifica instalação do FFmpeg
        """
        def check_and_install():
            if not self.ffmpeg_installer.is_ffmpeg_installed():
                self.log_message("FFmpeg não encontrado. Iniciando instalação automática...")
                self.status_var.set("Instalando FFmpeg...")
                
                try:
                    success = self.ffmpeg_installer.install_ffmpeg()
                    if success:
                        self.log_message("✓ FFmpeg instalado com sucesso!")
                        self.status_var.set("FFmpeg instalado - Pronto para conversão")
                    else:
                        self.log_message("✗ Falha na instalação do FFmpeg")
                        self.status_var.set("Erro na instalação do FFmpeg")
                except Exception as e:
                    self.log_message(f"✗ Erro na instalação do FFmpeg: {str(e)}")
                    self.status_var.set("Erro na instalação do FFmpeg")
                    messagebox.showwarning(
                        "Aviso", 
                        "Não foi possível instalar o FFmpeg automaticamente. "
                        "Instale manualmente para usar o conversor."
                    )
            else:
                self.log_message("✓ FFmpeg encontrado e pronto para uso")
                self.status_var.set("Pronto para conversão")
        
        # Executar verificação em thread separada
        threading.Thread(target=check_and_install, daemon=True).start()


def main():
    """
    Função principal para executar a aplicação
    """
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()