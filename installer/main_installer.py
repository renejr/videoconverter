#!/usr/bin/env python3
"""
🚀 VideoConverter - Instalador Universal Inteligente
===================================================

Instalador automático que configura todo o ambiente necessário:
- Python 3.13
- NVIDIA GPU/CUDA (se compatível)
- FFmpeg/FFprobe
- Dependências do projeto
- Configuração de ambiente

Suporta: Windows, Linux, macOS
Funcionalidades:
- Detecção automática do sistema
- Instalação customizada
- Validação em 3 níveis
- Interface CLI com progress bars
- Logs detalhados
- Instalação offline (cache)
"""

import os
import sys
import time
import argparse
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile
import shutil

# Adicionar diretório do instalador ao PATH
installer_dir = Path(__file__).parent
sys.path.insert(0, str(installer_dir))

from core.os_detector import OSDetector
from core.python_manager import PythonManager
from core.gpu_detector import GPUDetector
from core.cuda_installer import CUDAInstaller
from core.ffmpeg_manager import FFmpegManager
from utils.logger import Logger
from utils.progress import ProgressBar, installation_progress_bar
from config.settings import InstallerSettings


@dataclass
class InstallationPlan:
    """Plano de instalação"""

    install_python: bool = False
    python_version: str = "3.13.0"
    install_cuda: bool = False
    cuda_version: Optional[str] = None
    install_ffmpeg: bool = False
    ffmpeg_version: str = "latest"
    custom_paths: Dict[str, str] = None
    offline_mode: bool = False
    validation_level: str = "advanced"  # basic, advanced, benchmark

    def __post_init__(self):
        if self.custom_paths is None:
            self.custom_paths = {}


@dataclass
class InstallationResult:
    """Resultado da instalação"""

    success: bool
    components_installed: List[str]
    components_failed: List[str]
    installation_time: float
    system_info: Dict[str, Any]
    validation_results: Dict[str, bool]
    recommendations: List[str]
    errors: List[str]


