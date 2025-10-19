#!/usr/bin/env python3
"""
🎬 Demonstração do Instalador VideoConverter
===========================================

Script de demonstração que mostra todas as funcionalidades
do instalador universal em ação, incluindo:
- Análise completa do sistema
- Detecção de componentes
- Simulação de instalação
- Interface visual com progress bars
- Relatórios detalhados
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any

# Adicionar diretório do instalador ao PATH
installer_dir = Path(__file__).parent
sys.path.insert(0, str(installer_dir))

from core.os_detector import OSDetector
from core.python_manager import PythonManager
from core.gpu_detector import GPUDetector
from core.cuda_installer import CUDAInstaller
from core.ffmpeg_manager import FFmpegManager
from utils.logger import Logger
from utils.progress import ProgressBar
from config.settings import InstallerSettings
from main_installer import VideoConverterInstaller


def print_banner():
    """Exibe banner da demonstração"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎬 VideoConverter - Instalador Universal                  ║
║                                                              ║
║    Demonstração das funcionalidades avançadas               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def demo_os_detection():
    """Demonstra detecção de sistema operacional"""
    print("\n🔍 DEMONSTRAÇÃO: Detecção de Sistema Operacional")
    print("-" * 60)

    # Criar progress bar para simulação
    progress = ProgressBar(total=100, description="Analisando sistema", style="modern")

    detector = OSDetector()

    # Simular análise progressiva
    progress.update(20, "Detectando OS...")
    time.sleep(0.5)

    os_info = detector.detect_os()
    progress.update(40, "Verificando arquitetura...")
    time.sleep(0.3)

    is_admin = detector.is_admin()
    progress.update(60, "Checando privilégios...")
    time.sleep(0.3)

    python_compat = detector.is_python_313_compatible()
    progress.update(80, "Verificando compatibilidade...")
    time.sleep(0.3)

    progress.update(100, "Análise completa!")
    progress.close()

    # Exibir resultados
    print(f"\n📋 Informações do Sistema:")
    print(f"   Sistema Operacional: {os_info['os']} {os_info['version']}")
    print(f"   Arquitetura: {os_info['architecture']}")
    print(f"   Privilégios Admin: {'✅ Sim' if is_admin else '❌ Não'}")
    print(f"   Python 3.13 Compatível: {'✅ Sim' if python_compat else '❌ Não'}")

    if os_info["os"] == "Linux":
        distro = os_info.get("distro", {})
        if distro:
            print(
                f"   Distribuição: {distro.get('name', 'Desconhecida')} {distro.get('version', '')}"
            )

        pkg_manager = detector.get_package_manager()
        if pkg_manager:
            print(f"   Gerenciador de Pacotes: {pkg_manager}")

    return os_info


def demo_python_detection():
    """Demonstra detecção de Python"""
    print("\n🐍 DEMONSTRAÇÃO: Detecção de Python")
    print("-" * 60)

    progress = ProgressBar(total=100, description="Analisando Python", style="classic")

    manager = PythonManager()

    # Simular detecção progressiva
    progress.update(25, "Procurando instalações...")
    time.sleep(0.5)

    installations = manager.detect_python_installations()
    progress.update(50, "Verificando versões...")
    time.sleep(0.4)

    current_version = manager.get_current_python_version()
    progress.update(75, "Checando compatibilidade...")
    time.sleep(0.3)

    is_compatible = manager.is_python_313_compatible()
    progress.update(100, "Análise completa!")
    progress.close()

    # Exibir resultados
    print(f"\n📋 Instalações Python Encontradas: {len(installations)}")

    for i, install in enumerate(installations[:5], 1):  # Mostrar até 5
        print(f"   {i}. Python {install.version}")
        print(f"      Executável: {install.executable}")
        print(f"      Localização: {install.path}")
        print(f"      Padrão: {'✅ Sim' if install.is_default else '❌ Não'}")
        print()

    if len(installations) > 5:
        print(f"   ... e mais {len(installations) - 5} instalações")

    print(f"📍 Versão Atual: {current_version}")
    print(f"🔧 Python 3.13 Compatível: {'✅ Sim' if is_compatible else '❌ Não'}")

    return installations


