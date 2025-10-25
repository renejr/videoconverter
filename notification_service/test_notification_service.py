#!/usr/bin/env python3
"""
Teste do Notification Service
Testa conexão Redis, Event Bus e configurações Gmail
"""

import asyncio
import sys
import os
import redis.asyncio as redis

# Adicionar o diretório do notification_service ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings


async def test_notification_service():
    """
    Testa o Notification Service
    """
    print("🧪 Testando Notification Service...")
    print("=" * 50)
    
    # Teste 1: Configurações
    print("\n1️⃣ Testando Configurações:")
    print(f"   📧 SMTP Host: {settings.smtp_host}")
    print(f"   📧 SMTP Port: {settings.smtp_port}")
    print(f"   📧 SMTP User: {settings.smtp_user}")
    print(f"   📧 SMTP Password: {'***' if settings.smtp_password else 'NÃO CONFIGURADO'}")
    print(f"   🔄 Redis Host: {settings.redis_host}")
    print(f"   🔄 Redis Port: {settings.redis_port}")
    
    # Teste 2: Conexão Redis
    print("\n2️⃣ Testando Conexão Redis:")
    
    try:
        # Conectar diretamente ao Redis
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=True
        )
        
        # Testar conexão
        await redis_client.ping()
        print("   ✅ Conexão Redis estabelecida")
        
        # Teste 3: Publicar evento de teste
        print("\n3️⃣ Testando Publicação de Evento:")
        
        test_event = {
            "user_id": "test_123",
            "email": "test@example.com",
            "message": "Teste do Notification Service"
        }
        
        # Publicar no canal de teste
        channel = "notifications.test"
        result = await redis_client.publish(channel, str(test_event))
        print(f"   ✅ Evento publicado no canal '{channel}' - {result} subscribers")
        
        await redis_client.close()
        print("   ✅ Desconectado do Redis")
        
    except Exception as e:
        print(f"   ❌ Erro na conexão Redis: {e}")
        return False
    
    # Teste 4: Configurações Gmail
    print("\n4️⃣ Verificando Configurações Gmail:")
    
    if settings.smtp_user and settings.smtp_password:
        print("   ✅ Credenciais Gmail configuradas")
        
        if settings.smtp_user != "your-email@gmail.com":
            print("   ✅ Email personalizado configurado")
        else:
            print("   ⚠️  Email ainda é o padrão - configure com seu email real")
            
        if settings.smtp_password != "your-gmail-app-password":
            print("   ✅ Senha de app configurada")
        else:
            print("   ⚠️  Senha ainda é a padrão - configure com sua senha de app real")
    else:
        print("   ❌ Credenciais Gmail não configuradas")
        print("   📝 Configure SMTP_USER e SMTP_PASSWORD no arquivo .env")
    
    print("\n" + "=" * 50)
    print("✅ Teste do Notification Service concluído!")
    
    return True


async def main():
    """
    Função principal
    """
    try:
        await test_notification_service()
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())