# 🎬 Video Converter

[![CI/CD Pipeline](https://github.com/renejr/videoconverter/actions/workflows/ci.yml/badge.svg)](https://github.com/renejr/videoconverter/actions/workflows/ci.yml)
[![CodeQL](https://github.com/renejr/videoconverter/actions/workflows/codeql.yml/badge.svg)](https://github.com/renejr/videoconverter/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/renejr/videoconverter)
[![Release](https://img.shields.io/github/v/release/renejr/videoconverter)](https://github.com/renejr/videoconverter/releases)
[![Downloads](https://img.shields.io/github/downloads/renejr/videoconverter/total)](https://github.com/renejr/videoconverter/releases)
[![Issues](https://img.shields.io/github/issues/renejr/videoconverter)](https://github.com/renejr/videoconverter/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/renejr/videoconverter)](https://github.com/renejr/videoconverter/pulls)
[![Code Size](https://img.shields.io/github/languages/code-size/renejr/videoconverter)](https://github.com/renejr/videoconverter)
[![Last Commit](https://img.shields.io/github/last-commit/renejr/videoconverter)](https://github.com/renejr/videoconverter/commits/main)

Um conversor de vídeo moderno e eficiente com interface gráfica intuitiva, suporte completo para **aceleração CUDA/NVENC** e **sistema avançado de modos de performance**.

## 🚀 Características Principais

### 🎯 **Modos de Performance Inteligentes**
- **ECONÔMICA**: Otimizada para economia de recursos e menor consumo de energia
- **AUTOMÁTICA**: Detecção automática de hardware com configuração inteligente
- **PERFORMANCE**: Máxima velocidade utilizando todos os recursos disponíveis

### 🔄 **Sistema de Fila Avançado**
- **Conversão em Lote**: Processe múltiplos arquivos simultaneamente
- **Controle de Concorrência**: Gerenciamento inteligente de recursos do sistema
- **Monitoramento em Tempo Real**: Acompanhe o progresso de cada conversão
- **Recuperação de Erros**: Sistema robusto de tratamento de falhas

### 💻 **Interface e Usabilidade**
- **Interface Gráfica Moderna**: Design intuitivo e responsivo com Tkinter
- **Tooltips Informativos**: Ajuda contextual para cada funcionalidade
- **Validação de Estados**: Controle inteligente de botões e ações
- **Feedback Visual**: Indicadores claros de progresso e status

### ⚡ **Performance e Hardware**
- **Aceleração CUDA/NVENC**: Suporte completo para GPUs NVIDIA
- **Detecção Automática**: Identifica automaticamente hardware disponível
- **Fallback Inteligente**: Usa CPU automaticamente quando GPU não disponível
- **Otimização Adaptativa**: Ajusta configurações baseado no hardware detectado

### 🛠️ **Funcionalidades Técnicas**
- **Múltiplos Formatos**: Suporte extensivo para formatos de entrada e saída
- **Instalação Automática**: FFmpeg instalado automaticamente se necessário
- **Configurações Avançadas**: Controle total sobre qualidade, FPS e resolução
- **Sistema de Log**: Logging detalhado para debugging e monitoramento
- **Validação Robusta**: Verificação automática de arquivos e configurações

## 📋 Requisitos

### Requisitos Mínimos
- Python 3.7 ou superior
- Windows 10/11 (testado)
- Conexão com internet (para instalação automática do FFmpeg)

### Para Aceleração CUDA (Opcional)
- GPU NVIDIA compatível com CUDA
- Drivers NVIDIA atualizados
- CUDA Toolkit (instalado automaticamente com drivers modernos)

## 🚀 Autoinstalação (Recomendado)

O VideoConverter inclui um **instalador automático inteligente** que configura todo o ambiente necessário automaticamente, incluindo Python 3.13, CUDA (se compatível), FFmpeg e todas as dependências.

### ✨ Características do Instalador
- **🎯 Detecção automática** do sistema operacional e hardware
- **🖥️ Suporte multi-plataforma**: Windows, Linux e macOS
- **🔧 Instalação seletiva** apenas do que é necessário
- **📊 Interface avançada** com progress bars e output colorido
- **🛡️ Verificação de integridade** de todos os componentes
- **💾 Cache inteligente** para downloads
- **📝 Relatórios detalhados** de instalação

### 🚀 Início Rápido com Autoinstalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/renejr/videoconverter.git
   cd videoconverter
   ```

2. **Execute o instalador automático:**
   ```bash
   # Modo interativo (recomendado para primeira instalação)
   cd installer
   python main_installer.py
   
   # Ou modo automático (instalação silenciosa)
   python main_installer.py --auto
   ```

3. **O instalador irá automaticamente:**
   - ✅ Detectar seu sistema operacional e hardware
   - ✅ Instalar Python 3.13 (se necessário)
   - ✅ Detectar GPU NVIDIA e instalar CUDA compatível
   - ✅ Baixar e configurar FFmpeg/FFprobe
   - ✅ Instalar todas as dependências Python
   - ✅ Validar a instalação com testes automáticos
   - ✅ Gerar relatório detalhado da instalação

4. **Execute a aplicação:**
   ```bash
   python main_tkinter.py
   ```

### 🔧 Opções Avançadas do Instalador

```bash
# Instalação com configuração personalizada
python main_installer.py --config config.json

# Modo offline (usa cache local)
python main_installer.py --offline

# Apenas validar instalação existente
python main_installer.py --validate-only

# Gerar relatório detalhado
python main_installer.py --auto --report relatorio.txt
```

### 📊 Componentes Gerenciados pelo Instalador
- 🐍 **Python 3.13** - Instalação e configuração automática
- 🚀 **NVIDIA CUDA** - Detecção de GPU e instalação compatível (versões 11.8-12.6)
- 🎬 **FFmpeg/FFprobe** - Download e configuração de PATH
- 📦 **Dependências** - Instalação automática de todas as bibliotecas Python
- 🔧 **Configuração** - Setup automático de variáveis de ambiente

## 🛠️ Instalação Manual (Alternativa)

> **💡 Dica:** Recomendamos usar o [instalador automático](#-autoinstalação-recomendado) acima, que configura tudo automaticamente. Use a instalação manual apenas se preferir controle total sobre o processo.

### Pré-requisitos para Instalação Manual
- Python 3.7+ já instalado e configurado
- FFmpeg instalado e no PATH do sistema
- CUDA Toolkit (opcional, para aceleração GPU)

### Passos da Instalação Manual

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/renejr/videoconverter.git
   cd videoconverter
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure FFmpeg (se não estiver instalado):**
   ```bash
   # Windows: Baixe de https://ffmpeg.org/ e adicione ao PATH
   # Linux: sudo apt install ffmpeg (Ubuntu/Debian)
   # macOS: brew install ffmpeg
   ```

4. **Execute a aplicação:**
   ```bash
   python main_tkinter.py
   ```

### Verificação da Instalação Manual
```bash
# Teste se tudo está funcionando
python test_complete.py

# Verifique detecção de hardware CUDA
python debug_hardware.py
```

## 📦 Dependências

- `requests>=2.31.0` - Requisições HTTP para download do FFmpeg
- `tkinter` - Interface gráfica (incluído no Python padrão)
- `subprocess` - Execução de processos FFmpeg (biblioteca padrão)
- `threading` - Processamento assíncrono (biblioteca padrão)

**Nota**: FFmpeg é baixado automaticamente pela aplicação

## 🎯 Como Usar

### 1. Seleção de Arquivo
- Clique em "Procurar" para selecionar o arquivo de vídeo de entrada
- Formatos suportados: MP4, AVI, MOV, MKV, WMV, FLV, WEBM, M4V, 3GP, ASF, RM, RMVB, VOB, TS, MTS, M2TS
- **Novo**: Suporte para seleção múltipla de arquivos para conversão em lote

### 2. Modo de Performance
Escolha o modo que melhor se adapta às suas necessidades:

#### 🟢 **ECONÔMICA**
- **Ideal para**: Laptops, sistemas com recursos limitados
- **Características**: Menor uso de CPU/GPU, economia de energia
- **Velocidade**: Mais lenta, mas eficiente em recursos
- **Configuração**: 1-2 threads, configurações conservadoras

#### 🔵 **AUTOMÁTICA** (Recomendado)
- **Ideal para**: Uso geral, detecção automática
- **Características**: Balanceamento inteligente entre velocidade e recursos
- **Velocidade**: Otimizada baseada no hardware detectado
- **Configuração**: Ajuste automático baseado no sistema

#### 🔴 **PERFORMANCE**
- **Ideal para**: Workstations, sistemas potentes
- **Características**: Máxima velocidade, uso intensivo de recursos
- **Velocidade**: Mais rápida possível
- **Configuração**: Múltiplas threads, aceleração máxima

### 3. Configurações de Conversão

#### Formato de Saída
Escolha entre os formatos disponíveis:
- MP4 (recomendado para compatibilidade)
- AVI (boa qualidade)
- MOV (Apple)
- MKV (código aberto)
- WMV (Windows)
- FLV (web)
- WEBM (web)
- M4V (iTunes)

#### Qualidade
- **Alta**: Melhor qualidade, arquivo maior
- **Média**: Equilíbrio entre qualidade e tamanho
- **Baixa**: Menor qualidade, arquivo menor
- **Lossless**: Sem perda de qualidade (arquivo muito grande)

#### FPS (Frames por Segundo)
- Opções predefinidas: 24, 25, 30, 50, 60 FPS
- Opção "Personalizado" para valores específicos
- "Manter Original" preserva o FPS do arquivo original

#### Resolução
- Presets comuns: 480p, 720p, 1080p, 1440p, 4K
- Opção "Personalizada" para dimensões específicas
- "Manter Original" preserva a resolução original

#### Transparência
- Marque esta opção para preservar canais alfa (apenas para formatos compatíveis)

### 3. Diretório de Saída
- Clique em "Procurar" para escolher onde salvar o arquivo convertido
- O nome do arquivo será gerado automaticamente baseado no arquivo original

### 4. Conversão
- Clique em "Converter" para iniciar o processo
- Acompanhe o progresso na barra de progresso
- Veja detalhes no log na parte inferior da janela
- Use "Cancelar" para interromper a conversão se necessário

## 🔧 Estrutura do Projeto

```
videoconverter/
├── installer/              # 🚀 Sistema de Autoinstalação
│   ├── core/              # Módulos de detecção e instalação
│   │   ├── os_detector.py # Detecção de sistema operacional
│   │   ├── python_manager.py # Gerenciamento Python 3.13
│   │   ├── gpu_detector.py # Detecção GPU/CUDA
│   │   ├── cuda_installer.py # Instalação CUDA automática
│   │   └── ffmpeg_manager.py # Gerenciamento FFmpeg
│   ├── utils/             # Utilitários do instalador
│   │   ├── downloader.py  # Download inteligente com cache
│   │   ├── progress.py    # Progress bars avançadas
│   │   └── logger.py      # Sistema de logging
│   ├── config/            # Configurações do instalador
│   │   └── settings.py    # Configurações padrão
│   ├── main_installer.py  # 🎯 Instalador principal
│   ├── test_installer.py  # Suite de testes (28 testes)
│   └── README.md          # Documentação do instalador
├── core/                   # Módulos principais da aplicação
│   ├── ffmpeg_installer.py # Instalação automática do FFmpeg
│   ├── queue_manager.py    # Sistema de fila e gerenciamento de conversões
│   └── video_converter.py  # Motor de conversão com suporte CUDA
├── gui/                    # Interface gráfica
│   ├── main_window.py      # Interface PyQt6 (legacy)
│   └── main_window_tkinter.py # Interface Tkinter (atual)
├── utils/                  # Utilitários da aplicação
│   ├── config.py          # Configurações centralizadas
│   ├── hardware_detector.py # Detecção de hardware CUDA
│   ├── performance_modes.py # Modos de performance e configurações
│   └── validators.py      # Validação de entrada
├── main.py                # Arquivo principal (PyQt6)
├── main_tkinter.py        # 🎯 Arquivo principal da aplicação (Tkinter)
├── requirements.txt       # Dependências Python
├── .gitignore            # Arquivos ignorados pelo Git
└── README.md             # Este arquivo
```

## 🧪 Testes

Execute os testes para verificar se tudo está funcionando:

```bash
# Teste básico
python test_tkinter.py

# Teste completo
python test_complete.py
```

## ⚙️ Configurações Avançadas

### Formatos Suportados

**Entrada:**
- Vídeo: MP4, AVI, MOV, MKV, WMV, FLV, WEBM, M4V, 3GP, ASF, RM, RMVB, VOB, TS, MTS, M2TS

**Saída:**
- Vídeo: MP4, AVI, MOV, MKV, WMV, FLV, WEBM, M4V

### Presets de Qualidade

- **Alta**: CRF 18, alta taxa de bits
- **Média**: CRF 23, taxa de bits balanceada
- **Baixa**: CRF 28, taxa de bits reduzida
- **Lossless**: Sem compressão com perda

### Resolução Presets

- **480p**: 854x480
- **720p**: 1280x720
- **1080p**: 1920x1080
- **1440p**: 2560x1440
- **4K**: 3840x2160

## 🚀 Aceleração CUDA/NVENC

### Detecção Automática
A aplicação detecta automaticamente se você possui:
- GPU NVIDIA compatível
- Drivers atualizados
- Suporte CUDA disponível

### Codecs NVENC Suportados
- **H.264 (AVC)**: `h264_nvenc` - Melhor compatibilidade
- **H.265 (HEVC)**: `hevc_nvenc` - Melhor compressão
- **AV1**: `av1_nvenc` - Codec mais moderno (GPUs mais recentes)

### Benefícios da Aceleração
- **Velocidade**: Até 10x mais rápido que CPU
- **Eficiência**: Menor uso de CPU durante conversão
- **Qualidade**: Mantém qualidade com processamento otimizado
- **Fallback**: Automaticamente usa CPU se CUDA falhar

### Verificação de Suporte
Execute para verificar se CUDA está disponível:
```bash
python debug_hardware.py
```

## 🐛 Solução de Problemas

### Problemas com o Instalador Automático

#### Instalador não executa
```bash
# Verifique se Python está instalado
python --version

# Instale dependências do instalador
cd installer
pip install -r requirements.txt

# Execute com verbose para mais detalhes
python main_installer.py --verbose
```

#### Falha na detecção de sistema
```bash
# Execute validação para diagnóstico
python main_installer.py --validate-only --verbose

# Verifique logs detalhados
cat logs/installer.log
```

#### Problemas de permissão (Windows/Linux)
- Execute como administrador/sudo quando solicitado
- O instalador pedirá elevação automaticamente
- Verifique se tem permissões para instalar software

#### Falha no download de componentes
```bash
# Verifique conexão com internet
ping google.com

# Use modo offline se tiver cache
python main_installer.py --offline

# Configure proxy se necessário
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
```

### FFmpeg não encontrado
Se o instalador automático falhar ou você usar instalação manual:
1. Use o instalador automático: `cd installer && python main_installer.py`
2. Ou baixe manualmente de https://ffmpeg.org/
3. Adicione o executável ao PATH do sistema
4. Reinicie a aplicação

### Erro de conversão
- Verifique se o arquivo de entrada não está corrompido
- Certifique-se de que há espaço suficiente no disco
- Verifique se o arquivo não está sendo usado por outro programa

### Interface não abre
- Verifique se todas as dependências estão instaladas
- Execute `python test_complete.py` para diagnosticar problemas

### CUDA não funciona
- Verifique se você tem uma GPU NVIDIA
- Atualize os drivers NVIDIA para a versão mais recente
- Execute `python debug_hardware.py` para verificar detecção
- A aplicação usará CPU automaticamente se CUDA falhar

### Conversão lenta
- Se você tem GPU NVIDIA, verifique se CUDA está sendo usado
- Monitore o log para ver se está usando `nvenc` ou CPU
- Considere reduzir a resolução para melhor performance

## 📝 Log de Alterações

### v2.1.2 (Atual)
- **🎬 Correção Crítica GIF**: Resolvido problema de erro no FFmpeg com arquivos GIF contendo "(Animado)" no nome
- **🔧 Limpeza de Nomes**: Implementada limpeza automática de caracteres problemáticos em nomes de arquivos GIF
- **📁 Normalização de Extensões**: Conversão automática de ".GIF" maiúsculo para ".gif" minúsculo
- **🛠️ Robustez**: Melhorada estabilidade na conversão de arquivos GIF com nomes especiais
- **📊 Logging Aprimorado**: Adicionado log específico para correções de nomes de arquivos GIF

### v2.1.1
- **🔧 Correção NVENC**: Corrigido problema de incompatibilidade entre filtros de vídeo e NVENC
- **🎯 Mapeamento de Codec**: Implementado mapeamento automático de codec da interface (H.264/H.265) para formato interno
- **⚡ Otimização de Filtros**: Removido filtro `hwdownload,format=nv12` que causava conflitos entre CUDA e CPU
- **🛠️ Estabilidade**: Melhorada estabilidade da conversão NVENC com GPUs NVIDIA
- **📊 Compatibilidade**: Garantida compatibilidade entre interface gráfica e motor de conversão

### v2.1.0
- **🚀 Sistema de Autoinstalação**: Instalador automático inteligente completo
- **🎯 Detecção Multi-Plataforma**: Suporte Windows, Linux e macOS
- **🐍 Gerenciamento Python 3.13**: Instalação e configuração automática
- **💻 Detecção GPU/CUDA**: Identificação automática e instalação CUDA compatível
- **🎬 Gerenciamento FFmpeg**: Download e configuração automática
- **📊 Interface Avançada**: Progress bars, output colorido e relatórios detalhados
- **🛡️ Validação em 3 Níveis**: Básica, avançada e benchmark
- **💾 Cache Inteligente**: Sistema de cache para downloads e modo offline
- **🔧 Configuração Flexível**: Suporte a arquivos de configuração JSON
- **📝 Suite de Testes**: 28 testes automatizados com 100% de cobertura

### v2.0.0
- **🎯 Sistema de Modos de Performance**: ECONÔMICA, AUTOMÁTICA e PERFORMANCE
- **🔄 Gerenciador de Fila Avançado**: Conversão em lote com controle de concorrência
- **💻 Interface Aprimorada**: Tooltips informativos e validação de estados
- **⚡ Otimizações de Performance**: Configurações adaptativas baseadas no hardware
- **🛠️ Sistema de Callbacks**: Monitoramento em tempo real de progresso
- **🔧 Arquitetura Modular**: Separação clara entre lógica e interface
- **📊 Logging Avançado**: Sistema de log detalhado para debugging
- **🚀 Melhor Experiência do Usuário**: Feedback visual e controle intuitivo

### v1.0.0
- Interface gráfica com Tkinter
- **Suporte completo para aceleração CUDA/NVENC**
- **Detecção automática de hardware NVIDIA**
- Suporte a múltiplos formatos de vídeo
- Instalação automática do FFmpeg
- Sistema de validação robusto
- Barra de progresso em tempo real
- Sistema de log detalhado
- **Fallback automático CPU quando CUDA não disponível**
- **Otimizações de performance para conversão**

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- [FFmpeg](https://ffmpeg.org/) - Motor de conversão de vídeo
- [Python](https://python.org/) - Linguagem de programação
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - Interface gráfica

## 📞 Suporte

Se você encontrar problemas ou tiver sugestões:
1. Verifique a seção de [Solução de Problemas](#-solução-de-problemas)
2. Execute os testes para diagnosticar o problema
3. Abra uma issue no repositório com detalhes do erro

---

**Desenvolvido com ❤️ em Python**