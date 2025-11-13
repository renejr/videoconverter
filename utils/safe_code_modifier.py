#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Modificação Segura de Código
Wrapper para modificações que inclui verificações automáticas
"""

import os
import shutil
import tempfile
from typing import Optional, Dict, List
from datetime import datetime
from .code_integrity_checker import CodeIntegrityChecker

class SafeCodeModifier:
    """
    Modificador seguro de código com verificações automáticas
    """
    
    def __init__(self, project_root: str):
        """
        Inicializa o modificador seguro
        
        Args:
            project_root: Diretório raiz do projeto
        """
        self.project_root = project_root
        self.checker = CodeIntegrityChecker(project_root)
        self.temp_dir = tempfile.mkdtemp(prefix="safe_code_")
        self.modifications_log = []
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
    
    def _create_file_backup(self, file_path: str) -> str:
        """
        Cria backup temporário de um arquivo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Caminho do backup criado
        """
        if not os.path.exists(file_path):
            return ""
        
        filename = os.path.basename(file_path)
        backup_path = os.path.join(self.temp_dir, f"{filename}.backup")
        
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"⚠️ Erro ao criar backup de {file_path}: {e}")
            return ""
    
    def _restore_file_backup(self, file_path: str, backup_path: str) -> bool:
        """
        Restaura arquivo do backup
        
        Args:
            file_path: Caminho do arquivo original
            backup_path: Caminho do backup
            
        Returns:
            True se restaurado com sucesso
        """
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
                return True
        except Exception as e:
            print(f"❌ Erro ao restaurar backup de {file_path}: {e}")
        
        return False
    
    def _check_modification_safety(self, file_path: str, original_content: str, new_content: str) -> Dict:
        """
        Verifica se uma modificação é segura
        
        Args:
            file_path: Caminho do arquivo
            original_content: Conteúdo original
            new_content: Novo conteúdo
            
        Returns:
            Relatório de segurança da modificação
        """
        safety_report = {
            "safe": True,
            "warnings": [],
            "errors": [],
            "changes": {
                "lines_added": 0,
                "lines_removed": 0,
                "lines_modified": 0
            }
        }
        
        # Verificar sintaxe do novo código
        try:
            compile(new_content, file_path, 'exec')
        except SyntaxError as e:
            safety_report["safe"] = False
            safety_report["errors"].append(f"Erro de sintaxe linha {e.lineno}: {e.msg}")
        
        # Analisar mudanças
        original_lines = original_content.split('\n')
        new_lines = new_content.split('\n')
        
        import difflib
        diff = list(difflib.unified_diff(original_lines, new_lines, lineterm=''))
        
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                safety_report["changes"]["lines_added"] += 1
            elif line.startswith('-') and not line.startswith('---'):
                safety_report["changes"]["lines_removed"] += 1
        
        # Detectar possíveis duplicações
        if safety_report["changes"]["lines_added"] > 10:
            # Verificar se há muitas linhas similares sendo adicionadas
            added_lines = [line[1:] for line in diff if line.startswith('+') and not line.startswith('+++')]
            unique_lines = set(added_lines)
            
            if len(unique_lines) < len(added_lines) * 0.7:  # Menos de 70% de linhas únicas
                safety_report["warnings"].append("Possível duplicação de código detectada")
        
        # Verificar imports duplicados
        import_lines = [line for line in new_lines if line.strip().startswith(('import ', 'from '))]
        if len(import_lines) != len(set(import_lines)):
            safety_report["warnings"].append("Imports duplicados detectados")
        
        return safety_report
    
    def safe_modify_file(self, file_path: str, new_content: str, description: str = "") -> bool:
        """
        Modifica um arquivo de forma segura com verificações
        
        Args:
            file_path: Caminho do arquivo
            new_content: Novo conteúdo
            description: Descrição da modificação
            
        Returns:
            True se modificação foi bem-sucedida e segura
        """
        print(f"🔧 Modificando arquivo: {os.path.basename(file_path)}")
        if description:
            print(f"📝 Descrição: {description}")
        
        # Verificar se arquivo existe
        if not os.path.exists(file_path):
            print(f"❌ Arquivo não encontrado: {file_path}")
            return False
        
        # Criar backup
        backup_path = self._create_file_backup(file_path)
        if not backup_path:
            print("❌ Falha ao criar backup - operação cancelada")
            return False
        
        try:
            # Ler conteúdo original
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Verificar segurança da modificação
            safety_report = self._check_modification_safety(file_path, original_content, new_content)
            
            # Mostrar avisos
            if safety_report["warnings"]:
                print("⚠️  Avisos detectados:")
                for warning in safety_report["warnings"]:
                    print(f"  • {warning}")
            
            # Verificar erros críticos
            if not safety_report["safe"]:
                print("❌ Modificação não é segura:")
                for error in safety_report["errors"]:
                    print(f"  • {error}")
                return False
            
            # Aplicar modificação
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Verificar integridade pós-modificação
            integrity_report = self.checker.check_file_integrity(file_path)
            
            if integrity_report["status"] in ["syntax_error", "error"]:
                print("❌ Problemas detectados após modificação - revertendo...")
                self._restore_file_backup(file_path, backup_path)
                return False
            
            # Log da modificação
            modification_log = {
                "timestamp": datetime.now().isoformat(),
                "file": file_path,
                "description": description,
                "changes": safety_report["changes"],
                "warnings": safety_report["warnings"],
                "backup_path": backup_path
            }
            self.modifications_log.append(modification_log)
            
            print(f"✅ Modificação aplicada com sucesso")
            print(f"📊 Mudanças: +{safety_report['changes']['lines_added']} -{safety_report['changes']['lines_removed']} linhas")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante modificação: {e}")
            print("🔄 Revertendo para backup...")
            self._restore_file_backup(file_path, backup_path)
            return False
    
    def get_modification_summary(self) -> str:
        """
        Retorna resumo das modificações realizadas
        
        Returns:
            Resumo formatado das modificações
        """
        if not self.modifications_log:
            return "Nenhuma modificação realizada."
        
        summary = ["📋 RESUMO DAS MODIFICAÇÕES REALIZADAS", "=" * 50]
        
        total_added = 0
        total_removed = 0
        total_warnings = 0
        
        for mod in self.modifications_log:
            summary.append(f"\n📄 {os.path.basename(mod['file'])}")
            summary.append(f"   📝 {mod['description']}")
            summary.append(f"   📊 +{mod['changes']['lines_added']} -{mod['changes']['lines_removed']} linhas")
            
            if mod['warnings']:
                summary.append(f"   ⚠️  {len(mod['warnings'])} aviso(s)")
                total_warnings += len(mod['warnings'])
            
            total_added += mod['changes']['lines_added']
            total_removed += mod['changes']['lines_removed']
        
        summary.append(f"\n📈 TOTAIS:")
        summary.append(f"   • Arquivos modificados: {len(self.modifications_log)}")
        summary.append(f"   • Linhas adicionadas: {total_added}")
        summary.append(f"   • Linhas removidas: {total_removed}")
        summary.append(f"   • Avisos totais: {total_warnings}")
        
        return "\n".join(summary)

# Função de conveniência para uso direto
def safe_file_modification(file_path: str, new_content: str, description: str = "") -> bool:
    """
    Função de conveniência para modificação segura de arquivo único
    
    Args:
        file_path: Caminho do arquivo
        new_content: Novo conteúdo
        description: Descrição da modificação
        
    Returns:
        True se modificação foi bem-sucedida
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    with SafeCodeModifier(project_root) as modifier:
        return modifier.safe_modify_file(file_path, new_content, description)