def demo_gpu_detection():
    """Demonstra detecção de GPU"""
    print("\n🎮 DEMONSTRAÇÃO: Detecção de GPU/CUDA")
    print("-" * 60)

    progress = ProgressBar(total=100, description="Analisando GPUs", style="gradient")

    detector = GPUDetector()

    # Simular detecção progressiva
    progress.update(20, "Detectando GPUs...")
    time.sleep(0.6)

    gpus = detector.detect_gpus()
    progress.update(50, "Verificando CUDA...")
    time.sleep(0.5)

    driver_version = detector.get_nvidia_driver_version()
    progress.update(80, "Analisando capacidades...")
    time.sleep(0.4)

    progress.update(100, "Análise completa!")
    progress.close()

    # Exibir resultados
    print(f"\n📋 GPUs Encontradas: {len(gpus)}")

    if not gpus:
        print("   ❌ Nenhuma GPU NVIDIA detectada")
        return []

    for i, gpu in enumerate(gpus, 1):
        print(f"\n   {i}. {gpu.name}")
        print(f"      Memória: {gpu.memory_mb:,} MB")
        print(f"      CUDA Compatível: {'✅ Sim' if gpu.cuda_compatible else '❌ Não'}")

        if gpu.cuda_compatible:
            print(f"      Compute Capability: {gpu.compute_capability}")
            print(
                f"      Versões CUDA Recomendadas: {', '.join(gpu.recommended_cuda_versions)}"
            )

    if driver_version:
        print(f"\n🔧 Driver NVIDIA: {driver_version}")

    # Mostrar melhor GPU
    if gpus:
        best_gpu = detector.get_best_gpu(gpus)
        if best_gpu:
            print(f"\n⭐ Melhor GPU para CUDA: {best_gpu.name}")

    return gpus


def demo_cuda_detection():
    """Demonstra detecção de CUDA"""
    print("\n⚡ DEMONSTRAÇÃO: Detecção de CUDA")
    print("-" * 60)

    progress = ProgressBar(total=100, description="Analisando CUDA", style="dots")

    installer = CUDAInstaller()

    # Simular detecção progressiva
    progress.update(30, "Procurando instalações CUDA...")
    time.sleep(0.5)

    cuda_installations = installer.detect_installed_cuda()
    progress.update(60, "Verificando versões...")
    time.sleep(0.4)

    best_version = installer.select_best_cuda_version()
    progress.update(90, "Analisando compatibilidade...")
    time.sleep(0.3)

    progress.update(100, "Análise completa!")
    progress.close()

    # Exibir resultados
    print(f"\n📋 Instalações CUDA Encontradas: {len(cuda_installations)}")

    if cuda_installations:
        for install in cuda_installations:
            print(f"   • CUDA {install.version}")
            print(f"     Localização: {install.path}")
            print(f"     Método: {install.detection_method}")
            print()
    else:
        print("   ❌ Nenhuma instalação CUDA detectada")

    if best_version:
        print(f"🎯 Versão CUDA Recomendada: {best_version}")
    else:
        print("⚠️  Nenhuma versão CUDA recomendada (GPU não compatível)")

    return cuda_installations


def demo_ffmpeg_detection():
    """Demonstra detecção de FFmpeg"""
    print("\n🎥 DEMONSTRAÇÃO: Detecção de FFmpeg")
    print("-" * 60)

    progress = ProgressBar(total=100, description="Analisando FFmpeg", style="bar")

    manager = FFmpegManager()

    # Simular detecção progressiva
    progress.update(25, "Procurando FFmpeg...")
    time.sleep(0.4)

    ffmpeg_installations = manager.detect_installed_ffmpeg()
    progress.update(50, "Verificando versões...")
    time.sleep(0.3)

    progress.update(75, "Checando funcionalidades...")
    time.sleep(0.3)

    progress.update(100, "Análise completa!")
    progress.close()

    # Exibir resultados
    print(f"\n📋 Instalações FFmpeg Encontradas: {len(ffmpeg_installations)}")

    if ffmpeg_installations:
        for install in ffmpeg_installations:
            print(f"   • FFmpeg {install.version}")
            print(f"     Executável: {install.ffmpeg_path}")
            if install.ffprobe_path:
                print(f"     FFprobe: {install.ffprobe_path}")
            print(f"     Localização: {install.location}")
            print()
    else:
        print("   ❌ FFmpeg não encontrado no sistema")

    return ffmpeg_installations


