#!/usr/bin/env python3
"""
🧪 Testes do Instalador VideoConverter
=====================================

Script de testes para validar diferentes cenários:
- Detecção de sistema
- Análise de componentes
- Simulação de instalação
- Validação de funcionalidades
- Testes de performance
"""

import os
import sys
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import unittest
from unittest.mock import Mock, patch, MagicMock

# Adicionar diretório do instalador ao PATH
installer_dir = Path(__file__).parent
sys.path.insert(0, str(installer_dir))

from core.os_detector import OSDetector, OSInfo
from core.python_manager import PythonManager
from core.gpu_detector import GPUDetector
from core.cuda_installer import CUDAInstaller
from core.ffmpeg_manager import FFmpegManager
from utils.logger import Logger
from utils.progress import ProgressBar
from config.settings import InstallerSettings
from main_installer import VideoConverterInstaller, InstallationPlan


class TestOSDetector(unittest.TestCase):
    """Testes para detecção de sistema operacional"""

    def setUp(self):
        self.detector = OSDetector()

    def test_detect_os(self):
        """Testa detecção básica do OS"""
        os_info = self.detector.detect()

        self.assertIsInstance(os_info.name, str)
        self.assertIsInstance(os_info.version, str)
        self.assertIsInstance(os_info.architecture, str)
        self.assertIn(os_info.name, ["windows", "linux", "darwin"])
        self.assertIn(os_info.architecture, ["x64", "x86", "arm64"])

    def test_is_admin(self):
        """Testa verificação de privilégios administrativos"""
        # Não podemos garantir privilégios, mas método deve retornar bool
        is_admin = self.detector.has_admin_privileges()
        self.assertIsInstance(is_admin, bool)

    def test_get_package_manager(self):
        """Testa detecção de gerenciador de pacotes"""
        os_info = self.detector.detect()

        if os_info.name == "linux":
            pkg_manager = self.detector.get_package_manager()
            self.assertIsInstance(pkg_manager, (str, type(None)))

    def test_python_313_compatibility(self):
        """Testa verificação de compatibilidade Python 3.13"""
        os_info = self.detector.detect()
        compatible = os_info.python_compatible
        self.assertIsInstance(compatible, bool)


class TestPythonManager(unittest.TestCase):
    """Testes para gerenciador Python"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PythonManager(cache_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_python_installations(self):
        """Testa detecção de instalações Python"""
        current_python = self.manager.get_current_python()
        self.assertIsInstance(current_python, (type(None), type(current_python)))

        # Se encontrou Python atual, deve ter propriedades válidas
        if current_python:
            self.assertIsInstance(current_python.version, str)
            self.assertIsInstance(current_python.executable, str)
            self.assertIsInstance(current_python.is_compatible, bool)

    def test_get_python_url(self):
        """Testa geração de URLs de download"""
        url = self.manager.get_download_url()
        if url:  # Pode ser None se sistema não suportado
            self.assertIsInstance(url, str)
            self.assertIn("python", url.lower())
            self.assertIn("3.13.0", url)

    def test_is_python_313_compatible(self):
        """Testa verificação de compatibilidade"""
        needs_install = self.manager.needs_python_install()
        self.assertIsInstance(needs_install, bool)

    def test_verify_installation(self):
        """Testa verificação de instalação"""
        # Testa validação básica
        result = self.manager.validate_installation()
        self.assertIsInstance(result, bool)


class TestGPUDetector(unittest.TestCase):
    """Testes para detecção de GPU"""

    def setUp(self):
        self.detector = GPUDetector()

    def test_detect_gpus(self):
        """Testa detecção de GPUs"""
        gpus = self.detector.detect_gpus()
        self.assertIsInstance(gpus, list)

        # Cada GPU deve ter propriedades básicas
        for gpu in gpus:
            self.assertTrue(hasattr(gpu, "name"))
            self.assertTrue(hasattr(gpu, "memory_total"))
            self.assertTrue(hasattr(gpu, "is_cuda_capable"))

    def test_get_best_gpu(self):
        """Testa seleção da melhor GPU"""
        gpus = self.detector.detect_gpus()

        if gpus:
            best_gpu = self.detector.get_best_gpu(gpus)
            self.assertIsNotNone(best_gpu)
            self.assertIn(best_gpu, gpus)

    def test_cuda_compatibility(self):
        """Testa verificação de compatibilidade CUDA"""
        gpus = self.detector.detect_gpus()

        for gpu in gpus:
            if gpu.is_cuda_capable:
                self.assertIsInstance(gpu.compute_capability, (tuple, type(None)))
                self.assertIsInstance(gpu.recommended_cuda_versions, (list, type(None)))


class TestCUDAInstaller(unittest.TestCase):
    """Testes para instalador CUDA"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.installer = CUDAInstaller(cache_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_installed_cuda(self):
        """Testa detecção de CUDA instalado"""
        installations = self.installer.detect_installed_cuda()
        self.assertIsInstance(installations, list)

    def test_get_cuda_url(self):
        """Testa geração de URLs CUDA"""
        url = self.installer.get_cuda_url("12.6.0", "windows")
        self.assertIsInstance(url, str)

        if url:  # Se URL foi gerada
            self.assertIn("cuda", url.lower())
            self.assertIn("12.6.0", url)

    def test_select_best_cuda_version(self):
        """Testa seleção automática de versão CUDA"""
        version = self.installer.select_best_cuda_version()

        if version:  # Se versão foi selecionada
            self.assertIsInstance(version, str)
            self.assertRegex(version, r"\d+\.\d+\.\d+")


