# 📧 Configuração do Gmail SMTP - Notification Service

## **🎯 Objetivo**
Configurar o Gmail SMTP para envio de emails no Notification Service da Plataforma VOD.

## **📋 Pré-requisitos**

### 1. **Conta Gmail**
- Conta Gmail ativa
- Verificação em duas etapas habilitada

### 2. **Senha de App do Gmail**
Para usar o Gmail SMTP, você precisa gerar uma **Senha de App** (não use sua senha normal do Gmail).

## **🔧 Passo a Passo - Configuração do Gmail**

### **Etapa 1: Habilitar Verificação em Duas Etapas**

1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. Vá em **Segurança** → **Verificação em duas etapas**
3. Siga as instruções para habilitar

### **Etapa 2: Gerar Senha de App**

1. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Selecione **App**: "Email"
3. Selecione **Dispositivo**: "Outro (nome personalizado)"
4. Digite: "VidConv Notification Service"
5. Clique em **Gerar**
6. **Copie a senha de 16 caracteres** (ex: `abcd efgh ijkl mnop`)

### **Etapa 3: Configurar Variáveis de Ambiente**

Edite o arquivo `.env` no diretório `notification_service`:

```env
# Gmail SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
SMTP_USE_TLS=True
SMTP_USE_SSL=False
SMTP_TIMEOUT=30

# Sender Information
FROM_EMAIL=seu-email@gmail.com
FROM_NAME=VidConv Platform
REPLY_TO=support@vidconv.com
```

## **⚙️ Configurações Técnicas**

### **Configurações do Gmail SMTP:**
- **Host**: `smtp.gmail.com`
- **Porta**: `587` (TLS) ou `465` (SSL)
- **Segurança**: TLS (recomendado)
- **Autenticação**: Obrigatória

### **Limites do Gmail:**
- **Envios por dia**: 500 emails (contas gratuitas)
- **Envios por minuto**: ~100 emails
- **Tamanho máximo**: 25MB por email

## **🧪 Teste da Configuração**

### **1. Teste via API**
```bash
curl -X POST "http://localhost:8001/test/email" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "seu-email@gmail.com",
    "subject": "Teste Gmail SMTP"
  }'
```

### **2. Teste via Python**
```python
import asyncio
from notification_service.services.email_service import EmailService

async def test_gmail():
    email_service = EmailService()
    success = await email_service.send_test_email(
        recipient="seu-email@gmail.com",
        subject="Teste Gmail SMTP"
    )
    print(f"Teste: {'✅ Sucesso' if success else '❌ Falhou'}")

asyncio.run(test_gmail())
```

## **🔒 Segurança**

### **Boas Práticas:**
1. **Nunca** commite a senha de app no Git
2. Use variáveis de ambiente para credenciais
3. Rotacione senhas de app periodicamente
4. Use contas dedicadas para produção

### **Monitoramento:**
- Monitore logs de envio
- Configure alertas para falhas
- Acompanhe limites de envio

## **🚨 Troubleshooting**

### **Erro: "Username and Password not accepted"**
- ✅ Verifique se a verificação em duas etapas está habilitada
- ✅ Use senha de app (não a senha normal)
- ✅ Verifique se o email está correto

### **Erro: "Connection timeout"**
- ✅ Verifique conexão com internet
- ✅ Teste porta 587 ou 465
- ✅ Verifique firewall/proxy

### **Erro: "Daily sending quota exceeded"**
- ✅ Aguarde 24h para reset do limite
- ✅ Considere usar múltiplas contas
- ✅ Implemente rate limiting

## **📊 Monitoramento**

### **Logs Importantes:**
```python
# Logs de sucesso
INFO - Email enviado com sucesso para user@example.com
INFO - Gmail SMTP conectado com sucesso

# Logs de erro
ERROR - Falha no envio de email: Authentication failed
ERROR - Gmail SMTP timeout após 30s
```

### **Métricas:**
- Taxa de entrega
- Tempo de resposta
- Emails por hora/dia
- Taxa de erro

## **🔄 Próximos Passos**

1. ✅ Configurar Gmail SMTP
2. 🔄 Testar envio de emails
3. 🔄 Integrar com User Service
4. 🔄 Implementar monitoramento
5. 🔄 Configurar alertas

---

**📞 Suporte:** Se precisar de ajuda, consulte a documentação do Gmail ou entre em contato com a equipe de desenvolvimento.