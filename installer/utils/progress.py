"""
📊 Sistema de Progress Bars - VideoConverter Installer
=====================================================

Progress bars avançados para CLI:
- Múltiplos estilos visuais
- Animações suaves
- Informações detalhadas (velocidade, tempo restante)
- Suporte a múltiplas barras simultâneas
- Integração com sistema de logs
"""

import sys
import time
import threading
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import colorama
from colorama import Fore, Back, Style

# Inicializar colorama
colorama.init(autoreset=True)


@dataclass
class ProgressInfo:
    """Informações de progresso"""
    current: int
    total: int
    start_time: float
    description: str
    speed: float = 0.0
    eta: Optional[float] = None
    percentage: float = 0.0


class ProgressStyle:
    """Estilos de progress bar disponíveis"""
    
    # Caracteres para diferentes estilos
    STYLES = {
        "classic": {
            "filled": "█",
            "empty": "░",
            "prefix": "[",
            "suffix": "]"
        },
        "modern": {
            "filled": "▰",
            "empty": "▱",
            "prefix": "│",
            "suffix": "│"
        },
        "dots": {
            "filled": "●",
            "empty": "○",
            "prefix": "(",
            "suffix": ")"
        },
        "arrows": {
            "filled": "▶",
            "empty": "▷",
            "prefix": "<",
            "suffix": ">"
        },
        "blocks": {
            "filled": "■",
            "empty": "□",
            "prefix": "[",
            "suffix": "]"
        }
    }
    
    # Cores por tipo de operação
    COLORS = {
        "download": Fore.CYAN,
        "install": Fore.GREEN,
        "compile": Fore.YELLOW,
        "verify": Fore.MAGENTA,
        "extract": Fore.BLUE,
        "configure": Fore.WHITE,
        "error": Fore.RED,
        "success": Fore.GREEN
    }