class VideoConverterInstaller:
    """
    Instalador principal do VideoConverter

    Orquestra todos os componentes de instalação:
    - Detecção do sistema
    - Planejamento da instalação
    - Execução coordenada
    - Validação completa
    """

    def __init__(self, config_file: str = None, cache_dir: str = None):
        """
        Inicializa instalador principal

        Args:
            config_file: Arquivo de configuração personalizada
            cache_dir: Diretório de cache para downloads
        """
        # Configurar logging principal
        self.logger = Logger("VideoConverterInstaller")

        # Carregar configurações
        self.settings = InstallerSettings()
        if config_file and os.path.exists(config_file):
            self.settings.load_from_file(config_file)

        # Inicializar componentes
        self.os_detector = OSDetector()
        self.python_manager = PythonManager(cache_dir=cache_dir)
        self.gpu_detector = GPUDetector()
        self.cuda_installer = CUDAInstaller(cache_dir=cache_dir)
        self.ffmpeg_manager = FFmpegManager(cache_dir=cache_dir)

        # Informações do sistema
        self.system_info = self.os_detector.detect()
        self.cache_dir = cache_dir or tempfile.mkdtemp(prefix="vidconv_installer_")

        # Estado da instalação
        self.installation_plan: Optional[InstallationPlan] = None
        self.start_time = 0

        self.logger.info(f"Instalador VideoConverter inicializado")
        self.logger.info(f"Sistema: {self.system_info.name} {self.system_info.version}")
        self.logger.info(f"Arquitetura: {self.system_info.architecture}")

    def analyze_system(self) -> Dict[str, Any]:
        """
        Analisa o sistema e detecta componentes existentes

        Returns:
            Dict[str, Any]: Análise completa do sistema
        """
        self.logger.info("🔍 Analisando sistema...")

        analysis = {
            "system": {
                "os_info": self.system_info,
                "compatibility": {
                    "python_313": True,
                    "cuda_support": False,
                    "ffmpeg_support": True,
                },
            },
            "components": {
                "python_installations": [],
                "gpu_info": None,
                "cuda_installations": [],
                "ffmpeg_installations": [],
            },
            "recommendations": [],
        }

        # Progress bar para análise
        analysis_steps = 5
        progress_bar = ProgressBar(
            total=analysis_steps,
            description="Analisando sistema",
            style="modern",
            color="analysis",
        )

        try:
            # 1. Verificar Python
            progress_bar.update(1, description="Verificando Python")
            analysis["components"][
                "python_installations"
            ] = self.python_manager.get_current_python()

            # Verificar compatibilidade Python 3.13
            if self.python_manager.needs_python_install():
                analysis["system"]["compatibility"]["python_313"] = False
                analysis["recommendations"].append(
                    "Sistema pode não suportar Python 3.13"
                )

            # 2. Verificar GPU
            progress_bar.update(2, description="Detectando GPU")
            gpus = self.gpu_detector.detect_gpus()
            if gpus:
                analysis["components"]["gpu_info"] = self.gpu_detector.get_best_gpu(
                    gpus
                )
                analysis["system"]["compatibility"]["cuda_support"] = analysis[
                    "components"
                ]["gpu_info"].is_cuda_capable

            # 3. Verificar CUDA
            progress_bar.update(3, description="Verificando CUDA")
            analysis["components"][
                "cuda_installations"
            ] = self.cuda_installer.detect_installed_cuda()

            # 4. Verificar FFmpeg
            progress_bar.update(4, description="Verificando FFmpeg")
            analysis["components"][
                "ffmpeg_installations"
            ] = self.ffmpeg_manager.detect_installed_ffmpeg()

            # 5. Gerar recomendações
            progress_bar.update(5, description="Gerando recomendações")
            analysis["recommendations"].extend(self._generate_recommendations(analysis))

            progress_bar.finish("Análise concluída")

        except Exception as e:
            progress_bar.cancel(f"Erro na análise: {e}")
            self.logger.error(f"Erro durante análise do sistema: {e}")
            analysis["error"] = str(e)

        return analysis

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recommendations = []

        # Python
        python_info = analysis["components"]["python_installations"]
        python_313_found = python_info and python_info.version.startswith("3.13")

        if not python_313_found:
            recommendations.append("Instalar Python 3.13 para melhor compatibilidade")

        # CUDA
        if analysis["system"]["compatibility"]["cuda_support"]:
            cuda_installed = any(
                inst.is_complete
                for inst in analysis["components"]["cuda_installations"]
            )

            if not cuda_installed:
                recommendations.append("Instalar CUDA para aceleração GPU")
            else:
                # Verificar se versão é compatível com GPU
                gpu_info = analysis["components"]["gpu_info"]
                if gpu_info and gpu_info.recommended_cuda_versions:
                    installed_versions = [
                        inst.version
                        for inst in analysis["components"]["cuda_installations"]
                    ]
                    compatible_installed = any(
                        any(
                            rec_ver.startswith(inst_ver[:4])
                            for rec_ver in gpu_info.recommended_cuda_versions
                        )
                        for inst_ver in installed_versions
                    )

                    if not compatible_installed:
                        recommendations.append(
                            "Atualizar CUDA para versão compatível com GPU"
                        )

        # FFmpeg
        ffmpeg_found = any(
            inst.is_complete for inst in analysis["components"]["ffmpeg_installations"]
        )

        if not ffmpeg_found:
            recommendations.append("Instalar FFmpeg para processamento de vídeo")

        return recommendations

    def create_installation_plan(
        self, interactive: bool = True, custom_config: Dict[str, Any] = None
    ) -> InstallationPlan:
        """
        Cria plano de instalação

        Args:
            interactive: Se deve perguntar ao usuário
            custom_config: Configuração personalizada

        Returns:
            InstallationPlan: Plano de instalação
        """
        self.logger.info("📋 Criando plano de instalação...")

        # Analisar sistema primeiro
        analysis = self.analyze_system()

        # Configuração padrão
        plan = InstallationPlan()

        if custom_config:
            # Aplicar configuração personalizada
            for key, value in custom_config.items():
                if hasattr(plan, key):
                    setattr(plan, key, value)

        elif interactive:
            # Modo interativo
            plan = self._interactive_planning(analysis)

        else:
            # Modo automático - instalar o que for necessário
            plan = self._automatic_planning(analysis)

        self.installation_plan = plan

        # Log do plano
        self.logger.info("📋 Plano de instalação criado:")
        self.logger.info(f"  Python 3.13: {'✅' if plan.install_python else '❌'}")
        self.logger.info(
            f"  CUDA: {'✅' if plan.install_cuda else '❌'} {plan.cuda_version or ''}"
        )
        self.logger.info(f"  FFmpeg: {'✅' if plan.install_ffmpeg else '❌'}")
        self.logger.info(f"  Validação: {plan.validation_level}")
        self.logger.info(f"  Offline: {'✅' if plan.offline_mode else '❌'}")

        return plan

    def _interactive_planning(self, analysis: Dict[str, Any]) -> InstallationPlan:
        """Planejamento interativo com usuário"""
        plan = InstallationPlan()

        print("\n🎯 Configuração de Instalação Interativa")
        print("=" * 50)

        # Python
        python_info = analysis["components"]["python_installations"]
        python_313_found = python_info and python_info.version.startswith("3.13")

        if not python_313_found:
            response = input("\n📦 Instalar Python 3.13? [S/n]: ").strip().lower()
            plan.install_python = response in ["", "s", "sim", "y", "yes"]
        else:
            print("\n✅ Python 3.13 já instalado")

        # CUDA
        if analysis["system"]["compatibility"]["cuda_support"]:
            cuda_installed = any(
                inst.is_complete
                for inst in analysis["components"]["cuda_installations"]
            )

            if not cuda_installed:
                response = (
                    input("\n🚀 Instalar CUDA para aceleração GPU? [S/n]: ")
                    .strip()
                    .lower()
                )
                plan.install_cuda = response in ["", "s", "sim", "y", "yes"]

                if plan.install_cuda:
                    # Sugerir versão
                    gpu_info = analysis["components"]["gpu_info"]
                    if gpu_info and gpu_info.recommended_cuda_versions:
                        suggested = gpu_info.recommended_cuda_versions[0]
                        version = input(f"   Versão CUDA [{suggested}]: ").strip()
                        plan.cuda_version = version if version else suggested
            else:
                print("\n✅ CUDA já instalado")
        else:
            print("\n❌ GPU NVIDIA não detectada - CUDA não será instalado")

        # FFmpeg
        ffmpeg_found = any(
            inst.is_complete for inst in analysis["components"]["ffmpeg_installations"]
        )

        if not ffmpeg_found:
            response = input("\n🎬 Instalar FFmpeg? [S/n]: ").strip().lower()
            plan.install_ffmpeg = response in ["", "s", "sim", "y", "yes"]
        else:
            print("\n✅ FFmpeg já instalado")

        # Configurações avançadas
        print("\n⚙️  Configurações Avançadas:")

        # Validação
        print("   Níveis de validação:")
        print("   1. Básica (arquivos existem)")
        print("   2. Avançada (testes funcionais)")
        print("   3. Benchmark (testes de performance)")

        validation_choice = input("   Escolha [2]: ").strip()
        validation_map = {"1": "basic", "2": "advanced", "3": "benchmark"}
        plan.validation_level = validation_map.get(validation_choice, "advanced")

        # Modo offline
        response = (
            input("\n💾 Habilitar modo offline (cache downloads)? [s/N]: ")
            .strip()
            .lower()
        )
        plan.offline_mode = response in ["s", "sim", "y", "yes"]

        return plan

    def _automatic_planning(self, analysis: Dict[str, Any]) -> InstallationPlan:
        """Planejamento automático baseado na análise"""
        plan = InstallationPlan()

        # Python 3.13
        python_info = analysis["components"]["python_installations"]
        python_313_found = python_info and python_info.version.startswith("3.13")
        plan.install_python = not python_313_found

        # CUDA
        if analysis["system"]["compatibility"]["cuda_support"]:
            cuda_installed = any(
                inst.is_complete
                for inst in analysis["components"]["cuda_installations"]
            )
            plan.install_cuda = not cuda_installed

            if plan.install_cuda:
                gpu_info = analysis["components"]["gpu_info"]
                if gpu_info and gpu_info.recommended_cuda_versions:
                    plan.cuda_version = gpu_info.recommended_cuda_versions[0]

        # FFmpeg
        ffmpeg_found = any(
            inst.is_complete for inst in analysis["components"]["ffmpeg_installations"]
        )
        plan.install_ffmpeg = not ffmpeg_found

        # Configurações padrão para modo automático
        plan.validation_level = "advanced"
        plan.offline_mode = False

        return plan

    def execute_installation(self, plan: InstallationPlan = None) -> InstallationResult:
        """
        Executa instalação conforme plano

        Args:
            plan: Plano de instalação (usa o atual se None)

        Returns:
            InstallationResult: Resultado da instalação
        """
        if plan is None:
            plan = self.installation_plan

        if plan is None:
            raise ValueError("Nenhum plano de instalação definido")

        self.start_time = time.time()

        self.logger.info("🚀 Iniciando instalação...")

        # Resultado da instalação
        result = InstallationResult(
            success=False,
            components_installed=[],
            components_failed=[],
            installation_time=0,
            system_info=self.system_info,
            validation_results={},
            recommendations=[],
            errors=[],
        )

        # Calcular total de componentes
        total_components = sum(
            [plan.install_python, plan.install_cuda, plan.install_ffmpeg]
        )

        if total_components == 0:
            self.logger.info("✅ Nenhum componente precisa ser instalado")
            result.success = True
            result.installation_time = time.time() - self.start_time
            return result

        # Progress bar principal
        main_progress = ProgressBar(
            total=total_components,
            description="Instalação VideoConverter",
            style="modern",
            color="install",
        )

        component_count = 0

        try:
            # 1. Instalar Python 3.13
            if plan.install_python:
                component_count += 1
                main_progress.update(
                    component_count, description="Instalando Python 3.13"
                )

                if self._install_python(plan):
                    result.components_installed.append("Python 3.13")
                    self.logger.success("✅ Python 3.13 instalado")
                else:
                    result.components_failed.append("Python 3.13")
                    result.errors.append("Falha na instalação do Python 3.13")
                    self.logger.error("❌ Falha na instalação do Python 3.13")

            # 2. Instalar CUDA
            if plan.install_cuda:
                component_count += 1
                main_progress.update(
                    component_count, description=f"Instalando CUDA {plan.cuda_version}"
                )

                if self._install_cuda(plan):
                    result.components_installed.append(f"CUDA {plan.cuda_version}")
                    self.logger.success(f"✅ CUDA {plan.cuda_version} instalado")
                else:
                    result.components_failed.append(f"CUDA {plan.cuda_version}")
                    result.errors.append(
                        f"Falha na instalação do CUDA {plan.cuda_version}"
                    )
                    self.logger.error(
                        f"❌ Falha na instalação do CUDA {plan.cuda_version}"
                    )

            # 3. Instalar FFmpeg
            if plan.install_ffmpeg:
                component_count += 1
                main_progress.update(component_count, description="Instalando FFmpeg")

                if self._install_ffmpeg(plan):
                    result.components_installed.append("FFmpeg")
                    self.logger.success("✅ FFmpeg instalado")
                else:
                    result.components_failed.append("FFmpeg")
                    result.errors.append("Falha na instalação do FFmpeg")
                    self.logger.error("❌ Falha na instalação do FFmpeg")

            # Finalizar progress bar principal
            if result.components_failed:
                main_progress.cancel(
                    f"Instalação concluída com {len(result.components_failed)} falha(s)"
                )
            else:
                main_progress.finish("Instalação concluída com sucesso")

            # 4. Validação
            self.logger.info("🔍 Executando validação...")
            result.validation_results = self._validate_installation(plan)

            # 5. Gerar recomendações finais
            result.recommendations = self._generate_final_recommendations(result)

            # Determinar sucesso geral
            result.success = len(result.components_failed) == 0
            result.installation_time = time.time() - self.start_time

            # Log final
            if result.success:
                self.logger.success(
                    f"🎉 Instalação concluída com sucesso em {result.installation_time:.1f}s"
                )
            else:
                self.logger.error(
                    f"⚠️  Instalação concluída com falhas em {result.installation_time:.1f}s"
                )

        except Exception as e:
            main_progress.cancel(f"Erro crítico: {e}")
            self.logger.error(f"Erro crítico durante instalação: {e}")
            result.errors.append(f"Erro crítico: {e}")
            result.installation_time = time.time() - self.start_time

        return result

    def _install_python(self, plan: InstallationPlan) -> bool:
        """Instala Python 3.13"""
        try:
            # Verificar se já está instalado
            current_python = self.python_manager.get_current_python()
            if current_python and current_python.version.startswith("3.13"):
                self.logger.info("Python 3.13 já instalado")
                return True

            # Baixar Python 3.13
            installer_path = self.python_manager.download_python(plan.python_version)
            if not installer_path:
                return False

            # Instalar Python
            success = self.python_manager.install_python(
                installer_path, plan.python_version
            )

            return success

        except Exception as e:
            self.logger.error(f"Erro na instalação do Python: {e}")
            return False

    def _install_cuda(self, plan: InstallationPlan) -> bool:
        """Instala CUDA"""
        try:
            if not plan.cuda_version:
                # Selecionar melhor versão automaticamente
                plan.cuda_version = self.cuda_installer.select_best_cuda_version()

                if not plan.cuda_version:
                    self.logger.error(
                        "Não foi possível determinar versão CUDA compatível"
                    )
                    return False

            # Verificar se já está instalado
            installations = self.cuda_installer.detect_installed_cuda()
            cuda_found = any(
                inst.version.startswith(plan.cuda_version[:4]) and inst.is_complete
                for inst in installations
            )

            if cuda_found:
                self.logger.info(f"CUDA {plan.cuda_version} já instalado")
                return True

            # Baixar CUDA
            installer_path = self.cuda_installer.download_cuda(plan.cuda_version)
            if not installer_path:
                return False

            # Instalar CUDA
            success = self.cuda_installer.install_cuda(
                installer_path, plan.cuda_version
            )

            return success

        except Exception as e:
            self.logger.error(f"Erro na instalação do CUDA: {e}")
            return False

    def _install_ffmpeg(self, plan: InstallationPlan) -> bool:
        """Instala FFmpeg"""
        try:
            # Verificar se já está instalado
            installations = self.ffmpeg_manager.detect_installed_ffmpeg()
            ffmpeg_found = any(inst.is_complete for inst in installations)

            if ffmpeg_found:
                self.logger.info("FFmpeg já instalado")
                return True

            # Obter informações da versão mais recente
            build_info = self.ffmpeg_manager.get_latest_ffmpeg_info()
            if not build_info:
                return False

            # Baixar FFmpeg
            archive_path = self.ffmpeg_manager.download_ffmpeg(build_info)
            if not archive_path:
                return False

            # Instalar FFmpeg
            success = self.ffmpeg_manager.install_ffmpeg(archive_path, build_info)

            return success

        except Exception as e:
            self.logger.error(f"Erro na instalação do FFmpeg: {e}")
            return False

    def _validate_installation(self, plan: InstallationPlan) -> Dict[str, bool]:
        """
        Valida instalação conforme nível especificado

        Args:
            plan: Plano de instalação

        Returns:
            Dict[str, bool]: Resultados da validação
        """
        validation_results = {}

        # Validação básica - verificar se arquivos existem
        if plan.validation_level in ["basic", "advanced", "benchmark"]:
            validation_results.update(self._basic_validation(plan))

        # Validação avançada - testes funcionais
        if plan.validation_level in ["advanced", "benchmark"]:
            validation_results.update(self._advanced_validation(plan))

        # Benchmarks de performance
        if plan.validation_level == "benchmark":
            validation_results.update(self._benchmark_validation(plan))

        return validation_results

    def _basic_validation(self, plan: InstallationPlan) -> Dict[str, bool]:
        """Validação básica - verificar existência de arquivos"""
        results = {}

        if plan.install_python:
            python_path = shutil.which("python") or shutil.which("python3")
            results["python_executable"] = python_path is not None

        if plan.install_cuda:
            nvcc_path = shutil.which("nvcc")
            results["cuda_compiler"] = nvcc_path is not None

        if plan.install_ffmpeg:
            ffmpeg_path = shutil.which("ffmpeg")
            ffprobe_path = shutil.which("ffprobe")
            results["ffmpeg_executable"] = ffmpeg_path is not None
            results["ffprobe_executable"] = ffprobe_path is not None

        return results

    def _advanced_validation(self, plan: InstallationPlan) -> Dict[str, bool]:
        """Validação avançada - testes funcionais"""
        results = {}

        if plan.install_python:
            results["python_version"] = self.python_manager.verify_installation(
                plan.python_version
            )

        if plan.install_cuda:
            results["cuda_functionality"] = self.cuda_installer.verify_installation(
                plan.cuda_version
            )

        if plan.install_ffmpeg:
            # Teste básico de funcionalidade FFmpeg
            try:
                import subprocess

                result = subprocess.run(
                    ["ffmpeg", "-version"], capture_output=True, timeout=10
                )
                results["ffmpeg_functionality"] = result.returncode == 0
            except Exception:
                results["ffmpeg_functionality"] = False

        return results

    def _benchmark_validation(self, plan: InstallationPlan) -> Dict[str, bool]:
        """Validação com benchmarks de performance"""
        results = {}

        # Benchmark Python
        if plan.install_python:
            try:
                import subprocess
                import time

                # Teste simples de performance Python
                start_time = time.time()
                result = subprocess.run(
                    ["python", "-c", "import time; sum(i*i for i in range(100000))"],
                    capture_output=True,
                    timeout=30,
                )

                execution_time = time.time() - start_time
                results["python_performance"] = (
                    result.returncode == 0 and execution_time < 10
                )

            except Exception:
                results["python_performance"] = False

        # Benchmark CUDA (se disponível)
        if plan.install_cuda:
            try:
                import subprocess

                # Teste básico CUDA
                result = subprocess.run(
                    ["nvcc", "--version"], capture_output=True, timeout=10
                )

                results["cuda_performance"] = result.returncode == 0

            except Exception:
                results["cuda_performance"] = False

        # Benchmark FFmpeg
        if plan.install_ffmpeg:
            try:
                import subprocess
                import tempfile

                # Criar arquivo de teste pequeno
                with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                    test_file = f.name

                # Teste de conversão simples
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-f",
                        "lavfi",
                        "-i",
                        "testsrc=duration=1:size=320x240:rate=1",
                        "-t",
                        "1",
                        "-y",
                        test_file.replace(".txt", ".mp4"),
                    ],
                    capture_output=True,
                    timeout=30,
                )

                results["ffmpeg_performance"] = result.returncode == 0

                # Limpeza
                try:
                    os.unlink(test_file)
                    os.unlink(test_file.replace(".txt", ".mp4"))
                except:
                    pass

            except Exception:
                results["ffmpeg_performance"] = False

        return results

    def _generate_final_recommendations(self, result: InstallationResult) -> List[str]:
        """Gera recomendações finais baseadas no resultado"""
        recommendations = []

        if result.components_failed:
            recommendations.append("Revisar logs de erro para componentes que falharam")
            recommendations.append("Verificar privilégios administrativos")
            recommendations.append(
                "Tentar instalação manual dos componentes que falharam"
            )

        if result.success:
            recommendations.append(
                "Reiniciar terminal/sistema para aplicar mudanças de PATH"
            )
            recommendations.append("Testar VideoConverter com um arquivo de exemplo")

            # Recomendações específicas por validação
            validation_failed = [
                k for k, v in result.validation_results.items() if not v
            ]
            if validation_failed:
                recommendations.append(
                    f"Verificar componentes com falha na validação: {', '.join(validation_failed)}"
                )

        return recommendations

    def generate_report(self, result: InstallationResult) -> str:
        """
        Gera relatório detalhado da instalação

        Args:
            result: Resultado da instalação

        Returns:
            str: Relatório formatado
        """
        report = []
        report.append("🎯 RELATÓRIO DE INSTALAÇÃO - VIDEOCONVERTER")
        report.append("=" * 60)
        report.append("")

        # Informações do sistema
        report.append("📋 SISTEMA:")
        report.append(f"   OS: {result.system_info.name} {result.system_info.version}")
        report.append(f"   Arquitetura: {result.system_info.architecture}")
        report.append("")

        # Status geral
        status_icon = "✅" if result.success else "❌"
        report.append(
            f"📊 STATUS GERAL: {status_icon} {'SUCESSO' if result.success else 'FALHA'}"
        )
        report.append(f"   Tempo de instalação: {result.installation_time:.1f}s")
        report.append("")

        # Componentes instalados
        if result.components_installed:
            report.append("✅ COMPONENTES INSTALADOS:")
            for component in result.components_installed:
                report.append(f"   • {component}")
            report.append("")

        # Componentes que falharam
        if result.components_failed:
            report.append("❌ COMPONENTES COM FALHA:")
            for component in result.components_failed:
                report.append(f"   • {component}")
            report.append("")

        # Resultados de validação
        if result.validation_results:
            report.append("🔍 VALIDAÇÃO:")
            for test, passed in result.validation_results.items():
                icon = "✅" if passed else "❌"
                report.append(f"   {icon} {test}")
            report.append("")

        # Erros
        if result.errors:
            report.append("⚠️  ERROS:")
            for error in result.errors:
                report.append(f"   • {error}")
            report.append("")

        # Recomendações
        if result.recommendations:
            report.append("💡 RECOMENDAÇÕES:")
            for rec in result.recommendations:
                report.append(f"   • {rec}")
            report.append("")

        report.append("=" * 60)
        report.append("🚀 VideoConverter Installer - Concluído")

        return "\n".join(report)

    def cleanup(self):
        """Limpa arquivos temporários"""
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                self.logger.debug("Cache limpo")
        except Exception as e:
            self.logger.warning(f"Erro ao limpar cache: {e}")


