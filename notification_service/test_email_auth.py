#!/usr/bin/env python3
"""
Script de teste para verificar autenticação de email
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from services.email_service import EmailService

async def test_email_authentication():
    """Testa a autenticação do email"""
    print("🔍 Testando autenticação de email...")
    print(f"📧 Email configurado: {settings.smtp_user}")
    print(f"🔑 Senha configurada: {'*' * len(settings.smtp_password)}")
    print(f"🌐 Servidor SMTP: {settings.smtp_host}:{settings.smtp_port}")
    print(f"🔒 TLS: {settings.smtp_use_tls}")
    print("-" * 50)
    
    try:
        # Inicializar o serviço de email
        email_service = EmailService()
        
        # Testar envio de email simples
        result = await email_service.send_email(
            to_email="carolinescharmosa@gmail.com",
            subject="Teste de Autenticação - VidConv",
            html_content="""
            <html>
                <body>
                    <h2>✅ Teste de Autenticação Bem-sucedido!</h2>
                    <p>Este email confirma que a autenticação Gmail está funcionando corretamente.</p>
                    <p><strong>Configurações testadas:</strong></p>
                    <ul>
                        <li>Email: renebmjr@gmail.com</li>
                        <li>Servidor: smtp.gmail.com:587</li>
                        <li>TLS: Ativado</li>
                    </ul>
                    <p>🎉 Sistema de notificações operacional!</p>
                </body>
            </html>
            """,
            text_content="Teste de autenticação bem-sucedido! O sistema de notificações está funcionando."
        )
        
        if result:
            print("✅ Email enviado com sucesso!")
            print("🎉 Autenticação Gmail funcionando corretamente!")
        else:
            print("❌ Falha no envio do email")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        print(f"🔍 Tipo do erro: {type(e).__name__}")
        
        # Verificar erros específicos de autenticação
        if "authentication" in str(e).lower():
            print("\n🚨 ERRO DE AUTENTICAÇÃO DETECTADO!")
            print("Possíveis causas:")
            print("1. Email incorreto no arquivo .env")
            print("2. Senha de app incorreta")
            print("3. Verificação em 2 etapas não ativada")
            print("4. Senha de app não gerada corretamente")
        
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando teste de autenticação de email...")
    success = asyncio.run(test_email_authentication())
    
    if success:
        print("\n🎉 Teste concluído com sucesso!")
    else:
        print("\n❌ Teste falhou - verifique as configurações")