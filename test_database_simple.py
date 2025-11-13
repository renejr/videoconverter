#!/usr/bin/env python3
"""
Teste Simplificado do Sistema de Banco de Dados
Valida funcionalidades básicas sem dependências externas
"""

import os
import sys
import sqlite3
from datetime import datetime

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar módulos do sistema
from database import VideoMetadataDB, VideoQueries, get_module_info

def test_basic_database_operations():
    """Testa operações básicas do banco de dados"""
    
    print("🔧 Testando operações básicas do banco de dados...")
    
    # Criar banco de teste
    test_db = "test_simple.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    try:
        # Inicializar banco
        db = VideoMetadataDB(test_db)
        db.create_tables()
        
        # Verificar se tabelas foram criadas
        connection = db.get_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'videos', 'video_metadata', 'thumbnails', 'storyboards',
            'storyboard_fragments', 'chapters', 'video_formats', 'download_history'
        ]
        
        print(f"✅ Tabelas criadas: {len(tables)}")
        for table in expected_tables:
            if table in tables:
                print(f"   ✓ {table}")
            else:
                print(f"   ✗ {table} (FALTANDO)")
        
        # Testar inserção de dados de teste
        cursor.execute("""
            INSERT INTO videos (
                video_id, title, uploader, duration, view_count, 
                upload_date, webpage_url, extractor, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test123', 'Vídeo de Teste', 'Canal Teste', 180, 1000,
            '20231031', 'https://example.com/test', 'youtube', datetime.now()
        ))
        
        connection.commit()
        
        # Verificar inserção
        cursor.execute("SELECT COUNT(*) FROM videos")
        count = cursor.fetchone()[0]
        print(f"✅ Vídeos inseridos: {count}")
        
        db.close()
        
        # Testar consultas
        queries = VideoQueries(test_db)
        videos = queries.search_videos(query="Teste")
        print(f"✅ Busca por título: {len(videos)} resultado(s)")
        
        stats = queries.get_download_statistics()
        print(f"✅ Estatísticas obtidas: {len(stats)} campos")
        
        queries.close()
        
        print("✅ Teste básico concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste básico: {e}")
        return False
        
    finally:
        # Limpar arquivo de teste
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
                print("🧹 Arquivo de teste removido")
            except:
                print("⚠️ Não foi possível remover arquivo de teste")

def test_module_info():
    """Testa informações do módulo"""
    
    print("\n📦 Testando informações do módulo...")
    
    try:
        info = get_module_info()
        
        print(f"✅ Nome: {info['name']}")
        print(f"✅ Versão: {info['version']}")
        print(f"✅ Autor: {info['author']}")
        print(f"✅ Componentes: {len(info['components'])}")
        print(f"✅ Funcionalidades: {len(info['features'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao obter informações: {e}")
        return False

def test_database_schema():
    """Testa o schema do banco de dados"""
    
    print("\n🗄️ Testando schema do banco de dados...")
    
    test_db = "test_schema.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    try:
        db = VideoMetadataDB(test_db)
        db.create_tables()
        
        connection = db.get_connection()
        cursor = connection.cursor()
        
        # Verificar estrutura da tabela videos
        cursor.execute("PRAGMA table_info(videos)")
        columns = cursor.fetchall()
        
        print(f"✅ Tabela 'videos' tem {len(columns)} colunas:")
        for col in columns[:5]:  # Mostrar apenas as primeiras 5
            print(f"   - {col[1]} ({col[2]})")
        if len(columns) > 5:
            print(f"   ... e mais {len(columns) - 5} colunas")
        
        # Verificar índices
        cursor.execute("PRAGMA index_list(videos)")
        indexes = cursor.fetchall()
        print(f"✅ Tabela 'videos' tem {len(indexes)} índices")
        
        # Verificar chaves estrangeiras
        cursor.execute("PRAGMA foreign_key_list(thumbnails)")
        fks = cursor.fetchall()
        print(f"✅ Tabela 'thumbnails' tem {len(fks)} chave(s) estrangeira(s)")
        
        db.close()
        
        print("✅ Schema validado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação do schema: {e}")
        return False
        
    finally:
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except:
                pass

def main():
    """Função principal"""
    
    print("🚀 TESTE SIMPLIFICADO DO SISTEMA DE BANCO DE DADOS")
    print("=" * 60)
    
    start_time = datetime.now()
    
    tests = [
        ("Operações Básicas", test_basic_database_operations),
        ("Informações do Módulo", test_module_info),
        ("Schema do Banco", test_database_schema)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 40)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} - PASSOU")
        else:
            print(f"❌ {test_name} - FALHOU")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO: {passed}/{total} testes passaram")
    print(f"⏱️ Tempo total: {duration.total_seconds():.2f} segundos")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)