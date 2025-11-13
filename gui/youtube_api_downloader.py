"""
YouTube Data API v3 Downloader - Versão Anti-Detecção Avançada
Módulo para download de vídeos do YouTube usando técnicas anti-detecção:
- YouTube Data API v3 para metadados oficiais
- Extrator personalizado com rotação de identidade
- Sistema de proxies gratuitos e cache inteligente
- Bypass de rate limiting e detecção de bot
"""

import os
import re
import json
import requests
import urllib.parse
from typing import Dict, List, Optional, Tuple, Callable
import threading
import time
import subprocess
import tempfile
import random
import hashlib
from datetime import datetime, timedelta


class IdentityRotator:
    """Gerencia rotação de User-Agents e identidades para evitar detecção"""
    
    USER_AGENTS = [
        # Chrome Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Safari macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
        # Edge Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
        # Chrome Android
        'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
        # iPhone Safari
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
    ]
    
    @classmethod
    def get_random_user_agent(cls) -> str:
        """Retorna um User-Agent aleatório"""
        return random.choice(cls.USER_AGENTS)
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """Retorna headers realistas com User-Agent rotativo"""
        return {
            'User-Agent': cls.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }


class ProxyManager:
    """Gerencia proxies gratuitos para rotação de IP"""
    
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.last_update = None
        
    def get_free_proxies(self) -> List[str]:
        """Obtém lista de proxies gratuitos de fontes públicas"""
        proxy_sources = [
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
        ]
        
        all_proxies = []
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\n')
                    all_proxies.extend([p.strip() for p in proxies if p.strip()])
            except:
                continue
                
        return list(set(all_proxies))  # Remove duplicatas
    
    def test_proxy(self, proxy: str) -> bool:
        """Testa se um proxy está funcionando"""
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(
                'http://httpbin.org/ip', 
                proxies=proxy_dict, 
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def update_working_proxies(self):
        """Atualiza lista de proxies funcionais"""
        if self.last_update and datetime.now() - self.last_update < timedelta(hours=1):
            return  # Não atualizar se foi feito há menos de 1 hora
            
        print("Atualizando lista de proxies...")
        self.proxies = self.get_free_proxies()
        self.working_proxies = []
        
        # Testa até 10 proxies aleatórios
        test_proxies = random.sample(self.proxies, min(10, len(self.proxies)))
        for proxy in test_proxies:
            if self.test_proxy(proxy):
                self.working_proxies.append(proxy)
                
        self.last_update = datetime.now()
        print(f"Proxies funcionais encontrados: {len(self.working_proxies)}")
    
    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Retorna um proxy aleatório funcionnal"""
        if not self.working_proxies:
            self.update_working_proxies()
            
        if self.working_proxies:
            proxy = random.choice(self.working_proxies)
            return {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
        return None


class URLCache:
    """Sistema de cache para URLs de vídeo válidas"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(hours=1)  # Cache por 1 hora
    
    def _get_cache_key(self, video_id: str, quality: str) -> str:
        """Gera chave única para o cache"""
        return hashlib.md5(f"{video_id}_{quality}".encode()).hexdigest()
    
    def get(self, video_id: str, quality: str) -> Optional[str]:
        """Recupera URL do cache se ainda válida"""
        key = self._get_cache_key(video_id, quality)
        if key in self.cache:
            url, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_duration:
                return url
            else:
                del self.cache[key]  # Remove cache expirado
        return None
    
    def set(self, video_id: str, quality: str, url: str):
        """Armazena URL no cache"""
        key = self._get_cache_key(video_id, quality)
        self.cache[key] = (url, datetime.now())
    
    def clear_expired(self):
        """Remove entradas expiradas do cache"""
        now = datetime.now()
        expired_keys = [
            key for key, (url, timestamp) in self.cache.items()
            if now - timestamp >= self.cache_duration
        ]
        for key in expired_keys:
            del self.cache[key]


class YouTubeAPIDownloader:
    """
    Downloader avançado do YouTube com técnicas anti-detecção:
    - API oficial para metadados (sem detecção de bot)
    - Extrator personalizado com rotação de identidade
    - Sistema de proxies e cache inteligente
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa o downloader com a chave da API.
        
        Args:
            api_key: Chave da YouTube Data API v3
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        # Inicializa componentes anti-detecção
        self.identity_rotator = IdentityRotator()
        self.proxy_manager = ProxyManager()
        self.url_cache = URLCache()
        
        # Session com headers rotativos
        self.session = requests.Session()
        self._update_session_headers()
        
        # Controle de rate limiting
        self.last_request_time = 0
        self.min_delay = 2  # Mínimo 2 segundos entre requisições
        self.max_delay = 5  # Máximo 5 segundos
        
    def _update_session_headers(self):
        """Atualiza headers da sessão com identidade rotativa"""
        self.session.headers.update(self.identity_rotator.get_headers())
        
    def _apply_rate_limiting(self):
        """Aplica delay aleatório para evitar detecção de bot"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            delay = random.uniform(self.min_delay, self.max_delay)
            print(f"Aplicando delay anti-detecção: {delay:.1f}s")
            time.sleep(delay)
            
        self.last_request_time = time.time()
        
    def _make_request_with_fallback(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Faz requisição com fallback de proxy e rotação de identidade"""
        self._apply_rate_limiting()
        self._update_session_headers()
        
        method = kwargs.pop('method', 'GET')
        
        # Tenta primeiro sem proxy
        try:
            response = self.session.request(method, url, timeout=10, **kwargs)
            if response.status_code == 200:
                return response
        except Exception as e:
            print(f"Requisição direta falhou: {e}")
        
        # Tenta com proxy se disponível
        proxy = self.proxy_manager.get_random_proxy()
        if proxy:
            try:
                print("Tentando com proxy...")
                response = self.session.request(method, url, proxies=proxy, timeout=15, **kwargs)
                if response.status_code == 200:
                    return response
            except Exception as e:
                print(f"Requisição com proxy falhou: {e}")
        
        return None
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extrai o ID do vídeo de uma URL do YouTube.
        
        Args:
            url: URL do YouTube
            
        Returns:
            ID do vídeo ou None se inválido
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube\.com/embed/([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info(self, video_id: str) -> Dict:
        """
        Obtém informações do vídeo usando YouTube Data API v3.
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Dicionário com informações do vídeo
        """
        try:
            url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet,contentDetails,statistics',
                'id': video_id,
                'key': self.api_key
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('items'):
                raise Exception("Vídeo não encontrado ou privado")
            
            video = data['items'][0]
            snippet = video['snippet']
            
            return {
                'id': video_id,
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'duration': video['contentDetails']['duration'],
                'view_count': video['statistics'].get('viewCount', '0'),
                'channel': snippet['channelTitle'],
                'upload_date': snippet['publishedAt']
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro na API do YouTube: {e}")
        except KeyError as e:
            raise Exception(f"Resposta da API inválida: {e}")
    
    def get_video_streams_custom(self, video_id: str, quality: str = "720p") -> Dict:
        """
        Extrator personalizado usando engenharia reversa da API interna do YouTube.
        
        Args:
            video_id: ID do vídeo
            quality: Qualidade desejada (720p, 1080p, etc.)
            
        Returns:
            Dicionário com informações do stream
        """
        # Verifica cache primeiro
        cached_url = self.url_cache.get(video_id, quality)
        if cached_url:
            print(f"URL encontrada no cache para {video_id} ({quality})")
            return {
                'url': cached_url,
                'quality': quality,
                'source': 'cache'
            }
        
        try:
            print(f"Extraindo URLs para {video_id} usando método personalizado...")
            
            # Estratégia 1: Tentar com cliente WEB_EMBEDDED (mais difícil de detectar)
            player_url = "https://www.youtube.com/youtubei/v1/player"
            
            # Payload que simula o player embarcado (menos restritivo)
            payload = {
                'context': {
                    'client': {
                        'clientName': 'WEB_EMBEDDED_PLAYER',
                        'clientVersion': '1.20240125.00.00',
                        'hl': 'pt-BR',
                        'gl': 'BR',
                        'userAgent': self.identity_rotator.get_random_user_agent()
                    },
                    'thirdParty': {
                        'embedUrl': f'https://www.youtube.com/embed/{video_id}'
                    }
                },
                'videoId': video_id,
                'playbackContext': {
                    'contentPlaybackContext': {
                        'html5Preference': 'HTML5_PREF_WANTS'
                    }
                }
            }
            
            # Headers que simulam o player embarcado
            headers = self.identity_rotator.get_headers()
            headers.update({
                'Content-Type': 'application/json',
                'X-YouTube-Client-Name': '56',  # WEB_EMBEDDED_PLAYER
                'X-YouTube-Client-Version': '1.20240125.00.00',
                'Origin': 'https://www.youtube.com',
                'Referer': f'https://www.youtube.com/embed/{video_id}'
            })
            
            # Tenta múltiplos clientes em ordem de prioridade
            clients_to_try = [
                {
                    'name': 'WEB_EMBEDDED_PLAYER',
                    'client_name': '56',
                    'version': '1.20240125.00.00',
                    'payload_update': {
                        'context': {
                            'client': {
                                'clientName': 'WEB_EMBEDDED_PLAYER',
                                'clientVersion': '1.20240125.00.00'
                            }
                        }
                    }
                },
                {
                    'name': 'ANDROID_EMBEDDED',
                    'client_name': '55',
                    'version': '19.09.37',
                    'payload_update': {
                        'context': {
                            'client': {
                                'clientName': 'ANDROID_EMBEDDED',
                                'clientVersion': '19.09.37',
                                'androidSdkVersion': 30,
                                'osName': 'Android',
                                'osVersion': '11'
                            }
                        }
                    }
                }
            ]
            
            response = None
            for client in clients_to_try:
                try:
                    print(f"🔄 Tentando cliente: {client['name']}")
                    
                    # Atualiza headers para o cliente atual
                    current_headers = headers.copy()
                    current_headers['X-YouTube-Client-Name'] = client['client_name']
                    current_headers['X-YouTube-Client-Version'] = client['version']
                    
                    # Atualiza payload para o cliente atual
                    current_payload = payload.copy()
                    current_payload.update(client['payload_update'])
                    
                    # Faz requisição
                    response = self._make_request_with_fallback(
                        player_url,
                        method='POST',
                        json=current_payload,
                        headers=current_headers
                    )
                    
                    if response and response.status_code == 200:
                        print(f"✅ Sucesso com cliente: {client['name']}")
                        break
                    else:
                        print(f"❌ Falha com cliente: {client['name']}")
                        
                except Exception as e:
                    print(f"❌ Erro com cliente {client['name']}: {str(e)}")
                    continue
            
            if not response:
                print("❌ Falha ao obter resposta da API interna")
                raise Exception("Falha ao obter resposta da API interna")
            
            data = response.json()
            print(f"📊 Resposta da API interna recebida (status: {response.status_code})")
            
            # Debug: verificar se temos streamingData
            has_streaming = 'streamingData' in data
            print(f"🔍 streamingData presente: {has_streaming}")
            
            if has_streaming:
                streaming_data = data['streamingData']
                formats_count = len(streaming_data.get('formats', []))
                adaptive_count = len(streaming_data.get('adaptiveFormats', []))
                print(f"📹 Formatos encontrados: {formats_count} combinados, {adaptive_count} adaptativos")
            
            # Extrai URLs dos streams
            if 'streamingData' in data:
                streaming_data = data['streamingData']
                formats = streaming_data.get('formats', []) + streaming_data.get('adaptiveFormats', [])
                
                # Filtra por qualidade desejada
                target_height = self._get_target_height(quality)
                best_format = None
                
                print(f"🎯 Qualidade solicitada: {quality} (target: {target_height}p)")
                print(f"📊 Formatos disponíveis: {len(formats)}")
                
                # Estratégia inteligente de seleção de formato
                print(f"🔍 Analisando {len(formats)} formatos disponíveis...")
                
                # 1. Prioriza formatos combinados (vídeo + áudio)
                combined_formats = []
                adaptive_video_formats = []
                
                for fmt in formats:
                    if 'url' not in fmt or not fmt.get('height'):
                        continue
                        
                    mime_type = fmt.get('mimeType', '')
                    has_audio = (
                        'acodec' in mime_type or 
                        fmt.get('audioChannels') is not None or
                        'audio' in mime_type.lower() or
                        fmt.get('acodec', 'none') != 'none'
                    )
                    
                    if mime_type.startswith('video/') or fmt.get('height'):
                        if has_audio:
                            combined_formats.append(fmt)
                        else:
                            adaptive_video_formats.append(fmt)
                
                print(f"🎬 Formatos combinados: {len(combined_formats)}")
                print(f"📹 Formatos adaptativos: {len(adaptive_video_formats)}")
                
                # 2. Escolhe a melhor estratégia
                target_formats = combined_formats if combined_formats else adaptive_video_formats
                
                if not target_formats:
                    print("❌ Nenhum formato de vídeo encontrado")
                    raise Exception("Nenhum formato de vídeo encontrado")
                
                # 3. Análise de resoluções disponíveis
                available_heights = [fmt.get('height') for fmt in target_formats if fmt.get('height')]
                unique_heights = sorted(set(available_heights), reverse=True)
                print(f"📐 Resoluções disponíveis: {unique_heights}")
                
                # 4. Seleção inteligente de formato
                best_format = None
                
                if quality.lower() == "original":
                    # Para "Original", pega a maior resolução
                    for fmt in target_formats:
                        fmt_height = fmt.get('height', 0)
                        if not best_format or fmt_height > best_format.get('height', 0):
                            best_format = fmt
                else:
                    # Para resoluções específicas, usa estratégia inteligente
                    exact_match = None
                    closest_lower = None
                    closest_higher = None
                    
                    for fmt in target_formats:
                        fmt_height = fmt.get('height', 0)
                        
                        if fmt_height == target_height:
                            exact_match = fmt
                        elif fmt_height < target_height:
                            if not closest_lower or fmt_height > closest_lower.get('height', 0):
                                closest_lower = fmt
                        elif fmt_height > target_height:
                            if not closest_higher or fmt_height < closest_higher.get('height', 0):
                                closest_higher = fmt
                    
                    # Prioridade: exato > menor mais próximo > maior mais próximo
                    best_format = exact_match or closest_lower or closest_higher
                
                if best_format and 'url' in best_format:
                    url = best_format['url']
                    selected_height = best_format.get('height', 'unknown')
                    
                    print(f"✅ Formato selecionado: {selected_height}p")
                    
                    # Armazena no cache
                    self.url_cache.set(video_id, quality, url)
                    
                    return {
                        'url': url,
                        'quality': f"{selected_height}p",
                        'format': best_format.get('mimeType', 'unknown'),
                        'source': 'custom_extractor'
                    }
            
            raise Exception("Nenhum stream encontrado na resposta")
            
        except Exception as e:
            print(f"Extrator personalizado falhou: {e}")
            # Fallback para yt-dlp simplificado
            return self._fallback_ytdlp(video_id, quality)
    
    def _get_format_filter(self, quality: str) -> str:
        """
        Gera filtro de formato para yt-dlp baseado na qualidade.
        Usa códigos específicos do YouTube para forçar resolução exata.
        
        Args:
            quality: Qualidade desejada (720p, 1080p, Original, etc.)
            
        Returns:
            String do filtro de formato
        """
        # Mapeamento de resoluções para códigos específicos do YouTube
        format_codes = {
            '2160': '313+140',  # 4K + AAC
            '1440': '271+140',  # 1440p + AAC  
            '1080': '137+140',  # 1080p H.264 + AAC
            '720': '136+140',   # 720p H.264 + AAC
            '480': '135+140',   # 480p H.264 + AAC
            '360': '134+140',   # 360p H.264 + AAC
            '240': '133+140',   # 240p H.264 + AAC
            '144': '160+140'    # 144p H.264 + AAC
        }
        
        if quality.lower() == "original":
            # Para original, tenta 4K -> 1440p -> 1080p -> melhor disponível
            return "313+140/271+140/137+140/best"
        elif quality.endswith('p'):
            height = quality[:-1]
            if height in format_codes:
                # Força código específico + fallbacks inteligentes
                specific_code = format_codes[height]
                fallback_codes = []
                
                # Adiciona fallbacks para resoluções menores
                for res in ['1080', '720', '480', '360', '240', '144']:
                    if int(res) <= int(height) and res != height:
                        fallback_codes.append(format_codes[res])
                
                # Monta string final: específico + fallbacks + genérico
                format_string = specific_code
                if fallback_codes:
                    format_string += "/" + "/".join(fallback_codes)
                format_string += f"/best[height<={height}]/best"
                
                return format_string
        
        # Fallback para qualidade padrão (720p)
        return "136+140/best[height<=720]/best"
    
    def _get_target_height(self, quality: str) -> int:
        """
        Converte string de qualidade para altura em pixels.
        
        Args:
            quality: Qualidade desejada (720p, 1080p, Original, etc.)
            
        Returns:
            Altura em pixels
        """
        if quality.lower() == "original":
            return 9999  # Valor alto para pegar a melhor qualidade
        elif quality.endswith('p'):
            height = quality[:-1]
            if height.isdigit():
                return int(height)
        
        # Fallback para 720p
        return 720

    def _fallback_ytdlp(self, video_id: str, quality: str = "720p") -> Dict:
        """
        Fallback usando yt-dlp simplificado como último recurso.
        
        Args:
            video_id: ID do vídeo
            quality: Qualidade desejada
            
        Returns:
            Dicionário com informações do stream
        """
        try:
            format_filter = self._get_format_filter(quality)
            print(f"🔧 Usando fallback yt-dlp para {video_id}...")
            print(f"🎯 Resolução alvo: {quality}")
            print(f"📋 Código de formato: {format_filter}")
            
            # Comando yt-dlp simplificado e otimizado
            cmd = [
                'yt-dlp',
                '--quiet',
                '--no-warnings',
                '--no-playlist',
                '--user-agent', self.identity_rotator.get_random_user_agent(),
                '--referer', f'https://www.youtube.com/watch?v={video_id}',
                '--throttled-rate', '50K',  # Rate limiting agressivo
                '--sleep-interval', '2',     # Pausa entre requests
                '--format', format_filter,
                '--get-url',
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                raise Exception(f"yt-dlp falhou: {result.stderr}")
            
            url = result.stdout.strip()
            if not url:
                raise Exception("URL não encontrada na resposta do yt-dlp")
            
            # Armazena no cache
            self.url_cache.set(video_id, quality, url)
            
            return {
                'url': url,
                'quality': quality,
                'source': 'ytdlp_fallback'
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("Timeout ao obter streams do vídeo")
        except Exception as e:
            print(f"Fallback yt-dlp também falhou: {e}")
            raise Exception(f"Todos os métodos de extração falharam: {e}")
    
    def download_video(
        self,
        url: str,
        output_path: str,
        quality: str = "720p",
        progress_callback: Optional[Callable] = None,
        info_callback: Optional[Callable] = None
    ) -> bool:
        """
        Baixa um vídeo do YouTube usando abordagem híbrida.
        
        Args:
            url: URL do vídeo
            output_path: Caminho de saída
            quality: Qualidade desejada
            progress_callback: Callback para progresso
            info_callback: Callback para informações
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Extrair ID do vídeo
            video_id = self.extract_video_id(url)
            if not video_id:
                raise Exception("URL do YouTube inválida")
            
            if info_callback:
                info_callback("🔍 Obtendo informações do vídeo via API oficial...")
            
            # 1. Obter metadados via API oficial
            video_info = self.get_video_info(video_id)
            
            if info_callback:
                info_callback(f"📹 Vídeo: {video_info['title']}")
                info_callback(f"📺 Canal: {video_info['channel']}")
                info_callback("🔗 Obtendo URLs de download...")
            
            # 2. Obter URLs via extrator personalizado anti-detecção
            print(f"🎯 SOLICITADO: Qualidade {quality}")
            stream_info = self.get_video_streams_custom(video_id, quality)
            print(f"🎬 OBTIDO: {stream_info.get('quality', 'unknown')} via {stream_info.get('source', 'unknown')}")
            
            if info_callback:
                info_callback(f"✅ Stream encontrado: {stream_info['quality']}")
                info_callback("⬇️ Iniciando download...")
            
            # 3. Download direto via requests
            return self._download_stream(
                stream_info['url'],
                output_path,
                video_info['title'],
                progress_callback,
                info_callback
            )
            
        except Exception as e:
            if info_callback:
                info_callback(f"❌ Erro: {e}")
            return False
    
    def _download_stream(
        self,
        stream_url: str,
        output_path: str,
        title: str,
        progress_callback: Optional[Callable] = None,
        info_callback: Optional[Callable] = None
    ) -> bool:
        """
        Faz o download direto do stream.
        
        Args:
            stream_url: URL do stream
            output_path: Caminho de saída
            title: Título do vídeo
            progress_callback: Callback para progresso
            info_callback: Callback para informações
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Sanitizar nome do arquivo
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            filename = f"{safe_title}.mp4"
            full_path = os.path.join(output_path, filename)
            
            # Headers para download
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.youtube.com/',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            
            # Iniciar download
            response = self.session.get(stream_url, headers=headers, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            # Validar se o download foi bem-sucedido (arquivo não pode ser muito pequeno)
            file_size = os.path.getsize(full_path)
            if file_size < 5 * 1024 * 1024:  # Menos de 5MB indica problema
                if info_callback:
                    info_callback(f"⚠️ Arquivo muito pequeno ({file_size/1024/1024:.1f}MB), possível falha no extrator")
                os.remove(full_path)  # Remove arquivo corrompido
                return False
            
            if info_callback:
                info_callback(f"✅ Download concluído: {filename} ({file_size/1024/1024:.1f}MB)")
            
            return True
            
        except Exception as e:
            if info_callback:
                info_callback(f"❌ Erro no download: {e}")
            return False


# ... existing code ...
