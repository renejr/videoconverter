import sys
import os
import logging

# Adicionar o diretório do módulo ao sys.path para permitir importações relativas
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.queue_manager import ConversionQueueManager, ConversionJob
from core.video_converter import VideoConverter

def setup_logging():
    """Configura o logging para exibir mensagens no console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

def main():
    """Função principal para testar o módulo de conversão de vídeo."""
    setup_logging()
    logging.info("Iniciando o teste do módulo de conversão de vídeo...")

    queue_manager = ConversionQueueManager()
    queue_manager.start_queue()

    input_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "test_input.mp4")
    )
    output_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "test_output.mkv")
    )

    conversion_settings = {
        "format": "MKV",
        "quality": "Média",
        "resolution": "720p",
        "remove_audio": False,
    }

    def on_job_completed(job_id, output_path):
        logging.info(f"Conversão concluída! Arquivo de saída: {output_path}")
        queue_manager.stop_queue()

    def on_job_failed(job_id, error_message):
        logging.error(f"Falha na conversão: {error_message}")
        queue_manager.stop_queue()

    callbacks = {"on_completed": on_job_completed, "on_failed": on_job_failed}

    queue_manager.add_job(input_file, output_file, conversion_settings, callbacks)

    try:
        while queue_manager.is_running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        queue_manager.stop_queue()

    if os.path.exists(output_file):
        logging.info("Teste bem-sucedido: o arquivo de saída foi criado.")
        os.remove(output_file)  # Limpar o arquivo de saída
    else:
        logging.error("Teste falhou: o arquivo de saída não foi criado.")


if __name__ == "__main__":
    main()