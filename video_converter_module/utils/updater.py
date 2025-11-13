#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Verificação e Atualização Automática
Verifica atualizações no GitHub e gerencia o processo de atualização
"""

import json
import os
import sys
import time
import threading
import subprocess
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError, HTTPError
import tkinter as tk
from tkinter import messagebox

from version import __version__, GITHUB_REPO, UPDATE_CHECK_INTERVAL


class UpdateChecker:
    """
    Classe responsável por verificar e gerenciar atualizações do aplicativo
    """
    
    def __init__(self, callback_update_available: Optional[Callable] = None):
        """
        Inicializa o verificador de atualizações
        
        Args:
            callback_update_available: Função chamada quando uma atualização está disponível
        """
        self.current_version = __version__
        self.github_repo = GITHUB_REPO
        self.callback_update_available = callback_update_available
        self.latest_release_info = None
        self.check_interval = UPDATE_CHECK_INTERVAL
        self.is_checking = False
        self.periodic_thread = None
        self._stop_periodic = False  # FLAG DE CONTROLE PARA PARAR O LOOP
        
    def get_latest_release_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações da última release do GitHub
        
        Returns:
            Dicionário com informações da release ou None se houver erro
        """
        try:
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            
            with urlopen(api_url, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return data
                else:
                    print(f"Erro ao consultar API do GitHub: Status {response.status}")
                    return None
                    
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            print(f"Erro ao verificar atualizações: {e}")
            return None
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compara duas versões no formato semântico (v1.0.0)
        
        Args:
            version1: Primeira versão
            version2: Segunda versão
            
        Returns:
            -1 se version1 < version2
             0 se version1 == version2
             1 se version1 > version2
        """
        def normalize_version(v):
            # Remove 'v' do início se existir
            v = v.lstrip('v')
            # Divide em partes e converte para inteiros
            return [int(x) for x in v.split('.')]
        
        try:
            v1_parts = normalize_version(version1)
            v2_parts = normalize_version(version2)
            
            # Garante que ambas tenham o mesmo número de partes
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for i in range(max_len):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1
            
            return 0
            
        except (ValueError, AttributeError):
            return 0
    
    def _is_newer_version(self, current: str, latest: str) -> bool:
        """
        Verifica se a versão latest é mais nova que current
        
        Args:
            current: Versão atual
            latest: Versão mais recente
            
        Returns:
            True se latest for mais nova que current
        """
        return self.compare_versions(current, latest) < 0
    
    def _get_config(self) -> Dict[str, Any]:
        """
        Obtém configuração do sistema de atualizações
        
        Returns:
            Dicionário com configurações
        """
        return {
            'check_interval': UPDATE_CHECK_INTERVAL,
            'auto_download': False,
            'last_check': None
        }
    
    def _save_config(self, config: Dict[str, Any], config_file: str = None):
        """
        Salva configuração em arquivo
        
        Args:
            config: Configuração para salvar
            config_file: Caminho do arquivo (opcional)
        """
        if config_file is None:
            config_file = os.path.join(os.path.expanduser("~"), ".vidconv_config.json")
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
    
    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """
        Carrega configuração de arquivo
        
        Args:
            config_file: Caminho do arquivo (opcional)
            
        Returns:
            Dicionário com configurações
        """
        if config_file is None:
            config_file = os.path.join(os.path.expanduser("~"), ".vidconv_config.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
        
        return self._get_config()
    
    def is_update_available(self) -> bool:
        """
        Verifica se há uma atualização disponível
        
        Returns:
            True se houver atualização disponível
        """
        release_info = self.get_latest_release_info()
        
        if not release_info:
            return False
            
        self.latest_release_info = release_info
        latest_version = release_info.get('tag_name', '')
        
        # Compara versões
        comparison = self.compare_versions(self.current_version, latest_version)
        return comparison < 0  # Atualização disponível se versão atual for menor
    
    def check_for_updates(self, show_no_updates: bool = False) -> bool:
        """
        Verifica atualizações e chama callback se necessário
        
        Args:
            show_no_updates: Se deve mostrar mensagem quando não há atualizações
            
        Returns:
            True se houver atualização disponível
        """
        if self.is_checking:
            return False
            
        self.is_checking = True
        
        try:
            update_available = self.is_update_available()
            
            if update_available and self.callback_update_available:
                self.callback_update_available(self.latest_release_info)
            elif show_no_updates and not update_available:
                messagebox.showinfo(
                    "Verificação de Atualizações",
                    f"Você já está usando a versão mais recente ({self.current_version})"
                )
            
            return update_available
            
        finally:
            self.is_checking = False
    
    def start_periodic_check(self):
        """
        Inicia verificação periódica de atualizações
        """
        if self.periodic_thread and self.periodic_thread.is_alive():
            return
            
        # RESETAR FLAG DE PARADA
        self._stop_periodic = False
            
        def periodic_check():
            # CORREÇÃO CRÍTICA: Loop com condição de parada para evitar superaquecimento
            while not self._stop_periodic:
                try:
                    time.sleep(self.check_interval)
                    if not self._stop_periodic:  # Verificar novamente após o sleep
                        self.check_for_updates()
                except Exception as e:
                    print(f"Erro na verificação periódica: {e}")
                    # Em caso de erro, aguardar mais tempo antes de tentar novamente
                    time.sleep(60)  # 1 minuto de pausa em caso de erro
        
        self.periodic_thread = threading.Thread(target=periodic_check, daemon=True)
        self.periodic_thread.start()
    
    def stop_periodic_check(self):
        """
        Para a verificação periódica de atualizações
        """
        # CORREÇÃO: Usar flag para parar o loop de forma segura
        self._stop_periodic = True
        
        if self.periodic_thread and self.periodic_thread.is_alive():
            # Aguardar a thread terminar graciosamente (máximo 5 segundos)
            self.periodic_thread.join(timeout=5.0)
            if self.periodic_thread.is_alive():
                print("AVISO: Thread de verificação periódica não terminou no tempo esperado")
            self.periodic_thread = None


class UpdateDownloader:
    """
    Classe responsável por baixar e instalar atualizações
    """
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        Inicializa o downloader de atualizações
        
        Args:
            progress_callback: Função chamada para reportar progresso do download
        """
        self.progress_callback = progress_callback
        self.temp_dir = None
        
    def download_update(self, release_info: Dict[str, Any]) -> Optional[str]:
        """
        Baixa a atualização do GitHub
        
        Args:
            release_info: Informações da release obtidas da API
            
        Returns:
            Caminho do arquivo baixado ou None se houver erro
        """
        try:
            # Procura por assets (arquivos) na release
            assets = release_info.get('assets', [])
            
            # Prioriza executáveis (.exe) para Windows
            download_url = None
            filename = None
            
            for asset in assets:
                asset_name = asset.get('name', '').lower()
                if asset_name.endswith('.exe'):
                    download_url = asset.get('browser_download_url')
                    filename = asset.get('name')
                    break
            
            # Se não encontrar executável, usa o código fonte
            if not download_url:
                download_url = release_info.get('zipball_url')
                filename = f"vidconv-{release_info.get('tag_name', 'latest')}.zip"
            
            if not download_url:
                print("Nenhum arquivo de atualização encontrado")
                return None
            
            # Cria diretório temporário
            self.temp_dir = tempfile.mkdtemp(prefix='vidconv_update_')
            file_path = os.path.join(self.temp_dir, filename)
            
            # Baixa o arquivo
            def progress_hook(block_num, block_size, total_size):
                if self.progress_callback and total_size > 0:
                    progress = min(100, (block_num * block_size * 100) // total_size)
                    self.progress_callback(progress)
            
            urlretrieve(download_url, file_path, progress_hook)
            return file_path
            
        except Exception as e:
            print(f"Erro ao baixar atualização: {e}")
            return None
    
    def install_update(self, file_path: str, release_info: Dict[str, Any]) -> bool:
        """
        Instala a atualização baixada
        
        Args:
            file_path: Caminho do arquivo baixado
            release_info: Informações da release
            
        Returns:
            True se a instalação foi bem-sucedida
        """
        try:
            if file_path.endswith('.exe'):
                return self._install_executable(file_path)
            elif file_path.endswith('.zip'):
                return self._install_source_code(file_path)
            else:
                print(f"Tipo de arquivo não suportado: {file_path}")
                return False
                
        except Exception as e:
            print(f"Erro ao instalar atualização: {e}")
            return False
    
    def _install_executable(self, exe_path: str) -> bool:
        """
        Instala atualização a partir de executável
        
        Args:
            exe_path: Caminho do executável
            
        Returns:
            True se a instalação foi bem-sucedida
        """
        try:
            # Executa o instalador
            result = subprocess.run([exe_path, '/S'], capture_output=True, text=True, encoding='utf-8', errors='replace')
            return result.returncode == 0
            
        except Exception as e:
            print(f"Erro ao executar instalador: {e}")
            return False
    
    def _install_source_code(self, zip_path: str) -> bool:
        """
        Instala atualização a partir do código fonte
        
        Args:
            zip_path: Caminho do arquivo ZIP
            
        Returns:
            True se a instalação foi bem-sucedida
        """
        try:
            # Extrai o ZIP
            extract_dir = os.path.join(self.temp_dir, 'extracted')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Encontra o diretório principal do projeto
            extracted_items = os.listdir(extract_dir)
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_items[0])):
                source_dir = os.path.join(extract_dir, extracted_items[0])
            else:
                source_dir = extract_dir
            
            # Obtém o diretório atual do aplicativo
            current_dir = Path(__file__).parent.parent
            
            # Cria backup do diretório atual
            backup_dir = current_dir.parent / f"vidconv_backup_{int(time.time())}"
            shutil.copytree(current_dir, backup_dir)
            
            # Copia novos arquivos (exceto alguns diretórios)
            exclude_dirs = {'logs', '__pycache__', '.git', '.pytest_cache'}
            
            for item in os.listdir(source_dir):
                if item not in exclude_dirs:
                    source_item = os.path.join(source_dir, item)
                    dest_item = current_dir / item
                    
                    if os.path.isdir(source_item):
                        if dest_item.exists():
                            shutil.rmtree(dest_item)
                        shutil.copytree(source_item, dest_item)
                    else:
                        shutil.copy2(source_item, dest_item)
            
            return True
            
        except Exception as e:
            print(f"Erro ao instalar código fonte: {e}")
            return False
    
    def _create_backup_directory(self, backup_dir: str):
        """
        Cria diretório de backup
        
        Args:
            backup_dir: Caminho do diretório de backup
        """
        os.makedirs(backup_dir, exist_ok=True)
    
    def _backup_file(self, file_path: str, backup_dir: str) -> str:
        """
        Cria backup de um arquivo
        
        Args:
            file_path: Caminho do arquivo original
            backup_dir: Diretório de backup
            
        Returns:
            Caminho do arquivo de backup
        """
        filename = os.path.basename(file_path)
        backup_path = os.path.join(backup_dir, filename)
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Valida se uma URL é válida
        
        Args:
            url: URL para validar
            
        Returns:
            True se a URL for válida
        """
        if not url or not isinstance(url, str):
            return False
        
        return url.startswith(('http://', 'https://'))
    
    def _get_appropriate_asset(self, release_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Obtém o asset apropriado para o sistema atual
        
        Args:
            release_data: Dados da release
            
        Returns:
            Asset apropriado ou None
        """
        import platform
        
        assets = release_data.get('assets', [])
        system = platform.system().lower()
        
        # Procura por asset específico do sistema
        for asset in assets:
            name = asset.get('name', '').lower()
            if system == 'windows' and ('windows' in name or '.exe' in name):
                return asset
            elif system == 'linux' and ('linux' in name or '.tar.gz' in name):
                return asset
            elif system == 'darwin' and ('macos' in name or '.dmg' in name):
                return asset
        
        # Se não encontrar específico, retorna o primeiro
        return assets[0] if assets else None

    def cleanup(self):
        """
        Limpa arquivos temporários
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Erro ao limpar arquivos temporários: {e}")


def restart_application(delay_seconds: int = 2):
    """
    Reinicia a aplicação atual com delay opcional
    
    Args:
        delay_seconds: Tempo de espera antes de reiniciar (padrão: 2 segundos)
    """
    try:
        # Obtém o caminho do script principal
        main_script = sys.argv[0]
        
        # Se for um executável compilado, usa o caminho do executável
        if hasattr(sys, 'frozen'):
            main_script = sys.executable
        else:
            # Para scripts Python, garante que o caminho está correto
            main_script = os.path.abspath(main_script)
        
        # Cria um script de reinicialização temporário para Windows
        restart_script = _create_restart_script(main_script, delay_seconds)
        
        # Executa o script de reinicialização
        subprocess.Popen([restart_script], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        # Encerra a aplicação atual
        sys.exit(0)
        
    except Exception as e:
        print(f"Erro ao reiniciar aplicação: {e}")
        messagebox.showerror(
            "Erro de Reinicialização",
            f"Não foi possível reiniciar automaticamente.\nPor favor, reinicie manualmente.\n\nErro: {e}"
        )


def _create_restart_script(app_path: str, delay_seconds: int) -> str:
    """
    Cria um script temporário para reinicializar a aplicação
    
    Args:
        app_path: Caminho para a aplicação
        delay_seconds: Tempo de espera antes de reiniciar
        
    Returns:
        Caminho para o script de reinicialização
    """
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "vidconv_restart.bat")
    
    # Conteúdo do script batch para Windows
    script_content = f"""@echo off
