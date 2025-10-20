# Guia de Instalação - VidConv Frontend

## 🚨 Node.js não encontrado!

Para executar o frontend, você precisa instalar o Node.js primeiro.

## 📥 Opção 1: Instalação Automática (Recomendada)

Execute o script de instalação como **Administrador**:

```powershell
# Abra o PowerShell como Administrador e execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\install-nodejs.ps1
```

## 📥 Opção 2: Instalação Manual

### 1. Baixar Node.js

Acesse: https://nodejs.org/
- Baixe a versão **LTS** (recomendada)
- Escolha a versão para Windows (x64)

### 2. Instalar Node.js

- Execute o instalador baixado
- Siga as instruções padrão
- **Importante**: Marque a opção "Add to PATH"

### 3. Verificar Instalação

Abra um novo PowerShell e execute:

```powershell
node --version
npm --version
```

### 4. Instalar Dependências

```powershell
cd frontend
npm install
```

### 5. Executar Aplicação

```powershell
npm run dev
```

## 📥 Opção 3: Usando Chocolatey

Se você tem o Chocolatey instalado:

```powershell
choco install nodejs
```

## 📥 Opção 4: Usando Winget

Se você tem o Windows Package Manager:

```powershell
winget install OpenJS.NodeJS
```

## 🚀 Após a Instalação

1. **Reinicie o PowerShell** para carregar o PATH
2. Navegue até a pasta do frontend:
   ```powershell
   cd e:\pyProjs\vidconv\frontend
   ```
3. Instale as dependências:
   ```powershell
   npm install
   ```
4. Inicie o servidor de desenvolvimento:
   ```powershell
   npm run dev
   ```
5. Acesse: http://localhost:3000

## 🔧 Solução de Problemas

### "node não é reconhecido"
- Reinicie o PowerShell/CMD
- Verifique se o Node.js foi adicionado ao PATH
- Reinstale o Node.js marcando "Add to PATH"

### Erro de permissão no PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Erro de rede durante npm install
```powershell
npm config set registry https://registry.npmjs.org/
npm install
```

## 📋 Requisitos do Sistema

- **Windows 10/11**
- **Node.js 18+** (LTS recomendada)
- **npm 9+** (incluído com Node.js)
- **4GB RAM** (mínimo)
- **Conexão com internet** (para download de dependências)

## 🆘 Precisa de Ajuda?

Se você encontrar problemas:

1. Verifique se o backend está rodando (porta 8000)
2. Confirme que o Node.js está instalado corretamente
3. Tente limpar o cache do npm: `npm cache clean --force`
4. Delete `node_modules` e execute `npm install` novamente