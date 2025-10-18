#!/usr/bin/env python3
"""
Teste específico para verificar se o erro do FFmpeg foi corrigido
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ffmpeg_installer import FFmpegInstaller

def test_ffmpeg_installer():
    """
    Testa se o FFmpegInstaller tem todos os métodos necessários
    """
    print("=== Teste do FFmpegInstaller ===")
    
    try:
        # Criar instância do instalador
        installer = FFmpegInstaller()
        print("✓ FFmpegInstaller criado com sucesso")
        
        # Verificar se tem o método install_ffmpeg
        if hasattr(installer, 'install_ffmpeg'):
            print("✓ Método install_ffmpeg encontrado")
        else:
            print("✗ Método install_ffmpeg NÃO encontrado")
            return False
        
        # Verificar se tem o método is_ffmpeg_installed
        if hasattr(installer, 'is_ffmpeg_installed'):
            print("✓ Método is_ffmpeg_installed encontrado")
        else:
            print("✗ Método is_ffmpeg_installed NÃO encontrado")
            return False
        
        # Verificar se FFmpeg está instalado
        is_installed = installer.is_ffmpeg_installed()
        print(f"✓ Status do FFmpeg: {'Instalado' if is_installed else 'Não instalado'}")
        
        # Verificar se NÃO tem o método install (que causava o erro)
        if hasattr(installer, 'install'):
            print("⚠ Método install ainda existe (pode causar confusão)")
        else:
            print("✓ Método install não existe (correto)")
        
        print("✓ Todos os testes do FFmpegInstaller passaram!")
        return True
        
    except Exception as e:
        print(f"✗ Erro no teste do FFmpegInstaller: {str(e)}")
        return False

def test_gui_import():
    """
    Testa se a GUI pode ser importada sem erros
    """
    print("\n=== Teste de Importação da GUI ===")
    
    try:
        from gui.main_window_tkinter import MainWindow
        print("✓ MainWindow importado com sucesso")
        return True
    except Exception as e:
        print(f"✗ Erro na importação da GUI: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testando correção do erro do FFmpeg...\n")
    
    # Executar testes
    test1 = test_ffmpeg_installer()
    test2 = test_gui_import()
    
    # Resultado final
    print(f"\n=== RESULTADO FINAL ===")
    if test1 and test2:
        print("✓ TODOS OS TESTES PASSARAM! O erro foi corrigido.")
    else:
        print("✗ Alguns testes falharam. Verifique os erros acima.")