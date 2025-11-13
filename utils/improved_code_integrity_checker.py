#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Melhorado de Verificação de Integridade do Código
Detecta duplicações reais, elimina falsos positivos
"""

import os
import ast
import hashlib
import json
import re
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime
from collections import defaultdict

class ImprovedCodeIntegrityChecker:
    """
    Verificador de integridade melhorado do código fonte
    Elimina falsos positivos e detecta apenas problemas reais
    """
    
    def __init__(self, project_root: str):
        """
        Inicializa o verificador de integridade melhorado
        
        Args:
            project_root: Diretório raiz do projeto
        """
        self.project_root = project_root
        self.integrity_file = os.path.join(project_root, ".improved_integrity.json")
        self.backup_dir = os.path.join(project_root, ".integrity_backups")
        
        # Criar diretório de backup se não existir
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _normalize_import(self, import_statement: str) -> str:
        """
        Normaliza um statement de import para comparação semântica
        
        Args:
            import_statement: Statement de import original
            
        Returns:
            Statement normalizado
        """
        # Remove espaços extras e normaliza
        normalized = re.sub(r'\s+', ' ', import_statement.strip())
        
        # Ordena imports múltiplos (from x import a, b, c)
        if 'from' in normalized and 'import' in normalized:
            parts = normalized.split(' import ')
            if len(parts) == 2:
                module_part = parts[0]
                imports_part = parts[1]
                
                # Se há múltiplos imports, ordena eles
                if ',' in imports_part:
                    imports_list = [imp.strip() for imp in imports_part.split(',')]
                    imports_list.sort()
                    normalized = f"{module_part} import {', '.join(imports_list)}"
        
        return normalized
    
    def detect_duplicate_imports(self, file_path: str) -> List[Dict]:
        """
        Detecta imports REALMENTE duplicados usando análise semântica
        
        Returns:
            Lista de imports duplicados encontrados
        """
        duplicates = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST para análise semântica precisa
            try:
                tree = ast.parse(content)
            except SyntaxError:
                # Se há erro de sintaxe, não podemos analisar imports
                return duplicates
            
            imports_seen = {}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_name = alias.name
                        if alias.asname:
                            import_stmt = f"import {import_name} as {alias.asname}"
                        else:
                            import_stmt = f"import {import_name}"
                        
                        normalized = self._normalize_import(import_stmt)
                        
                        if normalized in imports_seen:
                            duplicates.append({
                                "import": import_stmt,
                                "first_occurrence": imports_seen[normalized],
                                "duplicate_line": node.lineno,
                                "file": file_path,
                                "type": "exact_duplicate"
                            })
                        else:
                            imports_seen[normalized] = node.lineno
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        if alias.name == "*":
                            import_stmt = f"from {module} import *"
                        else:
                            name = alias.name
                            if alias.asname:
                                import_stmt = f"from {module} import {name} as {alias.asname}"
                            else:
                                import_stmt = f"from {module} import {name}"
                        
                        normalized = self._normalize_import(import_stmt)
                        
                        if normalized in imports_seen:
                            duplicates.append({
                                "import": import_stmt,
                                "first_occurrence": imports_seen[normalized],
                                "duplicate_line": node.lineno,
                                "file": file_path,
                                "type": "exact_duplicate"
                            })
                        else:
                            imports_seen[normalized] = node.lineno
        
        except Exception as e:
            print(f"⚠️ Erro ao verificar imports em {file_path}: {e}")
        
        return duplicates
    
    def detect_duplicate_methods(self, file_path: str) -> List[Dict]:
        """
        Detecta métodos REALMENTE duplicados usando análise AST
        Considera contexto de classe e conteúdo do método
        
        Returns:
            Lista de métodos duplicados encontrados
        """
        duplicates = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST para análise semântica precisa
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return duplicates
            
            methods_by_context = defaultdict(list)
            
            # Analisar métodos em diferentes contextos
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Determinar contexto (classe ou módulo)
                    context = "module"
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            for child in ast.walk(parent):
                                if child is node:
                                    context = f"class:{parent.name}"
                                    break
                    
                    # Gerar hash do conteúdo do método (sem considerar nomes de variáveis)
                    method_content = ast.dump(node, annotate_fields=False, include_attributes=False)
                    content_hash = hashlib.md5(method_content.encode()).hexdigest()
                    
                    method_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "context": context,
                        "content_hash": content_hash,
                        "args": [arg.arg for arg in node.args.args],
                        "file": file_path
                    }
                    
                    methods_by_context[context].append(method_info)
            
            # Detectar duplicações dentro do mesmo contexto
            for context, methods in methods_by_context.items():
                seen_methods = {}
                
                for method in methods:
                    # Chave única: nome + argumentos + hash do conteúdo
                    method_key = f"{method['name']}:{':'.join(method['args'])}:{method['content_hash']}"
                    
                    if method_key in seen_methods:
                        duplicates.append({
                            "method": method['name'],
                            "context": context,
                            "first_occurrence": seen_methods[method_key]['line'],
                            "duplicate_line": method['line'],
                            "file": file_path,
                            "type": "identical_implementation"
                        })
                    else:
                        seen_methods[method_key] = method
        
        except Exception as e:
            print(f"⚠️ Erro ao verificar métodos em {file_path}: {e}")
        
        return duplicates
    
    def detect_code_blocks_duplication(self, file_path: str, min_lines: int = 10) -> List[Dict]:
        """
        Detecta blocos de código REALMENTE duplicados
        Usa análise semântica e ignora diferenças irrelevantes
        
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
            
            # Normalizar linhas (remover espaços, comentários vazios)
            normalized_lines = []
            for line in lines:
                stripped = line.strip()
                # Ignorar linhas vazias e comentários simples
                if stripped and not stripped.startswith('#') and stripped != '"""' and stripped != "'''":
                    # Normalizar espaços
                    normalized = re.sub(r'\s+', ' ', stripped)
                    normalized_lines.append(normalized)
                else:
                    normalized_lines.append("")
            
            # Procurar blocos duplicados com algoritmo mais eficiente
            block_hashes = {}
            
            for i in range(len(normalized_lines) - min_lines + 1):
                # Extrair bloco não-vazio
                block_lines = []
                actual_start = i
                
                for j in range(i, min(i + min_lines * 2, len(normalized_lines))):
                    if normalized_lines[j]:
                        block_lines.append(normalized_lines[j])
                        if len(block_lines) == 1:
                            actual_start = j
                        if len(block_lines) >= min_lines:
                            break
                
                if len(block_lines) >= min_lines:
                    # Criar hash do bloco
                    block_content = '\n'.join(block_lines[:min_lines])
                    block_hash = hashlib.md5(block_content.encode()).hexdigest()
                    
                    if block_hash in block_hashes:
                        # Verificar se não é o mesmo bloco (sobreposição)
                        prev_start = block_hashes[block_hash]
                        if abs(actual_start - prev_start) >= min_lines:
                            duplicates.append({
                                "block_start_1": prev_start + 1,
                                "block_start_2": actual_start + 1,
                                "block_size": min_lines,
                                "content_preview": block_content[:100] + "...",
                                "file": file_path,
                                "hash": block_hash
                            })
                    else:
                        block_hashes[block_hash] = actual_start
        
        except Exception as e:
            print(f"⚠️ Erro ao verificar blocos duplicados em {file_path}: {e}")
        
        return duplicates
    
    def check_syntax_errors(self, file_path: str) -> List[Dict]:
        """
        Verifica erros de sintaxe usando compile() do Python
        
        Returns:
            Lista de erros de sintaxe encontrados
        """
        syntax_errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                compile(content, file_path, 'exec')
            except SyntaxError as e:
                syntax_errors.append({
                    "line": e.lineno,
                    "column": e.offset,
                    "message": str(e.msg),
                    "text": e.text.strip() if e.text else "",
                    "file": file_path
                })
        
        except Exception as e:
            print(f"⚠️ Erro ao verificar sintaxe de {file_path}: {e}")
        
        return syntax_errors
    
    def check_file_integrity(self, file_path: str) -> Dict:
        """
        Verifica integridade de um arquivo específico com algoritmo melhorado
        
        Returns:
            Relatório de integridade do arquivo
        """
        report = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
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
            # Verificar sintaxe primeiro
            report["issues"]["syntax_errors"] = self.check_syntax_errors(file_path)
            
            # Se há erro de sintaxe, não verificar duplicações
            if report["issues"]["syntax_errors"]:
                report["status"] = "syntax_error"
                return report
            
            # Detectar duplicações com algoritmos melhorados
            report["issues"]["duplicate_methods"] = self.detect_duplicate_methods(file_path)
            report["issues"]["duplicate_imports"] = self.detect_duplicate_imports(file_path)
            report["issues"]["duplicate_blocks"] = self.detect_code_blocks_duplication(file_path)
            
            # Determinar status geral
            total_issues = (
                len(report["issues"]["duplicate_methods"]) +
                len(report["issues"]["duplicate_imports"]) +
                len(report["issues"]["duplicate_blocks"])
            )
            
            if total_issues > 0:
                report["status"] = "issues_found"
        
        except Exception as e:
            report["status"] = "error"
            report["error"] = str(e)
        
        return report
    
    def check_project_integrity(self, critical_files: List[str] = None) -> Dict:
        """
        Verifica integridade de arquivos críticos do projeto
        
        Args:
            critical_files: Lista de arquivos críticos para verificar
            
        Returns:
            Relatório completo de integridade
        """
        print("🔍 Iniciando verificação melhorada de integridade...")
        
        if critical_files is None:
            critical_files = [
                "video_converter_module/core/queue_manager.py",
                "video_converter_module/core/video_converter.py",
                "main_tkinter.py",
                "video_converter_module/utils/hardware_detector.py"
            ]
        
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
        
        # Verificar arquivos críticos
        for relative_path in critical_files:
            file_path = os.path.join(self.project_root, relative_path)
            
            if os.path.exists(file_path):
                print(f"  📄 Verificando: {relative_path}")
                
                file_report = self.check_file_integrity(file_path)
                project_report["files"][relative_path] = file_report
                project_report["files_checked"] += 1
                
                # Contar issues
                issues = file_report["issues"]
                file_total_issues = (
                    len(issues["duplicate_methods"]) +
                    len(issues["duplicate_imports"]) +
                    len(issues["duplicate_blocks"]) +
                    len(issues["syntax_errors"])
                )
                
                if file_total_issues > 0:
                    project_report["files_with_issues"] += 1
                    project_report["total_issues"] += file_total_issues
                    
                    # Atualizar summary
                    project_report["summary"]["duplicate_methods"] += len(issues["duplicate_methods"])
                    project_report["summary"]["duplicate_imports"] += len(issues["duplicate_imports"])
                    project_report["summary"]["duplicate_blocks"] += len(issues["duplicate_blocks"])
                    project_report["summary"]["syntax_errors"] += len(issues["syntax_errors"])
            else:
                print(f"  ❌ Arquivo não encontrado: {relative_path}")
                project_report["files"][relative_path] = {
                    "status": "missing",
                    "file": file_path
                }
        
        return project_report


