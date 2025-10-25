#!/bin/bash
# =========================================================
# SCRIPT DE AVALIAÇÃO DE SERVIDOR PARA PROJETO VOD
# =========================================================
# Este script avalia se o servidor Debian atende aos requisitos
# mínimos para o projeto VidConv (Video-on-Demand)
# Execução: bash server_assessment.sh
# =========================================================

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Criar diretório para resultados
RESULTS_DIR="/tmp/vidconv_assessment"
mkdir -p $RESULTS_DIR

# Arquivo de log
LOG_FILE="$RESULTS_DIR/assessment_results.log"
SUMMARY_FILE="$RESULTS_DIR/summary.txt"

# Limpar arquivos anteriores
rm -f $LOG_FILE $SUMMARY_FILE

# Função para log
log() {
  echo -e "$1" | tee -a $LOG_FILE
}

# Função para adicionar ao sumário
add_to_summary() {
  echo -e "$1" >> $SUMMARY_FILE
}

# Banner
log "${BLUE}============================================================${NC}"
log "${BLUE}      AVALIAÇÃO DE SERVIDOR PARA PROJETO VIDCONV           ${NC}"
log "${BLUE}============================================================${NC}"
log "Data: $(date)"
log "Hostname: $(hostname)"
log ""

# =========================================================
# 1. VERIFICAÇÃO DE HARDWARE
# =========================================================
log "${YELLOW}[1/5] Verificando especificações de hardware...${NC}"

# CPU
CPU_MODEL=$(cat /proc/cpuinfo | grep "model name" | head -1 | cut -d ":" -f2 | sed 's/^[ \t]*//')
CPU_CORES=$(nproc)
CPU_ARCH=$(uname -m)
CPU_AVX=$(grep -o 'avx\|avx2' /proc/cpuinfo | sort | uniq | tr '\n' ' ')
CPU_SSE=$(grep -o 'sse4_1\|sse4_2' /proc/cpuinfo | sort | uniq | tr '\n' ' ')

log "CPU: $CPU_MODEL"
log "Cores: $CPU_CORES"
log "Arquitetura: $CPU_ARCH"
log "Instruções AVX: $CPU_AVX"
log "Instruções SSE4: $CPU_SSE"

# Avaliação de CPU
if [ "$CPU_CORES" -ge 8 ]; then
  CPU_RATING="${GREEN}EXCELENTE${NC} ($CPU_CORES cores)"
  CPU_SCORE=3
elif [ "$CPU_CORES" -ge 4 ]; then
  CPU_RATING="${GREEN}BOM${NC} ($CPU_CORES cores)"
  CPU_SCORE=2
else
  CPU_RATING="${RED}INSUFICIENTE${NC} ($CPU_CORES cores, mínimo recomendado: 4)"
  CPU_SCORE=0
fi

# Verificar suporte a instruções
if [[ "$CPU_AVX" == *"avx"* ]] || [[ "$CPU_SSE" == *"sse4"* ]]; then
  INSTRUCTION_RATING="${GREEN}BOM${NC} (Suporte a $CPU_AVX $CPU_SSE)"
  INSTRUCTION_SCORE=1
else
  INSTRUCTION_RATING="${YELLOW}LIMITADO${NC} (Sem suporte a AVX/SSE4)"
  INSTRUCTION_SCORE=0
fi

# Memória
MEM_TOTAL=$(free -m | grep "Mem:" | awk '{print $2}')
MEM_TOTAL_GB=$(echo "scale=1; $MEM_TOTAL/1024" | bc)

log "Memória Total: ${MEM_TOTAL_GB}GB"

# Avaliação de memória
if (( $(echo "$MEM_TOTAL_GB >= 16" | bc -l) )); then
  MEM_RATING="${GREEN}EXCELENTE${NC} (${MEM_TOTAL_GB}GB)"
  MEM_SCORE=3
elif (( $(echo "$MEM_TOTAL_GB >= 8" | bc -l) )); then
  MEM_RATING="${GREEN}BOM${NC} (${MEM_TOTAL_GB}GB)"
  MEM_SCORE=2
elif (( $(echo "$MEM_TOTAL_GB >= 4" | bc -l) )); then
  MEM_RATING="${YELLOW}LIMITADO${NC} (${MEM_TOTAL_GB}GB, recomendado: 8GB+)"
  MEM_SCORE=1
else
  MEM_RATING="${RED}INSUFICIENTE${NC} (${MEM_TOTAL_GB}GB, mínimo: 4GB)"
  MEM_SCORE=0
fi

