"""
Teste de Integração - Event Bus
User Service -> Notification Service
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from events.publisher import event_publisher
from events.connection import event_bus


async def test_event_bus_connection():
    """
    Testa a conexão com o Event Bus
    """
    print("🔄 Testando conexão com Event Bus...")
    
    try:
        # Testar conexão
        connected = await event_bus.test_connection()
        
        if connected:
            print("✅ Conexão com Event Bus estabelecida!")
            
            # Obter informações da conexão
            info = await event_bus.get_info()
            print(f"📊 Informações da conexão: {json.dumps(info, indent=2)}")
            
            return True
        else:
            print("❌ Falha na conexão com Event Bus")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {str(e)}")
        return False


async def test_user_registered_event():
    """
    Testa evento de usuário registrado
    """
    print("\n📝 Testando evento USER_REGISTERED...")
    
    try:
        success = await event_publisher.publish_user_registered(
            user_id=12345,
            email="teste@exemplo.com",
            full_name="João da Silva",
            language_preference="pt-BR",
            timezone="America/Sao_Paulo",
            correlation_id=str(uuid.uuid4())
        )
        
        if success:
            print("✅ Evento USER_REGISTERED publicado com sucesso!")
        else:
            print("❌ Falha ao publicar evento USER_REGISTERED")
            
        return success
        
    except Exception as e:
        print(f"❌ Erro ao publicar USER_REGISTERED: {str(e)}")
        return False


async def test_email_verification_event():
    """
    Testa evento de verificação de email
    """
    print("\n📧 Testando evento EMAIL_VERIFICATION_REQUESTED...")
    
    try:
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        success = await event_publisher.publish_email_verification_requested(
            user_id=12345,
            email="teste@exemplo.com",
            full_name="João da Silva",
            verification_token="abc123def456",
            verification_url="https://vidconv.com/verify?token=abc123def456",
            expires_at=expires_at,
            language_preference="pt-BR",
            correlation_id=str(uuid.uuid4())
        )
        
        if success:
            print("✅ Evento EMAIL_VERIFICATION_REQUESTED publicado com sucesso!")
        else:
            print("❌ Falha ao publicar evento EMAIL_VERIFICATION_REQUESTED")
            
        return success
        
    except Exception as e:
        print(f"❌ Erro ao publicar EMAIL_VERIFICATION_REQUESTED: {str(e)}")
        return False


async def test_password_reset_event():
    """
    Testa evento de reset de senha
    """
    print("\n🔐 Testando evento PASSWORD_RESET_REQUESTED...")
    
    try:
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        success = await event_publisher.publish_password_reset_requested(
            user_id=12345,
            email="teste@exemplo.com",
            full_name="João da Silva",
            reset_token="reset123token456",
            reset_url="https://vidconv.com/reset?token=reset123token456",
            expires_at=expires_at,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            language_preference="pt-BR",
            correlation_id=str(uuid.uuid4())
        )
        
        if success:
            print("✅ Evento PASSWORD_RESET_REQUESTED publicado com sucesso!")
        else:
            print("❌ Falha ao publicar evento PASSWORD_RESET_REQUESTED")
            
        return success
        
    except Exception as e:
        print(f"❌ Erro ao publicar PASSWORD_RESET_REQUESTED: {str(e)}")
        return False


async def test_profile_updated_event():
    """
    Testa evento de perfil atualizado
    """
    print("\n👤 Testando evento USER_PROFILE_UPDATED...")
    
    try:
        updated_fields = {
            "email": "novo@exemplo.com",
            "phone": "+55 11 99999-9999",
            "security_settings": {"two_factor": True}
        }
        
        success = await event_publisher.publish_user_profile_updated(
            user_id=12345,
            email="teste@exemplo.com",
            full_name="João da Silva",
            updated_fields=updated_fields,
            language_preference="pt-BR",
            correlation_id=str(uuid.uuid4())
        )
        
        if success:
            print("✅ Evento USER_PROFILE_UPDATED publicado com sucesso!")
        else:
            print("❌ Falha ao publicar evento USER_PROFILE_UPDATED")
            
        return success
        
    except Exception as e:
        print(f"❌ Erro ao publicar USER_PROFILE_UPDATED: {str(e)}")
        return False


async def test_publisher_info():
    """
    Testa informações do publisher
    """
    print("\n📊 Obtendo informações do Event Publisher...")
    
    try:
        # Testar conexão do publisher
        connected = await event_publisher.test_connection()
        print(f"🔗 Publisher conectado: {connected}")
        
        # Obter informações da conexão
        info = await event_publisher.get_connection_info()
        print(f"📋 Informações do publisher: {json.dumps(info, indent=2)}")
        
        return connected
        
    except Exception as e:
        print(f"❌ Erro ao obter informações do publisher: {str(e)}")
        return False


async def run_all_tests():
    """
    Executa todos os testes de integração
    """
    print("🚀 Iniciando testes de integração Event Bus...")
    print("=" * 60)
    
    tests = [
        ("Conexão Event Bus", test_event_bus_connection),
        ("Informações Publisher", test_publisher_info),
        ("Evento User Registered", test_user_registered_event),
        ("Evento Email Verification", test_email_verification_event),
        ("Evento Password Reset", test_password_reset_event),
        ("Evento Profile Updated", test_profile_updated_event)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro no teste '{test_name}': {str(e)}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! Integração funcionando corretamente.")
    else:
        print("⚠️ Alguns testes falharam. Verifique as configurações.")
    
    return passed == total


if __name__ == "__main__":
    print("🧪 Teste de Integração - Event Bus")
    print("User Service -> Notification Service")
    print("=" * 60)
    
    # Executar testes
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n✅ Integração Event Bus funcionando corretamente!")
        exit(0)
    else:
        print("\n❌ Problemas na integração Event Bus!")
        exit(1)