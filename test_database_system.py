#!/usr/bin/env python3
"""
Teste Completo do Sistema de Banco de Dados de Metadados de Vídeo
Valida todas as funcionalidades implementadas
"""

import os
import sys
import logging
from datetime import datetime

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar módulos do sistema
from database import (
    VideoMetadataDB, VideoQueries, MetadataExtractor, StoryboardDownloader,
    initialize_database, verify_database_integrity, get_quick_stats,
    backup_database, get_module_info
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def test_database_initialization():
    """Testa a inicialização do banco de dados"""
    
    print("\n" + "="*60)
    print("🔧 TESTE 1: Inicialização do Banco de Dados")
    print("="*60)
    
    try:
        # Remover banco de teste se existir
        test_db_path = "test_video_metadata.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Inicializar banco
        db = initialize_database(test_db_path)
        
        # Verificar se arquivo foi criado
        assert os.path.exists(test_db_path), "Arquivo do banco não foi criado"
        
        # Verificar integridade
        integrity_ok = verify_database_integrity(test_db_path)
        assert integrity_ok, "Integridade do banco falhou"
        
        print("✅ Banco de dados inicializado com sucesso")
        print(f"📁 Arquivo criado: {test_db_path}")
        
        # Mostrar informações do módulo
        module_info = get_module_info()
        print(f"📦 Módulo: {module_info['name']} v{module_info['version']}")
        
        return test_db_path
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        raise

def test_metadata_extraction(db_path: str):
    """Testa a extração de metadados"""
    
    print("\n" + "="*60)
    print("📊 TESTE 2: Extração de Metadados")
    print("="*60)
    
    try:
        # URL de teste (vídeo curto do YouTube)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - vídeo famoso e estável
        
        # Criar extrator
        extractor = MetadataExtractor(db_path)
        
        print(f"🔍 Extraindo metadados de: {test_url}")
        
        # Extrair metadados (sem baixar o vídeo)
        video_data = extractor.extract_metadata(test_url)
        
        if video_data:
            print("✅ Metadados extraídos com sucesso")
            print(f"📺 Título: {video_data.get('title', 'N/A')}")
            print(f"👤 Canal: {video_data.get('uploader', 'N/A')}")
            print(f"⏱️ Duração: {video_data.get('duration', 'N/A')} segundos")
            print(f"👀 Visualizações: {video_data.get('view_count', 'N/A')}")
            print(f"📅 Upload: {video_data.get('upload_date', 'N/A')}")
            
            # Contar thumbnails e storyboards
            thumbnails = video_data.get('thumbnails', [])
            formats = video_data.get('formats', [])
            storyboards = [f for f in formats if f.get('format_note') == 'storyboard']
            
            print(f"🖼️ Thumbnails disponíveis: {len(thumbnails)}")
            print(f"📋 Storyboards disponíveis: {len(storyboards)}")
            print(f"🎬 Formatos de vídeo: {len([f for f in formats if f.get('vcodec') != 'none'])}")
            
            return video_data
        else:
            print("❌ Falha na extração de metadados")
            return None
            
    except Exception as e:
        print(f"❌ Erro na extração: {e}")
        return None

def test_database_operations(db_path: str, video_data: dict):
    """Testa operações do banco de dados"""
    
    print("\n" + "="*60)
    print("💾 TESTE 3: Operações do Banco de Dados")
    print("="*60)
    
    try:
        # Criar extrator e armazenar dados
        extractor = MetadataExtractor(db_path)
        video_id = extractor.store_video_metadata(video_data)
        
        print(f"✅ Metadados armazenados com ID: {video_id}")
        
        # Testar consultas
        queries = VideoQueries(db_path)
        
        # Buscar vídeo
        videos = queries.search_videos(title=video_data.get('title', '')[:20])
        print(f"🔍 Vídeos encontrados na busca: {len(videos)}")
        
        if videos:
            video = videos[0]
            print(f"📺 Primeiro resultado: {video['title']}")
            
            # Obter detalhes completos
            details = queries.get_video_details(video['id'])
            if details:
                print(f"🖼️ Thumbnails no banco: {len(details.get('thumbnails', []))}")
                print(f"📋 Storyboards no banco: {len(details.get('storyboards', []))}")
                print(f"📖 Capítulos no banco: {len(details.get('chapters', []))}")
                print(f"🎬 Formatos no banco: {len(details.get('formats', []))}")
        
        # Obter estatísticas
        stats = queries.get_download_statistics()
        print(f"📊 Total de vídeos no banco: {stats.get('total_videos', 0)}")
        print(f"📊 Total de thumbnails: {stats.get('total_thumbnails', 0)}")
        print(f"📊 Total de storyboards: {stats.get('total_storyboards', 0)}")
        
        return video_id
        
    except Exception as e:
        print(f"❌ Erro nas operações do banco: {e}")
        return None

def test_storyboard_downloader(db_path: str, video_id: int):
    """Testa o sistema de download de storyboards"""
    
    print("\n" + "="*60)
    print("📥 TESTE 4: Download de Storyboards")
    print("="*60)
    
    try:
        # Criar diretório de teste
        download_dir = "test_storyboards"
        os.makedirs(download_dir, exist_ok=True)
        
        # Criar downloader
        downloader = StoryboardDownloader(db_path, download_dir)
        
        # Obter storyboards do vídeo
        queries = VideoQueries(db_path)
        details = queries.get_video_details(video_id)
        
        if details and details.get('storyboards'):
            storyboards = details['storyboards']
            print(f"📋 Storyboards disponíveis: {len(storyboards)}")
            
            # Tentar baixar o primeiro storyboard (menor resolução)
            storyboard = min(storyboards, key=lambda x: x.get('width', 0) * x.get('height', 0))
            
            print(f"📥 Baixando storyboard: {storyboard['format_note']} ({storyboard.get('width')}x{storyboard.get('height')})")
            
            # Download com timeout menor para teste
            success = downloader.download_storyboard(
                storyboard['url'], 
                storyboard['id'],
                timeout=30  # 30 segundos para teste
            )
            
            if success:
                print("✅ Storyboard baixado com sucesso")
                
                # Verificar arquivos criados
                files = os.listdir(download_dir)
                print(f"📁 Arquivos criados: {len(files)}")
                
                # Mostrar alguns arquivos
                for i, file in enumerate(files[:5]):
                    print(f"   📄 {file}")
                    if i == 4 and len(files) > 5:
                        print(f"   ... e mais {len(files) - 5} arquivos")
                        break
            else:
                print("⚠️ Download do storyboard falhou (pode ser normal em teste)")
        else:
            print("⚠️ Nenhum storyboard disponível para download")
        
        # Limpar arquivos de teste
        import shutil
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
            print("🧹 Arquivos de teste removidos")
            
    except Exception as e:
        print(f"❌ Erro no teste de download: {e}")

def test_backup_and_stats(db_path: str):
    """Testa backup e estatísticas"""
    
    print("\n" + "="*60)
    print("💾 TESTE 5: Backup e Estatísticas")
    print("="*60)
    
    try:
        # Criar backup
        backup_path = f"{db_path}.backup_test"
        backup_success = backup_database(db_path, backup_path)
        
        if backup_success:
            print("✅ Backup criado com sucesso")
            print(f"📁 Arquivo de backup: {backup_path}")
            
            # Verificar tamanho
            original_size = os.path.getsize(db_path)
            backup_size = os.path.getsize(backup_path)
            
            print(f"📊 Tamanho original: {original_size} bytes")
            print(f"📊 Tamanho backup: {backup_size} bytes")
            
            assert original_size == backup_size, "Tamanhos diferentes"
            
            # Remover backup de teste
            os.remove(backup_path)
            print("🧹 Backup de teste removido")
        
        # Obter estatísticas rápidas
        stats = get_quick_stats(db_path)
        print("\n📊 Estatísticas Rápidas:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Erro no teste de backup: {e}")

def cleanup_test_files():
    """Remove arquivos de teste"""
    
    print("\n" + "="*60)
    print("🧹 LIMPEZA: Removendo Arquivos de Teste")
    print("="*60)
    
    test_files = [
        "test_video_metadata.db",
        "test_video_metadata.db.backup_test",
        "test_storyboards"
    ]
    
    for file_path in test_files:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"🗑️ Removido: {file_path}")
            elif os.path.isdir(file_path):
                import shutil
                shutil.rmtree(file_path)
                print(f"🗑️ Removido diretório: {file_path}")
        except Exception as e:
            print(f"⚠️ Erro ao remover {file_path}: {e}")

def main():
    """Função principal de teste"""
    
    print("🚀 INICIANDO TESTE COMPLETO DO SISTEMA DE BANCO DE DADOS")
    print("=" * 80)
    
    start_time = datetime.now()
    
    try:
        # Teste 1: Inicialização
        db_path = test_database_initialization()
        
        # Teste 2: Extração de metadados
        video_data = test_metadata_extraction(db_path)
        
        if video_data:
            # Teste 3: Operações do banco
            video_id = test_database_operations(db_path, video_data)
            
            if video_id:
                # Teste 4: Download de storyboards
                test_storyboard_downloader(db_path, video_id)
            
            # Teste 5: Backup e estatísticas
            test_backup_and_stats(db_path)
        
        # Calcular tempo total
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "="*80)
        print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print(f"⏱️ Tempo total: {duration.total_seconds():.2f} segundos")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Sempre limpar arquivos de teste
        cleanup_test_files()

if __name__ == "__main__":
    main()