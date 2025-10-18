"""
🎮 Detector de GPU NVIDIA - VideoConverter Installer
===================================================

Detector avançado de GPU NVIDIA com:
- Detecção automática de GPUs NVIDIA
- Verificação de compatibilidade CUDA
- Análise de capacidades (compute capability)
- Detecção de drivers instalados
- Recomendações de versão CUDA
- Suporte a múltiplas GPUs
"""

import os
import sys
import subprocess
import re
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import platform

try:
    from utils.logger import Logger
except ImportError:
    # Fallback para quando executado diretamente
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.logger import Logger


@dataclass
class GPUInfo:
    """Informações de GPU NVIDIA"""
    name: str
    uuid: str
    compute_capability: Tuple[int, int]
    memory_total: int  # MB
    memory_free: int   # MB
    driver_version: str
    cuda_version: str
    pci_bus_id: str
    gpu_index: int
    is_cuda_capable: bool = True
    recommended_cuda_versions: List[str] = None


@dataclass
class CUDACompatibility:
    """Informações de compatibilidade CUDA"""
    is_supported: bool
    min_driver_version: str
    recommended_cuda_version: str
    compute_capability_required: Tuple[int, int]
    reasons: List[str]


class GPUDetector:
    """
    Detector avançado de GPU NVIDIA
    
    Funcionalidades:
    - Detecção via nvidia-ml-py3 (se disponível)
    - Detecção via nvidia-smi
    - Detecção via WMI (Windows)
    - Verificação de compatibilidade CUDA
    - Análise de capacidades
    """
    
    # Mapeamento de compute capability para versões CUDA suportadas
    CUDA_COMPATIBILITY_MAP = {
        # Compute Capability -> (Min CUDA, Max CUDA, Recommended)
        (3, 0): ("7.5", "10.2", "10.2"),    # Kepler
        (3, 5): ("7.5", "11.8", "11.8"),    # Kepler
        (3, 7): ("7.5", "11.8", "11.8"),    # Kepler
        (5, 0): ("7.5", "12.6", "12.6"),    # Maxwell
        (5, 2): ("7.5", "12.6", "12.6"),    # Maxwell
        (5, 3): ("7.5", "12.6", "12.6"),    # Maxwell
        (6, 0): ("8.0", "12.6", "12.6"),    # Pascal
        (6, 1): ("8.0", "12.6", "12.6"),    # Pascal
        (6, 2): ("8.0", "12.6", "12.6"),    # Pascal
        (7, 0): ("9.0", "12.6", "12.6"),    # Volta
        (7, 2): ("9.0", "12.6", "12.6"),    # Volta
        (7, 5): ("10.0", "12.6", "12.6"),   # Turing
        (8, 0): ("11.0", "12.6", "12.6"),   # Ampere
        (8, 6): ("11.1", "12.6", "12.6"),   # Ampere
        (8, 7): ("11.4", "12.6", "12.6"),   # Ampere
        (8, 9): ("11.8", "12.6", "12.6"),   # Ada Lovelace
        (9, 0): ("12.0", "12.6", "12.6"),   # Hopper
    }
    
    # Versões mínimas de driver para CUDA
    DRIVER_CUDA_MAP = {
        "12.6": "560.94",
        "12.5": "555.42",
        "12.4": "550.54",
        "12.3": "545.23",
        "12.2": "535.54",
        "12.1": "530.30",
        "12.0": "525.60",
        "11.8": "520.61",
        "11.7": "515.43",
        "11.6": "510.39",
        "11.5": "495.29",
        "11.4": "470.57",
        "11.3": "465.19",
        "11.2": "460.27",
        "11.1": "455.23",
        "11.0": "450.36",
    }
    
    def __init__(self):
        """Inicializa detector de GPU"""
        self.logger = Logger("GPUDetector")
        self.os_type = platform.system().lower()
        
        # Tentar importar nvidia-ml-py3
        self.nvml_available = False
        try:
            import pynvml
            self.pynvml = pynvml
            self.nvml_available = True
            self.logger.debug("nvidia-ml-py3 disponível")
        except ImportError:
            self.logger.debug("nvidia-ml-py3 não disponível, usando métodos alternativos")
    
    def _run_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """
        Executa comando e retorna resultado
        
        Args:
            command: Lista com comando e argumentos
            
        Returns:
            Tuple[bool, str, str]: (sucesso, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if self.os_type == "windows" else 0
            )
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Timeout"
        except FileNotFoundError:
            return False, "", "Comando não encontrado"
        except Exception as e:
            return False, "", str(e)
    
    def _detect_via_nvml(self) -> List[GPUInfo]:
        """
        Detecta GPUs via NVML (nvidia-ml-py3)
        
        Returns:
            List[GPUInfo]: Lista de GPUs detectadas
        """
        if not self.nvml_available:
            return []
        
        gpus = []
        
        try:
            self.pynvml.nvmlInit()
            device_count = self.pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = self.pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # Informações básicas
                name = self.pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                uuid = self.pynvml.nvmlDeviceGetUUID(handle).decode('utf-8')
                
                # Memória
                memory_info = self.pynvml.nvmlDeviceGetMemoryInfo(handle)
                memory_total = memory_info.total // (1024 * 1024)  # MB
                memory_free = memory_info.free // (1024 * 1024)    # MB
                
                # Driver e CUDA
                driver_version = self.pynvml.nvmlSystemGetDriverVersion().decode('utf-8')
                cuda_version = self.pynvml.nvmlSystemGetCudaDriverVersion_v2()
                cuda_version_str = f"{cuda_version // 1000}.{(cuda_version % 1000) // 10}"
                
                # Compute capability
                major = self.pynvml.nvmlDeviceGetCudaComputeCapability(handle)[0]
                minor = self.pynvml.nvmlDeviceGetCudaComputeCapability(handle)[1]
                compute_capability = (major, minor)
                
                # PCI Bus ID
                pci_info = self.pynvml.nvmlDeviceGetPciInfo(handle)
                pci_bus_id = pci_info.busId.decode('utf-8')
                
                gpu_info = GPUInfo(
                    name=name,
                    uuid=uuid,
                    compute_capability=compute_capability,
                    memory_total=memory_total,
                    memory_free=memory_free,
                    driver_version=driver_version,
                    cuda_version=cuda_version_str,
                    pci_bus_id=pci_bus_id,
                    gpu_index=i
                )
                
                gpus.append(gpu_info)
                self.logger.debug(f"GPU detectada via NVML: {name}")
            
            self.pynvml.nvmlShutdown()
            
        except Exception as e:
            self.logger.warning(f"Erro na detecção via NVML: {e}")
        
        return gpus
    
    def _detect_via_nvidia_smi(self) -> List[GPUInfo]:
        """
        Detecta GPUs via nvidia-smi
        
        Returns:
            List[GPUInfo]: Lista de GPUs detectadas
        """
        # Comando nvidia-smi com output em XML
        command = ["nvidia-smi", "-q", "-x"]
        
        success, stdout, stderr = self._run_command(command)
        
        if not success:
            self.logger.debug(f"nvidia-smi não disponível: {stderr}")
            return []
        
        gpus = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(stdout)
            
            for i, gpu_elem in enumerate(root.findall('.//gpu')):
                # Nome
                name_elem = gpu_elem.find('product_name')
                name = name_elem.text if name_elem is not None else "Unknown"
                
                # UUID
                uuid_elem = gpu_elem.find('uuid')
                uuid = uuid_elem.text if uuid_elem is not None else f"GPU-{i}"
                
                # Memória
                memory_elem = gpu_elem.find('fb_memory_usage')
                memory_total = 0
                memory_free = 0
                
                if memory_elem is not None:
                    total_elem = memory_elem.find('total')
                    free_elem = memory_elem.find('free')
                    
                    if total_elem is not None:
                        memory_total = int(re.findall(r'\d+', total_elem.text)[0])
                    if free_elem is not None:
                        memory_free = int(re.findall(r'\d+', free_elem.text)[0])
                
                # Driver version
                driver_elem = root.find('.//driver_version')
                driver_version = driver_elem.text if driver_elem is not None else "Unknown"
                
                # CUDA version
                cuda_elem = root.find('.//cuda_version')
                cuda_version = cuda_elem.text if cuda_elem is not None else "Unknown"
                
                # PCI Bus ID
                pci_elem = gpu_elem.find('pci')
                pci_bus_id = "Unknown"
                if pci_elem is not None:
                    bus_id_elem = pci_elem.find('pci_bus_id')
                    if bus_id_elem is not None:
                        pci_bus_id = bus_id_elem.text
                
                # Compute capability (tentar obter via query específica)
                compute_capability = self._get_compute_capability_nvidia_smi(i)
                
                gpu_info = GPUInfo(
                    name=name,
                    uuid=uuid,
                    compute_capability=compute_capability,
                    memory_total=memory_total,
                    memory_free=memory_free,
                    driver_version=driver_version,
                    cuda_version=cuda_version,
                    pci_bus_id=pci_bus_id,
                    gpu_index=i
                )
                
                gpus.append(gpu_info)
                self.logger.debug(f"GPU detectada via nvidia-smi: {name}")
        
        except Exception as e:
            self.logger.warning(f"Erro ao parsear saída do nvidia-smi: {e}")
        
        return gpus
    
    def _get_compute_capability_nvidia_smi(self, gpu_index: int) -> Tuple[int, int]:
        """
        Obtém compute capability via nvidia-smi
        
        Args:
            gpu_index: Índice da GPU
            
        Returns:
            Tuple[int, int]: Compute capability (major, minor)
        """
        command = [
            "nvidia-smi",
            f"--id={gpu_index}",
            "--query-gpu=compute_cap",
            "--format=csv,noheader,nounits"
        ]
        
        success, stdout, stderr = self._run_command(command)
        
        if success and stdout.strip():
            try:
                capability_str = stdout.strip()
                major, minor = map(int, capability_str.split('.'))
                return (major, minor)
            except Exception:
                pass
        
        # Fallback: tentar deduzir pela arquitetura
        return self._estimate_compute_capability_by_name(gpu_index)
    
    def _estimate_compute_capability_by_name(self, gpu_index: int) -> Tuple[int, int]:
        """
        Estima compute capability pelo nome da GPU
        
        Args:
            gpu_index: Índice da GPU
            
        Returns:
            Tuple[int, int]: Compute capability estimado
        """
        # Mapeamento básico por arquitetura
        architecture_map = {
            # Kepler
            "GTX 6": (3, 0),
            "GTX 7": (3, 5),
            "Tesla K": (3, 5),
            
            # Maxwell
            "GTX 9": (5, 2),
            "GTX 10": (6, 1),  # Pascal na verdade
            "Tesla M": (5, 0),
            
            # Pascal
            "GTX 10": (6, 1),
            "GTX 16": (7, 5),  # Turing na verdade
            "Tesla P": (6, 0),
            "Titan X": (6, 1),
            
            # Turing
            "RTX 20": (7, 5),
            "GTX 16": (7, 5),
            "Tesla T4": (7, 5),
            
            # Ampere
            "RTX 30": (8, 6),
            "RTX 40": (8, 9),  # Ada Lovelace na verdade
            "A100": (8, 0),
            "A10": (8, 6),
            
            # Ada Lovelace
            "RTX 40": (8, 9),
            
            # Hopper
            "H100": (9, 0),
        }
        
        # Tentar obter nome da GPU
        command = [
            "nvidia-smi",
            f"--id={gpu_index}",
            "--query-gpu=name",
            "--format=csv,noheader,nounits"
        ]
        
        success, stdout, stderr = self._run_command(command)
        
        if success and stdout.strip():
            gpu_name = stdout.strip().upper()
            
            for pattern, capability in architecture_map.items():
                if pattern.upper() in gpu_name:
                    return capability
        
        # Fallback conservador
        return (3, 5)
    
    def _detect_via_wmi(self) -> List[GPUInfo]:
        """
        Detecta GPUs via WMI (Windows apenas)
        
        Returns:
            List[GPUInfo]: Lista de GPUs detectadas
        """
        if self.os_type != "windows":
            return []
        
        gpus = []
        
        try:
            import wmi
            c = wmi.WMI()
            
            for i, gpu in enumerate(c.Win32_VideoController()):
                if gpu.Name and "NVIDIA" in gpu.Name.upper():
                    # Informações básicas disponíveis via WMI
                    name = gpu.Name
                    memory_total = 0
                    
                    if gpu.AdapterRAM:
                        memory_total = gpu.AdapterRAM // (1024 * 1024)  # MB
                    
                    # Informações limitadas via WMI
                    gpu_info = GPUInfo(
                        name=name,
                        uuid=f"WMI-GPU-{i}",
                        compute_capability=(3, 5),  # Estimativa conservadora
                        memory_total=memory_total,
                        memory_free=memory_total,  # Não disponível via WMI
                        driver_version="Unknown",
                        cuda_version="Unknown",
                        pci_bus_id=gpu.PNPDeviceID or "Unknown",
                        gpu_index=i
                    )
                    
                    gpus.append(gpu_info)
                    self.logger.debug(f"GPU detectada via WMI: {name}")
        
        except ImportError:
            self.logger.debug("WMI não disponível")
        except Exception as e:
            self.logger.warning(f"Erro na detecção via WMI: {e}")
        
        return gpus
    
    def detect_gpus(self) -> List[GPUInfo]:
        """
        Detecta todas as GPUs NVIDIA disponíveis
        
        Returns:
            List[GPUInfo]: Lista de GPUs detectadas
        """
        self.logger.info("Iniciando detecção de GPUs NVIDIA...")
        
        gpus = []
        
        # Tentar métodos em ordem de preferência
        methods = [
            ("NVML", self._detect_via_nvml),
            ("nvidia-smi", self._detect_via_nvidia_smi),
            ("WMI", self._detect_via_wmi)
        ]
        
        for method_name, method_func in methods:
            try:
                detected_gpus = method_func()
                if detected_gpus:
                    self.logger.info(f"Detectadas {len(detected_gpus)} GPU(s) via {method_name}")
                    gpus.extend(detected_gpus)
                    break  # Usar apenas o primeiro método que funcionar
                else:
                    self.logger.debug(f"Nenhuma GPU detectada via {method_name}")
            except Exception as e:
                self.logger.warning(f"Erro no método {method_name}: {e}")
        
        # Adicionar recomendações de versão CUDA
        for gpu in gpus:
            gpu.recommended_cuda_versions = self._get_recommended_cuda_versions(gpu.compute_capability)
        
        if gpus:
            self.logger.success(f"Total de {len(gpus)} GPU(s) NVIDIA detectada(s)")
        else:
            self.logger.warning("Nenhuma GPU NVIDIA detectada")
        
        return gpus
    
    def _get_recommended_cuda_versions(self, compute_capability: Tuple[int, int]) -> List[str]:
        """
        Obtém versões CUDA recomendadas para compute capability
        
        Args:
            compute_capability: Compute capability (major, minor)
            
        Returns:
            List[str]: Versões CUDA recomendadas
        """
        if compute_capability in self.CUDA_COMPATIBILITY_MAP:
            min_cuda, max_cuda, recommended = self.CUDA_COMPATIBILITY_MAP[compute_capability]
            return [recommended, max_cuda, min_cuda]
        
        # Fallback para compute capabilities mais recentes
        if compute_capability[0] >= 9:
            return ["12.6", "12.5", "12.4"]
        elif compute_capability[0] >= 8:
            return ["12.6", "11.8", "11.0"]
        elif compute_capability[0] >= 7:
            return ["11.8", "10.0", "9.0"]
        else:
            return ["11.8", "10.2", "7.5"]
    
    def check_cuda_compatibility(self, gpu: GPUInfo, target_cuda_version: str = None) -> CUDACompatibility:
        """
        Verifica compatibilidade CUDA para GPU
        
        Args:
            gpu: Informações da GPU
            target_cuda_version: Versão CUDA desejada (opcional)
            
        Returns:
            CUDACompatibility: Informações de compatibilidade
        """
        reasons = []
        is_supported = True
        
        # Versão CUDA alvo (usar recomendada se não especificada)
        if target_cuda_version is None:
            target_cuda_version = gpu.recommended_cuda_versions[0] if gpu.recommended_cuda_versions else "12.6"
        
        # Verificar compute capability
        min_compute_capability = (3, 5)  # Mínimo para CUDA moderno
        if gpu.compute_capability < min_compute_capability:
            is_supported = False
            reasons.append(f"Compute capability {gpu.compute_capability} muito baixo (mínimo: {min_compute_capability})")
        
        # Verificar se compute capability suporta versão CUDA alvo
        if gpu.compute_capability in self.CUDA_COMPATIBILITY_MAP:
            min_cuda, max_cuda, _ = self.CUDA_COMPATIBILITY_MAP[gpu.compute_capability]
            
            if target_cuda_version < min_cuda:
                reasons.append(f"Versão CUDA {target_cuda_version} muito baixa (mínimo: {min_cuda})")
            elif target_cuda_version > max_cuda:
                reasons.append(f"Versão CUDA {target_cuda_version} muito alta (máximo: {max_cuda})")
        
        # Verificar driver
        min_driver_version = self.DRIVER_CUDA_MAP.get(target_cuda_version, "450.36")
        
        if gpu.driver_version != "Unknown":
            try:
                current_driver = tuple(map(int, gpu.driver_version.split('.')))
                required_driver = tuple(map(int, min_driver_version.split('.')))
                
                if current_driver < required_driver:
                    is_supported = False
                    reasons.append(f"Driver {gpu.driver_version} muito antigo (mínimo: {min_driver_version})")
            except ValueError:
                reasons.append("Não foi possível verificar versão do driver")
        
        # Verificar memória mínima (2GB para operações básicas)
        min_memory_mb = 2048
        if gpu.memory_total < min_memory_mb:
            reasons.append(f"Memória GPU {gpu.memory_total}MB insuficiente (recomendado: {min_memory_mb}MB+)")
        
        if is_supported and not reasons:
            reasons.append("GPU totalmente compatível com CUDA")
        
        return CUDACompatibility(
            is_supported=is_supported,
            min_driver_version=min_driver_version,
            recommended_cuda_version=target_cuda_version,
            compute_capability_required=min_compute_capability,
            reasons=reasons
        )
    
    def get_best_gpu(self, gpus: List[GPUInfo]) -> Optional[GPUInfo]:
        """
        Seleciona a melhor GPU para CUDA
        
        Args:
            gpus: Lista de GPUs
            
        Returns:
            Optional[GPUInfo]: Melhor GPU ou None
        """
        if not gpus:
            return None
        
        # Critérios de seleção (em ordem de prioridade):
        # 1. Compute capability mais alto
        # 2. Mais memória
        # 3. Mais memória livre
        
        def gpu_score(gpu: GPUInfo) -> Tuple[int, int, int, int]:
            return (
                gpu.compute_capability[0] * 10 + gpu.compute_capability[1],  # Compute capability
                gpu.memory_total,                                            # Memória total
                gpu.memory_free,                                             # Memória livre
                -gpu.gpu_index                                               # Preferir índices menores
            )
        
        best_gpu = max(gpus, key=gpu_score)
        self.logger.info(f"Melhor GPU selecionada: {best_gpu.name} (Compute {best_gpu.compute_capability})")
        
        return best_gpu
    
    def generate_report(self, gpus: List[GPUInfo]) -> Dict[str, Any]:
        """
        Gera relatório detalhado das GPUs
        
        Args:
            gpus: Lista de GPUs
            
        Returns:
            Dict[str, Any]: Relatório completo
        """
        report = {
            "detection_timestamp": time.time(),
            "total_gpus": len(gpus),
            "cuda_capable_gpus": sum(1 for gpu in gpus if gpu.is_cuda_capable),
            "gpus": [],
            "recommendations": []
        }
        
        for gpu in gpus:
            compatibility = self.check_cuda_compatibility(gpu)
            
            gpu_report = {
                "name": gpu.name,
                "uuid": gpu.uuid,
                "compute_capability": f"{gpu.compute_capability[0]}.{gpu.compute_capability[1]}",
                "memory_total_mb": gpu.memory_total,
                "memory_free_mb": gpu.memory_free,
                "driver_version": gpu.driver_version,
                "cuda_version": gpu.cuda_version,
                "pci_bus_id": gpu.pci_bus_id,
                "gpu_index": gpu.gpu_index,
                "is_cuda_compatible": compatibility.is_supported,
                "recommended_cuda_versions": gpu.recommended_cuda_versions,
                "compatibility_reasons": compatibility.reasons
            }
            
            report["gpus"].append(gpu_report)
        
        # Gerar recomendações
        if gpus:
            best_gpu = self.get_best_gpu(gpus)
            if best_gpu:
                report["recommendations"].append(f"Usar GPU: {best_gpu.name}")
                report["recommendations"].append(f"Versão CUDA recomendada: {best_gpu.recommended_cuda_versions[0]}")
                
                compatibility = self.check_cuda_compatibility(best_gpu)
                if not compatibility.is_supported:
                    report["recommendations"].append("⚠️  Atualização de driver necessária")
        else:
            report["recommendations"].append("❌ Nenhuma GPU NVIDIA detectada")
            report["recommendations"].append("💡 Considere usar processamento CPU apenas")
        
        return report


if __name__ == "__main__":
    # Teste do detector de GPU
    import time
    
    print("🧪 Teste do Detector de GPU NVIDIA\n")
    
    detector = GPUDetector()
    
    print("1. Detectando GPUs...")
    gpus = detector.detect_gpus()
    
    if gpus:
        print(f"\n✅ {len(gpus)} GPU(s) detectada(s):")
        
        for i, gpu in enumerate(gpus, 1):
            print(f"\n  GPU {i}: {gpu.name}")
            print(f"    Compute Capability: {gpu.compute_capability[0]}.{gpu.compute_capability[1]}")
            print(f"    Memória: {gpu.memory_total}MB (livre: {gpu.memory_free}MB)")
            print(f"    Driver: {gpu.driver_version}")
            print(f"    CUDA: {gpu.cuda_version}")
            
            # Verificar compatibilidade
            compatibility = detector.check_cuda_compatibility(gpu)
            print(f"    Compatível: {'✅' if compatibility.is_supported else '❌'}")
            
            for reason in compatibility.reasons:
                print(f"      - {reason}")
        
        # Melhor GPU
        best_gpu = detector.get_best_gpu(gpus)
        if best_gpu:
            print(f"\n🏆 Melhor GPU: {best_gpu.name}")
        
        # Relatório completo
        print("\n📊 Gerando relatório...")
        report = detector.generate_report(gpus)
        
        print(f"  Total de GPUs: {report['total_gpus']}")
        print(f"  GPUs compatíveis: {report['cuda_capable_gpus']}")
        
        print("\n📋 Recomendações:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")
    
    else:
        print("❌ Nenhuma GPU NVIDIA detectada")
        print("💡 Verifique se:")
        print("  - Drivers NVIDIA estão instalados")
        print("  - GPU NVIDIA está presente no sistema")
        print("  - nvidia-smi está funcionando")
    
    print("\n✅ Teste concluído!")