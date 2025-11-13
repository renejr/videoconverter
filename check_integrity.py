#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Verificação Rápida de Integridade
Execute antes de modificações importantes no código
"""

import sys
import os
from utils.code_integrity_checker import CodeIntegrityChecker

def quick_integrity_check():
    """
    Executa verificação rápida de integridade
    Foca nos arquivos principais do projeto
    """
    print("🚀 Iniciando verificação rápida de integridade...")
    
    # Arquivos críticos para verificar
    critical_files = [
        "video_converter_module/core/queue_manager.py",
        "video_converter_module/core/video_converter.py", 
        "video_converter_module/utils/performance_modes.py",
        "main_tkinter.py",
        "gui/main_window_tkinter.py"
    ]
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    checker = CodeIntegrityChecker(project_root)
    
    issues_found = False
    
    for file_path in critical_files:
        full_path = os.path.join(project_root, file_path)
        
        if not os.path.exists(full_path):
            print(f"⚠️  Arquivo não encontrado: {file_path}")
            continue
        
        print(f"🔍 Verificando: {file_path}")
        report = checker.check_file_integrity(full_path)
        
        if report["status"] in ["issues_found", "syntax_error"]:
            issues_found = True
            print(f"❌ Problemas encontrados em {file_path}:")
            
            for issue_type, issues in report["issues"].items():
                if issues:
                    print(f"  🔸 {issue_type.replace('_', ' ').title()}: {len(issues)} problema(s)")
                    
                    # Mostrar detalhes dos primeiros problemas
                    for issue in issues[:2]:
                        if issue_type == 'duplicate_methods':
                            print(f"    - Método duplicado: {issue['method']}")
                        elif issue_type == 'duplicate_imports':
                            print(f"    - Import duplicado: {issue['import']}")
                        elif issue_type == 'syntax_errors':
                            print(f"    - Erro de sintaxe linha {issue['line']}: {issue['message']}")
        else:
            print(f"✅ {file_path} - OK")
    
    print("\n" + "="*50)
    
    if issues_found:
        print("❌ PROBLEMAS DETECTADOS!")
        print("⚠️  Recomendação: Corrija os problemas antes de continuar")
        print("📄 Execute 'python utils/code_integrity_checker.py' para relatório completo")
        return False
    else:
        print("✅ VERIFICAÇÃO CONCLUÍDA - NENHUM PROBLEMA DETECTADO")
        print("🚀 Seguro para continuar com modificações")
        return True

def create_backup_before_changes():
    """
    Cria backup dos arquivos críticos antes de modificações
    """
    print("\n💾 Criando backup de segurança...")
    
    critical_files = [
        "video_converter_module/core/queue_manager.py",
        "video_converter_module/core/video_converter.py"
    ]
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    backup_dir = os.path.join(project_root, ".safety_backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for file_path in critical_files:
        full_path = os.path.join(project_root, file_path)
        
        if os.path.exists(full_path):
            filename = os.path.basename(file_path)
            backup_name = f"{filename}.{timestamp}.backup"
            backup_path = os.path.join(backup_dir, backup_name)
            
            try:
                with open(full_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                print(f"✅ Backup criado: {backup_name}")
            except Exception as e:
                print(f"❌ Erro ao criar backup de {file_path}: {e}")

if __name__ == "__main__":
    # Verificar integridade
    integrity_ok = quick_integrity_check()
    
    # Criar backup se tudo estiver OK
    if integrity_ok:
        create_backup_before_changes()
        print("\n🛡️  Sistema pronto para modificações seguras!")
    else:
        print("\n⛔ NÃO PROSSIGA com modificações até corrigir os problemas!")
        sys.exit(1)