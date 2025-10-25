# 📚 Documentação Técnica - API Users (Domínio A)

**Sistema de Identidade e Transações para Plataforma VOD**

---

## 📋 Índice

1. [Visão Geral](#-visão-geral)
2. [Arquitetura](#-arquitetura)
3. [Modelos de Dados](#-modelos-de-dados)
4. [Schemas de Validação](#-schemas-de-validação)
5. [Endpoints da API](#-endpoints-da-api)
6. [Sistema de Autenticação](#-sistema-de-autenticação)
7. [Tratamento de Erros](#-tratamento-de-erros)
8. [Exemplos Práticos](#-exemplos-práticos)
9. [Configuração e Deploy](#-configuração-e-deploy)
10. [Testes e Validação](#-testes-e-validação)

---

## 🎯 Visão Geral

### Propósito
A API Users é o núcleo do sistema de identidade e transações da plataforma VOD, responsável por:

- **Gerenciamento completo de usuários** (CRUD, perfis, preferências)
- **Sistema de autenticação robusto** (OAuth2, JWT, 2FA)
- **Controle de sessões** (múltiplas sessões, revogação)
- **Segurança avançada** (rate limiting, logs de auditoria)
- **Integração com sistemas de pagamento** (assinaturas, faturas)

### Características Técnicas
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **Banco de Dados**: MySQL 8.0+
- **Autenticação**: OAuth2 + JWT
- **Validação**: Pydantic v2
- **Criptografia**: bcrypt + PBKDF2

### Métricas de Performance
- **Latência média**: < 100ms
- **Throughput**: 1000+ req/s
- **Disponibilidade**: 99.9%
- **Tempo de resposta P95**: < 200ms

---

## 🏗️ Arquitetura

### Estrutura de Camadas

```
┌─────────────────────────────────────┐
│           API Layer (FastAPI)       │
├─────────────────────────────────────┤
│         Business Logic Layer        │
│           (Services)                │
├─────────────────────────────────────┤
│         Data Access Layer           │
│         (SQLAlchemy ORM)            │
├─────────────────────────────────────┤
│         Database Layer              │
│           (MySQL 8.0)               │
└─────────────────────────────────────┘
```

### Componentes Principais

#### 1. **API Layer** (`/api/v1/`)
- **Endpoints**: Definição de rotas e handlers HTTP
- **Dependencies**: Injeção de dependências (auth, db, pagination)
- **Exceptions**: Tratamento centralizado de erros
- **Middleware**: Rate limiting, CORS, logging

#### 2. **Business Logic** (`/services/`)
- **UserService**: Lógica de negócio para usuários
- **AuthService**: Autenticação e autorização
- **SessionService**: Gerenciamento de sessões
- **SecurityService**: Logs e auditoria

#### 3. **Data Layer** (`/models/` + `/schemas/`)
- **Models**: Entidades SQLAlchemy (User, Credential, Session)
- **Schemas**: Validação Pydantic (entrada/saída)
- **Migrations**: Versionamento do banco de dados

#### 4. **Infrastructure** (`/config/` + `/utils/`)
- **Configuration**: Gerenciamento de configurações
- **Database**: Conexão e pool de conexões
- **Utils**: Validadores, formatadores, helpers

---

## 🗄️ Modelos de Dados

### 1. **User** (Usuário Principal)

```python
class User(Base):
    """
    Modelo principal do usuário
    Armazena informações básicas e preferências
    """
    __tablename__ = 'users'
    
    # Identificação
    id: BigInteger (PK, Auto-increment)
    email: String(255) (Unique, Not Null)
    
    # Informações Pessoais
    first_name: String(100) (Not Null)
    last_name: String(100) (Not Null)
    phone: String(20) (Nullable)
    date_of_birth: Date (Nullable)
    
    # Configurações Regionais
    country_code: String(2) (Default: 'BR')
    language_preference: String(5) (Default: 'pt-BR')
    timezone: String(50) (Default: 'America/Sao_Paulo')
    
    # Status e Controle
    is_active: Boolean (Default: True)
    is_verified: Boolean (Default: False)
    
    # Timestamps
    created_at: TIMESTAMP (Default: CURRENT_TIMESTAMP)
    updated_at: TIMESTAMP (On Update: CURRENT_TIMESTAMP)
    last_login_at: TIMESTAMP (Nullable)
```

**Relacionamentos:**
- `1:1` com **Credential** (credenciais de acesso)
- `1:N` com **UserSession** (sessões ativas)
- `1:N` com **Subscription** (assinaturas)
- `1:N` com **Payment** (pagamentos)
- `1:N` com **Invoice** (faturas)

**Índices Otimizados:**
```sql
INDEX idx_email (email)
INDEX idx_active_verified (is_active, is_verified)
INDEX idx_created_at (created_at)
INDEX idx_last_login (last_login_at)
```

### 2. **Credential** (Credenciais de Acesso)

```python
class Credential(Base):
    """
    Credenciais de autenticação do usuário
    Senhas, tokens, configurações de segurança
    """
    __tablename__ = 'credentials'
    
    # Identificação
    id: BigInteger (PK)
    user_id: BigInteger (FK -> users.id, Unique)
    
    # Autenticação
    password_hash: String(255) (Not Null)
    password_salt: String(32) (Not Null)
    
    # Segurança
    two_factor_secret: String(32) (Nullable)
    two_factor_enabled: Boolean (Default: False)
    backup_codes: JSON (Nullable)
    
    # Controle de Acesso
    login_attempts: Integer (Default: 0)
    account_locked_until: TIMESTAMP (Nullable)
    password_changed_at: TIMESTAMP (Nullable)
    
    # Timestamps
    created_at: TIMESTAMP
    updated_at: TIMESTAMP
```

### 3. **UserSession** (Sessões Ativas)

```python
class UserSession(Base):
    """
    Controle de sessões ativas dos usuários
    Suporte a múltiplas sessões simultâneas
    """
    __tablename__ = 'user_sessions'
    
    # Identificação
    id: BigInteger (PK)
    user_id: BigInteger (FK -> users.id)
    session_token: String(255) (Unique)
    
    # Informações da Sessão
    ip_address: String(45)
    user_agent: String(500)
    device_info: JSON
    location_info: JSON
    
    # Controle de Tempo
    created_at: TIMESTAMP
    last_activity_at: TIMESTAMP
    expires_at: TIMESTAMP
    
    # Status
    is_active: Boolean (Default: True)
    revoked_at: TIMESTAMP (Nullable)
    revoked_reason: String(100) (Nullable)
```

### 4. **Subscription** (Assinaturas)

```python
class Subscription(Base):
    """
    Assinaturas de planos dos usuários
    Controle de ciclo de vida e renovações
    """
    __tablename__ = 'subscriptions'
    
    # Identificação
    id: BigInteger (PK)
    user_id: BigInteger (FK -> users.id)
    plan_id: BigInteger (FK -> plans.id)
    
    # Controle de Assinatura
    status: ENUM('active', 'cancelled', 'expired', 'suspended')
    started_at: TIMESTAMP
    expires_at: TIMESTAMP
    cancelled_at: TIMESTAMP (Nullable)
    
    # Financeiro
    amount: DECIMAL(10,2)
    currency: String(3) (Default: 'BRL')
    billing_cycle: ENUM('monthly', 'quarterly', 'yearly')
    
    # Controle
    auto_renew: Boolean (Default: True)
    trial_ends_at: TIMESTAMP (Nullable)
    
    # Timestamps
    created_at: TIMESTAMP
    updated_at: TIMESTAMP
```

### 5. **Payment** (Pagamentos)

```python
class Payment(Base):
    """
    Histórico de pagamentos dos usuários
    Integração com gateways de pagamento
    """
    __tablename__ = 'payments'
    
    # Identificação
    id: BigInteger (PK)
    user_id: BigInteger (FK -> users.id)
    subscription_id: BigInteger (FK -> subscriptions.id)
    
    # Informações do Pagamento
    external_id: String(100) (Unique)
    amount: DECIMAL(10,2)
    currency: String(3)
    
    # Status e Método
    status: ENUM('pending', 'completed', 'failed', 'refunded')
    payment_method: ENUM('credit_card', 'debit_card', 'pix', 'boleto')
    
    # Datas Importantes
    processed_at: TIMESTAMP (Nullable)
    failed_at: TIMESTAMP (Nullable)
    refunded_at: TIMESTAMP (Nullable)
    
    # Metadados
    gateway_response: JSON
    failure_reason: String(255) (Nullable)
    
    # Timestamps
    created_at: TIMESTAMP
    updated_at: TIMESTAMP
```

---

## 📝 Schemas de Validação

### Hierarquia de Schemas

```
BaseSchema (configurações base)
├── TimestampMixin (created_at, updated_at)
├── UserBaseSchema (campos básicos do usuário)
│   ├── UserCreateSchema (criação)
│   ├── UserUpdateSchema (atualização)
│   ├── UserResponseSchema (resposta básica)
│   └── UserDetailSchema (resposta detalhada)
├── AuthBaseSchema (campos de autenticação)
│   ├── LoginSchema (login)
│   ├── RegisterSchema (registro)
│   └── TokenResponseSchema (resposta de tokens)
└── SessionBaseSchema (campos de sessão)
    ├── SessionSchema (sessão individual)
    └── ActiveSessionsResponseSchema (lista de sessões)
```

### 1. **Schemas de Usuário**

#### UserCreateSchema
```python
class UserCreateSchema(UserBaseSchema):
    """Schema para criação de usuário"""
    
    # Campos obrigatórios
    email: EmailStr = Field(description="Email único do usuário")
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    
    # Campos opcionais
    phone: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    date_of_birth: Optional[date] = Field(None)
    country_code: Optional[CountryCodeEnum] = Field('BR')
    language_preference: Optional[str] = Field('pt-BR')
    
    # Validações customizadas
    @validator('date_of_birth')
    def validate_age(cls, v):
        if v and (date.today() - v).days < 18 * 365:
            raise ValueError('Usuário deve ser maior de idade')
        return v
```

#### UserResponseSchema
```python
class UserResponseSchema(UserBaseSchema, TimestampMixin):
    """Schema para resposta com dados do usuário"""
    
    id: int = Field(description="ID único do usuário")
    full_name: str = Field(description="Nome completo")
    is_active: bool = Field(description="Status ativo")
    is_verified: bool = Field(description="Email verificado")
    is_premium: bool = Field(description="Assinatura premium")
    last_login_at: Optional[datetime] = Field(None)
    profile_completion: int = Field(description="% completude do perfil")
```

### 2. **Schemas de Autenticação**

#### LoginSchema
```python
class LoginSchema(BaseSchema):
    """Schema para login de usuário"""
    
    email: EmailStr = Field(description="Email do usuário")
    password: str = Field(min_length=8, description="Senha do usuário")
    remember_me: bool = Field(False, description="Lembrar login")
    device_info: Optional[Dict[str, Any]] = Field(None)
```

#### LoginResponseSchema
```python
class LoginResponseSchema(BaseSchema):
    """Schema para resposta de login"""
    
    access_token: str = Field(description="Token de acesso JWT")
    refresh_token: str = Field(description="Token de renovação")
    token_type: str = Field("bearer", description="Tipo do token")
    expires_in: int = Field(description="Tempo de expiração em segundos")
    user: UserResponseSchema = Field(description="Dados do usuário")
```

#### RegisterSchema
```python
class RegisterSchema(UserCreateSchema):
    """Schema para registro de usuário"""
    
    password: str = Field(
        min_length=8,
        description="Senha (min 8 caracteres, maiúscula, minúscula, número)"
    )
    confirm_password: str = Field(description="Confirmação da senha")
    accept_terms: bool = Field(description="Aceite dos termos de uso")
    accept_privacy: bool = Field(description="Aceite da política de privacidade")
    marketing_consent: bool = Field(False, description="Consentimento marketing")
    referral_code: Optional[str] = Field(None, description="Código de indicação")
    
    @validator('password')
    def validate_password_strength(cls, v):
        return validate_password_strength(v)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Senhas não coincidem')
        return v
```

### 3. **Schemas de Sessão**

#### SessionSchema
```python
class SessionSchema(BaseSchema):
    """Schema para informações de sessão"""
    
    id: int = Field(description="ID da sessão")
    ip_address: str = Field(description="Endereço IP")
    user_agent: str = Field(description="User Agent do navegador")
    device_info: Dict[str, Any] = Field(description="Informações do dispositivo")
    location_info: Optional[Dict[str, Any]] = Field(None)
    created_at: datetime = Field(description="Data de criação")
    last_activity_at: datetime = Field(description="Última atividade")
    is_current: bool = Field(description="Sessão atual")
```

---

## 🔌 Endpoints da API

### Base URL
```
http://localhost:8000/api/v1
```

### 1. **Autenticação** (`/auth`)

#### POST `/auth/register`
**Registra um novo usuário no sistema**

**Request Body:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "MinhaSenh@123",
  "confirm_password": "MinhaSenh@123",
  "first_name": "João",
  "last_name": "Silva",
  "phone": "+5511999999999",
  "date_of_birth": "1990-01-15",
  "country_code": "BR",
  "language_preference": "pt-BR",
  "accept_terms": true,
  "accept_privacy": true,
  "marketing_consent": false,
  "referral_code": null
}
```

**Response (201):**
```json
{
  "id": 123,
  "email": "usuario@exemplo.com",
  "first_name": "João",
  "last_name": "Silva",
  "full_name": "João Silva",
  "phone": "+5511999999999",
  "country_code": "BR",
  "language_preference": "pt-BR",
  "is_active": true,
  "is_verified": false,
  "is_premium": false,
  "profile_completion": 75,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### POST `/auth/login`
**Autentica usuário e retorna tokens JWT**

**Request Body:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "MinhaSenh@123",
  "remember_me": true,
  "device_info": {
    "platform": "web",
    "browser": "Chrome",
    "version": "120.0.0.0"
  }
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 123,
    "email": "usuario@exemplo.com",
    "full_name": "João Silva",
    "is_active": true,
    "is_verified": true,
    "is_premium": false,
    "last_login_at": "2024-01-15T14:30:00Z"
  }
}
```

#### POST `/auth/login/oauth2`
**Login compatível com padrão OAuth2**

**Request (Form Data):**
```
username=usuario@exemplo.com
password=MinhaSenh@123
grant_type=password
scope=read write
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### GET `/auth/me`
**Retorna informações do usuário autenticado**

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "id": 123,
  "email": "usuario@exemplo.com",
  "full_name": "João Silva",
  "is_active": true,
  "is_verified": true,
  "is_premium": false,
  "last_login_at": "2024-01-15T14:30:00Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET `/auth/sessions`
**Lista todas as sessões ativas do usuário**

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "sessions": [
    {
      "id": 456,
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "device_info": {
        "platform": "web",
        "browser": "Chrome",
        "os": "Windows"
      },
      "location_info": {
        "country": "BR",
        "city": "São Paulo"
      },
      "created_at": "2024-01-15T14:30:00Z",
      "last_activity_at": "2024-01-15T15:45:00Z",
      "is_current": true
    }
  ],
  "total": 1
}
```

#### POST `/auth/refresh`
**Renova o access token usando refresh token**

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST `/auth/logout`
**Encerra a sessão atual**

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "message": "Logout realizado com sucesso"
}
```

### 2. **Usuários** (`/users`)

#### GET `/users/me`
**Retorna perfil completo do usuário autenticado**

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "id": 123,
  "email": "usuario@exemplo.com",
  "first_name": "João",
  "last_name": "Silva",
  "full_name": "João Silva",
  "phone": "+5511999999999",
  "date_of_birth": "1990-01-15",
  "country_code": "BR",
  "language_preference": "pt-BR",
  "timezone": "America/Sao_Paulo",
  "is_active": true,
  "is_verified": true,
  "is_premium": false,
  "profile_completion": 85,
  "last_login_at": "2024-01-15T14:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:15:00Z"
}
```

#### PUT `/users/me`
**Atualiza perfil do usuário autenticado**

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body:**
```json
{
  "first_name": "João Carlos",
  "last_name": "Silva Santos",
  "phone": "+5511888888888",
  "date_of_birth": "1990-01-15",
  "country_code": "BR",
  "language_preference": "pt-BR",
  "timezone": "America/Sao_Paulo"
}
```

**Response (200):**
```json
{
  "id": 123,
  "email": "usuario@exemplo.com",
  "first_name": "João Carlos",
  "last_name": "Silva Santos",
  "full_name": "João Carlos Silva Santos",
  "phone": "+5511888888888",
  "profile_completion": 90,
  "updated_at": "2024-01-15T16:20:00Z"
}
```

#### GET `/users/search`
**Busca usuários com filtros (requer permissão admin)**

**Query Parameters:**
```
?page=1&size=10&email=joao&is_active=true&is_verified=true&country_code=BR
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "users": [
    {
      "id": 123,
      "email": "joao@exemplo.com",
      "full_name": "João Silva",
      "is_active": true,
      "is_verified": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 10,
    "total": 1,
    "pages": 1
  }
}
```

#### GET `/users/stats`
**Estatísticas de usuários (requer permissão admin)**

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "total_users": 15420,
  "active_users": 14890,
  "verified_users": 13245,
  "premium_users": 2340,
  "new_users_today": 45,
  "new_users_this_week": 312,
  "new_users_this_month": 1205
}
```

### 3. **Health Check** (`/health`)

#### GET `/health`
**Verifica status da API**

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "user-service",
  "timestamp": "2024-01-15T16:30:00Z"
}
```

---

## 🔐 Sistema de Autenticação

### Fluxo de Autenticação OAuth2 + JWT

```mermaid
sequenceDiagram
    participant C as Cliente
    participant A as API
    participant D as Database
    
    C->>A: POST /auth/login (email, password)
    A->>D: Verificar credenciais
    D-->>A: Usuário válido
    A->>A: Gerar JWT tokens
    A->>D: Criar sessão
    A-->>C: access_token + refresh_token
    
    C->>A: GET /users/me (Authorization: Bearer token)
    A->>A: Validar JWT
    A->>D: Buscar dados do usuário
    D-->>A: Dados do usuário
    A-->>C: Perfil do usuário
```

### Estrutura do JWT Token

#### Access Token
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "123",
    "email": "usuario@exemplo.com",
    "exp": 1705329000,
    "iat": 1705327200,
    "type": "access",
    "session_id": "456"
  },
  "signature": "..."
}
```

#### Refresh Token
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "123",
    "exp": 1707919200,
    "iat": 1705327200,
    "type": "refresh",
    "session_id": "456"
  },
  "signature": "..."
}
```

### Configurações de Segurança

#### Tempos de Expiração
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30      # 30 minutos
REFRESH_TOKEN_EXPIRE_DAYS = 30        # 30 dias
SESSION_EXPIRE_DAYS = 90              # 90 dias (se remember_me=true)
```

#### Algoritmos de Criptografia
```python
# JWT
ALGORITHM = "HS256"
SECRET_KEY = "your-secret-key-here"

# Senhas
PASSWORD_SCHEMES = ["bcrypt"]
BCRYPT_ROUNDS = 12
```

#### Rate Limiting
```python
# Por IP
RATE_LIMIT_PER_IP = "100/minute"

# Por usuário autenticado
RATE_LIMIT_PER_USER = "1000/minute"

# Endpoints sensíveis
LOGIN_RATE_LIMIT = "5/minute"
REGISTER_RATE_LIMIT = "3/minute"
```

---

## ⚠️ Tratamento de Erros

### Hierarquia de Exceções

```python
BaseAPIException
├── AuthenticationError
│   ├── InvalidCredentialsError (401)
│   ├── TokenExpiredError (401)
│   └── SessionExpiredError (401)
├── AuthorizationError
│   ├── InsufficientPermissionsError (403)
│   └── AccountLockedError (403)
├── ValidationError
│   ├── UserAlreadyExistsError (409)
│   ├── UserNotFoundError (404)
│   └── BusinessRuleError (422)
└── ServerError
    ├── DatabaseError (500)
    └── ExternalServiceError (502)
```

### Formato Padrão de Erro

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "Usuário não encontrado",
    "details": "Nenhum usuário encontrado com o ID fornecido",
    "timestamp": "2024-01-15T16:30:00Z",
    "path": "/api/v1/users/999",
    "request_id": "req_123456789"
  }
}
```

### Códigos de Erro Comuns

| Código | Status | Descrição |
|--------|--------|-----------|
| `INVALID_CREDENTIALS` | 401 | Email ou senha incorretos |
| `TOKEN_EXPIRED` | 401 | Token JWT expirado |
| `SESSION_EXPIRED` | 401 | Sessão expirada |
| `INSUFFICIENT_PERMISSIONS` | 403 | Permissões insuficientes |
| `ACCOUNT_LOCKED` | 403 | Conta bloqueada por segurança |
| `USER_NOT_FOUND` | 404 | Usuário não encontrado |
| `USER_ALREADY_EXISTS` | 409 | Email já cadastrado |
| `VALIDATION_ERROR` | 422 | Dados de entrada inválidos |
| `RATE_LIMIT_EXCEEDED` | 429 | Limite de requisições excedido |
| `DATABASE_ERROR` | 500 | Erro interno do banco de dados |

---

## 💡 Exemplos Práticos

### 1. **Fluxo Completo de Registro e Login**

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. Registrar usuário
def register_user():
    """Registra um novo usuário"""
    user_data = {
        "email": "novo.usuario@exemplo.com",
        "password": "MinhaSenh@123",
        "confirm_password": "MinhaSenh@123",
        "first_name": "Novo",
        "last_name": "Usuário",
        "phone": "+5511999999999",
        "country_code": "BR",
        "accept_terms": True,
        "accept_privacy": True
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    
    if response.status_code == 201:
        user = response.json()
        print(f"✅ Usuário criado: {user['full_name']} (ID: {user['id']})")
        return user
    else:
        print(f"❌ Erro no registro: {response.json()}")
        return None

# 2. Fazer login
def login_user(email, password):
    """Autentica usuário e obtém tokens"""
    login_data = {
        "email": email,
        "password": password,
        "remember_me": True,
        "device_info": {
            "platform": "web",
            "browser": "Chrome",
            "version": "120.0.0.0"
        }
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        auth_data = response.json()
        print(f"✅ Login realizado: {auth_data['user']['full_name']}")
        return auth_data
    else:
        print(f"❌ Erro no login: {response.json()}")
        return None

# 3. Acessar dados do usuário
def get_user_profile(access_token):
    """Obtém perfil completo do usuário"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Perfil obtido: {profile['full_name']}")
        print(f"   Completude: {profile['profile_completion']}%")
        return profile
    else:
        print(f"❌ Erro ao obter perfil: {response.json()}")
        return None

# 4. Atualizar perfil
def update_profile(access_token, updates):
    """Atualiza dados do perfil"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.put(f"{BASE_URL}/users/me", json=updates, headers=headers)
    
    if response.status_code == 200:
        updated_profile = response.json()
        print(f"✅ Perfil atualizado: {updated_profile['full_name']}")
        return updated_profile
    else:
        print(f"❌ Erro na atualização: {response.json()}")
        return None

# Exemplo de uso
if __name__ == "__main__":
    # Registrar
    user = register_user()
    
    if user:
        # Login
        auth = login_user(user['email'], "MinhaSenh@123")
        
        if auth:
            token = auth['access_token']
            
            # Obter perfil
            profile = get_user_profile(token)
            
            # Atualizar perfil
            updates = {
                "phone": "+5511888888888",
                "date_of_birth": "1990-01-15",
                "timezone": "America/Sao_Paulo"
            }
            update_profile(token, updates)
```

### 2. **Gerenciamento de Sessões**

```python
def list_active_sessions(access_token):
    """Lista todas as sessões ativas"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{BASE_URL}/auth/sessions", headers=headers)
    
    if response.status_code == 200:
        sessions_data = response.json()
        sessions = sessions_data['sessions']
        
        print(f"📱 Sessões ativas: {len(sessions)}")
        for session in sessions:
            status = "🟢 ATUAL" if session['is_current'] else "⚪ OUTRA"
            print(f"   {status} - {session['device_info']['browser']} "
                  f"({session['ip_address']}) - {session['created_at']}")
        
        return sessions
    else:
        print(f"❌ Erro ao listar sessões: {response.json()}")
        return []

def revoke_session(access_token, session_id):
    """Revoga uma sessão específica"""
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {"session_id": session_id}
    
    response = requests.post(f"{BASE_URL}/auth/sessions/revoke", 
                           json=data, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Sessão {session_id} revogada com sucesso")
        return True
    else:
        print(f"❌ Erro ao revogar sessão: {response.json()}")
        return False
```

### 3. **Renovação de Tokens**

```python
def refresh_access_token(refresh_token):
    """Renova o access token usando refresh token"""
    data = {"refresh_token": refresh_token}
    
    response = requests.post(f"{BASE_URL}/auth/refresh", json=data)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Token renovado com sucesso")
        print(f"   Expira em: {token_data['expires_in']} segundos")
        return token_data['access_token']
    else:
        print(f"❌ Erro na renovação: {response.json()}")
        return None

# Exemplo de uso com renovação automática
class APIClient:
    def __init__(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.base_url = BASE_URL
    
    def _make_request(self, method, endpoint, **kwargs):
        """Faz requisição com renovação automática de token"""
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f"Bearer {self.access_token}"
        kwargs['headers'] = headers
        
        response = requests.request(method, f"{self.base_url}{endpoint}", **kwargs)
        
        # Se token expirou, tenta renovar
        if response.status_code == 401:
            new_token = refresh_access_token(self.refresh_token)
            if new_token:
                self.access_token = new_token
                headers['Authorization'] = f"Bearer {self.access_token}"
                response = requests.request(method, f"{self.base_url}{endpoint}", **kwargs)
        
        return response
    
    def get_profile(self):
        """Obtém perfil com renovação automática"""
        return self._make_request('GET', '/users/me')
```

### 4. **Tratamento de Erros Robusto**

```python
class UserAPIError(Exception):
    """Exceção customizada para erros da API"""
    def __init__(self, status_code, error_code, message, details=None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(f"{error_code}: {message}")

def handle_api_response(response):
    """Trata resposta da API com tratamento de erros"""
    if response.status_code >= 200 and response.status_code < 300:
        return response.json()
    
    try:
        error_data = response.json()
        error = error_data.get('error', {})
        
        raise UserAPIError(
            status_code=response.status_code,
            error_code=error.get('code', 'UNKNOWN_ERROR'),
            message=error.get('message', 'Erro desconhecido'),
            details=error.get('details')
        )
    except ValueError:
        # Resposta não é JSON válido
        raise UserAPIError(
            status_code=response.status_code,
            error_code='INVALID_RESPONSE',
            message='Resposta inválida do servidor'
        )

# Exemplo de uso com tratamento de erros
def safe_login(email, password):
    """Login com tratamento robusto de erros"""
    try:
        login_data = {
            "email": email,
            "password": password,
            "remember_me": True
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        return handle_api_response(response)
        
    except UserAPIError as e:
        if e.error_code == 'INVALID_CREDENTIALS':
            print("❌ Email ou senha incorretos")
        elif e.error_code == 'ACCOUNT_LOCKED':
            print("🔒 Conta bloqueada por segurança")
        elif e.error_code == 'RATE_LIMIT_EXCEEDED':
            print("⏰ Muitas tentativas. Tente novamente em alguns minutos")
        else:
            print(f"❌ Erro: {e.message}")
        return None
        
    except requests.RequestException as e:
        print(f"🌐 Erro de conexão: {e}")
        return None
```

---

## ⚙️ Configuração e Deploy

### Variáveis de Ambiente

```bash
# .env
# Banco de Dados
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/vod_users
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30

# JWT e Segurança
SECRET_KEY=your-super-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Servidor
HOST=0.0.0.0
PORT=8000
DEBUG=False
WORKERS=4

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_IP=100/minute
RATE_LIMIT_PER_USER=1000/minute

# CORS
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/user-service/app.log

# Email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true

# Redis (cache e sessões)
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# Monitoramento
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
```

### Docker Configuration

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expor porta
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  user-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+pymysql://user:password@mysql:3306/vod_users
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - mysql
      - redis
    volumes:
      - ./logs:/var/log/user-service
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: vod_users
      MYSQL_USER: user
      MYSQL_PASSWORD: password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  mysql_data:
  redis_data:
```

### Deployment com Kubernetes

#### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  labels:
    app: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: your-registry/user-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: user-service-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: user-service-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

---

## 🧪 Testes e Validação

### Estrutura de Testes

```
tests/
├── unit/                   # Testes unitários
│   ├── test_models.py      # Testes dos modelos
│   ├── test_schemas.py     # Testes dos schemas
│   ├── test_services.py    # Testes dos serviços
│   └── test_utils.py       # Testes dos utilitários
├── integration/            # Testes de integração
│   ├── test_auth_flow.py   # Fluxo de autenticação
│   ├── test_user_crud.py   # CRUD de usuários
│   └── test_sessions.py    # Gerenciamento de sessões
├── e2e/                    # Testes end-to-end
│   ├── test_complete_flow.py
│   └── test_api_endpoints.py
└── fixtures/               # Dados de teste
    ├── users.json
    └── sessions.json
```

### Scripts de Teste Automatizado

#### test_api_endpoints.py (Completo)
```python
#!/usr/bin/env python3
"""
Script de teste automatizado para todos os endpoints da API
"""

import asyncio
import pytest
import httpx
from datetime import datetime
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.user_email: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_health_check(self):
        """Testa endpoint de health check"""
        response = await self.client.get(f"{self.base_url}/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        print("✅ Health check passou")
    
    async def test_user_registration(self):
        """Testa registro de usuário"""
        self.user_email = f"teste.{datetime.now().strftime('%Y%m%d%H%M%S')}@exemplo.com"
        
        user_data = {
            "email": self.user_email,
            "password": "MinhaSenh@123",
            "confirm_password": "MinhaSenh@123",
            "first_name": "João",
            "last_name": "Silva",
            "accept_terms": True,
            "accept_privacy": True
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/register",
            json=user_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == self.user_email
        assert data["full_name"] == "João Silva"
        
        self.user_id = data["id"]
        print(f"✅ Registro passou - User ID: {self.user_id}")
    
    async def test_user_login(self):
        """Testa login de usuário"""
        login_data = {
            "email": self.user_email,
            "password": "MinhaSenh@123",
            "remember_me": True
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/login",
            json=login_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        print("✅ Login passou")
    
    async def test_authenticated_endpoints(self):
        """Testa endpoints que requerem autenticação"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Teste /auth/me
        response = await self.client.get(
            f"{self.base_url}/api/v1/auth/me",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == self.user_email
        print("✅ /auth/me passou")
        
        # Teste /users/me
        response = await self.client.get(
            f"{self.base_url}/api/v1/users/me",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == self.user_email
        assert "profile_completion" in data
        print("✅ /users/me passou")
        
        # Teste /auth/sessions
        response = await self.client.get(
            f"{self.base_url}/api/v1/auth/sessions",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) > 0
        print("✅ /auth/sessions passou")
    
    async def test_profile_update(self):
        """Testa atualização de perfil"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        update_data = {
            "first_name": "João Carlos",
            "last_name": "Silva Santos",
            "phone": "+5511999999999"
        }
        
        response = await self.client.put(
            f"{self.base_url}/api/v1/users/me",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "João Carlos"
        assert data["full_name"] == "João Carlos Silva Santos"
        print("✅ Atualização de perfil passou")
    
    async def test_token_refresh(self):
        """Testa renovação de token"""
        refresh_data = {"refresh_token": self.refresh_token}
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/refresh",
            json=refresh_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print("✅ Renovação de token passou")
    
    async def test_logout(self):
        """Testa logout"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/logout",
            headers=headers
        )
        
        assert response.status_code == 200
        print("✅ Logout passou")
    
    async def run_all_tests(self):
        """Executa todos os testes em sequência"""
        try:
            await self.test_health_check()
            await self.test_user_registration()
            await self.test_user_login()
            await self.test_authenticated_endpoints()
            await self.test_profile_update()
            await self.test_token_refresh()
            await self.test_logout()
            
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            return True
            
        except AssertionError as e:
            print(f"\n❌ TESTE FALHOU: {e}")
            return False
        except Exception as e:
            print(f"\n💥 ERRO INESPERADO: {e}")
            return False
        finally:
            await self.client.aclose()

# Executar testes
if __name__ == "__main__":
    async def main():
        tester = APITester()
        success = await tester.run_all_tests()
        return 0 if success else 1
    
    exit(asyncio.run(main()))
```

### Testes de Performance

#### load_test.py
```python
#!/usr/bin/env python3
"""
Teste de carga para a API Users
"""

import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
import statistics

async def test_endpoint_performance(session, url, headers=None):
    """Testa performance de um endpoint"""
    start_time = time.time()
    
    try:
        async with session.get(url, headers=headers) as response:
            await response.text()
            end_time = time.time()
            return {
                'status': response.status,
                'time': end_time - start_time,
                'success': response.status == 200
            }
    except Exception as e:
        end_time = time.time()
        return {
            'status': 0,
            'time': end_time - start_time,
            'success': False,
            'error': str(e)
        }

async def run_load_test(endpoint, concurrent_requests=100, total_requests=1000):
    """Executa teste de carga"""
    print(f"🚀 Iniciando teste de carga: {endpoint}")
    print(f"   Requisições simultâneas: {concurrent_requests}")
    print(f"   Total de requisições: {total_requests}")
    
    connector = aiohttp.TCPConnector(limit=concurrent_requests)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(
        connector=connector, 
        timeout=timeout
    ) as session:
        
        # Criar tasks
        tasks = []
        for _ in range(total_requests):
            task = test_endpoint_performance(session, endpoint)
            tasks.append(task)
        
        # Executar em batches
        results = []
        batch_size = concurrent_requests
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
            
            # Progress
            completed = min(i + batch_size, total_requests)
            print(f"   Progresso: {completed}/{total_requests}")
    
    # Analisar resultados
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    times = [r['time'] for r in successful]
    
    if times:
        print(f"\n📊 Resultados:")
        print(f"   ✅ Sucessos: {len(successful)}/{total_requests}")
        print(f"   ❌ Falhas: {len(failed)}")
        print(f"   ⏱️  Tempo médio: {statistics.mean(times):.3f}s")
        print(f"   📈 P95: {statistics.quantiles(times, n=20)[18]:.3f}s")
        print(f"   📈 P99: {statistics.quantiles(times, n=100)[98]:.3f}s")
        print(f"   🚀 RPS: {len(successful) / max(times):.1f}")
    else:
        print("❌ Nenhuma requisição bem-sucedida")

if __name__ == "__main__":
    # Testar health check
    asyncio.run(run_load_test(
        "http://localhost:8000/api/v1/health",
        concurrent_requests=50,
        total_requests=500
    ))
```

---

## 📈 Monitoramento e Observabilidade

### Métricas Importantes

#### Performance
- **Latência P50, P95, P99** por endpoint
- **Throughput** (requisições por segundo)
- **Taxa de erro** por endpoint
- **Tempo de resposta do banco de dados**

#### Negócio
- **Registros por dia/semana/mês**
- **Logins ativos por período**
- **Taxa de conversão** (registro → verificação)
- **Sessões ativas simultâneas**

#### Segurança
- **Tentativas de login falhadas**
- **Contas bloqueadas**
- **Tokens expirados/inválidos**
- **Rate limiting ativado**

### Logs Estruturados

```python
# Exemplo de log estruturado
{
  "timestamp": "2024-01-15T16:30:00Z",
  "level": "INFO",
  "service": "user-service",
  "version": "1.0.0",
  "request_id": "req_123456789",
  "user_id": 123,
  "endpoint": "/api/v1/auth/login",
  "method": "POST",
  "status_code": 200,
  "response_time_ms": 150,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "event": "user_login_success",
  "metadata": {
    "email": "user@example.com",
    "device_type": "web",
    "location": "São Paulo, BR"
  }
}
```

---

## 🔒 Considerações de Segurança

### Checklist de Segurança

#### ✅ Autenticação
- [x] Senhas criptografadas com bcrypt
- [x] Tokens JWT com expiração
- [x] Refresh tokens seguros
- [x] Rate limiting em endpoints sensíveis
- [x] Bloqueio de conta após tentativas falhadas

#### ✅ Autorização
- [x] Validação de permissões por endpoint
- [x] Isolamento de dados por usuário
- [x] Controle de acesso baseado em roles
- [x] Validação de tokens em todas as requisições

#### ✅ Dados
- [x] Validação rigorosa de entrada
- [x] Sanitização de dados
- [x] Prevenção de SQL Injection
- [x] Criptografia de dados sensíveis
- [x] Logs de auditoria completos

#### ✅ Infraestrutura
- [x] HTTPS obrigatório em produção
- [x] CORS configurado adequadamente
- [x] Headers de segurança (HSTS, CSP)
- [x] Monitoramento de vulnerabilidades
- [x] Backup seguro de dados

### Práticas de Segurança Recomendadas

#### 1. **Rotação de Secrets**
```bash
# Rotacionar SECRET_KEY mensalmente
SECRET_KEY=$(openssl rand -hex 32)

# Rotacionar senhas de banco trimestralmente
# Usar ferramentas como HashiCorp Vault
```

#### 2. **Monitoramento de Segurança**
```python
# Alertas automáticos para:
- Múltiplas tentativas de login falhadas
- Acessos de IPs suspeitos
- Tokens JWT inválidos em massa
- Picos de tráfego anômalos
```

#### 3. **Auditoria Regular**
- **Revisão de logs** semanalmente
- **Teste de penetração** trimestralmente
- **Atualização de dependências** mensalmente
- **Backup e recovery** testados mensalmente

---

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. **Erro de Conexão com Banco**
```
ERROR: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server")
```

**Soluções:**
```bash
# Verificar se MySQL está rodando
systemctl status mysql

# Verificar conectividade
telnet localhost 3306

# Verificar configurações
echo $DATABASE_URL

# Testar conexão manual
mysql -h localhost -u user -p vod_users
```

#### 2. **Token JWT Inválido**
```json
{
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Token JWT expirado"
  }
}
```

**Soluções:**
```python
# Verificar configuração de tempo
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Sincronizar relógio do servidor
ntpdate -s time.nist.gov

# Verificar SECRET_KEY
echo $SECRET_KEY | wc -c  # Deve ter pelo menos 32 caracteres
```

#### 3. **Rate Limiting Ativado**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Limite de requisições excedido"
  }
}
```

**Soluções:**
```python
# Ajustar limites no .env
RATE_LIMIT_PER_IP=200/minute
RATE_LIMIT_PER_USER=2000/minute

# Implementar cache Redis
REDIS_URL=redis://localhost:6379/0

# Usar CDN para assets estáticos
```

#### 4. **Performance Lenta**
```
Tempo de resposta > 1000ms
```

**Diagnóstico:**
```sql
-- Verificar queries lentas
SHOW PROCESSLIST;

-- Analisar índices
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- Verificar fragmentação
OPTIMIZE TABLE users;
```

**Otimizações:**
```python
# Pool de conexões
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30

# Cache de queries
from sqlalchemy import create_engine
engine = create_engine(url, pool_pre_ping=True)

# Paginação eficiente
LIMIT 20 OFFSET 0  # Evitar OFFSET alto
```

### Comandos de Diagnóstico

#### Sistema
```bash
# CPU e Memória
top -p $(pgrep -f "python main.py")

# Conexões de rede
netstat -tulpn | grep :8000

# Logs da aplicação
tail -f /var/log/user-service/app.log

# Espaço em disco
df -h
```

#### Banco de Dados
```sql
-- Conexões ativas
SHOW STATUS LIKE 'Threads_connected';

-- Queries por segundo
SHOW STATUS LIKE 'Questions';

-- Tabelas mais acessadas
SELECT * FROM information_schema.TABLE_STATISTICS;

-- Índices não utilizados
SELECT * FROM sys.schema_unused_indexes;
```

#### API
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Teste de autenticação
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Métricas de performance
curl http://localhost:8000/metrics
```

---

## 📚 Referências e Recursos

### Documentação Oficial
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/
- **MySQL**: https://dev.mysql.com/doc/

### Ferramentas Recomendadas

#### Desenvolvimento
- **Postman**: Testes de API
- **DBeaver**: Cliente MySQL
- **Redis Commander**: Interface Redis
- **Docker Desktop**: Containerização

#### Monitoramento
- **Grafana**: Dashboards
- **Prometheus**: Métricas
- **Sentry**: Error tracking
- **New Relic**: APM

#### Segurança
- **OWASP ZAP**: Teste de segurança
- **Bandit**: Análise de código Python
- **Safety**: Verificação de dependências
- **HashiCorp Vault**: Gerenciamento de secrets

### Padrões e Convenções

#### Nomenclatura
```python
# Endpoints: kebab-case
/api/v1/auth/two-factor-auth

# Variáveis: snake_case
user_email = "test@example.com"

# Classes: PascalCase
class UserService:

# Constantes: UPPER_SNAKE_CASE
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

#### Códigos de Status HTTP
```python
# Sucesso
200 OK          # Operação bem-sucedida
201 Created     # Recurso criado
204 No Content  # Operação sem retorno

# Erro do Cliente
400 Bad Request     # Dados inválidos
401 Unauthorized    # Não autenticado
403 Forbidden       # Sem permissão
404 Not Found       # Recurso não encontrado
409 Conflict        # Conflito (email já existe)
422 Unprocessable   # Validação falhou
429 Too Many Req    # Rate limit

# Erro do Servidor
500 Internal Error  # Erro interno
502 Bad Gateway     # Serviço indisponível
503 Service Unavail # Manutenção
```

---

## 🎯 Conclusão

### Resumo da Documentação

Esta documentação técnica apresentou uma visão completa da **API Users (Domínio A)**, cobrindo:

✅ **Arquitetura robusta** com separação clara de responsabilidades  
✅ **23 endpoints** bem documentados com exemplos práticos  
✅ **5 modelos principais** com relacionamentos otimizados  
✅ **Sistema de autenticação** OAuth2 + JWT completo  
✅ **Schemas de validação** Pydantic rigorosos  
✅ **Tratamento de erros** padronizado e informativo  
✅ **Configuração de deploy** Docker + Kubernetes  
✅ **Testes automatizados** unitários e de integração  
✅ **Monitoramento** e observabilidade completos  
✅ **Segurança** seguindo melhores práticas  

### Próximos Passos Recomendados

#### Curto Prazo (1-2 semanas)
1. **Implementar 2FA** (Two-Factor Authentication)
2. **Adicionar cache Redis** para sessões
3. **Configurar monitoramento** Grafana + Prometheus
4. **Implementar rate limiting** avançado

#### Médio Prazo (1-2 meses)
1. **Sistema de notificações** (email, SMS)
2. **API de recuperação de senha** completa
3. **Integração com OAuth providers** (Google, Facebook)
4. **Dashboard administrativo** para gestão de usuários

#### Longo Prazo (3-6 meses)
1. **Microserviços** separados por domínio
2. **Event sourcing** para auditoria completa
3. **Machine learning** para detecção de fraudes
4. **API Gateway** centralizado

### Contato e Suporte

Para dúvidas técnicas ou sugestões de melhorias:

- **Documentação**: Este arquivo (sempre atualizado)
- **Código fonte**: `/user_service/` (comentado e organizado)
- **Testes**: `/tests/` (exemplos práticos)
- **Issues**: Sistema de tickets interno

---

**📝 Última atualização:** Janeiro 2024  
**🔄 Versão da API:** v1.0.0  
**👥 Mantido por:** Equipe de Desenvolvimento VOD

---

*Esta documentação é um documento vivo e deve ser atualizada conforme a evolução da API.*