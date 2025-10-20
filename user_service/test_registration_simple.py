#!/usr/bin/env python3
"""
Teste simplificado para cadastro de usuários
"""

import pytest
import time
from fastapi.testclient import TestClient
from main import app


def test_simple_user_registration():
    """
    Teste simples: Cadastro de usuário
    
    Verifica se:
    - O endpoint retorna status 201
    - A resposta contém os campos básicos
    """
    client = TestClient(app)
    
    timestamp = int(time.time())
    user_data = {
        "email": f"teste_simples_{timestamp}@exemplo.com",
        "password": "MinhaSenh@123",
        "confirm_password": "MinhaSenh@123",
        "first_name": "Teste",
        "last_name": "Simples",
        "accept_terms": True,
        "accept_privacy": True,
        "marketing_consent": False
    }
    
    response = client.post("/api/v1/auth/register", json=user_data)
    
    # Verificar status code
    assert response.status_code == 201, f"Esperado 201, recebido {response.status_code}: {response.text}"
    
    # Verificar estrutura básica da resposta
    response_data = response.json()
    assert "user" in response_data
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert "token_type" in response_data
    
    print("✅ Teste simples de cadastro passou!")


def test_duplicate_email_registration():
    """
    Teste: Cadastro com email duplicado
    
    Verifica se:
    - O segundo cadastro com mesmo email falha
    - Retorna erro apropriado
    """
    client = TestClient(app)
    
    timestamp = int(time.time())
    user_data = {
        "email": f"teste_duplicado_{timestamp}@exemplo.com",
        "password": "MinhaSenh@123",
        "confirm_password": "MinhaSenh@123",
        "first_name": "Teste",
        "last_name": "Duplicado",
        "accept_terms": True,
        "accept_privacy": True,
        "marketing_consent": False
    }
    
    # Primeiro cadastro - deve funcionar
    response1 = client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 201
    
    # Segundo cadastro com mesmo email - deve falhar
    response2 = client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code in [400, 409, 422]  # Conflito ou erro de validação
    
    print("✅ Teste de email duplicado passou!")


if __name__ == "__main__":
    test_simple_user_registration()
    test_duplicate_email_registration()
    print("🎉 Todos os testes simples passaram!")