def main():
    """Função principal para teste do verificador melhorado"""
    import sys
    
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    checker = ImprovedCodeIntegrityChecker(project_root)
    report = checker.check_project_integrity()
    
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE INTEGRIDADE MELHORADO")
    print("="*60)
    
    print(f"📁 Projeto: {report['project_root']}")
    print(f"📄 Arquivos verificados: {report['files_checked']}")
    print(f"⚠️ Arquivos com problemas: {report['files_with_issues']}")
    print(f"🔍 Total de problemas: {report['total_issues']}")
    
    if report['total_issues'] > 0:
        print("\n📋 Resumo dos problemas:")
        summary = report['summary']
        if summary['syntax_errors'] > 0:
            print(f"  🚨 Erros de sintaxe: {summary['syntax_errors']}")
        if summary['duplicate_methods'] > 0:
            print(f"  🔄 Métodos duplicados: {summary['duplicate_methods']}")
        if summary['duplicate_imports'] > 0:
            print(f"  📦 Imports duplicados: {summary['duplicate_imports']}")
        if summary['duplicate_blocks'] > 0:
            print(f"  📝 Blocos duplicados: {summary['duplicate_blocks']}")
        
        print("\n📄 Detalhes por arquivo:")
        for file_path, file_report in report['files'].items():
            if file_report.get('status') == 'issues_found':
                print(f"\n📄 {file_path}:")
                issues = file_report['issues']
                
                for error in issues['syntax_errors']:
                    print(f"  🚨 Erro de sintaxe (linha {error['line']}): {error['message']}")
                
                for dup in issues['duplicate_methods']:
                    print(f"  🔄 Método duplicado: {dup['method']} (linhas {dup['first_occurrence']}, {dup['duplicate_line']})")
                
                for dup in issues['duplicate_imports']:
                    print(f"  📦 Import duplicado: {dup['import']} (linhas {dup['first_occurrence']}, {dup['duplicate_line']})")
                
                for dup in issues['duplicate_blocks']:
                    print(f"  📝 Bloco duplicado (linhas {dup['block_start_1']}-{dup['block_start_1']+dup['block_size']}, {dup['block_start_2']}-{dup['block_start_2']+dup['block_size']})")
    else:
        print("\n✅ Nenhum problema de integridade encontrado!")
    
    # Salvar relatório
    report_file = os.path.join(project_root, "improved_integrity_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Relatório salvo em: {report_file}")


if __name__ == "__main__":
    main()