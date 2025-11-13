#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Correção Automática de Duplicações
Corrige imports duplicados, métodos duplicados e blocos de código duplicados
"""

import os
import re
from typing import List, Set
from utils.safe_code_modifier import SafeCodeModifier

def remove_duplicate_imports(content: str) -> str:
    """
    Remove imports duplicados mantendo apenas a primeira ocorrência
    
    Args:
        content: Conteúdo do arquivo
        
    Returns:
        Conteúdo com imports duplicados removidos
    """
    lines = content.split('\n')
    seen_imports = set()
    cleaned_lines = []
    
    for line in lines:
        # Verificar se é uma linha de import
        stripped = line.strip()
        if stripped.startswith(('import ', 'from ')) and not stripped.startswith('#'):
            # Normalizar o import para comparação
            normalized_import = re.sub(r'\s+', ' ', stripped)
            
            if normalized_import not in seen_imports:
                seen_imports.add(normalized_import)
                cleaned_lines.append(line)
            else:
                print(f"  🗑️  Removendo import duplicado: {stripped}")
        else:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def remove_duplicate_methods(content: str) -> str:
    """
    Remove métodos duplicados mantendo apenas a primeira ocorrência
    
    Args:
        content: Conteúdo do arquivo
        
    Returns:
        Conteúdo com métodos duplicados removidos
    """
    lines = content.split('\n')
    seen_methods = set()
    cleaned_lines = []
    skip_until_next_def = False
    current_method = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Detectar início de método/função
        method_match = re.match(r'^\s*(def\s+\w+\s*\([^)]*\):)', line)
        if method_match:
            method_signature = method_match.group(1).strip()
            
            if method_signature in seen_methods:
                print(f"  🗑️  Removendo método duplicado: {method_signature}")
                skip_until_next_def = True
                current_method = method_signature
                i += 1
                continue
            else:
                seen_methods.add(method_signature)
                skip_until_next_def = False
        
        # Se estamos pulando um método duplicado
        if skip_until_next_def:
            # Verificar se chegamos ao próximo método/classe ou fim do arquivo
            if (stripped.startswith('def ') or 
                stripped.startswith('class ') or 
                (stripped and not line.startswith(' ') and not line.startswith('\t'))):
                skip_until_next_def = False
                # Não pular esta linha, ela é o início de algo novo
            else:
                i += 1
                continue
        
        cleaned_lines.append(line)
        i += 1
    
    return '\n'.join(cleaned_lines)

def remove_duplicate_blocks(content: str, min_lines: int = 5) -> str:
    """
    Remove blocos de código duplicados
    
    Args:
        content: Conteúdo do arquivo
        min_lines: Número mínimo de linhas para considerar um bloco
        
    Returns:
        Conteúdo com blocos duplicados removidos
    """
    lines = content.split('\n')
    
    # Encontrar blocos duplicados
    blocks_to_remove = []
    
    for i in range(len(lines) - min_lines):
        block = lines[i:i + min_lines]
        block_text = '\n'.join(block).strip()
        
        if not block_text or block_text.isspace():
            continue
        
        # Procurar por duplicatas deste bloco
        for j in range(i + min_lines, len(lines) - min_lines):
            compare_block = lines[j:j + min_lines]
            compare_text = '\n'.join(compare_block).strip()
            
            if block_text == compare_text:
                print(f"  🗑️  Removendo bloco duplicado nas linhas {j+1}-{j+min_lines}")
                blocks_to_remove.append((j, j + min_lines))
                break
    
    # Remover blocos duplicados (de trás para frente para não afetar índices)
    for start, end in sorted(blocks_to_remove, reverse=True):
        del lines[start:end]
    
    return '\n'.join(lines)

def fix_file_duplications(file_path: str) -> bool:
    """
    Corrige duplicações em um arquivo específico
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        True se correções foram aplicadas
    """
    if not os.path.exists(file_path):
        print(f"❌ Arquivo não encontrado: {file_path}")
        return False
    
    print(f"\n🔧 Corrigindo duplicações em: {os.path.basename(file_path)}")
    
    try:
        # Ler conteúdo original
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Aplicar correções
        content = original_content
        
        # 1. Remover imports duplicados
        print("  🔍 Verificando imports duplicados...")
        content = remove_duplicate_imports(content)
        
        # 2. Remover métodos duplicados
        print("  🔍 Verificando métodos duplicados...")
        content = remove_duplicate_methods(content)
        
        # 3. Remover blocos duplicados
        print("  🔍 Verificando blocos duplicados...")
        content = remove_duplicate_blocks(content)
        
        # Verificar se houve mudanças
        if content == original_content:
            print("  ✅ Nenhuma duplicação encontrada")
            return False
        
        # Aplicar mudanças usando o modificador seguro
        project_root = os.path.dirname(os.path.abspath(__file__))
        with SafeCodeModifier(project_root) as modifier:
            success = modifier.safe_modify_file(
                file_path, 
                content, 
                f"Correção automática de duplicações em {os.path.basename(file_path)}"
            )
            
            if success:
                print("  ✅ Duplicações corrigidas com sucesso")
                return True
            else:
                print("  ❌ Falha ao aplicar correções")
                return False
    
    except Exception as e:
        print(f"  ❌ Erro ao processar arquivo: {e}")
        return False

def main():
    """Função principal"""
    print("🛠️  CORREÇÃO AUTOMÁTICA DE DUPLICAÇÕES")
    print("=" * 50)
    
    # Arquivos para corrigir
    files_to_fix = [
        "video_converter_module/core/queue_manager.py",
        "video_converter_module/core/video_converter.py"
    ]
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    fixed_files = 0
    
    for file_path in files_to_fix:
        full_path = os.path.join(project_root, file_path)
        
        if fix_file_duplications(full_path):
            fixed_files += 1
    
    print(f"\n📊 RESUMO:")
    print(f"  • Arquivos processados: {len(files_to_fix)}")
    print(f"  • Arquivos corrigidos: {fixed_files}")
    
    if fixed_files > 0:
        print("\n🔍 Executando verificação pós-correção...")
        os.system("python check_integrity.py")
    else:
        print("\n✅ Nenhuma correção necessária")

if __name__ == "__main__":
    main()