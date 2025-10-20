# VidConv Frontend

Interface web moderna desenvolvida em React + Next.js para consumir a API do User Service.

## 🚀 Tecnologias Utilizadas

- **Next.js 14** - Framework React com App Router
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Framework CSS utilitário
- **Axios** - Cliente HTTP para API
- **React Hook Form** - Gerenciamento de formulários
- **React Hot Toast** - Notificações
- **Lucide React** - Ícones
- **js-cookie** - Gerenciamento de cookies

## 📋 Pré-requisitos

- Node.js 18+ 
- npm ou yarn
- Backend User Service rodando (porta 8000)

## 🔧 Instalação

### 1. Instalar Node.js

Se você não tem o Node.js instalado, baixe e instale a partir de:
https://nodejs.org/

### 2. Instalar dependências

```bash
cd frontend
npm install
```

### 3. Configurar variáveis de ambiente

O arquivo `.env.local` já está configurado com as seguintes variáveis:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=VidConv Portal
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_JWT_SECRET=your-super-secret-jwt-key-here
```

## 🚀 Executando a aplicação

### Modo de desenvolvimento

```bash
npm run dev
```

A aplicação estará disponível em: http://localhost:3000

### Build para produção

```bash
npm run build
npm start
```

## 📁 Estrutura do Projeto

```
frontend/
├── src/
│   ├── app/                    # Páginas (App Router)
│   │   ├── auth/              # Páginas de autenticação
│   │   │   ├── login/         # Página de login
│   │   │   └── register/      # Página de registro
│   │   ├── dashboard/         # Dashboard do usuário
│   │   ├── profile/           # Página de perfil
│   │   ├── globals.css        # Estilos globais
│   │   ├── layout.tsx         # Layout raiz
│   │   └── page.tsx           # Página inicial
│   ├── components/            # Componentes reutilizáveis
│   │   ├── ui/               # Componentes de UI
│   │   │   ├── Button.tsx    # Componente Button
│   │   │   ├── Input.tsx     # Componente Input
│   │   │   ├── Modal.tsx     # Componente Modal
│   │   │   └── index.ts      # Exportações
│   │   └── ProtectedRoute.tsx # Proteção de rotas
│   ├── contexts/             # Contextos React
│   │   └── AuthContext.tsx   # Contexto de autenticação
│   ├── hooks/                # Hooks customizados
│   │   └── useAuth.ts        # Hook de autenticação
│   ├── lib/                  # Utilitários e configurações
│   │   ├── api.ts            # Cliente da API
│   │   └── utils.ts          # Funções utilitárias
│   ├── types/                # Definições TypeScript
│   │   └── index.ts          # Tipos da aplicação
│   └── middleware.ts         # Middleware de rotas
├── .env.local                # Variáveis de ambiente
├── next.config.js            # Configuração do Next.js
├── tailwind.config.js        # Configuração do Tailwind
├── tsconfig.json             # Configuração do TypeScript
└── package.json              # Dependências e scripts
```

## 🔐 Funcionalidades

### Autenticação
- ✅ Login com email/senha
- ✅ Registro de novos usuários
- ✅ Gerenciamento de tokens JWT
- ✅ Refresh automático de tokens
- ✅ Logout seguro

### Dashboard
- ✅ Informações do perfil do usuário
- ✅ Status da conta (ativo, verificado)
- ✅ Gerenciamento de sessões ativas
- ✅ Estatísticas da conta

### Perfil
- ✅ Edição de informações pessoais
- ✅ Alteração de senha
- ✅ Validação de formulários
- ✅ Feedback visual

### Segurança
- ✅ Proteção de rotas
- ✅ Middleware de autenticação
- ✅ Interceptadores de requisições
- ✅ Tratamento de erros

## 🎨 Design

- **Design responsivo** - Funciona em desktop, tablet e mobile
- **Tema moderno** - Interface limpa e profissional
- **Feedback visual** - Loading states, notificações e validações
- **Acessibilidade** - Componentes acessíveis

## 🔗 Integração com Backend

A aplicação se conecta com o User Service API através de:

- **Base URL**: `http://localhost:8000`
- **Autenticação**: JWT tokens via cookies
- **Interceptadores**: Refresh automático de tokens
- **Tratamento de erros**: Redirecionamento automático para login

### Endpoints utilizados:

- `POST /auth/login` - Login
- `POST /auth/register` - Registro
- `POST /auth/refresh` - Refresh token
- `POST /auth/logout` - Logout
- `GET /users/me` - Dados do usuário
- `PUT /users/me` - Atualizar perfil
- `POST /users/change-password` - Alterar senha
- `GET /users/sessions` - Sessões ativas
- `DELETE /users/sessions/{id}` - Revogar sessão

## 🧪 Testando a aplicação

1. **Certifique-se que o backend está rodando**:
   ```bash
   cd ../user_service
   python main.py
   ```

2. **Inicie o frontend**:
   ```bash
   npm run dev
   ```

3. **Acesse**: http://localhost:3000

4. **Teste o fluxo**:
   - Registre um novo usuário
   - Faça login
   - Explore o dashboard
   - Edite o perfil
   - Gerencie sessões

## 🐛 Solução de Problemas

### Erro de conexão com API
- Verifique se o backend está rodando na porta 8000
- Confirme a URL da API no `.env.local`

### Problemas de autenticação
- Limpe os cookies do navegador
- Verifique se os tokens JWT estão sendo salvos

### Erros de build
- Delete `node_modules` e `.next`
- Execute `npm install` novamente
- Verifique se todas as dependências estão instaladas

## 📝 Scripts Disponíveis

```bash
npm run dev          # Inicia em modo desenvolvimento
npm run build        # Gera build de produção
npm start            # Inicia aplicação em produção
npm run lint         # Executa linter
npm run type-check   # Verifica tipos TypeScript
```

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.