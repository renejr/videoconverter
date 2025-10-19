#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Validação do Controle de Estado dos Botões
===================================================

Este teste valida se o sistema de controle de estado dos botões funciona
corretamente durante o processo de conversão de vídeos.

Testa especificamente:
- Estado inicial dos botões
- Estado durante conversão
- Estado após conclusão de todos os jobs
- Callbacks e timing corretos

Vídeos de teste:
- E:\\TEMP\\VID-20220805-WA0132.mp4
- E:\\TEMP\\100a5268b0bc4e6eab30923ca7ee5bac.mp4

Destino: E:\\pyProjs\\exports
Formato: MKV
"""

import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz ao path para importações
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from gui.main_window_tkinter import MainWindow
from core.queue_manager import ConversionQueueManager


class ButtonStateValidator:
    """
    Classe para validar o comportamento do controle de estado dos botões
    durante o processo de conversão de vídeos.
    """

    def __init__(self):
        """Inicializa o validador de estado dos botões."""
        self.test_videos = [
            r"E:\TEMP\VID-20220805-WA0132.mp4",
            r"E:\TEMP\100a5268b0bc4e6eab30923ca7ee5bac.mp4",
        ]
        self.output_dir = r"E:\pyProjs\exports"
        self.output_format = "mkv"

        # Estados dos botões para validação
        self.button_states = []
        self.conversion_events = []

        # Flags de controle
        self.conversion_started = False
        self.conversion_finished = False
        self.all_jobs_completed = False

        # Contadores
        self.jobs_started = 0
        self.jobs_completed = 0
        self.jobs_failed = 0

        # Interface
        self.root = None
        self.main_window = None

        print("=" * 60)
        print("TESTE DE VALIDAÇÃO DO CONTROLE DE ESTADO DOS BOTÕES")
        print("=" * 60)
        print(f"Vídeos de teste: {len(self.test_videos)}")
        for i, video in enumerate(self.test_videos, 1):
            print(f"  {i}. {video}")
        print(f"Diretório destino: {self.output_dir}")
        print(f"Formato de saída: {self.output_format.upper()}")
        print("=" * 60)

    def log_event(self, event_type, details):
        """
        Registra um evento durante o teste.

        Args:
            event_type (str): Tipo do evento
            details (str): Detalhes do evento
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        event = f"[{timestamp}] {event_type}: {details}"
        self.conversion_events.append(event)
        print(event)

    def capture_button_state(self, stage):
        """
        Captura o estado atual dos botões.

        Args:
            stage (str): Estágio atual do teste
        """
        if not self.main_window:
            return

        try:
            convert_state = str(self.main_window.convert_btn["state"])
            cancel_state = str(self.main_window.cancel_btn["state"])
            clear_state = str(self.main_window.clear_btn["state"])
            status_text = self.main_window.status_var.get()

            state_info = {
                "stage": stage,
                "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "convert_button": convert_state,
                "cancel_button": cancel_state,
                "clear_button": clear_state,
                "status": status_text,
            }

            self.button_states.append(state_info)
            self.log_event(
                "ESTADO_BOTÕES",
                f"{stage} - Convert: {convert_state}, Cancel: {cancel_state}, "
                f"Clear: {clear_state}, Status: '{status_text}'",
            )

        except Exception as e:
            self.log_event("ERRO", f"Erro ao capturar estado dos botões: {e}")

    def validate_initial_state(self):
        """Valida o estado inicial dos botões."""
        self.log_event("VALIDAÇÃO", "Verificando estado inicial dos botões...")
        self.capture_button_state("INICIAL")

        # Estado esperado inicial
        expected = {
            "convert_button": "normal",  # Habilitado
            "cancel_button": "disabled",  # Desabilitado
            "clear_button": "normal",  # Habilitado
        }

        current = self.button_states[-1]

        for button, expected_state in expected.items():
            if current[button] != expected_state:
                self.log_event(
                    "ERRO",
                    f"Estado inicial incorreto - {button}: "
                    f"esperado '{expected_state}', atual '{current[button]}'",
                )
                return False

        self.log_event("SUCESSO", "Estado inicial dos botões está correto!")
        return True

    def validate_conversion_state(self):
        """Valida o estado dos botões durante a conversão."""
        self.log_event("VALIDAÇÃO", "Verificando estado durante conversão...")
        self.capture_button_state("CONVERSÃO")

        # Estado esperado durante conversão
        expected = {
            "convert_button": "disabled",  # Desabilitado
            "cancel_button": "normal",  # Habilitado
            "clear_button": "disabled",  # Desabilitado
        }

        current = self.button_states[-1]

        for button, expected_state in expected.items():
            if current[button] != expected_state:
                self.log_event(
                    "ERRO",
                    f"Estado durante conversão incorreto - {button}: "
                    f"esperado '{expected_state}', atual '{current[button]}'",
                )
                return False

        self.log_event("SUCESSO", "Estado dos botões durante conversão está correto!")
        return True

    def validate_final_state(self):
        """Valida o estado final dos botões após conclusão."""
        self.log_event("VALIDAÇÃO", "Verificando estado final dos botões...")
        self.capture_button_state("FINAL")

        # Estado esperado final
        expected = {
            "convert_button": "normal",  # Habilitado
            "cancel_button": "disabled",  # Desabilitado
            "clear_button": "normal",  # Habilitado
        }

        current = self.button_states[-1]

        for button, expected_state in expected.items():
            if current[button] != expected_state:
                self.log_event(
                    "ERRO",
                    f"Estado final incorreto - {button}: "
                    f"esperado '{expected_state}', atual '{current[button]}'",
                )
                return False

        self.log_event("SUCESSO", "Estado final dos botões está correto!")
        return True

    def setup_callbacks(self):
        """Configura callbacks para monitorar o processo."""
        if not self.main_window or not self.main_window.queue_manager:
            return

        # Salvar callbacks originais
        original_callbacks = self.main_window.queue_manager.global_callbacks.copy()

        # Callback para job completado
        def on_job_completed_wrapper(job_data):
            self.jobs_completed += 1
            job_id = job_data.get("id", "unknown")
            self.log_event(
                "JOB_COMPLETADO",
                f"Job {job_id} concluído com sucesso "
                f"({self.jobs_completed}/{len(self.test_videos)})",
            )

            # Capturar estado após job individual (não deve mudar botões ainda)
            self.capture_button_state(f"APÓS_JOB_{self.jobs_completed}")

            # Chamar callback original
            if original_callbacks.get("job_completed"):
                original_callbacks["job_completed"](job_data)

        # Callback para job falhado
        def on_job_failed_wrapper(job_data):
            self.jobs_failed += 1
            job_id = job_data.get("id", "unknown")
            error = job_data.get("error_message", "Erro desconhecido")
            self.log_event(
                "JOB_FALHADO",
                f"Job {job_id} falhou: {error} " f"({self.jobs_failed} falhas)",
            )

            # Capturar estado após falha
            self.capture_button_state(f"APÓS_FALHA_{self.jobs_failed}")

            # Chamar callback original
            if original_callbacks.get("job_failed"):
                original_callbacks["job_failed"](job_data)

        # Callback para fila finalizada
        def on_queue_finished_wrapper(total, successful, failed):
            self.all_jobs_completed = True
            self.conversion_finished = True
            self.log_event(
                "FILA_FINALIZADA",
                f"Todos os jobs concluídos - Total: {total}, "
                f"Sucessos: {successful}, Falhas: {failed}",
            )

            # Aguardar um pouco para garantir que a UI foi atualizada
            self.root.after(100, lambda: self.validate_final_state())

            # Chamar callback original
            if original_callbacks.get("queue_finished"):
                original_callbacks["queue_finished"](total, successful, failed)

        # Configurar callbacks globais
        self.main_window.queue_manager.set_global_callbacks(
            {
                "job_completed": on_job_completed_wrapper,
                "job_failed": on_job_failed_wrapper,
                "queue_finished": on_queue_finished_wrapper,
            }
        )

    def check_prerequisites(self):
        """
        Verifica se os pré-requisitos para o teste estão atendidos.

        Returns:
            bool: True se todos os pré-requisitos estão OK
        """
        self.log_event("VERIFICAÇÃO", "Checando pré-requisitos...")

        # Verificar se os vídeos existem
        for video in self.test_videos:
            if not os.path.exists(video):
                self.log_event("ERRO", f"Vídeo não encontrado: {video}")
                return False
            else:
                size_mb = os.path.getsize(video) / (1024 * 1024)
                self.log_event("INFO", f"Vídeo encontrado: {video} ({size_mb:.1f} MB)")

        # Verificar/criar diretório de destino
        os.makedirs(self.output_dir, exist_ok=True)
        if not os.path.exists(self.output_dir):
            self.log_event(
                "ERRO", f"Não foi possível criar diretório: {self.output_dir}"
            )
            return False
        else:
            self.log_event("INFO", f"Diretório de destino OK: {self.output_dir}")

        self.log_event("SUCESSO", "Todos os pré-requisitos atendidos!")
        return True

    def run_test(self):
        """Executa o teste completo de validação."""
        if not self.check_prerequisites():
            return False

        try:
            # Criar interface
            self.root = tk.Tk()
            self.main_window = MainWindow(self.root)

            # Configurar callbacks de monitoramento
            self.setup_callbacks()

            # Validar estado inicial
            self.root.after(100, self.validate_initial_state)

            # Adicionar vídeos e iniciar conversão
            def start_conversion():
                self.log_event("INÍCIO", "Adicionando vídeos à lista...")

                # Adicionar vídeos
                for video in self.test_videos:
                    if video not in [
                        f["path"] for f in self.main_window.selected_files
                    ]:
                        file_info = {
                            "path": video,
                            "name": os.path.basename(video),
                            "status": "Pendente",
                            "progress": "0%",
                            "gpu": "-",
                            "job_id": None,
                        }
                        self.main_window.selected_files.append(file_info)
                    self.jobs_started += 1
                    self.log_event(
                        "VÍDEO_ADICIONADO", f"Adicionado: {os.path.basename(video)}"
                    )

                self.main_window.update_files_tree()

                # Configurar formato de saída
                self.main_window.format_var.set(self.output_format)
                self.main_window.output_dir_var.set(self.output_dir)

                self.log_event(
                    "CONFIGURAÇÃO",
                    f"Formato: {self.output_format.upper()}, "
                    f"Destino: {self.output_dir}",
                )

                # Aguardar um pouco e iniciar conversão
                self.root.after(500, start_actual_conversion)

            def start_actual_conversion():
                self.log_event("CONVERSÃO", "Iniciando processo de conversão...")
                self.conversion_started = True

                # Iniciar conversão
                self.main_window.start_conversion()

                # Validar estado durante conversão
                self.root.after(1000, self.validate_conversion_state)

                # Configurar timeout de segurança
                self.root.after(300000, self.timeout_handler)  # 5 minutos

            # Iniciar teste após interface estar pronta
            self.root.after(1000, start_conversion)

            # Executar interface
            self.root.mainloop()

            return True

        except Exception as e:
            self.log_event("ERRO", f"Erro durante execução do teste: {e}")
            return False

    def timeout_handler(self):
        """Manipula timeout do teste."""
        if not self.conversion_finished:
            self.log_event("TIMEOUT", "Teste excedeu tempo limite de 5 minutos")
            self.generate_report()
            self.root.quit()

    def generate_report(self):
        """Gera relatório final do teste."""
        print("\n" + "=" * 60)
        print("RELATÓRIO FINAL DO TESTE")
        print("=" * 60)

        print(f"Jobs iniciados: {self.jobs_started}")
        print(f"Jobs completados: {self.jobs_completed}")
        print(f"Jobs falhados: {self.jobs_failed}")
        print(f"Conversão finalizada: {self.conversion_finished}")

        print("\nESTADOS DOS BOTÕES CAPTURADOS:")
        print("-" * 40)
        for state in self.button_states:
            print(f"[{state['timestamp']}] {state['stage']}:")
            print(f"  Convert: {state['convert_button']}")
            print(f"  Cancel: {state['cancel_button']}")
            print(f"  Clear: {state['clear_button']}")
            print(f"  Status: '{state['status']}'")
            print()

        print("EVENTOS DO TESTE:")
        print("-" * 40)
        for event in self.conversion_events:
            print(event)

        print("\n" + "=" * 60)

        # Validação final
        if self.conversion_finished and self.jobs_completed == len(self.test_videos):
            print("✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("✅ Controle de estado dos botões funcionando corretamente!")
        else:
            print("❌ TESTE FALHOU!")
            print("❌ Problemas detectados no controle de estado dos botões!")

        print("=" * 60)


def main():
    """Função principal para executar o teste."""
    print("Iniciando teste de validação do controle de estado dos botões...")

    validator = ButtonStateValidator()
    success = validator.run_test()

    if success:
        validator.generate_report()
    else:
        print("❌ Falha na execução do teste!")

    input("\nPressione Enter para sair...")


if __name__ == "__main__":
    main()