def demo_installation_planning():
    """Demonstra planejamento de instalação"""
    print("\n📋 DEMONSTRAÇÃO: Planejamento de Instalação")
    print("-" * 60)

    progress = ProgressBar(total=100, description="Criando plano", style="modern")

    installer = VideoConverterInstaller()

    # Simular planejamento progressivo
    progress.update(20, "Analisando sistema...")
    time.sleep(0.5)

    system_analysis = installer.analyze_system()
    progress.update(50, "Avaliando necessidades...")
    time.sleep(0.4)

    plan = installer.create_installation_plan(interactive=False)
    progress.update(80, "Otimizando plano...")
    time.sleep(0.3)

    progress.update(100, "Plano criado!")
    progress.close()

    # Exibir plano
    print(f"\n📋 Plano de Instalação Automático:")
    print(f"   Python 3.13: {'✅ Instalar' if plan.install_python else '❌ Pular'}")
    if plan.install_python:
        print(f"     Versão: {plan.python_version}")
        print(f"     Caminho: {plan.python_install_path}")

    print(f"   CUDA: {'✅ Instalar' if plan.install_cuda else '❌ Pular'}")
    if plan.install_cuda:
        print(f"     Versão: {plan.cuda_version}")
        print(f"     Caminho: {plan.cuda_install_path}")

    print(f"   FFmpeg: {'✅ Instalar' if plan.install_ffmpeg else '❌ Pular'}")
    if plan.install_ffmpeg:
        print(f"     Versão: {plan.ffmpeg_version}")
        print(f"     Caminho: {plan.ffmpeg_install_path}")

    print(f"\n🔧 Configurações:")
    print(f"   Modo Offline: {'✅ Sim' if plan.offline_mode else '❌ Não'}")
    print(f"   Usar Cache: {'✅ Sim' if plan.use_cache else '❌ Não'}")
    print(f"   Nível de Validação: {plan.validation_level.title()}")
    print(f"   Tempo Estimado: {plan.estimated_time_minutes:.1f} minutos")

    # Mostrar recomendações
    if system_analysis.get("recommendations"):
        print(f"\n💡 Recomendações:")
        for rec in system_analysis["recommendations"][:3]:
            print(f"   • {rec}")

    return plan


def demo_settings_management():
    """Demonstra gerenciamento de configurações"""
    print("\n⚙️  DEMONSTRAÇÃO: Gerenciamento de Configurações")
    print("-" * 60)

    settings = InstallerSettings()

    print(f"📋 Configurações Padrão:")
    print(f"   Python Padrão: {settings.python.default_version}")
    print(f"   CUDA Padrão: {settings.cuda.default_version}")
    print(f"   Cache Habilitado: {'✅ Sim' if settings.cache_enabled else '❌ Não'}")
    print(f"   Requer Admin: {'✅ Sim' if settings.require_admin else '❌ Não'}")
    print(f"   Timeout Download: {settings.network.download_timeout}s")
    print(f"   Tentativas: {settings.network.max_retries}")

    # Validar configurações
    errors = settings.validate_config()
    print(f"\n🔍 Validação: {'✅ OK' if not errors else f'❌ {len(errors)} erros'}")

    if errors:
        for error in errors[:3]:
            print(f"   • {error}")

    # Mostrar alguns URLs
    print(f"\n🔗 URLs de Download:")
    python_url = settings.get_python_url("3.13.0", "windows", "x64")
    print(f"   Python: {python_url[:60]}...")

    # Mostrar caminhos
    print(f"\n📁 Caminhos de Instalação:")
    python_path = settings.get_install_path("python", "windows")
    print(f"   Python: {python_path}")

    return settings


def demo_comprehensive_analysis():
    """Demonstra análise completa do sistema"""
    print("\n🔍 DEMONSTRAÇÃO: Análise Completa do Sistema")
    print("-" * 60)

    progress = ProgressBar(total=100, description="Análise completa", style="gradient")

    installer = VideoConverterInstaller()

    # Simular análise completa
    progress.update(15, "Detectando sistema operacional...")
    time.sleep(0.3)

    progress.update(30, "Analisando Python...")
    time.sleep(0.4)

    progress.update(45, "Detectando GPUs...")
    time.sleep(0.5)

    progress.update(60, "Verificando CUDA...")
    time.sleep(0.4)

    progress.update(75, "Procurando FFmpeg...")
    time.sleep(0.3)

    progress.update(90, "Gerando recomendações...")
    time.sleep(0.3)

    analysis = installer.analyze_system()
    progress.update(100, "Análise completa!")
    progress.close()

    # Exibir resumo da análise
    print(f"\n📊 Resumo da Análise:")

    # Sistema
    os_info = analysis["os_info"]
    print(
        f"   Sistema: {os_info['os']} {os_info['version']} ({os_info['architecture']})"
    )

    # Python
    python_installs = analysis["python_installations"]
    print(f"   Python: {len(python_installs)} instalações encontradas")

    # GPU
    gpu_info = analysis["gpu_info"]
    print(f"   GPUs: {len(gpu_info)} NVIDIA detectadas")

    # CUDA
    cuda_installs = analysis["cuda_installations"]
    print(f"   CUDA: {len(cuda_installs)} instalações encontradas")

    # FFmpeg
    ffmpeg_installs = analysis["ffmpeg_installations"]
    print(f"   FFmpeg: {len(ffmpeg_installs)} instalações encontradas")

    # Compatibilidade
    compatibility = analysis["compatibility"]
    print(f"\n✅ Compatibilidade:")
    print(
        f"   Python 3.13: {'✅ Compatível' if compatibility['python_313'] else '❌ Incompatível'}"
    )
    print(
        f"   CUDA: {'✅ Suportado' if compatibility['cuda_capable'] else '❌ Não suportado'}"
    )
    print(
        f"   Admin: {'✅ Disponível' if compatibility['has_admin'] else '❌ Necessário'}"
    )

    # Recomendações
    recommendations = analysis["recommendations"]
    if recommendations:
        print(f"\n💡 Principais Recomendações:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec}")

    return analysis


