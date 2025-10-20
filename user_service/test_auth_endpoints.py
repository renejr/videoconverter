#!/usr/bin/env python3
"""
Teste específico para endpoints que requerem autenticação
"""

import requests
import json
import time

# Configurações
BASE_URL = "http://localhost:8000"

def test_authenticated_endpoints():
    """Testa endpoints que requerem autenticação"""
    
    # 1. Primeiro fazer login para obter token
    print("1. Fazendo login para obter token...")
    
    timestamp = int(time.time())
    user_data = {
        "email": f"teste_auth_{timestamp}@exemplo.com",
        "password": "MinhaSenh@123",
        "confirm_password": "MinhaSenh@123",
        "first_name": "Teste",
        "last_name": "Auth",
        "accept_terms": True,
        "accept_privacy": True,
        "marketing_consent": False
    }
    
    # Registrar usuário
    register_response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    print(f"Registro - Status: {register_response.status_code}")
    
    if register_response.status_code != 201:
        print(f"❌ Erro no registro: {register_response.text}")
        return
    
    # Fazer login
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"Login - Status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.text}")
        return
    
    login_data_response = login_response.json()
    access_token = login_data_response.get("access_token")
    
    if not access_token:
        print("❌ Token de acesso não encontrado na resposta do login")
        return
    
    print(f"✅ Login realizado com sucesso! Token: {access_token[:50]}...")
    
    # Headers com autenticação
    auth_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. Testar /api/v1/auth/me
    print("\n2. Testando /api/v1/auth/me...")
    try:
        me_response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=auth_headers)
        print(f"Auth Me - Status: {me_response.status_code}")
        print(f"Auth Me - Headers: {dict(me_response.headers)}")
        
        if me_response.status_code == 200:
            print(f"Auth Me - Response: {json.dumps(me_response.json(), indent=2)}")
            print("✅ /api/v1/auth/me funcionando!")
        else:
            print(f"❌ Erro em /api/v1/auth/me: {me_response.text}")
    except Exception as e:
        print(f"❌ Exceção em /api/v1/auth/me: {e}")
    
    # 3. Testar /api/v1/auth/sessions
    print("\n3. Testando /api/v1/auth/sessions...")
    try:
        sessions_response = requests.get(f"{BASE_URL}/api/v1/auth/sessions", headers=auth_headers)
        print(f"Auth Sessions - Status: {sessions_response.status_code}")
        print(f"Auth Sessions - Headers: {dict(sessions_response.headers)}")
        
        if sessions_response.status_code == 200:
            print(f"Auth Sessions - Response: {json.dumps(sessions_response.json(), indent=2)}")
            print("✅ /api/v1/auth/sessions funcionando!")
        else:
            print(f"❌ Erro em /api/v1/auth/sessions: {sessions_response.text}")
    except Exception as e:
        print(f"❌ Exceção em /api/v1/auth/sessions: {e}")
    
    # 4. Testar /api/v1/users/me
    print("\n4. Testando /api/v1/users/me...")
    try:
        users_me_response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=auth_headers)
        print(f"Users Me - Status: {users_me_response.status_code}")
        print(f"Users Me - Headers: {dict(users_me_response.headers)}")
        
        if users_me_response.status_code == 200:
            print(f"Users Me - Response: {json.dumps(users_me_response.json(), indent=2)}")
            print("✅ /api/v1/users/me funcionando!")
        else:
            print(f"❌ Erro em /api/v1/users/me: {users_me_response.text}")
    except Exception as e:
        print(f"❌ Exceção em /api/v1/users/me: {e}")

if __name__ == "__main__":
    test_authenticated_endpoints()