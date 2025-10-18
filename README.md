# Video Converter

Um conversor de vídeo simples e eficiente com interface gráfica, desenvolvido em Python usando Tkinter e FFmpeg.

## 🚀 Características

- **Interface Gráfica Intuitiva**: Interface moderna e fácil de usar desenvolvida com Tkinter
- **Aceleração por Hardware CUDA**: Suporte completo para NVENC (NVIDIA) com fallback automático para CPU
- **Detecção Automática de Hardware**: Identifica automaticamente GPUs NVIDIA compatíveis
- **Múltiplos Formatos**: Suporte para conversão entre diversos formatos de vídeo
- **Instalação Automática do FFmpeg**: Detecta e instala automaticamente o FFmpeg se necessário
- **Configurações Avançadas**: Controle de qualidade, FPS, resolução e transparência
- **Barra de Progresso**: Acompanhamento em tempo real do progresso da conversão
- **Validação de Entrada**: Verificação automática de arquivos e configurações
- **Log Detalhado**: Sistema de log para acompanhar o processo de conversão
- **Fallback Inteligente**: Automaticamente usa CPU se CUDA não estiver disponível

## 📋 Requisitos

### Requisitos Mínimos
- Python 3.7 ou superior
- Windows 10/11 (testado)
- Conexão com internet (para instalação automática do FFmpeg)

### Para Aceleração CUDA (Opcional)
- GPU NVIDIA compatível com CUDA
- Drivers NVIDIA atualizados
- CUDA Toolkit (instalado automaticamente com drivers modernos)

## 🛠️ Instalação

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd vidconv
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação:**
   ```bash
   python main_tkinter.py
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

### 2. Configurações de Conversão

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
vidconv/
├── core/                   # Módulos principais
│   ├── ffmpeg_installer.py # Instalação automática do FFmpeg
│   └── video_converter.py  # Motor de conversão com suporte CUDA
├── gui/                    # Interface gráfica
│   ├── main_window.py      # Interface PyQt6 (legacy)
│   └── main_window_tkinter.py # Interface Tkinter (atual)
├── utils/                  # Utilitários
│   ├── config.py          # Configurações centralizadas
│   ├── hardware_detector.py # Detecção de hardware CUDA
│   └── validators.py      # Validação de entrada
├── main.py                # Arquivo principal (PyQt6)
├── main_tkinter.py        # Arquivo principal da aplicação (Tkinter)
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

### FFmpeg não encontrado
A aplicação tentará instalar automaticamente o FFmpeg. Se falhar:
1. Baixe o FFmpeg manualmente de https://ffmpeg.org/
2. Adicione o executável ao PATH do sistema
3. Reinicie a aplicação

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