class ProgressBar:
    """
    Progress bar avançado para CLI
    
    Funcionalidades:
    - Múltiplos estilos visuais
    - Cálculo automático de velocidade e ETA
    - Animações suaves
    - Informações detalhadas
    - Thread-safe
    """
    
    def __init__(
        self,
        total: int,
        description: str = "",
        style: str = "classic",
        color: str = "download",
        width: int = 40,
        show_percentage: bool = True,
        show_speed: bool = True,
        show_eta: bool = True,
        show_count: bool = True
    ):
        """
        Inicializa progress bar
        
        Args:
            total: Valor total
            description: Descrição da operação
            style: Estilo visual (classic, modern, dots, arrows, blocks)
            color: Cor da barra (download, install, compile, etc.)
            width: Largura da barra em caracteres
            show_percentage: Mostrar porcentagem
            show_speed: Mostrar velocidade
            show_eta: Mostrar tempo estimado
            show_count: Mostrar contadores
        """
        self.total = total
        self.description = description
        self.style_name = style
        self.color = ProgressStyle.COLORS.get(color, Fore.WHITE)
        self.width = width
        self.show_percentage = show_percentage
        self.show_speed = show_speed
        self.show_eta = show_eta
        self.show_count = show_count
        
        # Estado interno
        self.current = 0
        self.start_time = time.time()
        self.last_update = self.start_time
        self.completed = False
        self.cancelled = False
        
        # Estilo visual
        self.style = ProgressStyle.STYLES.get(style, ProgressStyle.STYLES["classic"])
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Histórico para cálculo de velocidade
        self._history = []
        self._max_history = 10
    
    def update(self, current: Optional[int] = None, increment: int = 1, description: Optional[str] = None):
        """
        Atualiza o progresso
        
        Args:
            current: Valor atual (ou None para incrementar)
            increment: Valor para incrementar se current é None
            description: Nova descrição (opcional)
        """
        with self._lock:
            if self.completed or self.cancelled:
                return
            
            # Atualizar valor atual
            if current is not None:
                self.current = min(current, self.total)
            else:
                self.current = min(self.current + increment, self.total)
            
            # Atualizar descrição
            if description:
                self.description = description
            
            # Atualizar histórico
            now = time.time()
            self._history.append((now, self.current))
            
            # Manter histórico limitado
            if len(self._history) > self._max_history:
                self._history.pop(0)
            
            # Verificar se completou
            if self.current >= self.total:
                self.completed = True
            
            # Renderizar
            self._render()
    
    def _calculate_speed(self) -> float:
        """Calcula velocidade atual"""
        if len(self._history) < 2:
            return 0.0
        
        # Usar últimos pontos para cálculo
        recent_time, recent_value = self._history[-1]
        old_time, old_value = self._history[0]
        
        time_diff = recent_time - old_time
        value_diff = recent_value - old_value
        
        if time_diff > 0:
            return value_diff / time_diff
        
        return 0.0
    
    def _calculate_eta(self, speed: float) -> Optional[float]:
        """Calcula tempo estimado para conclusão"""
        if speed <= 0 or self.current >= self.total:
            return None
        
        remaining = self.total - self.current
        return remaining / speed
    
    def _format_time(self, seconds: float) -> str:
        """Formata tempo em formato legível"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:.0f}m{secs:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h{minutes:.0f}m"
    
    def _format_speed(self, speed: float) -> str:
        """Formata velocidade"""
        if speed < 1:
            return f"{speed:.2f}/s"
        elif speed < 1000:
            return f"{speed:.1f}/s"
        elif speed < 1000000:
            return f"{speed/1000:.1f}K/s"
        else:
            return f"{speed/1000000:.1f}M/s"
    
    def _render(self):
        """Renderiza a progress bar"""
        # Calcular porcentagem
        percentage = (self.current * 100) // self.total if self.total > 0 else 0
        
        # Calcular velocidade e ETA
        speed = self._calculate_speed()
        eta = self._calculate_eta(speed)
        
        # Construir barra visual
        filled_width = (self.current * self.width) // self.total if self.total > 0 else 0
        empty_width = self.width - filled_width
        
        filled_chars = self.style["filled"] * filled_width
        empty_chars = self.style["empty"] * empty_width
        
        bar = f"{self.style['prefix']}{filled_chars}{empty_chars}{self.style['suffix']}"
        
        # Aplicar cor
        colored_bar = f"{self.color}{bar}{Style.RESET_ALL}"
        
        # Construir linha de status
        parts = []
        
        # Descrição
        if self.description:
            parts.append(f"{self.description}")
        
        # Barra
        parts.append(colored_bar)
        
        # Porcentagem
        if self.show_percentage:
            parts.append(f"{percentage:3d}%")
        
        # Contadores
        if self.show_count:
            parts.append(f"({self.current}/{self.total})")
        
        # Velocidade
        if self.show_speed and speed > 0:
            parts.append(f"{self._format_speed(speed)}")
        
        # ETA
        if self.show_eta and eta is not None:
            parts.append(f"ETA: {self._format_time(eta)}")
        
        # Status final
        if self.completed:
            elapsed = time.time() - self.start_time
            parts.append(f"✅ Concluído em {self._format_time(elapsed)}")
        elif self.cancelled:
            parts.append("❌ Cancelado")
        
        # Renderizar linha
        line = " ".join(parts)
        
        # Limpar linha anterior e escrever nova
        print(f"\r{line:<80}", end="", flush=True)
        
        # Nova linha se completou
        if self.completed or self.cancelled:
            print()
    
    def finish(self, description: Optional[str] = None):
        """
        Finaliza a progress bar
        
        Args:
            description: Descrição final (opcional)
        """
        with self._lock:
            self.current = self.total
            if description:
                self.description = description
            self.completed = True
            self._render()
    
    def cancel(self, description: Optional[str] = None):
        """
        Cancela a progress bar
        
        Args:
            description: Descrição de cancelamento (opcional)
        """
        with self._lock:
            if description:
                self.description = description
            self.cancelled = True
            self._render()
    
    def get_info(self) -> ProgressInfo:
        """
        Retorna informações atuais do progresso
        
        Returns:
            ProgressInfo: Informações detalhadas
        """
        with self._lock:
            speed = self._calculate_speed()
            eta = self._calculate_eta(speed)
            percentage = (self.current * 100) / self.total if self.total > 0 else 0
            
            return ProgressInfo(
                current=self.current,
                total=self.total,
                start_time=self.start_time,
                description=self.description,
                speed=speed,
                eta=eta,
                percentage=percentage
            )


class MultiProgressBar:
    """
    Gerenciador de múltiplas progress bars
    
    Permite exibir várias barras de progresso simultaneamente
    """
    
    def __init__(self):
        """Inicializa gerenciador de múltiplas barras"""
        self.bars: Dict[str, ProgressBar] = {}
        self._lock = threading.Lock()
        self._active = True
    
    def add_bar(
        self,
        name: str,
        total: int,
        description: str = "",
        **kwargs
    ) -> ProgressBar:
        """
        Adiciona nova progress bar
        
        Args:
            name: Nome único da barra
            total: Valor total
            description: Descrição
            **kwargs: Argumentos para ProgressBar
            
        Returns:
            ProgressBar: Instância da barra criada
        """
        with self._lock:
            bar = ProgressBar(total, description, **kwargs)
            self.bars[name] = bar
            return bar
    
    def update_bar(self, name: str, current: Optional[int] = None, increment: int = 1, description: Optional[str] = None):
        """
        Atualiza barra específica
        
        Args:
            name: Nome da barra
            current: Valor atual
            increment: Incremento
            description: Nova descrição
        """
        with self._lock:
            if name in self.bars:
                self.bars[name].update(current, increment, description)
    
    def finish_bar(self, name: str, description: Optional[str] = None):
        """
        Finaliza barra específica
        
        Args:
            name: Nome da barra
            description: Descrição final
        """
        with self._lock:
            if name in self.bars:
                self.bars[name].finish(description)
    
    def cancel_bar(self, name: str, description: Optional[str] = None):
        """
        Cancela barra específica
        
        Args:
            name: Nome da barra
            description: Descrição de cancelamento
        """
        with self._lock:
            if name in self.bars:
                self.bars[name].cancel(description)
    
    def get_summary(self) -> Dict[str, ProgressInfo]:
        """
        Retorna resumo de todas as barras
        
        Returns:
            Dict: Informações de todas as barras
        """
        with self._lock:
            return {name: bar.get_info() for name, bar in self.bars.items()}
    
    def all_completed(self) -> bool:
        """
        Verifica se todas as barras foram completadas
        
        Returns:
            bool: True se todas completadas
        """
        with self._lock:
            return all(bar.completed or bar.cancelled for bar in self.bars.values())
    
    def cleanup(self):
        """Remove barras completadas"""
        with self._lock:
            completed_bars = [
                name for name, bar in self.bars.items()
                if bar.completed or bar.cancelled
            ]
            
            for name in completed_bars:
                del self.bars[name]


# Funções de conveniência
def create_progress_bar(
    total: int,
    description: str = "",
    style: str = "classic",
    color: str = "download"
) -> ProgressBar:
    """
    Cria progress bar com configurações padrão
    
    Args:
        total: Valor total
        description: Descrição
        style: Estilo visual
        color: Cor da barra
        
    Returns:
        ProgressBar: Nova instância
    """
    return ProgressBar(total, description, style, color)


def download_progress_bar(total_bytes: int, filename: str = "") -> ProgressBar:
    """
    Cria progress bar específica para downloads
    
    Args:
        total_bytes: Total de bytes
        filename: Nome do arquivo
        
    Returns:
        ProgressBar: Barra configurada para download
    """
    description = f"Baixando {filename}" if filename else "Download"
    return ProgressBar(
        total=total_bytes,
        description=description,
        style="modern",
        color="download",
        show_speed=True,
        show_eta=True
    )


def installation_progress_bar(total_steps: int, component: str = "") -> ProgressBar:
    """
    Cria progress bar específica para instalação
    
    Args:
        total_steps: Total de passos
        component: Nome do componente
        
    Returns:
        ProgressBar: Barra configurada para instalação
    """
    description = f"Instalando {component}" if component else "Instalação"
    return ProgressBar(
        total=total_steps,
        description=description,
        style="classic",
        color="install",
        show_speed=False,
        show_eta=True
    )


if __name__ == "__main__":
    # Teste das progress bars
    import random
    
    print("🧪 Teste do Sistema de Progress Bars\n")
    
    # Teste básico
    print("1. Progress Bar Básica:")
    bar = create_progress_bar(100, "Processando dados", "modern", "download")
    
    for i in range(101):
        bar.update(i)
        time.sleep(0.02)
    
    print("\n")
    
    # Teste de download
    print("2. Progress Bar de Download:")
    download_bar = download_progress_bar(1024*1024*10, "python-3.13.0.exe")  # 10MB
    
    downloaded = 0
    chunk_size = 1024 * 100  # 100KB chunks
    
    while downloaded < download_bar.total:
        chunk = min(chunk_size, download_bar.total - downloaded)
        downloaded += chunk
        download_bar.update(downloaded)
        time.sleep(0.01)
    
    print("\n")
    
    # Teste de instalação
    print("3. Progress Bar de Instalação:")
    install_bar = installation_progress_bar(5, "Python 3.13")
    
    steps = [
        "Verificando sistema",
        "Extraindo arquivos",
        "Configurando ambiente",
        "Instalando componentes",
        "Finalizando instalação"
    ]
    
    for i, step in enumerate(steps, 1):
        install_bar.update(i, description=f"Passo {i}: {step}")
        time.sleep(1)
    
    print("\n✅ Teste concluído!")