#!/usr/bin/env python3
"""
Protótipo de teste para PyWebView - Versão Corrigida
Testa a funcionalidade básica e integração com YouTube
"""

import webview
import threading
import time
import json
import sys

class YouTubeExtractor:
    def __init__(self):
        self.window = None
        self.extracted_data = {}
        
    def create_window(self):
        """Cria uma janela do navegador para acessar o YouTube"""
        # HTML simplificado para teste
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>YouTube Extractor Test</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background: #f5f5f5;
                }
                .container { 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .input-group { margin: 15px 0; }
                input[type="text"] { 
                    width: 70%; 
                    padding: 10px; 
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                button { 
                    padding: 10px 16px; 
                    margin: 5px; 
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                button:hover { background: #45a049; }
                .result { 
                    background: #f9f9f9; 
                    padding: 15px; 
                    margin: 15px 0; 
                    border-radius: 4px;
                    border-left: 4px solid #4CAF50;
                }
                .log { 
                    background: #2c3e50; 
                    color: #ecf0f1; 
                    padding: 15px; 
                    font-family: 'Courier New', monospace; 
                    border-radius: 4px;
                    max-height: 200px;
                    overflow-y: auto;
                }
                .success { color: #27ae60; }
                .error { color: #e74c3c; }
                .info { color: #3498db; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 YouTube Extractor - PyWebView Test</h1>
                <p><strong>Status:</strong> <span class="success">✅ PyWebView funcionando!</span></p>
                
                <div class="input-group">
                    <input type="text" id="youtube-url" placeholder="Cole a URL do YouTube aqui..." 
                           value="https://www.youtube.com/watch?v=dQw4w9WgXcQ">
                    <button onclick="analyzeUrl()">🔍 Analisar URL</button>
                </div>
                
                <div class="input-group">
                    <button onclick="testBrowserInfo()">🌐 Info do Navegador</button>
                    <button onclick="testJavaScriptCapabilities()">⚡ Capacidades JS</button>
                    <button onclick="simulateYouTubeAccess()">📺 Simular YouTube</button>
                </div>
                
                <div class="result">
                    <h3>📊 Resultados:</h3>
                    <div id="results">Clique em um botão para ver os resultados...</div>
                </div>
                
                <div class="log">
                    <h3>📝 Log do Sistema:</h3>
                    <div id="log"></div>
                </div>
            </div>
            
            <script>
                function log(message, type = 'info') {
                    const logDiv = document.getElementById('log');
                    const timestamp = new Date().toLocaleTimeString();
                    const className = type === 'error' ? 'error' : type === 'success' ? 'success' : 'info';
                    logDiv.innerHTML += `<span class="${className}">[${timestamp}] ${message}</span><br>`;
                    logDiv.scrollTop = logDiv.scrollHeight;
                }
                
                function updateResults(data) {
                    document.getElementById('results').innerHTML = 
                        '<pre style="white-space: pre-wrap; word-wrap: break-word;">' + 
                        JSON.stringify(data, null, 2) + '</pre>';
                }
                
                function analyzeUrl() {
                    const url = document.getElementById('youtube-url').value;
                    log('🔍 Analisando URL: ' + url);
                    
                    const videoId = extractVideoId(url);
                    const analysis = {
                        originalUrl: url,
                        videoId: videoId,
                        isValid: !!videoId,
                        embedUrl: videoId ? `https://www.youtube.com/embed/${videoId}` : null,
                        watchUrl: videoId ? `https://www.youtube.com/watch?v=${videoId}` : null,
                        timestamp: new Date().toISOString()
                    };
                    
                    updateResults(analysis);
                    
                    if (videoId) {
                        log('✅ URL válida! Video ID: ' + videoId, 'success');
                    } else {
                        log('❌ URL inválida!', 'error');
                    }
                }
                
                function extractVideoId(url) {
                    const patterns = [
                        /(?:youtube\\.com\\/watch\\?v=|youtu\\.be\\/)([^&\\n?#]+)/,
                        /youtube\\.com\\/embed\\/([^&\\n?#]+)/,
                        /youtube\\.com\\/v\\/([^&\\n?#]+)/
                    ];
                    
                    for (const pattern of patterns) {
                        const match = url.match(pattern);
                        if (match) return match[1];
                    }
                    return null;
                }
                
                function testBrowserInfo() {
                    log('🌐 Coletando informações do navegador...');
                    
                    const info = {
                        userAgent: navigator.userAgent,
                        language: navigator.language,
                        languages: navigator.languages,
                        platform: navigator.platform,
                        cookieEnabled: navigator.cookieEnabled,
                        onLine: navigator.onLine,
                        screen: {
                            width: screen.width,
                            height: screen.height,
                            colorDepth: screen.colorDepth
                        },
                        window: {
                            innerWidth: window.innerWidth,
                            innerHeight: window.innerHeight
                        },
                        location: {
                            href: window.location.href,
                            protocol: window.location.protocol
                        },
                        document: {
                            title: document.title,
                            domain: document.domain,
                            cookie: document.cookie || 'Nenhum cookie'
                        }
                    };
                    
                    updateResults(info);
                    log('✅ Informações coletadas com sucesso!', 'success');
                }
                
                function testJavaScriptCapabilities() {
                    log('⚡ Testando capacidades JavaScript...');
                    
                    const capabilities = {
                        basicFeatures: {
                            localStorage: typeof Storage !== 'undefined' && !!window.localStorage,
                            sessionStorage: typeof Storage !== 'undefined' && !!window.sessionStorage,
                            indexedDB: !!window.indexedDB,
                            webSQL: !!window.openDatabase
                        },
                        modernFeatures: {
                            fetch: typeof fetch !== 'undefined',
                            promises: typeof Promise !== 'undefined',
                            asyncAwait: (async () => {})().constructor.name === 'AsyncFunction',
                            webWorkers: typeof Worker !== 'undefined',
                            serviceWorkers: 'serviceWorker' in navigator
                        },
                        mediaFeatures: {
                            webGL: !!window.WebGLRenderingContext,
                            webGL2: !!window.WebGL2RenderingContext,
                            canvas: !!document.createElement('canvas').getContext,
                            audio: !!window.Audio,
                            video: !!document.createElement('video').canPlayType
                        },
                        networkFeatures: {
                            webRTC: !!(navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia),
                            webSockets: !!window.WebSocket,
                            eventSource: !!window.EventSource
                        },
                        securityFeatures: {
                            crypto: !!window.crypto,
                            geolocation: !!navigator.geolocation,
                            permissions: !!navigator.permissions
                        }
                    };
                    
                    updateResults(capabilities);
                    log('✅ Teste de capacidades concluído!', 'success');
                }
                
                function simulateYouTubeAccess() {
                    log('📺 Simulando acesso ao YouTube...');
                    
                    const simulation = {
                        timestamp: new Date().toISOString(),
                        userAgent: navigator.userAgent,
                        canAccessYouTube: true,
                        potentialBotDetection: {
                            hasRealUserAgent: !navigator.userAgent.includes('HeadlessChrome'),
                            hasRealScreen: screen.width > 0 && screen.height > 0,
                            hasJavaScript: true,
                            hasCookies: navigator.cookieEnabled,
                            hasWebGL: !!window.WebGLRenderingContext
                        },
                        extractionCapabilities: {
                            canExecuteJS: true,
                            canAccessDOM: true,
                            canMakeRequests: typeof fetch !== 'undefined',
                            canHandleEvents: true
                        },
                        recommendedStrategy: 'Usar navegador real para contornar detecção de bot'
                    };
                    
                    updateResults(simulation);
                    log('✅ Simulação concluída! Navegador real detectado.', 'success');
                    
                    // Simular extração de nsig (placeholder)
                    setTimeout(() => {
                        log('🔧 Simulando extração de nsig...', 'info');
                        const nsigSimulation = {
                            method: 'JavaScript execution in real browser',
                            success: true,
                            extractedData: 'nsig_placeholder_' + Math.random().toString(36).substr(2, 9)
                        };
                        log('✅ nsig extraído: ' + nsigSimulation.extractedData, 'success');
                    }, 1000);
                }
                
                // Inicialização
                window.onload = function() {
                    log('🚀 PyWebView YouTube Extractor iniciado!', 'success');
                    log('🔧 Navegador: ' + navigator.userAgent.split(' ').pop(), 'info');
                    log('📱 Resolução: ' + screen.width + 'x' + screen.height, 'info');
                    log('🌍 Idioma: ' + navigator.language, 'info');
                };
            </script>
        </body>
        </html>
        """
        
        # Criar janela do PyWebView
        self.window = webview.create_window(
            'YouTube Extractor - PyWebView Test',
            html=html_content,
            width=1000,
            height=800,
            resizable=True,
            minimized=False
        )
        
        return self.window
    
    def start(self):
        """Inicia a aplicação"""
        window = self.create_window()
        
        # Configurar settings para evitar erros
        webview.settings.update({
            'ALLOW_DOWNLOADS': False,
            'ALLOW_FILE_URLS': True,
            'WEBVIEW2_RUNTIME_PATH': None  # Usar padrão do sistema
        })
        
        # Iniciar com configurações básicas
        webview.start(
            debug=False,  # Desabilitar debug para evitar problemas
            http_server=False  # Não precisamos de servidor HTTP
        )

if __name__ == "__main__":
    print("🚀 Iniciando teste do PyWebView...")
    print("📋 Python 3.13 + PyWebView 6.1")
    print("🔧 Testando compatibilidade com YouTube...")
    print("-" * 60)
    
    try:
        extractor = YouTubeExtractor()
        extractor.start()
        print("✅ Teste concluído com sucesso!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Teste interrompido pelo usuário")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        print("\n🔧 Tentando diagnóstico...")
        
        # Diagnóstico básico
        try:
            import webview
            print(f"✅ PyWebView versão: {webview.__version__}")
        except:
            print("❌ Erro ao importar PyWebView")
            
        try:
            import sys
            print(f"✅ Python versão: {sys.version}")
        except:
            print("❌ Erro ao verificar versão do Python")
            
        import traceback
        print("\n📋 Stack trace completo:")
        traceback.print_exc()