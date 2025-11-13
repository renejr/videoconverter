#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Verificação de Integridade do Código
Detecta duplicações, corrupções e inconsistências no código fonte
"""

import os
import hashlib
import json
import re
from typing import Dict, List, Tuple, Set
from datetime import datetime
import difflib

class CodeIntegrityChecker:
    """
    Verificador de integridade do código fonte
    Detecta duplicações, métodos duplicados, imports inconsistentes
    """
    
    def __init__(self, project_root: str):
        """
        Inicializa o verificador de integridade
        
        Args:
            project_root: Diretório raiz do projeto
        """
        self.project_root = project_root
        self.integrity_file = os.path.join(project_root, ".code_integrity.json")
        self.backup_dir = os.path.join(project_root, ".integrity_backups")
        self.last_check = {}
        
        # Criar diretório de backup se não existir
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Carregar último estado
        self._load_last_state()
    
    def _load_last_state(self) -> None:
        """Carrega o último estado de integridade"""
        try:
            if os.path.exists(self.integrity_file):
                with open(self.integrity_file, 'r', encoding='utf-8') as f:
                    self.last_check = json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao carregar estado anterior: {e}")
            self.last_check = {}
    
    def _save_state(self, state: Dict) -> None:
        """Salva o estado atual de integridade"""
        try:
            with open(self.integrity_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Erro ao salvar estado: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcula hash MD5 de um arquivo"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _backup_file(self, file_path: str) -> str:
        """Cria backup de um arquivo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            backup_name = f"{filename}.{timestamp}.backup"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            return backup_path
        except Exception as e:
            print(f"⚠️ Erro ao criar backup de {file_path}: {e}")
            return ""
    
    def detect_duplicate_methods(self, file_path: str) -> List[Dict]:
        """
        Detecta métodos duplicados em um arquivo Python
        
        Returns:
            Lista de métodos duplicados encontrados
        """
        duplicates = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex para encontrar definições de métodos/funções
            method_pattern = r'^\s*(def\s+\w+\s*\([^)]*\):)'
            methods = {}
            
            for line_num, line in enumerate(content.split('\n'), 1):
                match = re.match(method_pattern, line)
                if match:
                    method_signature = match.group(1).strip()
                    
                    if method_signature in methods:
                        duplicates.append({
                            "method": method_signature,
                            "first_occurrence": methods[method_signature],
                            "duplicate_line": line_num,
                            "file": file_path
                        })
                    else:
                        methods[method_signature] = line_num
        
        except Exception as e:
            print(f"⚠️ Erro ao verificar métodos duplicados em {file_path}: {e}")
        
        return duplicates
    
    def detect_duplicate_imports(self, file_path: str) -> List[Dict]:
        """
        Detecta imports duplicados em um arquivo Python
        
        Returns:
            Lista de imports duplicados encontrados
        """
        duplicates = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex para encontrar imports
            import_pattern = r'^\s*(import\s+\w+|from\s+\w+\s+import\s+.+)'
            imports = {}
            
            for line_num, line in enumerate(content.split('\n'), 1):
                match = re.match(import_pattern, line)
                if match:
                    import_statement = match.group(1).strip()
                    
                    if import_statement in imports:
                        duplicates.append({
                            "import": import_statement,
                            "first_occurrence": imports[import_statement],
                            "duplicate_line": line_num,
                            "file": file_path
                        })
                    else:
                        imports[import_statement] = line_num
        
        except Exception as e:
            print(f"⚠️ Erro ao verificar imports duplicados em {file_path}: {e}")
        
        return duplicates
    
    def detect_code_blocks_duplication(self, file_path: str, min_lines: int = 5) -> List[Dict]:
        """
        Detecta blocos de código duplicados
        
        Args:
            file_path: Caminho do arquivo
            min_lines: Número mínimo de linhas para considerar duplicação
            
        Returns:
            Lista de blocos duplicados encontrados
        """
        duplicates = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Procurar por blocos duplicados
            for i in range(len(lines) - min_lines):
                block1 = lines[i:i + min_lines]
                block1_text = ''.join(block1).strip()
                
                if not block1_text or block1_text.isspace():
                    continue
                
                for j in range(i + min_lines, len(lines) - min_lines):
                    block2 = lines[j:j + min_lines]
                    block2_text = ''.join(block2).strip()
                    
                    if block1_text == block2_text:
                        duplicates.append({
                            "block_start_1": i + 1,
                            "block_start_2": j + 1,
                            "block_size": min_lines,
                            "content_preview": block1_text[:100] + "...",
                            "file": file_path
                        })
                        break
        
        except Exception as e:
            print(f"⚠️ Erro ao verificar blocos duplicados em {file_path}: {e}")
        
        return duplicates
    
    def check_file_integrity(self, file_path: str) -> Dict:
        """
        Verifica integridade de um arquivo específico
        
        Returns:
            Relatório de integridade do arquivo
        """
        report = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
            "hash": self._calculate_file_hash(file_path),
            "issues": {
                "duplicate_methods": [],
                "duplicate_imports": [],
                "duplicate_blocks": [],
                "syntax_errors": []
            },
            "status": "ok"
        }
        
        if not os.path.exists(file_path):
            report["status"] = "missing"
            return report
        
        # Verificar apenas arquivos Python
        if not file_path.endswith('.py'):
            return report
        
        try:
            # Verificar sintaxe Python
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                report["issues"]["syntax_errors"].append({
                    "line": e.lineno,
                    "message": str(e),
                    "text": e.text
                })
                report["status"] = "syntax_error"
            
            # Detectar duplicações
            report["issues"]["duplicate_methods"] = self.detect_duplicate_methods(file_path)
            report["issues"]["duplicate_imports"] = self.detect_duplicate_imports(file_path)
            report["issues"]["duplicate_blocks"] = self.detect_code_blocks_duplication(file_path)
            
            # Determinar status geral
            total_issues = (
                len(report["issues"]["duplicate_methods"]) +
                len(report["issues"]["duplicate_imports"]) +
                len(report["issues"]["duplicate_blocks"]) +
                len(report["issues"]["syntax_errors"])
            )
            
            if total_issues > 0:
                report["status"] = "issues_found"
        
        except Exception as e:
            report["status"] = "error"
            report["error"] = str(e)
        
        return report
    
    def check_project_integrity(self) -> Dict:
        """
        Verifica integridade de todo o projeto
        
        Returns:
            Relatório completo de integridade
        """
        print("🔍 Iniciando verificação de integridade do projeto...")
        
        project_report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": self.project_root,
            "files_checked": 0,
            "files_with_issues": 0,
            "total_issues": 0,
            "files": {},
            "summary": {
                "duplicate_methods": 0,
                "duplicate_imports": 0,
                "duplicate_blocks": 0,
                "syntax_errors": 0
            }
        }
        
        # Verificar arquivos Python no projeto
        for root, dirs, files in os.walk(self.project_root):
            # Ignorar diretórios específicos
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.project_root)
                    
                    print(f"  📄 Verificando: {relative_path}")
                    
                    file_report = self.check_file_integrity(file_path)
                    project_report["files"][relative_path] = file_report
                    project_report["files_checked"] += 1
                    
                    # Contar issues
                    if file_report["status"] in ["issues_found", "syntax_error"]:
                        project_report["files_with_issues"] += 1
                        
                        for issue_type, issues in file_report["issues"].items():
                            count = len(issues)
                            project_report["summary"][issue_type] += count
                            project_report["total_issues"] += count
        
        # Salvar estado atual
        self._save_state(project_report)
        
        return project_report
    
    def generate_integrity_report(self, report: Dict) -> str:
        """
        Gera relatório legível de integridade
        
        Args:
            report: Relatório de integridade
            
        Returns:
            Relatório formatado em texto
        """
        output = []
        output.append("=" * 60)
        output.append("🛡️  RELATÓRIO DE INTEGRIDADE DO CÓDIGO")
        output.append("=" * 60)
        output.append(f"📅 Data: {report['timestamp']}")
        output.append(f"📁 Projeto: {report['project_root']}")
        output.append(f"📄 Arquivos verificados: {report['files_checked']}")
        output.append(f"⚠️  Arquivos com problemas: {report['files_with_issues']}")
        output.append(f"🔢 Total de problemas: {report['total_issues']}")
        output.append("")
        
        # Resumo por tipo
        output.append("📊 RESUMO POR TIPO:")
        for issue_type, count in report['summary'].items():
            if count > 0:
                output.append(f"  • {issue_type.replace('_', ' ').title()}: {count}")
        output.append("")
        
        # Detalhes por arquivo
        if report['files_with_issues'] > 0:
            output.append("📋 DETALHES POR ARQUIVO:")
            
            for file_path, file_report in report['files'].items():
                if file_report['status'] in ['issues_found', 'syntax_error']:
                    output.append(f"\n📄 {file_path}:")
                    
                    for issue_type, issues in file_report['issues'].items():
                        if issues:
                            output.append(f"  🔸 {issue_type.replace('_', ' ').title()}:")
                            for issue in issues[:3]:  # Mostrar apenas os primeiros 3
                                if issue_type == 'duplicate_methods':
                                    output.append(f"    - {issue['method']} (linhas {issue['first_occurrence']}, {issue['duplicate_line']})")
                                elif issue_type == 'duplicate_imports':
                                    output.append(f"    - {issue['import']} (linhas {issue['first_occurrence']}, {issue['duplicate_line']})")
                                elif issue_type == 'duplicate_blocks':
                                    output.append(f"    - Bloco duplicado (linhas {issue['block_start_1']}-{issue['block_start_2']})")
                                elif issue_type == 'syntax_errors':
                                    output.append(f"    - Linha {issue['line']}: {issue['message']}")
                            
                            if len(issues) > 3:
                                output.append(f"    ... e mais {len(issues) - 3} problemas")
        else:
            output.append("✅ Nenhum problema encontrado!")
        
        output.append("")
        output.append("=" * 60)
        
        return "\n".join(output)

def main():
    """Função principal para teste"""
    checker = CodeIntegrityChecker("E:\\pyProjs\\vidconv")
    report = checker.check_project_integrity()
    
    print(checker.generate_integrity_report(report))
    
    # Salvar relatório em arquivo
    report_file = os.path.join("E:\\pyProjs\\vidconv", "integrity_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(checker.generate_integrity_report(report))
    
    print(f"\n📄 Relatório salvo em: {report_file}")

if __name__ == "__main__":
    main()