#!/usr/bin/env python3
"""
Script de Build para Video Converter
Cria um executável otimizado do aplicativo usando PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_directories():
    """Remove diretórios de build anteriores"""
    directories_to_clean = ['build', 'dist', '__pycache__']
    
    for directory in directories_to_clean:
        if os.path.exists(directory):
            print(f"🧹 Limpando diretório: {directory}")
            shutil.rmtree(directory)
    
    # Remover arquivos .spec antigos se existirem
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        print(f"🧹 Removendo arquivo spec: {spec_file}")
        spec_file.unlink()

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    try:
        import pyinstaller
        print(f"✅ PyInstaller {pyinstaller.__version__} encontrado")
    except ImportError:
        print("❌ PyInstaller não encontrado. Instalando...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    # Verificar dependências do projeto
    required_packages = ['requests', 'yt-dlp', 'google-api-python-client']
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} encontrado")
        except ImportError:
            print(f"❌ {package} não encontrado. Instale com: pip install {package}")
            return False
    
    return True

def build_executable():
    """Constrói o executável usando PyInstaller"""
    print("🔨 Construindo executável...")
    
    # Comando PyInstaller otimizado
    cmd = [
        'pyinstaller',
        '--onefile',                    # Arquivo único
        '--windowed',                   # Sem console
        '--name', 'VideoConverter',     # Nome do executável
        '--clean',                      # Limpar cache
        '--noconfirm',                  # Não pedir confirmação
        
        # Otimizações
        '--optimize', '2',              # Otimização Python
        '--strip',                      # Remover símbolos de debug
        
        # Incluir dados necessários
        '--add-data', 'video_converter_module;video_converter_module',
        '--add-data', 'requirements.txt;.',
        
        # Módulos ocultos importantes
        '--hidden-import', 'tkinter',
        '--hidden-import', 'tkinter.ttk',
        '--hidden-import', 'tkinter.filedialog',
        '--hidden-import', 'tkinter.messagebox',
        '--hidden-import', 'requests',
        '--hidden-import', 'yt_dlp',
        '--hidden-import', 'googleapiclient',
        '--hidden-import', 'googleapiclient.discovery',
        
        # Excluir módulos desnecessários
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'numpy',
        '--exclude-module', 'scipy',
        '--exclude-module', 'pandas',
        '--exclude-module', 'PIL',
        '--exclude-module', 'cv2',
        '--exclude-module', 'tensorflow',
        '--exclude-module', 'torch',
        '--exclude-module', 'PyQt5',
        '--exclude-module', 'PyQt6',
        
        'main_tkinter.py'               # Script principal
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build concluído com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro durante o build:")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def verify_executable():
    """Verifica se o executável foi criado corretamente"""
    exe_path = Path('dist') / 'VideoConverter.exe'
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✅ Executável criado: {exe_path}")
        print(f"📦 Tamanho: {size_mb:.1f} MB")
        
        # Verificar se o executável pode ser executado
        try:
            # Teste rápido (apenas verificar se inicia)
            result = subprocess.run([str(exe_path), '--help'], 
                                  capture_output=True, text=True, timeout=10)
            print("✅ Executável pode ser iniciado")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print("⚠️  Executável criado mas pode ter problemas de inicialização")
        except FileNotFoundError:
            print("❌ Executável não pode ser encontrado")
            return False
        
        return True
    else:
        print("❌ Executável não foi criado")
        return False

def create_portable_package():
    """Cria um pacote portável com o executável e arquivos necessários"""
    print("📦 Criando pacote portável...")
    
    package_dir = Path('VideoConverter_Portable')
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    
    # Copiar executável
    exe_source = Path('dist') / 'VideoConverter.exe'
    exe_dest = package_dir / 'VideoConverter.exe'
    shutil.copy2(exe_source, exe_dest)
    
    # Criar README para o pacote
    readme_content = """# Video Converter - Versão Portável

## Como usar:
1. Execute VideoConverter.exe
2. O aplicativo baixará automaticamente o FFmpeg se necessário
3. Selecione seus arquivos de vídeo e configure as opções de conversão

## Requisitos:
- Windows 10 ou superior
- Conexão com internet (para download do FFmpeg e vídeos do YouTube)

## Recursos:
- Conversão de vídeo para múltiplos formatos
- Download de vídeos do YouTube
- Interface gráfica intuitiva
- Suporte a aceleração por GPU (CUDA)

## Suporte:
Para problemas ou sugestões, consulte a documentação do projeto.
"""
    
    readme_path = package_dir / 'README.txt'
    readme_path.write_text(readme_content, encoding='utf-8')
    
    print(f"✅ Pacote portável criado em: {package_dir}")
    return True

def main():
    """Função principal do script de build"""
    print("🚀 Video Converter - Script de Build")
    print("=" * 50)
    
    # Verificar se estamos no diretório correto
    if not Path('main_tkinter.py').exists():
        print("❌ Erro: main_tkinter.py não encontrado!")
        print("Execute este script no diretório raiz do projeto.")
        return False
    
    # Etapas do build
    steps = [
        ("Limpando diretórios anteriores", clean_build_directories),
        ("Verificando dependências", check_dependencies),
        ("Construindo executável", build_executable),
        ("Verificando executável", verify_executable),
        ("Criando pacote portável", create_portable_package),
    ]
    
    for step_name, step_function in steps:
        print(f"\n📋 {step_name}...")
        try:
            if not step_function():
                print(f"❌ Falha na etapa: {step_name}")
                return False
        except Exception as e:
            print(f"❌ Erro na etapa '{step_name}': {e}")
            return False
    
    print("\n🎉 Build concluído com sucesso!")
    print("\n📁 Arquivos gerados:")
    print("   - dist/VideoConverter.exe (executável)")
    print("   - VideoConverter_Portable/ (pacote portável)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)