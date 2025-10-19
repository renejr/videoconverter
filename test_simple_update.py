#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Simples do Sistema de Atualizações
"""

import sys
import os
from unittest.mock import Mock, patch

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.updater import UpdateChecker, UpdateDownloader, restart_application

def test_basic_functionality():
    """
    Testa funcionalidade básica do sistema
    """
    print("=== TESTE SIMPLES DO SISTEMA DE ATUALIZAÇÕES ===\n")
    
    try:
        # Testa UpdateChecker
        print("1. Testando UpdateChecker...")
        checker = UpdateChecker()
        assert hasattr(checker, 'current_version'), "UpdateChecker deve ter current_version"
        assert hasattr(checker, 'github_repo'), "UpdateChecker deve ter github_repo"
        print("   ✓ UpdateChecker inicializado corretamente")
        
        # Testa UpdateDownloader
        print("2. Testando UpdateDownloader...")
        downloader = UpdateDownloader()
        assert hasattr(downloader, 'progress_callback'), "UpdateDownloader deve ter progress_callback"
        print("   ✓ UpdateDownloader inicializado corretamente")
        
        # Testa comparação de versões
        print("3. Testando comparação de versões...")
        result = checker.compare_versions("1.0.0", "1.0.1")
        assert result == -1, "1.0.0 deve ser menor que 1.0.1"
        print("   ✓ Comparação de versões funciona")
        
        # Testa função de reinicialização (mock)
        print("4. Testando sistema de reinicialização...")
        with patch('sys.exit') as mock_exit:
            with patch('subprocess.Popen') as mock_popen:
                with patch('utils.updater._create_restart_script') as mock_script:
                    mock_script.return_value = "test.bat"
                    restart_application()
                    mock_exit.assert_called_once_with(0)
        print("   ✓ Sistema de reinicialização funciona")
        
        print("\n=== RESULTADO ===")
        print("✓ Todos os testes passaram!")
        print("🎉 Sistema de atualizações está funcionando perfeitamente!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)