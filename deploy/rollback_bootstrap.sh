#!/bin/bash
# ROLLBACK SCRIPT - VideoClube Bootstrap
# Este script reverte as mudanças feitas pelo bootstrap_debian.sh
# ATENÇÃO: Execute apenas se necessário reverter a instalação

set -e

# --------- VARIÁVEIS (devem coincidir com bootstrap) ---------
APP_USER="videoclube"
MYSQL_APP_DB="videoclube_db"
MYSQL_APP_USER="videoclube_user"
MONGO_APP_DB="videoclube_logs"
MONGO_APP_USER="videoclube_user"

# --------- FUNÇÕES ---------
log() { echo -e "\n[ROLLBACK] $1"; }

confirm_rollback() {
  echo "⚠️  ATENÇÃO: Este script irá REVERTER todas as mudanças do bootstrap!"
  echo "Isso inclui:"
  echo "- Remoção do usuário $APP_USER"
  echo "- Desinstalação de Nginx, Node.js, Python, FFmpeg"
  echo "- Remoção dos bancos MySQL e MongoDB"
  echo "- Limpeza de diretórios /opt/videoclube"
  echo "- Desabilitação do firewall UFW"
  echo ""
  read -p "Tem certeza que deseja continuar? (digite 'CONFIRMO' para prosseguir): " confirm
  if [ "$confirm" != "CONFIRMO" ]; then
    log "Rollback cancelado pelo usuário."
    exit 0
  fi
}

backup_important_data() {
  log "Fazendo backup de dados importantes..."
  mkdir -p /tmp/videoclube_backup_$(date +%Y%m%d_%H%M%S)
  
  # Backup de logs se existirem
  if [ -d "/opt/videoclube/logs" ]; then
    cp -r /opt/videoclube/logs /tmp/videoclube_backup_*/
  fi
  
  # Backup de uploads se existirem
  if [ -d "/opt/videoclube/uploads" ]; then
    cp -r /opt/videoclube/uploads /tmp/videoclube_backup_*/
  fi
  
  log "Backup salvo em /tmp/videoclube_backup_*"
}

stop_services() {
  log "Parando serviços..."
  systemctl stop nginx || true
  systemctl stop mysql || true
  systemctl stop mongod || true
  systemctl stop redis-server || true
  
  # Parar processos PM2 se existirem
  if command -v pm2 >/dev/null 2>&1; then
    sudo -u "$APP_USER" pm2 kill || true
  fi
}

remove_databases() {
  log "Removendo bancos de dados..."
  
  # MySQL
  if command -v mysql >/dev/null 2>&1; then
    mysql -e "DROP DATABASE IF EXISTS $MYSQL_APP_DB;" || true
    mysql -e "DROP USER IF EXISTS '$MYSQL_APP_USER'@'localhost';" || true
    mysql -e "FLUSH PRIVILEGES;" || true
  fi
  
  # MongoDB
  if command -v mongosh >/dev/null 2>&1; then
    mongosh --eval "db.getSiblingDB('$MONGO_APP_DB').dropDatabase()" || true
    mongosh --eval "db.getSiblingDB('admin').dropUser('$MONGO_APP_USER')" || true
  fi
}

remove_packages() {
  log "Removendo pacotes instalados..."
  
  # Nginx
  systemctl disable nginx || true
  apt -y remove --purge nginx nginx-common || true
  
  # Node.js e PM2
  npm uninstall -g pm2 || true
  apt -y remove --purge nodejs npm || true
  rm -rf /etc/apt/sources.list.d/nodesource.list || true
  
  # Python packages
  pip3 uninstall -y fastapi uvicorn sqlalchemy alembic pymongo redis || true
  
  # FFmpeg
  apt -y remove --purge ffmpeg || true
  
  # MySQL
  systemctl disable mysql || true
  apt -y remove --purge mysql-server mysql-client mysql-common || true
  rm -rf /var/lib/mysql || true
  
  # MongoDB
  systemctl disable mongod || true
  apt -y remove --purge mongodb-org* || true
  rm -rf /var/lib/mongodb || true
  rm -rf /etc/apt/sources.list.d/mongodb-org-*.list || true
  
  # Redis
  systemctl disable redis-server || true
  apt -y remove --purge redis-server || true
  
  # Certbot
  apt -y remove --purge certbot python3-certbot-nginx || true
}

remove_user_and_dirs() {
  log "Removendo usuário e diretórios..."
  
  # Remover diretórios da aplicação
  rm -rf /opt/videoclube || true
  
  # Remover usuário
  if id -u "$APP_USER" >/dev/null 2>&1; then
    userdel -r "$APP_USER" || true
  fi
}

reset_firewall() {
  log "Resetando firewall..."
  ufw --force reset || true
  ufw disable || true
}

cleanup_configs() {
  log "Limpando configurações..."
  
  # Nginx configs
  rm -f /etc/nginx/sites-available/videoclube || true
  rm -f /etc/nginx/sites-enabled/videoclube || true
  
  # Logs
  rm -f /var/log/nginx/videoclube_* || true
  
  # Certificados SSL se existirem
  rm -rf /etc/letsencrypt/live/videoclube* || true
  rm -rf /etc/letsencrypt/archive/videoclube* || true
  rm -rf /etc/letsencrypt/renewal/videoclube* || true
}

final_cleanup() {
  log "Limpeza final..."
  apt -y autoremove
  apt -y autoclean
  
  # Atualizar cache de pacotes
  apt update
}

show_summary() {
  log "=== ROLLBACK CONCLUÍDO ==="
  echo "✅ Serviços parados e desabilitados"
  echo "✅ Bancos de dados removidos"
  echo "✅ Pacotes desinstalados"
  echo "✅ Usuário $APP_USER removido"
  echo "✅ Diretórios /opt/videoclube removidos"
  echo "✅ Firewall resetado"
  echo "✅ Configurações limpas"
  echo ""
  echo "📁 Backup dos dados salvo em: /tmp/videoclube_backup_*"
  echo ""
  echo "⚠️  IMPORTANTE:"
  echo "- O servidor está agora no estado anterior ao bootstrap"
  echo "- Verifique se há outros serviços que precisam ser reiniciados"
  echo "- Os backups em /tmp/ devem ser movidos para local seguro"
}

main() {
  confirm_rollback
  backup_important_data
  stop_services
  remove_databases
  remove_packages
  remove_user_and_dirs
  reset_firewall
  cleanup_configs
  final_cleanup
  show_summary
  log "Rollback concluído com sucesso."
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script deve ser executado como root (sudo)"
  exit 1
fi

main "$@"