# Armazenamento
DISK_TOTAL=$(df -h / | awk 'NR==2 {print $2}')
DISK_AVAIL=$(df -h / | awk 'NR==2 {print $4}')
DISK_AVAIL_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')

# Verificar tipo de disco (rotacional = HDD, não rotacional = SSD)
if [ -e "/sys/block/sda/queue/rotational" ]; then
  IS_SSD=$(cat /sys/block/sda/queue/rotational)
  if [ "$IS_SSD" -eq 0 ]; then
    DISK_TYPE="SSD"
  else
    DISK_TYPE="HDD"
  fi
else
  DISK_TYPE="Não determinado"
fi

log "Armazenamento Total: $DISK_TOTAL"
log "Armazenamento Disponível: $DISK_AVAIL"
log "Tipo de Disco: $DISK_TYPE"

# Avaliação de armazenamento
if [ "$DISK_AVAIL_GB" -ge 100 ]; then
  if [ "$DISK_TYPE" == "SSD" ]; then
    DISK_RATING="${GREEN}EXCELENTE${NC} ($DISK_AVAIL disponível em SSD)"
    DISK_SCORE=3
  else
    DISK_RATING="${GREEN}BOM${NC} ($DISK_AVAIL disponível em HDD)"
    DISK_SCORE=2
  fi
elif [ "$DISK_AVAIL_GB" -ge 50 ]; then
  if [ "$DISK_TYPE" == "SSD" ]; then
    DISK_RATING="${GREEN}BOM${NC} ($DISK_AVAIL disponível em SSD)"
    DISK_SCORE=2
  else
    DISK_RATING="${YELLOW}LIMITADO${NC} ($DISK_AVAIL disponível em HDD)"
    DISK_SCORE=1
  fi
else
  DISK_RATING="${RED}INSUFICIENTE${NC} ($DISK_AVAIL disponível, mínimo: 50GB)"
  DISK_SCORE=0
fi

# Rede
# Obter a interface principal (excluindo loopback)
MAIN_INTERFACE=$(ip -o -4 route show to default | awk '{print $5}' | head -1)
if [ -z "$MAIN_INTERFACE" ]; then
  MAIN_INTERFACE="Interface não encontrada"
  NETWORK_SPEED="Desconhecida"
else
  # Tentar obter velocidade da interface
  if command -v ethtool >/dev/null 2>&1; then
    SPEED_INFO=$(ethtool $MAIN_INTERFACE 2>/dev/null | grep "Speed:")
    if [ -n "$SPEED_INFO" ]; then
      NETWORK_SPEED=$(echo $SPEED_INFO | awk '{print $2}')
    else
      NETWORK_SPEED="Não determinada"
    fi
  else
    NETWORK_SPEED="ethtool não instalado"
  fi
fi

log "Interface de Rede: $MAIN_INTERFACE"
log "Velocidade: $NETWORK_SPEED"

# Avaliação de rede
if [[ "$NETWORK_SPEED" == *"1000"* ]]; then
  NETWORK_RATING="${GREEN}EXCELENTE${NC} (Gigabit)"
  NETWORK_SCORE=3
elif [[ "$NETWORK_SPEED" == *"100"* ]]; then
  NETWORK_RATING="${GREEN}BOM${NC} (100Mbps)"
  NETWORK_SCORE=2
else
  # Se não conseguimos determinar, assumimos como OK
  NETWORK_RATING="${YELLOW}NÃO DETERMINADO${NC}"
  NETWORK_SCORE=1
fi

# =========================================================
# 2. TESTES DE PERFORMANCE
# =========================================================
log "\n${YELLOW}[2/5] Executando testes de performance básicos...${NC}"

# Teste de CPU - Cálculo de Pi (sem dependências externas)
log "Teste de CPU: Cálculo de Pi (10000 dígitos)..."
CPU_TEST_START=$(date +%s.%N)
echo "scale=10000; 4*a(1)" | bc -l > /dev/null 2>&1
CPU_TEST_END=$(date +%s.%N)
CPU_TEST_TIME=$(echo "$CPU_TEST_END - $CPU_TEST_START" | bc)
CPU_TEST_TIME=$(printf "%.2f" $CPU_TEST_TIME)
log "Tempo: ${CPU_TEST_TIME}s"

# Avaliação do teste de CPU
if (( $(echo "$CPU_TEST_TIME < 3" | bc -l) )); then
  CPU_PERF_RATING="${GREEN}EXCELENTE${NC} (${CPU_TEST_TIME}s)"
  CPU_PERF_SCORE=3
elif (( $(echo "$CPU_TEST_TIME < 6" | bc -l) )); then
  CPU_PERF_RATING="${GREEN}BOM${NC} (${CPU_TEST_TIME}s)"
  CPU_PERF_SCORE=2
