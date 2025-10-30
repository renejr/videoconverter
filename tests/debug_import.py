import sys
import os

# Garante que o diretório raiz do projeto esteja no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from gui.main_window_tkinter import VideoConverterApp
    print("Importação bem-sucedida!")
    print(f"Tipo do objeto importado: {type(VideoConverterApp)}")
except Exception as e:
    print(f"Falha na importação: {e}")