"""
Script de Teste para Envio de Emails - VidConv Notification Service
Testa a funcionalidade de envio de emails via Gmail SMTP
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.email_service import EmailService
from config.settings import settings

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailTester:
    """
    Classe para testar funcionalidades de email
    """
    
    def __init__(self):
        """
        Inicializa o testador de email
        """
        self.email_service = EmailService()
        self.test_results = {
            "connection_test": False,
            "welcome_email": False,
            "verification_email": False,
            "conversion_completed_email": False,
            "total_tests": 4,
            "passed_tests": 0
        }
    
    async def test_smtp_connection(self) -> bool:
        """
        Testa a conexão SMTP com Gmail
        """
        logger.info("🔍 Testando conexão SMTP com Gmail...")
        
        try:
            # Testa conexão
            connection_ok = await self.email_service.test_connection()
            
            if connection_ok:
                logger.info("✅ Conexão SMTP testada com sucesso!")
                
                # Exibe informações da configuração
                gmail_info = await self.email_service.get_gmail_info()
                logger.info("📧 Configuração Gmail:")
                for key, value in gmail_info.items():
                    logger.info(f"   {key}: {value}")
                
                self.test_results["connection_test"] = True
                return True
            else:
                logger.error("❌ Falha na conexão SMTP")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão: {str(e)}")
            return False
    
    async def test_welcome_email(self, recipient_email: str) -> bool:
        """
        Testa o envio de email de boas-vindas
        """
        logger.info("📧 Testando envio de email de boas-vindas...")
        
        try:
            success = await self.email_service.send_welcome_email(
                email=recipient_email,
                name="Usuário Teste",
                user_id=12345
            )
            
            if success:
                logger.info("✅ Email de boas-vindas enviado com sucesso!")
                self.test_results["welcome_email"] = True
                return True
            else:
                logger.error("❌ Falha ao enviar email de boas-vindas")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste de email de boas-vindas: {str(e)}")
            return False
    
    async def test_verification_email(self, recipient_email: str) -> bool:
        """
        Testa o envio de email de verificação
        """
        logger.info("🔐 Testando envio de email de verificação...")
        
        try:
            # Token de verificação fictício para teste
            verification_token = "test_token_123456789"
            
            success = await self.email_service.send_verification_email(
                email=recipient_email,
                name="Usuário Teste",
                verification_token=verification_token
            )
            
            if success:
                logger.info("✅ Email de verificação enviado com sucesso!")
                self.test_results["verification_email"] = True
                return True
            else:
                logger.error("❌ Falha ao enviar email de verificação")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste de email de verificação: {str(e)}")
            return False
    
    async def test_conversion_completed_email(self, recipient_email: str) -> bool:
        """
        Testa o envio de email de conversão concluída
        """
        logger.info("🎬 Testando envio de email de conversão concluída...")
        
        try:
            # Dados de teste para conversão
            template_data = {
                "video_title": "Meu Vídeo de Teste",
                "original_format": "MP4",
                "converted_format": "AVI",
                "file_size": "125.5 MB",
                "conversion_time": "2 minutos e 30 segundos",
                "download_url": "https://vidconv.com/download/test123",
                "conversion_date": datetime.now().strftime("%d/%m/%Y às %H:%M"),
                "platform_name": settings.app_name
            }
            
            success = await self.email_service.send_conversion_completed_email(
                email=recipient_email,
                name="Usuário Teste",
                template_data=template_data
            )
            
            if success:
                logger.info("✅ Email de conversão concluída enviado com sucesso!")
                self.test_results["conversion_completed_email"] = True
                return True
            else:
                logger.error("❌ Falha ao enviar email de conversão concluída")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste de email de conversão concluída: {str(e)}")
            return False
    
    async def run_all_tests(self, recipient_email: str):
        """
        Executa todos os testes de email
        """
        logger.info("🚀 Iniciando testes de email do VidConv Notification Service")
        logger.info(f"📧 Email de teste: {recipient_email}")
        logger.info("=" * 60)
        
        # Teste 1: Conexão SMTP
        if await self.test_smtp_connection():
            self.test_results["passed_tests"] += 1
        
        logger.info("-" * 60)
        
        # Teste 2: Email de boas-vindas
        if await self.test_welcome_email(recipient_email):
            self.test_results["passed_tests"] += 1
        
        logger.info("-" * 60)
        
        # Teste 3: Email de verificação
        if await self.test_verification_email(recipient_email):
            self.test_results["passed_tests"] += 1
        
        logger.info("-" * 60)
        
        # Teste 4: Email de conversão concluída
        if await self.test_conversion_completed_email(recipient_email):
            self.test_results["passed_tests"] += 1
        
        # Resumo dos testes
        await self.print_test_summary()
    
    async def print_test_summary(self):
        """
        Exibe resumo dos testes executados
        """
        logger.info("=" * 60)
        logger.info("📊 RESUMO DOS TESTES DE EMAIL")
        logger.info("=" * 60)
        
        for test_name, result in self.test_results.items():
            if test_name not in ["total_tests", "passed_tests"]:
                status = "✅ PASSOU" if result else "❌ FALHOU"
                logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
        
        logger.info("-" * 60)
        passed = self.test_results["passed_tests"]
        total = self.test_results["total_tests"]
        percentage = (passed / total) * 100
        
        logger.info(f"Testes Aprovados: {passed}/{total} ({percentage:.1f}%)")
        
        if passed == total:
            logger.info("🎉 TODOS OS TESTES PASSARAM! Sistema de email funcionando corretamente.")
        elif passed > 0:
            logger.warning(f"⚠️  {total - passed} teste(s) falharam. Verifique a configuração.")
        else:
            logger.error("❌ TODOS OS TESTES FALHARAM! Verifique a configuração do Gmail.")
        
        logger.info("=" * 60)


async def main():
    """
    Função principal para executar os testes
    """
    # Email para receber os testes (substitua pelo seu email)
    test_email = input("Digite o email para receber os testes: ").strip()
    
    if not test_email:
        logger.error("❌ Email não fornecido. Encerrando testes.")
        return
    
    # Valida formato básico do email
    if "@" not in test_email or "." not in test_email:
        logger.error("❌ Formato de email inválido. Encerrando testes.")
        return
    
    # Executa os testes
    tester = EmailTester()
    await tester.run_all_tests(test_email)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Testes interrompidos pelo usuário.")
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {str(e)}")