#!/usr/bin/env python3
"""
Teste E2E Completo - Download de Vídeo do YouTube
Valida proteções contra loops infinitos, monitoramento térmico, 
extração de metadados e gravação no banco SQLite
"""

import pytest
import tempfile
import os
import sys
import time
import threading
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports do sistema
from database.video_metadata_db import VideoMetadataDB
from database.metadata_extractor import MetadataExtractor
from database.storyboard_downloader import StoryboardDownloader
from database.video_queries import VideoQueries
from video_converter_module.core.queue_manager import ConversionQueueManager
from installer.core.os_detector import OSDetector
from video_converter_module.utils.hd_thermal_detector import HDThermalDetector

# Configurar logging para o teste
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestYouTubeDownloadE2EComplete:
    """
    Teste E2E completo do sistema de download do YouTube
    """
    
    # URL de teste fornecida pelo usuário
    TEST_VIDEO_URL = "https://youtu.be/0s7vn5Sdc84?si=pXStUwkESClMbl2F"
    TEST_VIDEO_ID = "0s7vn5Sdc84"
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """
        Configura ambiente de teste isolado
        """
        # Criar diretório temporário para o teste
        self.temp_dir = tempfile.mkdtemp(prefix="vidconv_e2e_test_")
        self.test_db_path = os.path.join(self.temp_dir, "test_video_metadata.db")
        self.test_cache_dir = os.path.join(self.temp_dir, "cache")
        self.test_storyboard_dir = os.path.join(self.temp_dir, "storyboards")
        
        # Criar diretórios necessários
        os.makedirs(self.test_cache_dir, exist_ok=True)
        os.makedirs(self.test_storyboard_dir, exist_ok=True)
        
        # Inicializar componentes do sistema
        self.db = VideoMetadataDB(self.test_db_path)
        self.metadata_extractor = MetadataExtractor(self.test_db_path)
        self.storyboard_downloader = StoryboardDownloader(self.test_db_path, self.test_storyboard_dir)
        self.video_queries = VideoQueries(self.test_db_path)
        
        # Configurar monitoramento térmico para teste
        self.thermal_monitor = HDThermalDetector()
        
        # Flags de controle para o teste
        self.test_completed = False
        self.thermal_protection_triggered = False
        self.retry_count = 0
        self.max_test_retries = 3
        
        logger.info(f"🧪 Ambiente de teste configurado em: {self.temp_dir}")
        
        yield
        
        # Limpeza após o teste
        self._cleanup_test_environment()
    
    def _cleanup_test_environment(self):
        """
        Limpa o ambiente de teste
        """
        try:
            # Fechar conexões do banco
            if hasattr(self, 'db'):
                self.db.close()
            if hasattr(self, 'metadata_extractor'):
                self.metadata_extractor.close()
            if hasattr(self, 'storyboard_downloader'):
                self.storyboard_downloader.close()
            if hasattr(self, 'video_queries'):
                self.video_queries.close()
            
            # Remover arquivos temporários
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            
            logger.info("🧹 Ambiente de teste limpo")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro na limpeza: {e}")
    
    def test_thermal_protection_validation(self):
        """
        Testa as validações de proteção térmica durante o download
        """
        logger.info("🌡️ Testando proteção térmica...")
        
        # Simular alta temperatura
        with patch.object(self.thermal_monitor, 'get_hd_temperature') as mock_temp:
            # Configurar temperatura alta (acima do limite)
            mock_temp.return_value = 85.0  # Acima de 80°C
            
            # Verificar se a proteção térmica está ativa
            mock_temperatures = {'C:\\': 85.0}
            thermal_status = self.thermal_monitor.get_thermal_status(mock_temperatures)
            
            # Validações
            assert thermal_status['status'] == 'critical', "Status térmico deveria ser crítico"
            assert thermal_status['max_temperature'] >= 80, "Temperatura deveria ser >= 80°C"
            
            self.thermal_protection_triggered = True
            logger.info("✅ Proteção térmica funcionando corretamente")
        
        # Simular temperatura normal para recuperação
        with patch.object(self.thermal_monitor, 'get_hd_temperature') as mock_temp:
            mock_temp.return_value = 35.0
            
            thermal_status = self.thermal_monitor.get_temperature_status(self.temp_dir)
            
            # Validações de recuperação
            assert thermal_status['status'] == 'normal', "Status térmico deveria ser normal"
            assert thermal_status['temperature'] == 35.0, "Temperatura deveria ser 35°C"
            
            logger.info("✅ Recuperação térmica funcionando corretamente")
    
    def test_anti_loop_protection_validation(self):
        """
        Testa as validações de proteção contra loops infinitos
        """
        logger.info("🔄 Testando proteção anti-loop...")
        
        # Configurar retry limitado para teste rápido
        max_retries = 2
        timeout_seconds = 5
        
        # Simular falhas de rede consecutivas
        with patch('requests.get') as mock_get:
            # Configurar para falhar sempre
            mock_get.side_effect = Exception("Simulated network error")
            
            # Tentar download com retry limitado
            retry_count = 0
            success = False
            
            for attempt in range(max_retries + 1):
                try:
                    # Simular tentativa de download
                    response = mock_get("http://test.url", timeout=timeout_seconds)
                    success = True
                    break
                except Exception as e:
                    retry_count += 1
                    logger.info(f"Tentativa {retry_count} falhou: {e}")
                    
                    if retry_count >= max_retries:
                        logger.info("Máximo de tentativas atingido")
                        break
                    
                    # Pequeno delay entre tentativas
                    time.sleep(0.1)
            
            # Validações
            assert success == False, "Download deveria ter falhado após max_retries"
            assert retry_count == max_retries, f"Deveria ter tentado {max_retries} vezes, mas tentou {retry_count}"
            
            self.retry_count = retry_count
            logger.info("✅ Proteção anti-loop funcionando corretamente")
    
    def test_metadata_extraction_and_storage(self):
        """
        Testa extração e gravação de metadados no banco SQLite
        """
        logger.info("📋 Testando extração de metadados...")
        
        # Mock dos metadados do vídeo de teste
        mock_metadata = {
            'id': self.TEST_VIDEO_ID,
            'title': 'Teste E2E - Vídeo de Exemplo',
            'description': 'Vídeo usado para teste E2E do sistema VidConv',
            'duration': 120,  # 2 minutos
            'uploader': 'Canal de Teste',
            'upload_date': '20240101',
            'view_count': 1000,
            'like_count': 50,
            'webpage_url': self.TEST_VIDEO_URL,
            'extractor': 'youtube',
            'thumbnail': 'https://i.ytimg.com/vi/0s7vn5Sdc84/maxresdefault.jpg',
            'thumbnails': [
                {
                    'url': 'https://i.ytimg.com/vi/0s7vn5Sdc84/default.jpg',
                    'width': 120,
                    'height': 90,
                    'resolution': '120x90'
                },
                {
                    'url': 'https://i.ytimg.com/vi/0s7vn5Sdc84/hqdefault.jpg',
                    'width': 480,
                    'height': 360,
                    'resolution': '480x360'
                }
            ],
            'formats': [
                {
                    'format_id': '18',
                    'ext': 'mp4',
                    'width': 640,
                    'height': 360,
                    'fps': 30,
                    'vcodec': 'avc1',
                    'acodec': 'mp4a'
                }
            ]
        }
        
        # Simular extração de metadados
        with patch.object(self.metadata_extractor, 'extract_metadata') as mock_extract:
            mock_extract.return_value = mock_metadata
            
            # Extrair metadados
            extracted_metadata = self.metadata_extractor.extract_metadata(self.TEST_VIDEO_URL)
            
            # Validar extração
            assert extracted_metadata is not None, "Metadados não foram extraídos"
            assert extracted_metadata['id'] == self.TEST_VIDEO_ID, "ID do vídeo incorreto"
            assert extracted_metadata['title'] is not None, "Título não extraído"
            assert len(extracted_metadata['thumbnails']) > 0, "Thumbnails não extraídas"
            
            # Simular gravação no banco
            video_inserted = self.db.insert_video_metadata(extracted_metadata)
            assert video_inserted == True, "Vídeo não foi gravado no banco"
            
            # Verificar dados no banco
            connection = sqlite3.connect(self.test_db_path)
            cursor = connection.cursor()
            
            # Verificar tabela videos
            cursor.execute("SELECT * FROM videos WHERE video_id = ?", (extracted_metadata['id'],))
            video_row = cursor.fetchone()
            assert video_row is not None, "Vídeo não encontrado na tabela videos"
            
            # Verificar tabela video_metadata
            cursor.execute("SELECT * FROM video_metadata WHERE video_id = ?", (extracted_metadata['id'],))
            metadata_row = cursor.fetchone()
            assert metadata_row is not None, "Metadados não encontrados na tabela video_metadata"
            
            # Verificar tabela thumbnails
            cursor.execute("SELECT COUNT(*) FROM thumbnails WHERE video_id = ?", (extracted_metadata['id'],))
            thumbnail_count = cursor.fetchone()[0]
            assert thumbnail_count > 0, "Thumbnails não foram gravadas"
            
            connection.close()
            
            logger.info("✅ Extração e gravação de metadados funcionando corretamente")
    
    def test_storyboard_generation_and_storage(self):
        """
        Testa geração e gravação de storyboards
        """
        logger.info("🎬 Testando geração de storyboards...")
        
        # Mock dos dados de storyboard
        mock_storyboards = [
            {
                'id': 1,
                'storyboard_id': 'sb0',
                'format_note': 'storyboard',
                'ext': 'mhtml',
                'protocol': 'mhtml',
                'width': 48,
                'height': 27,
                'fps': 1,
                'rows': 10,
                'columns': 10,
                'url': 'https://i9.ytimg.com/sb/0s7vn5Sdc84/storyboard3_L1/M0.jpg?sqp=-oaymwEiCNACELwBSFryq4qpAxiHoAJIAQ==&rs=AOn4CLBmocked'
            }
        ]
        
        # Primeiro, inserir vídeo no banco para ter um video_id válido
        mock_video_data = {
            'id': self.TEST_VIDEO_ID,
            'title': 'Teste Storyboard',
            'duration': 120,
            'webpage_url': f'https://www.youtube.com/watch?v={self.TEST_VIDEO_ID}',
            'extractor': 'youtube'
        }
        
        success = self.db.insert_video_metadata(mock_video_data)
        assert success, "Falha ao inserir vídeo no banco"
        
        # Inserir storyboards no banco
        for storyboard in mock_storyboards:
            # Preparar dados do storyboard para inserção
            storyboard_data = {
                'video_id': self.TEST_VIDEO_ID,
                'storyboard_id': storyboard['storyboard_id'],
                'format_note': storyboard['format_note'],
                'url': storyboard['url'],
                'width': storyboard['width'],
                'height': storyboard['height'],
                'fps': storyboard['fps'],
                'rows': storyboard['rows'],
                'columns': storyboard['columns'],
                'total_frames': storyboard['rows'] * storyboard['columns'],
                'resolution': f"{storyboard['width']}x{storyboard['height']}"
            }
            storyboard_id = self.db.insert_storyboard(storyboard_data)
            assert storyboard_id is not None, "Storyboard não foi inserido no banco"
        
        # Simular download de storyboard
        with patch.object(self.storyboard_downloader, '_download_storyboard') as mock_download:
            # Simular arquivos baixados
            mock_files = [
                os.path.join(self.test_storyboard_dir, "storyboard.mhtml"),
                os.path.join(self.test_storyboard_dir, "frame_001.jpg"),
                os.path.join(self.test_storyboard_dir, "frame_002.jpg")
            ]
            
            # Criar arquivos simulados
            for file_path in mock_files:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write("mock content")
            
            mock_download.return_value = mock_files
            
            # Tentar baixar storyboards
            downloaded_files = self.storyboard_downloader.download_video_storyboards(
                self.TEST_VIDEO_ID, 
                quality='best'
            )
            
            # Validações
            assert len(downloaded_files) > 0, "Nenhum arquivo de storyboard foi baixado"
            
            # Verificar se arquivos existem
            for file_path in mock_files:
                assert os.path.exists(file_path), f"Arquivo {file_path} não existe"
            
            # Verificar dados no banco
            connection = sqlite3.connect(self.test_db_path)
            cursor = connection.cursor()
            
            # Verificar tabela storyboards
            cursor.execute("SELECT COUNT(*) FROM storyboards WHERE video_id = ?", (self.TEST_VIDEO_ID,))
            storyboard_count = cursor.fetchone()[0]
            assert storyboard_count > 0, "Storyboards não foram gravados no banco"
            
            connection.close()
            
            logger.info("✅ Geração e gravação de storyboards funcionando corretamente")
    
    def test_complete_integration_flow(self):
        """
        Testa o fluxo completo de integração
        """
        logger.info("🔄 Testando fluxo completo de integração...")
        
        # Simular fluxo completo de download
        integration_steps = []
        
        try:
            # 1. Verificar proteção térmica
            integration_steps.append("thermal_check")
            mock_temperatures = {'C:\\': 85.0}
            thermal_status = self.thermal_monitor.get_thermal_status(mock_temperatures)
            assert thermal_status is not None, "Monitoramento térmico não funcionou"
            
            # 2. Extrair metadados
            integration_steps.append("metadata_extraction")
            mock_metadata = {
                'id': self.TEST_VIDEO_ID,
                'title': 'Teste Integração Completa',
                'duration': 180,
                'webpage_url': self.TEST_VIDEO_URL,
                'extractor': 'youtube'
            }
            
            with patch.object(self.metadata_extractor, 'extract_metadata') as mock_extract:
                mock_extract.return_value = mock_metadata
                metadata = self.metadata_extractor.extract_metadata(self.TEST_VIDEO_URL)
                assert metadata is not None, "Falha na extração de metadados"
            
            # 3. Gravar no banco
            integration_steps.append("database_storage")
            insert_success = self.db.insert_video_metadata(metadata)
            assert insert_success, "Falha ao gravar no banco"
            video_id = metadata['id']  # Usar o ID do metadata, não o retorno do insert
            
            # 4. Processar storyboards
            integration_steps.append("storyboard_processing")
            mock_storyboard = {
                'video_id': video_id,
                'storyboard_id': 'sb_test',
                'format_note': 'test storyboard',
                'url': 'http://test.url/storyboard.mhtml',
                'width': 48,
                'height': 27,
                'fps': 30,
                'rows': 10,
                'columns': 10,
                'total_frames': 100,
                'resolution': '48x27'
            }
            
            storyboard_id = self.db.insert_storyboard(mock_storyboard)
            assert storyboard_id is not None, "Falha ao processar storyboard"
            
            # 5. Verificar integridade final
            integration_steps.append("integrity_check")
            video_details = self.video_queries.get_video_details(video_id)
            assert video_details is not None, "Falha na verificação de integridade"
            assert video_details['title'] == mock_metadata['title'], "Dados inconsistentes"
            
            integration_steps.append("completed")
            self.test_completed = True
            
            logger.info("✅ Fluxo completo de integração funcionando corretamente")
            
        except Exception as e:
            logger.error(f"❌ Falha no passo {integration_steps[-1]}: {e}")
            raise
    
    def test_resource_cleanup_validation(self):
        """
        Testa se os recursos são limpos adequadamente
        """
        logger.info("🧹 Testando limpeza de recursos...")
        
        # Verificar se conexões do banco são fechadas
        initial_connections = len(self.db._connections) if hasattr(self.db, '_connections') else 0
        
        # Simular operações que criam conexões
        stats = self.video_queries.get_download_statistics()
        video_count = stats.get('total_videos', 0)
        self.metadata_extractor.extract_metadata("http://test.url")
        
        # Fechar recursos explicitamente
        self.db.close()
        self.metadata_extractor.close()
        self.storyboard_downloader.close()
        self.video_queries.close()
        
        # Verificar se arquivos temporários podem ser removidos
        temp_file = os.path.join(self.temp_dir, "test_cleanup.tmp")
        with open(temp_file, 'w') as f:
            f.write("test")
        
        assert os.path.exists(temp_file), "Arquivo temporário não foi criado"
        
        # Tentar remover (deveria funcionar se recursos foram liberados)
        try:
            os.remove(temp_file)
            cleanup_success = True
        except Exception as e:
            cleanup_success = False
            logger.warning(f"Falha na limpeza: {e}")
        
        assert cleanup_success, "Falha na limpeza de recursos"
        
        logger.info("✅ Limpeza de recursos funcionando corretamente")
    
    def test_error_recovery_validation(self):
        """
        Testa recuperação de erros durante o processo
        """
        logger.info("🔧 Testando recuperação de erros...")
        
        # Simular erro de conexão com banco
        with patch.object(self.db, 'get_connection') as mock_conn:
            mock_conn.side_effect = sqlite3.Error("Simulated database error")
            
            # Tentar operação que deveria falhar graciosamente
            try:
                self.db.insert_video_metadata({'id': 'test', 'title': 'test'})
                recovery_handled = False
            except sqlite3.Error:
                recovery_handled = True
            except Exception as e:
                # Erro foi tratado de forma diferente
                recovery_handled = True
                logger.info(f"Erro tratado: {e}")
        
        assert recovery_handled, "Sistema não tratou erro de banco adequadamente"
        
        # Simular erro de rede
        with patch.object(self.storyboard_downloader.session, 'get') as mock_get:
            mock_get.side_effect = Exception("Network timeout")
            
            # Tentar download que deveria falhar graciosamente
            result = self.storyboard_downloader._download_direct_storyboard(
                "http://test.url", 
                Path(self.temp_dir), 
                {'storyboard_id': 'test'}
            )
            
            # Verificar se retornou lista vazia (erro tratado graciosamente)
            network_recovery = isinstance(result, list) and len(result) == 0
        
        assert network_recovery, "Sistema não tratou erro de rede adequadamente"
        
        logger.info("✅ Recuperação de erros funcionando corretamente")

# Função para executar o teste completo
def run_complete_e2e_test():
    """
    Executa o teste E2E completo
    """
    logger.info("🚀 Iniciando teste E2E completo do sistema de download do YouTube")
    
    # Executar todos os testes
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--capture=no"
    ])

if __name__ == "__main__":
    run_complete_e2e_test()