#!/usr/bin/env python3
"""
Testes automatizados para tratamento de playlists

Valida que:
- Playlists são inseridas como registros pai com is_playlist=1
- Vídeos filhos são inseridos individualmente
- Relações playlist_videos são criadas com posição correta
"""

import os
import sys
import unittest
from pathlib import Path

# Ajusta o sys.path para permitir importação de pacotes 'database'
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from database.metadata_extractor import MetadataExtractor
from database.video_metadata_db import VideoMetadataDB


class PlaylistHandlingTest(unittest.TestCase):
    """Testa o fluxo de playlist -> filhos e vínculo"""

    def setUp(self):
        """Cria um banco de dados temporário para os testes"""
        self.test_db_path = str(Path("test_playlist.db"))
        # Remover DB anterior se existir
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except Exception:
            pass

        self.db = VideoMetadataDB(self.test_db_path)
        self.extractor = MetadataExtractor(self.test_db_path)

    def tearDown(self):
        """Fecha conexões e remove o banco de testes"""
        try:
            self.extractor.close()
        except Exception:
            pass
        try:
            self.db.close()
        except Exception:
            pass
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except Exception:
            pass

    def _mock_playlist_metadata(self):
        """Retorna um dicionário de metadados simulando uma playlist com dois filhos"""
        return {
            '_type': 'playlist',
            'id': 'TEST_PLAYLIST_123',
            'title': 'Playlist de Teste',
            'uploader': 'Canal de Teste',
            'webpage_url': 'https://www.youtube.com/playlist?list=TEST_PLAYLIST_123',
            'entries': [
                {
                    'id': 'VID_1',
                    'title': 'Vídeo 1',
                    'uploader': 'Canal de Teste',
                    'duration': 60,
                    'webpage_url': 'https://www.youtube.com/watch?v=VID_1',
                    'playlist_index': 1,
                    'thumbnails': [],
                    'formats': []
                },
                {
                    'id': 'VID_2',
                    'title': 'Vídeo 2',
                    'uploader': 'Canal de Teste',
                    'duration': 120,
                    'webpage_url': 'https://www.youtube.com/watch?v=VID_2',
                    'playlist_index': 2,
                    'thumbnails': [],
                    'formats': []
                }
            ],
            'thumbnails': [],
            'formats': []
        }

    def test_process_and_store_playlist(self):
        """Verifica se playlist e filhos são gravados corretamente e vinculados"""
        # Monkeypatch da extração para retornar metadados simulados
        mock_data = self._mock_playlist_metadata()

        def mock_extract_metadata(url: str, save_thumbnails: bool = False):
            return mock_data

        # Substitui método de extração
        self.extractor.extract_metadata = mock_extract_metadata

        # Executa processamento com URL fictícia
        parent_id = self.extractor.process_and_store_metadata(
            url="https://www.youtube.com/playlist?list=TEST_PLAYLIST_123",
            save_thumbnails=False
        )

        self.assertEqual(parent_id, mock_data['id'], "ID da playlist pai deve ser retornado")

        # Verificar playlist pai com is_playlist=1
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT is_playlist FROM videos WHERE video_id = ?", (parent_id,))
        row = cur.fetchone()
        self.assertIsNotNone(row, "Playlist pai deve existir na tabela de vídeos")
        self.assertEqual(row[0], 1, "Playlist deve ter is_playlist=1")

        # Verificar filhos
        children_ids = ['VID_1', 'VID_2']
        for cid in children_ids:
            cur.execute("SELECT COUNT(*) FROM videos WHERE video_id = ?", (cid,))
            count = cur.fetchone()[0]
            self.assertEqual(count, 1, f"Vídeo filho {cid} deve existir em videos")

        # Verificar vínculos e posição
        cur.execute(
            "SELECT child_video_id, position FROM playlist_videos WHERE playlist_id = ? ORDER BY position",
            (parent_id,)
        )
        links = cur.fetchall()
        self.assertEqual(len(links), 2, "Devem existir dois vínculos de playlist")
        self.assertEqual(links[0][0], 'VID_1')
        self.assertEqual(links[0][1], 1)
        self.assertEqual(links[1][0], 'VID_2')
        self.assertEqual(links[1][1], 2)


if __name__ == '__main__':
    unittest.main()