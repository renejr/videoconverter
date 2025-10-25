"""
Teste Simplificado do Event Bus
Testa apenas a publicação de eventos
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta


async def test_event_publisher():
    """
    Testa a publicação de eventos sem depender do Notification Service
    """
    print("🔄 Testando Event Publisher...")
    
    try:
        # Import dinâmico para evitar problemas de configuração
        from events.connection import EventBusConnection
        
        # Criar conexão
        event_bus = EventBusConnection()
        
        # Conectar
        await event_bus.connect()
        print("✅ Conectado ao Event Bus")
        
        # Testar publicação de evento
        test_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "TEST_EVENT",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "message": "Teste de publicação de evento",
                "test_id": str(uuid.uuid4())
            }
        }
        
        # Publicar evento
        await event_bus.publish("test.events", test_event)
        print("✅ Evento publicado com sucesso")
        
        # Desconectar
        await event_bus.disconnect()
        print("✅ Desconectado do Event Bus")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do Event Bus: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_user_service_events():
    """
    Testa eventos específicos do User Service
    """
    print("\n🔄 Testando eventos do User Service...")
    
    try:
        from events.publisher import EventPublisher
        
        # Criar publisher
        publisher = EventPublisher()
        
        # Testar evento de registro de usuário
        user_id = 123
        email = "teste@exemplo.com"
        full_name = "Usuário Teste"
        
        await publisher.publish_user_registered(
            user_id=user_id,
            email=email,
            full_name=full_name
        )
        print("✅ Evento USER_REGISTERED publicado")
        
        # Testar evento de verificação de email
        verification_token = str(uuid.uuid4())
        verification_url = "http://localhost:3000/verify-email?token=123"
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        await publisher.publish_email_verification_requested(
            user_id=user_id,
            email=email,
            full_name=full_name,
            verification_token=verification_token,
            verification_url=verification_url,
            expires_at=expires_at
        )
        print("✅ Evento EMAIL_VERIFICATION_REQUESTED publicado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos eventos do User Service: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """
    Executa todos os testes
    """
    print("🧪 Teste Simplificado do Event Bus")
    print("=" * 50)
    
    # Teste 1: Conexão básica
    test1 = await test_event_publisher()
    
    # Teste 2: Eventos do User Service
    test2 = await test_user_service_events()
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("✅ Todos os testes passaram!")
        return True
    else:
        print("❌ Alguns testes falharam!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)