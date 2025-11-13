"""
Testes unitários para o sistema de monitoramento térmico de HD/SSD
Valida a funcionalidade em Windows e Linux
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json

# Adicionar o diretório raiz ao path para importações
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from video_converter_module.utils.hd_thermal_detector import HDThermalDetector
from video_converter_module.utils.config import HARDWARE_MONITORING
from video_converter_module.core.queue_manager import ConversionQueueManager


class TestHDThermalDetector(unittest.TestCase):
    """
    Testes para a classe HDThermalDetector
    """
    
    def setUp(self):
        """
        Configuração inicial para cada teste
        """
        self.detector = HDThermalDetector()
    
    def test_initialization(self):
        """
        Testa a inicialização correta do detector térmico
        """
        self.assertIsNotNone(self.detector.os_detector)
        self.assertIsInstance(self.detector.cache, dict)
        self.assertIsInstance(self.detector.cache_duration, (int, float))
        self.assertTrue(self.detector.cache_duration > 0)
    
    @patch('video_converter_module.utils.hd_thermal_detector.subprocess.run')
    def test_windows_thermal_detection_powershell(self, mock_subprocess):
        """
        Testa detecção térmica no Windows usando PowerShell
        """
        # Mock do sistema operacional
        with patch.object(self.detector.os_detector, 'get_os_type', return_value='windows'):
            # Mock da resposta do PowerShell
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '''
            [
                {
                    "DeviceID": "0",
                    "Model": "Samsung SSD 980",
                    "Temperature": 45
                },
                {
                    "DeviceID": "1", 
                    "Model": "WD Blue HDD",
                    "Temperature": 38
                }
            ]
            '''
            mock_subprocess.return_value = mock_result
            
            # Executar detecção
            temperatures = self.detector.get_hd_temperatures(simple_format=True)
            
            # Verificar resultados
            self.assertIsInstance(temperatures, dict)
            self.assertGreater(len(temperatures), 0)
            
            # Verificar se as temperaturas são números válidos
            for drive, temp in temperatures.items():
                self.assertIsInstance(temp, (int, float))
                self.assertGreater(temp, 0)
                self.assertLess(temp, 100)  # Temperatura razoável
    
    @patch('video_converter_module.utils.hd_thermal_detector.subprocess.run')
    def test_windows_thermal_detection_wmi_fallback(self, mock_subprocess):
        """
        Testa fallback para WMI no Windows quando PowerShell falha
        """
        with patch.object(self.detector.os_detector, 'get_os_type', return_value='windows'):
            # Mock PowerShell falhando
            mock_result_ps = Mock()
            mock_result_ps.returncode = 1
            mock_result_ps.stdout = ""
            
            # Mock WMI funcionando
            mock_result_wmi = Mock()
            mock_result_wmi.returncode = 0
            mock_result_wmi.stdout = "Temperature=42"
            
            # Configurar retornos sequenciais
            mock_subprocess.side_effect = [mock_result_ps, mock_result_wmi]
            
            # Executar detecção
            temperatures = self.detector.get_hd_temperatures(simple_format=True)
            
            # Verificar que o fallback funcionou
            self.assertIsInstance(temperatures, dict)
    
    @patch('video_converter_module.utils.hd_thermal_detector.os.path.exists')
    @patch('builtins.open', create=True)
    def test_linux_thermal_detection_hwmon(self, mock_open, mock_exists):
        """
        Testa detecção térmica no Linux usando hwmon
        """
        with patch.object(self.detector.os_detector, 'get_os_type', return_value='linux'):
            # Mock arquivos hwmon existindo
            mock_exists.return_value = True
            
            # Mock conteúdo dos arquivos de temperatura
            mock_file = MagicMock()
            mock_file.read.return_value = "45000"  # 45°C em miligraus
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Mock glob para encontrar sensores
            with patch('glob.glob', return_value=['/sys/class/hwmon/hwmon0/temp1_input']):
                temperatures = self.detector.get_hd_temperatures(simple_format=True)
                
                # Verificar resultados
                self.assertIsInstance(temperatures, dict)
    
    @patch('video_converter_module.utils.hd_thermal_detector.subprocess.run')
    def test_linux_thermal_detection_smartctl_fallback(self, mock_subprocess):
        """
        Testa fallback para smartctl no Linux
        """
        with patch.object(self.detector.os_detector, 'get_os_type', return_value='linux'):
            # Mock smartctl funcionando
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Temperature_Celsius     0x0022   045   045   000    Old_age   Always       -       45"
            mock_subprocess.return_value = mock_result
            
            # Mock hwmon não disponível
            with patch('glob.glob', return_value=[]):
                temperatures = self.detector.get_hd_temperatures(simple_format=True)
                
                # Verificar que o fallback funcionou
                self.assertIsInstance(temperatures, dict)
    
    def test_thermal_status_determination(self):
        """
        Testa determinação do status térmico baseado em limites
        """
        # Configurar limites de teste
        warning_threshold = 50
        critical_threshold = 60
        
        # Teste temperatura normal
        status = self.detector.get_thermal_status(
            {"SSD1": 40}, warning_threshold, critical_threshold
        )
        self.assertEqual(status["status"], "normal")
        
        # Teste temperatura de aviso
        status = self.detector.get_thermal_status(
            {"SSD1": 55}, warning_threshold, critical_threshold
        )
        self.assertEqual(status["status"], "warning")
        
        # Teste temperatura crítica
        status = self.detector.get_thermal_status(
            {"SSD1": 65}, warning_threshold, critical_threshold
        )
        self.assertEqual(status["status"], "critical")
    
    def test_cache_functionality(self):
        """
        Testa funcionalidade de cache de temperaturas
        """
        # Mock de temperaturas
        mock_temps = {"SSD1": 45, "HDD1": 38}
        
        # Adicionar ao cache
        self.detector._update_cache(mock_temps)
        
        # Verificar se está no cache
        self.assertIn("temperatures", self.detector.cache)
        self.assertEqual(self.detector.cache["temperatures"], mock_temps)
        
        # Verificar timestamp
        self.assertIn("timestamp", self.detector.cache)
        self.assertIsInstance(self.detector.cache["timestamp"], float)
    
    def test_io_activity_estimation(self):
        """
        Testa estimativa de temperatura baseada em atividade de I/O
        """
        with patch('psutil.disk_io_counters') as mock_io, \
             patch('psutil.disk_usage') as mock_usage:
            
            # Mock de estatísticas de I/O
            mock_io_stats = Mock()
            mock_io_stats.read_count = 100
            mock_io_stats.write_count = 50
            mock_io.return_value = {'C:': mock_io_stats}
            
            # Mock de uso do disco
            mock_usage.return_value = Mock(
                total=1000000000,  # 1GB
                used=500000000,    # 500MB (50% usado)
                free=500000000
            )
            
            # Executar estimativa
            estimated_temp = self.detector._estimate_temperature_from_io()
            
            # Verificar resultado
            self.assertIsInstance(estimated_temp, (int, float))
            self.assertGreater(estimated_temp, 20)  # Temperatura mínima razoável
            self.assertLess(estimated_temp, 80)     # Temperatura máxima razoável


class TestQueueManagerThermalIntegration(unittest.TestCase):
    """
    Testes para integração do monitoramento térmico no QueueManager
    """
    
    def setUp(self):
        """
        Configuração inicial para cada teste
        """
        self.queue_manager = ConversionQueueManager()
    
    def test_hd_thermal_detector_initialization(self):
        """
        Testa inicialização do detector térmico no queue manager
        """
        # Verificar se o detector foi inicializado
        if HARDWARE_MONITORING.get("enable_hd_thermal_monitoring", False):
            self.assertIsNotNone(self.queue_manager.hd_thermal_detector)
        else:
            # Se desabilitado, deve ser None
            self.assertIsNone(getattr(self.queue_manager, 'hd_thermal_detector', None))
    
    @patch.object(ConversionQueueManager, '_check_hd_thermal_status')
    def test_thermal_monitoring_integration(self, mock_thermal_check):
        """
        Testa integração do monitoramento térmico no worker de temperatura
        """
        # Simular monitoramento habilitado
        with patch.dict(HARDWARE_MONITORING, {"enable_hd_thermal_monitoring": True}):
            # Reinicializar queue manager com monitoramento habilitado
            queue_manager = ConversionQueueManager()
            
            # Verificar se o método de verificação térmica seria chamado
            # (teste conceitual - o método real roda em thread separada)
            self.assertTrue(hasattr(queue_manager, '_check_hd_thermal_status'))
    
    def test_get_hd_thermal_status_method(self):
        """
        Testa método público para obter status térmico do HD
        """
        # Executar método
        thermal_status = self.queue_manager.get_hd_thermal_status()
        
        # Verificar estrutura da resposta
        self.assertIsInstance(thermal_status, dict)
        self.assertIn("monitoring_enabled", thermal_status)
        self.assertIn("temperatures", thermal_status)
        self.assertIn("thermal_protection_active", thermal_status)
        
        # Verificar tipos
        self.assertIsInstance(thermal_status["monitoring_enabled"], bool)
        self.assertIsInstance(thermal_status["temperatures"], dict)
        self.assertIsInstance(thermal_status["thermal_protection_active"], bool)
    
    def test_thermal_protection_activation(self):
        """
        Testa ativação da proteção térmica
        """
        # Verificar método de verificação de proteção térmica
        is_active = self.queue_manager.is_hd_thermal_protection_active()
        self.assertIsInstance(is_active, bool)


class TestThermalConfiguration(unittest.TestCase):
    """
    Testes para configurações de monitoramento térmico
    """
    
    def test_hardware_monitoring_config_exists(self):
        """
        Testa se as configurações de monitoramento térmico existem
        """
        # Verificar configurações obrigatórias
        required_configs = [
            "enable_hd_thermal_monitoring",
            "hd_thermal_check_interval", 
            "hd_temp_warning_threshold",
            "hd_temp_critical_threshold",
            "hd_thermal_protection",
            "hd_thermal_cooldown_time",
            "hd_thermal_cache_duration"
        ]
        
        for config in required_configs:
            self.assertIn(config, HARDWARE_MONITORING, 
                         f"Configuração {config} não encontrada em HARDWARE_MONITORING")
    
    def test_thermal_thresholds_validity(self):
        """
        Testa validade dos limites de temperatura configurados
        """
        warning_threshold = HARDWARE_MONITORING.get("hd_temp_warning_threshold", 50)
        critical_threshold = HARDWARE_MONITORING.get("hd_temp_critical_threshold", 60)
        
        # Verificar se os limites são números válidos
        self.assertIsInstance(warning_threshold, (int, float))
        self.assertIsInstance(critical_threshold, (int, float))
        
        # Verificar se o limite crítico é maior que o de aviso
        self.assertGreater(critical_threshold, warning_threshold)
        
        # Verificar se os limites estão em faixas razoáveis
        self.assertGreater(warning_threshold, 20)  # Mínimo razoável
        self.assertLess(critical_threshold, 100)   # Máximo razoável


if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Executar testes
    unittest.main(verbosity=2)