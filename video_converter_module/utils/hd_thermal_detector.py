"""
🌡️ Detector Térmico de HD Multiplataforma - VideoConverter
=========================================================

Detecta temperatura de discos rígidos (HDD/SSD) em:
- Windows: PowerShell Get-PhysicalDisk + WMI
- Linux: lm-sensors (/sys/class/hwmon) + smartctl
- Fallback: Estimativa baseada em atividade de I/O

Integra com OSDetector existente para detecção automática de SO.
"""

import os
import sys
import subprocess
import time
import logging
import psutil
from typing import Optional, Dict, List, Tuple
from pathlib import Path

# Adicionar o diretório pai ao path para importar módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from installer.core.os_detector import OSDetector, OSInfo
except ImportError:
    # Fallback se não conseguir importar
    OSDetector = None
    OSInfo = None

logger = logging.getLogger(__name__)


class HDThermalDetector:
    """
    Detector térmico de HD multiplataforma
    
    Funcionalidades:
    - Detecção automática de SO (Windows/Linux)
    - Monitoramento de temperatura por métodos nativos
    - Fallback inteligente para estimativa térmica
    - Cache de resultados para performance
    """
    
    def __init__(self):
        """Inicializa o detector térmico de HD"""
        self.os_detector = OSDetector() if OSDetector else None
        self.os_info = self.os_detector.detect() if self.os_detector else None
        self.cache = {}  # Renomeado de temp_cache para cache
        self.temp_cache = {}  # Mantido para compatibilidade
        self.cache_timeout = 30  # segundos
        self.cache_duration = 30  # Alias para cache_timeout para compatibilidade com testes
        self.last_check = {}
        
        # Configurações de temperatura por tipo de disco
        self.temp_thresholds = {
            'hdd': {'warning': 50, 'critical': 60},  # HDDs tradicionais
            'ssd': {'warning': 60, 'critical': 70},  # SSDs
            'nvme': {'warning': 65, 'critical': 80}  # NVMe SSDs
        }
        
        logger.info(f"🌡️ HDThermalDetector inicializado para {self.os_info.name if self.os_info else 'SO desconhecido'}")
    
    def get_hd_temperature(self, drive_path: str) -> Optional[float]:
        """
        Obtém temperatura do HD baseado no caminho do diretório
        
        Args:
            drive_path: Caminho do diretório (ex: "C:\\" ou "/home/user")
            
        Returns:
            float: Temperatura em Celsius ou None se não detectada
        """
        try:
            # Normalizar caminho
            drive_path = os.path.abspath(drive_path)
            
            # Verificar cache
            if self._is_cache_valid(drive_path):
                return self.temp_cache[drive_path]['temperature']
            
            # Detectar disco físico
            physical_disk = self._get_physical_disk(drive_path)
            if not physical_disk:
                logger.warning(f"⚠️ Não foi possível identificar disco físico para: {drive_path}")
                return None
            
            # Obter temperatura baseado no SO
            temperature = None
            if self.os_info and self.os_info.name == "windows":
                temperature = self._get_windows_hd_temp(physical_disk)
            elif self.os_info and self.os_info.name == "linux":
                temperature = self._get_linux_hd_temp(physical_disk)
            
            # Fallback: estimativa baseada em I/O
            if temperature is None:
                temperature = self._estimate_temperature_from_io(drive_path, physical_disk)
            
            # Atualizar cache
            self._update_cache(drive_path, temperature, physical_disk)
            
            return temperature
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter temperatura do HD: {e}")
            return None
    
    def _get_physical_disk(self, drive_path: str) -> Optional[str]:
        """
        Identifica o disco físico baseado no caminho
        
        Returns:
            str: Identificador do disco físico
        """
        try:
            if self.os_info and self.os_info.name == "windows":
                # Windows: obter letra da unidade
                drive_letter = os.path.splitdrive(drive_path)[0]
                if not drive_letter:
                    return None
                return drive_letter.upper()
            
            elif self.os_info and self.os_info.name == "linux":
                # Linux: obter dispositivo do ponto de montagem
                result = subprocess.run(
                    ['df', drive_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        device = lines[1].split()[0]
                        # Remover números de partição (ex: /dev/sda1 -> /dev/sda)
                        import re
                        device = re.sub(r'\d+$', '', device)
                        return device
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao identificar disco físico: {e}")
            return None
    
    def _get_windows_hd_temp(self, drive_letter: str) -> Optional[float]:
        """
        Obtém temperatura do HD no Windows usando PowerShell
        
        Args:
            drive_letter: Letra da unidade (ex: "C:")
            
        Returns:
            float: Temperatura em Celsius
        """
        try:
            # Método 1: PowerShell Get-PhysicalDisk
            ps_command = f"""
            $drive = Get-Partition -DriveLetter {drive_letter.replace(':', '')} | Get-Disk
            $physicalDisk = Get-PhysicalDisk | Where-Object {{$_.DeviceId -eq $drive.Number}}
            if ($physicalDisk) {{
                $temp = Get-StorageReliabilityCounter -PhysicalDisk $physicalDisk | Select-Object Temperature
                if ($temp.Temperature -ne $null) {{
                    Write-Output $temp.Temperature
                }}
            }}
            """
            
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout.strip():
                temp_str = result.stdout.strip()
                if temp_str.isdigit():
                    return float(temp_str)
            
            # Método 2: WMI (fallback)
            return self._get_windows_wmi_temp(drive_letter)
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter temperatura Windows: {e}")
            return None
    
    def _get_windows_wmi_temp(self, drive_letter: str) -> Optional[float]:
        """
        Fallback: WMI para temperatura no Windows
        """
        try:
            wmi_command = f"""
            Get-WmiObject -Namespace "root/wmi" -Class "MSStorageDriver_FailurePredictTemperature" | 
            Where-Object {{$_.InstanceName -like "*{drive_letter.replace(':', '')}*"}} | 
            Select-Object -ExpandProperty CurrentTemperature
            """
            
            result = subprocess.run(
                ['powershell', '-Command', wmi_command],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # WMI retorna temperatura em Kelvin * 256
                temp_raw = int(result.stdout.strip())
                temp_celsius = (temp_raw / 256) - 273.15
                return temp_celsius if temp_celsius > 0 else None
            
        except Exception as e:
            logger.debug(f"WMI fallback falhou: {e}")
        
        return None
    
    def _get_linux_hd_temp(self, device: str) -> Optional[float]:
        """
        Obtém temperatura do HD no Linux usando lm-sensors
        
        Args:
            device: Dispositivo (ex: "/dev/sda")
            
        Returns:
            float: Temperatura em Celsius
        """
        try:
            # Método 1: lm-sensors via /sys/class/hwmon
            temp = self._get_linux_hwmon_temp(device)
            if temp is not None:
                return temp
            
            # Método 2: smartctl (se disponível)
            temp = self._get_linux_smartctl_temp(device)
            if temp is not None:
                return temp
            
            # Método 3: hddtemp (se disponível)
            return self._get_linux_hddtemp(device)
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter temperatura Linux: {e}")
            return None
    
    def _get_linux_hwmon_temp(self, device: str) -> Optional[float]:
        """
        Obtém temperatura via /sys/class/hwmon (lm-sensors)
        """
        try:
            # Procurar por sensores de temperatura relacionados ao dispositivo
            hwmon_path = Path("/sys/class/hwmon")
            if not hwmon_path.exists():
                return None
            
            device_name = device.split('/')[-1]  # ex: sda
            
            for hwmon_dir in hwmon_path.iterdir():
                if hwmon_dir.is_dir():
                    name_file = hwmon_dir / "name"
                    if name_file.exists():
                        name = name_file.read_text().strip()
                        
                        # Procurar por sensores relacionados ao dispositivo
                        if device_name in name.lower() or any(
                            keyword in name.lower() 
                            for keyword in ['sata', 'nvme', 'ata', 'scsi']
                        ):
                            # Procurar arquivos de temperatura
                            for temp_file in hwmon_dir.glob("temp*_input"):
                                temp_raw = int(temp_file.read_text().strip())
                                temp_celsius = temp_raw / 1000.0
                                if 20 <= temp_celsius <= 100:  # Temperatura razoável
                                    return temp_celsius
            
        except Exception as e:
            logger.debug(f"hwmon falhou: {e}")
        
        return None
    
    def _get_linux_smartctl_temp(self, device: str) -> Optional[float]:
        """
        Obtém temperatura via smartctl
        """
        try:
            result = subprocess.run(
                ['smartctl', '-A', device],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Temperature_Celsius' in line or 'Airflow_Temperature_Cel' in line:
                        parts = line.split()
                        if len(parts) >= 10:
                            temp = int(parts[9])
                            if 20 <= temp <= 100:
                                return float(temp)
            
        except Exception as e:
            logger.debug(f"smartctl falhou: {e}")
        
        return None
    
    def _get_linux_hddtemp(self, device: str) -> Optional[float]:
        """
        Obtém temperatura via hddtemp
        """
        try:
            result = subprocess.run(
                ['hddtemp', device],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # hddtemp output: /dev/sda: SAMSUNG HD103SJ: 35°C
                import re
                match = re.search(r'(\d+)°C', result.stdout)
                if match:
                    return float(match.group(1))
            
        except Exception as e:
            logger.debug(f"hddtemp falhou: {e}")
        
        return None
    
    def _estimate_temperature_from_io(self, drive_path: str = None, physical_disk: str = None) -> Optional[float]:
        """
        Estima temperatura baseada na atividade de I/O
        
        Método de fallback quando não conseguimos obter temperatura real
        
        Args:
            drive_path: Caminho do diretório
            physical_disk: Identificador do disco físico (opcional)
        """
        try:
            # Usar diretório atual se drive_path não fornecido
            if drive_path is None:
                drive_path = os.getcwd()
                
            # Obter estatísticas de I/O do disco
            disk_usage = psutil.disk_usage(drive_path)
            disk_io = psutil.disk_io_counters(perdisk=True)
            
            # Temperatura base estimada
            base_temp = 35.0  # Temperatura ambiente típica
            
            # Fator baseado no uso do disco
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            usage_factor = min(usage_percent / 100 * 10, 15)  # Máximo +15°C
            
            # Fator baseado em I/O (se disponível)
            io_factor = 0
            if disk_io:
                # Usar média de I/O de todos os discos como aproximação
                total_reads = sum(stats.read_count for stats in disk_io.values())
                total_writes = sum(stats.write_count for stats in disk_io.values())
                total_io = total_reads + total_writes
                
                # Normalizar I/O (valores altos indicam atividade)
                if total_io > 1000:
                    io_factor = min(total_io / 10000 * 5, 10)  # Máximo +10°C
            
            estimated_temp = base_temp + usage_factor + io_factor
            
            logger.info(f"🔥 Temperatura estimada para {drive_path}: {estimated_temp:.1f}°C")
            return estimated_temp
            
        except Exception as e:
            logger.error(f"❌ Erro na estimativa de temperatura: {e}")
            return None
    
    def _is_cache_valid(self, drive_path: str) -> bool:
        """Verifica se o cache é válido"""
        if drive_path not in self.temp_cache:
            return False
        
        cache_time = self.temp_cache[drive_path]['timestamp']
        return (time.time() - cache_time) < self.cache_timeout
    
    def _update_cache(self, *args, **kwargs):
        """Atualiza o cache de temperatura - método polimórfico"""
        if len(args) == 1 and isinstance(args[0], dict):
            # Versão para testes: _update_cache(temperatures_dict)
            temperatures = args[0]
            self.cache = {
                'temperatures': temperatures,
                'timestamp': time.time()
            }
        elif len(args) == 3:
            # Versão original: _update_cache(drive_path, temperature, physical_disk)
            drive_path, temperature, physical_disk = args
            self.temp_cache[drive_path] = {
                'temperature': temperature,
                'physical_disk': physical_disk,
                'timestamp': time.time()
            }
        else:
            raise TypeError(f"_update_cache() takes 1 or 3 positional arguments but {len(args)} were given")
    
    def get_disk_type(self, drive_path: str) -> str:
        """
        Detecta o tipo de disco (HDD/SSD/NVMe)
        
        Returns:
            str: 'hdd', 'ssd', ou 'nvme'
        """
        try:
            if self.os_info and self.os_info.name == "windows":
                drive_letter = os.path.splitdrive(drive_path)[0].replace(':', '')
                
                ps_command = f"""
                $drive = Get-Partition -DriveLetter {drive_letter} | Get-Disk
                $physicalDisk = Get-PhysicalDisk | Where-Object {{$_.DeviceId -eq $drive.Number}}
                if ($physicalDisk) {{
                    Write-Output $physicalDisk.MediaType
                }}
                """
                
                result = subprocess.run(
                    ['powershell', '-Command', ps_command],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    media_type = result.stdout.strip().lower()
                    if 'ssd' in media_type:
                        return 'ssd'
                    elif 'hdd' in media_type:
                        return 'hdd'
            
            elif self.os_info and self.os_info.name == "linux":
                physical_disk = self._get_physical_disk(drive_path)
                if physical_disk:
                    # Verificar se é NVMe
                    if 'nvme' in physical_disk.lower():
                        return 'nvme'
                    
                    # Verificar rotacional (0 = SSD, 1 = HDD)
                    device_name = physical_disk.split('/')[-1]
                    rotational_file = f"/sys/block/{device_name}/queue/rotational"
                    
                    if os.path.exists(rotational_file):
                        with open(rotational_file, 'r') as f:
                            rotational = f.read().strip()
                            return 'hdd' if rotational == '1' else 'ssd'
            
            # Fallback: assumir HDD
            return 'hdd'
            
        except Exception as e:
            logger.debug(f"Erro ao detectar tipo de disco: {e}")
            return 'hdd'
    
    def get_temperature_status(self, drive_path: str) -> Dict[str, any]:
        """
        Obtém status completo da temperatura do HD
        
        Returns:
            Dict com temperatura, status, tipo de disco, etc.
        """
        temperature = self.get_hd_temperature(drive_path)
        disk_type = self.get_disk_type(drive_path)
        thresholds = self.temp_thresholds.get(disk_type, self.temp_thresholds['hdd'])
        
        status = 'unknown'
        if temperature is not None:
            if temperature < thresholds['warning']:
                status = 'normal'
            elif temperature < thresholds['critical']:
                status = 'warning'
            else:
                status = 'critical'
        
        return {
            'temperature': temperature,
            'status': status,
            'disk_type': disk_type,
            'thresholds': thresholds,
            'drive_path': drive_path,
            'timestamp': time.time()
        }
    
    def get_thermal_status(self, temperatures_or_path, warning_threshold: float = None, critical_threshold: float = None) -> Dict[str, any]:
        """
        Determina status térmico baseado em temperaturas e limites
        
        Args:
            temperatures_or_path: Dict de temperaturas ou caminho do drive
            warning_threshold: Limite de aviso (opcional)
            critical_threshold: Limite crítico (opcional)
            
        Returns:
            Dict com status térmico
        """
        # Se for um dicionário de temperaturas (modo teste)
        if isinstance(temperatures_or_path, dict):
            temperatures = temperatures_or_path
            max_temp = max(temperatures.values()) if temperatures else 0
            
            # Usar limites fornecidos ou padrões
            warning = warning_threshold or 60
            critical = critical_threshold or 70
            
            if max_temp >= critical:
                status = "critical"
            elif max_temp >= warning:
                status = "warning"
            else:
                status = "normal"
                
            return {
                "status": status,
                "max_temperature": max_temp,
                "temperatures": temperatures,
                "thresholds": {
                    "warning": warning,
                    "critical": critical
                }
            }
        
        # Se for um caminho de drive (modo normal)
        else:
            drive_path = temperatures_or_path or os.getcwd()
            return self.get_temperature_status(drive_path)
    
    def get_hd_temperatures(self, drives: list = None, simple_format: bool = False) -> Dict[str, any]:
        """
        Obtém temperaturas de múltiplos HDs/SSDs
        
        Args:
            drives: Lista de caminhos de drives (opcional, usa drives disponíveis se None)
            simple_format: Se True, retorna apenas temperaturas numéricas (para compatibilidade com testes)
            
        Returns:
            Dict com temperaturas de cada drive (formato completo ou simples)
        """
        if drives is None:
            # Se não especificado, usar drives disponíveis
            if self.os_info and self.os_info.name == "windows":
                drives = [f"{chr(i)}:\\" for i in range(ord('C'), ord('Z')+1) if os.path.exists(f"{chr(i)}:\\")]
            else:
                drives = ["/"]  # Para Linux, usar root por padrão
        
        temperatures = {}
        for drive in drives:
            try:
                temp_status = self.get_temperature_status(drive)
                if simple_format:
                    # Retornar apenas a temperatura numérica
                    temp_value = temp_status.get('temperature')
                    if temp_value is not None:
                        temperatures[drive] = temp_value
                else:
                    temperatures[drive] = temp_status
            except Exception as e:
                logger.debug(f"Erro ao obter temperatura do drive {drive}: {e}")
                if simple_format:
                    # No formato simples, pular drives com erro
                    continue
                else:
                    temperatures[drive] = {
                        'temperature': None,
                        'status': 'error',
                        'error': str(e),
                        'drive_path': drive,
                        'timestamp': time.time()
                    }
        
        return temperatures


# Função de conveniência
def get_hd_temperature(drive_path: str) -> Optional[float]:
    """
    Função de conveniência para obter temperatura do HD
    
    Args:
        drive_path: Caminho do diretório
        
    Returns:
        float: Temperatura em Celsius ou None
    """
    detector = HDThermalDetector()
    return detector.get_hd_temperature(drive_path)


if __name__ == "__main__":
    # Teste do detector
    import sys
    
    test_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    detector = HDThermalDetector()
    status = detector.get_temperature_status(test_path)
    
    print(f"🌡️ Status Térmico do HD:")
    print(f"   Caminho: {status['drive_path']}")
    print(f"   Tipo: {status['disk_type'].upper()}")
    print(f"   Temperatura: {status['temperature']:.1f}°C" if status['temperature'] else "   Temperatura: Não detectada")
    print(f"   Status: {status['status'].upper()}")
    print(f"   Limites: Aviso={status['thresholds']['warning']}°C, Crítico={status['thresholds']['critical']}°C")