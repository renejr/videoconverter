#!/usr/bin/env python3
"""
Conversor de Vídeos - Aplicação Principal
Conversor de formatos de vídeo com interface gráfica PyQt6
Suporte a formatos modernos, transparência, controle de FPS e dimensões
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Adicionar o diretório atual ao path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import VideoConverterWindow


def main():
    """
    Função principal da aplicação
    Inicializa a interface gráfica e executa o loop principal
    """
    # Criar aplicação PyQt6
    app = QApplication(sys.argv)
    app.setApplicationName("Conversor de Vídeos")
    app.setApplicationVersion("1.0.0")
    
    # Configurar estilo da aplicação
    app.setStyle('Fusion')
    
    # Criar e mostrar janela principal
    window = VideoConverterWindow()
    window.show()
    
    # Executar loop principal
    sys.exit(app.exec())


if __name__ == "__main__":
    main()