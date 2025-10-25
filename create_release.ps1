# Script para criar release no GitHub
# Uso: powershell -ExecutionPolicy Bypass -File .\create_release.ps1

$repo = "renejr/videoconverter"
$tag = "v2.3.0"
$name = "Release v2.3.0 - Sistema de Atualizacoes Automaticas"
$body = @"
## Novidades da Versao 2.3.0

### Sistema de Atualizacoes Automaticas
- Verificacao automatica de versoes via GitHub API
- Download e instalacao inteligente de atualizacoes
- Sistema de reinicializacao pos-atualizacao
- Widget de atualizacao integrado na interface
- Verificacao de integridade e seguranca
- Testes abrangentes com 100% de cobertura

### Melhorias Tecnicas
- Implementado sistema completo de atualizacoes automaticas
- Verificacao inteligente de versoes via GitHub API
- Download e instalacao automatica de atualizacoes
- Sistema de reinicializacao inteligente pos-atualizacao
- Widget de atualizacao integrado na interface
- Verificacao de integridade e seguranca
- Testes abrangentes com 100% de cobertura
- Documentacao completa no README.md

### Arquivos Principais
- utils/updater.py - Sistema principal de atualizacoes
- gui/update_widget.py - Widget de interface para atualizacoes
- test_*_update*.py - Testes abrangentes do sistema
- README.md - Documentacao atualizada

### Como Usar
O sistema de atualizacoes funciona automaticamente:
1. Verifica atualizacoes na inicializacao
2. Notifica quando ha novas versoes disponiveis
3. Permite download e instalacao com um clique
4. Reinicia automaticamente apos a atualizacao

### Requisitos
- Python 3.8+
- Conexao com internet para verificacao de atualizacoes
- Permissoes de escrita no diretorio da aplicacao
"@

# Criar o JSON para o release
$releaseData = @{
    tag_name = $tag
    target_commitish = "feature/v2.3-new-features"
    name = $name
    body = $body
    draft = $false
    prerelease = $false
} | ConvertTo-Json -Depth 10

# URL da API
$url = "https://api.github.com/repos/$repo/releases"

Write-Host "Criando release $tag no repositorio $repo..." -ForegroundColor Green

try {
    # Fazer a requisicao POST para criar o release
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $releaseData -ContentType "application/json"
    
    Write-Host "Release criado com sucesso!" -ForegroundColor Green
    Write-Host "URL do Release: $($response.html_url)" -ForegroundColor Cyan
    Write-Host "Tag: $($response.tag_name)" -ForegroundColor Yellow
    Write-Host "Criado em: $($response.created_at)" -ForegroundColor Yellow
    
    # Salvar informacoes do release
    $response | ConvertTo-Json -Depth 10 | Out-File "release_info.json" -Encoding UTF8
    Write-Host "Informacoes salvas em release_info.json" -ForegroundColor Blue
    
} catch {
    Write-Host "Erro ao criar release:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Resposta da API: $responseBody" -ForegroundColor Yellow
    }
}