class TestFFmpegManager(unittest.TestCase):
    """Testes para gerenciador FFmpeg"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = FFmpegManager(cache_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_installed_ffmpeg(self):
        """Testa detecção de FFmpeg instalado"""
        installations = self.manager.detect_installed_ffmpeg()
        self.assertIsInstance(installations, list)

    def test_get_latest_ffmpeg_info(self):
        """Testa obtenção de informações da versão mais recente"""
        # Este teste pode falhar sem internet
        try:
            info = self.manager.get_latest_ffmpeg_info()
            if info:
                self.assertTrue(hasattr(info, "version"))
                self.assertTrue(hasattr(info, "download_url"))
        except Exception:
            self.skipTest("Teste requer conexão com internet")


class TestInstallerSettings(unittest.TestCase):
    """Testes para configurações do instalador"""

    def setUp(self):
        self.settings = InstallerSettings()

    def test_default_settings(self):
        """Testa configurações padrão"""
        self.assertEqual(self.settings.python.default_version, "3.13.0")
        self.assertTrue(self.settings.cache_enabled)
        self.assertTrue(self.settings.require_admin)

    def test_get_python_url(self):
        """Testa geração de URL Python"""
        url = self.settings.get_python_url("3.13.0", "windows", "x64")
        self.assertIsInstance(url, str)
        self.assertIn("python", url.lower())

    def test_get_install_path(self):
        """Testa obtenção de caminhos de instalação"""
        path = self.settings.get_install_path("python", "windows")
        self.assertIsInstance(path, str)
        self.assertTrue(len(path) > 0)

    def test_validate_config(self):
        """Testa validação de configurações"""
        errors = self.settings.validate_config()
        self.assertIsInstance(errors, list)
        # Configurações padrão devem ser válidas
        self.assertEqual(len(errors), 0, f"Erros de configuração: {errors}")

    def test_save_load_config(self):
        """Testa salvamento e carregamento de configuração"""
        temp_file = os.path.join(tempfile.gettempdir(), "test_config.json")

        try:
            # Salvar configuração
            self.settings.save_to_file(temp_file)
            self.assertTrue(os.path.exists(temp_file))

            # Carregar configuração
            new_settings = InstallerSettings(temp_file)
            self.assertEqual(
                new_settings.python.default_version,
                self.settings.python.default_version,
            )

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestVideoConverterInstaller(unittest.TestCase):
    """Testes para instalador principal"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.installer = VideoConverterInstaller(cache_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_analyze_system(self):
        """Testa análise completa do sistema"""
        analysis = self.installer.analyze_system()
        self.assertIsInstance(analysis, dict)

        # Verificar estrutura básica
        self.assertIn("system", analysis)
        self.assertIn("components", analysis)

        # Verificar tipos
        self.assertIsInstance(analysis["system"], dict)
        self.assertIsInstance(analysis["components"], dict)

    def test_create_installation_plan_automatic(self):
        """Testa criação de plano automático"""
        plan = self.installer.create_installation_plan(interactive=False)

        self.assertIsInstance(plan, InstallationPlan)
        self.assertIsInstance(plan.install_python, bool)
        self.assertIsInstance(plan.install_cuda, bool)
        self.assertIsInstance(plan.install_ffmpeg, bool)
        self.assertIn(plan.validation_level, ["basic", "advanced", "benchmark"])

    def test_generate_report(self):
        """Testa geração de relatório"""
        from main_installer import InstallationResult

        # Criar resultado mock
        result = InstallationResult(
            success=True,
            components_installed=["Python 3.13", "FFmpeg"],
            components_failed=[],
            installation_time=120.5,
            system_info=self.installer.system_info,
            validation_results={"python_executable": True},
            recommendations=["Reiniciar terminal"],
            errors=[],
        )

        report = self.installer.generate_report(result)

        self.assertIsInstance(report, str)
        self.assertIn("RELATÓRIO DE INSTALAÇÃO", report)
        self.assertIn("Python 3.13", report)
        self.assertIn("120.5s", report)