elif (( $(echo "$CPU_TEST_TIME < 10" | bc -l) )); then
  CPU_PERF_RATING="${YELLOW}ACEITÁVEL${NC} (${CPU_TEST_TIME}s)"
  CPU_PERF_SCORE=1
else
  CPU_PERF_RATING="${RED}LENTO${NC} (${CPU_TEST_TIME}s)"
  CPU_PERF_SCORE=0
fi

# Teste de I/O - Escrita e Leitura
log "Teste de I/O: Escrita de 1GB..."
IO_WRITE_START=$(date +%s.%N)
dd if=/dev/zero of=$RESULTS_DIR/test_file bs=64M count=16 oflag=direct status=none
IO_WRITE_END=$(date +%s.%N)
IO_WRITE_TIME=$(echo "$IO_WRITE_END - $IO_WRITE_START" | bc)
IO_WRITE_SPEED=$(echo "1024 / $IO_WRITE_TIME" | bc -l)
IO_WRITE_SPEED=$(printf "%.2f" $IO_WRITE_SPEED)
log "Velocidade de escrita: ${IO_WRITE_SPEED} MB/s"

log "Teste de I/O: Leitura de 1GB..."
IO_READ_START=$(date +%s.%N)
dd if=$RESULTS_DIR/test_file of=/dev/null bs=64M count=16 iflag=direct status=none
IO_READ_END=$(date +%s.%N)
IO_READ_TIME=$(echo "$IO_READ_END - $IO_READ_START" | bc)
IO_READ_SPEED=$(echo "1024 / $IO_READ_TIME" | bc -l)
IO_READ_SPEED=$(printf "%.2f" $IO_READ_SPEED)
log "Velocidade de leitura: ${IO_READ_SPEED} MB/s"

# Limpar arquivo de teste
rm -f $RESULTS_DIR/test_file

# Avaliação do teste de I/O
if (( $(echo "$IO_WRITE_SPEED >= 100" | bc -l) )); then
  IO_WRITE_RATING="${GREEN}EXCELENTE${NC} (${IO_WRITE_SPEED} MB/s)"
  IO_WRITE_SCORE=3
elif (( $(echo "$IO_WRITE_SPEED >= 50" | bc -l) )); then
  IO_WRITE_RATING="${GREEN}BOM${NC} (${IO_WRITE_SPEED} MB/s)"
  IO_WRITE_SCORE=2
elif (( $(echo "$IO_WRITE_SPEED >= 20" | bc -l) )); then
  IO_WRITE_RATING="${YELLOW}ACEITÁVEL${NC} (${IO_WRITE_SPEED} MB/s)"
  IO_WRITE_SCORE=1
else
  IO_WRITE_RATING="${RED}LENTO${NC} (${IO_WRITE_SPEED} MB/s, mínimo recomendado: 50 MB/s)"
  IO_WRITE_SCORE=0
fi

if (( $(echo "$IO_READ_SPEED >= 100" | bc -l) )); then
  IO_READ_RATING="${GREEN}EXCELENTE${NC} (${IO_READ_SPEED} MB/s)"
  IO_READ_SCORE=3
elif (( $(echo "$IO_READ_SPEED >= 50" | bc -l) )); then
  IO_READ_RATING="${GREEN}BOM${NC} (${IO_READ_SPEED} MB/s)"
  IO_READ_SCORE=2
elif (( $(echo "$IO_READ_SPEED >= 20" | bc -l) )); then
  IO_READ_RATING="${YELLOW}ACEITÁVEL${NC} (${IO_READ_SPEED} MB/s)"
  IO_READ_SCORE=1
else
  IO_READ_RATING="${RED}LENTO${NC} (${IO_READ_SPEED} MB/s, mínimo recomendado: 50 MB/s)"
  IO_READ_SCORE=0
fi

# =========================================================
# 3. SIMULAÇÃO DE CARGA VOD
# =========================================================
log "\n${YELLOW}[3/5] Simulando carga de processamento de vídeo...${NC}"

# Criar arquivo de teste (simula vídeo)
log "Criando arquivo de teste de 100MB..."
dd if=/dev/urandom of=$RESULTS_DIR/video_test.mp4 bs=1M count=100 status=none

# Teste de cópia múltipla (simula múltiplos uploads)
log "Simulando 5 uploads simultâneos..."
MULTI_COPY_START=$(date +%s.%N)
for i in {1..5}; do
  cp $RESULTS_DIR/video_test.mp4 $RESULTS_DIR/video_copy_$i.mp4 &
