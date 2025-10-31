# 🔨 Guia de Build do Executável

## 📋 Visão Geral

Este documento descreve como criar um executável standalone do VideoConverter usando PyInstaller.

## 🚀 Build Automático (Recomendado)

### Usando o Script Automatizado

```bash
python build_exe.py
```

O script `build_exe.py` executa automaticamente:

1. **Limpeza**: Remove diretórios `build/`, `dist/` e arquivos `.spec` antigos
2. **Verificação**: Confirma se todas as dependências estão instaladas
3. **Build**: Executa PyInstaller com configurações otimizadas
4. **Validação**: Testa o executável gerado
5. **Relatório**: Exibe informações sobre o arquivo final

### Características do Build Automático

- ✅ **Configuração Otimizada**: Inclui todos os módulos necessários
- ✅ **Limpeza Automática**: Remove builds anteriores
- ✅ **Validação Integrada**: Testa o executável após criação
- ✅ **Logs Detalhados**: Acompanhe todo o processo
- ✅ **Tratamento de Erros**: Identifica e reporta problemas

## 🔧 Build Manual

### Pré-requisitos

```bash
pip install pyinstaller
```

### Comando Manual

```bash
pyinstaller VideoConverter.spec
```

## 📁 Estrutura do Arquivo .spec

O arquivo `VideoConverter.spec` contém configurações específicas:

### Seção Analysis
```python
a = Analysis(
    ['main_tkinter.py'],  # Arquivo principal
    pathex=[],
    binaries=[],
    datas=[
        ('gui', 'gui'),                           # Interface gráfica
        ('video_converter_module', 'video_converter_module'),  # Módulo principal
        ('installer', 'installer'),               # Sistema de instalação
        ('version.py', '.'),                      # Arquivo de versão (CRÍTICO)
    ],
    hiddenimports=[
        # Módulos GUI
        'gui', 'gui.main_window_tkinter', 'gui.main_window',
        # Módulos tkinter
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog',
        # Módulos do projeto
        'video_converter_module', 'installer',
        # Dependências críticas
        'version', 'platform', 'psutil', 'GPUtil', 'pynvml', 'wmi',
        # Processamento de imagem/vídeo
        'PIL', 'cv2', 'numpy',
        # Interface web
        'webview', 'rich', 'jinja2',
        # Banco de dados
        'alembic', 'sqlalchemy',
        # Autenticação
        'jose', 'passlib', 'pydantic_settings',
        # Rede
        'aiohttp', 'httpx', 'redis', 'asyncio',
        # Framework web
        'uvicorn', 'fastapi',
        # E-mail
        'smtplib', 'ssl', 'email',
        # Dependências yt-dlp
        'yt_dlp', 'certifi', 'urllib3', 'requests', 'websockets',
        'mutagen', 'pycryptodomex', 'brotli',
    ],
)
```

### Seção EXE
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VideoConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                    # Compressão UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # Sem console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

## 🐛 Solução de Problemas Comuns

### Erro: ModuleNotFoundError

**Problema**: Módulo não encontrado durante execução
```
ModuleNotFoundError: No module named 'module_name'
```

**Solução**: Adicionar módulo aos `hiddenimports`:
```python
hiddenimports=[
    'module_name',
    # ... outros módulos
]
```

### Erro: Arquivo não encontrado

**Problema**: Arquivo local não incluído no executável
```
FileNotFoundError: [Errno 2] No such file or directory: 'file.py'
```

**Solução**: Adicionar arquivo à seção `datas`:
```python
datas=[
    ('file.py', '.'),
    # ... outros arquivos
]
```

### Erro: Permission denied

**Problema**: Executável em uso durante build
```
PermissionError: [WinError 5] Access denied: 'dist\\VideoConverter.exe'
```

**Solução**: Finalizar processos e tentar novamente:
```bash
taskkill /f /im VideoConverter.exe
pyinstaller VideoConverter.spec
```

## 📊 Informações do Build

### Tamanho do Executável
- **Tamanho Final**: ~102MB
- **Inclui**: Todas as dependências Python, FFmpeg, bibliotecas de ML/CV

### Dependências Incluídas
- **Core**: Python 3.13, tkinter, pathlib
- **Conversão**: FFmpeg, yt-dlp, mutagen
- **ML/CV**: numpy, opencv, PIL
- **Web**: fastapi, aiohttp, webview
- **Banco**: sqlalchemy, redis
- **Autenticação**: jose, passlib
- **Sistema**: psutil, platform, wmi

## 🎯 Otimizações Aplicadas

### Compressão UPX
- Reduz tamanho do executável
- Mantém performance de execução

### Hiddenimports Completos
- Inclui todos os módulos necessários
- Evita erros de importação em runtime

### Datas Específicos
- Inclui arquivos locais do projeto
- Garante acesso a recursos necessários

## ✅ Validação do Build

### Testes Automáticos
O script `build_exe.py` executa:
1. Teste de inicialização
2. Verificação de módulos
3. Teste de interface
4. Validação de dependências

### Testes Manuais
```bash
# Testar execução
.\dist\VideoConverter.exe

# Verificar logs
# (verificar se não há erros de importação)
```

## 📝 Notas Importantes

### Módulos Críticos
- **version.py**: DEVE estar em `datas`, não apenas `hiddenimports`
- **gui/**: Diretório completo necessário para interface
- **video_converter_module/**: Core do aplicativo

### Plataforma
- Build testado no Windows 10
- Executável compatível com Windows 7+
- Requer Visual C++ Redistributable

### Performance
- Primeira execução pode ser mais lenta (extração)
- Execuções subsequentes são rápidas
- Uso de memória: ~200-500MB dependendo da operação

---

**Desenvolvido com ❤️ usando PyInstaller**