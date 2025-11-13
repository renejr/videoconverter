import os
import sys
import json

sys.path.append(os.getcwd())
from database.video_metadata_db import VideoMetadataDB

def run():
    db_path = os.path.join(os.getcwd(), "test_video_metadata.db")
    db = VideoMetadataDB(db_path)
    metadata = {
        'id': 'TEST123',
        'title': 'Vídeo de Teste',
        'uploader': 'Canal de Teste',
        'webpage_url': 'https://youtu.be/TEST123',
        'extractor': 'youtube',
        'formats': None,
        'thumbnails': None,
        'chapters': None,
        'subtitles': {},
        'automatic_captions': {},
    }
    ok = db.insert_video_metadata(metadata)
    print("insert_video_metadata:", ok)
    db.close()

if __name__ == "__main__":
    run()
