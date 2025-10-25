"""
Script de Teste - Gmail SMTP Configuration
Notification Service - Plataforma VOD
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório pai ao path
sys.path.append(str(Path(__file__).parent))

from services.email_service import EmailService
from config.settings import settings


async def test_gmail_configuration():
    """
    Testa a configuração completa do Gmail SMTP
    """
    print("🔧 Testando Configuração Gmail SMTP - VidConv Platform")
    print("=" * 60)
    
    # Verificar configurações
    print("\n📋 1. Verificando Configurações:")
    print(f"   Host: {settings.SMTP_HOST}")
    print(f"   Porta: {settings.SMTP_PORT}")
    print(f"   Usuário: {settings.SMTP_USER}")
    print(f"   TLS: {settings.SMTP_USE_TLS}")
    print(f"   SSL: {settings.SMTP_USE_SSL}")
    print(f"   Timeout: {settings.SMTP_TIMEOUT}s")
    print(f"   From Email: {settings.FROM_EMAIL}")
    print(f"   From Name: {settings.FROM_NAME}")
    
    # Verificar se as credenciais estão configuradas
    if settings.SMTP_USER == "your-email@gmail.com" or settings.SMTP_PASSWORD == "your-gmail-app-password":
        print("\n❌ ERRO: Credenciais não configuradas!")
        print("💡 Edite o arquivo .env com suas credenciais do Gmail")
        print("📖 Consulte GMAIL_SETUP.md para instruções detalhadas")
        return False
    
    # Inicializar EmailService
    email_service = EmailService()
    
    # Teste 1: Obter informações do Gmail
    print("\n📊 2. Informações do Gmail:")
    try:
        gmail_info = await email_service.get_gmail_info()
        for key, value in gmail_info.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"   ❌ Erro ao obter informações: {str(e)}")
        return False
    
    # Teste 2: Conexão SMTP
    print("\n🔌 3. Testando Conexão SMTP:")
    try:
        connection_success = await email_service.test_connection()
        if connection_success:
            print("   ✅ Conexão Gmail SMTP bem-sucedida!")
        else:
            print("   ❌ Falha na conexão Gmail SMTP")
            return False
    except Exception as e:
        print(f"   ❌ Erro na conexão: {str(e)}")
        return False
    
    # Teste 3: Envio de email (opcional)
    test_email_input = input("\n📧 4. Deseja testar envio de email? (s/N): ").lower().strip()
    
    if test_email_input == 's':
        recipient = input("   Digite o email de destino: ").strip()
        
        if recipient and "@" in recipient:
            print(f"   📤 Enviando email de teste para {recipient}...")
            
            try:
                email_success = await email_service.send_test_email(
                    recipient=recipient,
                    subject="🧪 Teste Gmail SMTP - VidConv Platform"
                )
                
                if email_success:
                    print("   ✅ Email de teste enviado com sucesso!")
                    print(f"   📬 Verifique a caixa de entrada de {recipient}")
                else:
                    print("   ❌ Falha no envio do email")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Erro no envio: {str(e)}")
                return False
        else:
            print("   ⚠️ Email inválido, pulando teste de envio")
    
    print("\n🎉 Todos os testes passaram!")
    print("✅ Gmail SMTP configurado corretamente")
    return True


async def main():
    """
    Função principal
    """
    try:
        success = await test_gmail_configuration()
        
        if success:
            print("\n" + "=" * 60)
            print("🚀 Gmail SMTP pronto para uso!")
            print("📖 Consulte GMAIL_SETUP.md para mais informações")
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ Configuração do Gmail SMTP falhou")
            print("📖 Consulte GMAIL_SETUP.md para troubleshooting")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Verificar se o arquivo .env existe
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        print("💡 Copie .env.example para .env e configure suas credenciais")
        sys.exit(1)
    
    # Executar testes
    asyncio.run(main())