done
wait
MULTI_COPY_END=$(date +%s.%N)
MULTI_COPY_TIME=$(echo "$MULTI_COPY_END - $MULTI_COPY_START" | bc)
MULTI_COPY_TIME=$(printf "%.2f" $MULTI_COPY_TIME)
log "Tempo para 5 cópias simultâneas: ${MULTI_COPY_TIME}s"

# Avaliação do teste de cópias múltiplas
if (( $(echo "$MULTI_COPY_TIME < 5" | bc -l) )); then
  MULTI_COPY_RATING="${GREEN}EXCELENTE${NC} (${MULTI_COPY_TIME}s)"
  MULTI_COPY_SCORE=3
elif (( $(echo "$MULTI_COPY_TIME < 10" | bc -l) )); then
  MULTI_COPY_RATING="${GREEN}BOM${NC} (${MULTI_COPY_TIME}s)"
  MULTI_COPY_SCORE=2
elif (( $(echo "$MULTI_COPY_TIME < 20" | bc -l) )); then
  MULTI_COPY_RATING="${YELLOW}ACEITÁVEL${NC} (${MULTI_COPY_TIME}s)"
  MULTI_COPY_SCORE=1
else
  MULTI_COPY_RATING="${RED}LENTO${NC} (${MULTI_COPY_TIME}s)"
  MULTI_COPY_SCORE=0
fi

# Simulação de processamento (compressão)
log "Simulando processamento de vídeo (compressão)..."
COMPRESS_START=$(date +%s.%N)
gzip -c $RESULTS_DIR/video_test.mp4 > $RESULTS_DIR/video_test.mp4.gz
COMPRESS_END=$(date +%s.%N)
COMPRESS_TIME=$(echo "$COMPRESS_END - $COMPRESS_START" | bc)
COMPRESS_TIME=$(printf "%.2f" $COMPRESS_TIME)
log "Tempo de compressão: ${COMPRESS_TIME}s"

# Avaliação do teste de compressão
if (( $(echo "$COMPRESS_TIME < 3" | bc -l) )); then
  COMPRESS_RATING="${GREEN}EXCELENTE${NC} (${COMPRESS_TIME}s)"
  COMPRESS_SCORE=3
elif (( $(echo "$COMPRESS_TIME < 6" | bc -l) )); then
  COMPRESS_RATING="${GREEN}BOM${NC} (${COMPRESS_TIME}s)"
  COMPRESS_SCORE=2
elif (( $(echo "$COMPRESS_TIME < 10" | bc -l) )); then
  COMPRESS_RATING="${YELLOW}ACEITÁVEL${NC} (${COMPRESS_TIME}s)"
  COMPRESS_SCORE=1
else
  COMPRESS_RATING="${RED}LENTO${NC} (${COMPRESS_TIME}s)"
  COMPRESS_SCORE=0
fi

# Limpar arquivos de teste
rm -f $RESULTS_DIR/video_test.mp4 $RESULTS_DIR/video_test.mp4.gz
rm -f $RESULTS_DIR/video_copy_*

# =========================================================
# 4. VERIFICAÇÃO DE REDE
# =========================================================
log "\n${YELLOW}[4/5] Verificando conectividade de rede...${NC}"

# Ping para testar latência
log "Testando latência para google.com..."
PING_RESULT=$(ping -c 5 google.com 2>/dev/null | grep 'rtt min/avg/max' | awk -F '/' '{print $5}')
if [ -z "$PING_RESULT" ]; then
  PING_RESULT="Falha no ping"
  PING_RATING="${RED}FALHA${NC} (Não foi possível conectar)"
  PING_SCORE=0
else
  PING_RESULT=$(printf "%.1f" $PING_RESULT)
  if (( $(echo "$PING_RESULT < 50" | bc -l) )); then
    PING_RATING="${GREEN}EXCELENTE${NC} (${PING_RESULT}ms)"
    PING_SCORE=3
  elif (( $(echo "$PING_RESULT < 100" | bc -l) )); then
    PING_RATING="${GREEN}BOM${NC} (${PING_RESULT}ms)"
    PING_SCORE=2
  elif (( $(echo "$PING_RESULT < 200" | bc -l) )); then
    PING_RATING="${YELLOW}ACEITÁVEL${NC} (${PING_RESULT}ms)"
    PING_SCORE=1
  else
    PING_RATING="${RED}ALTO${NC} (${PING_RESULT}ms)"
    PING_SCORE=0
  fi
fi
log "Latência média: ${PING_RESULT}ms"

# =========================================================
# 5. VERIFICAÇÃO DE DEPENDÊNCIAS
# =========================================================
log "\n${YELLOW}[5/5] Verificando dependências do sistema...${NC}"

