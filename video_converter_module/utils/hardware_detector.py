"""
Detector de Hardware para Aceleração de Vídeo
Detecta capacidades de hardware disponíveis para aceleração de conversão de vídeo.
"""

import subprocess
import json
import re
import logging
from typing import Dict, List, Optional, Tuple
import sys
import os

# Adicionar o diretório pai ao path para importar módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ffmpeg_installer import FFmpegInstaller

logger = logging.getLogger(__name__)


class HardwareDetector:
    """
    Classe responsável por detectar hardware disponível para aceleração de vídeo.
    """

    def __init__(self):
        """Inicializa o detector de hardware"""
        self.ffmpeg_installer = FFmpegInstaller()
        # Força o uso do FFmpeg local se disponível
        local_ffmpeg = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "ffmpeg.exe"
        )
        if os.path.exists(local_ffmpeg):
            self.ffmpeg_command = local_ffmpeg
        else:
            self.ffmpeg_command = self.ffmpeg_installer.get_ffmpeg_command()

        self.nvidia_info = None
        self.ffmpeg_codecs = None
        self._detect_hardware()

    def _detect_hardware(self) -> None:
        """
        Detecta todo o hardware disponível para aceleração.
        """
        self.nvidia_info = self._detect_nvidia_gpu()
        self.ffmpeg_codecs = self._detect_ffmpeg_codecs()

    def _detect_nvidia_gpu(self) -> Optional[Dict]:
        """
        Detecta GPU NVIDIA usando nvidia-smi.

        Returns:
            Dict com informações da GPU ou None se não encontrada
        """
        try:
            # Executa nvidia-smi para obter informações da GPU
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,memory.free,driver_version",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                gpu_info = []

                for line in lines:
                    parts = [part.strip() for part in line.split(",")]
                    if len(parts) >= 4:
                        gpu_info.append(
                            {
                                "name": parts[0],
                                "memory_total_mb": int(parts[1]),
                                "memory_free_mb": int(parts[2]),
                                "driver_version": parts[3],
                                "cuda_version": None,  # Será detectado de outra forma se necessário
                            }
                        )

                if gpu_info:
                    logger.info(f"GPU NVIDIA detectada: {gpu_info[0]['name']}")
                    return {
                        "available": True,
                        "gpus": gpu_info,
                        "primary_gpu": gpu_info[0],
                    }

            logger.info("Nenhuma GPU NVIDIA detectada")
            return {"available": False, "gpus": [], "primary_gpu": None}

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ) as e:
            logger.warning(f"Erro ao detectar GPU NVIDIA: {e}")
            return {"available": False, "gpus": [], "primary_gpu": None}

    def _detect_ffmpeg_codecs(self) -> Dict[str, List[str]]:
        """
        Detecta codecs disponíveis no FFmpeg.

        Returns:
            Dict com listas de encoders e decoders disponíveis
        """
        codecs = {
            "encoders": [],
            "decoders": [],
            "hardware_encoders": [],
            "hardware_decoders": [],
        }

        if not self.ffmpeg_command:
            logger.warning(
                "FFmpeg não encontrado - tentando instalar automaticamente..."
            )
            try:
                self.ffmpeg_installer.install_ffmpeg()
                self.ffmpeg_command = self.ffmpeg_installer.get_ffmpeg_command()
            except Exception as e:
                logger.error(f"Falha na instalação automática do FFmpeg: {e}")
                return codecs

        if not self.ffmpeg_command:
            logger.error("FFmpeg não disponível após tentativa de instalação")
            return codecs

        try:
            # Detecta encoders
            result = subprocess.run(
                [self.ffmpeg_command, "-encoders"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10,
            )
            if result.returncode == 0:
                encoders = self._parse_ffmpeg_codecs(result.stdout)
                codecs["encoders"] = encoders

                # Filtra encoders de hardware
                hardware_patterns = ["nvenc", "qsv", "vaapi", "videotoolbox", "amf"]
                codecs["hardware_encoders"] = [
                    enc
                    for enc in encoders
                    if any(pattern in enc.lower() for pattern in hardware_patterns)
                ]

            # Detecta decoders
            result = subprocess.run(
                [self.ffmpeg_command, "-decoders"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10,
            )
            if result.returncode == 0:
                decoders = self._parse_ffmpeg_codecs(result.stdout)
                codecs["decoders"] = decoders

                # Filtra decoders de hardware
                hardware_patterns = ["cuvid", "qsv", "vaapi", "videotoolbox", "amf"]
                codecs["hardware_decoders"] = [
                    dec
                    for dec in decoders
                    if any(pattern in dec.lower() for pattern in hardware_patterns)
                ]

            logger.info(
                f"FFmpeg: {len(codecs['hardware_encoders'])} encoders de hardware detectados"
            )
            return codecs

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ) as e:
            logger.warning(f"Erro ao detectar codecs FFmpeg: {e}")
            return codecs

    def _parse_ffmpeg_codecs(self, output: str) -> List[str]:
        """
        Extrai nomes de codecs da saída do FFmpeg.

        Args:
            output: Saída do comando ffmpeg -encoders ou -decoders

        Returns:
            Lista de nomes de codecs
        """
        codecs = []
        lines = output.split("\n")

        for line in lines:
            # Procura por linhas que começam com flags de codec (ex: "V..... h264_nvenc")
            match = re.match(r"^\s*[VAD\.]{6}\s+(\w+)", line)
            if match:
                codecs.append(match.group(1))

        return codecs

    def is_cuda_available(self) -> bool:
        """
        Verifica se CUDA está disponível para uso.

        Returns:
            True se CUDA estiver disponível
        """
        if not self.nvidia_info or not self.nvidia_info.get("available", False):
            return False

        if not self.ffmpeg_codecs:
            return False

        # Verifica se há encoders NVENC disponíveis
        hardware_encoders = self.ffmpeg_codecs.get("hardware_encoders", [])
        nvenc_encoders = [enc for enc in hardware_encoders if "nvenc" in enc.lower()]

        return len(nvenc_encoders) > 0

    def get_cuda_encoders(self) -> List[str]:
        """
        Retorna lista de encoders CUDA disponíveis.

        Returns:
            Lista de encoders NVENC
        """
        if not self.ffmpeg_codecs:
            return []

        hardware_encoders = self.ffmpeg_codecs.get("hardware_encoders", [])
        return [enc for enc in hardware_encoders if "nvenc" in enc.lower()]

    def get_cuda_decoders(self) -> List[str]:
        """
        Retorna lista de decoders CUDA disponíveis.

        Returns:
            Lista de decoders CUVID
        """
        if not self.ffmpeg_codecs:
            return []

        hardware_decoders = self.ffmpeg_codecs.get("hardware_decoders", [])
        return [dec for dec in hardware_decoders if "cuvid" in dec.lower()]

    def get_gpu_memory_info(self) -> Optional[Tuple[int, int]]:
        """
        Retorna informações de memória da GPU principal.

        Returns:
            Tupla (memória_total_mb, memória_livre_mb) ou None
        """
        if not self.nvidia_info or not self.nvidia_info["available"]:
            return None

        gpu = self.nvidia_info["primary_gpu"]
        return (gpu["memory_total_mb"], gpu["memory_free_mb"])

    def get_hardware_summary(self) -> Dict:
        """
        Retorna resumo completo do hardware detectado.

        Returns:
            Dict com informações resumidas do hardware
        """
        summary = {
            "cuda_available": self.is_cuda_available(),
            "nvidia_gpu": None,
            "cuda_encoders": self.get_cuda_encoders(),
            "cuda_decoders": self.get_cuda_decoders(),
            "memory_info": self.get_gpu_memory_info(),
        }

        if self.nvidia_info and self.nvidia_info["available"]:
            gpu = self.nvidia_info["primary_gpu"]
            summary["nvidia_gpu"] = {
                "name": gpu["name"],
                "driver_version": gpu["driver_version"],
                "cuda_version": gpu["cuda_version"],
                "memory_gb": round(gpu["memory_total_mb"] / 1024, 1),
            }

        return summary

    def test_cuda_encoding(self) -> bool:
        """
        Testa se a codificação CUDA está funcionando.

        Returns:
            True se o teste passou
        """
        if not self.is_cuda_available() or not self.ffmpeg_command:
            return False

        try:
            # Teste simples: criar um vídeo de teste de 1 segundo
            test_cmd = [
                self.ffmpeg_command,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc=duration=1:size=320x240:rate=1",
                "-c:v",
                "h264_nvenc",
                "-preset",
                "fast",
                "-f",
                "null",
                "-",
            ]

            result = subprocess.run(
                test_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30
            )
            success = result.returncode == 0

            if success:
                logger.info("Teste de codificação CUDA passou com sucesso")
            else:
                logger.warning(f"Teste de codificação CUDA falhou: {result.stderr}")

            return success

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.warning(f"Erro no teste de codificação CUDA: {e}")
            return False


# Instância global para reutilização
_hardware_detector = None


def get_hardware_detector() -> HardwareDetector:
    """
    Retorna instância singleton do detector de hardware.

    Returns:
        Instância do HardwareDetector
    """
    global _hardware_detector
    if _hardware_detector is None:
        _hardware_detector = HardwareDetector()
    return _hardware_detector


def is_cuda_available() -> bool:
    """
    Função de conveniência para verificar disponibilidade do CUDA.

    Returns:
        True se CUDA estiver disponível
    """
    return get_hardware_detector().is_cuda_available()


def get_hardware_summary() -> Dict:
    """
    Função de conveniência para obter resumo do hardware.

    Returns:
        Dict com informações do hardware
    """
    return get_hardware_detector().get_hardware_summary()
