#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para o sistema de atualizações
Testa todos os componentes do sistema de atualização automática
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.updater import UpdateChecker, UpdateDownloader
from gui.update_widget import UpdateWidget


class UpdateTestApp:
    """
    Aplicação de teste para o sistema de atualizações
    """
    
    def __init__(self):
        """
        Inicializa a aplicação de teste
        """
        self.root = tk.Tk()
        self.root.title("Teste do Sistema de Atualizações")
        self.root.geometry("800x600")
        
        self.setup_ui()
        self.setup_update_system()
    
    def setup_ui(self):
        """
        Configura a interface do usuário
        """
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="Sistema de Atualizações - Teste", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame de controles
        controls_frame = ttk.LabelFrame(main_frame, text="Controles", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botões de teste
        ttk.Button(controls_frame, text="Verificar Atualizações", 
                  command=self.test_check_updates).grid(row=0, column=0, padx=5)
        
        ttk.Button(controls_frame, text="Simular Download", 
                  command=self.test_download).grid(row=0, column=1, padx=5)
        
        ttk.Button(controls_frame, text="Testar Widget", 
                  command=self.test_widget).grid(row=0, column=2, padx=5)
        
        ttk.Button(controls_frame, text="Limpar Log", 
                  command=self.clear_log).grid(row=0, column=3, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Pronto para teste")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                font=('Arial', 10, 'italic'))
        status_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Log de atividades
        log_frame = ttk.LabelFrame(main_frame, text="Log de Atividades", padding="10")
        log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame para o widget de atualização
        self.widget_frame = ttk.LabelFrame(main_frame, text="Widget de Atualização", padding="10")
        self.widget_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configurar redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def setup_update_system(self):
        """
        Configura o sistema de atualizações
        """
        # Componentes do sistema
        self.update_checker = UpdateChecker(callback_update_available=self.on_update_available)
        self.update_downloader = UpdateDownloader(progress_callback=self.on_download_progress)
        
        # Widget de atualização
        self.update_widget = UpdateWidget(self.widget_frame, repository="usuario/vidconv")
        self.update_widget.set_log_callback(self.log)
        self.update_widget.set_status_callback(self.set_status)
        
        # Cria botão do widget
        self.update_widget.create_button(self.widget_frame, row=0, column=0)
        
        self.log("Sistema de atualizações inicializado")
    
    def log(self, message):
        """
        Adiciona mensagem ao log
        
        Args:
            message: Mensagem para adicionar
        """
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Adiciona ao log de forma thread-safe
        self.root.after(0, lambda: self._add_to_log(log_message))
    
    def _add_to_log(self, message):
        """
        Adiciona mensagem ao log (thread-safe)
        
        Args:
            message: Mensagem para adicionar
        """
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
    
    def set_status(self, status):
        """
        Atualiza o status
        
        Args:
            status: Novo status
        """
        self.root.after(0, lambda: self.status_var.set(status))
    
    def clear_log(self):
        """
        Limpa o log de atividades
        """
        self.log_text.delete(1.0, tk.END)
        self.log("Log limpo")
    
    def test_check_updates(self):
        """
        Testa a verificação de atualizações
        """
        self.log("Iniciando teste de verificação de atualizações...")
        self.set_status("Verificando atualizações...")
        
        def check_in_thread():
            try:
                self.update_checker.check_for_updates(show_no_updates=True)
                self.log("Teste de verificação concluído")
            except Exception as e:
                self.log(f"Erro no teste de verificação: {e}")
            finally:
                self.set_status("Teste de verificação concluído")
        
        threading.Thread(target=check_in_thread, daemon=True).start()
    
    def test_download(self):
        """
        Testa o sistema de download (simulação)
        """
        self.log("Iniciando teste de download (simulação)...")
        self.set_status("Testando download...")
        
        def simulate_download():
            try:
                # Simula progresso de download
                for i in range(0, 101, 10):
                    time.sleep(0.2)
                    self.log(f"Progresso do download: {i}%")
                    self.on_download_progress(i)
                
                self.log("Teste de download concluído com sucesso")
            except Exception as e:
                self.log(f"Erro no teste de download: {e}")
            finally:
                self.set_status("Teste de download concluído")
        
        threading.Thread(target=simulate_download, daemon=True).start()
    
    def test_widget(self):
        """
        Testa o widget de atualização
        """
        self.log("Testando widget de atualização...")
        
        # Simula uma atualização disponível
        fake_release = {
            'tag_name': 'v2.0.0',
            'name': 'Versão 2.0.0 - Teste',
            'body': 'Esta é uma versão de teste para demonstrar o sistema de atualizações.',
            'assets': [
                {
                    'name': 'vidconv-v2.0.0-windows.exe',
                    'browser_download_url': 'https://github.com/usuario/vidconv/releases/download/v2.0.0/vidconv-v2.0.0-windows.exe'
                }
            ]
        }
        
        self.update_widget.show_update_notification(fake_release)
        self.log("Widget de atualização exibido com dados de teste")
    
    def on_update_available(self, release_info):
        """
        Callback chamado quando uma atualização está disponível
        
        Args:
            release_info: Informações da release
        """
        version = release_info.get('tag_name', 'Desconhecida')
        self.log(f"Atualização disponível: {version}")
        self.set_status(f"Atualização {version} disponível")
    
    def on_download_progress(self, progress):
        """
        Callback chamado durante o progresso do download
        
        Args:
            progress: Progresso em porcentagem (0-100)
        """
        self.set_status(f"Download: {progress}%")
    
    def run(self):
        """
        Executa a aplicação de teste
        """
        self.log("Aplicação de teste iniciada")
        self.log("Use os botões acima para testar diferentes funcionalidades")
        self.log("O widget de atualização está integrado na parte inferior")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log("Aplicação interrompida pelo usuário")
        finally:
            # Cleanup
            if hasattr(self, 'update_widget'):
                self.update_widget.destroy()


def main():
    """
    Função principal
    """
    print("Iniciando teste do sistema de atualizações...")
    
    try:
        app = UpdateTestApp()
        app.run()
    except Exception as e:
        print(f"Erro ao executar teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()