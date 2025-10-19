#!/usr/bin/env python3
"""Script para debugar o teste que está falhando"""

import sys
import traceback
import unittest
from pathlib import Path

# Adicionar o diretório installer ao path
installer_dir = Path(__file__).parent / "installer"
sys.path.insert(0, str(installer_dir))

from test_installer import TestVideoConverterInstaller


def main():
    print("🔍 Debugando teste test_analyze_system...")

    # Criar instância do teste
    test_instance = TestVideoConverterInstaller()

    try:
        # Executar setUp
        print("📋 Executando setUp...")
        test_instance.setUp()
        print("✅ setUp concluído")

        # Executar o teste
        print("🧪 Executando test_analyze_system...")
        test_instance.test_analyze_system()
        print("✅ Teste passou!")

    except Exception as e:
        print(f"❌ Erro no teste:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print("\n📋 Traceback completo:")
        traceback.print_exc()
        return 1

    finally:
        try:
            # Executar tearDown se existir
            if hasattr(test_instance, "tearDown"):
                print("🧹 Executando tearDown...")
                test_instance.tearDown()
                print("✅ tearDown concluído")
        except Exception as e:
            print(f"⚠️ Erro no tearDown: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
