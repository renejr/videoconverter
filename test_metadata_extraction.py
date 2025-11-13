#!/usr/bin/env python3
"""
Script de Teste para Extração Completa de Metadados
Testa todas as informações disponíveis do yt-dlp incluindo storyboards
"""

import yt_dlp
import json
import os
from pathlib import Path

def extract_complete_metadata(url):
    """
    Extrai todos os metadados possíveis de um vídeo usando yt-dlp
    
    Args:
        url: URL do vídeo
        
    Returns:
        dict: Metadados completos
    """
    
    # Configuração para extrair TODOS os metadados possíveis
    ydl_opts = {
        'writeinfojson': True,          # Salva metadados em JSON
        'writethumbnail': True,         # Baixa thumbnail
        'writesubtitles': True,         # Baixa legendas
        'writeautomaticsub': True,      # Baixa legendas automáticas
        'writedescription': True,       # Salva descrição
        'writeannotations': True,       # Salva anotações (se disponível)
        'extract_flat': False,          # Extrai informações completas
        'no_warnings': False,           # Mostra todos os avisos
        'ignoreerrors': False,          # Para em caso de erro
        'skip_download': True,          # NÃO baixa o vídeo, só metadados
        'outtmpl': 'metadata_test/%(title)s.%(ext)s',
        
        # Configurações específicas para storyboards
        'writelink': True,              # Salva links
        'writeurllink': True,           # Salva URL links
        'writewebloclink': True,        # Salva web location links
        
        # Extrair informações de formato detalhadas
        'listformats': True,            # Lista todos os formatos
        'listsubtitles': True,          # Lista todas as legendas
        'listthumbnails': True,         # Lista todas as thumbnails
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("🔍 Extraindo metadados completos...")
            
            # Extrair informações sem download
            info = ydl.extract_info(url, download=False)
            
            # Salvar metadados em arquivo JSON para análise
            metadata_file = Path("metadata_test") / "complete_metadata.json"
            metadata_file.parent.mkdir(exist_ok=True)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Metadados salvos em: {metadata_file}")
            
            # Analisar informações específicas
            analyze_metadata(info)
            
            return info
            
    except Exception as e:
        print(f"❌ Erro na extração: {e}")
        return None

def analyze_metadata(info):
    """
    Analisa e exibe informações específicas dos metadados
    
    Args:
        info: Dicionário com metadados do vídeo
    """
    print("\n" + "="*60)
    print("📊 ANÁLISE DE METADADOS")
    print("="*60)
    
    # Informações básicas do vídeo
    print(f"🎬 Título: {info.get('title', 'N/A')}")
    print(f"📺 Canal: {info.get('uploader', 'N/A')}")
    print(f"⏱️ Duração: {info.get('duration', 'N/A')} segundos")
    print(f"👀 Visualizações: {info.get('view_count', 'N/A')}")
    print(f"📅 Data de Upload: {info.get('upload_date', 'N/A')}")
    
    # Análise de Thumbnails/Capas
    print(f"\n🖼️ THUMBNAILS/CAPAS:")
    thumbnails = info.get('thumbnails', [])
    print(f"   📊 Total de thumbnails: {len(thumbnails)}")
    
    for i, thumb in enumerate(thumbnails[:5]):  # Mostrar apenas as primeiras 5
        print(f"   {i+1}. Resolução: {thumb.get('width', '?')}x{thumb.get('height', '?')}")
        print(f"      URL: {thumb.get('url', 'N/A')[:80]}...")
        print(f"      ID: {thumb.get('id', 'N/A')}")
    
    # Análise de Storyboards
    print(f"\n📽️ STORYBOARDS:")
    
    # Verificar se há informações de storyboard nos thumbnails
    storyboard_thumbs = [t for t in thumbnails if 'storyboard' in str(t.get('id', '')).lower()]
    print(f"   📊 Storyboards encontrados: {len(storyboard_thumbs)}")
    
    for i, story in enumerate(storyboard_thumbs):
        print(f"   {i+1}. ID: {story.get('id', 'N/A')}")
        print(f"      Resolução: {story.get('width', '?')}x{story.get('height', '?')}")
        print(f"      URL: {story.get('url', 'N/A')[:80]}...")
    
    # Verificar campos específicos de storyboard
    if 'storyboard' in info:
        print(f"   ✅ Campo 'storyboard' encontrado!")
        print(f"   📄 Conteúdo: {str(info['storyboard'])[:200]}...")
    
    # Análise de Formatos
    print(f"\n🎥 FORMATOS DISPONÍVEIS:")
    formats = info.get('formats', [])
    print(f"   📊 Total de formatos: {len(formats)}")
    
    # Mostrar formatos únicos por resolução
    resolutions = set()
    for fmt in formats:
        if fmt.get('height'):
            resolutions.add(f"{fmt.get('height')}p")
    
    print(f"   📐 Resoluções disponíveis: {sorted(resolutions, key=lambda x: int(x[:-1]) if x[:-1].isdigit() else 0, reverse=True)}")
    
    # Análise de Legendas
    print(f"\n📝 LEGENDAS:")
    subtitles = info.get('subtitles', {})
    auto_subtitles = info.get('automatic_captions', {})
    
    print(f"   📊 Legendas manuais: {len(subtitles)} idiomas")
    print(f"   🤖 Legendas automáticas: {len(auto_subtitles)} idiomas")
    
    if subtitles:
        print(f"   🌍 Idiomas disponíveis: {list(subtitles.keys())[:10]}")  # Primeiros 10
    
    # Informações técnicas
    print(f"\n⚙️ INFORMAÇÕES TÉCNICAS:")
    print(f"   🆔 ID do vídeo: {info.get('id', 'N/A')}")
    print(f"   🔗 URL original: {info.get('webpage_url', 'N/A')}")
    print(f"   📱 Extrator: {info.get('extractor', 'N/A')}")
    print(f"   🏷️ Tags: {len(info.get('tags', []))} tags")
    
    # Verificar campos relacionados a storyboard/preview
    storyboard_fields = ['storyboard', 'preview', 'chapters', 'thumbnails']
    print(f"\n🔍 CAMPOS RELACIONADOS A STORYBOARD:")
    for field in storyboard_fields:
        if field in info:
            value = info[field]
            if isinstance(value, list):
                print(f"   ✅ {field}: {len(value)} itens")
            else:
                print(f"   ✅ {field}: {type(value).__name__}")
        else:
            print(f"   ❌ {field}: não encontrado")

def main():
    """Função principal para teste"""
    print("🎯 TESTE DE EXTRAÇÃO COMPLETA DE METADADOS")
    print("="*60)
    
    # URL de teste (vídeo público do YouTube)
    test_url = input("🔗 Digite a URL do vídeo para teste (ou Enter para usar exemplo): ").strip()
    
    if not test_url:
        # URL de exemplo - vídeo curto e público
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - sempre disponível
        print(f"📺 Usando URL de exemplo: {test_url}")
    
    # Criar diretório para testes
    os.makedirs("metadata_test", exist_ok=True)
    
    # Extrair metadados
    metadata = extract_complete_metadata(test_url)
    
    if metadata:
        print(f"\n✅ Extração concluída com sucesso!")
        print(f"📁 Verifique o diretório 'metadata_test' para arquivos gerados")
        
        # Verificar se arquivos foram criados
        test_dir = Path("metadata_test")
        files = list(test_dir.glob("*"))
        print(f"📄 Arquivos criados: {len(files)}")
        for file in files:
            print(f"   - {file.name} ({file.stat().st_size} bytes)")
    else:
        print(f"\n❌ Falha na extração de metadados")

if __name__ == "__main__":
    main()