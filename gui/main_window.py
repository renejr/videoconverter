"""
Janela Principal do Conversor de Vídeos
Interface gráfica principal com todos os controles de conversão
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QCheckBox,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from core.ffmpeg_installer import FFmpegInstaller
from core.video_converter import VideoConverterManager
from core.queue_manager import ConversionQueueManager
from utils.config import (
    SUPPORTED_OUTPUT_FORMATS,
    FPS_OPTIONS,
    RESOLUTION_PRESETS,
    WINDOW_MIN_SIZE,
    WINDOW_DEFAULT_SIZE,
    MAIN_WINDOW_STYLE,
)


class VideoConverterWindow(QMainWindow):
    """
    Janela principal da aplicação de conversão de vídeos
    Contém todos os controles e interface do usuário
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Converter - Conversor de Vídeo")
        self.setMinimumSize(*WINDOW_MIN_SIZE)
        self.resize(*WINDOW_DEFAULT_SIZE)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        self.video_converter = VideoConverterManager()
        self.queue_manager = ConversionQueueManager()
        self.conversion_thread = None
        self.init_ui()
        self._setup_queue_callbacks()
        self.check_ffmpeg_installation()

    def init_ui(self):
        """
        Inicializa a interface do usuário
        Cria todos os widgets e layouts da janela principal
        """
        self.setWindowTitle("Conversor de Vídeos - v1.0")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(700, 500)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title_label = QLabel("Conversor de Formatos de Vídeo")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Seção de seleção de arquivos
        file_group = self.create_file_selection_group()
        main_layout.addWidget(file_group)

        # Seção de configurações
        config_group = self.create_configuration_group()
        main_layout.addWidget(config_group)

        # Seção de progresso
        progress_group = self.create_progress_group()
        main_layout.addWidget(progress_group)

        # Botões de ação
        button_layout = self.create_action_buttons()
        main_layout.addLayout(button_layout)

        # Log de saída
        log_group = self.create_log_group()
        main_layout.addWidget(log_group)

    def create_file_selection_group(self):
        """
        Cria o grupo de seleção de arquivos
        Inclui campos para arquivo de entrada e pasta de saída
        """
        group = QGroupBox("Seleção de Arquivos")
        layout = QGridLayout(group)

        # Arquivo de entrada
        layout.addWidget(QLabel("Vídeo de Entrada:"), 0, 0)
        self.input_file_edit = QLineEdit()
        self.input_file_edit.setPlaceholderText("Selecione o arquivo de vídeo...")
        layout.addWidget(self.input_file_edit, 0, 1)

        self.browse_input_btn = QPushButton("Procurar")
        self.browse_input_btn.clicked.connect(self.browse_input_file)
        layout.addWidget(self.browse_input_btn, 0, 2)

        # Pasta de saída
        layout.addWidget(QLabel("Pasta de Destino:"), 1, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Selecione a pasta de destino...")
        layout.addWidget(self.output_dir_edit, 1, 1)

        self.browse_output_btn = QPushButton("Procurar")
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        layout.addWidget(self.browse_output_btn, 1, 2)

        return group

    def create_configuration_group(self):
        """
        Cria o grupo de configurações de conversão
        Inclui formato, FPS, dimensões e outras opções
        """
        group = QGroupBox("Configurações de Conversão")
        layout = QGridLayout(group)

        # Formato de saída
        layout.addWidget(QLabel("Formato de Saída:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(SUPPORTED_OUTPUT_FORMATS)
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        layout.addWidget(self.format_combo, 0, 1)

        # FPS
        layout.addWidget(QLabel("FPS:"), 0, 2)
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(FPS_OPTIONS)
        self.fps_combo.currentTextChanged.connect(self.on_fps_changed)
        layout.addWidget(self.fps_combo, 0, 3)

        self.fps_custom = QSpinBox()
        self.fps_custom.setRange(1, 120)
        self.fps_custom.setValue(30)
        self.fps_custom.setEnabled(False)
        layout.addWidget(self.fps_custom, 0, 4)

        # Dimensões
        layout.addWidget(QLabel("Resolução:"), 1, 0)
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(list(RESOLUTION_PRESETS.keys()))
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        layout.addWidget(self.resolution_combo, 1, 1)

        # Largura e altura personalizadas
        layout.addWidget(QLabel("Largura:"), 1, 2)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 7680)
        self.width_spin.setValue(1920)
        self.width_spin.setEnabled(False)
        layout.addWidget(self.width_spin, 1, 3)

        layout.addWidget(QLabel("Altura:"), 1, 4)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 4320)
        self.height_spin.setValue(1080)
        self.height_spin.setEnabled(False)
        layout.addWidget(self.height_spin, 1, 5)

        # Opções avançadas
        layout.addWidget(QLabel("Qualidade:"), 2, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Alta", "Média", "Baixa", "Personalizada"])
        layout.addWidget(self.quality_combo, 2, 1)

        # Codec de vídeo
        layout.addWidget(QLabel("Codec de Vídeo:"), 2, 2)
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["H.264 (Recomendado)", "H.265 (HEVC)"])
        self.codec_combo.setCurrentText("H.264 (Recomendado)")  # Padrão H.264
        self.codec_combo.currentTextChanged.connect(self.on_codec_changed)
        layout.addWidget(self.codec_combo, 2, 3)

        # Manter transparência
        self.transparency_check = QCheckBox("Manter Transparência")
        layout.addWidget(self.transparency_check, 2, 4, 1, 2)

        return group

    def create_progress_group(self):
        """
        Cria o grupo de progresso da conversão
        Inclui barra de progresso e informações de status
        """
        group = QGroupBox("Progresso da Conversão")
        layout = QVBoxLayout(group)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("Pronto para conversão")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        return group

    def create_action_buttons(self):
        """
        Cria os botões de ação principal
        Inclui botões de converter, cancelar e limpar
        """
        layout = QHBoxLayout()

        # Botão converter
        self.convert_btn = QPushButton("Converter Vídeo")
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_btn)

        # Botão cancelar
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        layout.addWidget(self.cancel_btn)

        # Botão limpar
        self.clear_btn = QPushButton("Limpar")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_fields)
        layout.addWidget(self.clear_btn)

        return layout

    def create_log_group(self):
        """
        Cria o grupo de log de saída
        Mostra informações detalhadas do processo de conversão
        """
        group = QGroupBox("Log de Conversão")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        return group

    def browse_input_file(self):
        """
        Abre dialog para seleção do arquivo de vídeo de entrada
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Vídeo de Entrada",
            "",
            "Vídeos (*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv);;Todos os arquivos (*)",
        )
        if file_path:
            self.input_file_edit.setText(file_path)
            self.log_message(f"Arquivo selecionado: {os.path.basename(file_path)}")

    def browse_output_directory(self):
        """
        Abre dialog para seleção da pasta de destino
        """
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Destino")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.log_message(f"Pasta de destino: {dir_path}")

    def on_fps_changed(self, text):
        """
        Callback para mudança na seleção de FPS
        Habilita/desabilita campo personalizado
        """
        self.fps_custom.setEnabled(text == "Personalizado")

    def on_resolution_changed(self, text):
        """
        Callback para mudança na seleção de resolução
        Habilita/desabilita campos de largura e altura
        """
        is_custom = text == "Personalizada"
        self.width_spin.setEnabled(is_custom)
        self.height_spin.setEnabled(is_custom)

    def on_format_changed(self, text):
        """
        Callback para mudança no formato de saída
        Valida compatibilidade do codec com o formato
        """
        self._validate_codec_compatibility()

    def on_codec_changed(self, text):
        """
        Callback para mudança na seleção de codec
        Registra a mudança no log
        """
        codec_name = "H.264" if "H.264" in text else "H.265"
        self.log_message(f"Codec selecionado: {codec_name}")
        self._validate_codec_compatibility()

    def _validate_codec_compatibility(self):
        """
        Valida a compatibilidade entre codec e formato
        Desabilita H.265 para formato AVI
        """
        current_format = self.format_combo.currentText()
        is_avi = "AVI" in current_format.upper()

        if is_avi:
            # Para AVI, forçar H.264 e desabilitar H.265
            if "H.265" in self.codec_combo.currentText():
                self.codec_combo.setCurrentText("H.264 (Recomendado)")
                self.log_message(
                    "⚠️ H.265 não é compatível com AVI. Alterado para H.264."
                )

            # Desabilitar opção H.265 para AVI
            for i in range(self.codec_combo.count()):
                item_text = self.codec_combo.itemText(i)
                if "H.265" in item_text:
                    # Criar um modelo personalizado para desabilitar o item
                    model = self.codec_combo.model()
                    item = model.item(i)
                    item.setEnabled(False)
        else:
            # Para outros formatos, habilitar todas as opções
            for i in range(self.codec_combo.count()):
                model = self.codec_combo.model()
                item = model.item(i)
                item.setEnabled(True)

    def check_ffmpeg_installation(self):
        """
        Verifica se o FFmpeg está instalado
        Se não estiver, oferece instalação automática
        """
        installer = FFmpegInstaller()
        if not installer.is_ffmpeg_installed():
            self.log_message(
                "FFmpeg não encontrado. Iniciando instalação automática..."
            )
            self.install_ffmpeg()
        else:
            self.log_message("FFmpeg encontrado e pronto para uso.")

    def install_ffmpeg(self):
        """
        Instala o FFmpeg automaticamente
        """
        installer = FFmpegInstaller()

        def progress_callback(message, progress):
            self.status_label.setText(message)
            self.progress_bar.setValue(int(progress))
            self.log_message(f"{message} ({progress:.1f}%)")

        # Mostrar barra de progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Instalar em thread separada (simplificado para demonstração)
        success = installer.install_ffmpeg(progress_callback)

        if success:
            self.log_message("FFmpeg instalado com sucesso!")
            self.status_label.setText("FFmpeg pronto para uso")
        else:
            self.log_message("Falha na instalação do FFmpeg")
            QMessageBox.warning(
                self, "Erro", "Não foi possível instalar o FFmpeg automaticamente."
            )

        self.progress_bar.setVisible(False)

    def start_conversion(self):
        """
        Inicia o processo de conversão de vídeo usando o sistema de fila
        """
        # Validar campos obrigatórios
        if not self.input_file_edit.text():
            QMessageBox.warning(
                self, "Erro", "Selecione um arquivo de vídeo de entrada."
            )
            return

        if not self.output_dir_edit.text():
            QMessageBox.warning(self, "Erro", "Selecione uma pasta de destino.")
            return

        input_file = self.input_file_edit.text()
        output_dir = self.output_dir_edit.text()

        # Validar formato de entrada
        if not self.video_converter.is_supported_input_format(input_file):
            QMessageBox.warning(self, "Erro", "Formato de arquivo não suportado.")
            return

        # Coletar configurações
        settings = self.get_conversion_settings()

        # Configurar callbacks específicos do job
        job_callbacks = {
            "job_progress": self.on_progress_updated,
            "job_status": self.on_status_updated,
            "job_finished": self.on_conversion_finished,
            "log": self.log_message,
        }

        # Desabilitar controles durante conversão
        self.set_conversion_state(True)

        # Adicionar job à fila e iniciar processamento
        job_id = self.queue_manager.add_job(
            input_file=input_file,
            output_dir=output_dir,
            settings=settings,
            callbacks=job_callbacks,
        )

        # Iniciar a fila se não estiver rodando
        self.queue_manager.start_queue()

        self.log_message(f"Job {job_id} adicionado à fila de conversão")

    def cancel_conversion(self):
        """
        Cancela a conversão em andamento
        """
        reply = QMessageBox.question(
            self,
            "Cancelar Conversão",
            "Tem certeza que deseja cancelar todas as conversões?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.queue_manager.stop_queue()
            self.log_message("Fila de conversão parada pelo usuário")
            self.set_conversion_state(False)
            self.status_label.setText("Conversão cancelada")

    def clear_fields(self):
        """
        Limpa todos os campos da interface
        """
        self.input_file_edit.clear()
        self.output_dir_edit.clear()
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Pronto para conversão")
        self.log_message("Campos limpos.")

    def log_message(self, message):
        """
        Adiciona uma mensagem ao log de saída
        """
        self.log_text.append(f"[{self.get_timestamp()}] {message}")

    def get_timestamp(self):
        """
        Retorna timestamp atual formatado
        """
        from datetime import datetime

        return datetime.now().strftime("%H:%M:%S")

    def get_conversion_settings(self):
        """
        Coleta todas as configurações de conversão da interface

        Returns:
            dict: Configurações de conversão
        """
        # Determinar o codec baseado na seleção
        codec_text = self.codec_combo.currentText()
        codec = "h264" if "H.264" in codec_text else "hevc"

        settings = {
            "format": self.format_combo.currentText(),
            "quality": self.quality_combo.currentText(),
            "transparency": self.transparency_check.isChecked(),
            "fps": self.fps_combo.currentText(),
            "resolution": self.resolution_combo.currentText(),
            "codec": codec,
        }

        # FPS personalizado
        if settings["fps"] == "Personalizado":
            settings["fps_custom"] = self.fps_custom.value()

        # Resolução personalizada
        if settings["resolution"] == "Personalizada":
            settings["width"] = self.width_spin.value()
            settings["height"] = self.height_spin.value()

        return settings

    def set_conversion_state(self, converting):
        """
        Habilita/desabilita controles durante conversão

        Args:
            converting: True se conversão está em andamento
        """
        # Desabilitar controles de entrada
        self.browse_input_btn.setEnabled(not converting)
        self.browse_output_btn.setEnabled(not converting)
        self.format_combo.setEnabled(not converting)
        self.fps_combo.setEnabled(not converting)
        self.fps_custom.setEnabled(
            not converting and self.fps_combo.currentText() == "Personalizado"
        )
        self.resolution_combo.setEnabled(not converting)
        self.width_spin.setEnabled(
            not converting and self.resolution_combo.currentText() == "Personalizada"
        )
        self.height_spin.setEnabled(
            not converting and self.resolution_combo.currentText() == "Personalizada"
        )
        self.quality_combo.setEnabled(not converting)
        self.transparency_check.setEnabled(not converting)

        # Controlar botões
        self.convert_btn.setEnabled(not converting)
        self.cancel_btn.setEnabled(converting)

        # Mostrar/ocultar barra de progresso
        self.progress_bar.setVisible(converting)
        if not converting:
            self.progress_bar.setValue(0)

    def on_progress_updated(self, progress):
        """
        Callback para atualização de progresso

        Args:
            progress: Progresso em porcentagem (0-100)
        """
        self.progress_bar.setValue(progress)

    def on_status_updated(self, status):
        """
        Callback para atualização de status

        Args:
            status: Mensagem de status
        """
        self.status_label.setText(status)

    def on_conversion_finished(self, success, message):
        """
        Callback para conclusão da conversão

        Args:
            success: True se conversão foi bem-sucedida
            message: Mensagem de resultado
        """
        self.set_conversion_state(False)

        if success:
            QMessageBox.information(self, "Sucesso", message)
            self.log_message("✓ Conversão concluída com sucesso!")
        else:
            QMessageBox.critical(self, "Erro", message)
            self.log_message(f"✗ Erro na conversão: {message}")

        self.status_label.setText("Pronto para conversão")

    def _setup_queue_callbacks(self):
        """
        Configura callbacks para o gerenciador de fila
        """
        callbacks = {
            "queue_updated": self._on_queue_updated,
            "job_started": self._on_job_started,  # Implementado: callback que estava faltando
            "job_completed": self._on_job_completed,
            "job_failed": self._on_job_failed,
            "job_progress": self._on_job_progress,  # Corrigido: usar 'job_progress' em vez de 'job_status'
            "log": self._on_log_message,
        }
        self.queue_manager.set_global_callbacks(callbacks)

    def _on_queue_updated(self, queue_data):
        """
        Callback para atualização da fila de conversão

        Args:
            queue_data: Dados atualizados da fila
        """
        self.log_message(f"Fila atualizada: {len(queue_data)} jobs na fila")

    def _on_job_started(self, job_id, job_data):
        """
        Callback para início de um job de conversão

        Args:
            job_id: ID do job iniciado
            job_data: Dados do job
        """
        self.log_message(
            f"Iniciando conversão: {job_data.get('input_file', 'arquivo desconhecido')}"
        )
        self.set_conversion_state(True)
        self.status_label.setText("Conversão iniciada...")

    def _on_job_completed(self, job_id, result):
        """
        Callback para conclusão bem-sucedida de um job

        Args:
            job_id: ID do job concluído
            result: Resultado da conversão
        """
        self.log_message(f"✓ Conversão concluída com sucesso! Job ID: {job_id}")
        self.set_conversion_state(False)
        self.status_label.setText("Conversão concluída")
        QMessageBox.information(self, "Sucesso", "Conversão concluída com sucesso!")

    def _on_job_failed(self, job_id, error):
        """
        Callback para falha em um job

        Args:
            job_id: ID do job que falhou
            error: Erro ocorrido
        """
        self.log_message(f"✗ Erro na conversão! Job ID: {job_id} - Erro: {error}")
        self.set_conversion_state(False)
        self.status_label.setText("Erro na conversão")
        QMessageBox.critical(self, "Erro", f"Erro na conversão: {error}")

    def _on_job_progress(self, job_id, progress_data):
        """
        Callback para atualização de progresso de um job

        Args:
            job_id: ID do job
            progress_data: Dados de progresso (porcentagem, status, etc.)
        """
        if isinstance(progress_data, dict):
            percentage = progress_data.get("percentage", 0)
            status = progress_data.get("status", "")
        else:
            # Se progress_data for apenas um número (porcentagem)
            percentage = progress_data
            status = f"Progresso: {percentage}%"

        self.progress_bar.setValue(int(percentage))
        if status:
            self.status_label.setText(status)

        self.log_message(f"Progresso Job {job_id}: {percentage}%")

    def _on_log_message(self, message):
        """
        Callback para mensagens de log

        Args:
            message: Mensagem de log
        """
        self.log_message(message)
