#!/usr/bin/env python3
"""
Testes para cenários de falha e edge cases no cadastro de usuários
"""

import pytest
import time
import json
from fastapi.testclient import TestClient
from main import app


class TestRegistrationEdgeCases:
    """Testes para casos extremos e cenários de falha no cadastro"""
    
    @pytest.fixture
    def client(self):
        """Fixture para cliente de teste"""
        return TestClient(app)
    
    def test_registration_with_empty_payload(self, client):
        """
        Teste: Cadastro com payload vazio
        
        Verifica se:
        - Retorna erro 422 (Unprocessable Entity)
        - Mensagem de erro apropriada
        """
        response = client.post("/api/v1/auth/register", json={})
        
        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data
        
        print("✅ Validação de payload vazio funcionando")
    
    def test_registration_with_null_values(self, client):
        """
        Teste: Cadastro com valores nulos
        
        Verifica se:
        - Valores nulos são rejeitados
        - Erro apropriado é retornado
        """
        user_data = {
            "email": None,
            "password": None,
            "confirm_password": None,
            "first_name": None,
            "last_name": None,
            "accept_terms": None,
            "accept_privacy": None,
            "marketing_consent": None
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422
        
        print("✅ Validação de valores nulos funcionando")
    
    def test_registration_with_very_long_strings(self, client):
        """
        Teste: Cadastro com strings muito longas
        
        Verifica se:
        - Strings excessivamente longas são rejeitadas
        - Limites de tamanho são respeitados
        """
        timestamp = int(time.time())
        very_long_string = "a" * 1000  # 1000 caracteres
        
        user_data = {
            "email": f"teste_{timestamp}@exemplo.com",
            "password": "MinhaSenh@123",
            "confirm_password": "MinhaSenh@123",
            "first_name": very_long_string,
            "last_name": very_long_string,
            "accept_terms": True,
            "accept_privacy": True,
            "marketing_consent": False
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        # Deve retornar erro de validação
        assert response.status_code in [400, 422]
        
        print("✅ Validação de strings longas funcionando")
    
    def test_registration_with_special_characters_in_email(self, client):
        """
        Teste: Cadastro com caracteres especiais no email
        
        Verifica se:
        - Emails com caracteres especiais válidos são aceitos
        - Emails com caracteres inválidos são rejeitados
        """
        timestamp = int(time.time())
        
        # Casos válidos
        valid_emails = [
            f"teste.valido_{timestamp}@exemplo.com",
            f"teste+tag_{timestamp}@exemplo.com",
            f"teste-hifen_{timestamp}@exemplo.com",
            f"teste_underscore_{timestamp}@exemplo.com"
        ]
        
        for email in valid_emails:
            user_data = {
                "email": email,
                "password": "MinhaSenh@123",
                "confirm_password": "MinhaSenh@123",
                "first_name": "Teste",
                "last_name": "Especial",
                "accept_terms": True,
                "accept_privacy": True,
                "marketing_consent": False
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 201, f"Email válido rejeitado: {email}"
        
        # Casos inválidos
        invalid_emails = [
            "email@",
            "@exemplo.com",
            "email..duplo@exemplo.com",
            "email@.com",
            "email@exemplo.",
            "email espaço@exemplo.com"
        ]
        
        for email in invalid_emails:
            user_data = {
                "email": email,
                "password": "MinhaSenh@123",
                "confirm_password": "MinhaSenh@123",
                "first_name": "Teste",
                "last_name": "Inválido",
                "accept_terms": True,
                "accept_privacy": True,
                "marketing_consent": False
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code in [400, 422], f"Email inválido aceito: {email}"
        
        print("✅ Validação de caracteres especiais em email funcionando")
    
    def test_registration_with_unicode_characters(self, client):
        """
        Teste: Cadastro com caracteres Unicode
        
        Verifica se:
        - Caracteres Unicode são tratados corretamente
        - Nomes com acentos são aceitos
        """
        timestamp = int(time.time())
        
        user_data = {
            "email": f"teste_unicode_{timestamp}@exemplo.com",
            "password": "MinhaSenh@123",
            "confirm_password": "MinhaSenh@123",
            "first_name": "José",
            "last_name": "Müller",
            "accept_terms": True,
            "accept_privacy": True,
            "marketing_consent": False
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        response_data = response.json()
        assert response_data["user"]["first_name"] == "José"
        assert response_data["user"]["last_name"] == "Müller"
        
        print("✅ Suporte a caracteres Unicode funcionando")
    
    def test_registration_with_sql_injection_attempt(self, client):
        """
        Teste: Tentativa de SQL Injection no cadastro
        
        Verifica se:
        - Tentativas de SQL injection são bloqueadas
        - Dados maliciosos não afetam o banco
        """
        timestamp = int(time.time())
        
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin'--",
            "' OR '1'='1",
            "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --"
        ]
        
        for malicious_input in malicious_inputs:
            user_data = {
                "email": f"teste_sql_{timestamp}@exemplo.com",
                "password": "MinhaSenh@123",
                "confirm_password": "MinhaSenh@123",
                "first_name": malicious_input,
                "last_name": "Teste",
                "accept_terms": True,
                "accept_privacy": True,
                "marketing_consent": False
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            # Deve processar normalmente (SQLAlchemy protege contra SQL injection)
            # ou rejeitar por validação de tamanho/caracteres
            assert response.status_code in [201, 400, 422]
            
            if response.status_code == 201:
                # Se aceito, verificar que foi tratado como string normal
                response_data = response.json()
                assert response_data["user"]["first_name"] == malicious_input
        
        print("✅ Proteção contra SQL injection funcionando")
    
    def test_registration_with_xss_attempt(self, client):
        """
        Teste: Tentativa de XSS no cadastro
        
        Verifica se:
        - Scripts maliciosos são tratados como texto
        - Não há execução de código
        """
        timestamp = int(time.time())
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            user_data = {
                "email": f"teste_xss_{timestamp}@exemplo.com",
                "password": "MinhaSenh@123",
                "confirm_password": "MinhaSenh@123",
                "first_name": payload,
                "last_name": "Teste",
                "accept_terms": True,
                "accept_privacy": True,
                "marketing_consent": False
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            # Deve processar como string normal ou rejeitar por validação
            assert response.status_code in [201, 400, 422]
            
            if response.status_code == 201:
                response_data = response.json()
                # Verificar que foi armazenado como string (não executado)
                assert response_data["user"]["first_name"] == payload
        
        print("✅ Proteção contra XSS funcionando")
    
    def test_registration_with_invalid_json(self, client):
        """
        Teste: Cadastro com JSON inválido
        
        Verifica se:
        - JSON malformado é rejeitado
        - Erro apropriado é retornado
        """
        invalid_json = '{"email": "teste@exemplo.com", "password": "senha", invalid}'
        
        response = client.post(
            "/api/v1/auth/register",
            data=invalid_json,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        
        print("✅ Validação de JSON inválido funcionando")
    
    def test_registration_concurrent_requests(self, client):
        """
        Teste: Requisições concorrentes de cadastro
        
        Verifica se:
        - Múltiplas requisições simultâneas são tratadas corretamente
        - Não há condições de corrida
        """
        import threading
        import queue
        
        timestamp = int(time.time())
        results = queue.Queue()
        
        def register_user(thread_id):
            user_data = {
                "email": f"teste_concurrent_{timestamp}_{thread_id}@exemplo.com",
                "password": "MinhaSenh@123",
                "confirm_password": "MinhaSenh@123",
                "first_name": f"Teste{thread_id}",
                "last_name": "Concurrent",
                "accept_terms": True,
                "accept_privacy": True,
                "marketing_consent": False
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            results.put((thread_id, response.status_code))
        
        # Criar 5 threads para cadastros simultâneos
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_user, args=(i,))
            threads.append(thread)
        
        # Iniciar todas as threads
        for thread in threads:
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Verificar resultados
        success_count = 0
        while not results.empty():
            thread_id, status_code = results.get()
            if status_code == 201:
                success_count += 1
        
        # Todos os cadastros devem ter sido bem-sucedidos
        assert success_count == 5
        
        print("✅ Tratamento de requisições concorrentes funcionando")
    
    def test_registration_with_different_content_types(self, client):
        """
        Teste: Cadastro com diferentes Content-Types
        
        Verifica se:
        - Apenas application/json é aceito
        - Outros content-types são rejeitados
        """
        timestamp = int(time.time())
        user_data = {
            "email": f"teste_content_type_{timestamp}@exemplo.com",
            "password": "MinhaSenh@123",
            "confirm_password": "MinhaSenh@123",
            "first_name": "Teste",
            "last_name": "ContentType",
            "accept_terms": True,
            "accept_privacy": True,
            "marketing_consent": False
        }
        
        # Testar com application/json (deve funcionar)
        response = client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        assert response.status_code == 201
        
        # Testar com text/plain (deve falhar)
        response = client.post(
            "/api/v1/auth/register",
            data=json.dumps(user_data),
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code in [400, 415, 422]
        
        print("✅ Validação de Content-Type funcionando")


if __name__ == "__main__":
    import subprocess
    import sys
    
    print("🧪 Executando testes de edge cases para cadastro...")
    print("=" * 60)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short",
        "-m", "not slow"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("🎉 Todos os testes de edge cases passaram!")
    else:
        print("❌ Alguns testes falharam")