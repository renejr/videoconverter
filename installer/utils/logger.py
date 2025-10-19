"""
📝 Sistema de Logs Avançado - VideoConverter Installer
=====================================================

Sistema de logging completo com:
- Múltiplos níveis (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Formatação colorida para terminal
- Saída para arquivo com rotação
- Timestamps precisos
- Contexto de operações
- Progress tracking
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
import colorama
from colorama import Fore, Back, Style


# Inicializar colorama para Windows
colorama.init(autoreset=True)


class LogLevel(Enum):
    """Níveis de log disponíveis"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"  # Nível customizado para sucessos


class ColoredFormatter(logging.Formatter):
    """Formatter com cores para terminal"""

    # Cores por nível
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.WHITE,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Back.WHITE,
        "SUCCESS": Fore.GREEN,
    }

    # Ícones por nível
    ICONS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨",
        "SUCCESS": "✅",
    }

    def format(self, record):
        """Formata o log com cores e ícones"""
        # Obter cor e ícone
        color = self.COLORS.get(record.levelname, Fore.WHITE)
        icon = self.ICONS.get(record.levelname, "ℹ️")

        # Timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")

        # Formatação colorida
        colored_level = f"{color}{record.levelname:<8}{Style.RESET_ALL}"

        # Mensagem formatada
        message = f"{icon} {timestamp} {colored_level} {record.getMessage()}"

        # Adicionar contexto se disponível
        if hasattr(record, "context"):
            message += f" {Fore.CYAN}[{record.context}]{Style.RESET_ALL}"

        return message


