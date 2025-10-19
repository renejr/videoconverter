#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste automatizado dos componentes do sistema de atualizações
Verifica funcionalidades sem interface gráfica
"""

import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
import json

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.updater import UpdateChecker, UpdateDownloader


class UpdateSystemTester:
    """
    Classe para testar o sistema de atualizações
    """
    
    def __init__(self):
        """
        Inicializa o testador
        """
        self.test_results = []
        self.temp_dir = None
    
    def setup(self):
        """
        Configura ambiente de teste
        """
        print("Configurando ambiente de teste...")
        self.temp_dir = tempfile.mkdtemp()
        print(f"Diretório temporário: {self.temp_dir}")
    
    def cleanup(self):
        """
        Limpa ambiente de teste
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print("Ambiente de teste limpo")
    
    def log_test(self, test_name, success, message=""):
        """
        Registra resultado de teste
        
        Args:
            test_name: Nome do teste
            success: Se o teste passou
            message: Mensagem adicional
        """
        result = {
            'test': test_name,
            'success': success,
            'message': message
        }
        self.test_results.append(result)
        
        status = "✓ PASSOU" if success else "✗ FALHOU"
        print(f"{status} - {test_name}")
        if message:
            print(f"    {message}")
    
    def test_update_checker_init(self):
        """
        Testa inicialização do UpdateChecker
        """
        try:
            callback = Mock()
            checker = UpdateChecker(callback_update_available=callback)
            
            # Verifica se foi inicializado corretamente
            assert hasattr(checker, 'github_repo')
            assert hasattr(checker, 'callback_update_available')
            assert checker.callback_update_available == callback
            
            self.log_test("UpdateChecker - Inicialização", True)
            return True
            
        except Exception as e:
            self.log_test("UpdateChecker - Inicialização", False, str(e))
            return False
    
    def test_update_downloader_init(self):
        """
        Testa inicialização do UpdateDownloader
        """
        try:
            progress_callback = Mock()
            downloader = UpdateDownloader(progress_callback=progress_callback)
            
            # Verifica se foi inicializado corretamente
            assert hasattr(downloader, 'progress_callback')
            assert downloader.progress_callback == progress_callback
            
            self.log_test("UpdateDownloader - Inicialização", True)
            return True
            
        except Exception as e:
            self.log_test("UpdateDownloader - Inicialização", False, str(e))
            return False
    
    def test_version_comparison(self):
        """
        Testa comparação de versões
        """
        try:
            checker = UpdateChecker()
            
            # Testa diferentes cenários de versão
            test_cases = [
                ("1.0.0", "1.0.1", True),   # Atualização disponível
                ("1.0.1", "1.0.0", False),  # Versão atual é mais nova
                ("1.0.0", "1.0.0", False),  # Mesma versão
                ("1.0.0", "2.0.0", True),   # Atualização major
                ("v1.0.0", "v1.0.1", True), # Com prefixo 'v'
            ]
            
            for current, latest, expected in test_cases:
                result = checker._is_newer_version(current, latest)
                if result != expected:
                    raise AssertionError(f"Falha na comparação {current} vs {latest}: esperado {expected}, obtido {result}")
            
            self.log_test("Comparação de Versões", True)
            return True
            
        except Exception as e:
            self.log_test("Comparação de Versões", False, str(e))
            return False
    
    def test_file_operations(self):
        """
        Testa operações de arquivo
        """
        try:
            downloader = UpdateDownloader()
            
            # Testa criação de diretório de backup
            backup_dir = os.path.join(self.temp_dir, "backup_test")
            downloader._create_backup_directory(backup_dir)
            
            assert os.path.exists(backup_dir)
            
            # Testa backup de arquivo
            test_file = os.path.join(self.temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("conteúdo de teste")
            
            backup_path = downloader._backup_file(test_file, backup_dir)
            assert os.path.exists(backup_path)
            
            # Verifica conteúdo do backup
            with open(backup_path, 'r') as f:
                content = f.read()
            assert content == "conteúdo de teste"
            
            self.log_test("Operações de Arquivo", True)
            return True
            
        except Exception as e:
            self.log_test("Operações de Arquivo", False, str(e))
            return False
    
    def test_url_validation(self):
        """
        Testa validação de URLs
        """
        try:
            downloader = UpdateDownloader()
            
            # URLs válidas
            valid_urls = [
                "https://github.com/user/repo/releases/download/v1.0.0/app.exe",
                "https://api.github.com/repos/user/repo/zipball/main",
                "http://example.com/file.zip"
            ]
            
            for url in valid_urls:
                if not downloader._is_valid_url(url):
                    raise AssertionError(f"URL válida rejeitada: {url}")
            
            # URLs inválidas
            invalid_urls = [
                "not_a_url",
                "ftp://example.com/file.zip",
                "",
                None
            ]
            
            for url in invalid_urls:
                if downloader._is_valid_url(url):
                    raise AssertionError(f"URL inválida aceita: {url}")
            
            self.log_test("Validação de URLs", True)
            return True
            
        except Exception as e:
            self.log_test("Validação de URLs", False, str(e))
            return False
    
    def test_asset_detection(self):
        """
        Testa detecção de assets apropriados
        """
        try:
            downloader = UpdateDownloader()
            
            # Simula dados de release
            release_data = {
                'assets': [
                    {
                        'name': 'app-v1.0.0-linux.tar.gz',
                        'browser_download_url': 'https://example.com/linux.tar.gz'
                    },
                    {
                        'name': 'app-v1.0.0-windows.exe',
                        'browser_download_url': 'https://example.com/windows.exe'
                    },
                    {
                        'name': 'app-v1.0.0-macos.dmg',
                        'browser_download_url': 'https://example.com/macos.dmg'
                    }
                ]
            }
            
            # Testa detecção para Windows
            with patch('platform.system', return_value='Windows'):
                asset = downloader._get_appropriate_asset(release_data)
                assert asset is not None
                assert 'windows' in asset['name'].lower()
            
            self.log_test("Detecção de Assets", True)
            return True
            
        except Exception as e:
            self.log_test("Detecção de Assets", False, str(e))
            return False
    
    def test_config_management(self):
        """
        Testa gerenciamento de configuração
        """
        try:
            checker = UpdateChecker()
            
            # Testa configuração padrão
            config = checker._get_config()
            assert isinstance(config, dict)
            assert 'check_interval' in config
            assert 'auto_download' in config
            
            # Testa salvamento de configuração
            test_config = {
                'check_interval': 3600,
                'auto_download': False,
                'last_check': '2024-01-01T00:00:00'
            }
            
            config_file = os.path.join(self.temp_dir, "test_config.json")
            checker._save_config(test_config, config_file)
            
            assert os.path.exists(config_file)
            
            # Testa carregamento de configuração
            loaded_config = checker._load_config(config_file)
            assert loaded_config == test_config
            
            self.log_test("Gerenciamento de Configuração", True)
            return True
            
        except Exception as e:
            self.log_test("Gerenciamento de Configuração", False, str(e))
            return False
    
    def run_all_tests(self):
        """
        Executa todos os testes
        """
        print("=== INICIANDO TESTES DO SISTEMA DE ATUALIZAÇÕES ===\n")
        
        self.setup()
        
        try:
            # Lista de testes
            tests = [
                self.test_update_checker_init,
                self.test_update_downloader_init,
                self.test_version_comparison,
                self.test_file_operations,
                self.test_url_validation,
                self.test_asset_detection,
                self.test_config_management,
            ]
            
            # Executa cada teste
            for test in tests:
                try:
                    test()
                except Exception as e:
                    print(f"Erro inesperado no teste {test.__name__}: {e}")
            
            # Relatório final
            self.print_summary()
            
        finally:
            self.cleanup()
    
    def print_summary(self):
        """
        Imprime resumo dos testes
        """
        print("\n=== RESUMO DOS TESTES ===")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        failed = total - passed
        
        print(f"Total de testes: {total}")
        print(f"Passou: {passed}")
        print(f"Falhou: {failed}")
        
        if failed > 0:
            print("\nTestes que falharam:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nTaxa de sucesso: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✓ Sistema de atualizações está funcionando bem!")
        else:
            print("⚠ Sistema de atualizações precisa de correções")


def main():
    """
    Função principal
    """
    tester = UpdateSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()