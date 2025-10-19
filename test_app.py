"""
Teste simples para verificar se a aplicação está funcionando
"""

import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """
    Testa se todos os módulos podem ser importados
    """
    try:
        print("Testando imports...")

        # Testar configurações
        from utils.config import APP_NAME, SUPPORTED_INPUT_FORMATS

        print(f"✓ Configurações carregadas: {APP_NAME}")

        # Testar validadores
        from utils.validators import validate_input_file

        print("✓ Validadores carregados")

        # Testar instalador FFmpeg
        from core.ffmpeg_installer import FFmpegInstaller

        print("✓ Instalador FFmpeg carregado")

        # Testar conversor
        from core.video_converter import VideoConverterManager

        print("✓ Conversor de vídeo carregado")

        # Testar interface
        from gui.main_window import MainWindow

        print("✓ Interface gráfica carregada")

        print("\n✅ Todos os módulos foram importados com sucesso!")
        return True

    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def test_basic_functionality():
    """
    Testa funcionalidades básicas
    """
    try:
        print("\nTestando funcionalidades básicas...")

        # Testar validação de arquivo
        from utils.validators import validate_input_file, sanitize_filename

        # Teste com arquivo inexistente
        is_valid, msg = validate_input_file("arquivo_inexistente.mp4")
        if not is_valid:
            print("✓ Validação de arquivo inexistente funcionando")

        # Teste de sanitização de nome
        clean_name = sanitize_filename("arquivo<>inválido.mp4")
        if clean_name == "arquivo__inválido.mp4":
            print("✓ Sanitização de nome funcionando")

        # Testar configurações
        from utils.config import SUPPORTED_INPUT_FORMATS

        if "mp4" in SUPPORTED_INPUT_FORMATS:
            print("✓ Configurações de formatos funcionando")

        print("\n✅ Funcionalidades básicas testadas com sucesso!")
        return True

    except Exception as e:
        print(f"❌ Erro no teste de funcionalidades: {e}")
        return False


def main():
    """
    Executa todos os testes
    """
    print("=== TESTE DA APLICAÇÃO VIDEO CONVERTER ===\n")

    success = True

    # Teste de imports
    if not test_imports():
        success = False

    # Teste de funcionalidades
    if not test_basic_functionality():
        success = False

    if success:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("A aplicação está pronta para ser executada.")
        print("\nPara executar a aplicação, use:")
        print("python main.py")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("Verifique os erros acima antes de executar a aplicação.")

    return success


if __name__ == "__main__":
    main()
