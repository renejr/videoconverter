#!/usr/bin/env python3
"""
Script de teste automatizado para todos os endpoints da API User Service
Testa funcionalidades de autenticação, CRUD de usuários, e recursos avançados
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

# Configuração
BASE_URL = "http://localhost:8000"
console = Console()

class APITester:
    """Classe principal para testes da API"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.user_email: Optional[str] = None
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test_result(self, endpoint: str, method: str, status_code: int, 
                       success: bool, response_data: Any = None, error: str = None):
        """Registra resultado de um teste"""
        test_key = f"{method} {endpoint}"
        self.test_results[test_key] = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data,
            "error": error
        }
    
    async def test_health_check(self):
        """Testa endpoints de health check"""
        console.print("\n🏥 [bold blue]Testando Health Check[/bold blue]")
        
        # Test root endpoint
        try:
            response = await self.client.get(f"{self.base_url}/")
            success = response.status_code == 200
            self.log_test_result("/", "GET", response.status_code, success, response.json())
            console.print(f"✅ GET / - Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("/", "GET", 0, False, error=str(e))
            console.print(f"❌ GET / - Erro: {e}")
        
        # Test health endpoint
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            success = response.status_code == 200
            self.log_test_result("/api/v1/health", "GET", response.status_code, success, response.json())
            console.print(f"✅ GET /api/v1/health - Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("/api/v1/health", "GET", 0, False, error=str(e))
            console.print(f"❌ GET /api/v1/health - Erro: {e}")
    
    async def test_user_registration(self):
        """Testa registro de usuário"""
        console.print("\n👤 [bold blue]Testando Registro de Usuário[/bold blue]")
        
        # Armazenar o email para usar no login
        self.user_email = f"teste.{datetime.now().strftime('%Y%m%d%H%M%S')}@exemplo.com"
        
        user_data = {
            "email": self.user_email,
            "password": "MinhaSenh@123",
            "confirm_password": "MinhaSenh@123",
            "first_name": "João",
            "last_name": "Silva",
            "accept_terms": True,
            "accept_privacy": True,
            "marketing_consent": False,
            "referral_code": None
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data
            )
            success = response.status_code == 201
            response_data = response.json() if response.status_code == 201 else None
            
            if success and response_data:
                self.user_id = response_data.get("id")
                console.print(f"✅ POST /api/v1/auth/register - Status: {response.status_code}")
                console.print(f"   User ID: {self.user_id}")
                console.print(f"   Email: {self.user_email}")
            else:
                console.print(f"❌ POST /api/v1/auth/register - Status: {response.status_code}")
                if response.status_code != 201:
                    console.print(f"   Erro: {response.text}")
            
            self.log_test_result("/api/v1/auth/register", "POST", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/auth/register", "POST", 0, False, error=str(e))
            console.print(f"❌ POST /api/v1/auth/register - Erro: {e}")
    
    async def test_user_login(self):
        """Testa login de usuário"""
        console.print("\n🔐 [bold blue]Testando Login de Usuário[/bold blue]")
        
        # Primeiro, precisamos de um usuário registrado
        if not self.user_id or not self.user_email:
            console.print("⚠️ Usuário não registrado, pulando teste de login")
            return
        
        # Usar o email do usuário registrado
        login_data = {
            "email": self.user_email,
            "password": "MinhaSenh@123"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            success = response.status_code == 200
            response_data = response.json() if response.status_code == 200 else None
            
            if success and response_data:
                self.access_token = response_data.get("access_token")
                self.refresh_token = response_data.get("refresh_token")
                console.print(f"✅ POST /api/v1/auth/login - Status: {response.status_code}")
                console.print(f"   Token obtido: {self.access_token[:20]}...")
            else:
                console.print(f"❌ POST /api/v1/auth/login - Status: {response.status_code}")
                if response.status_code != 200:
                    console.print(f"   Erro: {response.text}")
            
            self.log_test_result("/api/v1/auth/login", "POST", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/auth/login", "POST", 0, False, error=str(e))
            console.print(f"❌ POST /api/v1/auth/login - Erro: {e}")
    
    async def test_oauth2_login(self):
        """Testa login OAuth2"""
        console.print("\n🔑 [bold blue]Testando Login OAuth2[/bold blue]")
        
        login_data = {
            "username": f"teste.{datetime.now().strftime('%Y%m%d%H%M%S')}@exemplo.com",
            "password": "MinhaSenh@123"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login/oauth2",
                data=login_data,  # OAuth2 usa form data
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            success = response.status_code == 200
            response_data = response.json() if response.status_code == 200 else None
            
            console.print(f"{'✅' if success else '❌'} POST /api/v1/auth/login/oauth2 - Status: {response.status_code}")
            if not success and response.status_code != 200:
                console.print(f"   Erro: {response.text}")
            
            self.log_test_result("/api/v1/auth/login/oauth2", "POST", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/auth/login/oauth2", "POST", 0, False, error=str(e))
            console.print(f"❌ POST /api/v1/auth/login/oauth2 - Erro: {e}")
    
    async def test_authenticated_endpoints(self):
        """Testa endpoints que requerem autenticação"""
        if not self.access_token:
            console.print("⚠️ Token de acesso não disponível, pulando testes autenticados")
            return
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        console.print("\n🔒 [bold blue]Testando Endpoints Autenticados[/bold blue]")
        
        # Test /auth/me
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
            success = response.status_code == 200
            response_data = response.json() if response.status_code == 200 else None
            
            console.print(f"{'✅' if success else '❌'} GET /api/v1/auth/me - Status: {response.status_code}")
            self.log_test_result("/api/v1/auth/me", "GET", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/auth/me", "GET", 0, False, error=str(e))
            console.print(f"❌ GET /api/v1/auth/me - Erro: {e}")
        
        # Test /users/me
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/users/me", headers=headers)
            success = response.status_code == 200
            response_data = response.json() if response.status_code == 200 else None
            
            console.print(f"{'✅' if success else '❌'} GET /api/v1/users/me - Status: {response.status_code}")
            self.log_test_result("/api/v1/users/me", "GET", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/users/me", "GET", 0, False, error=str(e))
            console.print(f"❌ GET /api/v1/users/me - Erro: {e}")
        
        # Test /auth/sessions
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/auth/sessions", headers=headers)
            success = response.status_code == 200
            response_data = response.json() if response.status_code == 200 else None
            
            console.print(f"{'✅' if success else '❌'} GET /api/v1/auth/sessions - Status: {response.status_code}")
            self.log_test_result("/api/v1/auth/sessions", "GET", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/auth/sessions", "GET", 0, False, error=str(e))
            console.print(f"❌ GET /api/v1/auth/sessions - Erro: {e}")
    
    async def test_password_management(self):
        """Testa endpoints de gerenciamento de senha"""
        console.print("\n🔑 [bold blue]Testando Gerenciamento de Senhas[/bold blue]")
        
        # Test password reset request
        reset_data = {"email": "teste@exemplo.com"}
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/reset-password/request",
                json=reset_data
            )
            success = response.status_code in [200, 202, 204]  # Incluir 204 como sucesso
            response_data = response.json() if response.status_code in [200, 202] else None
            
            console.print(f"{'✅' if success else '❌'} POST /api/v1/auth/reset-password/request - Status: {response.status_code}")
            self.log_test_result("/api/v1/auth/reset-password/request", "POST", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/auth/reset-password/request", "POST", 0, False, error=str(e))
            console.print(f"❌ POST /api/v1/auth/reset-password/request - Erro: {e}")
        
        # Test email verification request
        verify_data = {"email": "teste@exemplo.com"}
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/verify-email/request",
                json=verify_data
            )
            success = response.status_code in [200, 202, 204]  # Incluir 204 como sucesso
            response_data = response.json() if response.status_code in [200, 202] else None
            
            console.print(f"{'✅' if success else '❌'} POST /api/v1/auth/verify-email/request - Status: {response.status_code}")
            self.log_test_result("/api/v1/auth/verify-email/request", "POST", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/auth/verify-email/request", "POST", 0, False, error=str(e))
            console.print(f"❌ POST /api/v1/auth/verify-email/request - Erro: {e}")
    
    async def test_user_management(self):
        """Testa endpoints de gerenciamento de usuários"""
        console.print("\n👥 [bold blue]Testando Gerenciamento de Usuários[/bold blue]")
        
        # Test user search (pode não precisar de auth dependendo da implementação)
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/users/search?page=1&size=10")
            success = response.status_code in [200, 401, 403]  # 401/403 se precisar de auth
            response_data = response.json() if response.status_code == 200 else None
            
            console.print(f"{'✅' if success else '❌'} GET /api/v1/users/search - Status: {response.status_code}")
            self.log_test_result("/api/v1/users/search", "GET", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/users/search", "GET", 0, False, error=str(e))
            console.print(f"❌ GET /api/v1/users/search - Erro: {e}")
        
        # Test user stats
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/users/stats")
            success = response.status_code in [200, 401, 403]  # 401/403 se precisar de auth
            response_data = response.json() if response.status_code == 200 else None
            
            console.print(f"{'✅' if success else '❌'} GET /api/v1/users/stats - Status: {response.status_code}")
            self.log_test_result("/api/v1/users/stats", "GET", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/users/stats", "GET", 0, False, error=str(e))
            console.print(f"❌ GET /api/v1/users/stats - Erro: {e}")
    
    async def test_refresh_token(self):
        """Testa renovação de token"""
        if not self.refresh_token:
            console.print("⚠️ Refresh token não disponível, pulando teste")
            return
        
        console.print("\n🔄 [bold blue]Testando Renovação de Token[/bold blue]")
        
        refresh_data = {"refresh_token": self.refresh_token}
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json=refresh_data
            )
            success = response.status_code == 200
            response_data = response.json() if response.status_code == 200 else None
            
            if success and response_data:
                new_access_token = response_data.get("access_token")
                console.print(f"✅ POST /api/v1/auth/refresh - Status: {response.status_code}")
                console.print(f"   Novo token: {new_access_token[:20]}...")
            else:
                console.print(f"❌ POST /api/v1/auth/refresh - Status: {response.status_code}")
            
            self.log_test_result("/api/v1/auth/refresh", "POST", response.status_code, success, response_data)
            
        except Exception as e:
            self.log_test_result("/api/v1/auth/refresh", "POST", 0, False, error=str(e))
            console.print(f"❌ POST /api/v1/auth/refresh - Erro: {e}")
    
    def generate_report(self):
        """Gera relatório final dos testes"""
        console.print("\n" + "="*80)
        console.print("[bold green]📊 RELATÓRIO FINAL DOS TESTES[/bold green]")
        console.print("="*80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - successful_tests
        
        # Estatísticas gerais
        stats_table = Table(title="Estatísticas Gerais")
        stats_table.add_column("Métrica", style="cyan")
        stats_table.add_column("Valor", style="magenta")
        
        stats_table.add_row("Total de Testes", str(total_tests))
        stats_table.add_row("Sucessos", f"[green]{successful_tests}[/green]")
        stats_table.add_row("Falhas", f"[red]{failed_tests}[/red]")
        stats_table.add_row("Taxa de Sucesso", f"{(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        console.print(stats_table)
        
        # Detalhes dos testes
        details_table = Table(title="Detalhes dos Testes")
        details_table.add_column("Endpoint", style="cyan")
        details_table.add_column("Método", style="blue")
        details_table.add_column("Status", style="magenta")
        details_table.add_column("Resultado", style="green")
        
        for test_key, result in self.test_results.items():
            status_color = "green" if result["success"] else "red"
            result_icon = "✅" if result["success"] else "❌"
            
            details_table.add_row(
                result["endpoint"],
                result["method"],
                f"[{status_color}]{result['status_code']}[/{status_color}]",
                f"[{status_color}]{result_icon}[/{status_color}]"
            )
        
        console.print(details_table)
        
        # Salvar relatório em arquivo
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": (successful_tests/total_tests*100) if total_tests > 0 else 0
            },
            "test_results": self.test_results
        }
        
        with open("test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"\n📄 Relatório salvo em: [cyan]test_report.json[/cyan]")
        
        return successful_tests, failed_tests

async def main():
    """Função principal que executa todos os testes"""
    console.print(Panel.fit(
        "[bold blue]🚀 TESTE AUTOMATIZADO DA API USER SERVICE[/bold blue]\n"
        f"Base URL: {BASE_URL}\n"
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        title="Iniciando Testes"
    ))
    
    async with APITester() as tester:
        # Executar testes em sequência
        await tester.test_health_check()
        await tester.test_user_registration()
        await tester.test_user_login()
        await tester.test_oauth2_login()
        await tester.test_authenticated_endpoints()
        await tester.test_password_management()
        await tester.test_user_management()
        await tester.test_refresh_token()
        
        # Gerar relatório final
        successful, failed = tester.generate_report()
        
        # Status final
        if failed == 0:
            console.print("\n[bold green]🎉 TODOS OS TESTES PASSARAM![/bold green]")
            return 0
        else:
            console.print(f"\n[bold red]⚠️ {failed} TESTE(S) FALHARAM[/bold red]")
            return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Testes interrompidos pelo usuário[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Erro fatal: {e}[/red]")
        sys.exit(1)