class FileFormatter(logging.Formatter):
    """Formatter para arquivo (sem cores)"""

    def format(self, record):
        """Formata o log para arquivo"""
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

        message = f"{timestamp} [{record.levelname:<8}] {record.getMessage()}"

        # Adicionar contexto se disponível
        if hasattr(record, "context"):
            message += f" [Context: {record.context}]"

        # Adicionar informações de exceção se disponível
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class Logger:
    """
    Sistema de logging avançado para o instalador

    Funcionalidades:
    - Logs coloridos no terminal
    - Logs detalhados em arquivo
    - Contexto de operações
    - Progress tracking
    - Rotação de logs
    """

    def __init__(
        self, name: str = "VideoConverter-Installer", log_dir: Optional[str] = None
    ):
        """
        Inicializa o sistema de logs

        Args:
            name: Nome do logger
            log_dir: Diretório para arquivos de log (opcional)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Configurar diretório de logs
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".vidconv_installer" / "logs"

        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Contexto atual
        self._current_context: Optional[str] = None

        # Configurar handlers
        self._setup_handlers()

        # Adicionar nível SUCCESS customizado
        self._add_success_level()

    def _setup_handlers(self):
        """Configura handlers de console e arquivo"""
        # Limpar handlers existentes
        self.logger.handlers.clear()

        # Handler para console (colorido)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)

        # Handler para arquivo (detalhado)
        log_file = self.log_dir / f"installer_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter())
        self.logger.addHandler(file_handler)

        # Handler para arquivo de erros
        error_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file, encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(FileFormatter())
        self.logger.addHandler(error_handler)

    def _add_success_level(self):
        """Adiciona nível SUCCESS customizado"""
        # Definir nível SUCCESS (entre INFO e WARNING)
        SUCCESS_LEVEL = 25
        logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

        def success(self, message, *args, **kwargs):
            if self.isEnabledFor(SUCCESS_LEVEL):
                self._log(SUCCESS_LEVEL, message, args, **kwargs)

        logging.Logger.success = success

    def set_context(self, context: str):
        """
        Define contexto atual para os logs

        Args:
            context: Nome do contexto (ex: "OS Detection", "Python Install")
        """
        self._current_context = context
        self.info(f"Iniciando: {context}")

    def clear_context(self):
        """Remove contexto atual"""
        if self._current_context:
            self.info(f"Finalizando: {self._current_context}")
        self._current_context = None

    def _log_with_context(self, level: int, message: str, *args, **kwargs):
        """Log com contexto atual"""
        extra = kwargs.get("extra", {})
        if self._current_context:
            extra["context"] = self._current_context
        kwargs["extra"] = extra

        self.logger.log(level, message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        """Log de debug"""
        self._log_with_context(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log de informação"""
        self._log_with_context(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log de aviso"""
        self._log_with_context(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log de erro"""
        self._log_with_context(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log crítico"""
        self._log_with_context(logging.CRITICAL, message, *args, **kwargs)

    def success(self, message: str, *args, **kwargs):
        """Log de sucesso"""
        self._log_with_context(25, message, *args, **kwargs)  # SUCCESS level

    def step(self, step_num: int, total_steps: int, description: str):
        """
        Log de passo de instalação

        Args:
            step_num: Número do passo atual
            total_steps: Total de passos
            description: Descrição do passo
        """
        progress = f"[{step_num}/{total_steps}]"
        self.info(f"{progress} {description}")

    def progress(self, current: int, total: int, description: str = ""):
        """
        Log de progresso

        Args:
            current: Valor atual
            total: Valor total
            description: Descrição opcional
        """
        percent = (current * 100) // total if total > 0 else 0
        bar_length = 20
        filled_length = (current * bar_length) // total if total > 0 else 0

        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        message = f"Progress: {bar} {percent:3d}% ({current}/{total})"
        if description:
            message += f" - {description}"

        # Usar \r para sobrescrever linha anterior
        print(f"\r{Fore.CYAN}📊 {message}{Style.RESET_ALL}", end="", flush=True)

        # Log completo no arquivo
        self.debug(f"Progress: {percent}% ({current}/{total}) - {description}")

        # Nova linha quando completo
        if current >= total:
            print()

    def section(self, title: str):
        """
        Log de seção principal

        Args:
            title: Título da seção
        """
        separator = "=" * 60
        self.info("")
        self.info(separator)
        self.info(f"  {title}")
        self.info(separator)

    def subsection(self, title: str):
        """
        Log de subseção

        Args:
            title: Título da subseção
        """
        separator = "-" * 40
        self.info("")
        self.info(separator)
        self.info(f"  {title}")
        self.info(separator)

    def table(self, data: Dict[str, Any], title: str = "Informações"):
        """
        Log de tabela formatada

        Args:
            data: Dados para exibir
            title: Título da tabela
        """
        self.info(f"\n📋 {title}:")

        # Calcular largura máxima das chaves
        max_key_length = max(len(str(key)) for key in data.keys()) if data else 0

        for key, value in data.items():
            key_formatted = f"{key}:".ljust(max_key_length + 1)
            self.info(f"   {key_formatted} {value}")

    def exception(self, message: str, exc_info=True):
        """
        Log de exceção com stack trace

        Args:
            message: Mensagem de erro
            exc_info: Incluir informações da exceção
        """
        self.error(message, exc_info=exc_info)

    def command_output(self, command: str, output: str, return_code: int):
        """
        Log de saída de comando

        Args:
            command: Comando executado
            output: Saída do comando
            return_code: Código de retorno
        """
        self.debug(f"Comando: {command}")
        self.debug(f"Código de retorno: {return_code}")

        if output.strip():
            self.debug("Saída:")
            for line in output.strip().split("\n"):
                self.debug(f"  {line}")

    def download_progress(self, filename: str, downloaded: int, total: int):
        """
        Log específico para progresso de download

        Args:
            filename: Nome do arquivo
            downloaded: Bytes baixados
            total: Total de bytes
        """
        if total > 0:
            percent = (downloaded * 100) // total
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)

            self.progress(
                downloaded,
                total,
                f"Baixando {filename} - {mb_downloaded:.1f}/{mb_total:.1f} MB",
            )

    def installation_summary(self, results: Dict[str, bool]):
        """
        Log de resumo de instalação

        Args:
            results: Resultados das instalações
        """
        self.section("RESUMO DA INSTALAÇÃO")

        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        for component, success in results.items():
            status = "✅ Sucesso" if success else "❌ Falhou"
            self.info(f"  {component}: {status}")

        self.info("")
        if success_count == total_count:
            self.success(
                f"Instalação concluída com sucesso! ({success_count}/{total_count})"
            )
        else:
            self.error(
                f"Instalação parcial: {success_count}/{total_count} componentes instalados"
            )

    def get_log_files(self) -> Dict[str, str]:
        """
        Retorna caminhos dos arquivos de log

        Returns:
            Dict: Caminhos dos arquivos de log
        """
        today = datetime.now().strftime("%Y%m%d")

        return {
            "log_principal": str(self.log_dir / f"installer_{today}.log"),
            "log_erros": str(self.log_dir / f"errors_{today}.log"),
            "diretorio": str(self.log_dir),
        }

    def cleanup_old_logs(self, days_to_keep: int = 7):
        """
        Remove logs antigos

        Args:
            days_to_keep: Dias de logs para manter
        """
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            removed_count = 0
            for log_file in self.log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    removed_count += 1

            if removed_count > 0:
                self.debug(f"Removidos {removed_count} arquivos de log antigos")

        except Exception as e:
            self.warning(f"Erro ao limpar logs antigos: {e}")


# Instância global do logger
_global_logger: Optional[Logger] = None


def get_logger(name: str = "VideoConverter-Installer") -> Logger:
    """
    Obtém instância global do logger

    Args:
        name: Nome do logger

    Returns:
        Logger: Instância do logger
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = Logger(name)

    return _global_logger


# Funções de conveniência
def debug(message: str):
    """Log de debug"""
    get_logger().debug(message)


def info(message: str):
    """Log de informação"""
    get_logger().info(message)


def warning(message: str):
    """Log de aviso"""
    get_logger().warning(message)


def error(message: str):
    """Log de erro"""
    get_logger().error(message)


def success(message: str):
    """Log de sucesso"""
    get_logger().success(message)


if __name__ == "__main__":
    # Teste do sistema de logs
    logger = Logger("Teste")

    logger.section("Teste do Sistema de Logs")

    logger.set_context("Teste Básico")
    logger.debug("Mensagem de debug")
    logger.info("Mensagem de informação")
    logger.warning("Mensagem de aviso")
    logger.error("Mensagem de erro")
    logger.success("Mensagem de sucesso")
    logger.clear_context()

    logger.subsection("Teste de Progresso")
    for i in range(101):
        logger.progress(i, 100, f"Processando item {i}")
        import time

        time.sleep(0.01)

    logger.table(
        {
            "Sistema": "Windows 10",
            "Python": "3.13.0",
            "Arquitetura": "x64",
            "Status": "OK",
        },
        "Informações do Sistema",
    )

    logger.installation_summary(
        {"Python 3.13": True, "CUDA": True, "FFmpeg": False, "VideoConverter": True}
    )

    print(f"\nArquivos de log: {logger.get_log_files()}")
