#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Reinicialização do VidConv
Testa as funcionalidades de reinicialização da aplicação
"""

import sys
import os
import tempfile
import time
from unittest.mock import Mock, patch

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.updater import restart_application, _create_restart_script, schedule_restart


class RestartSystemTester:
    """
    Classe para testar o sistema de reinicialização
    """
    
    def __init__(self):
        """
        Inicializa o testador do sistema de reinicialização
        """
        self.test_results = []
        
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
    
    def test_restart_script_creation(self):
        """
        Testa criação do script de reinicialização
        """
        try:
            app_path = "C:\\test\\app.exe"
            delay_seconds = 3
            
            script_path = _create_restart_script(app_path, delay_seconds)
            
            # Verifica se o script foi criado
            assert os.path.exists(script_path), "Script não foi criado"
            
            # Verifica conteúdo do script
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "timeout /t 3" in content, "Delay não configurado corretamente"
            assert app_path in content, "Caminho da aplicação não encontrado"
            assert "del \"%~f0\"" in content, "Auto-exclusão não configurada"
            
            # Limpa o arquivo de teste
            os.remove(script_path)
            
            self.log_test("Criação de Script de Reinicialização", True, "Script criado e validado com sucesso")
            
        except Exception as e:
            self.log_test("Criação de Script de Reinicialização", False, f"Erro: {e}")
    
    def test_restart_function_parameters(self):
        """
        Testa parâmetros da função de reinicialização
        """
        try:
            # Mock do sys.exit para evitar encerrar o teste
            with patch('sys.exit') as mock_exit:
                with patch('subprocess.Popen') as mock_popen:
                    with patch('utils.updater._create_restart_script') as mock_script:
                        mock_script.return_value = "test_script.bat"
                        
                        # Testa com delay padrão
                        restart_application()
                        mock_script.assert_called_once()
                        
                        # Verifica se sys.exit foi chamado
                        mock_exit.assert_called_once_with(0)
            
            self.log_test("Parâmetros da Função de Reinicialização", True, "Função aceita parâmetros corretamente")
            
        except Exception as e:
            self.log_test("Parâmetros da Função de Reinicialização", False, f"Erro: {e}")
    
    def test_schedule_restart_function(self):
        """
        Testa função de agendamento de reinicialização
        """
        try:
            with patch('threading.Thread') as mock_thread:
                with patch('tkinter.messagebox.showinfo') as mock_info:
                    # Testa agendamento imediato
                    schedule_restart(0)
                    mock_thread.assert_called_once()
                    mock_info.assert_not_called()
                    
                    # Reset mocks
                    mock_thread.reset_mock()
                    mock_info.reset_mock()
                    
                    # Testa agendamento com delay
                    schedule_restart(5)
                    mock_thread.assert_called_once()
                    mock_info.assert_called_once()
            
            self.log_test("Função de Agendamento", True, "Agendamento funciona corretamente")
            
        except Exception as e:
            self.log_test("Função de Agendamento", False, f"Erro: {e}")
    
    def test_executable_detection(self):
        """
        Testa detecção de executável vs script Python
        """
        try:
            # Simula aplicação compilada
            with patch('sys.frozen', True, create=True):
                with patch('sys.executable', 'C:\\app\\vidconv.exe'):
                    with patch('sys.exit'):
                        with patch('subprocess.Popen') as mock_popen:
                            with patch('utils.updater._create_restart_script') as mock_script:
                                mock_script.return_value = "test.bat"
                                
                                restart_application()
                                
                                # Verifica se foi chamado com o executável
                                mock_script.assert_called_once()
                                args = mock_script.call_args[0]
                                assert args[0] == 'C:\\app\\vidconv.exe', "Caminho do executável incorreto"
            
            self.log_test("Detecção de Executável", True, "Detecção funciona corretamente")
            
        except Exception as e:
            self.log_test("Detecção de Executável", False, f"Erro: {e}")
    
    def test_error_handling(self):
        """
        Testa tratamento de erros
        """
        try:
            with patch('utils.updater._create_restart_script') as mock_script:
                with patch('tkinter.messagebox.showerror') as mock_error:
                    # Simula erro na criação do script
                    mock_script.side_effect = Exception("Erro simulado")
                    
                    restart_application()
                    
                    # Verifica se o erro foi tratado
                    mock_error.assert_called_once()
                    error_args = mock_error.call_args[0]  # args, não kwargs
                    assert "Erro de Reinicialização" in error_args[0], "Título do erro incorreto"
            
            self.log_test("Tratamento de Erros", True, "Erros são tratados adequadamente")
            
        except Exception as e:
            self.log_test("Tratamento de Erros", False, f"Erro: {e}")
    
    def run_all_tests(self):
        """
        Executa todos os testes do sistema de reinicialização
        """
        print("=== INICIANDO TESTES DO SISTEMA DE REINICIALIZAÇÃO ===\n")
        
        # Lista de testes
        tests = [
            self.test_restart_script_creation,
            self.test_restart_function_parameters,
            self.test_schedule_restart_function,
            self.test_executable_detection,
            self.test_error_handling
        ]
        
        # Executa cada teste
        for test in tests:
            try:
                test()
            except Exception as e:
                test_name = test.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, False, f"Erro inesperado: {e}")
        
        # Mostra resumo
        self.print_summary()
    
    def print_summary(self):
        """
        Imprime resumo dos testes
        """
        print("\n=== RESUMO DOS TESTES ===")
        
        total = len(self.test_results)
        passed = sum(1 for result in self.test_results if result['success'])
        failed = total - passed
        
        print(f"Total de testes: {total}")
        print(f"Passou: {passed}")
        print(f"Falhou: {failed}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"\nTaxa de sucesso: {success_rate:.1f}%")
            
            if success_rate == 100:
                print("✓ Sistema de reinicialização está funcionando perfeitamente!")
            elif success_rate >= 80:
                print("⚠ Sistema de reinicialização está funcionando bem, mas há melhorias possíveis.")
            else:
                print("✗ Sistema de reinicialização precisa de correções.")
        
        # Mostra detalhes dos testes que falharam
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n=== TESTES QUE FALHARAM ===")
            for test in failed_tests:
                print(f"- {test['test']}: {test['message']}")


def main():
    """
    Função principal para executar os testes
    """
    tester = RestartSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()