# Script de instalação do Node.js para Windows
# Execute este script como Administrador

Write-Host "=== Instalador do Node.js para VidConv Frontend ===" -ForegroundColor Green
Write-Host ""

# Verifica se já está instalado
try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Host "Node.js já está instalado: $nodeVersion" -ForegroundColor Yellow
        Write-Host "Verificando npm..."
        $npmVersion = npm --version 2>$null
        if ($npmVersion) {
            Write-Host "npm já está instalado: $npmVersion" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Instalando dependências do projeto..." -ForegroundColor Green
            npm install
            exit 0
        }
    }
} catch {
    Write-Host "Node.js não encontrado. Iniciando instalação..." -ForegroundColor Yellow
}

# Verifica se o Chocolatey está instalado
try {
    choco --version 2>$null | Out-Null
    $chocoInstalled = $true
} catch {
    $chocoInstalled = $false
}

if (-not $chocoInstalled) {
    Write-Host "Instalando Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Recarrega o PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

Write-Host "Instalando Node.js via Chocolatey..." -ForegroundColor Green
choco install nodejs -y

# Recarrega o PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verifica a instalação
Write-Host ""
Write-Host "Verificando instalação..." -ForegroundColor Green
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "✅ Node.js instalado: $nodeVersion" -ForegroundColor Green
    Write-Host "✅ npm instalado: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro na instalação. Tente reiniciar o PowerShell e executar novamente." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Instalando dependências do projeto..." -ForegroundColor Green
npm install

Write-Host ""
Write-Host "✅ Instalação concluída!" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar o projeto, execute:" -ForegroundColor Yellow
Write-Host "npm run dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "A aplicação estará disponível em: http://localhost:3000" -ForegroundColor Yellow