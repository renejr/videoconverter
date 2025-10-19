#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget de Atualização para a Interface Gráfica
Componente responsável por exibir notificações e gerenciar atualizações
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Dict, Any, Optional

from utils.updater import UpdateChecker, UpdateDownloader, restart_application


class UpdateWidget:
    """
    Widget responsável por exibir e gerenciar atualizações na interface
    """
    
    def __init__(self, parent_frame: tk.Widget, repository: str = "usuario/vidconv"):
        """
        Inicializa o widget de atualização
        
        Args:
            parent_frame: Frame pai onde o widget será inserido
            repository: Repositório GitHub no formato "usuario/repo"
        """
        self.parent_frame = parent_frame
        self.repository = repository
        self.update_frame = None
        self.update_button = None
        self.progress_bar = None
        self.status_label = None
        
        # Callbacks externos
        self.log_callback = None
        self.status_callback = None
        
        # Componentes do sistema de atualização
        self.update_checker = UpdateChecker(callback_update_available=self._on_update_available)
        self.update_downloader = UpdateDownloader(progress_callback=self._on_download_progress)
        
        # Estado atual
        self.current_release_info = None
        self.is_downloading = False
        
        # Inicia verificação automática
        self._start_automatic_checks()
    
    def _create_update_frame(self):
        """
        Cria o frame de atualização (só quando necessário)
        """
        if self.update_frame:
            return
            
        # Frame principal para atualização
        self.update_frame = tk.Frame(
            self.parent_frame,
            bg='#ff69b4',  # Rosa como mostrado na imagem
            relief='solid',
            bd=2
        )
        
        # Frame interno com padding
        inner_frame = tk.Frame(self.update_frame, bg='#ff69b4')
        inner_frame.pack(fill='both', expand=True, padx=5, pady=3)
        
        # Ícone de atualização
        update_icon = tk.Label(
            inner_frame,
            text="🔄",
            font=('Arial', 12),
            bg='#ff69b4',
            fg='white'
        )
        update_icon.pack(side='left', padx=(0, 5))
        
        # Label de status
        self.status_label = tk.Label(
            inner_frame,
            text="Atualização disponível!",
            font=('Arial', 9, 'bold'),
            bg='#ff69b4',
            fg='white'
        )
        self.status_label.pack(side='left', padx=(0, 10))
        
        # Botão de atualização
        self.update_button = tk.Button(
            inner_frame,
            text="Atualizar",
            font=('Arial', 8, 'bold'),
            bg='white',
            fg='#ff69b4',
            relief='raised',
            bd=1,
            padx=10,
            pady=2,
            command=self._on_update_clicked
        )
        self.update_button.pack(side='right', padx=(5, 0))
        
        # Barra de progresso (inicialmente oculta)
        self.progress_bar = ttk.Progressbar(
            inner_frame,
            mode='determinate',
            length=100
        )
        
        # Botão de fechar
        close_button = tk.Button(
            inner_frame,
            text="✕",
            font=('Arial', 8, 'bold'),
            bg='#ff69b4',
            fg='white',
            relief='flat',
            bd=0,
            padx=3,
            pady=0,
            command=self.hide_update_notification
        )
        close_button.pack(side='right')
    
    def show_update_notification(self, release_info: Dict[str, Any]):
        """
        Exibe a notificação de atualização
        
        Args:
            release_info: Informações da release disponível
        """
        self.current_release_info = release_info
        
        # Cria o frame se não existir
        self._create_update_frame()
        
        # Atualiza o texto com informações da versão
        version = release_info.get('tag_name', 'Nova versão')
        self.status_label.config(text=f"Atualização {version} disponível!")
        
        # Exibe o frame
        self.update_frame.pack(fill='x', padx=5, pady=2)
        
        # Adiciona tooltip com informações da release
        self._add_tooltip()
    
    def hide_update_notification(self):
        """
        Oculta a notificação de atualização
        """
        if self.update_frame:
            self.update_frame.pack_forget()
    
    def set_log_callback(self, callback):
        """
        Define callback para logging
        
        Args:
            callback: Função para logging
        """
        self.log_callback = callback
    
    def set_status_callback(self, callback):
        """
        Define callback para atualização de status
        
        Args:
            callback: Função para atualização de status
        """
        self.status_callback = callback
    
    def create_button(self, parent_frame, row=0, column=0, padx=5):
        """
        Cria um botão de atualização na interface
        
        Args:
            parent_frame: Frame pai onde o botão será criado
            row: Linha do grid
            column: Coluna do grid
            padx: Padding horizontal
        """
        self.update_btn = tk.Button(
            parent_frame,
            text="🔄 Verificar Atualizações",
            command=self.manual_check,
            font=('Arial', 9),
            bg='#f0f0f0',
            relief='raised',
            bd=1,
            padx=10,
            pady=2
        )
        self.update_btn.grid(row=row, column=column, padx=padx)
    
    def _add_tooltip(self):
        """
        Adiciona tooltip com informações da release
        """
        if not self.current_release_info:
            return
            
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            # Informações da release
            version = self.current_release_info.get('tag_name', 'N/A')
            name = self.current_release_info.get('name', 'Nova Atualização')
            published_at = self.current_release_info.get('published_at', '')
            body = self.current_release_info.get('body', 'Sem descrição disponível')
            
            # Formata a data
            if published_at:
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    published_at = date_obj.strftime('%d/%m/%Y')
                except:
                    published_at = published_at[:10]
            
            # Limita o tamanho da descrição
            if len(body) > 200:
                body = body[:200] + "..."
            
            tooltip_text = f"""Versão: {version}
Nome: {name}
Data: {published_at}

Descrição:
{body}"""
            
            label = tk.Label(
                tooltip,
                text=tooltip_text,
                background='lightyellow',
                relief='solid',
                borderwidth=1,
                font=('Arial', 9),
                justify='left',
                wraplength=300
            )
            label.pack()
            
            # Remove tooltip após 5 segundos
            tooltip.after(5000, tooltip.destroy)
        
        def hide_tooltip(event):
            pass
        
        # Adiciona eventos de mouse
        if self.status_label:
            self.status_label.bind('<Enter>', show_tooltip)
            self.status_label.bind('<Leave>', hide_tooltip)
    
    def _on_update_available(self, release_info: Dict[str, Any]):
        """
        Callback chamado quando uma atualização está disponível
        
        Args:
            release_info: Informações da release
        """
        # Executa na thread principal
        self.parent_frame.after(0, lambda: self.show_update_notification(release_info))
    
    def _on_update_clicked(self):
        """
        Callback chamado quando o botão de atualização é clicado
        """
        if self.is_downloading or not self.current_release_info:
            return
        
        # Confirma a atualização
        version = self.current_release_info.get('tag_name', 'nova versão')
        response = messagebox.askyesno(
            "Confirmar Atualização",
            f"Deseja baixar e instalar a {version}?\n\n"
            "O aplicativo será reiniciado após a instalação.",
            icon='question'
        )
        
        if response:
            self._start_update_process()
    
    def _start_update_process(self):
        """
        Inicia o processo de atualização em thread separada
        """
        self.is_downloading = True
        
        # Atualiza interface
        self.update_button.config(state='disabled', text='Baixando...')
        self.status_label.config(text='Baixando atualização...')
        
        # Log do início do processo
        if self.log_callback:
            self.log_callback("Iniciando processo de atualização...")
        
        # Atualiza status
        if self.status_callback:
            self.status_callback("Baixando atualização...")
        
        # Exibe barra de progresso
        self.progress_bar.pack(side='right', padx=(5, 5))
        self.progress_bar['value'] = 0
        
        # Inicia download em thread separada
        def download_and_install():
            try:
                # Baixa a atualização
                file_path = self.update_downloader.download_update(self.current_release_info)
                
                if file_path:
                    # Atualiza interface
                    self.parent_frame.after(0, lambda: self.status_label.config(text='Instalando...'))
                    self.parent_frame.after(0, lambda: self.progress_bar.config(mode='indeterminate'))
                    self.parent_frame.after(0, lambda: self.progress_bar.start())
                    
                    # Instala a atualização
                    success = self.update_downloader.install_update(file_path, self.current_release_info)
                    
                    if success:
                        # Sucesso - reinicia aplicação
                        self.parent_frame.after(0, self._on_update_success)
                    else:
                        # Erro na instalação
                        self.parent_frame.after(0, self._on_update_error)
                else:
                    # Erro no download
                    self.parent_frame.after(0, self._on_update_error)
                    
            except Exception as e:
                print(f"Erro durante atualização: {e}")
                self.parent_frame.after(0, self._on_update_error)
            finally:
                # Limpa arquivos temporários
                self.update_downloader.cleanup()
        
        threading.Thread(target=download_and_install, daemon=True).start()
    
    def _on_download_progress(self, progress: int):
        """
        Callback chamado durante o progresso do download
        
        Args:
            progress: Progresso em porcentagem (0-100)
        """
        if self.progress_bar:
            self.parent_frame.after(0, lambda: self.progress_bar.config(value=progress))
    
    def _on_update_success(self):
        """
        Callback chamado quando a atualização é bem-sucedida
        """
        self.progress_bar.stop()
        self.status_label.config(text='Atualização concluída!')
        
        # Log de sucesso
        if self.log_callback:
            self.log_callback("Atualização instalada com sucesso!")
        
        # Atualiza status
        if self.status_callback:
            self.status_callback("Atualização concluída!")
        
        # Pergunta se deve reiniciar agora
        response = messagebox.askyesno(
            "Atualização Concluída",
            "Atualização instalada com sucesso!\n\n"
            "Deseja reiniciar o aplicativo agora?",
            icon='info'
        )
        
        if response:
            restart_application()
        else:
            self.hide_update_notification()
    
    def _on_update_error(self):
        """
        Callback chamado quando há erro na atualização
        """
        self.is_downloading = False
        
        if self.progress_bar:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
        
        self.update_button.config(state='normal', text='Tentar Novamente')
        self.status_label.config(text='Erro na atualização')
        
        # Log de erro
        if self.log_callback:
            self.log_callback("Erro durante a atualização")
        
        # Atualiza status
        if self.status_callback:
            self.status_callback("Erro na atualização")
        
        messagebox.showerror(
            "Erro na Atualização",
            "Ocorreu um erro durante a atualização.\n\n"
            "Verifique sua conexão com a internet e tente novamente."
        )
    
    def _start_automatic_checks(self):
        """
        Inicia verificações automáticas de atualização
        """
        # Verificação na inicialização (após 5 segundos)
        self.parent_frame.after(5000, lambda: self.update_checker.check_for_updates())
        
        # Verificação periódica
        self.update_checker.start_periodic_check()
    
    def manual_check(self):
        """
        Executa verificação manual de atualizações
        """
        # Log da verificação manual
        if self.log_callback:
            self.log_callback("Verificando atualizações...")
        
        # Atualiza status
        if self.status_callback:
            self.status_callback("Verificando atualizações...")
        
        def check_in_thread():
            self.update_checker.check_for_updates(show_no_updates=True)
        
        threading.Thread(target=check_in_thread, daemon=True).start()
    
    def destroy(self):
        """
        Limpa recursos quando o widget é destruído
        """
        if self.update_checker:
            self.update_checker.stop_periodic_check()
        
        if self.update_downloader:
            self.update_downloader.cleanup()