# 🎵 Guia Completo de Extração de Áudio

Este guia detalha como usar a nova funcionalidade de extração de áudio do Video Converter para extrair trilhas sonoras de seus vídeos em diversos formatos de alta qualidade.

## 📋 Índice

1. [Visão Geral](#-visão-geral)
2. [Como Usar](#-como-usar)
3. [Formatos Suportados](#-formatos-suportados)
4. [Configurações de Qualidade](#-configurações-de-qualidade)
5. [Opções Avançadas](#-opções-avançadas)
6. [Exemplos Práticos](#-exemplos-práticos)
7. [Solução de Problemas](#-solução-de-problemas)
8. [Dicas e Melhores Práticas](#-dicas-e-melhores-práticas)

## 🎯 Visão Geral

A funcionalidade de extração de áudio permite converter qualquer arquivo de vídeo em um arquivo de áudio puro, mantendo a qualidade original ou aplicando configurações específicas conforme suas necessidades.

### ✨ Principais Características

- **8 Formatos de Áudio**: Suporte completo para MP3, AAC, WAV, FLAC, OGG, M4A, WMA e OPUS
- **4 Níveis de Qualidade**: Configurações otimizadas para cada formato
- **Preservação de Metadados**: Mantém informações como título, artista, álbum
- **Capa de Álbum**: Preserva artwork quando suportado
- **Interface Intuitiva**: Controles que aparecem dinamicamente

## 🚀 Como Usar

### Passo 1: Selecionar Arquivo de Vídeo
1. Clique no botão **"Procurar"** na seção "Arquivo de Entrada"
2. Selecione o arquivo de vídeo que contém o áudio que deseja extrair
3. Formatos suportados: MP4, AVI, MOV, MKV, WMV, FLV, WEBM, M4V, 3GP, etc.

### Passo 2: Escolher Extração de Áudio
1. Na seção "Configurações de Conversão", clique no dropdown **"Formato"**
2. Selecione **"Extração de Áudio"**
3. Automaticamente, novas opções aparecerão na interface

### Passo 3: Configurar Formato de Áudio
1. No dropdown **"Formato de Áudio"**, escolha o formato desejado:
   - **MP3**: Para compatibilidade universal
   - **FLAC**: Para qualidade sem perda
   - **WAV**: Para máxima qualidade sem compressão
   - **AAC**: Para dispositivos Apple
   - Outros formatos conforme necessidade

### Passo 4: Ajustar Qualidade
1. No dropdown **"Qualidade"**, selecione o nível desejado:
   - **Baixa**: Arquivos menores, qualidade reduzida
   - **Média**: Equilíbrio recomendado
   - **Alta**: Melhor qualidade, arquivos maiores
   - **Muito Alta**: Máxima qualidade disponível

### Passo 5: Configurar Opções Avançadas
1. **Preservar Metadados**: Marque para manter informações do arquivo original
2. **Preservar Capa do Álbum**: Marque para incluir artwork (quando suportado)

### Passo 6: Definir Destino e Converter
1. Clique em **"Procurar"** na seção "Diretório de Saída"
2. Escolha onde salvar o arquivo de áudio
3. Clique em **"Converter"** para iniciar o processo

## 🎼 Formatos Suportados

### MP3 (Recomendado para Uso Geral)
- **Codec**: libmp3lame
- **Extensão**: .mp3
- **Compatibilidade**: Universal
- **Metadados**: ✅ Suportado
- **Capa de Álbum**: ✅ Suportado
- **Uso Ideal**: Música, podcasts, compatibilidade máxima

### AAC (Apple/Dispositivos Móveis)
- **Codec**: aac
- **Extensão**: .aac
- **Compatibilidade**: Excelente em dispositivos Apple
- **Metadados**: ✅ Suportado
- **Capa de Álbum**: ❌ Não suportado
- **Uso Ideal**: iPhone, iPad, iTunes

### WAV (Máxima Qualidade)
- **Codec**: pcm_s16le
- **Extensão**: .wav
- **Compatibilidade**: Universal
- **Metadados**: ❌ Limitado
- **Capa de Álbum**: ❌ Não suportado
- **Uso Ideal**: Produção musical, edição profissional

### FLAC (Compressão Sem Perda)
- **Codec**: flac
- **Extensão**: .flac
- **Compatibilidade**: Boa (players modernos)
- **Metadados**: ✅ Suportado
- **Capa de Álbum**: ✅ Suportado
- **Uso Ideal**: Arquivamento, audiophiles

### OGG (Código Aberto)
- **Codec**: libvorbis
- **Extensão**: .ogg
- **Compatibilidade**: Boa (software livre)
- **Metadados**: ✅ Suportado
- **Capa de Álbum**: ✅ Suportado
- **Uso Ideal**: Jogos, aplicações open source

### M4A (iTunes/Apple)
- **Codec**: aac
- **Extensão**: .m4a
- **Compatibilidade**: Excelente em ecossistema Apple
- **Metadados**: ✅ Suportado
- **Capa de Álbum**: ✅ Suportado
- **Uso Ideal**: iTunes, dispositivos Apple

### WMA (Windows Media)
- **Codec**: wmav2
- **Extensão**: .wma
- **Compatibilidade**: Boa no Windows
- **Metadados**: ✅ Suportado
- **Capa de Álbum**: ❌ Não suportado
- **Uso Ideal**: Ambiente Windows

### OPUS (Moderno/Streaming)
- **Codec**: libopus
- **Extensão**: .opus
- **Compatibilidade**: Crescente
- **Metadados**: ✅ Suportado
- **Capa de Álbum**: ❌ Não suportado
- **Uso Ideal**: Streaming, VoIP, aplicações modernas

## ⚙️ Configurações de Qualidade

### Configurações por Formato

#### MP3
- **Baixa**: 128k bitrate, qualidade VBR 4
- **Média**: 192k bitrate, qualidade VBR 2 (recomendado)
- **Alta**: 256k bitrate, qualidade VBR 0
- **Muito Alta**: 320k bitrate, qualidade VBR 0

#### AAC
- **Baixa**: 128k bitrate, perfil aac_low
- **Média**: 192k bitrate, perfil aac_low (recomendado)
- **Alta**: 256k bitrate, perfil aac_low
- **Muito Alta**: 320k bitrate, perfil aac_low

#### WAV
- **Baixa**: 22050 Hz, 16-bit
- **Média**: 44100 Hz, 16-bit (CD quality)
- **Alta**: 48000 Hz, 24-bit
- **Muito Alta**: 96000 Hz, 24-bit

#### FLAC
- **Baixa**: Compressão 0, 44100 Hz
- **Média**: Compressão 5, 44100 Hz (recomendado)
- **Alta**: Compressão 8, 48000 Hz
- **Muito Alta**: Compressão 12, 96000 Hz

## 🔧 Opções Avançadas

### Preservar Metadados
Quando ativada, esta opção mantém informações como:
- **Título** da faixa
- **Artista** principal
- **Álbum** de origem
- **Ano** de lançamento
- **Gênero** musical
- **Número da faixa**
- **Comentários**

**Formatos que suportam metadados**: MP3, AAC, FLAC, OGG, M4A, WMA, OPUS

### Preservar Capa do Álbum
Quando ativada e suportada pelo formato, inclui:
- **Artwork** embutido no arquivo de áudio
- **Compatibilidade** com players que exibem capas
- **Tamanho otimizado** da imagem

**Formatos que suportam capa**: MP3, FLAC, OGG, M4A

## 📚 Exemplos Práticos

### Exemplo 1: Extrair Música de Vídeo Musical (MP3)
```
Arquivo de Entrada: video_musical.mp4
Formato: Extração de Áudio
Formato de Áudio: MP3
Qualidade: Média (192k)
Preservar Metadados: ✅ Ativado
Preservar Capa: ✅ Ativado
Resultado: video_musical.mp3 (compatível universalmente)
```

### Exemplo 2: Arquivar Áudio de Documentário (FLAC)
```
Arquivo de Entrada: documentario.mkv
Formato: Extração de Áudio
Formato de Áudio: FLAC
Qualidade: Alta (compressão 8)
Preservar Metadados: ✅ Ativado
Resultado: documentario.flac (qualidade sem perda)
```

### Exemplo 3: Podcast para iPhone (M4A)
```
Arquivo de Entrada: podcast_video.mp4
Formato: Extração de Áudio
Formato de Áudio: M4A
Qualidade: Média (192k)
Preservar Metadados: ✅ Ativado
Preservar Capa: ✅ Ativado
Resultado: podcast_video.m4a (otimizado para Apple)
```

### Exemplo 4: Edição Profissional (WAV)
```
Arquivo de Entrada: gravacao_estudio.mov
Formato: Extração de Áudio
Formato de Áudio: WAV
Qualidade: Muito Alta (96kHz, 24-bit)
Preservar Metadados: ❌ Desativado (não suportado)
Resultado: gravacao_estudio.wav (qualidade máxima)
```

## 🛠️ Solução de Problemas

### Problema: "Arquivo não contém áudio"
**Causa**: O vídeo selecionado não possui trilha de áudio
**Solução**: 
- Verifique se o vídeo realmente tem áudio
- Teste com outro arquivo de vídeo
- Use um player de mídia para confirmar presença de áudio

### Problema: "Erro na conversão de áudio"
**Causa**: Formato ou configuração incompatível
**Solução**:
- Tente um formato mais simples (MP3)
- Reduza a qualidade para "Média"
- Verifique se há espaço suficiente no disco

### Problema: "Metadados não preservados"
**Causa**: Formato de destino não suporta metadados
**Solução**:
- Use MP3, FLAC, OGG, M4A ou WMA
- Evite WAV para preservar metadados

### Problema: "Capa do álbum não incluída"
**Causa**: Formato não suporta artwork embutido
**Solução**:
- Use MP3, FLAC, OGG ou M4A
- Evite AAC, WAV, WMA, OPUS

### Problema: "Arquivo muito grande"
**Causa**: Qualidade muito alta ou formato sem compressão
**Solução**:
- Reduza a qualidade para "Média" ou "Baixa"
- Use MP3 ou AAC em vez de WAV
- Para FLAC, use compressão maior (nível 8-12)

## 💡 Dicas e Melhores Práticas

### Escolha do Formato
- **Para uso geral**: MP3 com qualidade "Média"
- **Para dispositivos Apple**: M4A com qualidade "Média"
- **Para arquivamento**: FLAC com qualidade "Alta"
- **Para edição profissional**: WAV com qualidade "Muito Alta"
- **Para streaming/web**: OPUS com qualidade "Média"

### Configurações Recomendadas
- **Música**: MP3 192k ou M4A 192k
- **Podcasts/Fala**: MP3 128k ou AAC 128k
- **Arquivamento**: FLAC compressão 5-8
- **Produção**: WAV 48kHz/24-bit

### Otimização de Tamanho
1. Use MP3 ou AAC para menor tamanho
2. Qualidade "Baixa" ou "Média" para economizar espaço
3. Evite WAV para arquivos grandes
4. FLAC oferece compressão sem perda

### Compatibilidade Máxima
1. MP3 é o formato mais compatível
2. AAC funciona bem em dispositivos móveis
3. WAV é universal mas gera arquivos grandes
4. Teste a compatibilidade antes de conversões em lote

### Performance
- Extração de áudio é mais rápida que conversão de vídeo
- Qualidades mais altas demoram mais para processar
- WAV é o mais rápido (sem compressão)
- FLAC com compressão alta demora mais

## 📊 Comparação de Formatos

| Formato | Tamanho | Qualidade | Compatibilidade | Metadados | Capa |
|---------|---------|-----------|------------------|-----------|------|
| MP3     | Médio   | Boa       | Excelente        | ✅        | ✅   |
| AAC     | Médio   | Boa       | Boa              | ✅        | ❌   |
| WAV     | Grande  | Excelente | Excelente        | ❌        | ❌   |
| FLAC    | Grande  | Excelente | Boa              | ✅        | ✅   |
| OGG     | Médio   | Boa       | Média            | ✅        | ✅   |
| M4A     | Médio   | Boa       | Boa (Apple)      | ✅        | ✅   |
| WMA     | Médio   | Boa       | Boa (Windows)    | ✅        | ❌   |
| OPUS    | Pequeno | Excelente | Crescente        | ✅        | ❌   |

---

**💡 Dica Final**: Para a maioria dos casos, recomendamos **MP3 com qualidade "Média"** - oferece o melhor equilíbrio entre qualidade, tamanho e compatibilidade universal.

**🎵 Aproveite sua nova funcionalidade de extração de áudio!**