# Verificar se o sistema é Debian
if [ -f /etc/debian_version ]; then
  DEBIAN_VERSION=$(cat /etc/debian_version)
  log "Debian versão: $DEBIAN_VERSION"
  DEBIAN_RATING="${GREEN}OK${NC} (Versão $DEBIAN_VERSION)"
  DEBIAN_SCORE=1
else
  log "Sistema não é Debian"
  DEBIAN_RATING="${RED}FALHA${NC} (Sistema não é Debian)"
  DEBIAN_SCORE=0
fi

# =========================================================
# SUMÁRIO E RECOMENDAÇÕES
# =========================================================
log "\n${BLUE}============================================================${NC}"
log "${BLUE}                     SUMÁRIO DA AVALIAÇÃO                    ${NC}"
log "${BLUE}============================================================${NC}"

# Calcular pontuação total
TOTAL_SCORE=$((CPU_SCORE + INSTRUCTION_SCORE + MEM_SCORE + DISK_SCORE + NETWORK_SCORE + CPU_PERF_SCORE + IO_WRITE_SCORE + IO_READ_SCORE + MULTI_COPY_SCORE + COMPRESS_SCORE + PING_SCORE + DEBIAN_SCORE))
MAX_SCORE=30

# Porcentagem de adequação
ADEQUACY_PERCENT=$((TOTAL_SCORE * 100 / MAX_SCORE))

# Adicionar resultados ao sumário
add_to_summary "${BLUE}SUMÁRIO DE AVALIAÇÃO DO SERVIDOR PARA PROJETO VIDCONV${NC}"
add_to_summary "${BLUE}============================================================${NC}"
add_to_summary "Data: $(date)"
add_to_summary "Hostname: $(hostname)"
add_to_summary "\n${YELLOW}HARDWARE:${NC}"
add_to_summary "CPU: $CPU_MODEL - $CPU_RATING"
add_to_summary "Instruções Especiais: $INSTRUCTION_RATING"
add_to_summary "Memória: ${MEM_TOTAL_GB}GB - $MEM_RATING"
add_to_summary "Armazenamento: $DISK_AVAIL disponível - $DISK_RATING"
add_to_summary "Rede: $MAIN_INTERFACE - $NETWORK_RATING"
add_to_summary "\n${YELLOW}PERFORMANCE:${NC}"
add_to_summary "Teste CPU: $CPU_PERF_RATING"
add_to_summary "Escrita em Disco: $IO_WRITE_RATING"
add_to_summary "Leitura em Disco: $IO_READ_RATING"
add_to_summary "Múltiplos Uploads: $MULTI_COPY_RATING"
add_to_summary "Processamento: $COMPRESS_RATING"
add_to_summary "Latência de Rede: $PING_RATING"
add_to_summary "Sistema Operacional: $DEBIAN_RATING"
add_to_summary "\n${YELLOW}RESULTADO FINAL:${NC}"
add_to_summary "Pontuação: $TOTAL_SCORE de $MAX_SCORE pontos"
add_to_summary "Adequação ao Projeto VOD: $ADEQUACY_PERCENT%"

# Avaliação final
if [ "$ADEQUACY_PERCENT" -ge 80 ]; then
  FINAL_RATING="${GREEN}EXCELENTE${NC}"
  RECOMMENDATION="Este servidor é ideal para o projeto VidConv. Pode prosseguir com a instalação."
elif [ "$ADEQUACY_PERCENT" -ge 60 ]; then
  FINAL_RATING="${GREEN}BOM${NC}"
  RECOMMENDATION="Este servidor atende bem aos requisitos do projeto VidConv. Pode prosseguir com a instalação."
elif [ "$ADEQUACY_PERCENT" -ge 40 ]; then
  FINAL_RATING="${YELLOW}ACEITÁVEL${NC}"
  RECOMMENDATION="Este servidor atende aos requisitos mínimos, mas pode ter limitações em carga alta."
else
  FINAL_RATING="${RED}INADEQUADO${NC}"
  RECOMMENDATION="Este servidor não atende aos requisitos mínimos para o projeto VidConv. Recomenda-se upgrade."
fi

add_to_summary "Avaliação Final: $FINAL_RATING"
add_to_summary "\n${YELLOW}RECOMENDAÇÃO:${NC}"
add_to_summary "$RECOMMENDATION"

# Exibir sumário
cat $SUMMARY_FILE

# Informações finais
log "\n${BLUE}============================================================${NC}"
log "Avaliação concluída!"
log "Relatório detalhado: $LOG_FILE"
log "Sumário: $SUMMARY_FILE"
log "${BLUE}============================================================${NC}"