# 🚀 GUIA COMPLETO DE MIGRAÇÃO PARA PRODUÇÃO
## Projeto VidConv - Servidor Debian

---

## 📋 **ÍNDICE**

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Preparação do Servidor Debian](#preparação-do-servidor-debian)
3. [Instalação de Dependências](#instalação-de-dependências)
4. [Configuração dos Bancos de Dados](#configuração-dos-bancos-de-dados)
5. [Deploy dos Serviços](#deploy-dos-serviços)
6. [Configuração do Nginx](#configuração-do-nginx)
7. [Configuração de SSL/HTTPS](#configuração-de-sslhttps)
8. [Scripts de Automação](#scripts-de-automação)
9. [Monitoramento e Logs](#monitoramento-e-logs)
10. [Backup e Recuperação](#backup-e-recuperação)
11. [Checklist de Segurança](#checklist-de-segurança)
12. [Troubleshooting](#troubleshooting)

---

## 🏗️ **VISÃO GERAL DA ARQUITETURA**

### **Componentes do Sistema:**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FRONTEND      │    │   USER SERVICE  │    │ NOTIFICATION    │
│   Next.js       │    │   FastAPI       │    │ SERVICE         │
│   Port: 3000    │    │   Port: 8001    │    │ Port: 8002      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     NGINX       │
                    │   Port: 80/443  │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   CORE VIDEO    │
                    │   CONVERTER     │
                    └─────────────────┘
```

### **Bancos de Dados:**

- **MySQL**: Dados relacionais (usuários, planos, pagamentos)
- **MongoDB**: Dados não-relacionais (logs, metadados, cache)
- **Redis**: Cache e filas de processamento

---

## 🖥️ **PREPARAÇÃO DO SERVIDOR DEBIAN**

### **1. Atualização do Sistema**

```bash
# Conectar ao servidor via SSH
ssh root@seu-servidor.com

# Atualizar repositórios e sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências básicas
sudo apt install -y curl wget git build-essential software-properties-common \
    apt-transport-https ca-certificates gnupg lsb-release unzip
```

### **2. Configuração de Usuário**

```bash
# Criar usuário para a aplicação
sudo adduser vidconv
sudo usermod -aG sudo vidconv

# Trocar para o usuário da aplicação
su - vidconv
```

### **3. Configuração de Firewall**

```bash
# Instalar e configurar UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw status
```

---

## 📦 **INSTALAÇÃO DE DEPENDÊNCIAS**

### **1. Node.js (v18 LTS)**

```bash
# Adicionar repositório oficial do Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Instalar Node.js e npm
sudo apt install -y nodejs

# Verificar instalação
node --version  # Deve mostrar v18.x.x
npm --version   # Deve mostrar 9.x.x

# Instalar PM2 globalmente
sudo npm install -g pm2
```

### **2. Python 3.11**

```bash
# Python já vem no Debian, instalar pip e ferramentas
sudo apt install -y python3-pip python3-venv python3-dev python3-setuptools

# Instalar dependências para compilação
sudo apt install -y gcc g++ make libffi-dev libssl-dev

# Verificar instalação
python3 --version  # Deve mostrar 3.11.x
pip3 --version
```

### **3. Nginx**

```bash
# Instalar Nginx
sudo apt install -y nginx

# Iniciar e habilitar serviço
sudo systemctl start nginx
sudo systemctl enable nginx

# Verificar status
sudo systemctl status nginx
```

### **4. FFmpeg**

```bash
# Instalar FFmpeg para conversão de vídeo
sudo apt install -y ffmpeg

# Verificar instalação
ffmpeg -version
```

---

## 🗄️ **CONFIGURAÇÃO DOS BANCOS DE DADOS**

### **1. MySQL Server**

```bash
# Instalar MySQL
sudo apt install -y mysql-server

# Executar script de segurança
sudo mysql_secure_installation

# Configurações recomendadas:
# - Remover usuários anônimos: Y
# - Desabilitar login root remoto: Y
# - Remover banco de teste: Y
# - Recarregar tabelas de privilégios: Y
```

**Configuração do banco:**

```sql
# Conectar ao MySQL
sudo mysql -u root -p

# Criar banco e usuário para a aplicação
CREATE DATABASE vidconv_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'vidconv_user'@'localhost' IDENTIFIED BY 'SuaSenhaSegura123!';
GRANT ALL PRIVILEGES ON vidconv_db.* TO 'vidconv_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### **2. MongoDB**

```bash
# Importar chave GPG do MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Adicionar repositório
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Atualizar e instalar
sudo apt update
sudo apt install -y mongodb-org

# Iniciar serviço
sudo systemctl start mongod
sudo systemctl enable mongod

# Verificar status
sudo systemctl status mongod
```

**Configuração de segurança do MongoDB:**

```bash
# Conectar ao MongoDB
mongosh

# Criar usuário administrador
use admin
db.createUser({
  user: "admin",
  pwd: "SuaSenhaSegura123!",
  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]
})

# Criar usuário para aplicação
use vidconv_logs
db.createUser({
  user: "vidconv_user",
  pwd: "SuaSenhaSegura123!",
  roles: ["readWrite"]
})

exit
```

**Habilitar autenticação:**

```bash
# Editar arquivo de configuração
sudo nano /etc/mongod.conf

# Adicionar/modificar:
security:
  authorization: enabled

# Reiniciar serviço
sudo systemctl restart mongod
```

### **3. Redis**

```bash
# Instalar Redis
sudo apt install -y redis-server

# Configurar para iniciar automaticamente
sudo systemctl enable redis-server

# Verificar instalação
redis-cli ping  # Deve retornar PONG
```

---

## 🚀 **DEPLOY DOS SERVIÇOS**

### **1. Estrutura de Diretórios**

```bash
# Criar estrutura de diretórios
sudo mkdir -p /opt/vidconv/{frontend,user_service,notification_service,core,logs,uploads,converted}
sudo chown -R vidconv:vidconv /opt/vidconv
```

### **2. Clone do Repositório**

```bash
# Navegar para diretório de trabalho
cd /opt/vidconv

# Clonar repositório (substitua pela sua URL)
git clone https://github.com/seu-usuario/vidconv.git temp
mv temp/* .
rm -rf temp
```

### **3. Deploy do Frontend (Next.js)**

```bash
# Navegar para diretório do frontend
cd /opt/vidconv/frontend

# Instalar dependências
npm install

# Criar arquivo de ambiente de produção
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://seu-dominio.com/api
NEXT_PUBLIC_USER_SERVICE_URL=https://seu-dominio.com/api/users
NEXT_PUBLIC_NOTIFICATION_SERVICE_URL=https://seu-dominio.com/api/notifications
NODE_ENV=production
EOF

# Build da aplicação
npm run build

# Configurar PM2
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'vidconv-frontend',
    script: 'npm',
    args: 'start',
    cwd: '/opt/vidconv/frontend',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    error_file: '/opt/vidconv/logs/frontend-error.log',
    out_file: '/opt/vidconv/logs/frontend-out.log',
    log_file: '/opt/vidconv/logs/frontend.log'
  }]
}
EOF

# Iniciar com PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### **4. Deploy do User Service (FastAPI)**

```bash
# Navegar para diretório do user service
cd /opt/vidconv/user_service

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo de ambiente
cat > .env << EOF
# Database
DATABASE_URL=mysql+pymysql://vidconv_user:SuaSenhaSegura123!@localhost/vidconv_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=sua-chave-secreta-muito-segura-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (configure conforme seu provedor)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app

# Environment
ENVIRONMENT=production
DEBUG=False
EOF

# Executar migrações do banco
alembic upgrade head

# Configurar PM2
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'vidconv-user-service',
    script: 'venv/bin/uvicorn',
    args: 'main:app --host 0.0.0.0 --port 8001',
    cwd: '/opt/vidconv/user_service',
    instances: 2,
    exec_mode: 'cluster',
    env: {
      PYTHONPATH: '/opt/vidconv/user_service'
    },
    error_file: '/opt/vidconv/logs/user-service-error.log',
    out_file: '/opt/vidconv/logs/user-service-out.log',
    log_file: '/opt/vidconv/logs/user-service.log'
  }]
}
EOF

# Iniciar com PM2
pm2 start ecosystem.config.js
```

### **5. Deploy do Notification Service**

```bash
# Navegar para diretório do notification service
cd /opt/vidconv/notification_service

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo de ambiente
cat > .env << EOF
# MongoDB
MONGODB_URL=mongodb://vidconv_user:SuaSenhaSegura123!@localhost:27017/vidconv_logs

# Redis
REDIS_URL=redis://localhost:6379/1

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app

# Environment
ENVIRONMENT=production
DEBUG=False
EOF

# Configurar PM2
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'vidconv-notification-service',
    script: 'venv/bin/python',
    args: 'main.py',
    cwd: '/opt/vidconv/notification_service',
    instances: 1,
    env: {
      PYTHONPATH: '/opt/vidconv/notification_service'
    },
    error_file: '/opt/vidconv/logs/notification-service-error.log',
    out_file: '/opt/vidconv/logs/notification-service-out.log',
    log_file: '/opt/vidconv/logs/notification-service.log'
  }]
}
EOF

# Iniciar com PM2
pm2 start ecosystem.config.js
```

### **6. Deploy do Core Video Converter**

```bash
# Navegar para diretório do core
cd /opt/vidconv/core

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r ../requirements.txt

# Configurar PM2 para worker de conversão
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'vidconv-worker',
    script: 'venv/bin/python',
    args: 'queue_manager.py',
    cwd: '/opt/vidconv/core',
    instances: 2,
    env: {
      PYTHONPATH: '/opt/vidconv',
      REDIS_URL: 'redis://localhost:6379/2',
      UPLOAD_DIR: '/opt/vidconv/uploads',
      OUTPUT_DIR: '/opt/vidconv/converted'
    },
    error_file: '/opt/vidconv/logs/worker-error.log',
    out_file: '/opt/vidconv/logs/worker-out.log',
    log_file: '/opt/vidconv/logs/worker.log'
  }]
}
EOF

# Iniciar com PM2
pm2 start ecosystem.config.js
```

---

## 🌐 **CONFIGURAÇÃO DO NGINX**

### **1. Configuração Principal**

```bash
# Criar arquivo de configuração
sudo nano /etc/nginx/sites-available/vidconv
```

```nginx
# Configuração do VidConv
upstream frontend {
    server 127.0.0.1:3000;
}

upstream user_service {
    server 127.0.0.1:8001;
}

upstream notification_service {
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;

    # SSL Configuration (será configurado na próxima seção)
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Upload size limit
    client_max_body_size 500M;
    client_body_timeout 300s;
    client_header_timeout 300s;

    # Frontend Next.js
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # API de usuários
    location /api/users/ {
        proxy_pass http://user_service/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # API de notificações
    location /api/notifications/ {
        proxy_pass http://notification_service/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Arquivos estáticos (uploads/downloads)
    location /uploads/ {
        alias /opt/vidconv/uploads/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    location /converted/ {
        alias /opt/vidconv/converted/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # Logs de acesso
    access_log /var/log/nginx/vidconv_access.log;
    error_log /var/log/nginx/vidconv_error.log;
}
```

### **2. Ativar Configuração**

```bash
# Habilitar site
sudo ln -s /etc/nginx/sites-available/vidconv /etc/nginx/sites-enabled/

# Remover configuração padrão
sudo rm /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## 🔒 **CONFIGURAÇÃO DE SSL/HTTPS**

### **1. Instalar Certbot**

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado SSL
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Configurar renovação automática
sudo crontab -e

# Adicionar linha para renovação automática (às 2h da manhã):
0 2 * * * /usr/bin/certbot renew --quiet
```

### **2. Testar SSL**

```bash
# Testar renovação
sudo certbot renew --dry-run

# Verificar certificado
openssl s_client -connect seu-dominio.com:443 -servername seu-dominio.com
```

---

## 🤖 **SCRIPTS DE AUTOMAÇÃO**

### **1. Script de Deploy**

```bash
# Criar script de deploy
cat > /opt/vidconv/deploy.sh << 'EOF'
#!/bin/bash

echo "🚀 Iniciando deploy do VidConv..."

# Parar serviços
pm2 stop all

# Atualizar código
cd /opt/vidconv
git pull origin main

# Frontend
echo "📦 Atualizando Frontend..."
cd frontend
npm install
npm run build
pm2 restart vidconv-frontend

# User Service
echo "🔧 Atualizando User Service..."
cd ../user_service
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
pm2 restart vidconv-user-service

# Notification Service
echo "📧 Atualizando Notification Service..."
cd ../notification_service
source venv/bin/activate
pip install -r requirements.txt
pm2 restart vidconv-notification-service

# Core Worker
echo "⚙️ Atualizando Core Worker..."
cd ../core
source venv/bin/activate
pip install -r ../requirements.txt
pm2 restart vidconv-worker

echo "✅ Deploy concluído!"
pm2 status
EOF

chmod +x /opt/vidconv/deploy.sh
```

### **2. Script de Backup**

```bash
# Criar script de backup
cat > /opt/vidconv/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/backups/vidconv"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "💾 Iniciando backup..."

# Backup MySQL
mysqldump -u vidconv_user -p'SuaSenhaSegura123!' vidconv_db > $BACKUP_DIR/mysql_$DATE.sql

# Backup MongoDB
mongodump --uri="mongodb://vidconv_user:SuaSenhaSegura123!@localhost:27017/vidconv_logs" --out=$BACKUP_DIR/mongodb_$DATE

# Backup arquivos de configuração
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/vidconv/*.env /etc/nginx/sites-available/vidconv

# Limpar backups antigos (manter últimos 7 dias)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "mongodb_*" -mtime +7 -exec rm -rf {} \;
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +7 -delete

echo "✅ Backup concluído em $BACKUP_DIR"
EOF

chmod +x /opt/vidconv/backup.sh

# Configurar backup automático
sudo crontab -e

# Adicionar linha para backup diário às 3h da manhã:
0 3 * * * /opt/vidconv/backup.sh
```

### **3. Script de Monitoramento**

```bash
# Criar script de monitoramento
cat > /opt/vidconv/monitor.sh << 'EOF'
#!/bin/bash

echo "📊 Status dos Serviços VidConv"
echo "================================"

# PM2 Status
echo "🔧 PM2 Processes:"
pm2 status

echo ""

# Nginx Status
echo "🌐 Nginx Status:"
sudo systemctl status nginx --no-pager -l

echo ""

# Database Status
echo "🗄️ Database Status:"
echo "MySQL:"
sudo systemctl status mysql --no-pager -l | head -3

echo "MongoDB:"
sudo systemctl status mongod --no-pager -l | head -3

echo "Redis:"
sudo systemctl status redis-server --no-pager -l | head -3

echo ""

# Disk Usage
echo "💾 Disk Usage:"
df -h /opt/vidconv

echo ""

# Memory Usage
echo "🧠 Memory Usage:"
free -h

echo ""

# Recent Logs
echo "📝 Recent Errors (last 10 lines):"
tail -10 /opt/vidconv/logs/*.log 2>/dev/null | grep -i error
EOF

chmod +x /opt/vidconv/monitor.sh
```

---

## 📊 **MONITORAMENTO E LOGS**

### **1. Configuração de Logs**

```bash
# Configurar rotação de logs
sudo nano /etc/logrotate.d/vidconv
```

```
/opt/vidconv/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 vidconv vidconv
    postrotate
        pm2 reloadLogs
    endscript
}
```

### **2. Monitoramento com PM2**

```bash
# Instalar PM2 Web Monitor
pm2 install pm2-server-monit

# Configurar monitoramento
pm2 set pm2-server-monit:port 9615
pm2 set pm2-server-monit:refresh 5000

# Visualizar logs em tempo real
pm2 logs

# Monitorar recursos
pm2 monit
```

---

## 💾 **BACKUP E RECUPERAÇÃO**

### **1. Estratégia de Backup**

- **Diário**: Bancos de dados e configurações
- **Semanal**: Arquivos de aplicação
- **Mensal**: Backup completo do sistema

### **2. Script de Recuperação**

```bash
# Criar script de recuperação
cat > /opt/vidconv/restore.sh << 'EOF'
#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Uso: $0 <data_backup> (formato: YYYYMMDD_HHMMSS)"
    exit 1
fi

BACKUP_DIR="/opt/backups/vidconv"
DATE=$1

echo "🔄 Iniciando restauração do backup $DATE..."

# Parar serviços
pm2 stop all

# Restaurar MySQL
mysql -u vidconv_user -p'SuaSenhaSegura123!' vidconv_db < $BACKUP_DIR/mysql_$DATE.sql

# Restaurar MongoDB
mongorestore --uri="mongodb://vidconv_user:SuaSenhaSegura123!@localhost:27017/vidconv_logs" --drop $BACKUP_DIR/mongodb_$DATE/vidconv_logs

# Restaurar configurações
tar -xzf $BACKUP_DIR/config_$DATE.tar.gz -C /

# Reiniciar serviços
pm2 start all

echo "✅ Restauração concluída!"
EOF

chmod +x /opt/vidconv/restore.sh
```

---

## 🔐 **CHECKLIST DE SEGURANÇA**

### **1. Sistema Operacional**

- [ ] Sistema atualizado
- [ ] Firewall configurado (UFW)
- [ ] SSH configurado com chaves
- [ ] Usuário não-root para aplicação
- [ ] Fail2ban instalado

```bash
# Instalar Fail2ban
sudo apt install -y fail2ban

# Configurar Fail2ban
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
```

### **2. Bancos de Dados**

- [ ] Senhas fortes configuradas
- [ ] Usuários com privilégios mínimos
- [ ] Acesso restrito ao localhost
- [ ] Backups automáticos configurados

### **3. Aplicação**

- [ ] Variáveis de ambiente seguras
- [ ] HTTPS configurado
- [ ] Headers de segurança
- [ ] Rate limiting implementado
- [ ] Logs de auditoria

### **4. Nginx**

- [ ] SSL/TLS configurado
- [ ] Headers de segurança
- [ ] Rate limiting
- [ ] Ocultação de versão

```bash
# Ocultar versão do Nginx
sudo nano /etc/nginx/nginx.conf

# Adicionar na seção http:
server_tokens off;
```

---

## 🔧 **TROUBLESHOOTING**

### **1. Problemas Comuns**

**Serviço não inicia:**
```bash
# Verificar logs
pm2 logs <nome-do-serviço>

# Verificar status
pm2 status

# Reiniciar serviço
pm2 restart <nome-do-serviço>
```

**Erro de conexão com banco:**
```bash
# Verificar status do MySQL
sudo systemctl status mysql

# Verificar logs do MySQL
sudo tail -f /var/log/mysql/error.log

# Testar conexão
mysql -u vidconv_user -p -h localhost vidconv_db
```

**Erro 502 Bad Gateway:**
```bash
# Verificar se serviços estão rodando
pm2 status

# Verificar logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Testar configuração do Nginx
sudo nginx -t
```

### **2. Comandos Úteis**

```bash
# Status geral do sistema
/opt/vidconv/monitor.sh

# Reiniciar todos os serviços
pm2 restart all

# Verificar uso de recursos
htop

# Verificar conexões de rede
netstat -tulpn

# Verificar espaço em disco
df -h

# Verificar logs de sistema
journalctl -f
```

### **3. Contatos de Emergência**

- **Administrador do Sistema**: seu-email@empresa.com
- **Provedor de Hospedagem**: suporte@provedor.com
- **Documentação**: https://github.com/seu-usuario/vidconv

---

## ✅ **CHECKLIST FINAL DE DEPLOY**

### **Pré-Deploy**
- [ ] Servidor Debian configurado
- [ ] Dependências instaladas
- [ ] Bancos de dados configurados
- [ ] SSL/HTTPS configurado

### **Deploy**
- [ ] Código clonado
- [ ] Frontend buildado e rodando
- [ ] User Service rodando
- [ ] Notification Service rodando
- [ ] Core Worker rodando
- [ ] Nginx configurado

### **Pós-Deploy**
- [ ] Testes de funcionalidade
- [ ] Monitoramento configurado
- [ ] Backups configurados
- [ ] Documentação atualizada

### **Segurança**
- [ ] Firewall ativo
- [ ] SSL válido
- [ ] Senhas seguras
- [ ] Logs configurados

---

## 📞 **SUPORTE**

Para dúvidas ou problemas:

1. Consulte os logs: `/opt/vidconv/logs/`
2. Execute o script de monitoramento: `/opt/vidconv/monitor.sh`
3. Verifique a documentação técnica
4. Entre em contato com a equipe de desenvolvimento

---

**Documento criado em**: $(date)
**Versão**: 1.0
**Autor**: Equipe VidConv