echo Aguardando {delay_seconds} segundos antes de reiniciar...
timeout /t {delay_seconds} /nobreak >nul
echo Reiniciando VidConv...
start "" "{app_path}"
del "%~f0"
"""
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        return script_path
    except Exception as e:
        print(f"Erro ao criar script de reinicialização: {e}")
        # Fallback para método simples
        return _create_simple_restart(app_path)


def _create_simple_restart(app_path: str) -> str:
    """
    Método de fallback para reinicialização simples
    
    Args:
        app_path: Caminho para a aplicação
        
    Returns:
        Comando para reinicialização
    """
    if hasattr(sys, 'frozen'):
        # Para executáveis compilados
        subprocess.Popen([app_path])
    else:
        # Para scripts Python
        subprocess.Popen([sys.executable, app_path] + sys.argv[1:])
    
    return app_path


def schedule_restart(delay_minutes: int = 0):
    """
    Agenda uma reinicialização da aplicação
    
    Args:
        delay_minutes: Minutos para aguardar antes de reiniciar (0 = imediato)
    """
    def delayed_restart():
        if delay_minutes > 0:
            time.sleep(delay_minutes * 60)
        restart_application()
    
    restart_thread = threading.Thread(target=delayed_restart, daemon=True)
    restart_thread.start()
    
    if delay_minutes > 0:
        messagebox.showinfo(
            "Reinicialização Agendada",
            f"A aplicação será reiniciada em {delay_minutes} minuto(s)."
        )