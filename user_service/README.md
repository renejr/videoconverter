# User Service API

Sistema de Identidade e Transações - Domínio A

## 📋 Descrição

API REST completa para gerenciamento de usuários, autenticação e autorização, desenvolvida com FastAPI, SQLAlchemy e MySQL. Este serviço fornece funcionalidades robustas de autenticação OAuth2, gerenciamento de sessões e operações CRUD de usuários.

## 🚀 Funcionalidades

### ✅ Autenticação e Autorização
- **Registro de usuários** com validação de dados
- **Login OAuth2** compatível com padrões de mercado
- **Gerenciamento de sessões** ativas
- **Tokens JWT** para autenticação
- **Refresh tokens** para renovação automática
- **Autenticação de dois fatores** (2FA) - preparado
- **Reset de senha** via email - preparado

### ✅ Gerenciamento de Usuários
- **Perfil completo** do usuário autenticado
- **Operações CRUD** de usuários
- **Validação de dados** robusta
- **Campos personalizáveis** (país, idioma, timezone)

### ✅ Segurança
- **Criptografia bcrypt** para senhas
- **Rate limiting** para proteção contra ataques
- **Validação de tokens** JWT
- **Logs de segurança** - preparado

## 🛠️ Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para Python
- **MySQL** - Banco de dados relacional
- **Pydantic** - Validação de dados
- **JWT** - Tokens de autenticação
- **bcrypt** - Criptografia de senhas
- **Uvicorn** - Servidor ASGI

## 📦 Instalação

### Pré-requisitos
- Python 3.8+
- MySQL 8.0+
- pip

### Configuração

1. **Clone o repositório**
```bash
git clone <repository-url>
cd user_service
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

4. **Configure o banco de dados**
```bash
# Execute o script SQL para criar o banco
mysql -u root -p < database/schema.sql
```

5. **Inicie o servidor**
```bash
python main.py
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```env
# Banco de Dados
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/play

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Servidor
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 📚 API Endpoints

### 🔐 Autenticação

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| POST | `/api/v1/auth/register` | Registrar novo usuário | ✅ |
| POST | `/api/v1/auth/login` | Login padrão | ✅ |
| POST | `/api/v1/auth/login/oauth2` | Login OAuth2 | ✅ |
| GET | `/api/v1/auth/me` | Informações do usuário autenticado | ✅ |
| GET | `/api/v1/auth/sessions` | Listar sessões ativas | ✅ |
| POST | `/api/v1/auth/logout` | Logout | ✅ |
| POST | `/api/v1/auth/refresh` | Renovar token | ✅ |

### 👤 Usuários

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| GET | `/api/v1/users/me` | Perfil completo do usuário | ✅ |
| PUT | `/api/v1/users/me` | Atualizar perfil | ✅ |
| GET | `/api/v1/users` | Listar usuários (admin) | ✅ |
| GET | `/api/v1/users/{id}` | Obter usuário por ID (admin) | ✅ |

## 🧪 Testes

### Scripts de Teste Disponíveis

```bash
# Teste completo dos endpoints
python test_auth_endpoints.py

# Teste específico do OAuth2
python test_oauth2_login.py

# Teste de login específico
python test_login_specific.py
```

### Exemplo de Uso

```python
import requests

# Registrar usuário
response = requests.post("http://localhost:8000/api/v1/auth/register", json={
    "email": "usuario@exemplo.com",
    "password": "MinhaSenh@123",
    "confirm_password": "MinhaSenh@123",
    "first_name": "João",
    "last_name": "Silva",
    "accept_terms": True,
    "accept_privacy": True
})

# Login OAuth2
response = requests.post("http://localhost:8000/api/v1/auth/login/oauth2", data={
    "username": "usuario@exemplo.com",
    "password": "MinhaSenh@123"
})

token = response.json()["access_token"]

# Acessar endpoint protegido
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/v1/auth/me", headers=headers)
```

## 🔄 Correções Implementadas

### ✅ Problemas Resolvidos

1. **Endpoint `/api/v1/auth/sessions`**
   - **Problema**: Erro 500 ao tentar converter dicionário para SessionSchema
   - **Solução**: Implementado método `get_user_sessions` e corrigida conversão de schemas
   - **Status**: ✅ Funcionando

2. **Endpoint `/api/v1/users/me`**
   - **Problema**: Erro 500 por campos inexistentes no modelo User
   - **Solução**: Ajustado UserDetailSchema para corresponder aos campos do modelo
   - **Status**: ✅ Funcionando

3. **Login OAuth2**
   - **Problema**: Erro de validação no campo `last_name`
   - **Solução**: Corrigido script de teste e validação
   - **Status**: ✅ Funcionando

## 📊 Estrutura do Projeto

```
user_service/
├── api/                    # Endpoints da API
│   ├── dependencies.py     # Dependências (auth, db, etc.)
│   ├── exceptions.py       # Exceções customizadas
│   └── v1/                 # Versão 1 da API
│       └── endpoints/      # Endpoints organizados por funcionalidade
├── config/                 # Configurações
├── database/              # Conexão e schemas do banco
├── models/                # Modelos SQLAlchemy
├── schemas/               # Schemas Pydantic
├── services/              # Lógica de negócio
├── utils/                 # Utilitários
└── tests/                 # Testes automatizados
```

## 🔒 Segurança

- **Senhas criptografadas** com bcrypt
- **Tokens JWT** com expiração configurável
- **Rate limiting** para proteção contra ataques
- **Validação rigorosa** de dados de entrada
- **Headers de segurança** configurados

## 📈 Performance

- **Conexão otimizada** com MySQL
- **Queries eficientes** com SQLAlchemy
- **Cache de sessões** (preparado)
- **Paginação** em listagens

## 🚧 Próximas Funcionalidades

- [ ] Sistema completo de gerenciamento de sessões
- [ ] Implementação de 2FA
- [ ] Sistema de notificações por email
- [ ] Logs de auditoria
- [ ] Cache Redis
- [ ] Testes unitários completos

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do servidor
2. Execute os scripts de teste
3. Consulte a documentação da API
4. Verifique as configurações do banco de dados

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

**Desenvolvido com ❤️ usando FastAPI e Python**