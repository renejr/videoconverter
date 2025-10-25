"""
Main Application - Notification Service
Plataforma VOD
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config.settings import settings
from database.connection import init_db, get_db, test_connection, get_db_info
from events.bus import EventBus
from events.handlers import EventHandlers
from services.email_service import EmailService
from services.notification_service import NotificationService
from services.template_service import TemplateService


# Configuração de logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instâncias globais
event_bus = None
event_handlers = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação
    """
    global event_bus, event_handlers
    
    try:
        # Inicialização
        logger.info("🚀 Iniciando Notification Service...")
        
        # Inicializar banco de dados
        logger.info("📊 Inicializando banco de dados...")
        init_db()
        
        # Testar conexão com banco
        if not test_connection():
            raise Exception("Falha na conexão com banco de dados")
        
        # Inicializar Event Bus
        logger.info("🔄 Inicializando Event Bus...")
        event_bus = EventBus()
        await event_bus.connect()
        
        # Inicializar Event Handlers
        logger.info("⚡ Inicializando Event Handlers...")
        email_service = EmailService()
        notification_service = NotificationService()
        template_service = TemplateService()
        
        # Importar novos handlers de usuário
        from event_handlers.user_handlers import (
            UserRegisteredHandler,
            EmailVerificationRequestedHandler,
            PasswordResetRequestedHandler,
            UserProfileUpdatedHandler
        )
        
        # Inicializar handlers específicos
        user_registered_handler = UserRegisteredHandler()
        email_verification_handler = EmailVerificationRequestedHandler()
        password_reset_handler = PasswordResetRequestedHandler()
        profile_updated_handler = UserProfileUpdatedHandler()
        
        # Registrar handlers no Event Bus para eventos específicos
        await event_bus.subscribe("user.registered", user_registered_handler.handle_event)
        await event_bus.subscribe("email.verification.requested", email_verification_handler.handle_event)
        await event_bus.subscribe("password.reset.requested", password_reset_handler.handle_event)
        await event_bus.subscribe("user.profile.updated", profile_updated_handler.handle_event)
        
        # Manter handlers existentes
        event_handlers = EventHandlers(
            email_service=email_service,
            notification_service=notification_service,
            template_service=template_service
        )
        
        # Registrar handlers legados no Event Bus
        await event_bus.subscribe_handlers(event_handlers)
        
        # Iniciar processamento de eventos
        await event_bus.start_listening()
        
        logger.info("✅ Notification Service iniciado com sucesso!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {str(e)}")
        raise
    
    finally:
        # Cleanup
        logger.info("🔄 Finalizando Notification Service...")
        
        if event_bus:
            await event_bus.stop_listening()
            await event_bus.disconnect()
        
        logger.info("✅ Notification Service finalizado!")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Serviço de Notificações da Plataforma VOD",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Endpoint raiz - informações do serviço
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "description": "Serviço de Notificações da Plataforma VOD"
    }


@app.get("/health")
async def health_check():
    """
    Health check do serviço
    """
    try:
        # Verificar banco de dados
        db_status = test_connection()
        
        # Verificar Event Bus
        event_bus_status = event_bus and event_bus.is_connected() if event_bus else False
        
        # Status geral
        overall_status = db_status and event_bus_status
        
        return {
            "status": "healthy" if overall_status else "unhealthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "services": {
                "database": "up" if db_status else "down",
                "event_bus": "up" if event_bus_status else "down"
            }
        }
        
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/info")
async def service_info():
    """
    Informações detalhadas do serviço
    """
    try:
        db_info = get_db_info()
        
        return {
            "service": {
                "name": settings.app_name,
                "version": settings.app_version,
                "environment": "development" if settings.debug else "production",
                "debug": settings.debug
            },
            "database": db_info,
            "event_bus": {
                "host": settings.redis_host,
                "port": settings.redis_port,
                "connected": event_bus.is_connected() if event_bus else False
            },
            "email": {
                "provider": "Gmail SMTP",
                "host": settings.smtp_host,
                "port": settings.smtp_port,
                "use_tls": settings.smtp_use_tls
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter informações: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gmail/info")
async def gmail_info():
    """
    Informações sobre a configuração do Gmail SMTP
    """
    try:
        email_service = EmailService()
        info = await email_service.get_gmail_info()
        
        return {
            "status": "success",
            "gmail_config": info
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do Gmail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gmail/test-connection")
async def test_gmail_connection():
    """
    Testa a conexão com Gmail SMTP
    """
    try:
        email_service = EmailService()
        
        # Testar conexão
        success = await email_service.test_connection()
        
        if success:
            return {
                "status": "success",
                "message": "✅ Conexão Gmail SMTP testada com sucesso",
                "provider": "Gmail SMTP"
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "❌ Falha na conexão Gmail SMTP",
                    "suggestion": "Verifique suas credenciais e configurações"
                }
            )
            
    except Exception as e:
        logger.error(f"Erro no teste de conexão Gmail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/email")
async def test_email(
    recipient: str,
    subject: str = "Teste Gmail SMTP - VidConv Platform",
    db: Session = Depends(get_db)
):
    """
    Endpoint para testar envio de email via Gmail
    """
    try:
        email_service = EmailService()
        
        # Enviar email de teste
        success = await email_service.send_test_email(
            recipient=recipient,
            subject=subject
        )
        
        if success:
            return {
                "status": "success",
                "message": f"✅ Email de teste enviado via Gmail para {recipient}",
                "provider": "Gmail SMTP"
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "❌ Falha no envio do email via Gmail",
                    "suggestion": "Verifique logs para mais detalhes"
                }
            )
            
    except Exception as e:
        logger.error(f"Erro no teste de email Gmail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/event")
async def test_event(event_type: str, event_data: dict):
    """
    Endpoint para testar publicação de eventos
    """
    try:
        if not event_bus:
            raise HTTPException(status_code=503, detail="Event Bus não disponível")
        
        # Publicar evento de teste
        await event_bus.publish(event_type, event_data)
        
        return {
            "status": "success",
            "message": f"Evento '{event_type}' publicado com sucesso"
        }
        
    except Exception as e:
        logger.error(f"Erro no teste de evento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )