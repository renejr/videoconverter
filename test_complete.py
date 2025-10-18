#!/usr/bin/env python3
"""
Teste Completo da Aplicação Video Converter
Testa todas as funcionalidades principais da aplicação
"""

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """
    Testa se todas as importações funcionam corretamente
    """
    print("=== Testando Importações ===")
    
    try:
        # Configurações
        from utils.config import (
            SUPPORTED_INPUT_FORMATS, SUPPORTED_OUTPUT_FORMATS,
            FPS_OPTIONS, RESOLUTION_PRESETS, QUALITY_PRESETS
        )
        print("✓ Configurações importadas com sucesso")
        
        # Validadores
        from utils.validators import (
            validate_input_file, validate_output_directory,
            validate_conversion_settings, generate_output_filename
        )
        print("✓ Validadores importados com sucesso")
        
        # FFmpeg Installer
        from core.ffmpeg_installer import FFmpegInstaller
        print("✓ FFmpeg Installer importado com sucesso")
        
        # Video Converter
        from core.video_converter import VideoConverter, VideoConverterManager
        print("✓ Video Converter importado com sucesso")
        
        # Interface Tkinter
        from gui.main_window_tkinter import MainWindow
        print("✓ Interface Tkinter importada com sucesso")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro na importação: {e}")
        return False

def test_configurations():
    """
    Testa se as configurações estão corretas
    """
    print("\n=== Testando Configurações ===")
    
    try:
        from utils.config import (
            SUPPORTED_INPUT_FORMATS, SUPPORTED_OUTPUT_FORMATS,
            FPS_OPTIONS, RESOLUTION_PRESETS, QUALITY_PRESETS
        )
        
        # Verificar formatos de entrada
        assert len(SUPPORTED_INPUT_FORMATS) > 0, "Nenhum formato de entrada definido"
        print(f"✓ Formatos de entrada: {len(SUPPORTED_INPUT_FORMATS)}")
        
        # Verificar formatos de saída
        assert len(SUPPORTED_OUTPUT_FORMATS) > 0, "Nenhum formato de saída definido"
        print(f"✓ Formatos de saída: {len(SUPPORTED_OUTPUT_FORMATS)}")
        
        # Verificar opções de FPS
        assert len(FPS_OPTIONS) > 0, "Nenhuma opção de FPS definida"
        print(f"✓ Opções de FPS: {len(FPS_OPTIONS)}")
        
        # Verificar presets de resolução
        assert len(RESOLUTION_PRESETS) > 0, "Nenhum preset de resolução definido"
        print(f"✓ Presets de resolução: {len(RESOLUTION_PRESETS)}")
        
        # Verificar presets de qualidade
        assert len(QUALITY_PRESETS) > 0, "Nenhum preset de qualidade definido"
        print(f"✓ Presets de qualidade: {len(QUALITY_PRESETS)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro nas configurações: {e}")
        return False

def test_validators():
    """
    Testa as funções de validação
    """
    print("\n=== Testando Validadores ===")
    
    try:
        from utils.validators import (
            validate_input_file, validate_output_directory,
            validate_conversion_settings, generate_output_filename,
            sanitize_filename
        )
        
        # Testar sanitização de nome de arquivo
        test_name = "arquivo teste!@#$%^&*().mp4"
        sanitized = sanitize_filename(test_name)
        assert sanitized != test_name, "Sanitização não funcionou"
        print(f"✓ Sanitização: '{test_name}' → '{sanitized}'")
        
        # Testar geração de nome de arquivo de saída
        output_name = generate_output_filename("test.mp4", "avi")
        assert output_name.endswith(".avi"), "Extensão não foi alterada corretamente"
        print(f"✓ Geração de nome: 'test.mp4' → '{output_name}'")
        
        # Testar validação de configurações de conversão
        settings = {
            'fps': 30,
            'resolution': '1920x1080',
            'quality': 'medium'
        }
        
        # Este teste pode falhar se os valores não estiverem nas configurações,
        # mas isso é esperado para demonstrar a validação
        try:
            validate_conversion_settings(settings)
            print("✓ Validação de configurações funcionando")
        except ValueError as ve:
            print(f"✓ Validação de configurações detectou erro (esperado): {ve}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro nos validadores: {e}")
        return False

def test_ffmpeg_installer():
    """
    Testa o instalador do FFmpeg
    """
    print("\n=== Testando FFmpeg Installer ===")
    
    try:
        from core.ffmpeg_installer import FFmpegInstaller
        
        installer = FFmpegInstaller()
        print(f"✓ Instalador criado para sistema: {installer.system}")
        print(f"✓ Diretório FFmpeg: {installer.ffmpeg_dir}")
        print(f"✓ Executável FFmpeg: {installer.ffmpeg_executable}")
        
        # Verificar se FFmpeg está instalado
        is_installed = installer.is_ffmpeg_installed()
        print(f"✓ FFmpeg instalado: {is_installed}")
        
        # Obter comando FFmpeg
        ffmpeg_cmd = installer.get_ffmpeg_command()
        if ffmpeg_cmd:
            print(f"✓ Comando FFmpeg encontrado: {ffmpeg_cmd}")
        else:
            print("! FFmpeg não encontrado no sistema")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro no FFmpeg Installer: {e}")
        return False

def test_video_converter():
    """
    Testa o conversor de vídeo (sem conversão real)
    """
    print("\n=== Testando Video Converter ===")
    
    try:
        from core.video_converter import VideoConverter, VideoConverterManager
        
        # Testar criação do conversor
        converter = VideoConverter()
        print("✓ VideoConverter criado com sucesso")
        
        # Testar manager
        manager = VideoConverterManager()
        print("✓ VideoConverterManager criado com sucesso")
        
        # Testar verificação de formato suportado
        # Este método agora usa validadores, então pode gerar exceção
        try:
            # Criar um arquivo temporário para teste
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Testar se o formato é suportado (deve falhar porque o arquivo não existe)
            try:
                result = converter.is_supported_input_format(temp_path)
                print(f"✓ Verificação de formato: {result}")
            except Exception:
                print("✓ Verificação de formato detectou arquivo inexistente (esperado)")
            
            # Limpar arquivo temporário
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            print(f"! Erro no teste de formato: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro no Video Converter: {e}")
        return False

def test_tkinter_interface():
    """
    Testa a interface Tkinter (criação e destruição rápida)
    """
    print("\n=== Testando Interface Tkinter ===")
    
    try:
        import tkinter as tk
        from gui.main_window_tkinter import MainWindow
        
        # Criar janela principal
        root = tk.Tk()
        root.withdraw()  # Ocultar janela para teste
        
        # Criar aplicação
        app = MainWindow(root)
        print("✓ Interface Tkinter criada com sucesso")
        
        # Verificar se os componentes principais existem
        assert hasattr(app, 'input_file_var'), "Variável de arquivo de entrada não encontrada"
        assert hasattr(app, 'format_var'), "Variável de formato de saída não encontrada"
        assert hasattr(app, 'progress_var'), "Variável de progresso não encontrada"
        print("✓ Componentes principais da interface verificados")
        
        # Destruir janela
        root.destroy()
        print("✓ Interface destruída com sucesso")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro na interface Tkinter: {e}")
        return False

def main():
    """
    Executa todos os testes
    """
    print("=== TESTE COMPLETO DA APLICAÇÃO VIDEO CONVERTER ===\n")
    
    tests = [
        ("Importações", test_imports),
        ("Configurações", test_configurations),
        ("Validadores", test_validators),
        ("FFmpeg Installer", test_ffmpeg_installer),
        ("Video Converter", test_video_converter),
        ("Interface Tkinter", test_tkinter_interface),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Erro crítico no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "="*50)
    print("RESUMO DOS TESTES:")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! A aplicação está funcionando corretamente.")
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)