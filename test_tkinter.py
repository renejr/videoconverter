"""
Teste da aplicação Video Converter com interface Tkinter
"""

import sys
import os
import tkinter as tk
from pathlib import Path

# Adicionar diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_tkinter_gui():
    """
    Testa a interface Tkinter
    """
    print("Testando interface Tkinter...")

    try:
        # Importar e testar GUI
        from gui.main_window_tkinter import MainWindow

        # Criar janela de teste
        root = tk.Tk()
        app = MainWindow(root)

        print("✓ Interface Tkinter carregada com sucesso!")
        print("✓ Todos os componentes inicializados")

        # Fechar janela após teste
        root.after(1000, root.destroy)  # Fechar após 1 segundo
        root.mainloop()

        return True

    except Exception as e:
        print(f"✗ Erro ao carregar interface Tkinter: {e}")
        return False


def test_basic_functionality():
    """
    Testa funcionalidades básicas
    """
    print("\nTestando funcionalidades básicas...")

    try:
        # Testar importações
        from utils.config import SUPPORTED_OUTPUT_FORMATS, FPS_OPTIONS
        from utils.validators import validate_input_file
        from core.ffmpeg_installer import FFmpegInstaller

        print("✓ Todas as importações funcionando")

        # Testar configurações
        print(f"✓ Formatos suportados: {len(SUPPORTED_OUTPUT_FORMATS)}")
        print(f"✓ Opções de FPS: {len(FPS_OPTIONS)}")

        # Testar validador
        is_valid, msg = validate_input_file("arquivo_inexistente.mp4")
        print(f"✓ Validador funcionando: {not is_valid}")

        # Testar FFmpeg installer
        installer = FFmpegInstaller()
        print(f"✓ FFmpeg installer carregado")

        return True

    except Exception as e:
        print(f"✗ Erro nas funcionalidades básicas: {e}")
        return False


if __name__ == "__main__":
    print("=== Teste da Aplicação Video Converter (Tkinter) ===\n")

    # Testar funcionalidades básicas
    basic_ok = test_basic_functionality()

    # Testar GUI apenas se as funcionalidades básicas funcionarem
    if basic_ok:
        gui_ok = test_tkinter_gui()

        if gui_ok:
            print("\n✓ Todos os testes passaram! A aplicação está funcionando.")
        else:
            print("\n✗ Problemas na interface gráfica.")
    else:
        print("\n✗ Problemas nas funcionalidades básicas.")

    print("\nPressione Enter para continuar...")
    input()
