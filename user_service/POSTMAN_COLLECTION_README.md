# 📮 Coleção Postman - User Service API

## 📋 Visão Geral

Esta coleção contém todos os endpoints da API do serviço de usuários, organizados por funcionalidade para facilitar os testes e desenvolvimento.

## ✅ Status dos Endpoints

**Todos os endpoints principais estão funcionais e testados:**

### 🟢 Endpoints Funcionais (Status 200)
- ✅ `POST /api/v1/auth/register` - Registro de usuário
- ✅ `POST /api/v1/auth/login/oauth2` - Login OAuth2
- ✅ `GET /api/v1/auth/me` - Dados do usuário autenticado
- ✅ `GET /api/v1/auth/sessions` - Sessões ativas do usuário
- ✅ `GET /api/v1/users/me` - Perfil detalhado do usuário

### 🔧 Correções Implementadas
- **Endpoint `/api/v1/auth/sessions`**: Corrigido erro 500 → Agora retorna status 200
- **Endpoint `/api/v1/users/me`**: Corrigido erro 500 → Agora retorna status 200
- **Schema UserDetailSchema**: Ajustado para corresponder ao modelo User
- **AuthService**: Implementado método `get_user_sessions` funcional

## 🚀 Como Importar a Coleção

### 1. Abrir o Postman
- Abra o aplicativo Postman no seu computador
- Ou acesse [Postman Web](https://web.postman.co/)

### 2. Importar a Coleção
1. Clique em **"Import"** no canto superior esquerdo
2. Selecione **"Upload Files"**
3. Navegue até o arquivo `User_Service_API.postman_collection.json`
4. Clique em **"Import"**

### 3. Configurar Variáveis
A coleção já vem com as variáveis pré-configuradas:
- `base_url`: http://localhost:8000
- `access_token`: (será preenchido automaticamente após login)
- `refresh_token`: (será preenchido automaticamente após login)
- `user_id`: (será preenchido automaticamente após registro)

## 📁 Estrutura da Coleção

### 🔐 **Autenticação**
- **Registrar Usuário**: Cria uma nova conta
- **Login**: Autentica e obtém tokens JWT
- **Login OAuth2**: Compatibilidade com padrão OAuth2
- **Renovar Token**: Renova o access_token usando refresh_token
- **Logout**: Encerra a sessão
- **Meus Dados**: Obtém informações do usuário autenticado

### 🔑 **Gerenciamento de Senhas**
- **Alterar Senha**: Altera senha do usuário autenticado
- **Solicitar Reset**: Solicita token para reset de senha
- **Resetar Senha**: Redefine senha usando token

### 📧 **Verificação de Email**
- **Solicitar Verificação**: Envia email de verificação
- **Verificar Email**: Confirma email usando token

### 🔐 **Autenticação 2FA**
- **Configurar 2FA**: Configura autenticação de dois fatores
- **Verificar 2FA**: Valida código 2FA
- **Desabilitar 2FA**: Remove autenticação de dois fatores

### 🔒 **Gerenciamento de Sessões**
- **Listar Sessões**: Lista todas as sessões ativas
- **Revogar Sessão**: Revoga uma sessão específica
- **Revogar Todas**: Revoga todas as sessões

### 🛡️ **Segurança**
- **Log de Segurança**: Visualiza histórico de atividades

### 👥 **Gerenciamento de Usuários**
- **Criar Usuário**: Cria novo usuário (admin)
- **Meu Perfil**: Obtém perfil do usuário autenticado
- **Obter Usuário**: Busca usuário por ID
- **Atualizar Usuário**: Atualiza dados do usuário
- **Desativar/Reativar**: Gerencia status do usuário

### 🔍 **Busca e Estatísticas**
- **Buscar Usuários**: Busca com filtros
- **Estatísticas**: Métricas do sistema

### 🏥 **Health Check**
- **Health Check**: Verifica status da API
- **API Info**: Informações da API

## 🔄 Fluxo de Teste Recomendado

### 1. **Primeiro Acesso**
```
1. Health Check → Verificar se API está funcionando
2. Registrar Usuário → Criar conta de teste
3. Login → Obter tokens de autenticação
```

### 2. **Testes de Funcionalidade**
```
1. Meus Dados (Auth) → Verificar autenticação
2. Meu Perfil → Verificar dados do usuário
3. Atualizar Usuário → Testar edição de perfil
4. Alterar Senha → Testar mudança de senha
```

### 3. **Testes Avançados**
```
1. Configurar 2FA → Testar autenticação de dois fatores
2. Listar Sessões → Verificar gerenciamento de sessões
3. Buscar Usuários → Testar funcionalidades de admin
4. Log de Segurança → Verificar auditoria
```

## 🔧 Scripts Automáticos

A coleção inclui scripts que executam automaticamente:

### **Pre-request Scripts**
- Adiciona automaticamente o token de autorização nas requisições

### **Test Scripts**
- Salva tokens automaticamente após login
- Salva IDs de usuários criados
- Valida respostas JSON
- Detecta tokens expirados
- Logs informativos no console

## 📝 Variáveis Importantes

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `base_url` | URL base da API | http://localhost:8000 |
| `access_token` | Token JWT para autenticação | eyJhbGciOiJIUzI1NiIs... |
| `refresh_token` | Token para renovação | eyJhbGciOiJIUzI1NiIs... |
| `user_id` | ID do usuário para testes | 123e4567-e89b-12d3... |

## 🚨 Dicas Importantes

### ✅ **Boas Práticas**
- Sempre execute "Health Check" primeiro
- Faça login antes de testar endpoints protegidos
- Use "Renovar Token" quando receber erro 401
- Monitore o console do Postman para logs úteis

### ⚠️ **Cuidados**
- Não compartilhe tokens em ambientes públicos
- Use dados de teste, não dados reais
- Revogue sessões após os testes
- Mantenha a API rodando durante os testes

### 🔄 **Renovação de Token**
Quando o token expirar (erro 401), execute:
1. **Renovar Token** (usando refresh_token)
2. Ou faça **Login** novamente

## 🐛 Solução de Problemas

### **Erro 401 - Unauthorized**
- Verifique se fez login
- Execute "Renovar Token"
- Verifique se o token não expirou

### **Erro 404 - Not Found**
- Verifique se a API está rodando
- Confirme a URL base (http://localhost:8000)
- Verifique se o endpoint existe

### **Erro 422 - Validation Error**
- Verifique os dados enviados no body
- Consulte a documentação Swagger em http://localhost:8000/docs
- Verifique tipos de dados e campos obrigatórios

### **Erro de Conexão**
- Confirme se o servidor está rodando
- Verifique se a porta 8000 está disponível
- Execute: `python main.py` no diretório do projeto

## 📚 Recursos Adicionais

- **Documentação Swagger**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🎯 Próximos Passos

Após importar e testar a coleção:

1. **Personalize** os dados de teste conforme sua necessidade
2. **Crie ambientes** diferentes (dev, staging, prod)
3. **Configure testes automatizados** usando Postman Runner
4. **Integre** com CI/CD para testes contínuos

---

**📞 Suporte**: Se encontrar problemas, verifique os logs do servidor e do Postman para mais detalhes.