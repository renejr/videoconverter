#!/usr/bin/env bash
set -euo pipefail

# =============================
# VidConv - Bootstrap Debian
# =============================
# Este script prepara um servidor Debian para rodar o VidConv em produção.
# Execute-o como root OU com sudo: sudo bash bootstrap_debian.sh
# Antes de executar, ajuste as variáveis abaixo.

# --------- VARIÁVEIS ---------
DOMAIN="170.62.161.33"             # IP do servidor VideoClube (será atualizado quando houver domínio)
APP_USER="videoclube"              # Usuário não-root para rodar a aplicação VideoClube
MYSQL_APP_DB="videoclube_db"
MYSQL_APP_USER="videoclube_user"
MYSQL_APP_PASS="VcMy\$ql2024#Pr0d"  # Senha forte para MySQL
MONGO_APP_DB="videoclube_logs"
MONGO_APP_USER="videoclube_user"
MONGO_APP_PASS="VcM0ng0#2024\$L0gs" # Senha forte para MongoDB

# --------- FUNÇÕES ---------
log() { echo -e "\n[BOOTSTRAP] $1"; }

update_system() {
  log "Atualizando sistema..."
  apt update && apt -y upgrade
  apt -y install curl wget git build-essential software-properties-common \
    apt-transport-https ca-certificates gnupg lsb-release unzip ufw
}

create_app_user() {
  if id -u "$APP_USER" >/dev/null 2>&1; then
    log "Usuário $APP_USER já existe."
  else
    log "Criando usuário $APP_USER..."
    adduser --disabled-password --gecos "VidConv User" "$APP_USER"
    usermod -aG sudo "$APP_USER"
  fi
}

configure_firewall() {
  log "Configurando UFW..."
  ufw allow ssh || true
  ufw allow 80 || true
  ufw allow 443 || true
  ufw --force enable || true
  ufw status
}

install_nginx() {
  log "Instalando Nginx..."
  apt -y install nginx
  systemctl enable nginx
  systemctl start nginx
}

install_nodejs() {
  log "Instalando Node.js 18 LTS..."
  curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
  apt -y install nodejs
  npm install -g pm2
}

install_python() {
  log "Instalando Python e ferramentas..."
  apt -y install python3 python3-pip python3-venv python3-dev python3-setuptools \
    gcc g++ make libffi-dev libssl-dev
}

install_ffmpeg() {
  log "Instalando FFmpeg..."
  apt -y install ffmpeg
}

install_mysql() {
  log "Instalando MySQL Server..."
  DEBIAN_FRONTEND=noninteractive apt -y install mysql-server
  systemctl enable mysql
  systemctl start mysql
  
  log "Criando banco e usuário de aplicação no MySQL..."
  mysql -e "CREATE DATABASE IF NOT EXISTS \`$MYSQL_APP_DB\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
  mysql -e "CREATE USER IF NOT EXISTS '$MYSQL_APP_USER'@'localhost' IDENTIFIED BY '$MYSQL_APP_PASS';"
  mysql -e "GRANT ALL PRIVILEGES ON \`$MYSQL_APP_DB\`.* TO '$MYSQL_APP_USER'@'localhost';"
  mysql -e "FLUSH PRIVILEGES;"
}

install_mongodb() {
  log "Instalando MongoDB (ajuste repo conforme sua versão do Debian)..."
  # Observação: verifique a doc oficial para Debian 12/Bookworm.
  # Exemplo abaixo usa repositório Ubuntu; em Debian, substitua pelas entradas adequadas.
  if ! command -v mongod >/dev/null 2>&1; then
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" > /etc/apt/sources.list.d/mongodb-org-7.0.list
    apt update
    apt -y install mongodb-org
    systemctl enable mongod
    systemctl start mongod
  else
    log "MongoDB já instalado."
  fi

  log "Habilitando autenticação no MongoDB..."
  sed -i 's/^#*\s*authorization:.*/  authorization: enabled/' /etc/mongod.conf || true
  if ! grep -q "authorization:" /etc/mongod.conf; then
    printf "\nsecurity:\n  authorization: enabled\n" >> /etc/mongod.conf
  fi
  systemctl restart mongod

  log "Criando usuário de aplicação no MongoDB..."
  cat > /tmp/mongo_init.js <<EOF
use $MONGO_APP_DB;
try {
  db.createUser({
    user: "$MONGO_APP_USER",
    pwd: "$MONGO_APP_PASS",
    roles: ["readWrite"]
  });
} catch (e) {
  print("Usuário pode já existir: " + e);
}
EOF
  mongosh < /tmp/mongo_init.js || true
}

install_redis() {
  log "Instalando Redis..."
  apt -y install redis-server
  systemctl enable redis-server
  systemctl start redis-server
}

issue_ssl_cert() {
  log "Instalando Certbot e preparando SSL..."
  apt -y install certbot python3-certbot-nginx
  log "Para emitir SSL, execute manualmente: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
}

prepare_dirs() {
  log "Preparando estrutura de diretórios em /opt/vidconv..."
  mkdir -p /opt/vidconv/{frontend,user_service,notification_service,core,logs,uploads,converted}
  chown -R "$APP_USER":"$APP_USER" /opt/vidconv
}

summary() {
  log "Resumo do bootstrap:"
  echo "- Usuário app: $APP_USER"
  echo "- Domain: $DOMAIN"
  echo "- MySQL: db=$MYSQL_APP_DB user=$MYSQL_APP_USER"
  echo "- MongoDB: db=$MONGO_APP_DB user=$MONGO_APP_USER"
  echo "- Diretórios: /opt/vidconv/*"
  echo "\nPróximos passos:"
  echo "1) Configurar Nginx com seus serviços e emitir SSL (Certbot)."
  echo "2) Clonar o repositório em /opt/vidconv e configurar PM2 para frontend e serviços."
  echo "3) Ajustar .env nos serviços (User Service, Notification Service, Frontend)."
  echo "4) Executar migrações do MySQL (Alembic) e validar conexões."
}

main() {
  update_system
  create_app_user
  configure_firewall
  install_nginx
  install_nodejs
  install_python
  install_ffmpeg
  install_mysql
  install_mongodb
  install_redis
  issue_ssl_cert
  prepare_dirs
  summary
  log "Bootstrap concluído."
}

main "$@"