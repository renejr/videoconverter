#!/usr/bin/env python3
"""
Teste específico para o endpoint de login
"""

import httpx
import json
from datetime import datetime

def test_login():
    """Testa especificamente o endpoint de login"""
    
    base_url = "http://localhost:8000"
    
    # Primeiro, registrar um usuário
    print("1. Registrando usuário...")
    timestamp = int(datetime.now().timestamp())
    email = f"teste_login_{timestamp}@exemplo.com"
    password = "MinhaSenh@123"
    
    register_data = {
        "email": email,
        "password": password,
        "confirm_password": password,
        "first_name": "Teste",
        "last_name": "Login",
        "accept_terms": True,
        "accept_privacy": True,
        "marketing_consent": False
    }
    
    try:
        with httpx.Client() as client:
            # Registrar
            register_response = client.post(
                f"{base_url}/api/v1/auth/register",
                json=register_data
            )
            print(f"Registro - Status: {register_response.status_code}")
            if register_response.status_code != 201:
                print(f"Erro no registro: {register_response.text}")
                return
            
            print("✅ Usuário registrado com sucesso!")
            
            # Fazer login
            print("\n2. Fazendo login...")
            login_data = {
                "email": email,
                "password": password
            }
            
            login_response = client.post(
                f"{base_url}/api/v1/auth/login",
                json=login_data
            )
            
            print(f"Login - Status: {login_response.status_code}")
            print(f"Login - Headers: {dict(login_response.headers)}")
            print(f"Login - Response: {login_response.text}")
            
            if login_response.status_code == 200:
                print("✅ Login realizado com sucesso!")
                response_data = login_response.json()
                print(f"Token recebido: {response_data.get('access_token', 'N/A')[:50]}...")
            else:
                print(f"❌ Erro no login: {login_response.text}")
                
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")

if __name__ == "__main__":
    test_login()