#!/usr/bin/env python3
"""
Video Converter - Aplicação Principal (Tkinter)
Conversor de vídeo com interface gráfica usando Tkinter
"""

import sys
from pathlib import Path

# Adicionar o diretório do módulo ao sys.path
sys.path.append(str(Path(__file__).parent / 'video_converter_module'))

import tkinter as tk
from tkinter import messagebox
from gui.main_window_tkinter import MainWindow


def main():
    """
    Função principal da aplicação
    """
    try:
        # Criar aplicação Tkinter
        root = tk.Tk()
        app = MainWindow(root)

        # Configurar fechamento da aplicação
        def on_closing():
            if messagebox.askokcancel("Sair", "Deseja realmente sair da aplicação?"):
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Iniciar loop principal
        root.mainloop()

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao iniciar a aplicação: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