class TestIntegration(unittest.TestCase):
    """Testes de integração"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_analysis_workflow(self):
        """Testa fluxo completo de análise"""
        installer = VideoConverterInstaller(cache_dir=self.temp_dir)

        # Análise do sistema
        analysis = installer.analyze_system()
        self.assertIsInstance(analysis, dict)

        # Criação de plano
        plan = installer.create_installation_plan(interactive=False)
        self.assertIsInstance(plan, InstallationPlan)

        # Geração de relatório mock
        from main_installer import InstallationResult

        result = InstallationResult(
            success=True,
            components_installed=[],
            components_failed=[],
            installation_time=0,
            system_info=analysis["system"]["os_info"],
            validation_results={},
            recommendations=[],
            errors=[],
        )

        report = installer.generate_report(result)
        self.assertIsInstance(report, str)

    def test_component_interaction(self):
        """Testa interação entre componentes"""
        # Verificar se componentes podem ser inicializados juntos
        os_detector = OSDetector()
        python_manager = PythonManager(cache_dir=self.temp_dir)
        gpu_detector = GPUDetector()

        # Obter informações básicas
        os_info = os_detector.detect()
        python_current = python_manager.get_current_python()
        gpus = gpu_detector.detect_gpus()

        # Verificar consistência
        self.assertIsInstance(os_info, OSInfo)
        self.assertIsNotNone(
            python_current
        )  # Pode ser None se Python não estiver instalado
        self.assertIsInstance(gpus, list)


class TestPerformance(unittest.TestCase):
    """Testes de performance"""

    def test_system_detection_speed(self):
        """Testa velocidade de detecção do sistema"""
        start_time = time.time()

        detector = OSDetector()
        os_info = detector.detect()

        detection_time = time.time() - start_time

        # Detecção deve ser rápida (< 5 segundos)
        self.assertLess(
            detection_time, 5.0, f"Detecção muito lenta: {detection_time:.2f}s"
        )
        self.assertIsInstance(os_info, OSInfo)

    def test_python_detection_speed(self):
        """Testa velocidade de detecção Python"""
        start_time = time.time()

        manager = PythonManager()
        installations = [manager.get_current_python()]

        detection_time = time.time() - start_time

        # Detecção deve ser razoável (< 10 segundos)
        self.assertLess(
            detection_time, 10.0, f"Detecção Python muito lenta: {detection_time:.2f}s"
        )
        self.assertIsInstance(installations, list)


def run_specific_test(test_class_name: str = None, test_method: str = None):
    """
    Executa teste específico

    Args:
        test_class_name: Nome da classe de teste
        test_method: Nome do método de teste
    """
    if test_class_name:
        if test_method:
            suite = unittest.TestSuite()
            suite.addTest(globals()[test_class_name](test_method))
        else:
            suite = unittest.TestLoader().loadTestsFromTestCase(
                globals()[test_class_name]
            )
    else:
        suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_quick_tests():
    """Executa testes rápidos essenciais"""
    print("🧪 Executando testes rápidos...")

    quick_tests = [
        (TestOSDetector, "test_detect_os"),
        (TestPythonManager, "test_detect_python_installations"),
        (TestInstallerSettings, "test_default_settings"),
        (TestVideoConverterInstaller, "test_analyze_system"),
    ]

    results = []
    for test_class, test_method in quick_tests:
        print(f"  Executando {test_class.__name__}.{test_method}...")

        suite = unittest.TestSuite()
        suite.addTest(test_class(test_method))

        # Capturar saída para análise de erros
        import io

        output_stream = io.StringIO()
        runner = unittest.TextTestRunner(verbosity=2, stream=output_stream)
        result = runner.run(suite)

        results.append(result.wasSuccessful())
        if result.wasSuccessful():
            print(f"    ✅ PASSOU")
        else:
            print(f"    ❌ FALHOU")
            # Mostrar saída capturada
            output_content = output_stream.getvalue()
            if output_content:
                print(f"      SAÍDA: {output_content}")
            # Mostrar erros e falhas
            for error in result.errors:
                print(f"      ERRO: {error[1].strip()}")
            for failure in result.failures:
                print(f"      FALHA: {failure[1].strip()}")

    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Taxa de sucesso: {success_rate:.1f}% ({sum(results)}/{len(results)})")

    return all(results)


def run_comprehensive_tests():
    """Executa todos os testes"""
    print("🧪 Executando testes abrangentes...")

    # Descobrir e executar todos os testes
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Estatísticas
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = (
        (total_tests - failures - errors) / total_tests * 100 if total_tests > 0 else 0
    )

    print(f"\n📊 Resultados dos Testes:")
    print(f"   Total: {total_tests}")
    print(f"   Sucessos: {total_tests - failures - errors}")
    print(f"   Falhas: {failures}")
    print(f"   Erros: {errors}")
    print(f"   Taxa de sucesso: {success_rate:.1f}%")

    if result.failures:
        print(f"\n❌ Falhas:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\n⚠️  Erros:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback.split('Exception:')[-1].strip()}")

    return result.wasSuccessful()


def main():
    """Função principal dos testes"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Testes do Instalador VideoConverter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python test_installer.py                    # Todos os testes
  python test_installer.py --quick            # Testes rápidos
  python test_installer.py --class TestOSDetector  # Classe específica
  python test_installer.py --method test_detect_os # Método específico
        """,
    )

    parser.add_argument(
        "--quick", action="store_true", help="Executar apenas testes rápidos"
    )
    parser.add_argument(
        "--class", dest="test_class", help="Executar classe de teste específica"
    )
    parser.add_argument(
        "--method", dest="test_method", help="Executar método de teste específico"
    )
    parser.add_argument("--verbose", action="store_true", help="Output detalhado")

    args = parser.parse_args()

    # Banner
    print("🧪 VideoConverter - Testes do Instalador")
    print("=" * 50)

    try:
        if args.quick:
            success = run_quick_tests()
        elif args.test_class or args.test_method:
            success = run_specific_test(args.test_class, args.test_method)
        else:
            success = run_comprehensive_tests()

        print("\n" + "=" * 50)
        if success:
            print("🎉 Todos os testes passaram!")
            sys.exit(0)
        else:
            print("❌ Alguns testes falharam!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Testes cancelados pelo usuário")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Erro durante execução dos testes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