def main():
    """Função principal do instalador"""
    parser = argparse.ArgumentParser(
        description="VideoConverter - Instalador Universal Inteligente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main_installer.py                    # Modo interativo
  python main_installer.py --auto             # Modo automático
  python main_installer.py --config config.json  # Usar configuração
  python main_installer.py --offline          # Modo offline
  python main_installer.py --validate-only    # Apenas validar
        """,
    )

    parser.add_argument(
        "--auto", action="store_true", help="Modo automático (sem interação)"
    )
    parser.add_argument("--config", type=str, help="Arquivo de configuração JSON")
    parser.add_argument(
        "--cache-dir", type=str, help="Diretório de cache personalizado"
    )
    parser.add_argument(
        "--offline", action="store_true", help="Modo offline (usar cache)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Apenas validar instalação existente",
    )
    parser.add_argument("--report", type=str, help="Salvar relatório em arquivo")
    parser.add_argument("--verbose", action="store_true", help="Log detalhado")

    args = parser.parse_args()

    # Banner
    print("🚀 VideoConverter - Instalador Universal Inteligente")
    print("=" * 60)
    print("Configurando ambiente completo para processamento de vídeo")
    print("Suporte: Windows, Linux, macOS")
    print("=" * 60)
    print()

    try:
        # Inicializar instalador
        installer = VideoConverterInstaller(
            config_file=args.config, cache_dir=args.cache_dir
        )

        if args.verbose:
            installer.logger.set_level("DEBUG")

        # Modo apenas validação
        if args.validate_only:
            print("🔍 Validando instalação existente...")
            analysis = installer.analyze_system()

            # Mostrar resultados
            print("\n📋 Análise do Sistema:")
            python_info = analysis["python_installations"]
            python_313_ok = python_info and python_info.version.startswith("3.13")
            print(f"   Python 3.13: {'✅' if python_313_ok else '❌'}")
            print(f"   CUDA: {'✅' if analysis['cuda_installations'] else '❌'}")
            print(f"   FFmpeg: {'✅' if analysis['ffmpeg_installations'] else '❌'}")

            if analysis["recommendations"]:
                print("\n💡 Recomendações:")
                for rec in analysis["recommendations"]:
                    print(f"   • {rec}")

            return

        # Criar plano de instalação
        custom_config = {}
        if args.offline:
            custom_config["offline_mode"] = True

        plan = installer.create_installation_plan(
            interactive=not args.auto,
            custom_config=custom_config if custom_config else None,
        )

        # Executar instalação
        result = installer.execute_installation(plan)

        # Gerar e mostrar relatório
        report = installer.generate_report(result)
        print("\n" + report)

        # Salvar relatório se solicitado
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n📄 Relatório salvo em: {args.report}")

        # Limpeza
        installer.cleanup()

        # Código de saída
        sys.exit(0 if result.success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Instalação cancelada pelo usuário")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