def interactive_demo():
    """Demonstração interativa"""
    print("\n🎮 MODO INTERATIVO")
    print("-" * 60)

    demos = {
        "1": ("Detecção de Sistema", demo_os_detection),
        "2": ("Detecção de Python", demo_python_detection),
        "3": ("Detecção de GPU", demo_gpu_detection),
        "4": ("Detecção de CUDA", demo_cuda_detection),
        "5": ("Detecção de FFmpeg", demo_ffmpeg_detection),
        "6": ("Planejamento de Instalação", demo_installation_planning),
        "7": ("Configurações", demo_settings_management),
        "8": ("Análise Completa", demo_comprehensive_analysis),
        "9": ("Todas as Demonstrações", None),
    }

    while True:
        print(f"\n📋 Escolha uma demonstração:")
        for key, (name, _) in demos.items():
            print(f"   {key}. {name}")
        print(f"   0. Sair")

        choice = input(f"\n👉 Sua escolha: ").strip()

        if choice == "0":
            print(f"\n👋 Obrigado por usar a demonstração!")
            break

        elif choice == "9":
            print(f"\n🎬 Executando todas as demonstrações...")
            run_all_demos()

        elif choice in demos and demos[choice][1]:
            print(f"\n🎬 Executando: {demos[choice][0]}")
            try:
                demos[choice][1]()
            except KeyboardInterrupt:
                print(f"\n⚠️  Demonstração cancelada")
            except Exception as e:
                print(f"\n❌ Erro na demonstração: {e}")

        else:
            print(f"\n❌ Opção inválida!")

        input(f"\n📱 Pressione Enter para continuar...")


def run_all_demos():
    """Executa todas as demonstrações"""
    demos = [
        ("Detecção de Sistema", demo_os_detection),
        ("Detecção de Python", demo_python_detection),
        ("Detecção de GPU", demo_gpu_detection),
        ("Detecção de CUDA", demo_cuda_detection),
        ("Detecção de FFmpeg", demo_ffmpeg_detection),
        ("Configurações", demo_settings_management),
        ("Planejamento de Instalação", demo_installation_planning),
        ("Análise Completa", demo_comprehensive_analysis),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        print(f"\n{'='*60}")
        print(f"🎬 DEMONSTRAÇÃO {i}/{len(demos)}: {name}")
        print(f"{'='*60}")

        try:
            demo_func()
        except KeyboardInterrupt:
            print(f"\n⚠️  Demonstração cancelada pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro na demonstração: {e}")

        if i < len(demos):
            time.sleep(1)  # Pausa entre demonstrações


def main():
    """Função principal da demonstração"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Demonstração do Instalador VideoConverter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python demo.py                    # Modo interativo
  python demo.py --all              # Todas as demonstrações
  python demo.py --quick            # Demonstrações rápidas
  python demo.py --analysis         # Apenas análise completa
        """,
    )

    parser.add_argument(
        "--all", action="store_true", help="Executar todas as demonstrações"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Demonstrações rápidas essenciais"
    )
    parser.add_argument(
        "--analysis", action="store_true", help="Apenas análise completa do sistema"
    )
    parser.add_argument("--no-banner", action="store_true", help="Não exibir banner")

    args = parser.parse_args()

    try:
        # Banner
        if not args.no_banner:
            print_banner()

        if args.analysis:
            demo_comprehensive_analysis()

        elif args.quick:
            print("🚀 Demonstrações Rápidas")
            print("-" * 60)
            demo_os_detection()
            demo_python_detection()
            demo_comprehensive_analysis()

        elif args.all:
            run_all_demos()

        else:
            interactive_demo()

        print(f"\n🎉 Demonstração concluída!")

    except KeyboardInterrupt:
        print(f"\n\n⚠️  Demonstração cancelada pelo usuário")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Erro durante demonstração: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
