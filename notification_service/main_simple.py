#!/usr/bin/env python3
"""
Notification Service - Versão Simplificada
Plataforma VOD
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import redis.asyncio as redis

from config.settings import settings

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="VOD Notification Service",
    description="Serviço de Notificações da Plataforma VOD",
    version=settings.app_version,
    debug=settings.debug
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variável global para Redis
redis_client = None


async def connect_redis():
    """
    Conecta ao Redis
    """
    global redis_client
    try:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Conectado ao Redis")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Redis: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """
    Evento de inicialização
    """
    logger.info("🚀 Iniciando Notification Service...")
    
    # Conectar ao Redis
    redis_connected = await connect_redis()
    if not redis_connected:
        logger.warning("⚠️ Redis não conectado - algumas funcionalidades podem não funcionar")
    
    logger.info("✅ Notification Service iniciado com sucesso!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento de encerramento
    """
    global redis_client
    if redis_client:
        await redis_client.close()
    logger.info("👋 Notification Service encerrado")


@app.get("/")
async def root():
    """
    Endpoint raiz
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
    Health check
    """
    global redis_client
    
    # Verificar Redis
    redis_status = "disconnected"
    if redis_client:
        try:
            await redis_client.ping()
            redis_status = "connected"
        except:
            redis_status = "error"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/info")
async def service_info():
    """
    Informações detalhadas do serviço
    """
    global redis_client
    
    # Status do Redis
    redis_info = {"status": "disconnected"}
    if redis_client:
        try:
            await redis_client.ping()
            redis_info = {
                "status": "connected",
                "host": settings.redis_host,
                "port": settings.redis_port,
                "db": settings.redis_db
            }
        except Exception as e:
            redis_info = {
                "status": "error",
                "error": str(e)
            }
    
    # Configurações de email
    email_info = {
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_user": settings.smtp_user,
        "smtp_configured": bool(settings.smtp_user and settings.smtp_password)
    }
    
    return {
        "service": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": "development" if settings.debug else "production",
            "debug": settings.debug
        },
        "redis": redis_info,
        "email": email_info
    }


@app.post("/test/email")
async def test_email(email: str):
    """
    Teste de envio de email
    """
    # Por enquanto apenas simula o envio
    return {
        "message": f"Email de teste enviado para {email}",
        "status": "simulated",
        "note": "Funcionalidade de email será implementada em breve"
    }


@app.post("/test/event")
async def test_event():
    """
    Teste de publicação de evento
    """
    global redis_client
    
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis não conectado")
    
    try:
        test_event = {
            "type": "test",
            "message": "Evento de teste do Notification Service",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        result = await redis_client.publish("notifications.test", str(test_event))
        
        return {
            "message": "Evento de teste publicado",
            "channel": "notifications.test",
            "subscribers": result,
            "event": test_event
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao publicar evento: {e}")


if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )