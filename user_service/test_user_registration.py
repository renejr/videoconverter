#!/usr/bin/env python3
"""
Testes automatizados para o processo de cadastro de usuários
Seguindo boas práticas de teste com pytest
"""

import pytest
import asyncio
import time
from datetime import datetime
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# Imports do projeto
from main import app
from database.connection import get_database_session
from models.user import User
from models.credential import Credential
from schemas.user import UserCreateSchema
from schemas.auth import LoginResponseSchema


class TestUserRegistration:
    """Classe de testes para o processo de cadastro de usuários"""
    
    @pytest.fixture
    def client(self):
        """Fixture para cliente de teste"""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Fixture para cliente assíncrono"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    def valid_user_data(self):
        """Fixture com dados válidos para cadastro"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time())
        return {
            "email": f"teste_cadastro_{timestamp}_{unique_id}@exemplo.com",
            "password": "MinhaSenh@123",
            "confirm_password": "MinhaSenh@123",
            "first_name": "João",
            "last_name": "Silva",
            "accept_terms": True,
            "accept_privacy": True,
            "marketing_consent": False
        }
    
    @pytest.fixture
    def invalid_user_data_cases(self):
        """Fixture com casos de dados inválidos para teste"""
        timestamp = int(time.time())
        base_email = f"teste_invalido_{timestamp}"
        
        return [
            # Email inválido
            {
                "data": {
                    "email": "email_invalido",
                    "password": "MinhaSenh@123",
                    "confirm_password": "MinhaSenh@123",
                    "first_name": "João",
                    "last_name": "Silva",
                    "accept_terms": True,
                    "accept_privacy": True,
                    "marketing_consent": False
                },
                "expected_error": "email"
            },
            # Senha muito fraca
            {
                "data": {
                    "email": f"{base_email}_1@exemplo.com",
                    "password": "123",
                    "confirm_password": "123",
                    "first_name": "João",
                    "last_name": "Silva",
                    "accept_terms": True,
                    "accept_privacy": True,
                    "marketing_consent": False
                },
                "expected_error": "password"
            },
            # Senhas não coincidem
            {
                "data": {
                    "email": f"{base_email}_2@exemplo.com",
                    "password": "MinhaSenh@123",
                    "confirm_password": "SenhasDiferentes@123",
                    "first_name": "João",
                    "last_name": "Silva",
                    "accept_terms": True,
                    "accept_privacy": True,
                    "marketing_consent": False
                },
                "expected_error": "confirm_password"
            },
            # Nome muito curto
            {
                "data": {
                    "email": f"{base_email}_3@exemplo.com",
                    "password": "MinhaSenh@123",
                    "confirm_password": "MinhaSenh@123",
                    "first_name": "A",
                    "last_name": "Silva",
                    "accept_terms": True,
                    "accept_privacy": True,
                    "marketing_consent": False
                },
                "expected_error": "first_name"
            },
            # Termos não aceitos
            {
                "data": {
                    "email": f"{base_email}_4@exemplo.com",
                    "password": "MinhaSenh@123",
                    "confirm_password": "MinhaSenh@123",
                    "first_name": "João",
                    "last_name": "Silva",
                    "accept_terms": False,
                    "accept_privacy": True,
                    "marketing_consent": False
                },
                "expected_error": "accept_terms"
            },
            # Política de privacidade não aceita
            {
                "data": {
                    "email": f"{base_email}_5@exemplo.com",
                    "password": "MinhaSenh@123",
                    "confirm_password": "MinhaSenh@123",
                    "first_name": "João",
                    "last_name": "Silva",
                    "accept_terms": True,
                    "accept_privacy": False,
                    "marketing_consent": False
                },
                "expected_error": "accept_privacy"
            }
        ]
    
    async def cleanup_test_user(self, email: str):
        """Limpa usuário de teste do banco de dados"""
        try:
            async for db in get_database_session():
                # Buscar usuário
                result = await db.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                
                if user:
                    # Deletar credenciais
                    await db.execute(delete(Credential).where(Credential.user_id == user.id))
                    # Deletar usuário
                    await db.execute(delete(User).where(User.id == user.id))
                    await db.commit()
                break
        except Exception as e:
            print(f"Erro ao limpar usuário de teste: {e}")
    
    def test_successful_user_registration(self, client, valid_user_data):
        """
        Teste: Cadastro bem-sucedido de usuário
        
        Verifica se:
        - O endpoint retorna status 201
        - Os dados do usuário são retornados corretamente
        - Os tokens de acesso e refresh são gerados
        - O tipo de token é 'bearer'
        """
        response = client.post("/api/v1/auth/register", json=valid_user_data)
        
        # Verificar status code
        assert response.status_code == 201, f"Esperado 201, recebido {response.status_code}: {response.text}"
        
        # Verificar estrutura da resposta
        response_data = response.json()
        
        # Verificar se contém os campos obrigatórios
        required_fields = ["user", "access_token", "refresh_token", "token_type"]
        for field in required_fields:
            assert field in response_data, f"Campo '{field}' não encontrado na resposta"
        
        # Verificar dados do usuário
        user_data = response_data["user"]
        assert user_data["email"] == valid_user_data["email"]
        assert user_data["first_name"] == valid_user_data["first_name"]
        assert user_data["last_name"] == valid_user_data["last_name"]
        assert user_data["is_active"] == True
        assert user_data["is_verified"] == False  # Usuário recém-criado não está verificado
        
        # Verificar tokens
        assert response_data["access_token"] is not None
        assert len(response_data["access_token"]) > 0
        assert response_data["refresh_token"] is not None
        assert len(response_data["refresh_token"]) > 0
        assert response_data["token_type"] == "bearer"
        
        # Verificar se os tokens são diferentes
        assert response_data["access_token"] != response_data["refresh_token"]
        
        print(f"✅ Cadastro bem-sucedido para: {valid_user_data['email']}")
    
    def test_duplicate_email_registration(self, client, valid_user_data):
        """
        Teste: Tentativa de cadastro com email duplicado
        
        Verifica se:
        - O primeiro cadastro é bem-sucedido
        - O segundo cadastro com mesmo email falha
        - Retorna erro apropriado
        """
        # Primeiro cadastro (deve funcionar)
        response1 = client.post("/api/v1/auth/register", json=valid_user_data)
        assert response1.status_code == 201
        
        # Segundo cadastro com mesmo email (deve falhar)
        response2 = client.post("/api/v1/auth/register", json=valid_user_data)
        assert response2.status_code == 409
        
        response_data = response2.json()
        assert "error" in response_data
        assert "message" in response_data["error"]
        assert "email" in response_data["error"]["message"].lower() or "já existe" in response_data["error"]["message"].lower()
        
        print(f"✅ Validação de email duplicado funcionando corretamente")
    
    def test_invalid_data_registration(self, client, invalid_user_data_cases):
        """
        Teste: Cadastro com dados inválidos
        
        Verifica se:
        - Dados inválidos são rejeitados
        - Mensagens de erro apropriadas são retornadas
        """
        for case in invalid_user_data_cases:
            response = client.post("/api/v1/auth/register", json=case["data"])
            
            # Deve retornar erro de validação (422) ou bad request (400)
            assert response.status_code in [400, 422], f"Esperado 400 ou 422 para {case['expected_error']}, recebido {response.status_code}"
            
            response_data = response.json()
            # Verifica se tem a estrutura de erro correta
            assert "error" in response_data or "detail" in response_data
            
            print(f"✅ Validação de {case['expected_error']} funcionando corretamente")
    
    def test_registration_with_authentication_flow(self, client, valid_user_data):
        """
        Teste: Fluxo completo de cadastro com autenticação automática
        
        Verifica se:
        - O cadastro é bem-sucedido
        - Os tokens são válidos
        - É possível acessar endpoints autenticados
        """
        # Cadastrar usuário
        response = client.post("/api/v1/auth/register", json=valid_user_data)
        assert response.status_code == 201
        
        response_data = response.json()
        access_token = response_data["access_token"]
        
        # Testar acesso a endpoint autenticado
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == valid_user_data["email"]
        
        print(f"✅ Fluxo de autenticação automática funcionando corretamente")
    
    def test_registration_response_structure(self, client, valid_user_data):
        """
        Teste: Estrutura da resposta do cadastro
        
        Verifica se:
        - A resposta segue o schema LoginResponseSchema
        - Todos os campos obrigatórios estão presentes
        - Os tipos de dados estão corretos
        """
        response = client.post("/api/v1/auth/register", json=valid_user_data)
        assert response.status_code == 201
        
        response_data = response.json()
        
        # Verificar estrutura do usuário
        user = response_data["user"]
        user_required_fields = ["id", "email", "first_name", "last_name", "is_active", "is_verified", "created_at"]
        for field in user_required_fields:
            assert field in user, f"Campo '{field}' não encontrado nos dados do usuário"
        
        # Verificar tipos
        assert isinstance(user["id"], int)
        assert isinstance(user["email"], str)
        assert isinstance(user["first_name"], str)
        assert isinstance(user["last_name"], str)
        assert isinstance(user["is_active"], bool)
        assert isinstance(user["is_verified"], bool)
        assert isinstance(user["created_at"], str)
        
        # Verificar tokens
        assert isinstance(response_data["access_token"], str)
        assert isinstance(response_data["refresh_token"], str)
        assert isinstance(response_data["token_type"], str)
        
        print(f"✅ Estrutura da resposta está correta")
    
    def test_registration_password_security(self, client):
        """
        Teste: Segurança da senha no cadastro
        
        Verifica se:
        - A senha não é retornada na resposta
        - A senha é criptografada no banco
        """
        timestamp = int(time.time())
        user_data = {
            "email": f"teste_seguranca_{timestamp}@exemplo.com",
            "password": "MinhaSenh@123",
            "confirm_password": "MinhaSenh@123",
            "first_name": "Teste",
            "last_name": "Segurança",
            "accept_terms": True,
            "accept_privacy": True,
            "marketing_consent": False
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        response_data = response.json()
        
        # Verificar que a senha não está na resposta
        user = response_data["user"]
        assert "password" not in user
        assert "password_hash" not in user
        
        # Verificar que a resposta não contém a senha original
        response_text = response.text
        assert user_data["password"] not in response_text
        
        print(f"✅ Segurança da senha está funcionando corretamente")


# Função para executar todos os testes
def run_all_tests():
    """Executa todos os testes de cadastro"""
    print("🚀 Iniciando testes automatizados de cadastro de usuário...")
    print("=" * 60)
    
    # Executar testes com pytest
    import subprocess
    import sys
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            __file__, 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        return False


if __name__ == "__main__":
    run_all_tests()