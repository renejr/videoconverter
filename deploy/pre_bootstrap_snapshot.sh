#!/bin/bash
# PRE-BOOTSTRAP SNAPSHOT - VideoClube
# Este script cria um snapshot do estado atual do servidor antes do bootstrap
# Permite rollback mais seguro e preciso

set -e

SNAPSHOT_DIR="/tmp/videoclube_pre_bootstrap_$(date +%Y%m%d_%H%M%S)"

log() { echo -e "\n[SNAPSHOT] $1"; }

create_snapshot() {
  log "Criando snapshot do estado atual em: $SNAPSHOT_DIR"
  mkdir -p "$SNAPSHOT_DIR"
  
  # 1. Lista de pacotes instalados
  log "Salvando lista de pacotes..."
  dpkg --get-selections > "$SNAPSHOT_DIR/packages_before.txt"
  apt list --installed > "$SNAPSHOT_DIR/apt_packages_before.txt" 2>/dev/null
  
  # 2. Serviços ativos
  log "Salvando estado dos serviços..."
  systemctl list-units --type=service --state=active > "$SNAPSHOT_DIR/services_before.txt"
  systemctl list-units --type=service --state=enabled > "$SNAPSHOT_DIR/services_enabled_before.txt"
  
  # 3. Usuários do sistema
  log "Salvando usuários..."
  cp /etc/passwd "$SNAPSHOT_DIR/passwd_before.txt"
  cp /etc/group "$SNAPSHOT_DIR/group_before.txt"
  
  # 4. Configuração do firewall
  log "Salvando configuração do firewall..."
  ufw status verbose > "$SNAPSHOT_DIR/ufw_before.txt" 2>/dev/null || echo "UFW não configurado" > "$SNAPSHOT_DIR/ufw_before.txt"
  
  # 5. Configurações do Nginx (se existir)
  if [ -d "/etc/nginx" ]; then
    log "Backup do Nginx..."
    cp -r /etc/nginx "$SNAPSHOT_DIR/nginx_backup/"
  fi
  
  # 6. Bancos de dados existentes
  log "Verificando bancos de dados..."
  if command -v mysql >/dev/null 2>&1; then
    mysql -e "SHOW DATABASES;" > "$SNAPSHOT_DIR/mysql_databases_before.txt" 2>/dev/null || echo "MySQL não acessível" > "$SNAPSHOT_DIR/mysql_databases_before.txt"
  fi
  
  if command -v mongosh >/dev/null 2>&1; then
    mongosh --eval "db.adminCommand('listDatabases')" > "$SNAPSHOT_DIR/mongo_databases_before.txt" 2>/dev/null || echo "MongoDB não acessível" > "$SNAPSHOT_DIR/mongo_databases_before.txt"
  fi
  
  # 7. Estrutura de diretórios /opt
  log "Salvando estrutura /opt..."
  ls -la /opt/ > "$SNAPSHOT_DIR/opt_structure_before.txt" 2>/dev/null || echo "/opt vazio" > "$SNAPSHOT_DIR/opt_structure_before.txt"
  
  # 8. Processos em execução
  log "Salvando processos..."
  ps aux > "$SNAPSHOT_DIR/processes_before.txt"
  
  # 9. Portas em uso
  log "Salvando portas..."
  netstat -tulpn > "$SNAPSHOT_DIR/ports_before.txt" 2>/dev/null || ss -tulpn > "$SNAPSHOT_DIR/ports_before.txt"
  
  # 10. Informações do sistema
  log "Salvando informações do sistema..."
  uname -a > "$SNAPSHOT_DIR/system_info.txt"
  lsb_release -a >> "$SNAPSHOT_DIR/system_info.txt" 2>/dev/null || true
  df -h > "$SNAPSHOT_DIR/disk_usage_before.txt"
  free -h > "$SNAPSHOT_DIR/memory_before.txt"
  
  # 11. Criar script de comparação
  create_comparison_script
  
  log "Snapshot criado com sucesso!"
  echo "📁 Localização: $SNAPSHOT_DIR"
  echo "📋 Arquivos salvos:"
  ls -la "$SNAPSHOT_DIR/"
}

create_comparison_script() {
  cat > "$SNAPSHOT_DIR/compare_after_bootstrap.sh" << 'EOF'
#!/bin/bash
# Script para comparar o estado antes e depois do bootstrap

SNAPSHOT_DIR="$(dirname "$0")"
echo "=== COMPARAÇÃO PRÉ/PÓS BOOTSTRAP ==="

echo -e "\n📦 NOVOS PACOTES INSTALADOS:"
dpkg --get-selections > /tmp/packages_after.txt
diff "$SNAPSHOT_DIR/packages_before.txt" /tmp/packages_after.txt | grep "^>" | head -20

echo -e "\n🔧 NOVOS SERVIÇOS ATIVOS:"
systemctl list-units --type=service --state=active > /tmp/services_after.txt
diff "$SNAPSHOT_DIR/services_before.txt" /tmp/services_after.txt | grep "^>" | head -10

echo -e "\n👥 NOVOS USUÁRIOS:"
diff "$SNAPSHOT_DIR/passwd_before.txt" /etc/passwd | grep "^>" || echo "Nenhum usuário novo"

echo -e "\n🔥 MUDANÇAS NO FIREWALL:"
ufw status verbose > /tmp/ufw_after.txt 2>/dev/null
diff "$SNAPSHOT_DIR/ufw_before.txt" /tmp/ufw_after.txt || echo "Firewall alterado"

echo -e "\n📁 NOVOS DIRETÓRIOS EM /opt:"
ls -la /opt/ > /tmp/opt_after.txt 2>/dev/null
diff "$SNAPSHOT_DIR/opt_structure_before.txt" /tmp/opt_after.txt | grep "^>" || echo "Nenhum novo diretório"

echo -e "\n🌐 NOVAS PORTAS EM USO:"
netstat -tulpn > /tmp/ports_after.txt 2>/dev/null || ss -tulpn > /tmp/ports_after.txt
echo "Portas antes: $(wc -l < "$SNAPSHOT_DIR/ports_before.txt") | Portas depois: $(wc -l < /tmp/ports_after.txt)"

echo -e "\n✅ Comparação concluída!"
echo "Para rollback completo, execute: sudo bash rollback_bootstrap.sh"
EOF

  chmod +x "$SNAPSHOT_DIR/compare_after_bootstrap.sh"
}

main() {
  if [ "$EUID" -ne 0 ]; then
    echo "Este script deve ser executado como root (sudo)"
    exit 1
  fi
  
  create_snapshot
  
  echo ""
  echo "🎯 PRÓXIMOS PASSOS:"
  echo "1. Execute o bootstrap: sudo bash bootstrap_debian.sh"
  echo "2. Para comparar mudanças: sudo bash $SNAPSHOT_DIR/compare_after_bootstrap.sh"
  echo "3. Para rollback: sudo bash rollback_bootstrap.sh"
  echo ""
  echo "📍 Snapshot salvo em: $SNAPSHOT_DIR"
}

main "$@"