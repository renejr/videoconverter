# 📧 Notification Service - VidConv Platform

Serviço de notificações da plataforma VidConv, responsável por gerenciar e enviar notificações por email, SMS e outros canais.

## 🏗️ Arquitetura

Este serviço segue os princípios de **Domain-Driven Design (DDD)** e **Microservices**, oferecendo:

- ✅ **Event Bus** para comunicação assíncrona
- ✅ **Email Service** com suporte Gmail SMTP
- ✅ **Template Engine** com Jinja2
- ✅ **Retry Mechanism** para falhas
- ✅ **Delivery Tracking** completo
- ✅ **Rate Limiting** e controle de spam

## 📁 Estrutura do Projeto

```
notification_service/
├── config/
│   ├── __init__.py
│   └── settings.py              # Configurações do serviço
├── database/
│   ├── __init__.py
│   └── connection.py            # Conexão com banco de dados
├── event_bus/
│   ├── __init__.py
│   ├── connection.py            # Conexão Redis
│   ├── handlers.py              # Event handlers
│   ├── publisher.py             # Publicador de eventos
│   └── schemas.py               # Schemas dos eventos
├── models/
│   ├── __init__.py
│   ├── notification.py          # Model de notificação
│   ├── template.py              # Model de template
│   └── delivery_log.py          # Model de log de entrega
├── services/
│   ├── __init__.py
│   ├── email_service.py         # Serviço de email
│   ├── template_service.py      # Serviço de templates
│   └── notification_service.py  # Serviço principal
├── templates/
│   ├── base.html                # Template base
│   ├── welcome.html             # Email de boas-vindas
│   ├── email_verification.html  # Verificação de email
│   └── password_reset.html      # Reset de senha
├── .env.example                 # Exemplo de configuração
├── .env                         # Configurações locais
├── main.py                      # API FastAPI
├── requirements.txt             # Dependências
├── test_gmail.py               # Script de teste Gmail
├── GMAIL_SETUP.md              # Guia de configuração Gmail
└── README.md                   # Este arquivo
```

## 🚀 Configuração Rápida

### 1. Instalar Dependências

```bash
cd notification_service
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados

Certifique-se de que o MySQL está rodando e configure no `.env`:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/vidconv_notifications
```

### 3. Configurar Gmail SMTP

1. **Copie o arquivo de configuração:**
   ```bash
   cp .env.example .env
   ```

2. **Configure suas credenciais Gmail no `.env`:**
   ```env
   SMTP_USER=seu-email@gmail.com
   SMTP_PASSWORD=sua-senha-de-app-gmail
   FROM_EMAIL=seu-email@gmail.com
   FROM_NAME=VidConv Platform
   ```

3. **Siga o guia completo:**
   📖 Consulte [GMAIL_SETUP.md](./GMAIL_SETUP.md) para instruções detalhadas

### 4. Testar Configuração Gmail

```bash
python test_gmail.py
```

### 5. Iniciar o Serviço

```bash
python main.py
```

O serviço estará disponível em: `http://localhost:8002`

## 📧 Configuração Gmail SMTP

### Pré-requisitos

1. **Conta Gmail ativa**
2. **Verificação em 2 etapas habilitada**
3. **Senha de app gerada**

### Passos Rápidos

1. **Habilitar verificação em 2 etapas:**
   - Acesse: https://myaccount.google.com/security
   - Ative "Verificação em 2 etapas"

2. **Gerar senha de app:**
   - Acesse: https://myaccount.google.com/apppasswords
   - Selecione "Email" e "Outro (nome personalizado)"
   - Digite "VidConv Notification Service"
   - Use a senha gerada no `.env`

3. **Configurar `.env`:**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USE_TLS=true
   SMTP_USER=seu-email@gmail.com
   SMTP_PASSWORD=senha-de-app-de-16-caracteres
   ```

📖 **Guia completo:** [GMAIL_SETUP.md](./GMAIL_SETUP.md)

## 🧪 Testes

### Teste de Configuração Gmail

```bash
python test_gmail.py
```

### Teste via API

1. **Informações do Gmail:**
   ```bash
   curl http://localhost:8002/gmail/info
   ```

2. **Teste de conexão:**
   ```bash
   curl -X POST http://localhost:8002/gmail/test-connection
   ```

3. **Envio de email:**
   ```bash
   curl -X POST "http://localhost:8002/test/email?recipient=teste@exemplo.com"
   ```

## 📊 API Endpoints

### Informações do Serviço

- `GET /` - Informações básicas
- `GET /health` - Status de saúde
- `GET /info` - Informações detalhadas

### Gmail SMTP

- `GET /gmail/info` - Configuração Gmail
- `POST /gmail/test-connection` - Teste de conexão
- `POST /test/email` - Envio de teste

### Event Bus

- `POST /test/event` - Publicar evento de teste

## 🔧 Configurações Importantes

### Limites Gmail

- **Limite diário:** 500 emails/dia (contas gratuitas)
- **Limite por minuto:** ~100 emails/minuto
- **Rate limiting:** Configurado automaticamente

### Segurança

- ✅ Senhas de app (não senha principal)
- ✅ TLS/SSL obrigatório
- ✅ Validação de destinatários
- ✅ Rate limiting
- ✅ Logs de auditoria

### Monitoramento

- 📊 Logs detalhados
- 📈 Métricas de entrega
- 🔍 Tracking de status
- ⚠️ Alertas de falha

## 🐛 Troubleshooting

### Erro: "Authentication failed"

1. Verifique se a verificação em 2 etapas está ativa
2. Gere uma nova senha de app
3. Confirme o email e senha no `.env`

### Erro: "Connection timeout"

1. Verifique sua conexão com internet
2. Confirme as configurações SMTP
3. Teste com `python test_gmail.py`

### Erro: "Daily sending quota exceeded"

1. Gmail tem limite de 500 emails/dia
2. Aguarde 24h ou use conta G Suite
3. Implemente queue para distribuir envios

## 📚 Documentação Adicional

- 📖 [GMAIL_SETUP.md](./GMAIL_SETUP.md) - Configuração Gmail completa
- 🔧 [.env.example](./.env.example) - Exemplo de configurações
- 🧪 [test_gmail.py](./test_gmail.py) - Script de teste

## 🤝 Suporte

Para dúvidas ou problemas:

1. Consulte este README
2. Verifique [GMAIL_SETUP.md](./GMAIL_SETUP.md)
3. Execute `python test_gmail.py`
4. Verifique os logs do serviço

---

**VidConv Platform** - Notification Service v1.0.0