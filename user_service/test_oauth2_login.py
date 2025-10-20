#!/usr/bin/env python3
"""
Teste específico para OAuth2 Login
"""

import requests
import json
import time

# Configurações
BASE_URL = "http://localhost:8000"

def test_oauth2_login():
    """Testa o endpoint OAuth2 login especificamente"""
    
    # 1. Primeiro registrar um usuário
    print("1. Registrando usuário...")
    
    timestamp = int(time.time())
    user_data = {
        "email": f"teste_oauth2_{timestamp}@exemplo.com",
        "password": "MinhaSenh@123",
        "confirm_password": "MinhaSenh@123",
        "first_name": "Teste",
        "last_name": "OAuth",
        "accept_terms": True,
        "accept_privacy": True,
        "marketing_consent": False
    }
    
    register_response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    print(f"Registro - Status: {register_response.status_code}")
    
    if register_response.status_code != 201:
        print(f"❌ Erro no registro: {register_response.text}")
        return
    
    print("✅ Usuário registrado com sucesso!")
    
    # 2. Testar OAuth2 login
    print("\n2. Testando OAuth2 login...")
    
    # Dados no formato OAuth2PasswordRequestForm (form-data)
    oauth2_data = {
        "username": user_data["email"],  # OAuth2 usa 'username' em vez de 'email'
        "password": user_data["password"]
    }
    
    oauth2_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login/oauth2", 
        data=oauth2_data,  # Usar 'data' em vez de 'json' para form-data
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"OAuth2 Login - Status: {oauth2_response.status_code}")
    print(f"OAuth2 Login - Headers: {dict(oauth2_response.headers)}")
    
    if oauth2_response.status_code == 200:
        response_data = oauth2_response.json()
        print(f"OAuth2 Login - Response: {json.dumps(response_data, indent=2)}")
        print("✅ OAuth2 Login realizado com sucesso!")
        print(f"Token recebido: {response_data.get('access_token', 'N/A')[:50]}...")
    else:
        print(f"❌ Erro no OAuth2 login: {oauth2_response.text}")

if __name__ == "__main__":
    test_oauth2_login()